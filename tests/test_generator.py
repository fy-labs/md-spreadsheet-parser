from md_spreadsheet_parser import (
    Table,
    Sheet,
    Workbook,
    ParsingSchema,
    MultiTableParsingSchema,
)


def test_table_to_markdown_basic():
    table = Table(
        headers=["Name", "Age", "City"],
        rows=[
            ["Alice", "30", "New York"],
            ["Bob", "25", "Los Angeles"],
            ["Charlie", "35", "Chicago"],
        ],
    )
    schema = ParsingSchema(require_outer_pipes=True)
    markdown = table.to_markdown(schema)

    expected = """| Name | Age | City |
| --- | --- | --- |
| Alice | 30 | New York |
| Bob | 25 | Los Angeles |
| Charlie | 35 | Chicago |"""

    assert markdown.strip() == expected.strip()


def test_table_to_markdown_no_headers():
    table = Table(
        headers=None,
        rows=[["A", "1", "X"], ["B", "2", "Y"], ["C", "3", "Z"]],
    )
    schema = ParsingSchema(require_outer_pipes=True)
    markdown = table.to_markdown(schema)

    expected = """| A | 1 | X |
| B | 2 | Y |
| C | 3 | Z |"""

    assert markdown.strip() == expected.strip()


def test_table_to_markdown_with_metadata():
    table = Table(
        headers=["Col1", "Col2"],
        rows=[["Val1", "Val2"]],
        name="MyTable",
        description="This is a description.",
    )
    schema = MultiTableParsingSchema(
        table_header_level=3, capture_description=True, require_outer_pipes=True
    )
    markdown = table.to_markdown(schema)

    expected = """### MyTable
This is a description.

| Col1 | Col2 |
| --- | --- |
| Val1 | Val2 |"""

    assert markdown.strip() == expected.strip()


def test_sheet_to_markdown():
    table1 = Table(headers=["A", "B"], rows=[["1", "2"]])
    table2 = Table(headers=["C", "D"], rows=[["3", "4"]])
    sheet = Sheet(name="Sheet1", tables=[table1, table2])

    schema = MultiTableParsingSchema(sheet_header_level=2, require_outer_pipes=True)
    markdown = sheet.to_markdown(schema)

    expected = """## Sheet1

| A | B |
| --- | --- |
| 1 | 2 |

| C | D |
| --- | --- |
| 3 | 4 |"""

    assert markdown.strip() == expected.strip()


def test_workbook_to_markdown():
    table1 = Table(headers=["A"], rows=[["1"]])
    sheet1 = Sheet(name="Sheet1", tables=[table1])

    table2 = Table(headers=["B"], rows=[["2"]])
    sheet2 = Sheet(name="Sheet2", tables=[table2])

    workbook = Workbook(sheets=[sheet1, sheet2])

    schema = MultiTableParsingSchema(root_marker="# Tables", require_outer_pipes=True)
    markdown = workbook.to_markdown(schema)

    expected = """# Tables

## Sheet1

| A |
| --- |
| 1 |


## Sheet2

| B |
| --- |
| 2 |"""

    assert markdown.strip() == expected.strip()
