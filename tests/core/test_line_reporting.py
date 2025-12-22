from md_spreadsheet_parser.parsing import parse_workbook
from md_spreadsheet_parser.schemas import MultiTableParsingSchema
import textwrap


def test_line_reporting_with_spacing():
    """
    Verify that start_line and end_line are correctly reported,
    excluding surrounding empty lines.
    """
    md_text = textwrap.dedent("""
        # Tables

        ## Sheet 1

        ### Table 1

        | A | B |
        | - | - |
        | 1 | 2 |

        ## Sheet 2
    """).strip()

    schema = MultiTableParsingSchema()
    workbook = parse_workbook(md_text, schema)

    table = workbook.sheets[0].tables[0]

    # Lines breakdown:
    # 0: # Tables
    # 1:
    # 2: ## Sheet 1
    # 3:
    # 4: ### Table 1
    # 5:
    # 6: | A | B |  <- Start
    # 7: | - | - |
    # 8: | 1 | 2 |
    # 9:          <- End (exclusive) points here (empty line)
    # 10: ## Sheet 2

    assert table.start_line == 6
    assert table.end_line == 9

    # Verify content match
    lines = md_text.split("\n")
    table_lines = lines[table.start_line : table.end_line]
    assert len(table_lines) == 3
    assert table_lines[0] == "| A | B |"
    assert table_lines[2] == "| 1 | 2 |"


def test_line_reporting_no_spacing():
    """
    Verify line reporting when there is no empty line after table.
    """
    md_text = textwrap.dedent("""
        | A | B |
        | - | - |
        | 1 | 2 |
        ## Sheet 2
    """).strip()

    # Lines:
    # 0: | A | B |
    # 1: | - | - |
    # 2: | 1 | 2 |
    # 3: ## Sheet 2

    schema = MultiTableParsingSchema(table_header_level=None, capture_description=False)
    workbook = parse_workbook(md_text, schema)

    # No sheet headers used here effectively, but parse_workbook might wrap in default if not found?
    # Actually parse_workbook with root_marker defaults might fail to find anything if root marker missing?
    # Let's use flexible schema or just scan_tables for this unit test if parse_workbook is strict.
    # parse_workbook defaults: root_marker="# Tables".
    # So we should use scan_tables or adjust schema.

    # Let's adjust input to have root marker for parse_workbook
    md_text_valid = textwrap.dedent("""
        # Tables
        
        ## Sheet 1
        
        | A | B |
        | - | - |
        | 1 | 2 |
        ## Sheet 2
    """).strip()

    # 0: # Tables
    # 1:
    # 2: ## Sheet 1
    # 3:
    # 4: | A | B |
    # 5: | - | - |
    # 6: | 1 | 2 |
    # 7: ## Sheet 2

    workbook = parse_workbook(md_text_valid, schema)
    table = workbook.sheets[0].tables[0]

    assert table.start_line == 4
    assert table.end_line == 7
