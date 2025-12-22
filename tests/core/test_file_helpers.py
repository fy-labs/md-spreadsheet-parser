import tempfile
from pathlib import Path
from md_spreadsheet_parser import (
    parse_table_from_file,
    parse_workbook_from_file,
    scan_tables_from_file,
)

MARKDOWN_CONTENT = """
# Tables

## Sheet 1

| Name | Age |
| --- | --- |
| Alice | 30 |

## Sheet 2

| ID | Item |
| -- | ---- |
| 1  | Apple |
"""


def test_parse_from_file_path():
    with tempfile.NamedTemporaryFile("w+", encoding="utf-8", suffix=".md") as tmp:
        tmp.write(MARKDOWN_CONTENT)
        tmp.flush()

        # Test Path
        workbook = parse_workbook_from_file(Path(tmp.name))
        assert len(workbook.sheets) == 2
        assert workbook.sheets[0].name == "Sheet 1"

        # Test Str
        workbook_str = parse_workbook_from_file(tmp.name)
        assert len(workbook_str.sheets) == 2


def test_parse_from_file_object():
    with tempfile.TemporaryFile("w+", encoding="utf-8") as tmp:
        tmp.write(MARKDOWN_CONTENT)
        tmp.seek(0)

        # Test TextIO
        workbook = parse_workbook_from_file(tmp)
        assert len(workbook.sheets) == 2


def test_scan_from_file():
    with tempfile.NamedTemporaryFile("w+", encoding="utf-8", suffix=".md") as tmp:
        tmp.write(MARKDOWN_CONTENT)
        tmp.flush()

        tables = scan_tables_from_file(tmp.name)
        assert len(tables) == 2
        assert len(tables[0].rows) == 1
        assert tables[0].rows[0] == ["Alice", "30"]


def test_single_table_from_file():
    single_table = "| A | B |\n|---|---|\n| 1 | 2 |"
    with tempfile.NamedTemporaryFile("w+", encoding="utf-8", suffix=".md") as tmp:
        tmp.write(single_table)
        tmp.flush()

        table = parse_table_from_file(tmp.name)
        assert table.headers == ["A", "B"]
        assert table.rows == [["1", "2"]]
