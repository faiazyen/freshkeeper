"""Chapter 1 Introduction, Chapter 2 Objectives and Methodology."""

from docx_builder import (
    bullet, heading, numbered, para, reset_numbering, rich_para,
)


def build(document) -> None:
    heading(document, "Introduction", 1)

    para(document,
         "About one third of all food produced for people is never eaten. The "
         "Food and Agriculture Organization puts the figure at 1.3 billion tonnes "
         "a year, worth about USD 940 billion. The environmental cost is even "
         "worse than the money. Food waste causes an estimated 8 to 10 percent of "
         "global greenhouse gas emissions. Part of this comes from food rotting "
         "in landfill. Part of it is the carbon already spent to grow, transport "
         "and cool food that nobody eats (FAO, 2019; UNEP, 2021).")

    para(document,
         "In the European Union, more than half of this waste happens at home, "
         "not on farms, in factories or in shops (Eurostat, 2022). This is a hard "
         "place for the problem to be. Waste in shops and supply chains can be "
         "reduced with better forecasting and dynamic prices, and this works. "
         "Household waste has no central manager. It is the sum of millions of "
         "small decisions made by people standing at an open fridge, often in a "
         "hurry.")

    para(document,
         "When researchers ask people why they threw food away, the answers are "
         "often about not knowing. People do not know if the yoghurt is still "
         "fine three days after its date. They do not know that a bag of "
         "spinach was pushed to the back of the shelf a week ago. And they are "
         "not sure if chicken that smells a bit strange is really bad or if it "
         "just smells of the packaging. So the waste is a reaction to "
         "uncertainty. Nobody wants food poisoning, and when people are in "
         "doubt the food goes in the bin.")

    para(document,
         "My interest in this problem is personal. For a while I shared a flat, "
         "and we spent around two thousand crowns a week on groceries. At the "
         "end of most weeks we threw a lot of it away: butter, tomatoes, fruit, "
         "sometimes a whole cake. Food ordered from a restaurant and left "
         "overnight would smell by the next day, and cooked rice went bad "
         "within a day. When I later worked in a restaurant I saw the same "
         "thing on a larger scale, with a lot of good food thrown out at the "
         "end of every night. Most of this was not carelessness. People forgot "
         "what they already had, bought more, and did not know how long it "
         "would last. That is the gap this thesis tries to close.")

    heading(document, "The problem with printed dates", 2)

    para(document,
         "Printed dates are the main tool people have, and they are a rough "
         "tool. A best before date is set by the producer for an item stored "
         "under assumed conditions, usually a constant temperature at the top of "
         "the recommended range, plus a safety margin. It describes an average "
         "item, not the one in your fridge.")

    para(document,
         "This matters more than it seems, because spoilage speed depends a lot "
         "on temperature. Microbial growth roughly doubles or triples for every "
         "ten degrees of warming in the range where home fridges work. A fridge "
         "at 7 °C because its thermostat drifted, or one opened forty times a "
         "day in a shared flat, ages its contents much faster than one held at "
         "3 °C and opened five times. Two boxes of strawberries with the same "
         "printed date can be days apart in their real condition, and the "
         "label has no way to know this.")

    para(document,
         "A date also cannot change. Once printed it is fixed, whether the item "
         "spent an afternoon in a hot car or went straight from a cold van into "
         "a cold fridge. Anything that reacts to what an item really went "
         "through has to measure it.")

    heading(document, "Why now", 2)

    para(document,
         "Two things have changed that make a home version of this measurement "
         "realistic. Small computers that can run a convolutional neural network "
         "cost about EUR 55, and the sensors needed to watch a shelf cost a few "
         "euros each. A Raspberry Pi 4 with a camera, two gas sensors, a load "
         "cell and a temperature probe costs about EUR 147 in parts. This is "
         "the price of a kitchen accessory, not of laboratory equipment.")

    para(document,
         "At the same time, neural networks designed for small hardware have "
         "become good enough to be useful. MobileNetV2 classifies a 224 by 224 "
         "image in tens of milliseconds on an ARM processor. This is far below "
         "the budget of a system that only needs to look at a shelf every half "
         "hour.")

    para(document,
         "What has not appeared is a product. Smart fridges from the big "
         "manufacturers track what is inside, usually with a camera or a "
         "barcode, and some show it on your phone. None of them predict "
         "spoilage from measured conditions. The research literature has "
         "prototypes, reviewed in Chapter 3, but they usually test a few food "
         "types in a laboratory and rarely publish enough detail to rebuild the "
         "system.")

    heading(document, "What this thesis does", 2)

    para(document,
         "This thesis designs and builds a software prototype that watches items on a "
         "fridge shelf. It predicts how far each one has moved towards "
         "spoilage. It tells the user in time to eat the food instead of "
         "throwing it away. The system is called FreshKeeper. It runs completely on the "
         "device. Images are taken, classified and deleted locally. Nothing is "
         "sent to a cloud service.")

    para(document,
         "An earlier version of this thesis described such a system without "
         "showing that it existed, and the supervisor said so directly. This "
         "version is the answer to that. The software is written, it runs, it is "
         "tested, and the figures in this document are generated from it, not "
         "drawn to show an idea. Where a result is weaker than I hoped, it is "
         "reported as it is.")

    para(document,
         "One limit shaped the work a lot, and I state it here rather than at "
         "the end. The hardware was not built. There is no public dataset that "
         "pairs photos of spoiling food with gas, temperature, humidity and "
         "weight readings taken at the same time. Building one needs a physical "
         "rig running for months, which a bachelor thesis does not have. So the "
         "sensor values are generated by a physical model calibrated against "
         "published shelf life data. Every result that depends on them is "
         "reported as a property of that model, not of a real fridge. The images "
         "and their labels are real. Chapter 4 marks this line exactly, and "
         "Chapter 5 returns to what it does and does not allow us to conclude.")

    heading(document, "Structure of this thesis", 2)

    para(document,
         "Chapter 2 gives the objectives, the research questions and the "
         "methodology, including how the evaluation was designed. Chapter 3 "
         "reviews the literature on food waste, IoT monitoring, spoilage "
         "sensing, machine learning for freshness and predictive microbiology, "
         "and lists the gaps this work addresses. Chapter 4 is the practical "
         "part: the architecture, the hardware design, the physical model, the "
         "dataset work including an audit that changed the results, the machine "
         "learning pipeline, the software and the tests. Chapter 5 reports what "
         "was measured and discusses it, including two findings that go against "
         "the design idea. Chapter 6 concludes and says what has to happen next "
         "before the system can be trusted on a real shelf.")

    # ======================================================================
    heading(document, "Objectives and Methodology", 1)

    heading(document, "Objectives", 2)

    para(document,
         "The overall aim is to find out if a low cost device can usefully "
         "predict household food spoilage by combining computer vision with "
         "environmental sensing. A second aim is to build a working prototype "
         "that shows the answer instead of only claiming it. This breaks into "
         "six objectives.")

    reset_numbering()
    numbered(document,
             "Design a sensing platform from standard parts costing under EUR "
             "150, described in enough detail that someone else could build it: "
             "named parts, a pin level wiring design and working driver code.")
    numbered(document,
             "Build a physical model of food spoilage from established "
             "predictive microbiology equations, and calibrate it against "
             "published fridge shelf lives so that its output can be checked.")
    numbered(document,
             "Build a machine learning pipeline that classifies monitored items "
             "into three states, using transfer learning for the visual part and "
             "late fusion to combine it with sensor features.")
    numbered(document,
             "Test if sensor fusion really beats each single input, by training "
             "vision only and sensor only baselines under the same conditions "
             "and comparing them.")
    numbered(document,
             "Implement the complete software: data acquisition, database, "
             "inference service, REST API, alerts and a user interface, good "
             "enough to run without supervision and covered by automated tests.")
    numbered(document,
             "Evaluate the prototype on classification accuracy, inference cost "
             "and system behaviour, and say clearly what the evaluation does not "
             "prove.")

    para(document,
         "Objective 4 needs a comment, because it is the one that could give an "
         "unwanted answer, and it did. The design assumes that combining inputs "
         "beats each input alone. This assumption is the reason for putting gas "
         "sensors in the box at all. Testing it honestly means being ready to "
         "find that the extra hardware is not worth it. Chapter 5 reports what "
         "happened.")

    heading(document, "Research questions", 2)

    para(document,
         "The objectives lead to four questions. Each one is written so that "
         "the evidence can actually answer it.")

    rich_para(document, [
        ("RQ1. ", "b"),
        ("Can a physical model of spoilage, built from published predictive "
         "microbiology equations and calibrated against literature shelf lives, "
         "reproduce those shelf lives closely enough to serve as ground truth "
         "for training a classifier?", ""),
    ])
    rich_para(document, [
        ("RQ2. ", "b"),
        ("How accurately can a transfer learned convolutional network tell "
         "fresh from spoiled produce from photos alone, and what does that "
         "accuracy really show about detecting spoilage early?", ""),
    ])
    rich_para(document, [
        ("RQ3. ", "b"),
        ("Does late fusion of visual and sensor features beat vision only and "
         "sensor only baselines on a three state spoilage task?", ""),
    ])
    rich_para(document, [
        ("RQ4. ", "b"),
        ("Is the inference cost low enough for continuous operation on a "
         "Raspberry Pi 4 within a realistic power and duty cycle budget?", ""),
    ])

    para(document,
         "RQ2 is worded carefully. Asking only how accurate the classifier is "
         "would invite a number that sounds good and means less than it seems. "
         "The second half of the question is the part that matters, and Chapter "
         "5 spends more words on it than on the accuracy number.")

    heading(document, "Terms used in this thesis", 2)

    para(document,
         "Some terms are used with a fixed meaning throughout the thesis. They "
         "are defined here once so that the later chapters can use them "
         "without explaining them again.")

    rich_para(document, [("Fresh, marginal, spoiled. ", "b"),
        ("The three states an item can be in. Fresh means safe and good to "
         "eat. Marginal means the item should be used soon. Spoiled means it "
         "should not be eaten. In the simulation these are cuts at 0.35 and "
         "0.70 on the spoilage extent.", "")])
    rich_para(document, [("Spoilage extent. ", "b"),
        ("A number from 0 to 1 that says how far an item has gone towards "
         "being spoiled. Zero is a perfectly fresh item. One is fully spoiled. "
         "It is computed by the physical model from temperature, humidity and "
         "time.", "")])
    rich_para(document, [("Freshness score. ", "b"),
        ("A number from 0 to 100 shown to the user. It is the reverse of the "
         "spoilage extent in spirit: 100 is fresh, 0 is spoiled. It is "
         "computed from the three class probabilities the model outputs.", "")])
    rich_para(document, [("Slot. ", "b"),
        ("One position on the monitored shelf, with its own load cell. The "
         "prototype has six slots. One item is tracked per slot.", "")])
    rich_para(document, [("Measurement cycle. ", "b"),
        ("One full round of reading every sensor for every slot, running the "
         "model, and saving the result. In the real system this happens every "
         "thirty minutes. In the accelerated demonstration, one cycle stands "
         "for twelve simulated hours.", "")])
    rich_para(document, [("Embedding. ", "b"),
        ("A list of 1280 numbers that the MobileNetV2 network produces from a "
         "photo. It is a compact description of what is in the image. The "
         "classifier works on this list, not on the raw pixels.", "")])
    rich_para(document, [("Late fusion. ", "b"),
        ("A way of combining two inputs, here the image embedding and the "
         "sensor readings. Each input first goes through its own small "
         "network. Their outputs are then joined and a final network makes "
         "the decision. The alternative, early fusion, would join the raw "
         "inputs at the start.", "")])
    rich_para(document, [("Ablation. ", "b"),
        ("An experiment where one part of a system is removed to see how much "
         "it contributed. Here the vision only and sensor only models are "
         "ablations of the fusion model.", "")])
    rich_para(document, [("Leakage. ", "b"),
        ("When information from the test data reaches the model during "
         "training, usually by accident. It makes test scores look better than "
         "they really are. Chapter 4 describes a case of it.", "")])
    rich_para(document, [("Simulated backend. ", "b"),
        ("The version of the sensor layer that generates readings from the "
         "physical model instead of reading real hardware. All sensor numbers "
         "in this thesis come from it.", "")])

    heading(document, "Methodology", 2)

    heading(document, "Overall approach", 3)

    para(document,
         "The work has a theoretical part and a practical part, in the order the "
         "faculty template expects. The theoretical part reviews the literature "
         "and builds the foundation. It looks at which sensing methods carry information about spoilage, which model types suit small hardware, and which equations describe microbial growth well enough to build on. The "
         "practical part designs, implements and evaluates the prototype on "
         "that foundation.")

    para(document,
         "Development was incremental rather than following a formal framework. "
         "Scrum and similar methods assume a team and changing requirements. "
         "Neither applies to one person building against a fixed assignment. "
         "What I kept is the useful part. I worked in steps, and each step ended with something I could test. The steps were the physical model, the sensor "
         "layer, the dataset pipeline, the machine learning models, the "
         "backend, the interface, and integration. Each is a package in the "
         "repository with its own tests.")

    heading(document, "Tooling and reproducibility", 3)

    para(document,
         "Everything is written in Python 3.12, with TensorFlow and Keras for "
         "the models, Flask and SQLAlchemy for the backend, SQLite for storage "
         "and Vue 3 for the interface. Version control is Git. Dependencies are "
         "pinned in a requirements file. The Raspberry Pi only packages are "
         "listed separately because they do not install on a development "
         "machine.")

    para(document,
         "Reproducibility was treated as a requirement, not as a nice extra. "
         "Every random process is seeded: the dataset split, the sensor "
         "simulation, the model initialisation and the training shuffles. Each "
         "pipeline stage writes a machine readable result file, and every "
         "number and every figure in this thesis is generated from those files "
         "by a script. The pin numbers in the wiring diagram, for example, are "
         "imported from the driver module, so the diagram cannot disagree with "
         "the code.")

    para(document,
         "One command reruns the whole pipeline from the raw dataset download to "
         "the final figures. It takes about forty minutes, most of it fine "
         "tuning the visual network.")

    heading(document, "Evaluation design", 3)

    para(document,
         "The evaluation has three parts. I want to say clearly which claims "
         "each part can support.")

    para(document,
         "Model performance is measured on a held out test split that was never "
         "used for training or model selection. I report accuracy, macro "
         "averaged F1, per class precision and recall, and confusion matrices. "
         "Recall on the spoiled class is reported separately everywhere, "
         "because the two error directions do not cost the same. Calling a "
         "spoiled item fresh may make somebody ill. Calling a fresh item "
         "spoiled wastes the food the system is meant to save. Both are real "
         "costs, but they are not equal, and one accuracy number hides the "
         "difference.")

    para(document,
         "The comparison against baselines is the core of the model "
         "evaluation. Three models are trained on the same splits with the same "
         "settings: vision only, sensor only, and fusion. Reporting only the "
         "fusion accuracy would mean almost nothing, because there would be "
         "nothing to compare it with.")

    para(document,
         "Inference cost is measured stage by stage, so we can see which part "
         "is expensive. The measurements are taken on the development "
         "computer. The Raspberry Pi figures are that measurement scaled by a "
         "public benchmark ratio. They are marked as estimates every time they "
         "appear.")

    para(document,
         "System behaviour is checked by running the real acquisition and "
         "inference path against the simulated backend with time compressed, "
         "so that twelve days of storage happen in a few seconds. This confirms "
         "that the pipeline works end to end and that predictions follow the "
         "physics. It shows that the plumbing is correct. It is not evidence "
         "about real food.")

    heading(document, "Project risks and how they were handled", 3)

    para(document,
         "Three risks were clear from the start. Each one shaped a design "
         "decision, so I record them here.")

    para(document,
         "The first was hardware availability. If the parts could not be bought "
         "and assembled in time, a design that assumed physical sensors would "
         "leave nothing to evaluate. The answer was the abstraction layer in "
         "Chapter 4: the system talks to a sensor interface, not to GPIO pins, "
         "so the whole software could be built and tested against a simulated "
         "backend. This risk did happen. The answer worked. The cost is that "
         "the strongest results are limited by the simulation.")

    para(document,
         "The second was dataset availability. Food spoilage datasets are rare "
         "and often not licensed for sharing. The answer was to choose a dataset "
         "with a clear permissive licence and to script the download, so the "
         "pipeline can be repeated without sharing anyone's data. What I did "
         "not expect was that the chosen dataset had quality problems of its "
         "own. Chapter 4 documents them.")

    para(document,
         "The third was that a prototype tested only in simulation could give "
         "results that look like measurements but are not. This is the risk "
         "that matters most for the honesty of the work. The answer is not "
         "technical but editorial. The source of every number is stated where "
         "it is reported, the simulation module carries a warning in its own "
         "documentation, and Chapter 5 separates what was measured from what it "
         "supports. Whether this worked is for the reader to judge.")

    heading(document, "Ethical and sustainability considerations", 3)

    para(document,
         "Two ethical questions come directly from the design, and both "
         "influenced it.")

    para(document,
         "The first is privacy. A camera inside a fridge, taking a picture "
         "every thirty minutes, builds a record of what a household eats, when "
         "they shop, when they cook and when the house is empty. This is "
         "sensitive information. The usual design for such a device, upload "
         "the images and process them in the cloud, creates the risk on "
         "somebody else's server. The design here keeps all processing local, "
         "so the sensitive data never leaves the home, and Chapter 4 explains how. "
         "This protection is built into the structure. It is not a promise "
         "that someone has to keep.")

    para(document,
         "The second is the risk of being wrong in the dangerous direction. A "
         "system that says food is fine when it is not could make someone "
         "ill. This is why recall on the spoiled class is reported separately. "
         "It is why the alert logic stays quiet when the model is not "
         "confident. And it is why the interface presents predictions as "
         "advice the user can override, not as final verdicts. A prototype tested in simulation "
         "should not be trusted over a person's own judgement, and the "
         "interface is designed with that in mind.")

    para(document,
         "On sustainability, the work fits Sustainable Development Goal 12.3, "
         "which aims to halve food waste per person at consumer level by 2030 "
         "(United Nations, 2015). I want to state this modestly. The device "
         "uses power all the time to save food now and then. Whether that trade "
         "is good depends on how much food it really saves, and this thesis "
         "does not measure that. Chapter 4 gives the power budget so the "
         "calculation can be done once someone has the missing number.")

    heading(document, "What this methodology cannot establish", 3)

    para(document,
         "Three limits follow directly from the constraint stated in Chapter 1. "
         "It is more honest to list them here than in a limitations section at "
         "the end.")

    bullet(document,
           "No claim is made about real sensor accuracy. The gas, temperature, "
           "humidity and mass readings come from a model. The model is "
           "calibrated and its assumptions are documented, but a calibrated "
           "model is not a measurement.")
    bullet(document,
           "No claim is made about real waste reduction. To show that, one "
           "would need a controlled trial across many households over months. "
           "What can be said is what the literature reports for similar tools, "
           "and Chapter 5 says it as a citation, not as a result.")
    bullet(document,
           "No usability study was done. The interface follows established "
           "rules and the design reasoning is written down, but design "
           "reasoning is a guess about users, not evidence about them.")

    para(document,
         "These are real limits and they narrow the conclusions a lot. They do "
         "not make the work pointless. The software, the physical model, the "
         "dataset audit and the baseline comparison are all reproducible "
         "contributions on their own, and they are what a hardware validation "
         "would be built on.")
