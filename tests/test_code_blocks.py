from md_spreadsheet_parser import MultiTableParsingSchema, parse_workbook


def test_parse_workbook_ignores_code_blocks():
    md = """# Document Title

Comparison of something.

```markdown
# Tables
Here is an example of structure.
```

# Tables

## Sheet 1

| A | B |
|---|---|
| 1 | 2 |
"""
    schema = MultiTableParsingSchema(root_marker="# Tables", sheet_header_level=2)
    workbook = parse_workbook(md, schema)

    # If it picked up the first "# Tables" inside the code block, it would likely fail to find "## Sheet 1"
    # because "## Sheet 1" is much later, or it might treat the text inside code block as sheets?
    # Actually, if it starts at the code block, it will see "Here is an example of structure."
    # Then it sees lines. It won't find any sheets until it hits "## Sheet 1" later.
    # However, proper behavior is that the root marker is the SECOND "# Tables".

    # Let's see what happens.
    # If it starts at line 5 (inside code block), it parses.
    # It scans for sheets.
    # It sees "# Tables" (the real one) at line 9. "# Tables" is level 1.
    # schema.sheet_header_level is 2.
    # The scanner stops parsing workbook if it encounters a header with level < sheet_header_level.
    # So if it starts inside the code block, it will hit the real "# Tables" (Level 1) and STOP parsing.
    # Result: 0 sheets.

    assert len(workbook.sheets) == 1
    assert workbook.sheets[0].name == "Sheet 1"


def test_parse_sheet_ignores_code_blocks():
    md = """# Tables

## Sheet 1

Some description.

```python
# Not a sheet header
## Not a sheet header
```

| A | B |
|---|---|
| 1 | 2 |

## Sheet 2

| C | D |
|---|---|
| 3 | 4 |
"""
    schema = MultiTableParsingSchema(root_marker="# Tables", sheet_header_level=2)
    workbook = parse_workbook(md, schema)

    assert len(workbook.sheets) == 2
    assert workbook.sheets[0].name == "Sheet 1"
    assert workbook.sheets[1].name == "Sheet 2"
