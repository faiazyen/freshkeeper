"""Front matter: title page, declaration, acknowledgement, abstracts."""

from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Pt

from docx_builder import add_toc, caption, heading, page_break, para

TITLE = "Design of an IoT-Based Food Spoilage Prediction System for Waste Reduction"
AUTHOR = "Faiaz Hossain Mazumder Yen"
SUPERVISOR = "Ing. Jiří Brožek, Ph.D."
DEPARTMENT = "Department of Information Engineering"
YEAR = "2026"

KEYWORDS = ("IoT, food waste reduction, spoilage prediction, sensor fusion, "
            "convolutional neural networks, predictive microbiology, Raspberry Pi, "
            "edge inference, Python, sustainable development")


def _centre(document, text: str, size: int, bold: bool = False,
            space_after: int = 12, caps: bool = False):
    paragraph = document.add_paragraph()
    run = paragraph.add_run(text.upper() if caps else text)
    run.bold = bold
    run.font.size = Pt(size)
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    paragraph.paragraph_format.space_after = Pt(space_after)
    return paragraph


def build(document) -> None:
    # -- title page ------------------------------------------------------
    _centre(document, "Czech University of Life Sciences Prague", 17, bold=True,
            space_after=6)
    _centre(document, "Faculty of Economics and Management", 14, space_after=4)
    _centre(document, DEPARTMENT, 13, space_after=90)
    _centre(document, "Bachelor Thesis", 20, bold=True, space_after=60)
    _centre(document, TITLE, 18, bold=True, space_after=50)
    _centre(document, AUTHOR, 14, space_after=6)
    _centre(document, f"Supervisor: {SUPERVISOR}", 12, space_after=90)
    _centre(document, f"© {YEAR} CZU Prague", 11, space_after=0)
    page_break(document)

    # -- assignment placeholder -----------------------------------------
    _centre(document, "Thesis Assignment", 14, bold=True, space_after=24)
    para(document,
         "Replace this page with the official thesis assignment exported to PDF "
         "from is.czu.cz, front page and back page, as required by the faculty "
         "template.", italic=True, justify=False)
    page_break(document)

    # -- declaration -----------------------------------------------------
    _centre(document, "Declaration", 14, bold=True, space_after=18)
    para(document,
         f'I declare that I have worked on my bachelor thesis titled "{TITLE}" '
         "by myself and I have used only the sources mentioned at the end of the "
         "thesis. As the author of the bachelor thesis, I declare that the thesis "
         "does not break any copyrights.")
    para(document,
         "The prototype software described in this thesis was written by the "
         "author and is published under the MIT licence. The image corpus used "
         "for training is a third-party dataset released under CC-BY-4.0 and is "
         "credited in Chapter 4 and in the references. Machine learning "
         "frameworks, libraries and the pretrained MobileNetV2 weights are "
         "third-party components used under their respective open-source "
         "licences.")
    para(document, "", space_after=36)
    para(document, "In Prague on ______________                "
                   "_________________________", justify=False)
    para(document, "                                                              "
                   f"      {AUTHOR}", justify=False)
    page_break(document)

    # -- acknowledgement -------------------------------------------------
    _centre(document, "Acknowledgement", 14, bold=True, space_after=18)
    para(document,
         f"I would like to thank {SUPERVISOR} for supervising this thesis and, in "
         "particular, for the review that prompted its substantial revision. The "
         "criticism that the earlier draft described a system without "
         "demonstrating that one existed was correct, and acting on it changed "
         "the work for the better: what had been a design document became a "
         "prototype that runs, with results that can be reproduced and, where "
         "they disappoint, reported as such.")
    para(document,
         "I also thank the Department of Information Engineering for the "
         "teaching that made the practical part possible, and the maintainers of "
         "the open-source projects this work is built on.")
    page_break(document)

    # -- abstract --------------------------------------------------------
    _centre(document, TITLE, 13, bold=True, space_after=18)
    _centre(document, "Abstract", 12, bold=True, space_after=10)
    para(document,
         "Households in developed countries discard a large share of the food "
         "they buy, and a recurring reason is uncertainty: people cannot tell "
         "whether an item is still good, so they throw it away to be safe. "
         "Printed dates do not help much, because they describe an item stored "
         "under ideal conditions rather than the item actually sitting in a "
         "particular refrigerator. This thesis designs, builds and evaluates a "
         "prototype that measures the conditions instead of assuming them.")
    para(document,
         "The system combines a camera, two metal-oxide gas sensors, a load cell "
         "and a temperature and humidity sensor on a Raspberry Pi 4, classifies "
         "each monitored item as fresh, marginal or spoiled, and presents the "
         "result through a web interface served from the device. All inference "
         "runs locally; no image leaves the home network. The software is "
         "complete and tested: 5,472 lines of Python across a physical spoilage "
         "model, a hardware abstraction layer with both real and simulated "
         "backends, a machine learning pipeline, a REST API, a database and a "
         "single-page interface, covered by 119 automated tests.")
    para(document,
         "Three results are reported. A MobileNetV2 classifier trained on 12,335 "
         "real photographs reaches 98.0% accuracy distinguishing fresh from "
         "rotten produce on a held-out split, after an audit found and removed "
         "near-duplicate leakage that had inflated an earlier figure. A physical "
         "spoilage model built from the Ratkowsky and Gompertz equations "
         "reproduces published refrigerated shelf lives for eight commodities to "
         "within 1.7%. On the three-state task, a sensor-only classifier reaches "
         "96.9% accuracy and the late-fusion model 96.0%, so fusion did not beat "
         "its own baseline. That negative result is analysed rather than "
         "hidden: because the simulated sensor features and the ground-truth "
         "labels derive from the same physical model, the sensor branch has "
         "privileged access to the target, and validating fusion honestly needs "
         "instrumented hardware.")
    para(document,
         "The boundary between what was measured and what was simulated is "
         "stated wherever a result depends on it. The images and their labels "
         "are real; the gas, temperature, humidity and mass readings are "
         "generated by the physical model; the Raspberry Pi drivers are written "
         "but not validated against instruments.")
    para(document, "", space_after=6)
    keyword_paragraph = document.add_paragraph()
    label = keyword_paragraph.add_run("Keywords: ")
    label.bold = True
    keyword_paragraph.add_run(KEYWORDS)
    keyword_paragraph.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    page_break(document)

    # -- contents --------------------------------------------------------
    contents_heading = document.add_paragraph()
    contents_run = contents_heading.add_run("Table of Contents")
    contents_run.bold = True
    contents_run.font.size = Pt(16)
    contents_heading.paragraph_format.space_after = Pt(14)
    add_toc(document)
    para(document,
         "To build this list in Word: click anywhere in it, press F9, and choose "
         "to update the entire table. In LibreOffice: Tools, then Update, then "
         "Indexes and Tables.", italic=True, space_after=4)
    page_break(document)
