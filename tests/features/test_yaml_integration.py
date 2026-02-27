from md_spreadsheet_parser.parsing import parse_workbook


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
## Sheet
| A |
|---|
| 1 |

<!-- md-spreadsheet-workbook-metadata: {"title": "Comment Title", "author": "original", "guiData": 123} -->
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
# Round-trip tests: parse → to_markdown() → text comparison
# ==========================================


def test_frontmatter_roundtrip_basic():
    """Basic round-trip: parse frontmatter, verify to_markdown() output text."""
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
    wb = parse_workbook(original_md)

    # Verify initial parse is correct
    assert wb.name == "My Workbook"
    assert wb.metadata is not None
    assert wb.metadata["header_type"] == "frontmatter"
    assert wb.metadata["frontmatter"]["description"] == "A test workbook"
    assert wb.metadata["frontmatter"]["version"] == 2

    expected = """\
---
title: My Workbook
description: A test workbook
version: 2
---

## Sheet 1

| Col A | Col B |
| --- | --- |
| 1 | 2 |"""
    assert wb.to_markdown() == expected


def test_frontmatter_roundtrip_preserves_format():
    """to_markdown() must output frontmatter, not H1 + comment."""
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
    wb = parse_workbook(original_md)

    expected = """\
---
title: Frontmatter Book
author: Jane
---

## Data

| X |
| --- |
| y |"""
    result = wb.to_markdown()
    assert result == expected, (
        f"Generated output does not match expected.\n"
        f"Expected:\n{expected}\n\nGot:\n{result}"
    )


def test_frontmatter_roundtrip_with_metadata_comment_coexistence():
    """Frontmatter → YAML block, comment metadata → HTML comment at end."""
    original_md = """\
---
title: Mixed Book
author: frontmatter_author
---
## Sheet
| A |
|---|
| 1 |

<!-- md-spreadsheet-workbook-metadata: {"guiData": 42, "author": "comment_author"} -->
"""
    wb = parse_workbook(original_md)

    # Verify isolation
    assert wb.metadata is not None
    assert wb.metadata["frontmatter"]["author"] == "frontmatter_author"
    assert wb.metadata["guiData"] == 42

    expected = """\
---
title: Mixed Book
author: frontmatter_author
---

## Sheet

| A |
| --- |
| 1 |

<!-- md-spreadsheet-workbook-metadata: {"guiData": 42, "author": "comment_author"} -->"""
    assert wb.to_markdown() == expected


def test_frontmatter_yaml_comments_lost_on_roundtrip():
    """YAML comments are stripped during round-trip (accepted behavior)."""
    original_md = """\
---
title: Commented Book
author: Jane # Lead author
status: draft # Will change to published
tags:
  - fiction
  # - non-fiction  (commented out)
  - novel
---
## Chapter
| A |
|---|
| 1 |
"""
    wb = parse_workbook(original_md)

    # Comments are stripped — output will not contain them
    expected = """\
---
title: Commented Book
author: Jane
status: draft
tags:
  - fiction
  - novel
---

## Chapter

| A |
| --- |
| 1 |"""
    assert wb.to_markdown() == expected


def test_frontmatter_roundtrip_dendron_style():
    """Dendron-style daily note: quoted strings, large ints, lists."""
    original_md = """\
---
title: "2026-02-25"
desc: Daily note for today
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
    wb = parse_workbook(original_md)

    expected = """\
---
title: "2026-02-25"
desc: Daily note for today
updated: 1708851375000
created: 1708851375000
tags:
  - daily
  - journal
---

## Tasks

| Task | Status |
| --- | --- |
| Buy milk | pending |"""
    assert wb.to_markdown() == expected
