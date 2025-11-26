from md_spreadsheet_parser import parse_table


def test_short_row():
    """
    Row has fewer columns than headers.
    Should be padded with empty strings.
    """
    markdown = """
| A | B | C |
|---|---|---|
| 1 | 2 |
"""
    table = parse_table(markdown)
    assert table.headers == ["A", "B", "C"]
    # Expect padding
    assert len(table.rows[0]) == 3
    assert table.rows[0] == ["1", "2", ""]


def test_long_row():
    """
    Row has more columns than headers.
    Should be truncated.
    """
    markdown = """
| A | B |
|---|---|
| 1 | 2 | 3 |
"""
    table = parse_table(markdown)
    assert table.headers == ["A", "B"]
    # Expect truncation
    assert len(table.rows[0]) == 2
    assert table.rows[0] == ["1", "2"]
