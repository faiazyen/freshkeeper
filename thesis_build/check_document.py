"""Validate the rendered thesis PDF.

Catches the layout defects that are invisible in the .docx and obvious in
print: text past the margin, captions that lost their figure, headings
numbered twice, code that fell back to a proportional font.

Requires LibreOffice for the conversion:

    python check_document.py "../Main thesis.docx"
"""

from __future__ import annotations

import collections
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

SOFFICE = "/Applications/LibreOffice.app/Contents/MacOS/soffice"

# A4 with the faculty template's margins, in points, plus the small allowance
# LibreOffice's block boxes carry.
RIGHT_EDGE = 541.85
MARGIN_TOLERANCE = 2.0


def to_pdf(docx: Path, outdir: Path) -> Path:
    if not Path(SOFFICE).exists():
        raise SystemExit(f"LibreOffice not found at {SOFFICE}")
    subprocess.run(
        [SOFFICE, "--headless", "--convert-to", "pdf", "--outdir", str(outdir),
         str(docx)],
        check=True, capture_output=True)
    return outdir / (docx.stem + ".pdf")


def main() -> int:
    import pymupdf

    source = Path(sys.argv[1] if len(sys.argv) > 1 else "../Main thesis.docx")
    if not source.exists():
        raise SystemExit(f"{source} not found")

    with tempfile.TemporaryDirectory() as tmp:
        pdf_path = to_pdf(source, Path(tmp))
        document = pymupdf.open(pdf_path)
        pages = len(document)
        failures: list[str] = []

        def heading_page(label: str) -> int | None:
            for index in range(pages):
                for line in (document[index].get_text() or "").split("\n")[:4]:
                    if line.strip() == label:
                        return index + 1
            return None

        intro = heading_page("Introduction")
        references = heading_page("References")
        own_text = (references - intro) if (intro and references) else 0

        print(f"total pages          {pages}")
        print(f"own text (Ch 1-6)    {own_text} pages")
        if own_text < 60:
            failures.append(f"own text is {own_text} pages; the faculty asks for 60")

        # Text past the right margin, which usually means an over-wide code
        # listing or a table with too many columns.
        overflow = {
            index + 1
            for index in range(pages)
            for block in document[index].get_text("blocks")
            if block[4].strip() and block[2] > RIGHT_EDGE + MARGIN_TOLERANCE
        }
        print(f"margin overflows     {len(overflow)}")
        if overflow:
            failures.append(f"text past the right margin on pages {sorted(overflow)}")

        # Every caption should appear twice: once under its object, once in the
        # list at the back.
        captions: collections.Counter[str] = collections.Counter()
        for index in range(pages):
            for match in re.finditer(r"^(Figure|Table|Listing) (\d+):",
                                     document[index].get_text(), re.M):
                captions[match.group(0)] += 1
        stray = {k: v for k, v in captions.items() if v != 2}
        print(f"captions listed once and used once   "
              f"{len(captions) - len(stray)}/{len(captions)}")
        if stray:
            failures.append(f"captions appearing other than twice: {stray}")

        # A heading that carries its own label must not also be auto-numbered.
        doubled = [
            line.strip()
            for index in range(pages)
            for line in (document[index].get_text() or "").split("\n")
            if re.match(r"^\d+(\.\d+)*\s+(Appendix|A\.\d)", line.strip())
        ]
        print(f"doubled heading numbers   {len(doubled)}")
        if doubled:
            failures.append(f"headings numbered twice: {doubled[:3]}")

        # Code listings must render monospaced; Consolas silently falls back to
        # a proportional face off Windows.
        mono = any(
            "Mono" in span["font"] or "Courier" in span["font"]
            for index in range(pages)
            for block in document[index].get_text("dict")["blocks"]
            for line in block.get("lines", [])
            for span in line["spans"]
        )
        print(f"monospaced code font      {'yes' if mono else 'NO'}")
        if not mono:
            failures.append("code listings are not rendering in a monospaced font")

        print()
        if failures:
            print(f"{len(failures)} problem(s):")
            for failure in failures:
                print(f"  - {failure}")
            return 1
        print("All checks passed.")
        return 0


if __name__ == "__main__":
    sys.exit(main())
