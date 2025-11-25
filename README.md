# Markdown Spreadsheet Parser

A lightweight, pure Python library for parsing Markdown tables into structured data.
Designed to be portable and run in WebAssembly environments (like Pyodide in VS Code extensions).

## Features

- **Pure Python**: Zero dependencies, runs anywhere Python runs (including WASM).
- **Structured Output**: Converts Markdown tables into JSON-friendly objects with headers and rows.
- **Multi-Table Support**: Can parse multiple tables (sheets) from a single file using a specific structure.
- **Configurable**: Supports different table styles via schemas.

## Installation

```bash
pip install md-spreadsheet-parser
```

## Usage

### Single Table

Use `parse_table` to parse a standard Markdown table.

```python
from md_spreadsheet_parser import parse_table

markdown = """
| Name | Age |
| --- | --- |
| Alice | 30 |
| Bob | 25 |
"""

result = parse_table(markdown)

print(result.headers)
# ['Name', 'Age']

print(result.rows)
# [['Alice', '30'], ['Bob', '25']]
```

### Multiple Tables (Workbook)

Use `parse_workbook` to parse a file containing multiple sheets.
**Note**: The file must start with the root marker `# Tables` (configurable).

You can also extract table names and descriptions by configuring the schema.

```python
from md_spreadsheet_parser import parse_workbook, MultiTableParsingSchema

markdown = """
# Tables

## Sheet 1

### Users Table
List of active users.

| ID | User |
| -- | ---- |
| 99 | Bob  |
"""

# Configure schema to capture table headers (level 3) and descriptions
schema = MultiTableParsingSchema(
    table_header_level=3,
    capture_description=True
)
workbook = parse_workbook(markdown, schema)

# Access structured data
for sheet in workbook.sheets:
    print(f"Sheet: {sheet.name}")
    for table in sheet.tables:
        print(f"  Table: {table.name}")
        print(f"  Description: {table.description}")
        print(f"  Headers: {table.headers}")

# Export to JSON-compatible dict
import json
print(json.dumps(workbook.json, indent=2))
```


## License

MIT
