from md_spreadsheet_parser.parsing import parse_table


def test_pipes_inside_inline_code():
    """
    Test that pipes inside inline code blocks (backticks) are NOT treated as separators.
    GFM Spec: `|` is a literal pipe.
    """
    markdown = """
| Col 1 | Col 2 |
| --- | --- |
| `|` | Normal |
| `a|b` | Text |
"""
    table = parse_table(markdown)

    # Needs to be 2 columns
    assert len(table.headers) == 2

    # Row 0: `|`, Normal
    # Current broken parser splits `|` -> ["`", "`", "Normal"] (3 cols) or similar
    assert len(table.rows[0]) == 2
    assert table.rows[0][0] == "`|`"
    assert table.rows[0][1] == "Normal"

    # Row 1: `a|b`, Text
    assert len(table.rows[1]) == 2
    assert table.rows[1][0] == "`a|b`"
    assert table.rows[1][1] == "Text"


def test_pipes_inside_inline_code_mixed():
    """
    Test mixed content with code blocks and pipes.
    """
    markdown = """
| A | B |
| - | - |
| `code` | `|` |
| `|` | `|` |
"""
    table = parse_table(markdown)
    assert len(table.rows) == 2
    assert table.rows[0] == ["`code`", "`|`"]
    assert table.rows[1] == ["`|`", "`|`"]


def test_escaped_pipes_vs_code_pipes():
    """
    Test that escaped pipes `\|` and code pipes `` `|` `` coexist.
    """
    markdown = """
| A | B |
| - | - |
| \| | `|` |
"""
    table = parse_table(markdown)
    assert table.rows[0][0] == "|"  # Escaped pipe becomes logical pipe (cleaned)
    assert table.rows[0][1] == "`|`"  # Code pipe remains code
