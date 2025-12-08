import pytest
from md_spreadsheet_parser import parse_table, ParsingSchema

def test_br_conversion_basic():
    markdown = """
| Col1 | Col2 |
| --- | --- |
| Line1<br>Line2 | Normal |
"""
    table = parse_table(markdown)
    assert table.rows[0][0] == "Line1\nLine2"
    assert table.rows[0][1] == "Normal"

def test_br_conversion_variations():
    markdown = """
| Type | Value |
| --- | --- |
| Simple | A<br>B |
| Slash | C<br/>D |
| Space | E<br />F |
| Caps | G<BR>H |
| Mixed | I<br>J<br />K |
"""
    table = parse_table(markdown)
    rows = table.rows
    assert rows[0][1] == "A\nB"
    assert rows[1][1] == "C\nD"
    assert rows[2][1] == "E\nF"
    assert rows[3][1] == "G\nH"
    assert rows[4][1] == "I\nJ\nK"

def test_br_conversion_disabled():
    markdown = """
| Col1 |
| --- |
| A<br>B |
"""
    schema = ParsingSchema(convert_br_to_newline=False)
    table = parse_table(markdown, schema)
    assert table.rows[0][0] == "A<br>B"

def test_br_at_edges():
    # Test interaction with strip_whitespace
    # ParsingSchema defaults: strip_whitespace=True, convert_br=True
    # strip() happens first, then replace.
    
    # CASE 1: <br> in middle surrounded by spaces
    # "| A <br> B |" -> strip -> "A <br> B" -> replace -> "A \n B"
    
    # CASE 2: <br> at end
    # "| A <br> |" -> strip -> "A <br>" -> replace -> "A \n"
    # Result has trailing newline.
    
    markdown = """
| Case | Value |
| --- | --- |
| Middle | A <br> B |
| End | A <br> |
| Start | <br> B |
"""
    table = parse_table(markdown)
    # Note: "A <br> B" becomes "A \n B" (spaces preserved around br because they are internal to the stripped string)
    assert table.rows[0][1] == "A \n B"
    assert table.rows[1][1] == "A \n"
    assert table.rows[2][1] == "\n B"
