from md_spreadsheet_parser import MultiTableParsingSchema, parse_workbook


def test_single_h1_auto_detected_as_workbook():
    """
    With new auto-detection, a single H1 header becomes the workbook root.
    H2 headers become sheets.
    """
    markdown = """# Introduction

This file has a single H1 header which becomes the workbook.

## Section 1

Some text content here.

- List item 1
- List item 2

## Conclusion

Final thoughts.
"""

    workbook = parse_workbook(markdown)

    # Single H1 is auto-detected as workbook
    assert workbook.name == "Introduction"
    # H2 headers become sheets
    assert len(workbook.sheets) == 2
    assert workbook.sheets[0].name == "Section 1"
    assert workbook.sheets[1].name == "Conclusion"
    # These are doc sheets (no tables)
    assert workbook.sheets[0].type == "doc"
    assert workbook.sheets[1].type == "doc"


def test_explicit_root_marker_requires_exact_match():
    """
    When using explicit root_marker, parser requires exact match.
    """
    markdown = """# Introduction

This file does not contain a `# Tables` section.

## Section 1

Some text content here.
"""

    schema = MultiTableParsingSchema(
        root_marker="# Tables",
        sheet_header_level=2,
    )
    workbook = parse_workbook(markdown, schema)

    # With explicit root_marker, must find exact match
    assert len(workbook.sheets) == 0


def test_multiple_h1_fallback_to_tables_or_workbook():
    """
    When multiple H1 headers exist and no explicit root_marker,
    look for '# Tables' or '# Workbook' as fallback.
    """
    markdown = """# Introduction

Some intro text.

# Another Section

More text.
"""

    workbook = parse_workbook(markdown)

    # Multiple H1 but no "# Tables" or "# Workbook" - empty workbook
    assert len(workbook.sheets) == 0


def test_multiple_h1_with_workbook_marker():
    """
    When multiple H1 headers exist, '# Workbook' can act as root marker.
    """
    markdown = """# Introduction

Some intro text.

# Workbook

## Sheet1

| A | B |
| - | - |
| 1 | 2 |
"""

    workbook = parse_workbook(markdown)

    assert workbook.name == "Workbook"
    assert len(workbook.sheets) == 1
    assert workbook.sheets[0].name == "Sheet1"
    assert workbook.sheets[0].type == "table"
