# Markdown Spreadsheet Parser

A lightweight, pure Python library for parsing Markdown tables into structured data.
It provides zero-dependency parsing with support for multiple tables, configurable schemas, and JSON-friendly output.

## Features

- **Pure Python**: Zero dependencies, runs anywhere Python runs.
- **Structured Output**: Converts Markdown tables into JSON-friendly objects with headers and rows.
- **Multi-Table Support**: Can parse multiple tables (sheets) from a single file using a specific structure.
- **Configurable**: Supports different table styles via schemas.

## Installation

```bash
pip install md-spreadsheet-parser
```

## Usage

### 1. Basic Parsing

#### Single Table
Parse a standard Markdown table into a structured object.

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

#### Multiple Tables (Workbook)
Parse a file containing multiple sheets (sections). By default, it looks for `# Tables` as the root marker and `## Sheet Name` for sheets.

```python
from md_spreadsheet_parser import parse_workbook, MultiTableParsingSchema

markdown = """
# Tables

## Users
| ID | Name |
| -- | ---- |
| 1  | Alice|

## Products
| ID | Item |
| -- | ---- |
| A  | Apple|
"""

# Use default schema
schema = MultiTableParsingSchema()
workbook = parse_workbook(markdown, schema)

for sheet in workbook.sheets:
    print(f"Sheet: {sheet.name}")
    for table in sheet.tables:
        print(table.rows)
```

### 2. Advanced Features

#### Metadata Extraction (Table Names & Descriptions)
You can configure the parser to extract table names (from headers) and descriptions (text preceding the table).

```python
from md_spreadsheet_parser import parse_workbook, MultiTableParsingSchema

markdown = """
# Tables

## Sales Data

### Q1 Results
Financial performance for the first quarter.

| Month | Revenue |
| ----- | ------- |
| Jan   | 1000    |
"""

# Configure schema to capture table headers (level 3) and descriptions
schema = MultiTableParsingSchema(
    table_header_level=3,     # Treat ### Header as table name
    capture_description=True  # Capture text between header and table
)

workbook = parse_workbook(markdown, schema)
table = workbook.sheets[0].tables[0]

print(f"Table: {table.name}")        # "Q1 Results"
print(f"Desc: {table.description}")  # "Financial performance for the first quarter."
```

#### Lookup API
Retrieve sheets and tables directly by name instead of iterating.

```python
sheet = workbook.get_sheet("Sales Data")
if sheet:
    table = sheet.get_table("Q1 Results")
    if table:
        print(table.rows)
```

#### Simple Scan Interface
If you want to extract *all* tables from a document regardless of its structure (ignoring sheets and headers), use `scan_tables`.

**Example 1: Basic Scanning**
Extract all tables from a text, ignoring headers and other content.

```python
from md_spreadsheet_parser import scan_tables

markdown = """
Some introductory text...

| A | B |
| - | - |
| 1 | 2 |

More text...

| C |
| - |
| 3 |
"""

# Returns a flat list of all tables found
tables = scan_tables(markdown)

print(len(tables)) # 2
print(tables[0].headers) # ['A', 'B']
```

**Example 2: Metadata Extraction (Flat File)**
You can use `MultiTableParsingSchema` with `scan_tables` to extract table names and descriptions even without a root marker or sheets. This is useful for flat Markdown files.

```python
from md_spreadsheet_parser import scan_tables, MultiTableParsingSchema

markdown = """
### Users
List of users.

| Name | Age |
| ---- | --- |
| Alice| 30  |

### Products
List of products.

| Item | Price |
| ---- | ----- |
| Apple| 1.00  |
"""

# Configure schema to capture table headers and descriptions
schema = MultiTableParsingSchema(
    table_header_level=3,
    capture_description=True
)

tables = scan_tables(markdown, schema)

for table in tables:
    print(f"Table: {table.name}")        # "Users", "Products"
    print(f"Desc: {table.description}")  # "List of users.", "List of products."
    print(table.rows)
```

**Example 3: Mixed Content Handling**
`scan_tables` is robust against mixed content. It will identify tables based on the schema (column separator) and ignore other text blocks unless configured to capture them as descriptions.

```python
markdown = """
# Title
Introduction paragraph.

| Col 1 |
| ----- |
| Val 1 |

> Blockquote that is not a table.

| Col 2 |
| ----- |
| Val 2 |
"""

tables = scan_tables(markdown)
# tables[0] -> Table with header ['Col 1']
# tables[1] -> Table with header ['Col 2']
```

#### JSON / Dict Export
All result objects (`Workbook`, `Sheet`, `Table`) have a `.json` property that returns a dictionary, making it easy to serialize or pass to other libraries (like Pandas).

```python
import json
import pandas as pd

# Export to JSON
print(json.dumps(workbook.json, indent=2))

# Convert to Pandas DataFrame
table_data = workbook.sheets[0].tables[0].json
df = pd.DataFrame(table_data["rows"], columns=table_data["headers"])
```

#### Schema Validation (Pydantic-like)
You can validate and convert table data into Python objects using standard `dataclasses`. This ensures type safety without external dependencies.

```python
from dataclasses import dataclass
from md_spreadsheet_parser import parse_as

@dataclass
class User:
    id: int
    name: str
    is_active: bool
    email: str | None = None

markdown = """
| ID | Name  | Is Active | Email          |
| -- | ----- | --------- | -------------- |
| 1  | Alice | true      | alice@test.com |
| 2  | Bob   | false     |                |
"""

# Returns a list of User objects
users = parse_as(User, markdown)

print(users[0].id)        # 1 (int)
print(users[0].is_active) # True (bool)
print(users[1].email)     # None
```

If validation fails, a `TableValidationError` is raised with detailed error messages.

### 3. Configuration (Schemas)

You can customize parsing behavior using `ParsingSchema` and `MultiTableParsingSchema`.

| Option | Default | Description |
| :--- | :--- | :--- |
| `column_separator` | `\|` | Character used to separate columns. |
| `header_separator_char` | `-` | Character used in the separator row (e.g. `---`). |
| `strip_whitespace` | `True` | Whether to strip whitespace from cell values. |
| `root_marker` | `# Tables` | (Multi-table only) Marker indicating start of data. |
| `sheet_header_level` | `2` | (Multi-table only) Header level for sheets (e.g. `##`). |
| `table_header_level` | `None` | (Multi-table only) Header level for tables. `None` disables name extraction. |
| `capture_description` | `False` | (Multi-table only) Whether to capture text descriptions. |

```python
schema = MultiTableParsingSchema(
    root_marker="# My Data",
    sheet_header_level=1,
    strip_whitespace=False
)
```




## License

MIT
