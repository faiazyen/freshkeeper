"""Chapter 4: Practical Part."""

from docx_builder import (
    bullet, code_block, figure, heading, numbered, para, reset_numbering,
    rich_para, table,
)

from results import Results

FIG = "../freshkeeper/docs/figures"

_COV_MODULES = [
    "freshkeeper/hardware/base.py", "freshkeeper/ml/model.py", "freshkeeper/alerts.py",
    "freshkeeper/db/models.py", "freshkeeper/hardware/sim_backend.py",
    "freshkeeper/hardware/spoilage_model.py", "freshkeeper/api/app.py",
    "freshkeeper/db/session.py", "freshkeeper/ml/inference.py",
    "freshkeeper/db/maintenance.py", "freshkeeper/hardware/rpi_backend.py",
]


def build(document) -> None:
    R = Results()
    heading(document, "Practical Part", 1)

    para(document,
         "This chapter describes what was built. It follows the order the system "
         "was constructed in, which is also the order in which each piece became "
         "testable: the physical model first, then the sensing layer on top of "
         "it, then the data, then the models, then the software that ties them "
         "together.")

    para(document,
         f"The complete implementation is {R.n(R.loc)} lines of Python across "
         f"{R.files} tracked files, with {R.tests} automated tests. Listings in "
         "this chapter are excerpts; "
         "Appendix A contains the significant modules in full and the repository "
         "structure is given in Appendix B.")

    # ==================================================================
    heading(document, "System architecture", 2)

    para(document,
         "The system follows the three-layer decomposition standard in IoT work "
         "(Atzori et al., 2010), with one departure: the "
         "network layer carries data between components on the same board rather "
         "than to a remote server, because all processing is local.")

    figure(document, f"{FIG}/architecture.png", "Figure 1",
           "System architecture. Sensors feed an acquisition scheduler running "
           "on a thirty-minute cycle; a frozen MobileNetV2 backbone turns each "
           "image into an embedding which the fusion head classifies alongside "
           "five sensor features; results reach the user through a REST API and "
           "a single-page interface served from the device.", width_cm=15.5)

    para(document,
         "The perception layer is a camera, two metal-oxide gas sensors, a "
         "temperature and humidity sensor and one load cell per shelf slot. The "
         "processing layer schedules measurements, converts analogue signals, "
         "runs inference and writes to the database. The application layer is "
         "the API, the alert engine and the interface.")

    para(document,
         "A design decision worth stating early is the sensor abstraction "
         "boundary. Nothing above the hardware layer imports a GPIO library. "
         "Everything talks to an interface with two implementations behind it: "
         "one that drives real hardware, one that synthesises readings from the "
         "physical model. This is what allows the entire system — the API, the "
         "alert logic, the inference service, the test suite — to run on a "
         "laptop with nothing plugged in, and it means moving to real hardware "
         "changes one line of configuration rather than requiring a rewrite.")

    # ==================================================================
    heading(document, "Hardware design", 2)

    heading(document, "Component selection", 3)

    para(document,
         "Components were chosen for cost, availability and the existence of "
         "mature Python libraries. Table 2 lists the bill of materials.")

    table(document,
          ["Component", "Part", "Purpose", "Cost (EUR)"],
          [["Single-board computer", "Raspberry Pi 4 Model B, 4 GB",
            "Inference host, web server, acquisition", "55"],
           ["Camera", "Raspberry Pi Camera Module 3", "Visual inspection", "28"],
           ["Gas sensor 1", "MQ-135 module", "Ammonia and related VOCs", "4"],
           ["Gas sensor 2", "MQ-3 module", "Ethanol", "4"],
           ["Environment", "DHT22 (AM2302)", "Temperature and humidity", "4"],
           ["Mass", "HX711 amplifier + 5 kg load cell", "Per-slot mass", "8"],
           ["ADC", "MCP3008, 8-channel 10-bit", "Analogue gas sensors to SPI", "3"],
           ["Illumination", "5 V LED strip, 50 cm", "Consistent lighting", "5"],
           ["Storage", "64 GB Class 10 microSD", "OS and database", "12"],
           ["Power", "Official 5 V / 3 A supply", "Power delivery", "10"],
           ["Enclosure", "3D-printed PLA", "Housing", "6"],
           ["Wiring", "Jumpers, resistors, capacitors, breadboard", "Connections", "8"],
           ["**Total**", "", "", "**147**"]],
          "Table 2",
          "Bill of materials with approximate retail prices at the time of "
          "writing. The total is comparable to a mid-range kitchen appliance "
          "and well below commercial smart-fridge retrofits.",
          widths=[4.0, 5.2, 4.6, 2.2])

    para(document,
         "Two choices deserve justification. The Raspberry Pi 4 rather than the "
         "cheaper Pi Zero 2 W was selected because the visual backbone dominates "
         "inference cost, and Chapter 5 shows that even on the Pi 4 the backbone "
         "accounts for 92% of the per-item time. The MCP3008 is required rather "
         "than optional: the Raspberry Pi has no analogue input at all, and the "
         "MQ sensors are analogue devices, so without an external converter "
         "there is no gas channel.")

    heading(document, "Wiring", 3)

    para(document,
         "Figure 2 gives the pin-level design. The pin numbers in the figure are "
         "imported from the driver module rather than typed into the diagram, so "
         "the two cannot disagree.")

    figure(document, f"{FIG}/wiring.png", "Figure 2",
           "Sensor wiring in BCM pin numbering. The DHT22 uses a single-wire "
           "protocol with a pull-up; the HX711 is bit-banged over two pins; both "
           "gas sensors reach the Pi through the MCP3008 over SPI0 via a "
           "resistive divider; the LED strip and the gas-heater supply rail are "
           "each switched by a MOSFET rather than driven from a GPIO pin.",
           width_cm=15.5)

    para(document,
         "Three details in that design are not obvious and are recorded here "
         "because they are the kind of thing that costs an afternoon.")

    para(document,
         "The LED strip is switched through a 2N7000 N-channel MOSFET rather "
         "than driven from a GPIO pin. A Raspberry Pi GPIO pin sources about 16 "
         "mA safely, and a 50 cm strip wants considerably more; driving it "
         "directly damages the pin.")

    para(document,
         "The MQ sensors need a 5 V heater supply, but the MCP3008 input must "
         "stay below 3.3 V, so the sensor output is divided down by a factor of "
         "0.66 before it reaches the converter, and the driver scales the "
         "reading back up before applying the resistance formula. An earlier "
         "revision of the driver omitted that step and would have reported "
         "every resistance too high by the divider ratio — a defect no test "
         "could catch without hardware, which is why it is recorded here.")

    para(document,
         "The heater supply rail for both gas sensors is switched through a "
         "logic-level MOSFET on GPIO 17, so the heaters draw power only during "
         "the measurement window. The driver switches them on at the start of "
         "a cycle, waits 30 seconds for the elements to settle, reads every "
         "slot, and switches them off again — in a finally block, so a sensor "
         "fault mid-cycle cannot leave them burning.")

    para(document,
         "The gas heaters and the load cell share the 5 V rail, and heater "
         "switching couples into the HX711. The mitigation in the design is to "
         "separate the two readings in time — the driver waits 500 ms between "
         "the gas channels and the weight channel — and to decouple the HX711 "
         "supply. This is documented as a design measure rather than a solved "
         "problem, because the hardware was not built and the mitigation has not "
         "been verified on a bench.")

    heading(document, "Enclosure", 3)

    para(document,
         "The sensing head is designed to sit inside the cabinet in a 3D-printed "
         "PLA enclosure of roughly 15 × 10 × 8 cm, small enough to occupy part "
         "of one shelf. It carries a transparent front panel for the camera, "
         "ventilation slots so the gas sensors sample cabinet air rather than "
         "their own microclimate, a platform above each load cell, and a cable "
         "channel.")

    para(document,
         "Two conflicting requirements meet here and the resolution is a "
         "compromise. The gas sensors want air exchange with the cabinet, so "
         "that what they measure reflects the shelf. The camera wants "
         "controlled, repeatable lighting, which argues for enclosing the "
         "imaging volume. Ventilation slots placed away from the imaging path "
         "give both, imperfectly.")

    para(document,
         "The Raspberry Pi itself can be mounted outside the cabinet with "
         "extension cables through the door seal. This is the preferred "
         "arrangement: the board dissipates around 4 W, and putting a 4 W heater "
         "inside a refrigerator both wastes energy and biases the temperature "
         "reading the whole system depends on. Running cables through a door "
         "seal is its own compromise, and a production design would use an "
         "internal battery with wireless data rather than either option.")

    heading(document, "Sensor calibration", 3)

    para(document,
         "Three of the four sensing channels need calibration before their "
         "readings mean anything in absolute terms, and the procedure is "
         "specified here because omitting it is a common gap in the prototypes "
         "reviewed in Chapter 3.")

    para(document,
         "The MQ sensors report a resistance ratio against a clean-air reference "
         "R₀, and without that reference the datasheet power law has no anchor. "
         "Establishing it requires running the heater for 24 to 48 hours to "
         "settle the element, then recording the resistance in clean air at "
         "known temperature and humidity. R₀ drifts as the element ages, so the "
         "design stores it in configuration and expects periodic "
         "re-establishment. The simulation models that drift at 0.4% per day.")

    para(document,
         "The load cell needs two constants: an offset, recorded with the "
         "platform empty, and a scale factor in counts per gram, obtained by "
         "placing a known mass and dividing. Both are per-device and per-cell, "
         "because load cells vary in sensitivity and the amplifier gain is not "
         "identical between boards.")

    para(document,
         "The DHT22 is factory-calibrated and needs none, which is a large part "
         "of why it was chosen over a cheaper analogue thermistor arrangement.")

    para(document,
         "The camera needs a per-slot region of interest. The camera photographs "
         "the whole shelf, and each slot's crop box is recorded at setup so that "
         "individual item images can be extracted from one exposure. This is "
         "manual configuration, and getting it wrong means classifying the wrong "
         "item — a real weakness of the design, and one an automatic "
         "segmentation step would remove.")

    heading(document, "Driver implementation", 3)

    para(document,
         "The Raspberry Pi driver is written and syntactically complete, and the "
         "test suite verifies its interface conformance, pin-map consistency, "
         "the divider correction, that the heaters are switched off even when a "
         "read raises, and the pure conversion functions. Its readings have not "
         "been validated "
         "against instruments, and the module's own docstring says so, so that "
         "nobody reading the code mistakes it for a tested component.")

    para(document,
         "The HX711 has no standard bus and must be bit-banged, which is the "
         "least obvious part of the driver:")

    code_block(document,
               '''def _read_hx711(self, samples: int = 10) -> float:
    """Read the load cell and return grams."""
    GPIO = self._gpio
    readings = []
    for _ in range(samples):
        timeout = time.time() + 1.0
        while GPIO.input(PIN_HX711_DOUT) == 1:       # wait for data-ready
            if time.time() > timeout:
                raise TimeoutError("HX711 did not signal data ready within 1 s")
            time.sleep(0.001)

        value = 0
        for _ in range(24):                          # 24 clock pulses, MSB first
            GPIO.output(PIN_HX711_SCK, True)
            value = (value << 1) | GPIO.input(PIN_HX711_DOUT)
            GPIO.output(PIN_HX711_SCK, False)
        GPIO.output(PIN_HX711_SCK, True)             # 25th pulse: channel A, gain 128
        GPIO.output(PIN_HX711_SCK, False)

        if value & 0x800000:                         # sign-extend two's complement
            value -= 0x1000000
        readings.append(value)

    # Median, not mean: one mains-borne spike drags a mean by tens of grams.
    readings.sort()
    median = readings[len(readings) // 2]
    return round((median - self.load_cell_offset) / self.load_cell_scale, 1)''',
               "Listing 1",
               "Bit-banged HX711 read. The 25th clock pulse selects channel A at "
               "gain 128 for the following conversion; omitting it silently "
               "switches the amplifier to a different channel.")

    # ==================================================================
    heading(document, "The physical spoilage model", 2)

    para(document,
         "This module is the foundation the simulated sensing layer stands on, "
         "and it is the part of the practical work with the most scientific "
         "content. Each function implements a published model and names its "
         "source.")

    heading(document, "Temperature-dependent growth", 3)

    para(document,
         "The Ratkowsky square-root relationship gives the specific growth rate "
         "of the spoilage population as a function of temperature. Below the "
         "notional minimum the implementation returns zero rather than a "
         "negative rate, which is what freezing does in practice:")

    code_block(document,
               '''def ratkowsky_growth_rate(temp_c: float, b_coefficient: float = 0.0130) -> float:
    """Specific growth rate of the spoilage population, 1/hour, natural-log basis.

    The rate is on a natural-log basis, which is how Ratkowsky defined it.
    Gompertz below works in log10, so callers must divide by ln(10). Getting
    this wrong shortens every predicted shelf life by a factor of 2.3.
    """
    if temp_c <= T_MIN_GROWTH:
        return 0.0
    return (b_coefficient * (temp_c - T_MIN_GROWTH)) ** 2''',
               "Listing 2",
               "Ratkowsky growth rate. The docstring warning is not decorative: "
               "the log-basis mismatch it describes was a real bug in an early "
               "version, and a regression test now guards against it.")

    para(document,
         "That comment records an actual defect. The first implementation passed "
         "the Ratkowsky rate, which is on a natural-log basis, straight into a "
         "Gompertz function expecting log₁₀ units. Every shelf life came out "
         "2.3 times too short — strawberries spoiled in 50 hours at 4 °C — and "
         "the curves looked entirely plausible until they were compared against "
         "published values. A calibration test now fails if the conversion is "
         "removed.")

    heading(document, "Population growth", 3)

    para(document,
         "Growth over time follows the modified Gompertz function in the "
         "Zwietering et al. (1990) parameterisation, returning the log₁₀ "
         "increase in population above the initial level. Temperature history is "
         "folded in by accumulating effective time: at each step the "
         "instantaneous rate is compared against the rate at a 4 °C reference, "
         "and the elapsed interval is credited in proportion. An hour at 12 °C "
         "therefore advances the item further than an hour at 4 °C by exactly "
         "the ratio the Ratkowsky model predicts.")

    para(document,
         "This is what makes the model path-dependent, and path dependence is "
         "the entire argument for measuring conditions rather than trusting a "
         "printed date. Two items of identical age, one of which spent three "
         "days at 14 °C, end up in measurably different states.")

    heading(document, "Moisture loss", 3)

    para(document,
         "Mass loss is driven by the vapour pressure deficit, computed from the "
         "Magnus-Tetens saturation vapour pressure (Alduchov and Eskridge, "
         "1996), multiplied by a commodity-specific transpiration coefficient. "
         "Relative humidity alone is not sufficient, because the same relative "
         "humidity at different temperatures corresponds to different deficits.")

    heading(document, "Combining the two", 3)

    para(document,
         "Spoilage extent is a number between 0 and 1 combining microbial load "
         "and desiccation. The two are combined by taking whichever is further "
         "advanced rather than averaging them, because either alone renders an "
         "item inedible: a cucumber that has gone rubbery is not rescued by "
         "having a low bacterial count. Extent maps onto the three reported "
         "states at 0.35 and 0.70.")

    heading(document, "Calibration", 3)

    para(document,
         "Every growth coefficient was solved backwards from a published "
         "refrigerated shelf life at 4 °C and 85% relative humidity rather than "
         "chosen to look reasonable. This makes the model falsifiable, and a "
         "parametrised test asserts the reproduction to within 5%. Chapter 5 "
         "reports the agreement achieved.")

    table(document,
          ["Commodity", "Ratkowsky b", "Lag at 4 °C (h)", "Transpiration coeff.",
           "Published shelf life (d)"],
          [["Strawberry", "0.02400", "14", "0.0030", "5"],
           ["Banana", "0.01666", "20", "0.0012", "10"],
           ["Grape", "0.01404", "26", "0.0016", "14"],
           ["Guava", "0.01408", "28", "0.0020", "14"],
           ["Jujube", "0.01147", "40", "0.0012", "21"],
           ["Orange", "0.01050", "46", "0.0008", "25"],
           ["Apple", "0.00956", "52", "0.0009", "30"],
           ["Pomegranate", "0.00673", "90", "0.0004", "60"]],
          "Table 3",
          "Per-commodity model parameters. The eight commodities are those "
          "labelled in the image corpus, so the visual and sensor branches "
          "describe the same foods. Transpiration coefficients are fractional "
          "mass loss per hour per kPa of vapour pressure deficit.",
          widths=[3.2, 2.6, 3.0, 3.4, 3.6])

    # ==================================================================
    heading(document, "Sensor abstraction and simulation", 2)

    para(document,
         "The simulated backend is not a stub returning canned values. Each slot "
         "holds an item with a commodity and an age; every read integrates the "
         "spoilage model over the conditions that slot has experienced and then "
         "converts the result into the signal a real sensor would produce.")

    heading(document, "Refrigerator thermal model", 3)

    para(document,
         "A real refrigerator does not hold its setpoint, and simulating one "
         "that does would remove the phenomenon the system exists to detect. The "
         "thermal model has a compressor cycling between bounds, door openings "
         "drawn from a Poisson process, and exponential recovery afterwards. "
         "Different households are modelled as different fridges: setpoints from "
         "2.5 to 7.5 °C and door-opening rates from 6 to 24 per day, sampled "
         "with weights when generating training data.")

    para(document,
         "The first implementation of this summed the contribution of every past "
         "door opening at every time step, which is quadratic. Generating a "
         "60-day pomegranate trajectory took minutes, and the corpus generator "
         "needs thousands of them. Because the contributions decay "
         "exponentially, the accumulated excess can instead be carried forward "
         "with one multiplication per step. The same 180-day series now takes "
         "8 milliseconds.")

    heading(document, "Sensor signal chain", 3)

    para(document,
         "Simulated readings pass through the transfer functions of the "
         "specified parts rather than being reported as clean values. "
         "Concentration becomes a resistance ratio through a power law whose "
         "coefficients were digitised from the datasheet sensitivity curves by "
         "the open-source MQSensorsLib project (Califa Urquiza, 2019) — the "
         "Hanwei datasheets publish the curves as graphs, not as equations, so "
         "the coefficients are a community fit rather than a manufacturer "
         "specification. The ratio becomes a voltage across the load resistor, "
         "the MCP3008 "
         "quantises that to 10 bits, and the firmware inverts the chain. The "
         "round trip is lossy, and that loss is part of what the classifier has "
         "to cope with. Gaussian noise is added at the DHT22's stated accuracy "
         "and the HX711's noise floor, and the MQ baseline drifts slowly upward "
         "as a heater would age.")

    para(document,
         "The direction of the MQ power law caused a real bug here. Published "
         "fits are given as concentration in terms of resistance ratio:")

    rich_para(document, [("        ppm = A · (R", "i"), ("s", "i"), ("/R", "i"),
                         ("0", "i"), (")", "i"), ("−B", "i")], justify=False)

    para(document,
         "The first implementation applied those constants in the opposite "
         "direction. At realistic concentrations that drove the modelled "
         "resistance ratio to around 10⁻⁴, which saturates a 10-bit converter, "
         "and the ethanol channel silently returned zero for every reading above "
         "the low tens of ppm. The symptom was a spoiled strawberry reporting no "
         "ethanol at all. Both conversion directions are now separate named "
         "functions with a round-trip test.")

    figure(document, f"{FIG}/sensor_trajectories.png", "Figure 3",
           "Simulated sensor response over 30 days for three commodities in one "
           "cabinet. Volatile production tracks microbial growth, mass declines "
           "with transpiration, and the temperature panel shows compressor "
           "cycling with door-opening spikes. Strawberry, banana and apple "
           "separate in the order their published shelf lives predict.",
           width_cm=15.5)

    heading(document, "What the simulation does not do", 3)

    para(document,
         "The simulated backend returns None when asked for an image. It "
         "synthesises the sensor array and never the photograph, and returning a "
         "fabricated image path would blur exactly the boundary this thesis "
         "needs to keep sharp. Real images come from the corpus described next.")

    # ==================================================================
    heading(document, "Dataset preparation and audit", 2)

    heading(document, "Source", 3)

    para(document,
         "The image corpus is the augmented configuration of "
         "Project-AgML/fresh_rotten_fruit_classification, released under "
         "CC-BY-4.0: 12,335 photographs across eight commodities — apple, "
         "banana, grape, guava, jujube, orange, pomegranate and strawberry — "
         "each labelled fresh or rotten, close to evenly balanced at 6,194 fresh "
         "against 6,141 rotten.")

    para(document,
         "Images were decoded, resized to 224 × 224 and split 70/15/15, "
         "stratified jointly on commodity and label. Stratifying on the label "
         "alone would allow most of one fruit into training and most of another "
         "into test, so that the test score would measure transfer between "
         "fruits rather than spoilage detection.")

    heading(document, "An audit that changed the results", 3)

    para(document,
         f"The first training run, on the naive split, reached "
         f"{R.pct(R.naive_best_val) if R.naive_best_val else 'about 99.7%'} "
         "validation accuracy, which is not a believable number for this task. "
         "Rather than report it, the corpus was audited.")

    para(document,
         f"Hashing found nothing: all {R.n(R.audit['corpus_size'])} files are "
         "byte-distinct, so conventional duplicate detection reports a clean "
         "dataset. The problem was visible only in feature space. Embedding "
         "every image with the frozen backbone and measuring each test image "
         f"against its nearest training neighbour showed {R.pct(R.naive_leak)} "
         f"of test images within cosine {R.audit['similarity_threshold']} of "
         "some training image, and a median nearest-neighbour similarity of "
         f"{R.naive_median_nn:.3f}. The corpus is an augmented set, and "
         "variants derived from the same original photograph were being "
         "separated across the split.")

    para(document,
         "The remedy was to split by group rather than by image. Pairs above "
         "cosine 0.95 were joined, connected components collapsed with "
         "union-find, and whole groups assigned to splits with stratification "
         f"preserved. The {R.n(R.audit['corpus_size'])} images resolve into "
         f"{R.n(R.audit['n_groups'])} groups, the largest containing "
         f"{R.audit['largest_group']} images. Residual leakage afterwards is "
         f"{R.pct(R.audit['residual_test_leakage_fraction'], 2)}.")

    _sizes = R.audit["group_size_distribution"]
    table(document,
          ["Group size"] + list(_sizes.keys()),
          [["Groups"] + [R.n(v) for v in _sizes.values()]],
          "Table 4",
          f"Near-duplicate group sizes at cosine {R.audit['similarity_threshold']}. "
          "Most images are independent, but "
          f"{R.n(sum(v for k, v in _sizes.items() if int(k) > 1))} groups contain "
          "variants that a naive split would have scattered across training "
          "and test.",
          widths=[2.6] + [1.25] * 10, font_size=8.5)

    para(document,
         f"The retrained model scored {R.pct(R.stage2_best_val)} on validation, "
         "essentially unchanged. Leakage was therefore not the explanation, and "
         "the honest conclusion is that the "
         "task itself is easy. Chapter 5 takes that up, because it changes what "
         "the headline accuracy is evidence for. The audit was still worth doing: "
         "without it the figure would have rested on an assumption nobody had "
         "checked.")

    heading(document, "A labelling anomaly", 3)

    para(document,
         "The audit turned up a second oddity. The 734 images labelled as fresh "
         "apples carry filenames beginning FreshOrange, which suggests either "
         "mislabelling or duplicated files. Comparing group centroids in "
         "embedding space settled it: the fresh-apple centroid sits closer to "
         f"rotten-apple ({R.anomaly['fresh_apple_vs_rotten_apple']:.3f}) than to "
         f"fresh-orange ({R.anomaly['fresh_apple_vs_fresh_orange']:.3f}), and the "
         "two file "
         "sets are disjoint. The images are apples; only the filenames are "
         "wrong. The metadata column was trusted and the filenames disregarded.")

    # ==================================================================
    heading(document, "Pairing images with sensor readings", 2)

    para(document,
         "No public dataset pairs photographs of spoiling food with synchronised "
         "sensor measurements, so the paired corpus is constructed. This is the "
         "most consequential methodological decision in the thesis and it is set "
         "out in full.")

    para(document,
         "Each generated sample gets a commodity, a fridge drawn from the "
         "population above, and a target spoilage extent sampled uniformly on "
         "(0, 1). The storage age producing that extent is found by integrating "
         "the trajectory once and scanning for the crossing. Sampling extent "
         "rather than age matters: extent is sigmoid in time, so uniform ages "
         "pile up in the saturated tail. The first version did exactly that and "
         "produced 69% spoiled samples, starving the other two classes.")

    para(document,
         "The image is then chosen to match how the item would look at that "
         "extent, and this is where the design encodes its central hypothesis. "
         "Visible change lags physical change: an item can be well advanced "
         "microbiologically and still photograph as sound. The model represents "
         "that with a per-commodity visual threshold, set above the marginal "
         "boundary so the marginal band straddles it. Firm-skinned commodities "
         "hide spoilage longer, so pomegranate sits at 0.64 and strawberry at "
         "0.50.")

    para(document,
         "The consequence is deliberate and it is the point of the experiment. "
         "Marginal items draw images from both the fresh and the rotten pool, so "
         "appearance alone cannot separate marginal from fresh. A vision-only "
         "model therefore has an accuracy ceiling well below 100% by "
         "construction, and whether the sensor channel recovers the difference "
         "is precisely what the ablation tests.")

    rich_para(document, [
        ("This must be read as a constraint on the results. ", "b"),
        ("The images and their fresh/rotten labels are real. Every numeric "
         "sensor feature is generated by the physical model, and the "
         "visual-lag assumption is an assumption, not a measurement. Three-state "
         "accuracies therefore measure whether the architecture can exploit "
         "sensor information under a stated model. They are not measurements of "
         "how the system would perform on a real shelf, and Chapter 5 does not "
         "present them as such.", ""),
    ])

    # ==================================================================
    heading(document, "Model architecture and training", 2)

    figure(document, f"{FIG}/model_diagram.png", "Figure 4",
           "The late-fusion classifier. The visual embedding is projected from "
           "1280 to 64 dimensions before the join, so that the two branches "
           "enter the fusion layers at comparable width.", width_cm=15.0)

    heading(document, "Visual branch", 3)

    para(document,
         "MobileNetV2 pretrained on ImageNet supplies the backbone, pooled to a "
         "1280-dimensional embedding. Training is the standard two-stage "
         "transfer-learning recipe. Stage one fits only the classifier head with "
         "the backbone frozen; because a frozen backbone produces identical "
         "outputs every epoch, embeddings are computed once and cached, turning "
         "an hour-long job into four seconds with numerically identical results. "
         "Stage two unfreezes the top 40 layers and fine-tunes at a tenth of the "
         "learning rate.")

    para(document,
         "Batch normalisation layers stay frozen throughout stage two. Updating "
         "their running statistics on small batches from a new domain is a "
         "well-known way to make fine-tuning diverge.")

    para(document,
         "Stage two initially trained to exactly chance — around 51% accuracy on "
         f"a balanced binary task — while stage one had reached "
         f"{R.pct(R.stage1_final_val)}. The cause "
         "was double preprocessing: MobileNetV2 normalisation was applied both "
         "inside the model and again in the input pipeline, mapping every input "
         "into a band roughly 0.008 wide. The fix was to preprocess in exactly "
         "one place, and a guard now evaluates the assembled model before "
         "fine-tuning begins and raises if it does not match what stage one "
         "achieved.")

    code_block(document,
               '''# Sanity check before any fine-tuning: with the stage-1 head transferred,
# the assembled model must already score what stage 1 scored. If it does
# not, the image pipeline disagrees with the embedding pipeline, and
# fine-tuning from here would be training on mangled input.
pre = model.evaluate(val_ds, verbose=0, return_dict=True)
if pre["accuracy"] < 0.90:
    raise RuntimeError(
        f"Assembled model scores {pre['accuracy']:.3f} on validation but "
        f"stage 1 scored {h1.history['val_accuracy'][-1]:.3f}. The image "
        "pipeline and the embedding pipeline are not equivalent."
    )''',
               "Listing 3",
               "Guard against pipeline mismatch between the two training stages. "
               "Added after a silent double-normalisation bug trained the model "
               "to chance.")

    heading(document, "Fusion branch and the width problem", 3)

    para(document,
         "The sensor branch takes five features — ethanol, ammonia, temperature, "
         "humidity and mass delta — through dense layers of 64 and 32 units with "
         "batch normalisation and dropout. Features are standardised using "
         "statistics computed on the training split alone; fitting the scaler "
         "across all splits leaks test statistics, and while the effect is small "
         "for five features it is free to avoid.")

    para(document,
         "Naive late fusion concatenates the 1280-dimensional visual embedding "
         "with the 32-dimensional sensor embedding. That gives the image branch "
         "forty times the width, and the first fusion layer allocates capacity "
         "accordingly. Since the visual features are the weaker signal in this "
         "task by construction, the raw concatenation trained to a lower "
         "accuracy than the sensor branch reached alone.")

    para(document,
         "Projecting the visual embedding to 64 dimensions before the join lets "
         "both modalities compete on comparable terms. Chapter 5 reports both "
         "variants, because the failure is more instructive than the fix.")

    heading(document, "Ablation baselines", 3)

    para(document,
         "Three additional models are trained on identical splits with identical "
         "hyperparameters: vision-only over the embedding, sensor-only over the "
         "five features, and the raw-concatenation fusion variant. Without these "
         "the fusion accuracy would be a number with nothing to compare against, "
         "and the question of whether the gas sensors earn their place in the "
         "bill of materials could not be asked.")

    # ==================================================================
    heading(document, "Software implementation", 2)

    heading(document, "Design decisions", 3)

    para(document,
         "Three structural choices in the software are worth setting out, "
         "because each was made against a plausible alternative.")

    para(document,
         "Dependencies are injected rather than imported. The inference service "
         "receives a sensor backend and a session factory; the Flask application "
         "receives a database path and an optional inference service. The "
         "alternative — modules importing their collaborators directly — is "
         "shorter to write and makes the system untestable, because there is "
         "then no way to run the API without a trained model or the acquisition "
         "loop without hardware. The test suite runs in nine seconds precisely "
         "because nothing has to be real.")

    para(document,
         "Failure modes are chosen deliberately rather than inherited. A cycle "
         "that raises does not kill the scheduler thread, because a sensor "
         "throwing once every few days is normal while a monitoring system that "
         "silently stops monitoring is not. A missing camera falls back to the "
         "sensor-only model rather than aborting. A missing model returns a "
         "uniform distribution, which cannot clear the alert confidence floor, "
         "so the system goes quiet instead of guessing. The general principle is "
         "that a degraded system should do less, not do something wrong.")

    para(document,
         "Timestamps are timezone-aware throughout. This looks like fussiness "
         "and is not: a system logging naive local timestamps produces a corrupt "
         "hour of history twice a year at the daylight-saving boundaries, and "
         "the corruption surfaces months later as a freshness trajectory that "
         "goes backwards. Readings are stored in UTC and converted only for "
         "display.")

    heading(document, "Acquisition loop", 3)

    para(document,
         "Measurement runs on a background thread under APScheduler at a "
         "thirty-minute interval, chosen to match the MQ heater duty cycle and "
         "the power budget rather than being an arbitrary round number. The job "
         "is configured so that only one instance can run at a time and "
         "overdue runs coalesce.")

    para(document,
         "That configuration matters more than it appears. A cycle that "
         "overruns its slot must not have a second copy started on top of it: "
         "two threads reading the same load cell produce a reading that belongs "
         "to neither, and on real hardware the gas heaters would be commanded on "
         "and off simultaneously. The default scheduler behaviour permits "
         "exactly that.")

    heading(document, "Database", 3)

    figure(document, f"{FIG}/er_diagram.png", "Figure 5",
           "Database schema, generated from the SQLAlchemy metadata. Sensor "
           "readings key on slot rather than on item, so a slot's history "
           "survives the item being eaten.", width_cm=15.0)

    para(document,
         "SQLite was chosen for zero-configuration deployment; the write volume "
         "here is around 300 rows a day, far below where its single-writer limit "
         "matters. Write-ahead logging is enabled so the acquisition thread can "
         "write while a request reads, and foreign keys are enabled explicitly, "
         "since SQLite ignores them by default and the declared cascades would "
         "otherwise be inert.")

    para(document,
         "The fourth table is the one that makes the system evaluable. "
         "Consumption events record whether an item was eaten or binned and how "
         "long before that the first spoilage alert fired. Without it there is "
         "no way to establish whether the predictions were any good; a system "
         "that logs only its own predictions can never be shown to be wrong.")

    heading(document, "Inference service", 3)

    figure(document, f"{FIG}/sequence.png", "Figure 6",
           "One measurement cycle. The interface polls rather than being pushed "
           "to, because data changes every thirty minutes and holding a socket "
           "open on a mostly-idle device buys nothing.", width_cm=15.5)

    para(document,
         "A cycle warms the gas sensors, reads every slot, stores the raw "
         "readings, embeds the image, classifies, computes a freshness score and "
         "a days-remaining estimate, and stores the prediction with its "
         "measured latency.")

    para(document,
         "When no camera is available — the simulated backend, a hardware "
         "failure, or the user disabling it for privacy — the service falls back "
         "to the sensor-only model rather than refusing to run. With no model "
         "loaded at all it returns a uniform distribution, which cannot clear "
         "the alert confidence floor, so the system stays silent when it knows "
         "nothing. That is the correct failure mode: a monitoring system should "
         "go quiet rather than start guessing.")

    heading(document, "Freshness score and alerting", 3)

    para(document,
         "The three class probabilities are collapsed into a 0-100 score as the "
         "expected freshness under the predicted distribution, weighting fresh "
         "at 100, marginal at 50 and spoiled at 0. Using the whole distribution "
         "rather than the top class means an item the model is torn between "
         "fresh and spoiled lands mid-range instead of flipping between extremes "
         "as the argmax changes.")

    para(document,
         "Days remaining is a least-squares line through the recent score "
         "history, extended to the use-soon threshold. A line is a poor "
         "description of a spoilage curve over its full span, but over the last "
         "day or two of samples it is a reasonable local approximation, and "
         "fitting a sigmoid to six noisy points is worse. When the trend is flat "
         "or rising the function returns nothing rather than an invented number.")

    para(document,
         "Three mechanisms hold the notification rate down. Alerts fire on state "
         "transitions, never on states, so an item that is spoiled today and "
         "still spoiled tomorrow generates one alert. Predictions must clear a "
         "confidence floor of 0.55 on the top class. And the user can snooze an "
         "item for 24 hours or override the model entirely, after which the "
         "system stops commenting on that item.")

    heading(document, "REST API and interface", 3)

    para(document,
         "The API exposes eleven endpoints for listing and registering items, "
         "retrieving history, recording consumption, snoozing, overriding, "
         "reading sensor history, fetching alerts and statistics, and triggering "
         "a cycle. Authentication is a bearer token generated on first run. The "
         "comparison is constant-time, since a naive equality check leaks the "
         "token a byte at a time to anything that can measure response latency.")

    para(document,
         "It is a modest protection, but the device sits on a home network where "
         "anything else on the LAN can reach it, and an unauthenticated API that "
         "reports when the fridge was last opened is a more useful burglary aid "
         "than it first appears.")

    para(document,
         "The interface is a Vue 3 single-page application with Tailwind CSS, "
         "served by Flask from the device and polling every 30 seconds. It is "
         "mobile-first, since the realistic use is glancing at a phone before "
         "going shopping.")

    table(document,
          ["Method and path", "Purpose"],
          [["GET /api/health", "Liveness and whether a model is loaded"],
           ["GET /api/items", "All active items with current state and history"],
           ["POST /api/items", "Register an item in a slot"],
           ["GET /api/items/<id>", "One item with predictions and slot readings"],
           ["POST /api/items/<id>/consume", "Record that it was eaten or binned"],
           ["POST /api/items/<id>/snooze", "Silence its alerts for 24 hours"],
           ["POST /api/items/<id>/override", "Set the state manually"],
           ["GET /api/readings/<slot>", "Recent sensor readings for a slot"],
           ["GET /api/alerts", "Currently active alerts"],
           ["GET /api/stats", "Waste-tracking summary"],
           ["POST /api/cycle", "Run one measurement cycle immediately"]],
          "Table 6",
          "REST API. Every route except health requires a bearer token. "
          "Registering an item into an occupied slot returns 409 rather than "
          "silently replacing what is there.",
          widths=[6.5, 8.0], font_size=9.0)

    para(document,
         "Input validation returns specific errors rather than a generic "
         "rejection: a missing field names the field, a non-numeric mass says "
         "so, and an occupied slot names the item already in it. This is worth "
         "the effort because the API is what a future mobile client or a "
         "researcher's analysis script would talk to, and opaque 400 responses "
         "make that painful.")

    figure(document, f"{FIG}/ui_dashboard.png", "Figure 7",
           "Dashboard from the accelerated demonstration run, captured at a "
           "cycle in which an item had just crossed into a new state so that "
           "the alert banner is visible; on the following cycle it would be "
           "silent again. Each card carries a state badge, a freshness bar, "
           "days remaining, mass and age.", width_cm=15.0)

    para(document,
         "Freshness state is never carried by colour alone. Each card also has a "
         "text badge and a numeric score, so the interface remains readable "
         "under deuteranopia and protanopia. This was a design decision rather "
         "than a tested outcome — no accessibility evaluation was run.")

    figure(document, f"{FIG}/ui_item_detail.png", "Figure 8",
           "Item detail view showing the class probabilities and the freshness "
           "trajectory over the tracked lifetime. The controls record what "
           "actually happened to the item, which is what makes the system "
           "measurable against reality.", width_cm=12.0)

    figure(document, f"{FIG}/ui_mobile.png", "Figure 9",
           "The same dashboard at 390 px. The layout collapses to a single "
           "column; nothing is hidden behind a menu.", width_cm=7.5)

    # ==================================================================
    heading(document, "Edge deployment", 2)

    para(document,
         "Models are converted to TensorFlow Lite in three variants: float32, "
         "float16 and full int8 quantisation. Integer quantisation needs a "
         "representative dataset to calibrate activation ranges; feeding it "
         "random noise produces ranges matching nothing real and quietly "
         "destroys accuracy, so a sample of the actual training split is used. "
         "Each converted model is re-evaluated on the test set, so a size "
         "reduction that costs accuracy cannot pass unnoticed.")

    # ==================================================================
    heading(document, "Privacy, security and power", 2)

    heading(document, "Privacy by architecture", 3)

    para(document,
         "A camera photographing the inside of a refrigerator every thirty "
         "minutes builds a detailed record of a household: what they eat, when "
         "they shop, when they cook, and when nobody is home. That is a "
         "sensitive dataset, and the design treats it as one.")

    para(document,
         "The protection is architectural rather than procedural. Images are "
         "captured, embedded and discarded on the device; no image is "
         "transmitted anywhere. There is no cloud account, no remote endpoint "
         "and no telemetry. The consequence is that a privacy failure would "
         "require someone to be on the local network, rather than requiring a "
         "third party to keep a promise.")

    para(document,
         "The camera can be switched off from the interface. The switch is "
         "honoured by the sensor backend itself — capture_image() returns None "
         "without touching the camera — so no code path above it can "
         "photograph the shelf, and the system degrades to the sensor-only "
         "model rather than refusing to run. Given the "
         "ablation result in Chapter 5, that degraded mode is in fact the more "
         "accurate one under the present evaluation, which is an unexpectedly "
         "comfortable position for a privacy control to be in.")

    para(document,
         "Retention is bounded: at the end of every measurement cycle, sensor "
         "readings older than 90 days and predictions older than 30 days are "
         "deleted, while items and their recorded outcomes are kept because "
         "they are what the evaluation is measured against. A monitoring device "
         "does "
         "not need a permanent record of a household's diet, and keeping one "
         "creates risk without creating value.")

    heading(document, "Security", 3)

    para(document,
         "Authentication is a bearer token generated on first run and compared "
         "in constant time. This is deliberately modest, and its limits should "
         "be stated. It protects against casual access from another device on "
         "the same network. It does not protect against anyone who can read the "
         "token, and the transport is plain HTTP on the local network rather "
         "than TLS, because provisioning certificates for a device with a "
         "local-only hostname is a genuinely awkward problem that a prototype "
         "does not solve well.")

    para(document,
         "A production version would need TLS with a locally-trusted "
         "certificate, per-client credentials and a way to revoke them. These "
         "are noted as missing rather than described as future work, because "
         "they are the minimum a shipping device would require.")

    heading(document, "Power budget", 3)

    para(document,
         "The Raspberry Pi 4 draws roughly 3 to 4 W at idle and somewhat more "
         "under inference load. The two MQ heaters are the other significant "
         "consumer, at around 0.8 W each while powered.")

    para(document,
         "The duty cycle is what makes the total manageable. Inference runs for "
         "about two seconds per thirty-minute cycle, and the gas heaters are "
         "powered only during the warm-up and reading window rather than "
         "continuously — a design choice that trades a 30-second settling delay "
         "for most of the heater energy. The LED strip is lit only for the "
         "exposure, which saves power and, more importantly, avoids warming the "
         "enclosure and biasing the temperature reading.")

    para(document,
         "Total continuous consumption is on the order of 4 to 5 W. Against a "
         "domestic refrigerator drawing 100 to 200 W average, this is a few "
         "percent, and it is a genuine cost that has to be set against any waste "
         "saved. A device that prevents one discarded punnet of strawberries a "
         "week comfortably repays a few watts on embodied-carbon grounds, but "
         "that calculation depends on the device working, which is exactly what "
         "has not yet been demonstrated on real food.")

    heading(document, "Deployment", 3)

    para(document,
         "Deployment to a Raspberry Pi involves installing Raspberry Pi OS "
         "Bookworm 64-bit, enabling SPI and the camera interface, installing the "
         "device-only dependencies listed separately from the main requirements "
         "file, copying the model artefacts, running the calibration procedure "
         "and installing the systemd unit shipped in the repository so the "
         "service starts at boot and restarts on failure.")

    para(document,
         "On the device, tflite-runtime replaces full TensorFlow. It is a "
         "fraction of the size, and all the device does is inference; installing "
         "a training framework on a machine that will never train anything wastes "
         "storage and installation time.")

    # ==================================================================
    heading(document, "Testing", 2)

    para(document,
         f"The suite is {R.tests} tests across {R.test_modules} modules, running "
         "in under ten seconds. Coverage of the runtime modules is between "
         f"{min(R.cov(m)['percent'] for m in _COV_MODULES):.0f}% and "
         f"{max(R.cov(m)['percent'] for m in _COV_MODULES):.0f}%; the one-shot "
         "training scripts are not unit-tested, which pulls the overall figure "
         f"to {R.cov_total:.0f}%.")

    table(document,
          ["Module", "Statements", "Coverage"],
          [[m.replace("freshkeeper/", ""), str(R.cov(m)["statements"]),
            f"{R.cov(m)['percent']:.0f}%"]
           for m in sorted(_COV_MODULES, key=lambda m: -R.cov(m)["percent"])],
          "Table 5",
          "Test coverage of the runtime modules. The Raspberry Pi driver is low "
          "because most of it cannot execute off a Pi; what is tested there is "
          "interface conformance, pin-map consistency and the pure conversion "
          "functions.",
          widths=[7.0, 3.5, 3.5])

    para(document,
         "Several tests exist specifically to prevent a bug from returning. A "
         "subprocess test runs the simulation under two different "
         "PYTHONHASHSEED values and requires identical output, because an "
         "earlier version seeded per-item randomness from Python's hash() of a "
         "string — which the interpreter salts per process — so that the "
         "sensor corpus, and everything trained on it, silently differed on "
         "every run while the documentation claimed exact reproducibility. The "
         "calibration test fails if any growth coefficient drifts from its "
         "published reference. A round-trip test guards the MQ conversion "
         "direction. A mass-delta test asserts that the change is measured "
         "against the registered mass, after an early demo registered a 250 g "
         "punnet against an 18 g simulated berry and produced a −232 g delta "
         "that made every item read as spoiled.")

    para(document,
         "The physics tests check behaviour rather than just values: that warmer "
         "storage spoils faster, that the temperature coefficient is "
         "biologically plausible, that a warm excursion costs shelf life, and "
         "that drier air drives more mass loss. These would catch a model that "
         "produced correct numbers for incorrect reasons.")
