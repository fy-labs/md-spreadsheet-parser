from md_spreadsheet_parser import parse_workbook


def test_missing_root_marker_with_similar_headers():
    """
    Verify that the parser does not incorrectly detect other H1 headers as the root marker.
    The input text has headers like '# Introduction' but lacks '# Tables'.
    Expected behavior: Return an empty workbook.
    """
    markdown = """# Introduction

This file does not contain a `# Tables` section. 
It represents a standard Markdown document that might be opened in the editor.

## Section 1

Some text content here.

- List item 1
- List item 2

## Conclusion

Final thoughts.
"""

    workbook = parse_workbook(markdown)

    # Needs to match behavior in parsing.py:
    # if not found: return Workbook(sheets=[], metadata=metadata)
    assert len(workbook.sheets) == 0, (
        f"Expected 0 sheets, found {len(workbook.sheets)}: {[s.name for s in workbook.sheets]}"
    )
