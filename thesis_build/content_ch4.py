"""Chapter 4: Practical Part."""

from docx_builder import (
    code_block, figure, heading, para, rich_para, table,
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
         "This chapter describes what was built. It follows the order in which "
         "the system was built. That is also the order in which each part "
         "became testable. The physical model came first, then the sensing "
         "layer on top of it, then the data, then the models, then the "
         "software that connects them.")

    para(document,
         f"The complete implementation is {R.n(R.loc)} lines of Python across "
         f"{R.files} tracked files, with {R.tests} automated tests. The listings "
         "in this chapter are extracts. Appendix A has the main modules in full "
         "and Appendix B gives the repository layout. The complete source is "
         "public at https://github.com/faiazyen/freshkeeper.")

    # ==================================================================
    heading(document, "System architecture", 2)

    para(document,
         "The system follows the three layer structure that is standard in IoT "
         "work (Atzori et al., 2010), with one difference. The network layer "
         "carries data between parts on the same board, not to a remote "
         "server, because all processing is local.")

    figure(document, f"{FIG}/architecture.png", "Figure 1",
           "System architecture. Sensors feed an acquisition scheduler running "
           "on a thirty minute cycle. A frozen MobileNetV2 backbone turns each "
           "image into an embedding, which the fusion head classifies together "
           "with five sensor features. Results reach the user through a REST "
           "API and a web interface served from the device.", width_cm=15.5)

    para(document,
         "The perception layer is a camera, two gas sensors, a temperature and "
         "humidity sensor and one load cell per shelf slot. The processing "
         "layer schedules measurements, converts analogue signals, runs the "
         "model and writes to the database. The application layer is the API, "
         "the alert engine and the interface.")

    para(document,
         "One design decision should be stated early, and that is the sensor abstraction boundary. Nothing above the hardware layer imports a GPIO library. "
         "Everything talks to an interface with two implementations behind it. "
         "One drives real hardware. The other generates readings from the "
         "physical model. This is what lets the whole system (the API, the "
         "alert logic, the inference service, the test suite) run on a laptop "
         "with nothing plugged in. Moving to real hardware then changes one line of configuration and leaves the code untouched.")

    # ==================================================================
    heading(document, "Hardware design", 2)

    heading(document, "Component selection", 3)

    para(document,
         "Parts were chosen for cost, availability and the existence of mature "
         "Python libraries. Table 2 lists the bill of materials.")

    table(document,
          ["Component", "Part", "Purpose", "Cost (EUR)"],
          [["Single board computer", "Raspberry Pi 4 Model B, 4 GB",
            "Inference host, web server, acquisition", "55"],
           ["Camera", "Raspberry Pi Camera Module 3", "Visual inspection", "28"],
           ["Gas sensor 1", "MQ-135 module", "Ammonia and related VOCs", "4"],
           ["Gas sensor 2", "MQ-3 module", "Ethanol", "4"],
           ["Environment", "DHT22 (AM2302)", "Temperature and humidity", "4"],
           ["Mass", "HX711 amplifier + 5 kg load cell", "Per slot mass", "8"],
           ["ADC", "MCP3008, 8 channel 10 bit", "Analogue gas sensors to SPI", "3"],
           ["Illumination", "5 V LED strip, 50 cm", "Consistent lighting", "5"],
           ["Storage", "64 GB Class 10 microSD", "OS and database", "12"],
           ["Power", "Official 5 V / 3 A supply", "Power delivery", "10"],
           ["Enclosure", "3D printed PLA", "Housing", "6"],
           ["Wiring", "Jumpers, resistors, capacitors, breadboard", "Connections", "8"],
           ["**Total**", "", "", "**147**"]],
          "Table 2",
          "Bill of materials with approximate shop prices at the time of "
          "writing. The total is similar to a mid range kitchen appliance and "
          "well below commercial smart fridge add ons.",
          widths=[4.0, 5.2, 4.6, 2.2])

    para(document,
         "Two choices need a reason. The Raspberry Pi 4 was chosen over the "
         "cheaper Pi Zero 2 W because the visual backbone dominates inference "
         "cost. Chapter 5 shows that even on the Pi 4 the backbone is 92% of "
         "the per item time. The MCP3008 is a required part. The "
         "Raspberry Pi has no analogue input at all, and the MQ sensors are "
         "analogue, so without an external converter there is no gas channel.")

    heading(document, "Wiring", 3)

    para(document,
         "Figure 2 gives the pin level design. The pin numbers in the figure "
         "are imported from the driver module, not typed into the diagram, so "
         "the two cannot disagree.")

    figure(document, f"{FIG}/wiring.png", "Figure 2",
           "Sensor wiring in BCM pin numbering. The DHT22 uses a single wire "
           "protocol with a pull up. The HX711 is bit banged over two pins. "
           "Both gas sensors reach the Pi through the MCP3008 over SPI0 via a "
           "resistive divider. The LED strip and the gas heater supply are each "
           "switched by a MOSFET, not driven from a GPIO pin.", width_cm=15.5)

    para(document,
         "Three details in this design are not obvious. I record them because "
         "they are the kind of thing that costs an afternoon.")

    para(document,
         "The LED strip is switched through a 2N7000 N-channel MOSFET, not "
         "driven from a GPIO pin. A Raspberry Pi pin can safely give about 16 "
         "mA, and a 50 cm strip wants much more than that. If you drive it "
         "directly, the pin gets damaged.")

    para(document,
         "The MQ sensors need a 5 V heater supply, but the MCP3008 input must "
         "stay below 3.3 V. So the sensor output is divided by 0.66 before it "
         "reaches the converter, and the driver scales the reading back up "
         "before applying the resistance formula. An earlier version of the "
         "driver missed that step and would have reported every resistance too "
         "high by the divider ratio. No test could catch that without "
         "hardware, which is why it is recorded here.")

    para(document,
         "The heater supply for both gas sensors is switched through a logic "
         "level MOSFET on GPIO 17, so the heaters use power only during the "
         "measurement window. The driver switches them on at the start of a "
         "cycle, waits 30 seconds for the elements to settle, reads every slot, "
         "and switches them off again. This happens in a finally block, so a "
         "sensor fault in the middle of a cycle cannot leave them on.")

    heading(document, "Enclosure", 3)

    para(document,
         "The sensing head is designed to sit inside the fridge in a 3D printed "
         "PLA box of about 15 by 10 by 8 cm, small enough to use part of one "
         "shelf. It has a clear front panel for the camera, ventilation slots so "
         "the gas sensors sample the fridge air and not their own pocket of "
         "air, a platform above each load cell, and a cable channel.")

    para(document,
         "Two needs conflict here and the solution is a compromise. The gas "
         "sensors want air exchange with the fridge, so what they measure "
         "reflects the shelf. The camera wants controlled, repeatable light, "
         "which argues for closing the imaging space. Ventilation slots placed "
         "away from the camera's view give both, imperfectly.")

    para(document,
         "The Raspberry Pi itself can sit outside the fridge with extension "
         "cables through the door seal. This is the better arrangement. The "
         "board gives off about 4 W of heat, and putting a 4 W heater inside a "
         "fridge both wastes energy and biases the temperature reading the "
         "whole system depends on. Cables through a door seal are their own "
         "compromise. A real product would use an internal battery with "
         "wireless data instead.")

    heading(document, "Sensor calibration", 3)

    para(document,
         "Three of the four sensing channels need calibration before their "
         "readings mean anything in absolute terms. The procedure is given "
         "here because leaving it out is a common gap in the prototypes "
         "reviewed in Chapter 3.")

    para(document,
         "The MQ sensors report a resistance ratio against a clean air "
         "reference R₀. Without that reference the datasheet power law has "
         "nothing to hold on to. To find it, the heater runs for 24 to 48 hours "
         "to settle the element, then the resistance in clean air at known "
         "temperature and humidity is recorded. R₀ drifts as the element ages, "
         "so the design stores it in configuration and expects it to be "
         "measured again from time to time. The simulation models that drift "
         "at 0.4% per day.")

    para(document,
         "The load cell needs two constants: an offset, recorded with the "
         "platform empty, and a scale factor in counts per gram, found by "
         "placing a known mass and dividing. Both are per device and per cell, "
         "because load cells differ in sensitivity and the amplifier gain is "
         "not identical between boards.")

    para(document,
         "The DHT22 is calibrated in the factory and needs nothing, which is a "
         "big part of why it was chosen over a cheaper analogue thermistor.")

    para(document,
         "The camera needs a region of interest per slot. The camera "
         "photographs the whole shelf, and each slot's crop box is recorded "
         "at setup so that single item images can be cut from one exposure. "
         "This is manual configuration, and getting it wrong means "
         "classifying the wrong item. That is a real weakness of the design, "
         "and an automatic segmentation step would remove it.")

    heading(document, "Driver implementation", 3)

    para(document,
         "The Raspberry Pi driver is written and complete. The test suite "
         "checks its interface, its pin map, the divider correction and its "
         "pure conversion functions. It also checks that the heaters go off "
         "even when a read fails. Its readings have not been checked against "
         "instruments, "
         "and the module's own documentation says so, so that nobody reading "
         "the code mistakes it for a tested part.")

    para(document,
         "The HX711 has no standard bus and must be bit banged, which is the "
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
               "Bit banged HX711 read. The 25th clock pulse selects channel A at "
               "gain 128 for the next conversion. Leaving it out silently "
               "switches the amplifier to a different channel.")

    # ==================================================================
    heading(document, "The physical spoilage model", 2)

    para(document,
         "This module is the foundation the simulated sensing layer stands on, "
         "and it is the part of the practical work with the most scientific "
         "content. Each function implements a published model and names its "
         "source.")

    heading(document, "Temperature dependent growth", 3)

    para(document,
         "The Ratkowsky square root relationship gives the growth rate of the "
         "spoilage microbes as a function of temperature. Below the notional "
         "minimum the code returns zero and not a negative rate, which is what "
         "freezing does in practice:")

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
               "Ratkowsky growth rate. The warning in the docstring is not "
               "decoration. The log basis mismatch it describes was a real bug "
               "in an early version, and a regression test now guards it.")

    para(document,
         "That comment records a real bug. The first implementation passed the "
         "Ratkowsky rate, which is on a natural log basis, straight into a "
         "Gompertz function that expects log₁₀ units. Every shelf life came "
         "out 2.3 times too short. Strawberries spoiled in 50 hours at 4 °C. "
         "The curves looked completely believable until they were compared "
         "with published values. A calibration test now fails if the "
         "conversion is removed.")

    heading(document, "Population growth", 3)

    para(document,
         "Growth over time follows the modified Gompertz function in the "
         "Zwietering et al. (1990) form, which returns the log₁₀ increase of "
         "the population above its starting level. Temperature history is "
         "included by adding up effective time. At each step the current rate "
         "is compared with the rate at a 4 °C reference, and the elapsed time "
         "is credited in that proportion. So an hour at 12 °C moves the item "
         "further than an hour at 4 °C by exactly the ratio the Ratkowsky "
         "model predicts.")

    para(document,
         "This is what makes the model depend on the path, and path dependence "
         "is the whole argument for measuring conditions instead of trusting a "
         "printed date. Two items of the same age, one of which spent three "
         "days at 14 °C, end up in measurably different states.")

    heading(document, "Moisture loss", 3)

    para(document,
         "Mass loss is driven by the vapour pressure deficit, computed from the "
         "Magnus-Tetens saturation vapour pressure (Alduchov and Eskridge, "
         "1996), multiplied by a transpiration coefficient for each commodity. "
         "Relative humidity alone is not enough, because the same relative "
         "humidity at different temperatures means different deficits.")

    heading(document, "Combining the two", 3)

    para(document,
         "Spoilage extent is a number between 0 and 1 that combines microbial "
         "load and drying. The two are combined by taking whichever is further "
         "along, not by averaging them, because either one alone makes an item "
         "inedible. A cucumber that has gone rubbery is not saved by a low "
         "bacterial count. Extent maps onto the three reported states at 0.35 "
         "and 0.70.")

    heading(document, "Calibration", 3)

    para(document,
         "Every growth coefficient was solved backwards from a published fridge "
         "shelf life at 4 °C and 85% relative humidity, not chosen to look "
         "reasonable. This makes the model checkable, and a parametrised test "
         "asserts the match to within 5%. Chapter 5 reports the agreement "
         "achieved.")

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
          "Model parameters per commodity. The eight commodities are the ones "
          "labelled in the image dataset, so the visual and sensor branches "
          "describe the same foods. Transpiration coefficients are the fraction "
          "of mass lost per hour per kPa of vapour pressure deficit.",
          widths=[3.2, 2.6, 3.0, 3.4, 3.6])

    # ==================================================================
    heading(document, "Sensor abstraction and simulation", 2)

    para(document,
         "The simulated backend is not a stub that returns fixed values. Each "
         "slot holds an item with a commodity and an age. Every read integrates "
         "the spoilage model over the conditions that slot has seen and then "
         "converts the result into the signal a real sensor would produce.")

    heading(document, "Refrigerator thermal model", 3)

    para(document,
         "A real fridge does not hold its set temperature, and simulating one "
         "that does would remove the very thing the system exists to detect. "
         "The thermal model has a compressor cycling between limits, door "
         "openings drawn from a Poisson process, and exponential recovery "
         "afterwards. Different households are modelled as different fridges: "
         "set points from 2.5 to 7.5 °C and door openings from 6 to 24 per "
         "day, sampled with weights when generating training data.")

    para(document,
         "The first implementation summed the effect of every past door "
         "opening at every time step, which is quadratic. A 60 day pomegranate "
         "trajectory took minutes, and the corpus generator needs thousands of "
         "them. Because the effects decay exponentially, the total can be "
         "carried forward with one multiplication per step. The same 180 day "
         "series now takes 8 milliseconds.")

    heading(document, "Sensor signal chain", 3)

    para(document,
         "Simulated readings pass through the transfer functions of the real "
         "parts instead of being reported as clean values. Concentration "
         "becomes a resistance ratio through a power law. Its coefficients "
         "were digitised from the datasheet sensitivity curves by the open "
         "source MQSensorsLib project (Califa Urquiza, 2019). The Hanwei "
         "datasheets give the curves as graphs, not as equations, so the "
         "coefficients are a community fit and not a manufacturer "
         "specification. The ratio becomes a voltage across the load resistor, "
         "the MCP3008 rounds that to 10 bits, and the firmware inverts the "
         "chain. The round trip loses information on purpose, and that loss is "
         "part of what the classifier has to handle. Gaussian noise is added "
         "at the DHT22's stated accuracy and the HX711's noise floor, and the "
         "MQ baseline drifts slowly upwards as a heater would age.")

    para(document,
         "The direction of the MQ power law caused a real bug. Published fits "
         "give concentration as a function of resistance ratio:")

    rich_para(document, [("        ppm = A · (R", "i"), ("s", "i"), ("/R", "i"),
                         ("0", "i"), (")", "i"), ("−B", "i")], justify=False)

    para(document,
         "The first implementation applied those constants the other way "
         "round. At realistic concentrations that pushed the modelled ratio to "
         "about 10⁻⁴, which saturates a 10 bit converter, and the ethanol "
         "channel silently returned zero for every reading above the low tens "
         "of ppm. The symptom was a spoiled strawberry reporting no ethanol at "
         "all. Both conversion directions are now separate named functions "
         "with a round trip test.")

    figure(document, f"{FIG}/sensor_trajectories.png", "Figure 3",
           "Simulated sensor response over 30 days for three commodities in "
           "one fridge. Volatile production follows microbial growth, mass "
           "falls with transpiration, and the temperature panel shows compressor "
           "cycling with door opening spikes. Strawberry, banana and apple "
           "separate in the order their published shelf lives predict.",
           width_cm=15.5)

    heading(document, "What the simulation does not do", 3)

    para(document,
         "The simulated backend returns None when asked for an image. It "
         "generates the sensor array and never the photograph. Returning a "
         "fake image path would blur exactly the line this thesis needs to "
         "keep sharp. Real images come from the dataset described next.")

    # ==================================================================
    heading(document, "Dataset preparation and audit", 2)

    heading(document, "Source", 3)

    para(document,
         "The image dataset is the augmented configuration of "
         "Project-AgML/fresh_rotten_fruit_classification, released under "
         "CC-BY-4.0. It has 12,335 photos of eight fruits: apple, banana, "
         "grape, guava, jujube, orange, pomegranate and strawberry. Each photo "
         "is labelled fresh or rotten. The classes are nearly balanced, with "
         "6,194 fresh against 6,141 rotten.")

    para(document,
         "Images were decoded, resized to 224 by 224 and split 70/15/15, "
         "stratified on commodity and label together. Stratifying on the label "
         "alone would let most of one fruit into training and most of another "
         "into test, so the test score would measure transfer between fruits "
         "instead of spoilage detection.")

    heading(document, "An audit that changed the results", 3)

    para(document,
         "The first training run, on the naive split, reached "
         f"{R.pct(R.naive_best_val) if R.naive_best_val else 'about 99.7%'} "
         "validation accuracy. That is not a believable number for this task. "
         "Instead of reporting it, I audited the dataset.")

    para(document,
         f"Hashing found nothing. All {R.n(R.audit['corpus_size'])} files are "
         "different at the byte level, so a normal duplicate check reports a "
         "clean dataset. The problem was visible only in feature space. I "
         "embedded every image with the frozen backbone and measured each test "
         "image against its nearest training neighbour. This showed "
         f"{R.pct(R.naive_leak)} of test images within cosine "
         f"{R.audit['similarity_threshold']} of some training image, and a "
         f"median nearest neighbour similarity of {R.naive_median_nn:.3f}. The "
         "dataset is an augmented set, and variants made from the same original "
         "photo were being split between training and test.")

    para(document,
         "The fix was to split by group instead of by image. Pairs above "
         "cosine 0.95 were linked, connected groups were merged with union "
         "find, and whole groups were assigned to splits while keeping the "
         f"stratification. The {R.n(R.audit['corpus_size'])} images resolve into "
         f"{R.n(R.audit['n_groups'])} groups, the largest with "
         f"{R.audit['largest_group']} images. Leakage after the fix is "
         f"{R.pct(R.audit['residual_test_leakage_fraction'], 2)}.")

    _sizes = R.audit["group_size_distribution"]
    table(document,
          ["Group size"] + list(_sizes.keys()),
          [["Groups"] + [R.n(v) for v in _sizes.values()]],
          "Table 4",
          f"Near duplicate group sizes at cosine {R.audit['similarity_threshold']}. "
          "Most images are independent, but "
          f"{R.n(sum(v for k, v in _sizes.items() if int(k) > 1))} groups contain "
          "variants that a naive split would have scattered across training "
          "and test.",
          widths=[2.6] + [1.25] * 10, font_size=8.5)

    para(document,
         f"The retrained model scored {R.pct(R.stage2_best_val)} on validation, "
         "almost the same. So leakage was not the explanation, and the honest "
         "conclusion is that the task itself is easy. Chapter 5 takes that up, "
         "because it changes what the headline accuracy is evidence for. The "
         "audit was still worth doing. Without it the number would rest on an "
         "assumption nobody had checked.")

    heading(document, "A labelling anomaly", 3)

    para(document,
         "The audit found a second strange thing. The 734 images labelled as "
         "fresh apples have file names starting with FreshOrange, which "
         "suggests either wrong labels or duplicated files. Comparing group "
         "centres in embedding space settled it. The fresh apple centre is "
         f"closer to rotten apple ({R.anomaly['fresh_apple_vs_rotten_apple']:.3f}) "
         f"than to fresh orange ({R.anomaly['fresh_apple_vs_fresh_orange']:.3f}), "
         "and the two file sets do not overlap. So the images really are apples "
         "and only the file names are wrong. For this reason I trusted the "
         "metadata column and ignored the file names.")

    # ==================================================================
    heading(document, "Pairing images with sensor readings", 2)

    para(document,
         "No public dataset pairs photos of spoiling food with sensor readings "
         "taken at the same time, so the paired dataset is built. This is the "
         "most important method decision in the thesis, and it is set out in "
         "full.")

    para(document,
         "Each generated sample gets a commodity, a fridge drawn from the "
         "population above, and a target spoilage extent sampled uniformly on "
         "(0, 1). The storage age that produces that extent is found by "
         "integrating the trajectory once and scanning for the crossing. "
         "Sampling extent and not age matters. Extent is S shaped in time, so "
         "uniform ages pile up in the flat end. The first version did exactly "
         "that and produced 69% spoiled samples, starving the other two "
         "classes.")

    para(document,
         "The image is then chosen to match how the item would look at that "
         "extent, and this is where the design encodes its main hypothesis. "
         "Visible change comes later than physical change. An item can be far "
         "along microbiologically and still photograph as fine. The model "
         "represents that with a visual threshold per commodity, set above the "
         "marginal boundary so that the marginal band straddles it. Firm "
         "skinned fruits hide spoilage longer, so pomegranate sits at 0.64 and "
         "strawberry at 0.50.")

    para(document,
         "The consequence is intended and it is the point of the experiment. "
         "Marginal items draw images from both the fresh and the rotten pool, "
         "so appearance alone cannot separate marginal from fresh. A vision "
         "only model therefore has an accuracy ceiling well below 100% by "
         "construction. Whether the sensor channel recovers the difference is "
         "exactly what the baseline comparison tests.")

    rich_para(document, [
        ("This must be read as a limit on the results. ", "b"),
        ("The images and their fresh/rotten labels are real. Every numeric "
         "sensor feature is generated by the physical model, and the visual "
         "lag is an assumption, not a measurement. Three state accuracies "
         "therefore measure whether the architecture can use sensor "
         "information under a stated model. They are not measurements of how "
         "the system would perform on a real shelf, and Chapter 5 does not "
         "present them that way.", ""),
    ])

    # ==================================================================
    heading(document, "Model architecture and training", 2)

    figure(document, f"{FIG}/model_diagram.png", "Figure 4",
           "The late fusion classifier. The visual embedding is projected from "
           "1280 to 64 dimensions before the join, so that the two branches "
           "enter the fusion layers at similar width.", width_cm=15.0)

    heading(document, "Visual branch", 3)

    para(document,
         "MobileNetV2 pretrained on ImageNet is the backbone, pooled to a 1280 "
         "dimensional embedding. Training is the standard two stage transfer "
         "learning recipe. Stage one fits only the classifier head with the "
         "backbone frozen. A frozen backbone gives the same output every "
         "epoch, so the embeddings are computed once and cached, which turns "
         "an hour long job into four seconds with identical results. Stage two "
         "unfreezes the top 40 layers and fine tunes at a tenth of the learning "
         "rate.")

    para(document,
         "Batch normalisation layers stay frozen in stage two. Updating their "
         "running statistics on small batches from a new domain is a well "
         "known way to make fine tuning diverge.")

    para(document,
         "Stage two at first trained to exactly chance, about 51% on a "
         "balanced binary task, while stage one had reached "
         f"{R.pct(R.stage1_final_val)}. The cause was double preprocessing. "
         "MobileNetV2 normalisation was applied both inside the model and again "
         "in the input pipeline, which squeezed every input into a band about "
         "0.008 wide. The fix was to preprocess in exactly one place. A guard "
         "now evaluates the assembled model before fine tuning starts and "
         "raises an error if it does not match what stage one achieved.")

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
               "Guard against a pipeline mismatch between the two training "
               "stages. Added after a silent double normalisation bug trained "
               "the model to chance.")

    heading(document, "Fusion branch and the width problem", 3)

    para(document,
         "The sensor branch takes five features (ethanol, ammonia, "
         "temperature, humidity and mass change) through dense layers of 64 and "
         "32 units with batch normalisation and dropout. Features are "
         "standardised with statistics from the training split only. Fitting "
         "the scaler on all splits leaks test statistics. The effect is small "
         "for five features, but it costs nothing to avoid.")

    para(document,
         "Naive late fusion joins the 1280 dimensional visual embedding with "
         "the 32 dimensional sensor embedding. That gives the image branch "
         "forty times the width, and the first fusion layer gives out capacity "
         "in that proportion. Because the visual features are the weaker "
         "signal in this task by construction, the raw join trained to a lower "
         "accuracy than the sensor branch reached alone.")

    para(document,
         "Projecting the visual embedding down to 64 dimensions before the "
         "join lets both inputs compete on similar terms. Chapter 5 reports "
         "both versions, because the failure teaches more than the fix.")

    heading(document, "Ablation baselines", 3)

    para(document,
         "Three more models are trained on the same splits with the same "
         "settings: vision only over the embedding, sensor only over the five "
         "features, and the raw join fusion version. Without them the fusion "
         "accuracy would be a number with nothing to compare against, and the "
         "question of whether the gas sensors earn their place in the bill of "
         "materials could not be asked.")

    # ==================================================================
    heading(document, "Software implementation", 2)

    heading(document, "Design decisions", 3)

    para(document,
         "Three structural choices in the software are worth explaining, "
         "because each was made against a reasonable alternative.")

    para(document,
         "The code passes dependencies in instead of importing them directly. The inference service "
         "receives a sensor backend and a session factory. The Flask app "
         "receives a database path and an optional inference service. The "
         "alternative, modules importing their collaborators directly, is "
         "shorter to write and makes the system untestable. There would then "
         "be no way to run the API without a trained model, or the acquisition "
         "loop without hardware. The test suite runs in a few seconds exactly "
         "because nothing has to be real.")

    para(document,
         "The code sets its failure modes on purpose instead of taking whatever the libraries do by default. A cycle that "
         "raises an error does not kill the scheduler thread, because a sensor "
         "failing once every few days is normal, while a monitoring system "
         "that silently stops monitoring is not. A missing camera falls back "
         "to the sensor only model instead of stopping. A missing model returns "
         "a uniform distribution, which cannot pass the alert confidence floor, "
         "so the system goes quiet instead of guessing. The general rule is "
         "that a degraded system should do less, not do something wrong.")

    para(document,
         "Timestamps carry a time zone everywhere. This looks like fussiness "
         "and it is not. A system that logs naive local times produces a "
         "corrupt hour of history twice a year at the daylight saving "
         "changes, and the corruption shows up months later as a freshness "
         "curve that goes backwards. Readings are stored in UTC and converted "
         "only for display.")

    heading(document, "Acquisition loop", 3)

    para(document,
         "Measurement runs on a background thread under APScheduler at a "
         "thirty minute interval. The interval matches the MQ heater duty "
         "cycle and the power budget, so it is not just a round number that "
         "was picked at random. The "
         "job is configured so that only one instance can run at a time and "
         "overdue runs are merged.")

    para(document,
         "That configuration matters more than it seems. A cycle that runs "
         "over its slot must not have a second copy started on top of it. Two "
         "threads reading the same load cell produce a reading that belongs to "
         "neither, and on real hardware the gas heaters would be switched on "
         "and off at the same time. The default scheduler behaviour would allow "
         "exactly this to happen.")

    heading(document, "Database", 3)

    figure(document, f"{FIG}/er_diagram.png", "Figure 5",
           "Database schema, generated from the SQLAlchemy metadata. Sensor "
           "readings are keyed on the slot and not on the item, so a slot's "
           "history survives the item being eaten.", width_cm=15.0)

    para(document,
         "SQLite was chosen because it needs no setup. The write volume here is "
         "about 300 rows a day, far below the point where its single writer "
         "limit matters. Write ahead logging is on so the acquisition thread "
         "can write while a request reads. Foreign keys are switched on "
         "explicitly, because SQLite ignores them by default and the declared "
         "cascades would otherwise do nothing.")

    para(document,
         "The fourth table is the one that makes the system measurable. "
         "Consumption events record whether an item was eaten or thrown away, "
         "and how long before that the first spoilage alert fired. Without it "
         "there is no way to know if the predictions were any good. A system "
         "that logs only its own predictions can never be shown to be wrong.")

    heading(document, "Inference service", 3)

    figure(document, f"{FIG}/sequence.png", "Figure 6",
           "One measurement cycle. The interface polls and is not pushed to, "
           "because the data changes every thirty minutes and keeping a socket "
           "open on a mostly idle device gains nothing.", width_cm=15.5)

    para(document,
         "A cycle warms the gas sensors, reads every slot, stores the raw "
         "readings, embeds the image, classifies, computes a freshness score "
         "and a days remaining estimate, and stores the prediction with its "
         "measured latency.")

    para(document,
         "When no camera is available, because of the simulated backend, a "
         "hardware failure, or the user switching it off for privacy, the "
         "service falls back to the sensor only model instead of refusing to "
         "run. With no model loaded at all it returns a uniform distribution, "
         "which cannot pass the alert confidence floor, so the system stays "
         "silent when it knows nothing. That is the right failure mode. A "
         "monitoring system should go quiet, not start guessing.")

    heading(document, "Freshness score and alerting", 3)

    para(document,
         "The three class probabilities are turned into a 0 to 100 score as "
         "the expected freshness under the predicted distribution, with fresh "
         "worth 100, marginal 50 and spoiled 0. Using the whole distribution "
         "and not the top class means an item the model is torn about between "
         "fresh and spoiled lands in the middle instead of jumping between "
         "extremes as the top class changes.")

    para(document,
         "Days remaining is a least squares line through the recent score "
         "history, extended to the use soon threshold. A line is a poor "
         "description of a spoilage curve over its whole length. But over the "
         "last day or two of samples it is a fair local approximation, and "
         "fitting an S curve to six noisy points is worse. When the trend is "
         "flat or rising the function returns nothing instead of an invented "
         "number.")

    para(document,
         "Three mechanisms keep the number of notifications down. Alerts fire "
         "on state transitions, never on states, so an item that is spoiled "
         "today and still spoiled tomorrow produces one alert. Predictions must "
         "pass a confidence floor of 0.55 on the top class. And the user can "
         "snooze an item for 24 hours or override the model completely, after "
         "which the system stops commenting on that item.")

    heading(document, "REST API and interface", 3)

    para(document,
         "The API has endpoints for listing and registering items, reading "
         "history, recording consumption, snoozing, overriding, reading sensor "
         "history, reading alerts and statistics, changing settings and "
         "starting a cycle. Authentication is a bearer token generated on first "
         "run. The comparison is constant time, because a naive equality check "
         "leaks the token one byte at a time to anything that can measure "
         "response time.")

    para(document,
         "It is a modest protection. But the device sits on a home network "
         "where anything else on the LAN can reach it. An open API that "
         "reports when the fridge was last opened is a more useful burglary "
         "aid than it first seems.")

    para(document,
         "The interface is a Vue 3 single page application with Tailwind CSS, "
         "served by Flask from the device and polling every 30 seconds. It is "
         "designed for phones first, because the realistic use is a quick "
         "look before going shopping.")

    table(document,
          ["Method and path", "Purpose"],
          [["GET /api/health", "Liveness and whether a model is loaded"],
           ["GET /api/items", "All active items with current state and history"],
           ["POST /api/items", "Register an item in a slot"],
           ["GET /api/items/<id>", "One item with predictions and slot readings"],
           ["POST /api/items/<id>/consume", "Record that it was eaten or thrown away"],
           ["POST /api/items/<id>/snooze", "Silence its alerts for 24 hours"],
           ["POST /api/items/<id>/override", "Set the state by hand"],
           ["GET /api/readings/<slot>", "Recent sensor readings for a slot"],
           ["GET /api/alerts", "Currently active alerts"],
           ["GET /api/stats", "Waste tracking summary"],
           ["GET, POST /api/settings", "Read or change the camera switch"],
           ["POST /api/cycle", "Run one measurement cycle now"]],
          "Table 6",
          "REST API. Every route except health needs a bearer token. "
          "Registering an item into an occupied slot returns 409 instead of "
          "silently replacing what is there.",
          widths=[6.5, 8.0], font_size=9.0)

    para(document,
         "Input validation returns specific errors and not a generic "
         "rejection. A missing field names the field, a non numeric mass says "
         "so, and an occupied slot names the item already in it. This is worth "
         "the effort because the API is what a future mobile client or a "
         "researcher's script would talk to, and unclear 400 responses make "
         "that painful.")

    figure(document, f"{FIG}/ui_dashboard.png", "Figure 7",
           "Dashboard from the accelerated demonstration run, captured at a "
           "cycle in which an item had just moved into a new state so that the "
           "alert banner is visible. On the next cycle it would be silent "
           "again. Each card has a state badge, a freshness bar, days "
           "remaining, mass and age.", width_cm=15.0)

    para(document,
         "Freshness state is never shown by colour alone. Each card also has a "
         "text badge and a number, so the interface stays readable for people "
         "with red green colour blindness. This was a design decision, not a "
         "tested result. No accessibility evaluation was done.")

    figure(document, f"{FIG}/ui_item_detail.png", "Figure 8",
           "Item detail view with the class probabilities and the freshness "
           "curve over the tracked lifetime. The buttons record what really "
           "happened to the item, which is what makes the system measurable "
           "against reality.", width_cm=12.0)

    figure(document, f"{FIG}/ui_mobile.png", "Figure 9",
           "The same dashboard at 390 px. The layout collapses to one column. "
           "Nothing is hidden behind a menu.", width_cm=7.5)

    # ==================================================================
    heading(document, "Edge deployment", 2)

    para(document,
         "Models are converted to TensorFlow Lite in three versions: float32, "
         "float16 and full int8 quantisation. Integer quantisation needs a "
         "representative dataset to calibrate activation ranges. Feeding it "
         "random noise gives ranges that match nothing real and quietly "
         "destroys accuracy, so a sample of the real training split is used. "
         "Each converted model is evaluated again on the test set, so a size "
         "saving that costs accuracy cannot pass unnoticed.")

    # ==================================================================
    heading(document, "Privacy, security and power", 2)

    heading(document, "Privacy by architecture", 3)

    para(document,
         "A camera photographing the inside of a fridge every thirty minutes "
         "builds a detailed record of a household: what they eat, when they "
         "shop, when they cook, and when nobody is home. This is sensitive "
         "data and the design treats it that way.")

    para(document,
         "The protection is in the structure, not in a procedure. Images are "
         "taken, embedded and deleted on the device. No image is sent "
         "anywhere. There is no cloud account, no remote endpoint and no "
         "telemetry. So a privacy failure would need someone on the local "
         "network, not a third party breaking a promise.")

    para(document,
         "The camera can be switched off from the interface. The switch is "
         "honoured by the sensor backend itself. capture_image() returns None "
         "without touching the camera, so no code above it can photograph the "
         "shelf, and the system falls back to the sensor only model instead of "
         "refusing to run. Given the result in Chapter 5, that fallback mode "
         "is in fact the more accurate one under the present evaluation, which "
         "is an unexpectedly comfortable position for a privacy control.")

    para(document,
         "Retention is limited. At the end of every measurement cycle, sensor "
         "readings older than 90 days and predictions older than 30 days are "
         "deleted. Items and their recorded outcomes are kept, because they "
         "are what the evaluation is measured against. A monitoring device "
         "does not need a permanent record of a household's diet, and keeping "
         "one creates risk without creating value.")

    heading(document, "Security", 3)

    para(document,
         "Authentication is a bearer token generated on first run and compared "
         "in constant time. This is modest on purpose, and its limits should "
         "be stated. It stops casual access from another device on the same "
         "network. It does not stop anyone who can read the token. The "
         "transport is plain HTTP on the local network and not TLS. Providing "
         "certificates for a device with a local only host name is an awkward "
         "problem that a prototype does not solve well.")

    para(document,
         "A real product would need TLS with a locally trusted certificate, "
         "per client credentials and a way to revoke them. These are listed as "
         "missing, not as future work, because they are the minimum a shipped "
         "device would need.")

    heading(document, "Power budget", 3)

    para(document,
         "The Raspberry Pi 4 draws about 3 to 4 W at idle and a bit more under "
         "inference load. The two MQ heaters are the other big consumer, at "
         "about 0.8 W each while powered.")

    para(document,
         "The duty cycle is what keeps the total manageable. Inference runs for "
         "about two seconds per thirty minute cycle, and the gas heaters are "
         "powered only during the warm up and reading window, not all the "
         "time. This trades a 30 second settling delay for most of the heater "
         "energy. The LED strip is on only for the exposure, which saves power "
         "and, more importantly, avoids warming the box and biasing the "
         "temperature reading.")

    para(document,
         "Total continuous consumption is about 4 to 5 W. Against a home "
         "fridge drawing 100 to 200 W on average, this is a few percent, and it "
         "is a real cost that must be set against any food saved. A device "
         "that stops one box of strawberries a week going in the bin easily "
         "repays a few watts in carbon terms. But that calculation depends on "
         "the device working, which is exactly what has not yet been shown on "
         "real food.")

    heading(document, "Deployment", 3)

    para(document,
         "Deploying to a Raspberry Pi takes six steps. Install Raspberry Pi OS "
         "Bookworm 64 bit. Enable SPI and the camera interface. Install the "
         "device only packages, which are listed separately from the main "
         "requirements file. Copy the model files. Run the calibration "
         "procedure. Install the systemd unit shipped in the repository, so "
         "the service starts at boot and restarts on failure.")

    para(document,
         "On the device, tflite-runtime replaces full TensorFlow. It is a "
         "fraction of the size, and all the device does is inference. "
         "Installing a training framework on a machine that will never train "
         "anything wastes storage and time.")

    # ==================================================================
    heading(document, "Running the prototype", 2)

    para(document,
         "The whole pipeline is driven by a Makefile, so a reader can repeat "
         "any stage with one command. The stages run in the order below. Each "
         "one writes its output to a file that the next one reads, and each "
         "one writes a result file in JSON that this document reads.")

    table(document,
          ["Command", "What it does", "Approximate time"],
          [["make venv install", "Creates the Python 3.12 environment and installs the packages", "3 min"],
           ["make data", "Downloads the image dataset, decodes and splits it", "5 min"],
           ["make audit", "Finds near duplicate groups and builds the group aware split", "2 min"],
           ["make embeddings", "Runs the frozen backbone once and caches the embeddings", "1 min"],
           ["make train", "Trains the visual classifier in two stages", "12 min"],
           ["make corpus", "Builds the paired sensor dataset from the physical model", "2 min"],
           ["make fusion", "Trains the fusion model and the two baselines", "1 min"],
           ["make evaluate", "Scores every model on the test split and draws the figures", "1 min"],
           ["make tflite bench", "Converts to TensorFlow Lite and measures inference cost", "2 min"],
           ["make diagrams", "Draws the schematics and the analysis figures", "1 min"],
           ["make demo serve", "Seeds the demonstration database and starts the interface", "1 min"],
           ["make test", "Runs the automated tests", "10 s"],
           ["make all", "Everything above, from raw download to final figures", "about 40 min"]],
          "Table",
          "Pipeline stages. Times are for the development computer with the "
          "machine otherwise idle. A training job running at the same time "
          "slowed the benchmark by more than three times once, which is why the "
          "benchmark should be run alone.",
          widths=[3.6, 8.0, 2.9], font_size=9.0)

    para(document,
         "Two details make repeat runs give the same numbers. First, every "
         "random process has a fixed seed: the split, the simulation, the "
         "weight initialisation and the shuffling during training. Second, the "
         "seeds are derived with a checksum function and not with Python's "
         "built in hash(), because hash() gives a different value for the same "
         "text in every new process. An earlier version used hash() and the "
         "results changed a little on every run without anyone noticing. A "
         "test now runs the simulation in two separate processes and requires "
         "identical output.")

    para(document,
         "The interface can also be tried without the hardware. The demo "
         "database holds twelve simulated days of six items, and the server "
         "shows it on http://127.0.0.1:5055. With the --live flag the server "
         "attaches the simulated backend and runs a new cycle in the "
         "background, so the dashboard changes over time.")

    # ==================================================================
    heading(document, "Testing", 2)

    para(document,
         f"The suite is {R.tests} tests across {R.test_modules} modules, running "
         "in under ten seconds. Coverage of the runtime modules is between "
         f"{min(R.cov(m)['percent'] for m in _COV_MODULES):.0f}% and "
         f"{max(R.cov(m)['percent'] for m in _COV_MODULES):.0f}%. The one off "
         "training scripts are not unit tested, which pulls the overall figure "
         f"to {R.cov_total:.0f}%.")

    table(document,
          ["Module", "Statements", "Coverage"],
          [[m.replace("freshkeeper/", ""), str(R.cov(m)["statements"]),
            f"{R.cov(m)['percent']:.0f}%"]
           for m in sorted(_COV_MODULES, key=lambda m: -R.cov(m)["percent"])],
          "Table 5",
          "Test coverage of the runtime modules. The Raspberry Pi driver is low "
          "because most of it cannot run off a Pi. What is tested there is the "
          "interface, the pin map and the pure conversion functions.",
          widths=[7.0, 3.5, 3.5])

    para(document,
         "Several tests exist only to stop a bug coming back. A subprocess "
         "test runs the simulation under two different PYTHONHASHSEED values "
         "and requires identical output, because an earlier version seeded per "
         "item randomness from Python's hash() of a string, which the "
         "interpreter salts per process. So the sensor corpus, and everything "
         "trained on it, silently differed on every run while the "
         "documentation claimed exact reproducibility. The calibration test "
         "fails if any growth coefficient drifts from its published reference. "
         "A round trip test guards the MQ conversion direction. A mass delta "
         "test checks that the change is measured against the registered "
         "mass. That test exists because an early demo registered a 250 g box "
         "against an 18 g simulated berry. The result was a −232 g delta that "
         "made every item read as spoiled.")

    para(document,
         "The physics tests check how the model behaves, not just what numbers "
         "it gives: that warmer "
         "storage spoils faster, that the temperature coefficient is "
         "biologically believable, that a warm period costs shelf life, and "
         "that drier air causes more mass loss. These would catch a model that "
         "gave correct numbers for wrong reasons.")
