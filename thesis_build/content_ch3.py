"""Chapter 3: Literature Review."""

from docx_builder import (
    heading, numbered, para, reset_numbering, rich_para, table,
)
from results import Results


def build(document) -> None:
    R = Results()
    heading(document, "Literature Review", 1)

    para(document,
         "This chapter covers five areas. They are the size and causes of "
         "household food waste, IoT architectures for food monitoring, the "
         "sensing methods that carry information about spoilage, machine "
         "learning for freshness classification, and predictive microbiology. "
         "The first four "
         "are the obvious ones for a thesis like this. The fifth is cited less "
         "often in IoT papers, but it turned out to matter most, because it "
         "gives the equations that let a simulated shelf behave like a real "
         "one.")

    para(document,
         "Most of the IoT work reviewed is from 2020 onwards, because the "
         "hardware costs changed fast in that period. The microbiology is older "
         "and does not need to be new. The Ratkowsky relationship is from 1982 "
         "and has been confirmed many times since.")

    heading(document, "Household food waste: scale and causes", 2)

    para(document,
         "The main numbers are well known. About one third of food produced for "
         "people is lost or wasted, around 1.3 billion tonnes a year (Gustavsson "
         "et al., 2011; FAO, 2019). The UNEP Food Waste Index says households "
         "are the largest single source of consumer stage waste in the world "
         "(UNEP, 2021). In the European Union, households cause more than half "
         "of all food waste (Eurostat, 2022).")

    para(document,
         "The behaviour research is more useful for design than the tonnage "
         "numbers, because it shows where a tool could help. Quested et al. "
         "(2013) argue that food waste is not one behaviour but the leftover of "
         "many loosely connected ones: planning, shopping, storing, cooking and "
         "judging. Their point is that a tool aimed at one step often "
         "disappoints, because the waste simply moves to another step.")

    para(document,
         "Stancu et al. (2016) and Schanes et al. (2018) both find that buying "
         "too much and not knowing what is in the fridge are steady causes, "
         "together with not being sure if food is still safe. That last cause "
         "is the one a sensing system can address directly. The others are "
         "shopping and planning habits, and no fridge sensor changes how much "
         "somebody buys on a Saturday.")

    para(document,
         "Date labels deserve special attention, because they are the tool most "
         "people rely on and they are widely misunderstood. Wansink and Wright "
         "(2006) showed confusion between date types, with consumers treating "
         "quality dates as safety deadlines and throwing away good food. The "
         "label is not lying. It answers a different question from the one "
         "people ask. A best before date describes a producer's assumption "
         "about storage, plus a safety margin. It cannot describe the item in "
         "front of you, because it was printed before that item was stored.")

    para(document,
         "This gap between assumed and real storage history is the space this "
         "thesis works in. The space is narrow. The system addresses "
         "uncertainty at the moment of judging, which is one of several causes, "
         "and the literature suggests it is not the biggest one.")

    heading(document, "Policy context", 3)

    para(document,
         "Target 12.3 of the Sustainable Development Goals aims to halve food "
         "waste per person at retail and consumer level by 2030 (United "
         "Nations, 2015). The consumer half is the harder half, for the reason "
         "given above: there is no manager to instruct. Retail waste responds "
         "to margins and regulation. Household waste responds only to what "
         "people do in their own kitchens.")

    para(document,
         "This shapes what a tool must look like. It has to work without "
         "anyone being paid to run it, survive people who did not choose to "
         "join a study, and give a benefit the household notices. A benefit "
         "that only a researcher can measure is not enough. These are hard "
         "conditions, and they explain "
         "why so much of the technical literature stops at the prototype stage. "
         "The engineering is the easy part.")

    para(document,
         "It also sets a realistic limit on what one device can claim. "
         "Uncertainty about edibility is one cause among several, and the "
         "behaviour research suggests buying too much and poor planning matter "
         "at least as much. A system that removed the uncertainty completely "
         "would still leave those untouched.")

    heading(document, "IoT architectures for food monitoring", 2)

    para(document,
         "The Internet of Things, as Ashton (2009) described it, is about "
         "giving computers their own way to collect information instead of "
         "relying on people to type it in. Atzori et al. (2010) set out the "
         "layered architecture most later work follows: a perception layer of "
         "sensors, a network layer that carries data, and an application layer "
         "where data is processed and shown.")

    para(document,
         "Food monitoring systems generally use this structure. Ahmadzadeh et "
         "al. (2023) review IoT and big data food waste management models, "
         "algorithms and technologies across every stage from farm to "
         "consumption, and list the open challenges. It is a review, not a "
         "prototype, and it reports no hardware or accuracy numbers of its own. "
         "Reading the works it covers, the consumer stage appears much less "
         "often than retail and supply chain uses. This is my observation, not "
         "a claim the review makes. The imbalance is understandable. A "
         "supermarket has a manager with a budget and a measurable return. A "
         "household has neither.")

    para(document,
         "Sonwani et al. (2022) built an Arduino based prototype with gas, "
         "humidity and temperature sensors, a camera, a Peltier cooling module "
         "and a humidifier. So the system both monitors and actively controls "
         "the storage environment. An eleven layer convolutional network "
         "trained on Fruits-360 identifies the type of fruit or vegetable with "
         "95% accuracy. Spoilage itself is judged from the gas, humidity and "
         "temperature readings, not from the image. They tested fifteen of "
         "fifty listed produce types and report extending the usable life of "
         "some of them by about two days, with alerts sent to the user's phone. "
         "Two things carry over to this thesis. One is the split of work, with "
         "vision used to identify the item and sensors used for its condition. "
         "The other is the use of Fruits-360 for what it really contains, "
         "which is fruit types and not freshness states.")

    para(document,
         "Nemade et al. (2024) used a NodeMCU microcontroller with MQ2 and MQ4 "
         "methane sensors and a DHT11 temperature and humidity sensor. Their "
         "classifier is a Random Forest with recursive feature elimination and "
         "M-SMOTE rebalancing, and it reaches 94.76% accuracy on cooked foods "
         "(rice, bread, samosas and dal) while also predicting remaining shelf "
         "life. There is no camera and no load cell. Their result is worth "
         "remembering when reading Chapter 5. A gas plus environment classifier "
         "with no visual input did well on their data, and the same pattern "
         "appears in this thesis.")

    heading(document, "Cloud, edge, or both", 3)

    para(document,
         "Where the processing happens is a real design choice, and most "
         "published prototypes choose the cloud: the device collects, a server "
         "decides. Shi et al. (2016) give the general case for the other "
         "choice. Pushing computation towards the data source cuts delay and "
         "bandwidth and improves privacy.")

    para(document,
         "For a fridge camera the privacy argument decides it. A device that "
         "photographs the inside of a fridge every thirty minutes and uploads "
         "the images builds a detailed record of a household's diet, shopping, "
         "meal times and absences. That is sensitive data by any standard, and "
         "there is no good reason to create it on somebody else's server when "
         "the alternative exists. Edge inference on a Raspberry Pi 4 is fast "
         "enough here, as Chapter 5 shows, so the usual trade for speed is not "
         "even needed.")

    para(document,
         "This thesis therefore runs everything on the device. Nothing leaves "
         "the local network, and the camera can be switched off from the "
         "interface. This is different from most of the prototypes reviewed, "
         "and it is on purpose.")

    heading(document, "Sensing modalities for spoilage", 2)

    para(document,
         "Four sensing methods appear again and again in the literature. They "
         "carry different and partly complementary information.")

    heading(document, "Visual inspection", 3)

    para(document,
         "Discolouration, mould, wilting and collapse are all visible, and a "
         "camera captures them cheaply. Visual inspection has one basic "
         "weakness that the literature admits less often than it should. It "
         "detects spoilage at the point where a person would also detect it. "
         "By the time an item looks bad, the user did not need a system to say "
         "so. The value of a camera is in noticing an item the user has "
         "forgotten, not in noticing spoilage earlier than they would.")

    para(document,
         "Lighting is the practical difficulty. The same tomato looks different "
         "under a fridge bulb, in daylight through an open door, and in a dark "
         "kitchen at night. A classifier trained on one kind of light gets "
         "worse on another. Controlled internal lighting is the standard fix "
         "and is used here.")

    heading(document, "Gas sensing", 3)

    para(document,
         "As organic matter breaks down it releases volatile organic compounds. "
         "Which ones depends on the food and the microbes involved: ethanol "
         "from fermentation, ammonia and amines from protein breakdown, "
         "hydrogen sulphide from sulphur containing amino acids, and carbon "
         "dioxide all the time. Metal oxide sensors respond to these with a "
         "change in resistance, and the MQ series provides them for a few "
         "euros each.")

    para(document,
         "The electronic nose literature is the relevant background. Loutfi et "
         "al. (2015) review the field for food quality, and Sanaeifar et al. "
         "(2017) survey early detection of contamination and defects. Both make "
         "the same two points. Sensor arrays can tell spoilage states apart "
         "with useful accuracy, and they detect change before visual "
         "inspection does, because volatiles start while the item still looks "
         "fine.")

    para(document,
         "That second point is the whole argument for putting gas sensors in "
         "the box. If gas only became useful once the item looked bad, a "
         "camera alone would do.")

    para(document,
         "The limits are also the same across the literature. Metal oxide "
         "sensors drift as their heaters age, react to humidity as well as to "
         "the target gas, and are cross sensitive. An MQ-135 responds to "
         "ammonia, but also to benzene, alcohol and smoke. They measure the air "
         "of the whole box, not one item, so with several foods present the "
         "reading is a mixture. Absolute calibration needs a clean air "
         "reference resistance that must be set per device.")

    heading(document, "Mass and moisture loss", 3)

    para(document,
         "Fresh produce loses water all the time in storage, and the rate "
         "depends on the vapour pressure deficit between the item and the air "
         "around it. Kader (2002) documents transpiration rates for many "
         "commodities and how they relate to storage quality. Mass loss is a "
         "good thing to measure for three reasons. It only goes one way. It is "
         "cheap to sense with a load cell and an HX711 amplifier. And it is "
         "independent of the microbial signal, so it adds information instead "
         "of repeating it.")

    para(document,
         "The difficulty is practical, not physical. A load cell measures what "
         "is on it, so taking an item out to use half of it looks like a big "
         "sudden mass loss that has nothing to do with spoilage. Telling "
         "consumption from drying needs either user input or a rule about "
         "believable rates.")

    heading(document, "Temperature and humidity", 3)

    para(document,
         "These do not measure spoilage. They measure the conditions that "
         "drive it, which makes them the most valuable channel for prediction "
         "rather than detection. A DHT22 costs about four euros and reports "
         "temperature to about ±0.5 °C and humidity to ±2%. That is enough, "
         "because the effect being tracked is a difference of several degrees "
         "between one fridge and another.")

    para(document,
         "Home fridges do not hold their set temperature. The compressor cycles "
         "between limits, each door opening lets in warm room air, and recovery "
         "takes tens of minutes. So an item sees a sawtooth with spikes, not a "
         "constant temperature. Integrating spoilage over that history gives a "
         "different answer from evaluating it at the average. This is exactly "
         "the information a printed date cannot contain.")

    heading(document, "Other technological approaches", 2)

    heading(document, "Smart packaging and time temperature indicators", 3)

    para(document,
         "Instead of instrumenting the storage space, one can instrument the "
         "food. Time temperature indicators are labels whose colour changes "
         "permanently with accumulated heat exposure. They integrate "
         "temperature history in the same way the Ratkowsky model does, but "
         "chemically instead of by computing. Taoukis and Labuza (1989) set out "
         "the kinetic basis for matching an indicator's activation energy to "
         "the spoilage reaction of a product. This is what makes the colour "
         "change say something about the food, and not just about the time.")

    para(document,
         "TTIs have two advantages over anything in this thesis. They travel "
         "with the item through the whole cold chain instead of only watching "
         "the last step, and they need no power, no calibration and no "
         "interface. Their limit is that they give exactly one bit at a "
         "threshold: the label has changed or it has not. They cannot report a "
         "trend, cannot say how many days are left, and cannot notice that an "
         "item has been forgotten.")

    para(document,
         "Printed gas sensors inside packaging have been shown to work and "
         "would carry richer information, but cost and disposal are unsolved "
         "at supermarket scale. A sensor that goes to landfill after one use "
         "is hard to justify for a technology sold on environmental grounds.")

    heading(document, "Retail stage interventions", 3)

    para(document,
         "In shops, dynamic markdown systems cut waste by lowering prices as "
         "expiry approaches, and several European chains use them at scale. "
         "They work well because the operator is a business with an inventory "
         "system, a profit motive and staff to act on the output.")

    para(document,
         "They are mentioned here mainly as a contrast. The retail problem is "
         "an optimisation problem with a clear goal. The household problem is a "
         "human behaviour problem dressed as an engineering problem, and the "
         "literature often underestimates how much of it is the first.")

    heading(document, "Machine learning for freshness classification", 2)

    heading(document, "Convolutional networks and transfer learning", 3)

    para(document,
         "Convolutional neural networks are the standard tool for image "
         "classification. They learn layers of filters from data instead of "
         "relying on hand designed features. The constraint for this "
         "application is not accuracy but size: the network has to run on an "
         "ARM processor inside a power budget.")

    para(document,
         "MobileNetV2 (Sandler et al., 2018) is designed for exactly that. "
         "Depthwise separable convolutions split a normal convolution into a "
         "per channel spatial filter followed by a pointwise combination. This "
         "cuts parameters and multiply operations by about ten times compared "
         "with a normal architecture at similar ImageNet accuracy. The inverted "
         "residual structure with linear bottlenecks keeps the intermediate "
         "tensors small, which matters on a device with limited memory "
         "bandwidth.")

    para(document,
         "Training such a network from scratch needs far more labelled data "
         "than any food freshness dataset has. Transfer learning is the "
         "standard answer: start from weights trained on a large general "
         "dataset such as ImageNet (Deng et al., 2009), then adapt. Pan and "
         "Yang (2010) give the general framework, and Yosinski et al. (2014) "
         "show that early convolutional layers learn widely reusable features "
         "(edges, textures, colour contrasts) while later layers specialise. "
         "This is why it is fine to freeze the early layers and fine tune only "
         "the top, which is what Chapter 4 does.")

    heading(document, "Choosing an architecture", 3)

    para(document,
         "The candidates for a small device fall into a few families. VGG16 is "
         "simple and well understood but has about 138 million parameters, "
         "which rules it out on memory alone. ResNet50 cut that to about 25 "
         "million while improving accuracy, using residual connections to make "
         "deeper networks trainable. It is still a reasonable general choice "
         "where memory is not tight.")

    para(document,
         "The mobile families go further. MobileNetV1 introduced depthwise "
         "separable convolutions. MobileNetV2 added inverted residuals with "
         "linear bottlenecks, reaching similar ImageNet accuracy with about 3.5 "
         "million parameters. EfficientNet later showed that scaling depth, "
         "width and resolution together beats scaling any one of them, and its "
         "smallest versions compete with MobileNetV2.")

    para(document,
         "I chose MobileNetV2 for three reasons, in order of weight. Its size "
         "fits the target device easily. Its Keras implementation and ImageNet "
         "weights are available without extra dependencies, which matters for "
         "reproducibility. And it is the architecture used by the most similar "
         "prior work, so a reader can compare results without wondering if the "
         "backbone explains the difference.")

    para(document,
         "ImageNet accuracy was not a deciding factor. Chapter 5 shows the "
         "visual task here is easy enough that the backbone choice is unlikely "
         "to matter. The interesting variation is in the data, not the "
         "network.")

    heading(document, "Compression and edge deployment", 3)

    para(document,
         "Running a network on small hardware usually involves compression. "
         "Post training quantisation converts floating point weights and "
         "activations to lower precision, usually 16 bit float or 8 bit "
         "integer. This reduces model size and often improves speed where the "
         "processor has integer acceleration. Integer quantisation needs a "
         "sample of real inputs to calibrate the range of each activation "
         "tensor. Calibrating on unrealistic data hurts accuracy in ways that "
         "are easy to miss.")

    para(document,
         "Pruning and knowledge distillation are the other standard tools. "
         "Neither was needed here. Chapter 5 shows inference already uses about "
         "a tenth of a percent of the duty cycle, so compression beyond float16 "
         "saves storage that is not scarce.")

    heading(document, "Data leakage and evaluation integrity", 3)

    para(document,
         "Work across many machine learning fields documents how easily "
         "evaluation protocols overstate performance. The same causes come up "
         "again and again. Duplicate or near duplicate samples across training "
         "and test splits. Preprocessing statistics fitted before splitting. "
         "Test data used during model selection. And time leakage, where a "
         "split ignores the order in which data arrived.")

    para(document,
         "Near duplicate leakage is the one that matters here, and it is "
         "dangerous because the obvious check does not find it. Hashing finds "
         "identical files. It finds nothing when a dataset has been augmented "
         "and the variants of one photo differ in every byte while showing the "
         "same object under the same light from almost the same angle. Finding "
         "that needs a comparison in a space where visual similarity can be "
         "measured, which is what the audit in Chapter 4 does.")

    para(document,
         "The prototypes reviewed in this chapter report accuracies without "
         "describing any such check. This is not proof their numbers are "
         "wrong. It does mean that neither they nor a reader can tell.")

    heading(document, "Datasets and what they contain", 3)

    para(document,
         "Food image datasets are common. Food spoilage datasets are not. "
         "Food-101 (Bossard et al., 2014) covers prepared dishes by type, not "
         "by condition. Fruits-360 (Mureșan and Oltean, 2018) has about 90,000 "
         "images in 131 classes, but the classes are fruit varieties on a "
         "white background under controlled light, and it has no spoiled "
         "examples. An earlier draft of this thesis claimed otherwise. Checking "
         "the dataset's own class list showed the claim was wrong.")

    para(document,
         "Researchers working on spoilage therefore build their own datasets, "
         "which is why comparing studies is hard. Reported accuracies cannot "
         "be compared in a meaningful way when each is measured on a different "
         "private dataset of a different difficulty.")

    para(document,
         "There is a deeper problem with public fresh versus rotten datasets, "
         "and Chapter 5 returns to it. They contain clearly fresh items and "
         "clearly rotten ones, because those are the images a human labeller "
         "can label with confidence. The in between state, the item that is "
         "past its best but still looks acceptable, is the case a prediction "
         "system exists to catch, and it is missing from the data. High "
         "accuracy on such a dataset shows that the easy case is easy.")

    heading(document, "Sensor fusion", 3)

    para(document,
         "Combining inputs can be done early, by joining raw inputs, or late, "
         "by letting each branch form its own representation and joining "
         "afterwards. Late fusion is usually preferred when the inputs differ a "
         "lot in size and scale, which is the case here: 150,528 pixel values "
         "against five numbers. Joining those raw would let the pixels dominate "
         "completely.")

    para(document,
         "Chapter 5 reports that late fusion by itself is not enough, and that "
         "the width of each branch at the join matters a lot. The literature "
         "rarely mentions this detail. This work found it the hard way.")

    heading(document, "Evaluating under asymmetric cost", 3)

    para(document,
         "Accuracy is the default metric and it is almost useless for this "
         "problem, for two reasons that add up.")

    para(document,
         "The first is class balance. A dataset with three equal classes makes "
         "accuracy easy to read, but a real system sees mostly fresh items, "
         "because most food in a fridge is fine most of the time. A classifier "
         "that always said fresh would score well on that distribution while "
         "being useless. Macro averaged F1 weights each class equally no matter "
         "how common it is, and is the more honest summary. That is why it is "
         "reported next to accuracy in Chapter 5.")

    para(document,
         "The second is that the two error directions do not cost the same. "
         "Calling a spoiled item fresh may make someone ill. Calling a fresh "
         "item spoiled wastes the food the system is meant to save. Both are "
         "real costs and they are not equal, so a single number that averages "
         "them throws away the most important distinction.")

    para(document,
         "The standard answer is to report per class recall and precision "
         "separately and to say in advance which class carries the higher "
         "cost. Here that is recall on the spoiled class, and it is reported "
         "for every model in Chapter 5. Confusion matrices are shown in full, "
         "because the pattern of the errors carries information that no single "
         "number keeps.")

    heading(document, "Human factors and alert design", 2)

    para(document,
         "A monitoring system that nobody acts on saves nothing. So the "
         "interface is part of the engineering, not decoration on top of it.")

    para(document,
         "Nielsen's usability heuristics (Nielsen, 1994) give the relevant "
         "principles: visibility of system status, user control and freedom, "
         "and error prevention. The third is the sharpest constraint here. A "
         "system that raises false alarms teaches its user to ignore it, and "
         "an ignored alert is worse than no alert, because the user has "
         "stopped checking and believes they are covered.")

    para(document,
         "The applied psychology literature on alarm fatigue, mostly from "
         "hospitals, agrees: response to alerts gets worse as alerts get more "
         "frequent, and it gets worse fastest when many alerts turn out to be "
         "false. The design lesson is to alert on changes and not on states, "
         "to require confidence before interrupting anyone, and to give the "
         "user a way to silence the system without abandoning it. Chapter 4 "
         "does all three.")

    heading(document, "Comparison of related systems", 2)

    para(document,
         "Table 1 puts the reviewed prototypes next to the present work. The "
         "accuracy column should be read with care, and the note under the "
         "table explains why.")

    table(document,
          ["Study", "Sensing", "Model", "Platform", "Processing", "Reported accuracy"],
          [["Sonwani et al. (2022)", "Gas, humidity, temperature; camera; "
            "Peltier cooler and humidifier",
            "11-layer CNN on Fruits-360 for produce type; sensor thresholds "
            "for condition", "Arduino", "Phone alerts",
            "95% (fruit type identification)"],
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
            "**Fully on device**",
            f"**{R.pct(R.visual['accuracy'])} binary; {R.pct(R.acc('fusion'))} three state**"]],
          "Table 1",
          "Reviewed food spoilage monitoring systems. The accuracy figures "
          "cannot be compared across rows. Each was measured on a different "
          "private dataset of unknown difficulty, with different class "
          "definitions. The column records what each study reported, not a "
          "ranking. Sonwani's figure is for identifying the produce type, not "
          "its condition. The last row is explained in Chapter 5, including "
          "why the binary result is less impressive than it looks and why the "
          "simulated sensors limit what the three state figure means.",
          widths=[3.0, 2.8, 3.0, 2.4, 2.2, 2.6], font_size=8.0)

    heading(document, "Gaps addressed by this work", 2)

    para(document,
         "Five gaps come out of the review. This thesis addresses four of them "
         "and admits that it leaves the fifth open.")

    reset_numbering()
    numbered(document,
             "Reproducibility. Most prototypes are described, not released. "
             "Part lists are incomplete, pin assignments are missing, and source "
             "code is rarely published, so the results cannot be checked or "
             "built on. This work publishes the full implementation, a pin "
             "level wiring design, and a pipeline that regenerates every figure "
             "from raw data with one command.")
    numbered(document,
             "Missing baselines. Studies that combine inputs often report only "
             "the combined accuracy, which cannot show if combining helped. Here "
             "vision only and sensor only baselines are trained under the same "
             "conditions, and the comparison gave a result that goes against "
             "the design assumption.")
    numbered(document,
             "Unchecked datasets. Reported accuracies rarely come with any audit "
             "of the dataset they were measured on. Chapter 4 documents an audit "
             "that found near duplicate leakage invisible to normal duplicate "
             "checks, and Chapter 5 discusses what the corrected figure does and "
             "does not show.")
    numbered(document,
             "Ignored human factors. Alert behaviour is usually left unspecified. "
             "This work implements alerts that fire on transitions, with a "
             "confidence floor and snoozing, and tests that logic.")
    numbered(document,
             "Long term real world evaluation. No reviewed study measures real "
             "waste reduction in households over a meaningful period, and this "
             "one does not either. The gap stays open. Closing it needs real "
             "hardware and a long trial.")

    para(document,
         "The fifth gap is the one that matters most for the field, and it is "
         "beyond a bachelor thesis. What this work can do is build the system "
         "such a trial would use, and make it possible to inspect.")
