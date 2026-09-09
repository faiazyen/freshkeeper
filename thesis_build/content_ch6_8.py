"""Chapters 6-8: Conclusion, References, Lists, and the appendices."""

from pathlib import Path

from docx_builder import (
    bullet, code_block, figure, heading, list_of, numbered, page_break, para,
    reset_numbering, rich_para, table, unnumbered_heading,
)

from results import Results

REPO = Path(__file__).resolve().parents[1] / "freshkeeper"


def build(document) -> None:
    R = Results()
    # ==================================================================
    heading(document, "Conclusion", 1)

    max_err = max(abs(r["error_percent"]) for r in R.shelf["rows"])

    para(document,
         "This thesis set out to find out whether a low cost device can "
         "usefully predict household food spoilage by combining computer "
         "vision with environmental sensing. It also set out to build a "
         "prototype that shows the answer instead of only describing one. The "
         "prototype exists, it "
         "runs, and it produced results, including two that go against the "
         "design.")

    heading(document, "Answers to the research questions", 2)

    rich_para(document, [
        ("RQ1, on the physical model. ", "b"),
        ("Yes. A model built from the Ratkowsky square root relationship, the "
         "modified Gompertz growth curve and the Magnus-Tetens vapour pressure "
         "formula reproduces published fridge shelf lives to within "
         f"{max_err:.1f}% for eight commodities from five to sixty days. It "
         "extends to temperatures it was not fitted for, with a factor of "
         "about 3 per ten degrees, which is inside the range reported for "
         "microbial spoilage.", ""),
    ])

    rich_para(document, [
        ("RQ2, on visual classification. ", "b"),
        (f"A transfer learned MobileNetV2 reaches {R.pct(R.visual['accuracy'])} "
         f"accuracy and {R.f4(R.visual['auc'])} AUC at telling fresh from "
         "rotten produce on a leakage controlled split of "
         f"{R.n(R.visual['n'])} real photos. The second half of the question "
         "has the more useful answer. That figure does not show early "
         "spoilage detection, because public datasets contain only the clear "
         "cases. The in between state a prediction system exists to catch is "
         "missing, so high accuracy shows competence on the case where the "
         "user needed no help.", ""),
    ])

    rich_para(document, [
        ("RQ3, on sensor fusion. ", "b"),
        (f"No. Under this simulation the sensor only baseline reaches "
         f"{R.pct(R.acc('sensor_only'))} and the best fusion version "
         f"{R.pct(R.acc('fusion'))}, so adding the visual branch costs "
         "accuracy. The cause is in the setup: because the sensor features and "
         "the true labels come from one physical model, the sensor branch has "
         "an unfair advantage. A second finding is that relative branch width "
         "at the join matters. Projecting the visual embedding from 1280 to 64 "
         f"dimensions before joining recovered {R.projection_gain_points:.1f} "
         "percentage points.", ""),
    ])

    rich_para(document, [
        ("RQ4, on inference cost. ", "b"),
        (f"Most likely yes, but I do not claim it as proven. Measured cost is "
         f"{R.stage('total'):.2f} ms per item on the development computer, of "
         "which the MobileNetV2 backbone is "
         f"{R.pct(R.pipe['stages_ms']['backbone']['share_of_total'], 0)}. "
         f"Scaled by the Geekbench 6 single core ratio of {R.pi_factor:.1f}, a "
         f"Raspberry Pi 4 would need about {R.pi_ms:.0f} ms per item, so six "
         f"slots use about {R.pct(R.duty, 1)} of a thirty minute cycle. That "
         "leaves a large margin, but the figure is an estimate and should be "
         "confirmed on a real Pi before it is stated as fact.", ""),
    ])

    heading(document, "Contributions", 2)

    reset_numbering()
    numbered(document,
             f"A complete, reproducible prototype of {R.n(R.loc)} lines of "
             "Python. It covers a physical spoilage model, a hardware layer with "
             "real and simulated backends, a machine learning pipeline, a REST "
             f"API, a database and a web interface. It has {R.tests} automated "
             "tests, and one command regenerates every figure and every number "
             "in this document from raw data.")
    numbered(document,
             "A calibrated, checkable spoilage model that implements "
             "established predictive microbiology, with a test suite that fails "
             "if any coefficient drifts from its published reference. It can be "
             "used without the rest of the system.")
    numbered(document,
             "A dataset audit method that finds near duplicate leakage which "
             f"hash based checks miss completely. With it, {R.pct(R.naive_leak, 0)} "
             "of a widely used dataset's test split was found to sit within "
             "cosine 0.95 of a training image.")
    numbered(document,
             "An honest baseline comparison, including the negative result and "
             "an explanation of why simulated sensor data biases such "
             "comparisons before training starts.")
    numbered(document,
             "A documented critique of public fresh versus rotten datasets. "
             "They contain the easy cases, so accuracies measured on them, "
             "including several in the literature, overstate real "
             "performance.")

    heading(document, "Limitations", 2)

    para(document,
         "The hardware was not built. Every gas, temperature, humidity and "
         "mass reading in this thesis is generated by a model. The model is "
         "calibrated and its assumptions are documented, but no result here is "
         "a measurement from a fridge, and the three state accuracies in "
         "particular should not be read as if they were.")

    para(document,
         "The visual lag assumption, that appearance changes later than "
         "physiology by a commodity specific margin, is supported in direction "
         "by the electronic nose literature, but the exact thresholds were "
         "chosen, not measured. They directly shape the difficulty of the "
         "three state task.")

    para(document,
         "No waste reduction was measured, and no usability study was done. "
         "The consumption event table exists exactly so that a long study "
         "could measure the first, and the interface reasoning is written down "
         "so that the second has something to test.")

    para(document,
         "The dataset covers eight commodities, all fruit. Dairy, meat and "
         "cooked leftovers are where the health risk is highest and they are "
         "missing completely. Ammonia sensing was included partly with protein "
         "breakdown in mind, and no protein food was tested.")

    heading(document, "Future work", 2)

    para(document,
         "The priority is clear, and everything else comes after it.")

    rich_para(document, [
        ("Build the hardware and collect a paired dataset. ", "b"),
        ("Assemble the design in Chapter 4, put instrumented items on the "
         "shelf, and log real sensor readings together with photos and expert "
         "spoilage judgements over several months. That dataset would answer "
         "RQ3 properly, replace the calibrated model with measurements, and "
         "would be a contribution on its own, because no such public dataset "
         "exists. Everything else in this list is less useful until it is "
         "done.", ""),
    ])

    bullet(document,
           "Validate the drivers. The Raspberry Pi module is written and its "
           "interface is tested, but its readings have never been compared "
           "with instruments. The electrical coupling between the gas heaters "
           "and the load cell is a predicted problem with a designed fix and "
           "no evidence either way.")
    bullet(document,
           "Go beyond fruit. Dairy, meat and cooked food carry the real safety "
           "risk. Doing so needs both images and a spoilage model for foods "
           "where the main microbes are different.")
    bullet(document,
           "Run a usability study. Task based evaluation with the System "
           "Usability Scale (Brooke, 1996) would test the interface reasoning "
           "instead of assuming it, and tolerance of false alarms is the "
           "specific thing to measure.")
    bullet(document,
           "Handle several items per slot. The current design assumes one "
           "item per load cell and shared air, which is not how anyone really "
           "loads a fridge. Attributing a gas reading to one of several items "
           "in a shared box is a really hard problem and may be the sharpest "
           "limit of the whole approach.")
    bullet(document,
           "Measure waste reduction. A long deployment across households, with "
           "the consumption event logging already implemented, is the only way "
           "to know whether any of this saves food.")

    heading(document, "A longer term vision", 3)

    para(document,
         "The steps above are the technical next steps. Beyond them, my longer "
         "term aim is to turn the prototype into a product that people actually "
         "use. In that version the user would see the contents of their fridge "
         "and the expected shelf life of each item in a phone app, get a "
         "reminder before something is about to spoil, and get simple recipe "
         "suggestions for the items that need to be used soon.")

    para(document,
         "A single household is only part of the problem. The same information "
         "could connect households, restaurants and shops to food banks and "
         "recycling services, so that food close to its expiry is passed to "
         "someone who can use it instead of going in the bin. Food that is no "
         "longer fit to eat could still go to animal feed, or to compost and "
         "bio fertiliser for farming. A restaurant that cannot sell cooked "
         "food the next day could offer it at a large discount through the same "
         "app rather than throw it away.")

    para(document,
         "These ideas are beyond the scope of this thesis, which tests only the "
         "core prediction system in simulation. They are the direction I would "
         "take the work if it were funded and built for real.")

    heading(document, "Closing remarks", 2)

    para(document,
         "The most valuable outcome of this project was not the accuracy "
         "figures. It was finding out which of these numbers actually mean "
         "something.")

    para(document,
         f"A {R.pct(R.naive_best_val) if R.naive_best_val else '99.7%'} "
         "validation score started an audit that found real leakage, and "
         "fixing it barely moved the number. That showed the task was easy, "
         "not that the model was good. A fusion architecture built on the "
         "assumption that combining inputs helps turned out not to beat its "
         "own baseline, for a reason that says more about simulated "
         "validation than about sensor fusion. Five separate bugs produced "
         "completely believable output while being wrong, and each was caught "
         "by comparing against something external and not by reading the "
         "code.")

    para(document,
         "That pattern is the thing worth keeping. Building the system was the "
         "easier part of the work. Working out what it had really shown, and "
         "being willing "
         "to write down the answer when it was less than I hoped, was the part "
         "that needed judgement.")

    para(document,
         "The prototype is not ready for real use. The sensors were simulated "
         "and nothing was tested on hardware, so it should not be trusted with "
         "real food yet. But it shows the idea can work, and it gives a clear "
         "plan for building and testing the real thing. Everything in it can "
         "be checked and repeated, and the experiment that would prove or "
         "disprove the real system is written down. That is a more useful "
         "place to stop than a confident number nobody can verify.")

    page_break(document)

    # ==================================================================
    heading(document, "References", 1)

    references = [
        "AHMADZADEH, S., AJMAL, T., RAMANATHAN, R. and DUAN, Y., 2023. A "
        "Comprehensive Review on Food Waste Reduction Based on IoT and Big Data "
        "Technologies. Sustainability, 15(4), 3482. doi:10.3390/su15043482",

        "ALDUCHOV, O. A. and ESKRIDGE, R. E., 1996. Improved Magnus Form "
        "Approximation of Saturation Vapor Pressure. Journal of Applied "
        "Meteorology, 35(4), pp. 601-609.",

        "ASHTON, K., 2009. That 'Internet of Things' Thing. RFID Journal, 22(7), "
        "pp. 97-114.",

        "ATZORI, L., IERA, A. and MORABITO, G., 2010. The Internet of Things: A "
        "survey. Computer Networks, 54(15), pp. 2787-2805.",

        "BARANYI, J. and ROBERTS, T. A., 1994. A dynamic approach to predicting "
        "bacterial growth in food. International Journal of Food Microbiology, "
        "23(3-4), pp. 277-294.",

        "BOSSARD, L., GUILLAUMIN, M. and VAN GOOL, L., 2014. Food-101: Mining "
        "Discriminative Components with Random Forests. In: European Conference "
        "on Computer Vision (ECCV), pp. 446-461.",

        "BROOKE, J., 1996. SUS: A 'quick and dirty' usability scale. In: "
        "Usability Evaluation in Industry. London: Taylor and Francis, "
        "pp. 189-194.",

        "DENG, J., DONG, W., SOCHER, R., LI, L.-J., LI, K. and FEI-FEI, L., "
        "2009. ImageNet: A large-scale hierarchical image database. In: IEEE "
        "Conference on Computer Vision and Pattern Recognition, pp. 248-255.",

        "EUROSTAT, 2022. Food waste and food waste prevention - estimates. "
        "Luxembourg: Statistical Office of the European Union.",

        "FAO, 2019. The State of Food and Agriculture 2019: Moving forward on "
        "food loss and waste reduction. Rome: Food and Agriculture Organization "
        "of the United Nations.",

        "GÓMEZ, A. H., WANG, J., HU, G. and PEREIRA, A. G., 2008. Monitoring "
        "storage shelf life of tomato using electronic nose technique. Journal "
        "of Food Engineering, 85(4), pp. 625-631.",

        "GUSTAVSSON, J., CEDERBERG, C., SONESSON, U., VAN OTTERDIJK, R. and "
        "MEYBECK, A., 2011. Global Food Losses and Food Waste: Extent, Causes "
        "and Prevention. Rome: Food and Agriculture Organization of the United "
        "Nations.",

        "IOFFE, S. and SZEGEDY, C., 2015. Batch Normalization: Accelerating Deep "
        "Network Training by Reducing Internal Covariate Shift. In: "
        "International Conference on Machine Learning, pp. 448-456.",

        "KADER, A. A., ed., 2002. Postharvest Technology of Horticultural Crops. "
        "3rd ed. Oakland: University of California Agriculture and Natural "
        "Resources, Publication 3311.",

        "KINGMA, D. P. and BA, J., 2015. Adam: A Method for Stochastic "
        "Optimization. In: International Conference on Learning Representations.",

        "LOUTFI, A., CORADESCHI, S., MANI, G. K., SHANKAR, P. and RAYAPPAN, "
        "J. B. B., 2015. Electronic noses for food quality: A review. Journal "
        "of Food Engineering, 144, pp. 103-111.",

        "McMEEKIN, T. A., OLLEY, J. N., ROSS, T. and RATKOWSKY, D. A., 1993. "
        "Predictive Microbiology: Theory and Application. Taunton: Research "
        "Studies Press.",

        "MUREȘAN, H. and OLTEAN, M., 2018. Fruit recognition from images using "
        "deep learning. Acta Universitatis Sapientiae, Informatica, 10(1), "
        "pp. 26-42.",

        "NEMADE, B. P., SHAH, K., MARAKARKANDY, B., SHAH, K., SURVE, B. C. and "
        "NAGRA, R. K., 2024. An efficient IoT-based automated food waste "
        "management system with food spoilage detection. International Journal "
        "of Intelligent Systems and Applications in Engineering, 12(5s), "
        "pp. 434-449.",

        "NIELSEN, J., 1994. Enhancing the explanatory power of usability "
        "heuristics. In: Proceedings of the SIGCHI Conference on Human Factors "
        "in Computing Systems, pp. 152-158.",

        "PAN, S. J. and YANG, Q., 2010. A Survey on Transfer Learning. IEEE "
        "Transactions on Knowledge and Data Engineering, 22(10), pp. 1345-1359.",

        "QUESTED, T. E., MARSH, E., STUNELL, D. and PARRY, A. D., 2013. "
        "Spaghetti soup: The complex world of food waste behaviours. Resources, "
        "Conservation and Recycling, 79, pp. 43-51.",

        "RATKOWSKY, D. A., OLLEY, J., McMEEKIN, T. A. and BALL, A., 1982. "
        "Relationship between temperature and growth rate of bacterial cultures. "
        "Journal of Bacteriology, 149(1), pp. 1-5.",

        "SANAEIFAR, A., ZAKIDIZAJI, H., JAFARI, A. and DE LA GUARDIA, M., 2017. "
        "Early detection of contamination and defect in foodstuffs by electronic "
        "nose: A review. TrAC Trends in Analytical Chemistry, 97, pp. 257-271.",

        "SANDLER, M., HOWARD, A., ZHU, M., ZHMOGINOV, A. and CHEN, L.-C., 2018. "
        "MobileNetV2: Inverted Residuals and Linear Bottlenecks. In: IEEE "
        "Conference on Computer Vision and Pattern Recognition, pp. 4510-4520.",

        "SCHANES, K., DOBERNIG, K. and GÖZET, B., 2018. Food waste matters - A "
        "systematic review of household food waste practices and their policy "
        "implications. Journal of Cleaner Production, 182, pp. 978-991.",

        "SHI, W., CAO, J., ZHANG, Q., LI, Y. and XU, L., 2016. Edge Computing: "
        "Vision and Challenges. IEEE Internet of Things Journal, 3(5), "
        "pp. 637-646.",

        "SONWANI, E., BANSAL, U., ALROOBAEA, R., BAQASAH, A. M. and HEDABOU, "
        "M., 2022. An Artificial Intelligence Approach Toward Food Spoilage "
        "Detection and Analysis. Frontiers in Public Health, 9, 816226. "
        "doi:10.3389/fpubh.2021.816226",

        "SRIVASTAVA, N., HINTON, G., KRIZHEVSKY, A., SUTSKEVER, I. and "
        "SALAKHUTDINOV, R., 2014. Dropout: A Simple Way to Prevent Neural "
        "Networks from Overfitting. Journal of Machine Learning Research, 15, "
        "pp. 1929-1958.",

        "STANCU, V., HAUGAARD, P. and LÄHTEENMÄKI, L., 2016. Determinants of "
        "consumer food waste behaviour: Two routes to food waste. Appetite, 96, "
        "pp. 7-17.",

        "UNEP, 2021. Food Waste Index Report 2021. Nairobi: United Nations "
        "Environment Programme.",

        "UNITED NATIONS, 2015. Transforming our world: the 2030 Agenda for "
        "Sustainable Development. Resolution A/RES/70/1. New York: United "
        "Nations General Assembly.",

        "WANSINK, B. and WRIGHT, A. O., 2006. 'Best if Used By...' How Freshness "
        "Dating Influences Food Acceptance. Journal of Food Science, 71(4), "
        "pp. S354-S357.",

        "YOSINSKI, J., CLUNE, J., BENGIO, Y. and LIPSON, H., 2014. How "
        "transferable are features in deep neural networks? In: Advances in "
        "Neural Information Processing Systems 27, pp. 3320-3328.",

        "ZWIETERING, M. H., JONGENBURGER, I., ROMBOUTS, F. M. and VAN 'T RIET, "
        "K., 1990. Modeling of the Bacterial Growth Curve. Applied and "
        "Environmental Microbiology, 56(6), pp. 1875-1881.",

        "TAOUKIS, P. S. and LABUZA, T. P., 1989. Applicability of "
        "Time-Temperature Indicators as Shelf Life Monitors of Food Products. "
        "Journal of Food Science, 54(4), pp. 783-788.",
    ]
    for reference in sorted(references):
        paragraph = para(document, reference, space_after=8)
        paragraph.paragraph_format.line_spacing = 1.15
        paragraph.paragraph_format.left_indent = __import__(
            "docx.shared", fromlist=["Cm"]).Cm(1.0)
        paragraph.paragraph_format.first_line_indent = __import__(
            "docx.shared", fromlist=["Cm"]).Cm(-1.0)

    heading(document, "Software and data sources", 2)

    for entry in [
        "MAZUMDER YEN, F. H., 2026. FreshKeeper: an IoT food spoilage "
        "prediction prototype. Source code, MIT licence. Available at: "
        f"https://github.com/faiazyen/freshkeeper",
        "CALIFA URQUIZA, M. A., 2019. MQSensorsLib: Arduino library for MQ "
        "series gas sensors, with sensitivity-curve coefficients digitised from "
        "the manufacturer datasheets. Available at: "
        "https://github.com/miguel5612/MQSensorsLib",
        "PRIMATE LABS, 2026. Geekbench 6 CPU Benchmark Chart. Available at: "
        "https://browser.geekbench.com/v6/cpu [retrieved September 2026].",
        "PROJECT-AGML, 2024. fresh_rotten_fruit_classification. HuggingFace "
        "Datasets. Licensed CC-BY-4.0. Available at: "
        "https://huggingface.co/datasets/Project-AgML/fresh_rotten_fruit_classification",
        "HANWEI ELECTRONICS, n.d. MQ-3 Semiconductor Sensor for Alcohol. "
        "Technical datasheet.",
        "HANWEI ELECTRONICS, n.d. MQ-135 Semiconductor Sensor for Air Quality. "
        "Technical datasheet.",
        "MICROCHIP TECHNOLOGY, 2008. MCP3004/3008 2.7V 4-Channel/8-Channel "
        "10-Bit A/D Converters with SPI Serial Interface. Datasheet DS21295D.",
        "AVIA SEMICONDUCTOR, n.d. HX711 24-Bit Analog-to-Digital Converter for "
        "Weigh Scales. Datasheet.",
        "AOSONG ELECTRONICS, n.d. AM2302 (DHT22) Digital Temperature and "
        "Humidity Sensor. Datasheet.",
    ]:
        paragraph = para(document, entry, space_after=8)
        paragraph.paragraph_format.line_spacing = 1.15

    page_break(document)

    # ==================================================================
    heading(document, "List of pictures, tables, graphs and abbreviations", 1)

    heading(document, "List of pictures", 2)
    para(document,
         "Figures are numbered in order of appearance. Every one is generated "
         "by a script in the repository rather than drawn by hand.",
         space_after=8)
    list_of(document, "figure")

    heading(document, "List of tables", 2)
    list_of(document, "table")

    heading(document, "List of graphs", 2)
    para(document,
         "Graphs are integrated with the figures above; see in particular the "
         "sensor trajectories, the shelf-life calibration, the ablation "
         "comparison and the training curves.", justify=False)

    heading(document, "List of source listings", 2)
    list_of(document, "listing")

    heading(document, "List of abbreviations", 2)

    table(document,
          ["Abbreviation", "Meaning"],
          [["ADC", "Analogue-to-digital converter"],
           ["API", "Application programming interface"],
           ["AUC", "Area under the receiver operating characteristic curve"],
           ["BCM", "Broadcom GPIO pin numbering scheme"],
           ["CNN", "Convolutional neural network"],
           ["CSI", "Camera Serial Interface"],
           ["CFU", "Colony-forming unit"],
           ["FAO", "Food and Agriculture Organization of the United Nations"],
           ["GPIO", "General-purpose input/output"],
           ["HTTP", "Hypertext Transfer Protocol"],
           ["IoT", "Internet of Things"],
           ["JPEG", "Joint Photographic Experts Group image format"],
           ["LED", "Light-emitting diode"],
           ["MLP", "Multi-layer perceptron"],
           ["MOSFET", "Metal-oxide-semiconductor field-effect transistor"],
           ["MQTT", "Message Queuing Telemetry Transport"],
           ["ORM", "Object-relational mapping"],
           ["ppm", "Parts per million"],
           ["REST", "Representational state transfer"],
           ["RH", "Relative humidity"],
           ["ROI", "Region of interest"],
           ["SDG", "Sustainable Development Goal"],
           ["SPI", "Serial Peripheral Interface"],
           ["SUS", "System Usability Scale"],
           ["TFLite", "TensorFlow Lite"],
           ["UNEP", "United Nations Environment Programme"],
           ["VOC", "Volatile organic compound"],
           ["VPD", "Vapour pressure deficit"],
           ["WAL", "Write-ahead logging"]],
          "Table 12", "Abbreviations used in this thesis.",
          widths=[3.5, 11.0], font_size=9.5)

    page_break(document)

    # ==================================================================
    unnumbered_heading(document, "Appendix", 1)

    unnumbered_heading(document, "Appendix A: Source code", 2)

    para(document,
         f"The complete implementation is {R.n(R.loc)} lines of Python across "
         f"{R.files} tracked files. "
         "The modules reproduced here are the ones a reader would need to check "
         "the claims in Chapters 4 and 5. Everything else, including the test "
         "suite, the training scripts and the interface, is in the repository "
         "at https://github.com/faiazyen/freshkeeper.")

    _listing(document, "A.1", "freshkeeper/hardware/spoilage_model.py",
             REPO / "freshkeeper/hardware/spoilage_model.py",
             "The physical spoilage model: Ratkowsky growth, the modified "
             "Gompertz curve, vapour pressure deficit, MQ sensor conversion, "
             "and the per-commodity calibration.")

    _listing(document, "A.2", "freshkeeper/hardware/base.py",
             REPO / "freshkeeper/hardware/base.py",
             "The sensor abstraction. Nothing above this layer imports a GPIO "
             "library, which is what lets the whole system run without "
             "hardware.")

    _listing(document, "A.3", "freshkeeper/alerts.py",
             REPO / "freshkeeper/alerts.py",
             "Freshness scoring, trend extrapolation and the alert rules, "
             "including the three mechanisms that hold the notification rate "
             "down.")

    _listing(document, "A.4", "freshkeeper/ml/model.py",
             REPO / "freshkeeper/ml/model.py",
             "Network definitions: the MobileNetV2 backbone, the visual "
             "classifier, the late-fusion model with its optional projection, "
             "and the ablation baselines.")

    _listing(document, "A.5", "scripts/audit_dataset.py",
             REPO / "scripts/audit_dataset.py",
             "The dataset audit: embedding, near-duplicate linking, union-find "
             "grouping and the group-aware split.")

    _listing(document, "A.6", "tests/test_spoilage_model.py",
             REPO / "tests/test_spoilage_model.py",
             "Physics tests, including the calibration test that fails if any "
             "growth coefficient drifts from its published reference.")

    unnumbered_heading(document, "Appendix B: Repository structure", 2)

    code_block(document,
               '''freshkeeper/
├── freshkeeper/
│   ├── hardware/
│   │   ├── spoilage_model.py    Ratkowsky, Gompertz, VPD, MQ curves
│   │   ├── base.py              SensorBackend interface, SensorSample
│   │   ├── sim_backend.py       simulated array + fridge thermal model
│   │   └── rpi_backend.py       real drivers: GPIO, SPI, CSI
│   ├── ml/
│   │   ├── model.py             backbone, fusion head, ablation baselines
│   │   ├── embeddings.py        cache frozen-backbone embeddings
│   │   ├── train_cnn.py         two-stage transfer learning
│   │   ├── sensor_corpus.py     pair real images with simulated readings
│   │   ├── train_fusion.py      fusion model and ablations
│   │   ├── evaluate.py          test metrics, confusion matrices, figures
│   │   ├── export_tflite.py     edge conversion and benchmarking
│   │   └── inference.py         the measurement cycle
│   ├── db/
│   │   ├── models.py            SQLAlchemy schema
│   │   └── session.py           engine, pragmas, session scope
│   ├── acquisition/scheduler.py background measurement loop
│   ├── api/app.py               Flask REST API
│   └── alerts.py                scoring, trends, alert rules
├── frontend/                    Vue 3 single-page interface
├── scripts/
│   ├── download_dataset.sh      fetch the corpus
│   ├── prepare_dataset.py       decode, resize, stratified split
│   ├── audit_dataset.py         leakage audit and group-aware split
│   ├── make_diagrams.py         schematic and analysis figures
│   ├── capture_screenshots.py   interface figures
│   ├── benchmark_pipeline.py    end-to-end inference cost
│   ├── seed_demo.py             accelerated demonstration run
│   └── run_server.py            start the web interface
├── tests/                       automated tests (count in results/test_metrics.json)
├── docs/figures/                every figure used in this thesis
├── results/                     machine-readable metrics per stage
├── Makefile                     make all reruns the whole pipeline
└── requirements.txt             pinned dependencies''',
               "Listing B.1",
               "Repository layout. The Makefile target `all` regenerates every "
               "result and figure in this thesis from the raw dataset "
               f"download. The repository is public at https://github.com/faiazyen/freshkeeper.")

    unnumbered_heading(document, "Appendix C: Reproducing the results", 2)

    para(document,
         "Python 3.12 is required. TensorFlow does not work on the Python 3.9 "
         "that ships with macOS, which cost an hour to discover. Start by "
         f"cloning the repository from https://github.com/faiazyen/freshkeeper.")

    code_block(document,
               '''make venv install     # create the environment, install dependencies
make data             # download the corpus, decode and split it
make audit            # near-duplicate audit, group-aware re-split
make embeddings       # cache frozen-backbone embeddings
make train            # two-stage transfer learning for the visual CNN
make corpus           # generate the paired sensor corpus
make fusion           # train fusion and both ablation baselines
make evaluate         # test-set metrics and confusion matrices
make tflite bench     # edge conversion and inference profiling
make diagrams         # regenerate every schematic and analysis figure
make demo serve       # seed the demonstration and start the interface
make test coverage    # the full suite with a coverage report

make all              # everything above, about 40 minutes''',
               "Listing C.1",
               "Full reproduction. Every stochastic process is seeded, so a "
               "rerun reproduces the figures in this thesis exactly.")

    unnumbered_heading(document, "Appendix D: Machine-readable results", 2)

    para(document,
         "Each pipeline stage writes a JSON file. Every number quoted in "
         "Chapter 5 comes from one of these, and no figure in this thesis was "
         "transcribed by hand from a console.")

    table(document,
          ["File", "Contents"],
          [["results/dataset_audit.json",
            "Group sizes, linking pairs, residual leakage, nearest-neighbour "
            "percentiles"],
           ["results/cnn_training_history.json",
            "Per-epoch metrics for both transfer-learning stages"],
           ["results/sensor_corpus_meta.json",
            "Simulation parameters, class balance, provenance statement"],
           ["results/fusion_training.json",
            "Training histories for all four three-state models"],
           ["results/evaluation.json",
            "Test metrics, per-class precision and recall, confusion matrices"],
           ["results/tflite_benchmark.json",
            "Size, latency and accuracy for each quantisation variant"],
           ["results/pipeline_benchmark.json",
            "Per-stage inference timings and the Raspberry Pi projection"]],
          "Table 13",
          "Machine-readable result files produced by the pipeline.",
          widths=[6.0, 8.5], font_size=9.0)


def _listing(document, number: str, title: str, path: Path, description: str,
             max_lines: int = 150) -> None:
    """Insert a source listing, truncated if very long."""
    unnumbered_heading(document, f"{number}  {title}", 3)
    para(document, description, space_after=4)
    if not path.exists():
        para(document, f"[source not found: {path}]", italic=True)
        return
    lines = path.read_text().splitlines()
    truncated = len(lines) > max_lines
    body = "\n".join(lines[:max_lines])
    if truncated:
        body += (f"\n\n    ... {len(lines) - max_lines} further lines; "
                 "the complete file is in the repository.")
    code_block(document, body, f"Listing {number}", f"{title} ({len(lines)} lines)",
               font_size=7.5)
