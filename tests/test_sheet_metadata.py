from md_spreadsheet_parser.generator import generate_workbook_markdown
from md_spreadsheet_parser.models import Sheet, Table
from md_spreadsheet_parser.parsing import parse_sheet, parse_workbook
from md_spreadsheet_parser.schemas import MultiTableParsingSchema


def test_sheet_metadata_parsing():
    markdown = """# Tables

## Sheet 1
<!-- md-spreadsheet-sheet-metadata: {"layout": {"type": "split", "direction": "vertical"}} -->

| A | B |
|---|---|
| 1 | 2 |
"""
    workbook = parse_workbook(markdown)
    assert len(workbook.sheets) == 1
    sheet = workbook.sheets[0]
    assert sheet.name == "Sheet 1"
    assert sheet.metadata == {"layout": {"type": "split", "direction": "vertical"}}
    assert len(sheet.tables) == 1


def test_sheet_metadata_generation():
    table = Table(headers=["A", "B"], rows=[["1", "2"]])
    sheet = Sheet(
        name="Sheet 1", tables=[table], metadata={"layout": {"type": "split"}}
    )

    schema = MultiTableParsingSchema()
    from md_spreadsheet_parser.models import Workbook

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
<!-- md-spreadsheet-sheet-metadata: {"layout": "test"} -->

| A |
|---|
| 1 |
"""
    workbook = parse_workbook(original_md)
    assert workbook.sheets[0].metadata == {"layout": "test"}

    generated = workbook.to_markdown(MultiTableParsingSchema())
    # Note: Whitespace might vary slightly (empty lines), but data should be there.
    assert '<!-- md-spreadsheet-sheet-metadata: {"layout": "test"} -->' in generated

    workbook2 = parse_workbook(generated)
    assert workbook2.sheets[0].metadata == {"layout": "test"}
