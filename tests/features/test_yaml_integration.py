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
    assert workbook.metadata["description"] == "A test app"
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
    assert workbook.metadata == {}
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
    # The lines relative to text after frontmatter removal (lines are shifted by +4):
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
    # Frontmatter MUST take precedence over comment
    assert workbook.name == "Frontmatter Title"
    assert workbook.metadata is not None
    assert workbook.metadata["title"] == "Frontmatter Title"
    assert workbook.metadata["author"] == "overriding_author"
    assert workbook.metadata["guiData"] == 123  # Non-overlapping keys merge


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

    # Metadata should contain all the other attributes
    assert workbook.metadata is not None
    assert workbook.metadata["id"] == "1234567890abc"
    assert workbook.metadata["desc"] == "Daily note for today"
    assert workbook.metadata["updated"] == 1708851375000
    assert workbook.metadata["tags"] == ["daily", "journal"]
    assert workbook.metadata["custom"] == {"weather": "sunny", "mood": 5}

    # Verify the table parsed correctly too
    assert len(workbook.sheets) == 1
    assert workbook.sheets[0].name == "Tasks"
    assert len(workbook.sheets[0].tables) == 1
    assert workbook.sheets[0].tables[0].rows == [
        ["Buy milk", "[ ]"],
        ["Write code", "[x]"],
    ]
