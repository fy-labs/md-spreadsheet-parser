from md_spreadsheet_parser.models import Sheet, Table, Workbook
from md_spreadsheet_parser.parsing import parse_workbook


def test_parse_workbook_with_root_content():
    """
    Test that parse_workbook correctly captures content immediately following the workbook header.
    """
    markdown = """# My Workbook

This is root content.
 It has multiple lines.

## Sheet 1

| A | B |
|---|---|
| 1 | 2 |
"""
    workbook = parse_workbook(markdown)

    # Check basic properties
    assert workbook.name == "My Workbook"
    assert len(workbook.sheets) == 1
    assert workbook.sheets[0].name == "Sheet 1"

    # Check root content
    expected_content = "This is root content.\n It has multiple lines."
    assert workbook.root_content == expected_content


def test_round_trip_with_root_content():
    """
    Test that a workbook with root content can be round-tripped through generator and parser.
    """
    original_wb = Workbook(
        name="Test Workbook",
        root_content="Some introductory text.\n\nMore text.",
        sheets=[
            Sheet(name="Sheet1", tables=[Table(headers=["Col1"], rows=[["Val1"]])])
        ],
    )

    # Generate markdown
    markdown = original_wb.to_markdown()

    # Verify markdown contains root content
    assert "Some introductory text." in markdown

    # Parse back
    parsed_wb = parse_workbook(markdown)

    # Verify equality
    assert parsed_wb.name == original_wb.name
    assert parsed_wb.root_content == original_wb.root_content
    assert len(parsed_wb.sheets) == len(original_wb.sheets)


def test_empty_workbook_with_root_content():
    """
    Test an empty workbook (no sheets) that only has root content.
    This corresponds to the User's "Single Document" scenario.
    """
    markdown = """# Doc

This is a Root Document
"""
    workbook = parse_workbook(markdown)

    assert workbook.name == "Doc"
    assert len(workbook.sheets) == 0

    expected_content = "This is a Root Document"
    assert workbook.root_content == expected_content
