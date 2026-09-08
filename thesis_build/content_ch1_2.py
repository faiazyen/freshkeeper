"""Chapter 1 Introduction, Chapter 2 Objectives and Methodology."""

from docx_builder import (
    bullet, figure, heading, numbered, para, reset_numbering, rich_para, table,
)

FIG = "../freshkeeper/docs/figures"


def build(document) -> None:
    # ======================================================================
    heading(document, "Introduction", 1)

    para(document,
         "About a third of the food produced for human consumption is never "
         "eaten. The Food and Agriculture Organization puts the figure at 1.3 "
         "billion tonnes a year, worth roughly USD 940 billion, and the "
         "environmental cost is worse than the price tag suggests: food waste "
         "accounts for an estimated 8 to 10 percent of global greenhouse gas "
         "emissions, partly from organic matter decomposing in landfill and "
         "partly from the carbon already spent growing, moving and chilling food "
         "that nobody eats (FAO, 2019; UNEP, 2021).")

    para(document,
         "In the European Union, more than half of that waste happens in "
         "people's homes rather than in fields, factories or shops (Eurostat, "
         "2022). This is an uncomfortable place for the problem to sit. Retail "
         "and supply-chain waste can be attacked with better forecasting and "
         "dynamic pricing, and those interventions work. Household waste has no "
         "central operator to optimise. It is the aggregate of millions of "
         "small decisions made by people standing in front of an open fridge, "
         "usually in a hurry.")

    para(document,
         "When researchers ask people why they threw food away, the answers "
         "cluster around not knowing. Not knowing whether the yoghurt is still "
         "fine three days past its date. Not knowing that a bag of spinach was "
         "pushed to the back of a shelf a week ago. Not knowing whether the "
         "chicken that smells slightly odd is genuinely off or just smells of "
         "packaging. The waste is a response to uncertainty, and it is "
         "asymmetric on purpose: nobody wants food poisoning, so when in doubt, "
         "the item goes in the bin.")

    heading(document, "The problem with printed dates", 2)

    para(document,
         "Printed dates are the main tool people have, and they are a blunt one. "
         "A best-before date is set by the manufacturer for an item stored under "
         "assumed conditions, usually a constant temperature at the top of the "
         "recommended range, and it carries a safety margin. It describes a "
         "hypothetical average item, not the one in your fridge.")

    para(document,
         "That distinction matters more than it might appear, because spoilage "
         "rate depends steeply on temperature. Microbial growth roughly doubles "
         "to triples for every ten degrees of warming across the range domestic "
         "refrigerators actually operate in. A fridge running at 7 °C because "
         "its thermostat drifted, or one opened forty times a day in a shared "
         "flat, ages its contents measurably faster than one held at 3 °C and "
         "opened five times. Two punnets of strawberries with the same printed "
         "date can be days apart in real condition, and the label has no way to "
         "know.")

    para(document,
         "A date also cannot be revised. Once printed it is fixed, whether the "
         "item spent an afternoon in a hot car or went straight from a chilled "
         "delivery van into a cold fridge. Anything that reacts to the "
         "conditions an item actually experienced has to measure them.")

    heading(document, "Why now", 2)

    para(document,
         "Two things have changed that make a domestic version of this "
         "measurement plausible. Single-board computers capable of running a "
         "convolutional neural network cost around EUR 55, and the sensors "
         "needed to watch a shelf cost a few euros each. A Raspberry Pi 4 with a "
         "camera, two gas sensors, a load cell and a temperature probe comes to "
         "roughly EUR 147 in parts, which is inside the range of a domestic "
         "appliance accessory rather than laboratory equipment.")

    para(document,
         "At the same time, neural network architectures designed for "
         "constrained hardware have become good enough to be useful. MobileNetV2 "
         "classifies a 224 by 224 image in tens of milliseconds on an ARM "
         "processor, which is far inside the budget of a system that only needs "
         "to look at a shelf every half hour.")

    para(document,
         "What has not appeared is a product. Smart refrigerators from the major "
         "manufacturers track inventory, usually by camera or barcode, and some "
         "will tell you what is inside from your phone. None of them predict "
         "spoilage from sensed conditions. The research literature has "
         "prototypes, reviewed in Chapter 3, but they tend to test a handful of "
         "food types under laboratory conditions and rarely publish enough "
         "detail to rebuild the system.")

    heading(document, "What this thesis does", 2)

    para(document,
         "This thesis designs and builds a prototype that monitors items on a "
         "refrigerator shelf, predicts how far each has progressed towards "
         "spoilage, and tells the user in time to eat the food rather than throw "
         "it out. The system is called FreshKeeper. It runs entirely on the "
         "device: images are captured, classified and discarded locally, and "
         "nothing is sent to a cloud service.")

    para(document,
         "An earlier version of this thesis described such a system without "
         "demonstrating that it existed, and the supervisor's review said so "
         "directly. The present version is a response to that. The software is "
         "written, it runs, it is tested, and the figures throughout this "
         "document are generated from it rather than drawn to illustrate an "
         "intention. Where a result is weaker than hoped, it is reported at the "
         "strength it has.")

    para(document,
         "One constraint shaped the work heavily and is declared here rather "
         "than buried in a limitations section. The hardware was not built. "
         "There is no public dataset that pairs photographs of spoiling food "
         "with synchronised gas, temperature, humidity and weight measurements, "
         "and constructing one requires a physical rig running for months, which "
         "a bachelor thesis does not have. The sensor channel is therefore "
         "generated by a physical model calibrated against published shelf-life "
         "data, and every result that depends on it is reported as a property of "
         "that model rather than of a real refrigerator. The images and their "
         "labels are real. Chapter 4 marks the boundary precisely, and Chapter 5 "
         "returns to what it does and does not permit anyone to conclude.")

    heading(document, "Structure of this thesis", 2)

    para(document,
         "Chapter 2 sets out the objectives and the methodology used to pursue "
         "them, including the research questions and the evaluation design. "
         "Chapter 3 reviews the literature on food waste, IoT monitoring "
         "architectures, spoilage sensing, machine learning for freshness "
         "classification and predictive microbiology, and identifies the gaps "
         "this work addresses. Chapter 4 is the practical part: the system "
         "architecture, the hardware design, the physical model, the dataset "
         "work including an audit that changed the results materially, the "
         "machine learning pipeline, the software implementation and the test "
         "strategy. Chapter 5 reports what was measured and discusses it, "
         "including two findings that contradict the design hypothesis. "
         "Chapter 6 concludes and sets out what would have to happen next for "
         "the system to be trusted on a real shelf.")

    # ======================================================================
    heading(document, "Objectives and Methodology", 1)

    heading(document, "Objectives", 2)

    para(document,
         "The overall aim is to determine whether a low-cost device combining "
         "computer vision with environmental sensing can usefully predict "
         "household food spoilage, and to build a working prototype that "
         "demonstrates the answer rather than asserting it. That breaks into "
         "six specific objectives.")

    reset_numbering()
    numbered(document,
             "Design a sensing platform from commodity components costing under "
             "EUR 150, specified precisely enough that somebody else could build "
             "it: named parts, a pin-level wiring design and working driver code.")
    numbered(document,
             "Construct a physical model of food spoilage from established "
             "predictive-microbiology equations, and calibrate it against "
             "published refrigerated shelf lives so that its outputs can be "
             "checked rather than merely believed.")
    numbered(document,
             "Build a machine learning pipeline that classifies monitored items "
             "into three states, using transfer learning for the visual branch "
             "and late fusion to combine it with sensor features.")
    numbered(document,
             "Test whether sensor fusion actually outperforms either modality "
             "alone, by training vision-only and sensor-only baselines under "
             "identical conditions and comparing them.")
    numbered(document,
             "Implement the complete software system: data acquisition, "
             "database, inference service, REST API, alerting and a user "
             "interface, at a standard where it runs unattended and is covered "
             "by automated tests.")
    numbered(document,
             "Evaluate the prototype on classification accuracy, inference cost "
             "and system behaviour, and report the limits of what the evaluation "
             "supports.")

    para(document,
         "Objective 4 deserves a comment, because it is the one that could "
         "return an unwelcome answer, and did. The design assumes that combining "
         "modalities beats either alone; that assumption is the reason for "
         "putting gas sensors in the enclosure at all. Testing it properly means "
         "being willing to find that the extra hardware does not earn its place. "
         "Chapter 5 reports what happened.")

    heading(document, "Research questions", 2)

    para(document,
         "The objectives correspond to four questions, phrased so that each has "
         "an answer the evidence can actually supply.")

    rich_para(document, [
        ("RQ1. ", "b"),
        ("Can a physical model of spoilage, built from published "
         "predictive-microbiology equations and calibrated against literature "
         "shelf lives, reproduce those shelf lives closely enough to serve as "
         "ground truth for training a classifier?", ""),
    ])
    rich_para(document, [
        ("RQ2. ", "b"),
        ("How accurately can a transfer-learned convolutional network "
         "distinguish fresh from spoiled produce from photographs alone, and "
         "what does that accuracy actually demonstrate about detecting spoilage "
         "early?", ""),
    ])
    rich_para(document, [
        ("RQ3. ", "b"),
        ("Does late fusion of visual and sensor features outperform "
         "vision-only and sensor-only baselines on a three-state spoilage "
         "classification task?", ""),
    ])
    rich_para(document, [
        ("RQ4. ", "b"),
        ("Is the resulting inference cost compatible with continuous "
         "operation on a Raspberry Pi 4 within a realistic power and duty-cycle "
         "budget?", ""),
    ])

    para(document,
         "RQ2 is worded carefully. Asking only how accurate the classifier is "
         "would invite a number that sounds impressive and means less than it "
         "appears. The second half of the question is the part that matters, and "
         "Chapter 5 spends more words on it than on the accuracy figure.")

    heading(document, "Methodology", 2)

    heading(document, "Overall approach", 3)

    para(document,
         "The work has a theoretical part and a practical part, in the sequence "
         "the faculty template expects. The theoretical part reviews the "
         "scientific and technical literature and establishes the foundation: "
         "which sensing modalities carry information about spoilage, which model "
         "architectures suit constrained hardware, and which equations describe "
         "microbial growth well enough to build on. The practical part designs, "
         "implements and evaluates the prototype on that foundation.")

    para(document,
         "Development followed an incremental process rather than a formal "
         "framework. Scrum and its relatives assume a team and a stream of "
         "changing requirements, and neither applies to one person building "
         "against a fixed assignment. What was borrowed is the part that "
         "generalises: work in increments that each end with something testable. "
         "The increments were the physical model, the sensor abstraction layer, "
         "the dataset pipeline, the machine learning models, the backend, the "
         "interface, and integration. Each is a package in the repository with "
         "its own tests.")

    heading(document, "Tooling and reproducibility", 3)

    para(document,
         "Everything is written in Python 3.12, with TensorFlow and Keras for "
         "the models, Flask and SQLAlchemy for the backend, SQLite for storage "
         "and Vue 3 for the interface. Version control is Git. Dependencies are "
         "pinned in a requirements file, and the Raspberry Pi-only packages are "
         "listed separately because they have no wheels for a development "
         "machine.")

    para(document,
         "Reproducibility was treated as a requirement rather than a courtesy. "
         "Every stochastic process is seeded: the dataset split, the sensor "
         "simulation, the model initialisation and the training shuffles. Each "
         "pipeline stage writes a machine-readable result file, and every figure "
         "in this thesis is generated by a script that reads those files. There "
         "are no numbers in this document that were typed in by hand from a "
         "console, and no diagram that was drawn to match a description rather "
         "than generated from the code it describes. The pin numbers in the "
         "wiring diagram, for instance, are imported from the driver module, so "
         "changing a pin assignment without updating the figure is not "
         "possible.")

    para(document,
         "A single command reruns the entire pipeline from the raw dataset "
         "download to the final figures. It takes about forty minutes, most of "
         "it fine-tuning the visual network.")

    heading(document, "Evaluation design", 3)

    para(document,
         "The evaluation covers three dimensions, and it is worth being explicit "
         "about which claims each can support.")

    para(document,
         "Model performance is measured on a held-out test split, never touched "
         "during training or model selection. Accuracy, macro-averaged F1 and "
         "per-class precision and recall are reported, along with confusion "
         "matrices. Recall on the spoiled class is called out separately "
         "throughout, because the two error directions do not cost the same: "
         "calling a spoiled item fresh may make somebody ill, while calling a "
         "fresh item spoiled wastes the food the system exists to save. Neither "
         "is free, but they are not equivalent, and a single accuracy number "
         "hides the difference.")

    para(document,
         "The comparison against baselines is the core of the model evaluation. "
         "Three models are trained on identical splits with identical "
         "hyperparameters: vision-only, sensor-only, and fusion. Reporting "
         "fusion accuracy alone would be close to meaningless, because there "
         "would be nothing to compare it against.")

    para(document,
         "Inference cost is profiled stage by stage rather than end to end, so "
         "that the expensive part is identifiable rather than merely the total "
         "being known. Measurements are taken on the development host; the "
         "Raspberry Pi figures quoted are that measurement scaled by a published "
         "single-core ratio, and are labelled as estimates every time they "
         "appear.")

    para(document,
         "System behaviour is exercised by running the real acquisition and "
         "inference path against the simulated backend with time compressed, so "
         "that twelve days of storage happen in a few seconds. This confirms "
         "that the pipeline works end to end and that predictions follow the "
         "physics, but it is a demonstration of correct plumbing, not evidence "
         "about real food.")

    heading(document, "Project risks and how they were handled", 3)

    para(document,
         "Three risks were identified at the outset and each shaped a design "
         "decision, so they are recorded here rather than in a retrospective.")

    para(document,
         "The first was hardware availability. If the components could not be "
         "obtained and assembled in time, a design that assumed physical "
         "sensors would leave nothing to evaluate. The mitigation was the "
         "abstraction seam described in Chapter 4: the system talks to a sensor "
         "interface rather than to GPIO, so the software could be built and "
         "tested in full against a simulated backend. This risk materialised, "
         "the mitigation held, and the cost was that the strongest results are "
         "bounded by the simulation.")

    para(document,
         "The second was dataset availability. Food spoilage corpora are scarce "
         "and often unlicensed for redistribution. The mitigation was to select "
         "a corpus with an explicit permissive licence and to write the download "
         "as a scripted step, so that the pipeline is reproducible without "
         "redistributing anyone's data. What was not anticipated was that the "
         "chosen corpus would have quality problems of its own, which "
         "Chapter 4 documents.")

    para(document,
         "The third was that a prototype validated only in simulation might "
         "produce results that look like measurements and are not. This is the "
         "risk that most concerns the scientific integrity of the work, and the "
         "mitigation is editorial rather than technical: the provenance of every "
         "number is stated at the point it is reported, the simulation module "
         "carries the warning in its own docstring, and Chapter 5 separates what "
         "was measured from what it supports. Whether that mitigation worked is "
         "for the reader to judge.")

    heading(document, "Ethical and sustainability considerations", 3)

    para(document,
         "Two ethical questions arise directly from the design and both "
         "influenced it.")

    para(document,
         "The first is privacy. A camera inside a refrigerator, sampling every "
         "thirty minutes, accumulates a record of what a household eats, when "
         "they shop, when they cook and when the house is empty. That is "
         "sensitive by any reasonable standard, and the ordinary architecture "
         "for such a device — upload images, infer in the cloud — creates the "
         "risk on somebody else's server. The design here keeps all processing "
         "local, so the sensitive data never leaves the home. Chapter 4 "
         "describes how, and notes that this is a structural protection rather "
         "than a promise anyone has to keep.")

    para(document,
         "The second is the risk of being wrong in the dangerous direction. A "
         "system that tells someone food is fine when it is not could cause "
         "illness. This is why recall on the spoiled class is reported "
         "separately throughout, why the alert logic refuses to speak when the "
         "model is not confident, and why the interface presents predictions as "
         "guidance the user can override rather than as verdicts. A prototype "
         "validated in simulation has no business being trusted over somebody's "
         "own judgement, and the interface is designed on that assumption.")

    para(document,
         "On sustainability, the work aligns with Sustainable Development Goal "
         "12.3, which targets halving per-capita food waste at consumer level by "
         "2030 (United Nations, 2015). The alignment should be stated modestly. "
         "The device consumes power continuously to save food occasionally, and "
         "whether that trade is favourable depends on how much food it actually "
         "saves — which this thesis does not measure. Chapter 4 gives the power "
         "budget so the arithmetic can be done once someone has the missing "
         "number.")

    heading(document, "What this methodology cannot establish", 3)

    para(document,
         "Three limits follow directly from the constraint declared in Chapter "
         "1, and stating them here is more honest than leaving them to a "
         "limitations section at the end.")

    bullet(document,
           "No claim is made about real-world sensor accuracy. The gas, "
           "temperature, humidity and mass readings come from a model. The "
           "model is calibrated and its assumptions are documented, but a "
           "calibrated model is not a measurement.")
    bullet(document,
           "No claim is made about actual waste reduction. Establishing that "
           "would need a randomised controlled trial across many households "
           "over months. What can be said is what the literature reports for "
           "comparable interventions, and Chapter 5 says it as a citation "
           "rather than a result.")
    bullet(document,
           "No usability study was run. The interface follows established "
           "heuristics and the design reasoning is documented, but design "
           "reasoning is a hypothesis about users, not evidence about them.")

    para(document,
         "These are real limits and they narrow the conclusions considerably. "
         "They do not make the exercise pointless: the software, the physical "
         "model, the dataset audit and the ablation comparison are all "
         "reproducible contributions that stand on their own, and they are what "
         "a hardware validation would be built on.")
