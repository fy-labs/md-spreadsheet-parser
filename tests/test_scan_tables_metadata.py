from md_spreadsheet_parser import scan_tables, MultiTableParsingSchema


def test_scan_tables_with_metadata():
    markdown = """
### Table 1
Description for Table 1.

| A | B |
| - | - |
| 1 | 2 |

### Table 2
Description for Table 2.

| C | D |
| - | - |
| 3 | 4 |
"""
    # Use MultiTableParsingSchema to configure table_header_level and capture_description
    schema = MultiTableParsingSchema(table_header_level=3, capture_description=True)

    tables = scan_tables(markdown, schema)

    assert len(tables) == 2

    t1 = tables[0]
    assert t1.name == "Table 1"
    assert t1.description == "Description for Table 1."
    assert t1.headers == ["A", "B"]
    assert t1.rows == [["1", "2"]]

    t2 = tables[1]
    assert t2.name == "Table 2"
    assert t2.description == "Description for Table 2."
    assert t2.headers == ["C", "D"]
    assert t2.rows == [["3", "4"]]


def test_scan_tables_mixed_content():
    """
    Test scan_tables with content that doesn't strictly follow the schema (e.g. text outside tables).
    """
    markdown = """
Introduction text.

### Table A

| Col |
| --- |
| Val |

Some text between tables.

### Table B

| Col 2 |
| ----- |
| Val 2 |

Footer text.
"""
    schema = MultiTableParsingSchema(table_header_level=3, capture_description=False)

    tables = scan_tables(markdown, schema)

    assert len(tables) == 2
    assert tables[0].name == "Table A"
    assert tables[1].name == "Table B"
