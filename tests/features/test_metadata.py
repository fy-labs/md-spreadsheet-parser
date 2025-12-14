import pytest
from md_spreadsheet_parser.generator import generate_table_markdown
from md_spreadsheet_parser.models import Sheet, Table, Workbook
from md_spreadsheet_parser.parsing import parse_sheet, parse_table, parse_workbook
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
    assert table.metadata is not None
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
    assert table.metadata is not None
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
    assert sheet.tables[0].metadata is not None
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
    assert table.metadata is not None
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
    assert sheet.tables[0].metadata is not None
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
    assert sheet.tables[0].metadata is not None
    assert "visual" in sheet.tables[0].metadata
    assert sheet.tables[0].metadata["visual"]["columnWidths"] == [100]


# --- Consolidated Tests from test_sheet_metadata.py ---


def test_sheet_metadata_parsing():
    markdown = """# Tables

## Sheet 1

| A | B |
|---|---|
| 1 | 2 |

<!-- md-spreadsheet-sheet-metadata: {"layout": {"type": "split", "direction": "vertical"}} -->
"""
    workbook = parse_workbook(markdown)
    assert len(workbook.sheets) == 1
    sheet = workbook.sheets[0]
    assert sheet.name == "Sheet 1"
    assert sheet.metadata == {"layout": {"type": "split", "direction": "vertical"}}
    assert len(sheet.tables) == 1


def test_workbook_metadata_with_empty_lines():
    markdown = """# Tables

## Sheet 1

| A |
|---|
| 1 |

<!-- md-spreadsheet-sheet-metadata: {"layout": "relaxed"} -->
"""
    workbook = parse_workbook(markdown)
    assert len(workbook.sheets) == 1
    assert workbook.sheets[0].metadata == {"layout": "relaxed"}


def test_sheet_metadata_generation():
    table = Table(headers=["A", "B"], rows=[["1", "2"]])
    sheet = Sheet(
        name="Sheet 1", tables=[table], metadata={"layout": {"type": "split"}}
    )

    schema = MultiTableParsingSchema()
    workbook = Workbook(sheets=[sheet])
    generated = workbook.to_markdown(schema)

    expected_comment = (
        '<!-- md-spreadsheet-sheet-metadata: {"layout": {"type": "split"}} -->'
    )
    assert expected_comment in generated
    assert "## Sheet 1" in generated


def test_round_trip():
    original_md = """# Tables

## Sheet 1

| A |
|---|
| 1 |

<!-- md-spreadsheet-sheet-metadata: {"layout": "test"} -->
"""
    workbook = parse_workbook(original_md)
    assert workbook.sheets[0].metadata == {"layout": "test"}

    generated = workbook.to_markdown(MultiTableParsingSchema())
    # Note: Whitespace might vary slightly (empty lines), but data should be there.
    assert '<!-- md-spreadsheet-sheet-metadata: {"layout": "test"} -->' in generated

    workbook2 = parse_workbook(generated)
    assert workbook2.sheets[0].metadata == {"layout": "test"}


# --- Consolidated Tests from test_metadata_combinations.py ---


@pytest.mark.parametrize(
    "sheet_meta",
    [None, {"layout": {"type": "split", "direction": "vertical"}}, {"other": "data"}],
)
@pytest.mark.parametrize(
    "table_meta",
    [None, {"visual": {"bgColor": "#ff0000"}}, {"visual": {"hidden": True}}],
)
def test_metadata_round_trip_combinations(sheet_meta, table_meta):
    # Setup
    table = Table(headers=["A", "B"], rows=[["1", "2"]], metadata=table_meta)
    sheet = Sheet(name="Sheet 1", tables=[table], metadata=sheet_meta)
    workbook = Workbook(sheets=[sheet])
    schema = MultiTableParsingSchema()

    # Generate Markdown
    markdown = workbook.to_markdown(schema)

    # Verify Markdown Structure
    if sheet_meta:
        # Sheet metadata should be at the end (from v0.3.2)
        assert "<!-- md-spreadsheet-sheet-metadata:" in markdown
    else:
        assert "<!-- md-spreadsheet-sheet-metadata:" not in markdown

    if table_meta and "visual" in table_meta:
        assert "<!-- md-spreadsheet-metadata:" in markdown
    else:
        assert "<!-- md-spreadsheet-metadata:" not in markdown

    # Parse Back
    parsed_workbook = parse_workbook(markdown, schema)
    parsed_sheet = parsed_workbook.sheets[0]
    parsed_table = parsed_sheet.tables[0]

    # Verify Data
    assert parsed_sheet.metadata == (sheet_meta or {})

    # Table metadata might contain extra 'schema_used', so subset check or exact check if handled
    # Note: Table model also converts None to {}
    parsed_table_meta = parsed_table.metadata or {}
    expected_table_meta = table_meta or {}

    # We mainly verify "visual" part because "schema_used" might be added by parser
    if "visual" in expected_table_meta:
        assert parsed_table_meta.get("visual") == expected_table_meta["visual"]
    else:
        assert "visual" not in parsed_table_meta
