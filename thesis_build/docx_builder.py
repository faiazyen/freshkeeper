"""Render the thesis from structured content into the CZU FEM template.

Why generate rather than hand-edit. The supervisor's fourth comment -- that the
table of contents contains whole paragraphs -- has a specific cause: in the
previous draft about twenty-five body paragraphs carried Heading 2 or Heading 3
styles. Word builds its contents list from heading styles, so those paragraphs
were pulled in verbatim. Generating the document makes that class of mistake
impossible: a paragraph is a paragraph because it was declared as one.

The template's heading styles are already numbered by Word, so heading text
here never carries its own "1.2" or "Chapter 3:" prefix. Typing numbers into
headings that Word also numbers is how a document ends up reading "3 Chapter 3:
Literature Review".
"""

from __future__ import annotations

from pathlib import Path

import docx
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

TEMPLATE = Path(__file__).resolve().parents[1] / "template-bt-fem-single-sided-2021-en.docx"

CAPTION_COLOUR = RGBColor(0x44, 0x44, 0x44)

# Figures, tables and listings number themselves. Hand-numbered captions drift
# the moment a section is inserted, and this document had exactly that problem
# after two rounds of expansion.
_REGISTRY: dict[str, list[tuple[str, str]]] = {"figure": [], "table": [], "listing": []}
_SEQ: dict[str, int] = {"figure": 0, "table": 0, "listing": 0}


def next_label(kind: str, text: str) -> str:
    """Allocate the next number for a figure, table or listing."""
    _SEQ[kind] += 1
    label = {"figure": "Figure", "table": "Table", "listing": "Listing"}[kind]
    label = f"{label} {_SEQ[kind]}"
    _REGISTRY[kind].append((label, text))
    return label


#: Captions from a completed previous pass. The lists of figures and tables sit
#: in the middle of the document but must include items created after them, so
#: the document is rendered twice: pass one collects every caption, pass two
#: renders the lists from that snapshot.
_LIST_SOURCE: dict[str, list[tuple[str, str]]] | None = None


def registry(kind: str) -> list[tuple[str, str]]:
    """Captions for the lists at the back, from the snapshot when there is one."""
    if _LIST_SOURCE is not None:
        return list(_LIST_SOURCE.get(kind, []))
    return list(_REGISTRY[kind])


def snapshot() -> dict[str, list[tuple[str, str]]]:
    return {kind: list(items) for kind, items in _REGISTRY.items()}


def set_list_source(source: dict[str, list[tuple[str, str]]] | None) -> None:
    global _LIST_SOURCE
    _LIST_SOURCE = source


def reset_registry() -> None:
    for kind in _SEQ:
        _SEQ[kind] = 0
        _REGISTRY[kind].clear()
CODE_FONT = "Courier New"


def new_document() -> docx.Document:
    """Open the template and strip its placeholder body, keeping the styles."""
    document = docx.Document(str(TEMPLATE))
    body = document.element.body
    for child in list(body):
        if child.tag == qn("w:sectPr"):
            continue  # keep page size, margins, headers and footers
        body.remove(child)
    return document


# --------------------------------------------------------------------------
# Field codes
# --------------------------------------------------------------------------

def _field(paragraph, instruction: str, placeholder: str) -> None:
    """Insert a Word field, e.g. a TOC or a page number.

    python-docx has no field API, so the run is assembled from raw XML. The
    placeholder is what a reader sees until the field is refreshed with F9.
    """
    run = paragraph.add_run()
    begin = OxmlElement("w:fldChar")
    begin.set(qn("w:fldCharType"), "begin")
    instr = OxmlElement("w:instrText")
    instr.set(qn("xml:space"), "preserve")
    instr.text = instruction
    separate = OxmlElement("w:fldChar")
    separate.set(qn("w:fldCharType"), "separate")
    text = OxmlElement("w:t")
    text.text = placeholder
    end = OxmlElement("w:fldChar")
    end.set(qn("w:fldCharType"), "end")
    for element in (begin, instr, separate, text, end):
        run._r.append(element)


def add_toc(document, levels: str = "1-3") -> None:
    """Insert a table of contents built from heading levels 1 to 3.

    \\o restricts the field to outline levels, which is the point: the previous
    draft's contents list swept up body text because that text carried heading
    styles, not because the field was wrong.
    """
    paragraph = document.add_paragraph()
    _field(paragraph, f' TOC \\o "{levels}" \\h \\z \\u ',
           "Right-click and choose Update Field to build the contents list.")


def add_page_field(paragraph) -> None:
    _field(paragraph, " PAGE ", "1")


# --------------------------------------------------------------------------
# Block helpers
# --------------------------------------------------------------------------

def heading(document, text: str, level: int):
    """Add a numbered heading. Never include the number in ``text``."""
    return document.add_heading(text, level=level)


def unnumbered_heading(document, text: str, level: int):
    """A heading that keeps its style but carries no automatic number.

    The template numbers every heading style, which is right for the chapters
    and wrong for the appendices: a paragraph labelled "A.2" in its own text
    comes out as "9.1.2  A.2", numbered twice. Cancelling the numbering for
    these specific paragraphs -- rather than dropping the heading style -- keeps
    them in the contents list and keeps their formatting.
    """
    paragraph = document.add_heading(text, level=level)
    p_pr = paragraph._p.get_or_add_pPr()
    num_pr = OxmlElement("w:numPr")
    ilvl = OxmlElement("w:ilvl")
    ilvl.set(qn("w:val"), "0")
    num_id = OxmlElement("w:numId")
    num_id.set(qn("w:val"), "0")   # numId 0 cancels inherited list numbering
    num_pr.append(ilvl)
    num_pr.append(num_id)
    p_pr.append(num_pr)
    return paragraph


def para(document, text: str, style: str | None = None, justify: bool = True,
         space_after: int = 6, italic: bool = False, first_line_indent: bool = False):
    paragraph = document.add_paragraph(style=style)
    run = paragraph.add_run(text)
    run.italic = italic
    if justify:
        paragraph.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    paragraph.paragraph_format.space_after = Pt(space_after)
    paragraph.paragraph_format.line_spacing = 1.5
    if first_line_indent:
        paragraph.paragraph_format.first_line_indent = Cm(0.75)
    return paragraph


def rich_para(document, parts: list[tuple[str, str]], justify: bool = True,
              space_after: int = 6):
    """A paragraph with mixed formatting: parts are (text, style) pairs.

    Style is one of "", "b", "i", "bi", "code".
    """
    paragraph = document.add_paragraph()
    for text, style in parts:
        run = paragraph.add_run(text)
        run.bold = "b" in style
        run.italic = "i" in style
        if style == "code":
            run.font.name = CODE_FONT
            run.font.size = Pt(9.5)
    if justify:
        paragraph.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    paragraph.paragraph_format.space_after = Pt(space_after)
    paragraph.paragraph_format.line_spacing = 1.5
    return paragraph


def bullet(document, text: str, level: int = 0):
    """A bulleted item.

    The faculty template defines no List Bullet or List Number style, so the
    marker is a literal character with a hanging indent rather than a Word list
    definition. That is less elegant, but it survives the round trip through
    other word processors, which numbered-list definitions frequently do not.
    """
    paragraph = document.add_paragraph(style="List Paragraph")
    marker = "\u2022" if level == 0 else "\u2013"
    run = paragraph.add_run(f"{marker}\t{text}")
    paragraph.paragraph_format.left_indent = Cm(0.9 + 0.6 * level)
    paragraph.paragraph_format.first_line_indent = Cm(-0.45)
    paragraph.paragraph_format.space_after = Pt(4)
    paragraph.paragraph_format.line_spacing = 1.35
    paragraph.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    return paragraph


_COUNTERS: dict[int, int] = {}


def numbered(document, text: str, restart: bool = False, key: int = 0):
    """A numbered item. Pass restart=True on the first item of a new list."""
    if restart or key not in _COUNTERS:
        _COUNTERS[key] = 0
    _COUNTERS[key] += 1
    paragraph = document.add_paragraph(style="List Paragraph")
    paragraph.add_run(f"{_COUNTERS[key]}.\t{text}")
    paragraph.paragraph_format.left_indent = Cm(1.0)
    paragraph.paragraph_format.first_line_indent = Cm(-0.55)
    paragraph.paragraph_format.space_after = Pt(4)
    paragraph.paragraph_format.line_spacing = 1.35
    paragraph.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    return paragraph


def reset_numbering(key: int = 0) -> None:
    _COUNTERS[key] = 0


def caption(document, label: str, text: str):
    """A figure or table caption.

    Deliberately a Normal paragraph with direct formatting rather than a
    heading style. Captions styled as headings are exactly how body text ends
    up in a contents list.
    """
    paragraph = document.add_paragraph()
    bold_run = paragraph.add_run(f"{label}: ")
    bold_run.bold = True
    bold_run.font.size = Pt(9)
    bold_run.font.color.rgb = CAPTION_COLOUR
    run = paragraph.add_run(text)
    run.font.size = Pt(9)
    run.font.color.rgb = CAPTION_COLOUR
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    paragraph.paragraph_format.space_after = Pt(12)
    paragraph.paragraph_format.space_before = Pt(3)
    paragraph.paragraph_format.line_spacing = 1.0
    return paragraph


def figure(document, path: Path | str, label: str, text: str, width_cm: float = 15.0,
           short: str | None = None):
    """Insert a figure. ``label`` is ignored; numbering is automatic."""
    path = Path(path)
    if not path.exists():
        para(document, f"[missing figure: {path}]", italic=True)
        return
    paragraph = document.add_paragraph()
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    paragraph.paragraph_format.space_before = Pt(10)
    paragraph.paragraph_format.space_after = Pt(2)
    paragraph.add_run().add_picture(str(path), width=Cm(width_cm))
    caption(document, next_label("figure", short or _first_sentence(text)), text)


def table(document, headers: list[str], rows: list[list[str]], label: str,
          text: str, widths: list[float] | None = None, font_size: float = 9.0,
          short: str | None = None):
    """Insert a table. ``label`` is ignored; numbering is automatic."""
    tbl = document.add_table(rows=1, cols=len(headers))
    tbl.style = "Table Grid"
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER

    header_cells = tbl.rows[0].cells
    for cell, text_value in zip(header_cells, headers):
        cell.text = ""
        paragraph = cell.paragraphs[0]
        run = paragraph.add_run(text_value)
        run.bold = True
        run.font.size = Pt(font_size)
        paragraph.paragraph_format.space_after = Pt(2)
        paragraph.paragraph_format.space_before = Pt(2)
        _shade(cell, "E8EEF4")

    for row_values in rows:
        cells = tbl.add_row().cells
        for cell, value in zip(cells, row_values):
            cell.text = ""
            paragraph = cell.paragraphs[0]
            run = paragraph.add_run(str(value))
            run.font.size = Pt(font_size)
            if str(value).startswith("**") and str(value).endswith("**"):
                run.text = str(value)[2:-2]
                run.bold = True
            paragraph.paragraph_format.space_after = Pt(2)
            paragraph.paragraph_format.space_before = Pt(2)

    if widths:
        for row in tbl.rows:
            for cell, width in zip(row.cells, widths):
                cell.width = Cm(width)

    # Repeat the header when a table spans a page break.
    _repeat_header(tbl.rows[0])
    caption(document, next_label("table", short or _first_sentence(text)), text)
    return tbl


def _shade(cell, hex_colour: str) -> None:
    shading = OxmlElement("w:shd")
    shading.set(qn("w:val"), "clear")
    shading.set(qn("w:fill"), hex_colour)
    cell._tc.get_or_add_tcPr().append(shading)


def _repeat_header(row) -> None:
    tr_pr = row._tr.get_or_add_trPr()
    header = OxmlElement("w:tblHeader")
    header.set(qn("w:val"), "true")
    tr_pr.append(header)


def code_block(document, code: str, label: str | None = None, text: str | None = None,
               font_size: float = 8.5, short: str | None = None):
    """A monospaced listing with a light background."""
    paragraph = document.add_paragraph()
    paragraph.paragraph_format.left_indent = Cm(0.4)
    paragraph.paragraph_format.space_before = Pt(6)
    paragraph.paragraph_format.space_after = Pt(2)
    paragraph.paragraph_format.line_spacing = 1.0
    run = paragraph.add_run(code.rstrip("\n"))
    run.font.name = CODE_FONT
    run.font.size = Pt(font_size)
    rpr = run._r.get_or_add_rPr()
    rfonts = rpr.find(qn("w:rFonts"))
    if rfonts is None:
        rfonts = OxmlElement("w:rFonts")
        rpr.append(rfonts)
    rfonts.set(qn("w:ascii"), CODE_FONT)
    rfonts.set(qn("w:hAnsi"), CODE_FONT)

    shading = OxmlElement("w:shd")
    shading.set(qn("w:val"), "clear")
    shading.set(qn("w:fill"), "F6F8FA")
    paragraph._p.get_or_add_pPr().append(shading)

    if label and text:
        caption(document, next_label("listing", short or _first_sentence(text)), text)
    return paragraph


def _first_sentence(text: str, limit: int = 90) -> str:
    """A short caption for the lists at the back of the document."""
    sentence = text.split(". ")[0].rstrip(".")
    return sentence if len(sentence) <= limit else sentence[:limit].rsplit(" ", 1)[0]


def list_of(document, kind: str) -> None:
    """Write the recorded captions for one kind as a list."""
    for label, text in registry(kind):
        paragraph = document.add_paragraph()
        run = paragraph.add_run(f"{label}: ")
        run.bold = True
        paragraph.add_run(text)
        paragraph.paragraph_format.space_after = Pt(3)
        paragraph.paragraph_format.line_spacing = 1.2
        paragraph.paragraph_format.left_indent = Cm(1.2)
        paragraph.paragraph_format.first_line_indent = Cm(-1.2)


def page_break(document) -> None:
    document.add_paragraph().add_run().add_break(WD_BREAK.PAGE)


def add_footer_page_numbers(document) -> None:
    for section in document.sections:
        footer = section.footer
        paragraph = footer.paragraphs[0] if footer.paragraphs else footer.add_paragraph()
        paragraph.text = ""
        paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
        add_page_field(paragraph)
