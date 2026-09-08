"""Flag the paragraphs that still read as machine written, without rewriting them.

Rewriting them is the author's job under Rector's Directive 5/2019 Art. (5).
This report only says which paragraph, on which page, and which pattern it
matches, so the effort can go where it matters.

    python make_rewrite_report.py
"""

from __future__ import annotations

import re
import subprocess
import sys
import tempfile
from collections import Counter
from pathlib import Path

import docx
from docx.shared import Pt

import docx_builder as B

ROOT = Path(__file__).resolve().parents[1]
THESIS = ROOT / "Main thesis.docx"
OUT = ROOT / "Rewrite priorities.docx"
SOFFICE = "/Applications/LibreOffice.app/Contents/MacOS/soffice"

# Chapters the directive requires the author to write personally.
MUST_REWRITE = {"Abstract", "Objectives and Methodology", "Results and Discussion",
                "Conclusion"}


def page_index(pdf_path: Path) -> list[str]:
    import pymupdf
    doc = pymupdf.open(pdf_path)
    return [doc[i].get_text() for i in range(len(doc))]


def find_page(pages: list[str], snippet: str) -> int | None:
    probe = " ".join(snippet.split()[:8])
    for i, text in enumerate(pages):
        if probe and probe in " ".join(text.split()):
            return i + 1
    return None


def sentences(text: str) -> list[str]:
    return [s for s in re.split(r"(?<=[.!?])\s+", text.strip()) if s.split()]


def flags_for(text: str) -> list[str]:
    """Every machine-writing pattern this paragraph matches."""
    found = []
    sents = sentences(text)
    lens = [len(s.split()) for s in sents]

    if len(sents) >= 2 and lens[-1] <= 6 and lens[-2] >= 12:
        found.append("ends on a short sentence for effect")
    if re.search(r"[a-z)]: [a-z]", text):
        found.append("colon used instead of a full stop")
    if len(sents) >= 3:
        # "The" and "It" open sentences constantly in normal English, so
        # repeating them is not a tell. Demonstratives are.
        common = {"the", "it", "a", "an", "in", "for", "but", "and", "so", "if"}
        openers = [s.split()[0].lower() for s in sents if s.split()]
        repeated = [w for w, c in Counter(openers).items()
                    if c >= 3 and len(w) > 2 and w not in common]
        if repeated:
            found.append(f"three or more sentences start with '{repeated[0]}'")
    if re.search(r"\b(not just|not only)\b.{0,60}\b(but|it is)\b", text, re.I):
        found.append("'not only X but Y' construction")
    if len(lens) >= 4 and max(lens) - min(lens) <= 6:
        found.append("every sentence about the same length")
    if re.search(r"\b(That is|This is) (why|what|the|exactly)\b", text):
        found.append("tidy summing-up sentence at the end")
    if len(re.findall(r", which\b", text)) >= 2:
        found.append("two or more 'which' clauses stacked")
    if re.search(r"\b\w+, \w+ and \w+\b.{0,80}\b\w+, \w+ and \w+\b", text):
        found.append("two lists of three in one paragraph")
    if re.search(r"\bIt is (worth|important|clear|fair)\b", text):
        found.append("'it is worth/important' opener")
    if len(text.split()) > 110:
        found.append("very long paragraph, over 110 words")
    return found


def main() -> int:
    if not THESIS.exists():
        raise SystemExit(f"{THESIS} not found")

    with tempfile.TemporaryDirectory() as tmp:
        subprocess.run([SOFFICE, "--headless", "--convert-to", "pdf",
                        "--outdir", tmp, str(THESIS)], check=True, capture_output=True)
        pages = page_index(Path(tmp) / (THESIS.stem + ".pdf"))

    src = docx.Document(THESIS)
    chapter = "Front matter"
    records = []
    for para in src.paragraphs:
        text = para.text.strip()
        if not text:
            continue
        if para.style.name == "Heading 1":
            chapter = text
            continue
        if para.style.name.startswith("Heading"):
            continue
        if para.style.name not in ("Normal", "List Paragraph"):
            continue
        # Reference entries, code listings and the appendix are not prose.
        if chapter in ("References", "Appendix",
                       "List of pictures, tables, graphs and abbreviations"):
            continue
        if len(text.split()) < 25 or "def " in text or text.startswith(
                ("Figure ", "Table ", "Listing ", "[DISCLOSURE")):
            continue
        if re.match(r"^[A-ZÀ-Ž][A-ZÀ-Ž'\- ,.]+,\s*\d{4}", text):  # a citation
            continue
        found = flags_for(text)
        if found:
            records.append({
                "chapter": chapter, "text": text, "flags": found,
                "page": find_page(pages, text),
                "priority": ("A" if chapter in MUST_REWRITE else "B"),
            })

    B.reset_registry()
    d = B.new_document()
    h = d.add_paragraph()
    run = h.add_run("Rewrite priorities")
    run.bold = True
    run.font.size = Pt(16)
    h.paragraph_format.space_after = Pt(10)

    B.para(d,
           "This report lists the paragraphs that still read as machine "
           "written, with the page and the pattern each one matches. It does "
           "not rewrite them. Under Rector's Directive 5/2019 Art. (5) the "
           "results and conclusions have to be written by you, and a machine "
           "rewriting them again would not change that.")

    counts = Counter(r["priority"] for r in records)
    B.para(d,
           f"{len(records)} paragraphs are flagged. "
           f"{counts.get('A', 0)} of them are in the chapters the directive "
           f"requires you to write yourself. {counts.get('B', 0)} are in the "
           "other chapters, where a lighter pass is enough.")

    B.heading(d, "Priority A: rewrite these from the fact sheet", 1)
    B.para(d,
           "The abstract and Chapters 2, 5 and 6. Do not edit the sentences "
           "below. Close the draft, open the fact sheet, and write what you "
           "think the numbers show. Then compare.")
    _emit(d, [r for r in records if r["priority"] == "A"])

    B.heading(d, "Priority B: a lighter pass is enough", 1)
    B.para(d,
           "Chapters 1, 3 and 4 are description and method rather than "
           "results, so Art. (5) does not apply to them in the same way. "
           "Reading each of these aloud and changing what sounds unlike you is "
           "enough.")
    _emit(d, [r for r in records if r["priority"] == "B"])

    B.heading(d, "What each pattern means", 1)
    for name, meaning in [
        ("ends on a short sentence for effect",
         "a long sentence followed by a very short one. Used once it is fine. "
         "Used in many paragraphs it becomes a rhythm no person keeps up."),
        ("colon used instead of a full stop",
         "a colon introducing a clause that could be its own sentence. Common "
         "in machine writing, less common in student writing."),
        ("three or more sentences start with the same word",
         "a deliberate repeated opening. It reads as constructed."),
        ("'not only X but Y' construction",
         "a balanced contrast. Fine once in a chapter."),
        ("every sentence about the same length",
         "no variation in rhythm within the paragraph."),
        ("tidy summing-up sentence at the end",
         "the paragraph closes its own argument. Real writing often just stops."),
        ("two or more 'which' clauses stacked",
         "long sentences held together by relative clauses."),
        ("two lists of three in one paragraph",
         "the rule of three used twice in a row."),
        ("'it is worth/important' opener", "filler that delays the point."),
        ("very long paragraph, over 110 words", "usually two paragraphs."),
    ]:
        B.rich_para(d, [(f"{name}. ", "b"), (meaning, "")])

    d.save(str(OUT))
    print(f"Wrote {OUT}")
    print(f"  {len(records)} flagged paragraphs "
          f"(A: {counts.get('A', 0)}, B: {counts.get('B', 0)})")
    for chapter, n in Counter(r["chapter"] for r in records).most_common():
        print(f"    {chapter:34s} {n}")
    return 0


def _emit(document, records) -> None:
    current = None
    for rec in records:
        if rec["chapter"] != current:
            current = rec["chapter"]
            B.heading(document, current, 2)
        page = f"p. {rec['page']}" if rec["page"] else "page not found"
        B.rich_para(document, [
            (f"{page}. ", "b"),
            ("; ".join(rec["flags"]) + ".", "i"),
        ], space_after=2)
        quote = " ".join(rec["text"].split())
        if len(quote) > 260:
            quote = quote[:260].rsplit(" ", 1)[0] + " ..."
        para = B.para(document, f'"{quote}"', space_after=10)
        para.paragraph_format.left_indent = docx.shared.Cm(0.8)
        for run in para.runs:
            run.font.size = Pt(9.5)


if __name__ == "__main__":
    sys.exit(main())
