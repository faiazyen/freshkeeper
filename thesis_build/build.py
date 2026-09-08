"""Assemble the thesis into a single .docx.

    python build.py [output.docx]
"""

from __future__ import annotations

import sys
from pathlib import Path

import docx_builder as builder
import content_ch1_2
import content_ch3
import content_ch4
import content_ch5
import content_ch6_8
import content_front

OUTPUT = Path(__file__).resolve().parents[1] / "Main thesis.docx"


def _render():
    document = builder.new_document()
    content_front.build(document)
    content_ch1_2.build(document)
    content_ch3.build(document)
    content_ch4.build(document)
    content_ch5.build(document)
    content_ch6_8.build(document)
    return document


def main() -> int:
    destination = Path(sys.argv[1]) if len(sys.argv) > 1 else OUTPUT

    # Pass one collects every caption so that the lists of figures and tables,
    # which sit before the appendices, can include items defined after them.
    builder.set_list_source(None)
    builder.reset_registry()
    _render()
    captions = builder.snapshot()

    # Pass two renders for real, with those lists populated.
    builder.set_list_source(captions)
    builder.reset_registry()
    document = _render()
    builder.add_footer_page_numbers(document)
    document.save(str(destination))

    words = sum(len(p.text.split()) for p in document.paragraphs)
    headings = [p for p in document.paragraphs if p.style.name.startswith("Heading")]
    body = [p for p in document.paragraphs
            if p.style.name in ("Normal", "List Paragraph")]

    print(f"Wrote {destination}")
    print(f"  paragraphs      {len(document.paragraphs)}")
    print(f"  headings        {len(headings)}")
    print(f"  body paragraphs {len(body)}")
    print(f"  tables          {len(document.tables)}")
    print(f"  figures         {len(document.inline_shapes)}")
    print(f"  words           {words:,}")

    # The supervisor's fourth comment was that body paragraphs appear in the
    # contents list. That happens when body text carries a heading style, so
    # check that every heading is short enough to actually be one.
    suspicious = [p for p in headings if len(p.text.split()) > 12]
    if suspicious:
        print("\n  WARNING: headings that look like body text:")
        for paragraph in suspicious:
            print(f"    {paragraph.style.name}: {paragraph.text[:80]}")
    else:
        print("\n  All headings are short: nothing that would pollute the "
              "contents list.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
