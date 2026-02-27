from md_spreadsheet_parser.generator import generate_workbook_markdown
from md_spreadsheet_parser.parsing import parse_workbook
from md_spreadsheet_parser.schemas import MultiTableParsingSchema


def test_frontmatter_with_title_creates_workbook():
    md = """---
title: My Cool App
description: A test app
---
## Sheet 1
| Col A |
|---|
| Val |
"""
    workbook = parse_workbook(md)
    assert workbook.name == "My Cool App"
    assert workbook.metadata is not None
    assert workbook.metadata["header_type"] == "frontmatter"
    assert workbook.metadata["frontmatter"]["description"] == "A test app"
    assert len(workbook.sheets) == 1
    assert workbook.sheets[0].name == "Sheet 1"


def test_frontmatter_without_title_not_h1():
    md = """---
author: john_doe
---
# Real Book
## Sheet 1
| A |
|---|
| 1 |
"""
    workbook = parse_workbook(md)
    assert workbook.name == "Real Book"
    # Frontmatter without title is ignored — no header_type or frontmatter key
    assert workbook.metadata is not None
    assert workbook.metadata.get("header_type") is None
    assert "frontmatter" not in workbook.metadata
    assert len(workbook.sheets) == 1


def test_frontmatter_with_title_and_multi_h1():
    md_content = """---
title: Book 1
---
## Sheet 1
| A |
|---|
| 1 |

# Book 2
## Sheet 2
| B |
|---|
| 2 |
"""
    # parse_workbook should stop at the next H1
    workbook1 = parse_workbook(md_content)
    assert workbook1.name == "Book 1"
    assert len(workbook1.sheets) == 1
    assert workbook1.sheets[0].name == "Sheet 1"

    # Prove that end_line is set correctly to stop before # Book 2
    assert workbook1.end_line == 5

    # Next workbook would be parsed correctly if we passed the remaining text
    # The frontmatter takes 3 lines (indexes 0,1,2). The next text starts at index 3.
    # index 5 in remaining text = 3 + 5 = index 8 in the original lines.
    lines = md_content.split("\n")
    remaining_text = "\n".join(lines[8:])
    workbook2 = parse_workbook(remaining_text)
    assert workbook2.name == "Book 2"
    assert len(workbook2.sheets) == 1
    assert workbook2.sheets[0].name == "Sheet 2"


def test_legacy_metadata_comment_precedence():
    md = """---
title: Frontmatter Title
author: overriding_author
---
<!-- md-spreadsheet-workbook-metadata: {"title": "Comment Title", "author": "original", "guiData": 123} -->
## Sheet
| A |
|---|
| 1 |
"""
    workbook = parse_workbook(md)
    # Frontmatter title becomes the workbook name
    assert workbook.name == "Frontmatter Title"
    assert workbook.metadata is not None
    # Frontmatter data is isolated in sub-dict
    assert workbook.metadata["frontmatter"]["title"] == "Frontmatter Title"
    assert workbook.metadata["frontmatter"]["author"] == "overriding_author"
    # Comment metadata stays at top level
    assert workbook.metadata["guiData"] == 123
    # Comment's "title" and "author" are at top level (not overwritten by frontmatter)
    assert workbook.metadata["title"] == "Comment Title"
    assert workbook.metadata["author"] == "original"


def test_dendron_daily_note_frontmatter_integration():
    md = """---
id: 1234567890abc
title: "2026-02-25"
desc: 'Daily note for today'
updated: 1708851375000
created: 1708851375000
tags:
  - daily
  - journal
custom:
  weather: sunny
  mood: 5 # Rating out of 5
---
## Tasks
| Task | Status |
|---|---|
| Buy milk | [ ] |
| Write code | [x] |
"""
    workbook = parse_workbook(md)
    # The title should become the workbook name
    assert workbook.name == "2026-02-25"

    # Metadata should contain frontmatter isolation
    assert workbook.metadata is not None
    assert workbook.metadata["header_type"] == "frontmatter"
    fm = workbook.metadata["frontmatter"]
    assert fm["id"] == "1234567890abc"
    assert fm["desc"] == "Daily note for today"
    assert fm["updated"] == 1708851375000
    assert fm["tags"] == ["daily", "journal"]
    assert fm["custom"] == {"weather": "sunny", "mood": 5}

    # Verify the table parsed correctly too
    assert len(workbook.sheets) == 1
    assert workbook.sheets[0].name == "Tasks"
    assert len(workbook.sheets[0].tables) == 1
    assert workbook.sheets[0].tables[0].rows == [
        ["Buy milk", "[ ]"],
        ["Write code", "[x]"],
    ]


# ==========================================
# Round-trip tests: parse → generate → re-parse
# ==========================================


def test_frontmatter_roundtrip_basic():
    """Basic round-trip: parse frontmatter, generate markdown, re-parse.

    The re-parsed Workbook's name, metadata, and table data
    MUST be identical to the first parse.
    """
    original_md = """\
---
title: My Workbook
description: A test workbook
version: 2
---
## Sheet 1
| Col A | Col B |
|---|---|
| 1 | 2 |
"""
    schema = MultiTableParsingSchema()
    wb1 = parse_workbook(original_md, schema)

    # Verify initial parse is correct
    assert wb1.name == "My Workbook"
    assert wb1.metadata is not None
    assert wb1.metadata["header_type"] == "frontmatter"
    fm = wb1.metadata["frontmatter"]
    assert fm["description"] == "A test workbook"
    assert fm["version"] == 2
    assert len(wb1.sheets) == 1
    assert wb1.sheets[0].tables[0].rows == [["1", "2"]]

    # Generate markdown from the parsed workbook
    generated_md = generate_workbook_markdown(wb1, schema)

    # Re-parse the generated markdown
    wb2 = parse_workbook(generated_md, schema)

    # The round-tripped workbook must have the same semantic content
    assert wb2.name == wb1.name, (
        f"Name mismatch after round-trip: {wb2.name!r} != {wb1.name!r}"
    )
    assert len(wb2.sheets) == len(wb1.sheets), (
        f"Sheet count mismatch: {len(wb2.sheets)} != {len(wb1.sheets)}"
    )
    assert wb2.sheets[0].name == wb1.sheets[0].name
    assert wb2.sheets[0].tables[0].headers == wb1.sheets[0].tables[0].headers
    assert wb2.sheets[0].tables[0].rows == wb1.sheets[0].tables[0].rows

    # Metadata round-trip: frontmatter sub-dict should survive
    assert wb2.metadata is not None
    assert wb2.metadata["header_type"] == "frontmatter"
    fm2 = wb2.metadata["frontmatter"]
    for key in ("description", "version"):
        assert key in fm2, f"Frontmatter key {key!r} lost after round-trip. fm2 = {fm2}"
        assert fm2[key] == fm[key], (
            f"frontmatter[{key!r}] mismatch: {fm2[key]!r} != {fm[key]!r}"
        )


def test_frontmatter_roundtrip_preserves_format():
    """Verify that the generated markdown preserves the YAML frontmatter format.

    If the original document used frontmatter, the generated output should also
    use frontmatter (not H1 heading + HTML comment metadata).
    """
    original_md = """\
---
title: Frontmatter Book
author: Jane
---
## Data
| X |
|---|
| y |
"""
    schema = MultiTableParsingSchema()
    wb = parse_workbook(original_md, schema)
    generated_md = generate_workbook_markdown(wb, schema)

    # The generated markdown SHOULD start with frontmatter
    assert generated_md.startswith("---\n"), (
        "Generated markdown does not start with YAML frontmatter delimiter.\n"
        f"Generated output:\n{generated_md}"
    )

    # The generated markdown should NOT contain an H1 heading for the workbook name
    # (because the name is in the frontmatter 'title' field)
    lines = generated_md.split("\n")
    h1_lines = [line for line in lines if line.startswith("# ")]
    assert len(h1_lines) == 0, (
        "Generated markdown contains H1 heading, but name should be in frontmatter.\n"
        f"H1 lines found: {h1_lines}\n"
        f"Generated output:\n{generated_md}"
    )


def test_frontmatter_roundtrip_with_metadata_comment_coexistence():
    """Round-trip with both frontmatter and comment metadata.

    Frontmatter is isolated. Comment metadata stays at top level.
    After round-trip, both should be preserved independently.
    """
    original_md = """\
---
title: Mixed Book
author: frontmatter_author
---
<!-- md-spreadsheet-workbook-metadata: {"guiData": 42, "author": "comment_author"} -->
## Sheet
| A |
|---|
| 1 |
"""
    schema = MultiTableParsingSchema()
    wb1 = parse_workbook(original_md, schema)

    # Frontmatter is isolated in sub-dict
    assert wb1.metadata is not None
    assert wb1.metadata["frontmatter"]["author"] == "frontmatter_author"
    # Comment metadata at top level
    assert wb1.metadata["guiData"] == 42
    assert wb1.metadata["author"] == "comment_author"

    generated_md = generate_workbook_markdown(wb1, schema)
    wb2 = parse_workbook(generated_md, schema)

    assert wb2.name == "Mixed Book"
    assert wb2.metadata is not None
    assert wb2.metadata["frontmatter"]["author"] == "frontmatter_author"
    assert wb2.metadata.get("guiData") == 42


def test_frontmatter_roundtrip_dendron_style():
    """Round-trip for a Dendron-style daily note with complex metadata.

    This tests lists and nested dicts survive the round-trip.
    """
    original_md = """\
---
title: "2026-02-25"
desc: 'Daily note for today'
updated: 1708851375000
created: 1708851375000
tags:
  - daily
  - journal
---
## Tasks
| Task | Status |
|---|---|
| Buy milk | pending |
"""
    schema = MultiTableParsingSchema()
    wb1 = parse_workbook(original_md, schema)

    assert wb1.name == "2026-02-25"
    assert wb1.metadata is not None
    fm1 = wb1.metadata["frontmatter"]
    assert fm1["tags"] == ["daily", "journal"]
    assert fm1["updated"] == 1708851375000

    generated_md = generate_workbook_markdown(wb1, schema)
    wb2 = parse_workbook(generated_md, schema)

    assert wb2.name == wb1.name
    assert wb2.metadata is not None
    fm2 = wb2.metadata["frontmatter"]

    # Scalar metadata should round-trip
    assert fm2.get("desc") == fm1["desc"]
    assert fm2.get("updated") == fm1["updated"]
    assert fm2.get("created") == fm1["created"]

    # Complex metadata (lists) should round-trip
    assert fm2.get("tags") == fm1["tags"], (
        f"Tags mismatch: {fm2.get('tags')!r} != {fm1['tags']!r}"
    )

    # Table data must survive
    assert len(wb2.sheets) == 1
    assert wb2.sheets[0].tables[0].rows == [["Buy milk", "pending"]]
