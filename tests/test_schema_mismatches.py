from md_spreadsheet_parser import (
    parse_workbook,
    parse_table,
    MultiTableParsingSchema,
    ParsingSchema,
)


def test_root_marker_mismatch():
    """
    Test that parsing returns an empty workbook if the root marker is not found.
    """
    markdown = """
# Wrong Marker
## Sheet 1
| A |
|---|
| 1 |
"""
    schema = MultiTableParsingSchema(root_marker="# Correct Marker")
    workbook = parse_workbook(markdown, schema)

    assert len(workbook.sheets) == 0


def test_sheet_header_level_mismatch_too_high():
    """
    Schema expects level 3 (###), but text has level 2 (##).
    The parser should stop or ignore the level 2 headers as they are 'higher' level than expected (or just not match).
    In the current logic, if it encounters a level < expected, it breaks.
    """
    markdown = """
# Tables

## Sheet 1
| A |
|---|
| 1 |
"""
    # Expecting ###, but finding ##.
    # ## is level 2. Expected is 3. 2 < 3, so it should break (stop parsing).
    schema = MultiTableParsingSchema(root_marker="# Tables", sheet_header_level=3)
    workbook = parse_workbook(markdown, schema)

    assert len(workbook.sheets) == 0


def test_sheet_header_level_mismatch_too_low():
    """
    Schema expects level 2 (##), but text has level 3 (###).
    These should be treated as content, not sheets.
    """
    markdown = """
# Tables

### Not a Sheet
| A |
|---|
| 1 |
"""
    schema = MultiTableParsingSchema(root_marker="# Tables", sheet_header_level=2)
    workbook = parse_workbook(markdown, schema)

    # "### Not a Sheet" does not match "## " prefix.
    # So no sheets should be found.
    assert len(workbook.sheets) == 0


def test_table_header_level_mismatch():
    """
    Schema expects table header level 3 (###), but text has level 2 (##).
    Tables should be found but names/descriptions should NOT be extracted.
    """

    schema = MultiTableParsingSchema(
        table_header_level=3,  # Expecting ###
        capture_description=True,
    )
    # Using scan_tables logic via parse_sheet (if we were parsing a sheet)
    # But here let's use parse_workbook to test the full flow or just check extraction behavior.
    # Let's use parse_workbook with a dummy sheet.

    markdown_wb = """
# Tables
## Sheet 1

#### Table Name (Level 4)
| A |
|---|
| 1 |
"""
    schema = MultiTableParsingSchema(
        root_marker="# Tables",
        sheet_header_level=2,
        table_header_level=3,  # Expecting ###
        capture_description=True,
    )
    workbook = parse_workbook(markdown_wb, schema)

    assert len(workbook.sheets) == 1
    sheet = workbook.sheets[0]
    # Should have 1 table (unnamed) because #### doesn't match ### but relaxed parsing finds the table
    assert len(sheet.tables) == 1
    assert sheet.tables[0].name is None


def test_column_separator_mismatch():
    """
    Schema expects '|', but text uses ','.
    Should fail to parse as a table (or return empty/malformed table).
    """
    markdown = """
A,B
1,2
"""
    schema = ParsingSchema(column_separator="|")
    table = parse_table(markdown, schema)

    # parse_table splits by separator. If not found, row is just the whole line.
    # It might interpret "A,B" as a single cell row.
    # But since there are no separator rows (---|---), headers will be None.

    assert table.headers is None
    # It might parse as rows with 1 column
    assert len(table.rows) == 2
    assert table.rows[0] == ["A,B"]
