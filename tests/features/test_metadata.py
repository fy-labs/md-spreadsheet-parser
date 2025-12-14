import pytest
from md_spreadsheet_parser.generator import generate_table_markdown
from md_spreadsheet_parser.models import Table
from md_spreadsheet_parser.parsing import parse_sheet, parse_table
from md_spreadsheet_parser.schemas import MultiTableParsingSchema


def test_parse_metadata_after_table():
    markdown = """
| A | B |
|---|---|
| 1 | 2 |
<!-- md-spreadsheet-metadata: {"columnWidths": [100, 200]} -->
""".strip()

    # We expect schema handling to strip whitespace usually
    table = parse_table(markdown)

    assert table.rows == [["1", "2"]]
    # Metadata should be extracted
    assert "visual" in table.metadata
    assert table.metadata["visual"] == {"columnWidths": [100, 200]}


def test_parse_metadata_complex_json():
    # Test with nested objects and potentially complex data
    markdown = """
| Header |
|---|
| Data |
<!-- md-spreadsheet-metadata: {"filters": {"0": {"type": "text", "val": "abc"}}, "hidden": [1]} -->
""".strip()

    table = parse_table(markdown)
    assert table.rows == [["Data"]]
    assert table.metadata["visual"]["filters"]["0"]["val"] == "abc"
    assert table.metadata["visual"]["hidden"] == [1]


def test_generate_metadata_comment():
    table = Table(
        headers=["Col1"], rows=[["Val1"]], metadata={"visual": {"columnWidths": [123]}}
    )

    md = generate_table_markdown(table)

    expected_comment = '<!-- md-spreadsheet-metadata: {"columnWidths": [123]} -->'
    assert expected_comment in md
    # Ensure it follows the table with an empty line
    lines = md.split("\n")
    assert lines[-1] == expected_comment
    assert lines[-2] == ""


def test_sheet_parsing_with_metadata():
    # Verify metadata is preserved when parsing a full sheet
    markdown = """# Sheet 1

| A |
|---|
| 1 |
<!-- md-spreadsheet-metadata: {"test": true} -->
"""
    sheet = parse_sheet(markdown, "Sheet 1", MultiTableParsingSchema())
    assert len(sheet.tables) == 1
    assert sheet.tables[0].metadata["visual"]["test"] is True


def test_parse_metadata_with_empty_lines():
    markdown = """
| A |
|---|
| 1 |


<!-- md-spreadsheet-metadata: {"columnWidths": [100]} -->
""".strip()

    table = parse_table(markdown)
    assert table.rows == [["1"]]
    assert "visual" in table.metadata
    assert table.metadata["visual"]["columnWidths"] == [100]


def test_sheet_parsing_with_gapped_metadata():
    markdown = """# Sheet

| A |
|---|
| 1 |


<!-- md-spreadsheet-metadata: {"test": true} -->

# Next Section
"""
    sheet = parse_sheet(markdown, "Sheet", MultiTableParsingSchema())
    assert len(sheet.tables) == 1
    assert "visual" in sheet.tables[0].metadata
    assert sheet.tables[0].metadata["visual"]["test"] is True


def test_simple_parsing_with_gapped_metadata():
    # Test without headers (Simple extraction)
    markdown = """
| A |
|---|
| 1 |


<!-- md-spreadsheet-metadata: {"columnWidths": [100]} -->
""".strip()

    schema = MultiTableParsingSchema(table_header_level=None, capture_description=False)
    sheet = parse_sheet(markdown, "Sheet", schema)

    assert len(sheet.tables) == 1
    assert "visual" in sheet.tables[0].metadata
    assert sheet.tables[0].metadata["visual"]["columnWidths"] == [100]
