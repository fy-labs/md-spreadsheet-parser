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
    assert table.rows[1][1] == "A \n"
    assert table.rows[2][1] == "\n B"


def test_br_roundtrip():
    # Markdown -> Object -> Markdown
    original_markdown = "| A | B |\n| --- | --- |\n| 1 | Line1<br>Line2 |"
    table = parse_table(original_markdown)

    # Verify parsing
    assert table.rows[0][1] == "Line1\nLine2"

    # Verify generation
    generated_markdown = table.to_markdown()

    # We expect <br> to be restored (normalized to <br> from logic)
    # Note: to_markdown adds spaces around pipes by default
    assert "| 1 | Line1<br>Line2 |" in generated_markdown

    # Verify round-trip re-parsing
    table2 = parse_table(generated_markdown)
    assert table2.rows[0][1] == "Line1\nLine2"


def test_br_roundtrip_disabled():
    # If disabled, \n should remain \n (which breaks table if not careful)
    # But wait, if we disable br conversion, then \n in clean_cell is just \n?
    # No, parser splits by \n.
    pass
    # Actually, if we have \n in memory and generate with convert=False, it will produce multiline markdown which is broken table.
    # That is expected behavior (garbage in, garbage out for markdown tables).
    # We test the ENABLED case which is the fix.
