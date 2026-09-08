# Thesis document generator

Renders the thesis into the CZU FEM template from structured content.

```bash
python build.py                # writes ../../Main thesis.docx
python build.py out.docx       # or somewhere else
```

## Why generate rather than hand-edit

The supervisor's review of the previous draft noted that the table of contents
contained whole paragraphs. The cause was specific: about twenty-five body
paragraphs carried Heading 2 or Heading 3 styles, and Word builds its contents
list from heading styles. Generating the document makes that impossible — a
paragraph is body text because it was declared as body text — and `build.py`
additionally warns if any heading is longer than twelve words.

Two other things the generator handles that hand-editing gets wrong:

- **Numbering.** Figures, tables and listings number themselves, and the lists
  at the back are generated from the captions actually used. Hand-numbered
  captions drift the moment a section is inserted, which happened twice here.
- **Heading numbers.** The template's heading styles are numbered by Word, so
  heading text never carries its own "1.2" or "Chapter 3:" prefix.

The document is rendered twice. The first pass collects every caption; the
second renders the lists of figures and tables, which sit before the
appendices, from that snapshot.

## Files

| File | Contents |
|---|---|
| `docx_builder.py` | Template handling, styles, captions, tables, figures, TOC field |
| `content_front.py` | Title page, declaration, acknowledgement, abstract, contents |
| `content_ch1_2.py` | Introduction; Objectives and Methodology |
| `content_ch3.py` | Literature Review |
| `content_ch4.py` | Practical Part |
| `content_ch5.py` | Results and Discussion |
| `content_ch6_8.py` | Conclusion, References, Lists, Appendices |
| `build.py` | Assembly and validation |
| `check_document.py` | Renders to PDF and checks the layout |
| `results.py` | Loads every result file; all numbers in the text come from here |
| `check_numbers.py` | Verifies every result-derived number in the built .docx against the result files |

Figures are read from `../docs/figures`, so regenerate those first with
`make diagrams` and `make screenshots` if the results have changed.

## Checking the output

```bash
python check_document.py "../../Main thesis.docx"
```

Renders to PDF via LibreOffice and checks what the .docx cannot show: text past
the margin, captions that lost their figure, headings numbered twice, and code
listings that fell back to a proportional font because Consolas is not
installed. It also reports the page count of Chapters 1-6, which is the figure
the faculty measures against.

## Numbers

No result-derived number is a literal in the content modules. `results.py`
reads `../results/*.json` and the content modules format from it, so a rerun of
the pipeline changes the thesis by rebuilding. `check_numbers.py` then confirms
every expected value appears in the built document and that no unexplained
four-decimal figure does. The first draft typed its tables in by hand; three
of them were wrong within a day, and one number (stage-1 epochs) was from a
superseded run.
