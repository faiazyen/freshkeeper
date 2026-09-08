"""Chapter 3: Literature Review."""

from docx_builder import (
    bullet, figure, heading, numbered, para, reset_numbering, rich_para, table,
)
from results import Results


def build(document) -> None:
    R = Results()
    heading(document, "Literature Review", 1)

    para(document,
         "This chapter covers five bodies of work: the scale and behavioural "
         "causes of household food waste, IoT architectures for food monitoring, "
         "the sensing modalities that carry information about spoilage, machine "
         "learning for freshness classification, and predictive microbiology. "
         "The first four are the obvious ones for a thesis of this type. The "
         "fifth is less commonly cited in the IoT literature and turned out to "
         "matter most, because it supplies the equations that let a simulated "
         "shelf behave like a real one.")

    para(document,
         "Most of the reviewed IoT work is from 2020 onwards, since the hardware "
         "economics changed quickly over that period. The microbiology is older "
         "and does not need to be recent; the Ratkowsky relationship dates from "
         "1982 and has been re-validated many times since.")

    # ------------------------------------------------------------------
    heading(document, "Household food waste: scale and causes", 2)

    para(document,
         "The headline numbers are well established. Roughly a third of food "
         "produced for human consumption is lost or wasted, around 1.3 billion "
         "tonnes annually (Gustavsson et al., 2011; FAO, 2019). The UNEP Food "
         "Waste Index puts household waste at the largest single share of "
         "consumer-stage waste globally (UNEP, 2021), and within the European "
         "Union households account for more than half of total food waste "
         "(Eurostat, 2022).")

    para(document,
         "The behavioural literature is more useful for design purposes than the "
         "tonnage figures, because it explains where an intervention could bite. "
         "Quested et al. (2013) argue that food waste is not a single behaviour "
         "but the residue of many loosely related ones: planning, shopping, "
         "storing, cooking and judging. Their point is that interventions aimed "
         "at a single stage tend to disappoint, because the waste simply "
         "reappears somewhere else in the chain.")

    para(document,
         "Stancu et al. (2016) and Schanes et al. (2018) both identify "
         "over-purchasing and poor stock awareness as consistent drivers, "
         "alongside uncertainty about whether food is still safe. That last "
         "factor is the one a sensing system can address directly. The others "
         "are shopping and planning behaviours, and no fridge sensor changes how "
         "much somebody buys on a Saturday.")

    para(document,
         "Date labelling deserves particular attention because it is the "
         "instrument most consumers rely on and it is widely misunderstood. "
         "Wansink and Wright (2006) documented confusion between date types, "
         "with consumers treating quality indicators as safety deadlines and "
         "discarding edible food accordingly. The label itself is not "
         "misleading; it is answering a different question from the one people "
         "ask it. A best-before date describes a manufacturer's assumption about "
         "storage conditions, with a safety margin. It cannot describe the item "
         "in front of you, because it was printed before that item was stored.")

    para(document,
         "This gap between an assumed storage history and an actual one is the "
         "opening this thesis works in. It is worth being clear about how "
         "narrow the opening is: the system addresses uncertainty at the point "
         "of judging, which is one of several causes, and the literature "
         "suggests it is not the largest one.")

    heading(document, "Policy context", 3)

    para(document,
         "Target 12.3 of the Sustainable Development Goals commits to halving "
         "per-capita global food waste at retail and consumer level by 2030 "
         "(United Nations, 2015). The consumer half of that target is the harder "
         "one, for the reason given above: there is no operator to instruct. "
         "Retail waste responds to margin pressure and regulation; household "
         "waste responds only to what individual people do in their own "
         "kitchens.")

    para(document,
         "This shapes what an intervention has to look like. It has to work "
         "without anyone being paid to operate it, survive contact with people "
         "who did not choose to participate in a study, and produce a benefit "
         "the household perceives rather than one only a researcher can measure. "
         "Those are demanding constraints, and they explain why so much of the "
         "technical literature stops at the prototype stage: the engineering is "
         "the easy part.")

    para(document,
         "It also sets a realistic ceiling on what any single device can claim. "
         "Uncertainty about edibility is one cause among several, and the "
         "behavioural work reviewed above suggests over-purchasing and poor "
         "planning contribute at least as much. A system that resolves the "
         "uncertainty perfectly would still leave those untouched.")

    # ------------------------------------------------------------------
    heading(document, "IoT architectures for food monitoring", 2)

    para(document,
         "The Internet of Things, as Ashton (2009) framed it, is about giving "
         "computers their own means of gathering information rather than relying "
         "on people to type it in. Atzori et al. (2010) set out the layered "
         "architecture that most subsequent work follows: a perception layer of "
         "sensors and actuators, a network layer carrying data, and an "
         "application layer where it is processed and presented.")

    para(document,
         "Food monitoring systems generally adopt that structure. Ahmadzadeh et "
         "al. (2023) review IoT and big-data food waste management models, "
         "algorithms and technologies across every stage from agricultural "
         "production through post-harvest handling, processing and "
         "distribution to consumption, and set out the open challenges. It is "
         "a review rather than a prototype, and it reports no hardware or "
         "accuracy figures of its own. Reading the works it surveys, the "
         "consumer stage appears far less often than retail and supply-chain "
         "applications — an observation of this author's, not a claim the "
         "review makes — and the imbalance is understandable: a supermarket "
         "has an operator with a budget and a measurable return, whereas a "
         "household has neither.")

    para(document,
         "Sonwani et al. (2022) built an Arduino-based prototype with gas, "
         "humidity and temperature sensors, a camera, a Peltier cooling module "
         "and a humidifier, so the system both monitors and actively regulates "
         "the storage environment. An eleven-layer convolutional network "
         "trained on Fruits-360 identifies the type of fruit or vegetable with "
         "95% accuracy; spoilage itself is inferred from the gas, humidity and "
         "temperature readings, not from the image. They tested fifteen of "
         "fifty catalogued produce types and report extending the usable life "
         "of some categories by around two days, with alerts pushed to the "
         "user's phone. Two things carry over to this thesis: the division of "
         "labour, with vision used for identification and the sensor channel "
         "for condition, and the use of Fruits-360 for exactly what it "
         "contains, which is fruit types rather than freshness states.")

    para(document,
         "Nemade et al. (2024) used a NodeMCU microcontroller with MQ2 and MQ4 "
         "methane sensors and a DHT11 temperature and humidity sensor, and a "
         "Random Forest classifier with recursive feature elimination and "
         "M-SMOTE rebalancing, reaching 94.76% accuracy on cooked foods — rice, "
         "bread, samosas and dal — while also predicting remaining shelf life. "
         "There is no camera and no load cell. Their result is worth holding in "
         "mind when reading Chapter 5: a gas-plus-environment classifier with "
         "no visual channel performed well on their data, and the same pattern "
         "appears in this thesis's ablation.")

    heading(document, "Cloud, edge, or both", 3)

    para(document,
         "Where the processing happens is a genuine architectural fork, and most "
         "published prototypes take the cloud branch: the device collects, a "
         "server infers. Shi et al. (2016) set out the general case for the "
         "other branch, arguing that pushing computation towards the data source "
         "reduces latency and bandwidth and improves privacy.")

    para(document,
         "For a fridge camera the privacy argument is the decisive one. A device "
         "that photographs the inside of a refrigerator every thirty minutes and "
         "uploads the images builds a detailed record of a household's diet, "
         "shopping patterns, meal times and periods of absence. That is a "
         "sensitive dataset by any reasonable standard, and the case for "
         "creating it on somebody else's server is weak when the alternative is "
         "available. Edge inference on a Raspberry Pi 4 is fast enough here, as "
         "Chapter 5 shows, so the trade normally made for latency is not even "
         "required.")

    para(document,
         "This thesis therefore runs everything on the device. Nothing leaves "
         "the local network, and the camera can be disabled from the interface. "
         "That is a departure from most of the reviewed prototypes and it is a "
         "deliberate one.")

    # ------------------------------------------------------------------
    heading(document, "Sensing modalities for spoilage", 2)

    para(document,
         "Four modalities recur in the literature, and they carry different, "
         "partly complementary information.")

    heading(document, "Visual inspection", 3)

    para(document,
         "Discolouration, mould, wilting and collapse are all visible, and a "
         "camera captures them cheaply. Visual inspection has one structural "
         "weakness that the literature acknowledges less often than it should: "
         "it detects spoilage at the point where a human would also detect it. "
         "By the time an item looks bad, the user did not need a system to tell "
         "them. The value of a camera lies in noticing an item the user has "
         "forgotten, not in noticing spoilage earlier than they would.")

    para(document,
         "Illumination is the practical difficulty. The same tomato photographs "
         "differently under a fridge bulb, daylight through an open door, and a "
         "dim kitchen at night, and a classifier trained on one distribution "
         "degrades on another. Controlled internal lighting is the standard "
         "remedy and is adopted here.")

    heading(document, "Gas sensing", 3)

    para(document,
         "As organic matter breaks down it releases volatile organic compounds. "
         "Which ones depends on the food and the dominant organisms: ethanol "
         "from fermentation, ammonia and amines from protein breakdown, "
         "hydrogen sulphide from sulphur-containing amino acids, and carbon "
         "dioxide throughout. Metal-oxide semiconductor sensors respond to these "
         "with a change in resistance, and the MQ series provides them for a few "
         "euros each.")

    para(document,
         "The electronic-nose literature is the relevant background. Loutfi et "
         "al. (2015) review the field for food quality applications, and "
         "Sanaeifar et al. (2017) survey early detection of contamination and "
         "defects specifically. Both make the same two points. Sensor arrays can "
         "discriminate spoilage states with useful accuracy, and they detect "
         "change before visual inspection does, because volatile production "
         "begins while the item still looks sound.")

    para(document,
         "That second point is the entire argument for putting gas sensors in "
         "the enclosure. If gas only became informative once the item looked "
         "bad, a camera alone would do.")

    para(document,
         "The limitations are equally consistent across the literature. "
         "Metal-oxide sensors drift as their heaters age, respond to humidity "
         "as well as to the target gas, and are cross-sensitive: an MQ-135 "
         "responds to ammonia, but also to benzene, alcohol and smoke. They "
         "measure the headspace of the whole enclosure rather than any "
         "individual item, so with several foods present the reading is a "
         "mixture. Absolute calibration requires a clean-air reference "
         "resistance that has to be established per device.")

    heading(document, "Mass and moisture loss", 3)

    para(document,
         "Fresh produce loses water continuously in storage, and the rate "
         "depends on the vapour pressure deficit between the item and the air "
         "around it. Kader (2002) documents transpiration rates across "
         "commodities and their relationship to storage quality. Mass loss is "
         "attractive to measure because it is monotonic, cheap to sense with a "
         "load cell and an HX711 amplifier, and independent of the microbial "
         "signal, so it adds information rather than duplicating it.")

    para(document,
         "The awkwardness is practical rather than physical. A load cell "
         "measures what is on it, so removing an item to use half of it "
         "registers as a large sudden mass loss that has nothing to do with "
         "spoilage. Distinguishing consumption from desiccation requires either "
         "user input or a rule about plausible rates.")

    heading(document, "Temperature and humidity", 3)

    para(document,
         "These do not measure spoilage. They measure the conditions that drive "
         "it, which makes them the most valuable channel for prediction rather "
         "than detection. A DHT22 costs about four euros and reports temperature "
         "to roughly ±0.5 °C and relative humidity to ±2%, which is ample given "
         "that the effect being tracked is a several-degree difference between "
         "one refrigerator and another.")

    para(document,
         "Domestic refrigerators do not hold their setpoint. The compressor "
         "cycles between bounds, each door opening admits warm room air, and the "
         "recovery takes tens of minutes. An item therefore experiences a "
         "sawtooth with spikes rather than a constant temperature, and "
         "integrating spoilage over that history gives a different answer from "
         "evaluating it at the mean. This is exactly the information a printed "
         "date cannot contain.")

    # ------------------------------------------------------------------
    heading(document, "Other technological approaches", 2)

    heading(document, "Smart packaging and time-temperature indicators", 3)

    para(document,
         "An alternative to instrumenting the storage space is instrumenting the "
         "food. Time-temperature indicators are labels whose colour changes "
         "irreversibly in response to accumulated thermal exposure, integrating "
         "temperature history in the same way the Ratkowsky model does but "
         "chemically rather than computationally. Taoukis and Labuza (1989) "
         "established the kinetic basis for matching an indicator's activation "
         "energy to the spoilage reaction of a particular product, which is "
         "what makes the colour change meaningful rather than merely "
         "proportional to time.")

    para(document,
         "TTIs have two advantages over anything in this thesis. They travel "
         "with the item through the whole cold chain rather than only observing "
         "it at the last step, and they need no power, no calibration and no "
         "user interface. Their limitation is that they emit exactly one bit at "
         "a threshold: the label has changed or it has not. They cannot report a "
         "trajectory, cannot say how many days are left, and cannot notice that "
         "an item has been forgotten.")

    para(document,
         "Printed gas sensors integrated into packaging have been demonstrated "
         "and would carry richer information, but cost and disposal remain "
         "unresolved at supermarket volumes. A sensor destined for landfill "
         "after one use is a difficult proposition for a technology justified on "
         "environmental grounds.")

    heading(document, "Retail-stage interventions", 3)

    para(document,
         "At the retail stage, dynamic markdown systems reduce waste by adjusting "
         "prices as expiry approaches, and several European chains have deployed "
         "them at scale. These work well because the operator is a business with "
         "an inventory system, a margin motive and staff to act on the output.")

    para(document,
         "They are worth mentioning here mainly as a contrast. The retail "
         "problem is an optimisation problem with a clear objective function. "
         "The household problem is a human-factors problem wearing an "
         "engineering costume, and the reviewed literature consistently "
         "underestimates how much of it is the former.")

    # ------------------------------------------------------------------
    heading(document, "Machine learning for freshness classification", 2)

    heading(document, "Convolutional networks and transfer learning", 3)

    para(document,
         "Convolutional neural networks are the standard tool for image "
         "classification, learning hierarchies of filters from data rather than "
         "relying on hand-designed features. The constraint for this application "
         "is not accuracy but size: the network has to run on an ARM processor "
         "inside a power budget.")

    para(document,
         "MobileNetV2 (Sandler et al., 2018) is designed for exactly that "
         "setting. Depthwise separable convolutions factor a standard "
         "convolution into a per-channel spatial filter followed by a pointwise "
         "combination, cutting parameters and multiply-accumulate operations by "
         "roughly an order of magnitude against a conventional architecture at "
         "comparable ImageNet accuracy. The inverted residual structure with "
         "linear bottlenecks keeps intermediate tensors small, which matters on "
         "a device with limited memory bandwidth.")

    para(document,
         "Training such a network from scratch needs far more labelled data than "
         "any food-freshness corpus provides. Transfer learning is the standard "
         "answer: initialise from weights trained on a large general corpus such "
         "as ImageNet (Deng et al., 2009), then adapt. Pan and Yang (2010) give "
         "the general framework, and Yosinski et al. (2014) show empirically "
         "that early convolutional layers learn broadly reusable features — "
         "edges, textures, colour opponency — while later layers specialise. "
         "This is what justifies freezing the early layers and fine-tuning only "
         "the top, which is the recipe followed in Chapter 4.")

    heading(document, "Choosing an architecture", 3)

    para(document,
         "The candidates for a constrained device fall into a few families. "
         "VGG16 is simple and well understood but carries roughly 138 million "
         "parameters, which rules it out on memory alone. ResNet50 reduced that "
         "to about 25 million while improving accuracy, using residual "
         "connections to make deeper networks trainable, and it remains a "
         "reasonable general-purpose choice where memory is not tight.")

    para(document,
         "The mobile-oriented families go further. MobileNetV1 introduced "
         "depthwise separable convolutions; MobileNetV2 added inverted "
         "residuals with linear bottlenecks, reaching comparable ImageNet "
         "accuracy at around 3.5 million parameters. EfficientNet later showed "
         "that scaling depth, width and resolution together outperforms scaling "
         "any one of them, and its smallest variants are competitive with "
         "MobileNetV2.")

    para(document,
         "MobileNetV2 was selected here for three reasons, in order of weight. "
         "Its parameter count fits comfortably on the target device. Its Keras "
         "implementation and ImageNet weights are available without additional "
         "dependencies, which matters for reproducibility. And it is the "
         "architecture used by the most directly comparable prior work, so a "
         "reader can set the results side by side without wondering whether the "
         "backbone explains the difference.")

    para(document,
         "Accuracy on ImageNet was not a deciding factor. Chapter 5 shows the "
         "visual task here is easy enough that backbone choice is unlikely to "
         "matter, and the interesting variation is in the data rather than the "
         "network.")

    heading(document, "Compression and edge deployment", 3)

    para(document,
         "Deploying a network on constrained hardware usually involves "
         "compression. Post-training quantisation converts floating-point "
         "weights and activations to lower precision, typically 16-bit float or "
         "8-bit integer, reducing model size and often improving latency where "
         "the processor has integer acceleration. Integer quantisation requires "
         "a representative sample of real inputs to calibrate the range of each "
         "activation tensor, and calibrating on unrepresentative data degrades "
         "accuracy in ways that are easy to miss.")

    para(document,
         "Pruning and knowledge distillation are the other standard tools. "
         "Neither was needed here: Chapter 5 shows inference already consumes "
         "about a tenth of a percent of the duty cycle, so compression beyond "
         "float16 buys storage that is not scarce.")

    heading(document, "Data leakage and evaluation integrity", 3)

    para(document,
         "A body of work across machine learning disciplines documents how "
         "readily evaluation protocols overstate performance. The mechanisms "
         "recur: duplicate or near-duplicate samples spanning training and test "
         "splits, preprocessing statistics fitted before splitting, test data "
         "consulted during model selection, and temporal leakage where a split "
         "ignores the order in which data arrived.")

    para(document,
         "Near-duplicate leakage is the mechanism relevant here, and it is "
         "insidious because the obvious check does not detect it. Hashing finds "
         "byte-identical files. It finds nothing when a corpus has been "
         "augmented and the variants of one photograph differ in every byte "
         "while depicting the same object under the same lighting from nearly "
         "the same angle. Detecting that requires comparison in a representation "
         "where perceptual similarity is measurable, which is what the audit in "
         "Chapter 4 does.")

    para(document,
         "The published prototypes reviewed in this chapter report accuracies "
         "without describing any such check. That is not evidence their figures "
         "are wrong. It does mean that neither they nor a reader can tell.")

    heading(document, "Datasets and what they contain", 3)

    para(document,
         "Food image datasets are plentiful; food *spoilage* datasets are not. "
         "Food-101 (Bossard et al., 2014) covers prepared dishes by category, "
         "not condition. Fruits-360 (Mureșan and Oltean, 2018) contains around "
         "90,000 images across 131 classes, but the classes are fruit varieties "
         "photographed on a white background under controlled lighting; it "
         "contains no spoiled examples. An earlier draft of this thesis claimed "
         "otherwise, and checking the dataset's own class listing showed the "
         "claim was wrong.")

    para(document,
         "Researchers working on spoilage therefore assemble their own corpora, "
         "which is why cross-study comparison is difficult. Reported accuracies "
         "cannot be compared meaningfully when each is measured on a different "
         "private dataset of a different difficulty.")

    para(document,
         "There is a deeper issue with the public fresh-versus-rotten datasets "
         "that Chapter 5 returns to. They contain clearly fresh items and "
         "clearly rotten ones, because those are the images a human annotator "
         "can label confidently. The intermediate state — the item that is "
         "physiologically past its best but still looks acceptable — is the case "
         "a prediction system exists to catch, and it is systematically absent "
         "from the data. High accuracy on such a corpus demonstrates that the "
         "easy case is easy.")

    heading(document, "Sensor fusion", 3)

    para(document,
         "Combining modalities can be done early, by concatenating raw inputs, "
         "or late, by letting each branch form its own representation and "
         "joining afterwards. Late fusion is generally preferred when the "
         "modalities differ sharply in dimensionality and scale, which is the "
         "case here: 150,528 pixel values against five scalar readings. "
         "Concatenating those raw would let the pixels dominate entirely.")

    para(document,
         "Chapter 5 reports that late fusion by itself is not sufficient, and "
         "that the width of each branch at the join matters considerably — a "
         "detail the reviewed literature mentions rarely, and one this work "
         "found the hard way.")

    # ------------------------------------------------------------------
    heading(document, "Predictive microbiology", 2)

    para(document,
         "This is the body of work that made the practical part possible, and it "
         "is largely absent from the IoT food-monitoring papers reviewed above. "
         "Predictive microbiology models the growth of microbial populations as "
         "a function of environmental conditions, and it has been used in food "
         "safety for decades (McMeekin et al., 1993).")

    heading(document, "Temperature dependence", 3)

    para(document,
         "Ratkowsky et al. (1982) established that the square root of the "
         "specific growth rate of bacterial cultures is linear in temperature "
         "above a notional minimum:")

    rich_para(document, [("        √μ = b (T − T", "i"), ("min", "i"), (")", "i")],
              justify=False)

    para(document,
         "where μ is the maximum specific growth rate, T is temperature, T"
         "ₘᵢₙ is a notional minimum growth temperature below "
         "which the model predicts no growth, and b is an organism-specific "
         "coefficient. For the psychrotrophic organisms that dominate chilled "
         "produce, principally Pseudomonas species, Tₘᵢₙ falls "
         "between roughly −10 and −8 °C.")

    para(document,
         "The relationship holds well across the suboptimal temperature range, "
         "which is the range a refrigerator operates in. It is what allows a "
         "warm excursion to be converted into an equivalent amount of lost shelf "
         "life rather than merely noted.")

    heading(document, "Population growth over time", 3)

    para(document,
         "Growth follows a sigmoid: a lag phase while organisms adapt, an "
         "exponential phase, then a stationary phase as resources deplete. "
         "Zwietering et al. (1990) reparameterised the Gompertz function so that "
         "its parameters are the quantities a microbiologist measures — the "
         "maximum growth rate, the lag duration and the asymptote — rather than "
         "abstract curve coefficients. Baranyi and Roberts (1994) later "
         "developed a dynamic alternative better suited to changing conditions.")

    para(document,
         "The modified Gompertz form is used in this thesis, with the "
         "temperature history folded in by integrating over the conditions the "
         "item actually experienced rather than evaluating at a single "
         "temperature. Chapter 4 gives the details.")

    heading(document, "Moisture loss", 3)

    para(document,
         "Transpiration is driven by the vapour pressure deficit between the "
         "produce surface and the surrounding air, not by relative humidity "
         "alone. Computing it needs the saturation vapour pressure at the "
         "ambient temperature, for which the Magnus-Tetens form refined by "
         "Alduchov and Eskridge (1996) is accurate to better than 0.4% across "
         "the relevant range. Kader (2002) supplies commodity-specific "
         "transpiration behaviour and the mass-loss thresholds at which produce "
         "becomes visibly shrivelled.")

    heading(document, "Why this matters here", 3)

    para(document,
         "These models make it possible to generate sensor data that is not "
         "arbitrary. A lookup table of plausible-looking numbers would produce "
         "curves that resemble published ones without responding correctly to "
         "anything. A model built from these equations behaves as the physics "
         "does: warm the cabinet and growth accelerates by the right factor, dry "
         "the air and mass loss increases in proportion to the vapour pressure "
         "deficit, and an item that spent three days at 14 °C ends up "
         "measurably worse than an identical one that did not.")

    para(document,
         "Crucially, the model can be checked. Published shelf lives at 4 °C "
         "exist for common commodities, so the calibration is falsifiable: "
         "either the model reproduces them or it does not. Chapter 5 reports how "
         "closely it does.")

    heading(document, "Evaluating under asymmetric cost", 3)

    para(document,
         "Accuracy is the default reported metric and it is close to useless "
         "for this problem, for two reasons that compound.")

    para(document,
         "The first is class balance. A corpus with three roughly equal classes "
         "makes accuracy interpretable, but a deployed system sees mostly fresh "
         "items, because most food in a fridge is fine most of the time. A "
         "classifier that predicted fresh unconditionally would score well on "
         "such a distribution while being worthless. Macro-averaged F1 weights "
         "each class equally regardless of frequency and is the more honest "
         "summary, which is why it is reported alongside accuracy throughout "
         "Chapter 5.")

    para(document,
         "The second is that the two error directions do not cost the same. "
         "Declaring a spoiled item fresh may make someone ill. Declaring a fresh "
         "item spoiled wastes the food the system exists to save. Both are "
         "real costs and they are not equal, so a single figure that averages "
         "over them discards the distinction that matters most.")

    para(document,
         "The standard treatment is to report per-class recall and precision "
         "separately and to name in advance which class carries the asymmetric "
         "cost. Here that is recall on the spoiled class, and it is reported "
         "for every model in Chapter 5. Confusion matrices are given in full "
         "rather than summarised, because the structure of the errors — which "
         "classes get confused with which — carries information that no scalar "
         "preserves.")

    # ------------------------------------------------------------------
    heading(document, "Human factors and alert design", 2)

    para(document,
         "A monitoring system that nobody acts on saves nothing, which makes the "
         "interface part of the engineering rather than decoration on top of it.")

    para(document,
         "Nielsen's usability heuristics (Nielsen, 1994) supply the relevant "
         "principles: visibility of system status, user control and freedom, and "
         "error prevention. The third is the sharpest constraint here. A system "
         "that raises false alarms trains its user to dismiss it, and a "
         "dismissed alert is worse than no alert, because the user has now "
         "stopped checking and believes they are covered.")

    para(document,
         "The applied-psychology literature on alarm fatigue, developed largely "
         "in clinical settings, reaches a consistent conclusion: alert response "
         "degrades with alert frequency, and it degrades fastest when a "
         "meaningful share of alerts turn out to be spurious. The design "
         "implication is to alert on changes rather than states, to require "
         "confidence before interrupting anyone, and to give the user a way to "
         "silence the system without abandoning it. Chapter 4 implements all "
         "three.")

    # ------------------------------------------------------------------
    heading(document, "Comparison of related systems", 2)

    para(document,
         "Table 1 sets the reviewed prototypes beside the present work. The "
         "accuracy column should be read with care, and the note beneath the "
         "table explains why.")

    table(document,
          ["Study", "Sensing", "Model", "Platform", "Processing", "Reported accuracy"],
          [["Sonwani et al. (2022)", "Gas, humidity, temperature; camera; "
            "Peltier cooler and humidifier",
            "11-layer CNN on Fruits-360 for produce type; sensor thresholds "
            "for condition", "Arduino", "Phone alerts",
            "95% (fruit-type identification)"],
           ["Ahmadzadeh et al. (2023)", "Review, whole supply chain",
            "Various", "Various", "Various", "n/a (review)"],
           ["Nemade et al. (2024)", "MQ2/MQ4 methane, DHT11",
            "Random Forest with RFE and M-SMOTE", "NodeMCU", "Not stated",
            "94.76% (cooked foods)"],
           ["Gómez et al. (2008)", "PEN2 electronic nose",
            "PCA and LDA", "Laboratory instrument", "Offline",
            "Storage ages separated only partially"],
           ["**This thesis**", "**Camera, gas, mass, temp/RH (sensors simulated)**",
            "**MobileNetV2 + late fusion, with ablations**", "**Raspberry Pi 4 (design)**",
            "**Fully on-device**",
            f"**{R.pct(R.visual['accuracy'])} binary; {R.pct(R.acc('fusion'))} three-state**"]],
          "Table 1",
          "Reviewed food spoilage monitoring systems. Accuracy figures are not "
          "comparable across rows: each was measured on a different private "
          "dataset of unknown difficulty, under different class definitions. "
          "The column records what each study reported, not a ranking; "
          "Sonwani's figure is for identifying the produce type, not its "
          "condition. The final row is explained in Chapter 5, including why "
          "the binary result is less impressive than it looks and why the "
          "sensor channel being simulated constrains what the three-state "
          "figure means.",
          widths=[3.0, 2.8, 3.0, 2.4, 2.2, 2.6], font_size=8.0)

    # ------------------------------------------------------------------
    heading(document, "Gaps addressed by this work", 2)

    para(document,
         "Five gaps emerge from the review. This thesis addresses four of them "
         "and is honest that it leaves the fifth open.")

    reset_numbering()
    numbered(document,
             "Reproducibility. Most prototypes are described rather than "
             "released. Component lists are partial, pin assignments are absent, "
             "and source code is rarely published, so the results cannot be "
             "checked or built on. This work publishes the complete "
             "implementation, a pin-level wiring design, and a pipeline that "
             "regenerates every figure from raw data with one command.")
    numbered(document,
             "Missing ablations. Studies that combine modalities frequently "
             "report only the combined accuracy, which cannot show whether the "
             "combination helped. Here vision-only and sensor-only baselines are "
             "trained under identical conditions, and the comparison produced a "
             "result that contradicts the design assumption.")
    numbered(document,
             "Unexamined datasets. Reported accuracies are rarely accompanied by "
             "any audit of the corpus they were measured on. Chapter 4 documents "
             "an audit that found near-duplicate leakage invisible to "
             "conventional duplicate checking, and Chapter 5 discusses what the "
             "corrected figure does and does not demonstrate.")
    numbered(document,
             "Neglected human factors. Alert behaviour is usually left "
             "unspecified. This work implements transition-triggered alerting "
             "with a confidence floor and snoozing, and tests that logic.")
    numbered(document,
             "Long-term real-world evaluation. No reviewed study measures actual "
             "waste reduction in households over a meaningful period, and "
             "neither does this one. The gap remains open, and closing it needs "
             "instrumented hardware and a longitudinal trial.")

    para(document,
         "The fifth is the one that matters most for the field and it is beyond "
         "the scope of a bachelor thesis. What this work can do is make the "
         "system that such a trial would deploy, and make it inspectable.")
