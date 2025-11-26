# Markdown Spreadsheet Parser

A lightweight, pure Python library for parsing Markdown tables into structured data.
It provides zero-dependency parsing with support for multiple tables, configurable schemas, and JSON-friendly output.

## Features

- **Pure Python & Zero Dependencies**: Lightweight and portable. Runs anywhere Python runs, including WebAssembly (Pyodide).
- **Type-Safe Validation**: Convert loose Markdown tables into strongly-typed Python `dataclasses` with automatic type conversion and validation.
- **Round-Trip Support**: Parse Markdown to objects, modify data, and generate Markdown back. Ideal for building editors or automation tools.
- **Robust Parsing**: Gracefully handles malformed tables (missing/extra columns) and escaped characters.
- **Multi-Table Workbooks**: Support for parsing multiple sheets and tables from a single file, including metadata (names, descriptions).
- **JSON-Friendly**: Easy export to dictionaries/JSON for integration with other tools (e.g., Pandas, APIs).

## Installation

```bash
pip install md-spreadsheet-parser
```

## Usage

### Command Line Interface (CLI)

You can use the `md-spreadsheet-parser` command to parse Markdown files and output JSON. This is useful for piping data to other tools.

```bash
# Read from file
md-spreadsheet-parser input.md

# Read from stdin (pipe)
cat input.md | md-spreadsheet-parser
```

**Options:**
- `--scan`: Scan for all tables ignoring workbook structure (returns a list of tables).
- `--root-marker`: Set the root marker (default: `# Tables`).
- `--sheet-header-level`: Set sheet header level (default: 2).
- `--table-header-level`: Set table header level (default: None).
- `--capture-description`: Capture table descriptions (requires `--table-header-level`).

### Python API

#### 1. Basic Parsing

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
```

### 2. Type-Safe Validation (Recommended)

The most powerful feature of this library is converting loose markdown tables into strongly-typed Python objects using `dataclasses`. This ensures your data is valid and easy to work with.

```python
from dataclasses import dataclass
from md_spreadsheet_parser import parse_table, TableValidationError

@dataclass
class User:
    name: str
    age: int
    is_active: bool = True

markdown = """
| Name | Age | Is Active |
|---|---|---|
| Alice | 30 | yes |
| Bob | 25 | no |
"""

try:
    # Parse and validate in one step
    users = parse_table(markdown).to_models(User)
    
    for user in users:
        print(f"{user.name} is {user.age} years old.")
        # Alice is 30 years old.
        # Bob is 25 years old.

except TableValidationError as e:
    print(e)
```

**Features:**
*   **Type Conversion**: Automatically converts strings to `int`, `float`, `bool`.
*   **Boolean Handling**: Understands "yes/no", "on/off", "1/0", "true/false".
*   **Optional Fields**: Handles `Optional[T]` by converting empty strings to `None`.
*   **Validation**: Raises detailed errors if data doesn't match the schema.

### 3. Markdown Generation (Round-Trip)

You can modify parsed objects and convert them back to Markdown strings using `to_markdown()`. This enables a complete "Parse -> Modify -> Generate" workflow.

```python
from md_spreadsheet_parser import parse_table, ParsingSchema

markdown = "| A | B |\n|---|---| \n| 1 | 2 |"
table = parse_table(markdown)

# Modify data
table.rows.append(["3", "4"])

# Generate Markdown
# You can customize the output format using a schema
schema = ParsingSchema(require_outer_pipes=True)
print(table.to_markdown(schema))
# | A | B |
# | --- | --- |
# | 1 | 2 |
# | 3 | 4 |
```

This works for `Table`, `Sheet`, and `Workbook` objects.

### 4. Advanced Parsing (Workbooks & Metadata)

Handle complex markdown files with multiple tables and sections.

#### Parsing a Workbook (Multiple Sheets)

```python
from md_spreadsheet_parser import parse_workbook, MultiTableParsingSchema

markdown = """
# Tables

## Users
| Name | Age |
|---|---|
| Alice | 30 |

## Products
| Item | Price |
|---|---|
| Apple | 100 |
"""

schema = MultiTableParsingSchema()
workbook = parse_workbook(markdown, schema)

users_sheet = workbook.get_sheet("Users")
products_sheet = workbook.get_sheet("Products")
```


### 5. Robustness (Handling Malformed Tables)

The parser is designed to handle imperfect markdown tables gracefully.

*   **Missing Columns**: Rows with fewer columns than the header are automatically **padded** with empty strings.
*   **Extra Columns**: Rows with more columns than the header are automatically **truncated**.

```python
markdown = """
| A | B |
|---|---|
| 1 |       <-- Missing column (padded to ["1", ""])
| 1 | 2 | 3 <-- Extra column (truncated to ["1", "2"])
"""
table = parse_table(markdown)
```

This ensures that `table.rows` always matches the structure of `table.headers`, preventing crashes during iteration or validation.

### 6. Configuration (Schemas)

Customize parsing behavior using `ParsingSchema` and `MultiTableParsingSchema`.

| Option | Default | Description |
|---|---|---|
| `column_separator` | `\|` | Character used to separate columns. |
| `header_separator_char` | `-` | Character used in the separator row. |
| `require_outer_pipes` | `True` | If `True`, generated markdown tables will include outer pipes (e.g. `\| col \|`). Does not affect parsing. |
| `strip_whitespace` | `True` | If `True`, whitespace is stripped from cell values. |
| `root_marker` | `# Tables` | (MultiTable) Marker indicating start of data section. |
| `sheet_header_level` | `2` | (MultiTable) Header level for sheets (e.g. `## Sheet`). |
| `table_header_level` | `None` | (MultiTable) Header level for tables. |
| `capture_description` | `False` | (MultiTable) Capture text between header and table. |

```python
schema = MultiTableParsingSchema(
    root_marker="# My Data",
    sheet_header_level=1,
    strip_whitespace=False
)
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

## Future Roadmap

We plan to extend the library to support **Visual Metadata** for better integration with rich Markdown editors.

### Visual Metadata Integration
Future versions will support parsing and generating metadata that controls the visual presentation of tables in an editor UI, such as:
- **Column Widths**: Persisting user-adjusted column widths.
- **Conditional Formatting**: Highlighting cells based on values.
- **Data Types**: Explicitly defining column types (e.g., currency, date) for better editor UX.

This metadata will be embedded in the Markdown file in a way that remains invisible or unobtrusive in standard Markdown viewers (e.g., using HTML comments or specific metadata blocks), ensuring compatibility while enabling rich editing experiences.

## License

MIT
