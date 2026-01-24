"""
Tests for Sheet.type and Sheet.content detection.

Sheet type is determined by:
- type="table": Section contains valid table(s)
- type="doc": Section contains no valid tables (text-only content)

Sheet content:
- content=None: When type="table"
- content=raw_markdown: When type="doc"
"""

from md_spreadsheet_parser import MultiTableParsingSchema, parse_workbook


def test_sheet_type_table_when_tables_found():
    """Sheet with valid table should have type='table' and content=None."""
    markdown = """# Workbook

## Sheet1

| A | B |
| - | - |
| 1 | 2 |
"""
    workbook = parse_workbook(markdown)

    assert len(workbook.sheets) == 1
    sheet = workbook.sheets[0]
    assert sheet.type == "table"
    assert sheet.content is None
    assert len(sheet.tables) == 1


def test_sheet_type_doc_when_no_tables():
    """Sheet with text only (no tables) should have type='doc' and content set."""
    markdown = """# Workbook

## Notes

This is just a documentation section.

- Bullet point 1
- Bullet point 2

Some more text content.
"""
    workbook = parse_workbook(markdown)

    assert len(workbook.sheets) == 1
    sheet = workbook.sheets[0]
    assert sheet.type == "doc"
    assert sheet.content is not None
    assert "This is just a documentation section." in sheet.content
    assert "- Bullet point 1" in sheet.content
    assert len(sheet.tables) == 0


def test_sheet_type_doc_empty_section():
    """Empty sheet section should have type='doc' with None or empty content."""
    markdown = """# Workbook

## Empty Section

## Another Sheet

| A |
| - |
| 1 |
"""
    workbook = parse_workbook(markdown)

    assert len(workbook.sheets) == 2

    # First sheet is empty
    empty_sheet = workbook.sheets[0]
    assert empty_sheet.name == "Empty Section"
    assert empty_sheet.type == "doc"
    # Empty content results in None (stripped empty string)
    assert empty_sheet.content is None
    assert len(empty_sheet.tables) == 0

    # Second sheet has table
    table_sheet = workbook.sheets[1]
    assert table_sheet.name == "Another Sheet"
    assert table_sheet.type == "table"
    assert table_sheet.content is None
    assert len(table_sheet.tables) == 1


def test_sheet_content_preserves_markdown():
    """Doc sheet content should preserve the raw markdown structure."""
    markdown = """# Workbook

## Documentation

### Subsection

Here is some **bold** and *italic* text.

```python
def hello():
    print("world")
```

> A blockquote
"""
    workbook = parse_workbook(markdown)

    assert len(workbook.sheets) == 1
    sheet = workbook.sheets[0]
    assert sheet.type == "doc"
    assert sheet.content is not None

    # Verify markdown structure preserved
    assert "### Subsection" in sheet.content
    assert "**bold**" in sheet.content
    assert "*italic*" in sheet.content
    assert "```python" in sheet.content
    assert "> A blockquote" in sheet.content


def test_mixed_sheets_table_and_doc():
    """Workbook with mixed table and doc sheets."""
    markdown = """# Workbook

## Data Sheet

| Name | Value |
| ---- | ----- |
| foo  | 123   |

## Readme

This is a documentation section explaining the data.

## Config

| Key | Setting |
| --- | ------- |
| a   | on      |
"""
    workbook = parse_workbook(markdown)

    assert len(workbook.sheets) == 3

    # First sheet: table
    assert workbook.sheets[0].name == "Data Sheet"
    assert workbook.sheets[0].type == "table"
    assert workbook.sheets[0].content is None
    assert len(workbook.sheets[0].tables) == 1

    # Second sheet: doc
    assert workbook.sheets[1].name == "Readme"
    assert workbook.sheets[1].type == "doc"
    assert workbook.sheets[1].content is not None
    assert "documentation section" in workbook.sheets[1].content
    assert len(workbook.sheets[1].tables) == 0

    # Third sheet: table
    assert workbook.sheets[2].name == "Config"
    assert workbook.sheets[2].type == "table"
    assert workbook.sheets[2].content is None
    assert len(workbook.sheets[2].tables) == 1


def test_sheet_type_json_serialization():
    """Sheet.json should include type and content fields."""
    markdown = """# Workbook

## TableSheet

| A |
| - |
| 1 |

## DocSheet

This is doc content.
"""
    workbook = parse_workbook(markdown)

    # Table sheet JSON
    table_json = workbook.sheets[0].json
    assert table_json["type"] == "table"
    assert table_json["content"] is None

    # Doc sheet JSON
    doc_json = workbook.sheets[1].json
    assert doc_json["type"] == "doc"
    assert doc_json["content"] is not None
    assert "This is doc content." in doc_json["content"]


def test_explicit_schema_preserves_sheet_type():
    """Sheet type detection works with explicit schema configuration."""
    markdown = """# Tables

## Sheet1

### MyTable

| A | B |
| - | - |
| 1 | 2 |

## Notes

Some documentation text here.
"""
    schema = MultiTableParsingSchema(
        root_marker="# Tables",
        sheet_header_level=2,
        table_header_level=3,
    )
    workbook = parse_workbook(markdown, schema)

    assert len(workbook.sheets) == 2

    # Sheet with table
    assert workbook.sheets[0].name == "Sheet1"
    assert workbook.sheets[0].type == "table"
    assert workbook.sheets[0].content is None

    # Sheet without table
    assert workbook.sheets[1].name == "Notes"
    assert workbook.sheets[1].type == "doc"
    assert "Some documentation text here." in workbook.sheets[1].content
