import tempfile
from md_spreadsheet_parser import scan_tables_iter, MultiTableParsingSchema


def test_streaming_from_iterable():
    # Simulate a stream of lines
    lines = [
        "# Tables\n",
        "\n",
        "## Table 1\n",
        "| A | B |\n",
        "|---|---|\n",
        "| 1 | 2 |\n",
        "\n",
        "## Table 2\n",
        "| X | Y |\n",
        "|---|---|\n",
        "| 9 | 8 |\n",
    ]

    # Use schema with headers
    schema = MultiTableParsingSchema(table_header_level=2)
    iterator = scan_tables_iter(lines, schema)

    tables = list(iterator)
    assert len(tables) == 2

    assert tables[0].name == "Table 1"
    assert tables[0].rows == [["1", "2"]]

    assert tables[1].name == "Table 2"
    assert tables[1].rows == [["9", "8"]]


def test_streaming_from_file():
    content = """
# Log Data

| Time | Event |
| ---- | ----- |
| 10:00| Start |

| Time | Event |
| ---- | ----- |
| 10:05| Stop  |
"""
    with tempfile.NamedTemporaryFile("w+", encoding="utf-8", suffix=".md") as tmp:
        tmp.write(content)
        tmp.flush()

        # Scan without headers (just finding tables)
        tables = list(scan_tables_iter(tmp.name))
        assert len(tables) == 2
        assert tables[0].rows[0] == ["10:00", "Start"]
        assert tables[1].rows[0] == ["10:05", "Stop"]


def test_streaming_header_switching():
    # Verify that encountering a new header yields the previous table
    lines = [
        "### Table A\n",
        "| A |\n",
        "|---|\n",
        "| 1 |\n",
        "### Table B\n",  # This should force yield of Table A
        "| B |\n",
        "|---|\n",
        "| 2 |\n",
    ]
    schema = MultiTableParsingSchema(table_header_level=3)
    tables = list(scan_tables_iter(lines, schema))

    assert len(tables) == 2
    assert tables[0].name == "Table A"
    assert tables[1].name == "Table B"
