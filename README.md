# Markdown Spreadsheet Parser

<p align="center">
  <a href="https://github.com/f-y/md-spreadsheet-parser/blob/main/LICENSE">
    <img src="https://img.shields.io/badge/license-MIT-blue.svg" alt="License" />
  </a>
  <a href="https://pypi.org/project/md-spreadsheet-parser/">
    <img src="https://img.shields.io/pypi/v/md-spreadsheet-parser.svg" alt="PyPI" />
  </a>
  <a href="https://pepy.tech/projects/md-spreadsheet-parser"><img src="https://static.pepy.tech/personalized-badge/md-spreadsheet-parser?period=total&units=INTERNATIONAL_SYSTEM&left_color=GREY&right_color=BLUE&left_text=downloads" alt="PyPI Downloads"></a>
  <a href="https://www.npmjs.com/package/md-spreadsheet-parser">
    <img src="https://img.shields.io/npm/v/md-spreadsheet-parser.svg" alt="npm" />
  </a>
  <a href="https://github.com/f-y/md-spreadsheet-parser">
    <img src="https://img.shields.io/badge/repository-github-blue.svg" alt="Repository" />
  </a>
  <a href="https://github.com/f-y/md-spreadsheet-parser/actions?query=workflow%3ATests">
    <img src="https://github.com/f-y/md-spreadsheet-parser/workflows/Tests/badge.svg" alt="Build Status" />
  </a>
</p>

<p align="center">
  <strong>A robust, zero-dependency Python library for converting Excel to Markdown, parsing tables, and type-safe validation.</strong>
</p>

---

**md-spreadsheet-parser** elevates Markdown tables from simple text to first-class data structures. It offers a precise, zero-dependency engine to parse, validate, and manipulate tables with the ease of a spreadsheet and the power of Python.

> [!IMPORTANT]
> **🎉 Official GUI Editor Released: [PengSheets](https://marketplace.visualstudio.com/items?itemName=f-y.peng-sheets)**
>
> We have transformed this library into an Excel-like interface for VS Code. Edit Markdown tables with sort, filter, and easy navigation directly in your editor.
>
> [![Get it on VS Code Marketplace](https://img.shields.io/badge/Get%20it%20on-VS%20Code%20Marketplace-007ACC?style=for-the-badge&logo=visual-studio-code&logoColor=white)](https://marketplace.visualstudio.com/items?itemName=f-y.peng-sheets)

�🚀 **Need a quick solution?** Check out the [Cookbook](https://github.com/f-y/md-spreadsheet-parser/blob/main/COOKBOOK.md) for copy-pasteable recipes (Excel conversion, Pandas integration, Markdown table manipulation, and more).

Read in Japanese: 日本語版はこちら(
<a href="https://github.com/f-y/md-spreadsheet-parser/blob/main/README.ja.md">README</a>, <a href="https://github.com/f-y/md-spreadsheet-parser/blob/main/COOKBOOK.ja.md">Cookbook</a>
)

## Table of Contents

- [Features](#features)
- [Installation](#installation)
- [Usage](#usage)
    - [1. Basic Parsing](#1-basic-parsing)
    - [GFM Feature Support](#gfm-feature-support)
    - [2. Type-Safe Validation](#2-type-safe-validation-recommended)
        - [Pydantic Integration](#pydantic-integration)
    - [3. JSON & Dictionary Conversion](#3-json--dictionary-conversion)
    - [4. Pandas Integration & Export](#4-pandas-integration--export)
    - [5. Excel Import](#5-excel-import)
    - [6. Markdown Generation](#6-markdown-generation-round-trip)
    - [7. Advanced Features](#7-advanced-features)
    - [8. Advanced Type Conversion](#8-advanced-type-conversion)
    - [9. Robustness](#9-robustness-handling-malformed-tables)
    - [10. In-Cell Line Break Support](#10-in-cell-line-break-support)
    - [11. Performance & Scalability (Streaming API)](#11-performance--scalability-streaming-api)
    - [12. Programmatic Manipulation](#12-programmatic-manipulation)
    - [13. Visual Metadata Persistence](#13-visual-metadata-persistence)
    - [Command Line Interface (CLI)](#command-line-interface-cli)
- [Configuration](#configuration)
- [Ecosystem](#ecosystem)
- [License](#license)

## Features

- **Pure Python & Zero Dependencies**: Lightweight and portable. Perfect for **AWS Lambda Layers** and constrained environments. Runs anywhere Python runs, including **WebAssembly (Pyodide)**.
- **Type-Safe Validation**: Convert loose Markdown tables into strongly-typed Python `dataclasses` with automatic type conversion, including customizable boolean logic (I18N) and custom type converters.
- **Markdown as a Database**: Treat your Markdown files as Git-managed configuration or master data. Validate schema and types automatically, preventing human error in handwritten tables.
- **Round-Trip Support**: Parse to objects, modify data, and generate Markdown back. Perfect for editors.
- **GFM Compliance**: Supports GitHub Flavored Markdown (GFM) specifications, including column alignment (`:--`, `:--:`, `--:`) and correct handling of pipes within inline code (`` `|` ``).
- **Robust Parsing**: Gracefully handles malformed tables (missing/extra columns) and escaped characters.
- **Multi-Table Workbooks**: Support for parsing multiple sheets and tables from a single file, including metadata.
- **JSON & Dict Support**: Column-level JSON parsing and direct conversion to `dict`/`TypedDict`.
- **Pandas Integration**: seamlessly create DataFrames from markdown tables.
- **Excel Import & Data Cleaning**: Convert Excel/TSV/CSV to Markdown with intelligent merged cell handling. Automatically flattens hierarchical headers and fills gaps, turning "dirty" spreadsheets into clean, structured data.
- **JSON-Friendly**: Easy export to dictionaries/JSON for integration with other tools.

## Installation

```bash
pip install md-spreadsheet-parser
```

## Usage

### 1. Basic Parsing

**Single Table**
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

**Multiple Tables (Workbook)**
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

**Lookup API & Metadata**
Retrieve sheets and tables directly by name, and access parsed metadata like descriptions.

```python
from md_spreadsheet_parser import parse_workbook

markdown = """
# Tables

## Sales Data

### Q1 Results
Financial performance for the first quarter.

| Year | Revenue |
| ---- | ------- |
| 2023 | 1000    |
"""

workbook = parse_workbook(markdown)

# Access by name
sheet = workbook.get_sheet("Sales Data")
if sheet:
    # Retrieve table by name (from ### Header)
    table = sheet.get_table("Q1 Results")
    
    print(table.description)
    # "Financial performance for the first quarter."
    
    print(table.rows)
    # [['2023', '1000']]
```

**Simple Scan Interface**
If you want to extract *all* tables from a document regardless of its structure (ignoring sheets and headers), use `scan_tables`.

```python
from md_spreadsheet_parser import scan_tables

markdown = """
| ID | Name |
| -- | ---- |
| 1  | Alice|

... text ...

| ID | Item |
| -- | ---- |
| A  | Apple|
"""

# Returns a flat list of all tables found
tables = scan_tables(markdown)
print(len(tables)) # 2
```

**File Loading Helpers**

For convenience, you can parse directly from a file path (`str` or `Path`) or file-like object using the `_from_file` variants:

```python
from md_spreadsheet_parser import parse_workbook_from_file

# Clean and easy
workbook = parse_workbook_from_file("data.md")
```

Available helpers:
- `parse_table_from_file(path_or_file)`
- `parse_workbook_from_file(path_or_file)`
- `scan_tables_from_file(path_or_file)`

### GFM Feature Support

The parser strictly adheres to GitHub Flavored Markdown (GFM) specifications for tables.

**Column Alignment**
Alignment markers in the separator row are parsed and preserved.

```python
markdown = """
| Left | Center | Right |
| :--- | :----: | ----: |
| 1    | 2      | 3     |
"""
table = parse_table(markdown)
print(table.alignments)
# ["left", "center", "right"]
```

**Pipes in Code & Escaping**
Pipes `|` inside inline code blocks (backticks) or escaped with `\` are correctly treated as content, not column separators.

```python
markdown = """
| Code  | Escaped |
| ----- | ------- |
| `a|b` | \|      |
"""
table = parse_table(markdown)
# table.rows[0] == ["`a|b`", "|"]
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
*   **Type Conversion**: Automatically converts strings to `int`, `float`, `bool` using standard rules.
*   **Boolean Handling (Default)**: Supports standard pairs out-of-the-box: `true/false`, `yes/no`, `on/off`, `1/0`. (See [Advanced Type Conversion](#7-advanced-type-conversion) for customization).
*   **Optional Fields**: Handles `Optional[T]` by converting empty strings to `None`.
*   **Validation**: Raises detailed errors if data doesn't match the schema.

### Pydantic Integration

For more advanced validation (email format, ranges, regex), you can use [Pydantic](https://docs.pydantic.dev/) models instead of dataclasses. This feature is enabled automatically if `pydantic` is installed.

```python
from pydantic import BaseModel, Field, EmailStr

class User(BaseModel):
    name: str = Field(alias="User Name")
    age: int = Field(gt=0)
    email: EmailStr

# Automatically detects Pydantic model and uses it for validation
users = parse_table(markdown).to_models(User)
```

The parser respects Pydantic's `alias` and `Field` constraints.

### 3. JSON & Dictionary Conversion

Sometimes you don't want to define a full Dataclass or Pydantic model, or you have columns containing JSON strings.

**Simple Dictionary Output**
Convert tables directly to a list of dictionaries. Keys are derived from headers.

```python
# Returns list[dict[str, Any]] (Values are raw strings)
rows = parse_table(markdown).to_models(dict)
print(rows[0])
# {'Name': 'Alice', 'Age': '30'}
```

**TypedDict Support**
Use `TypedDict` for lightweight type safety. The parser uses the type annotations to convert values automatically.

```python
from typing import TypedDict

class User(TypedDict):
    name: str
    age: int
    active: bool

rows = parse_table(markdown).to_models(User)
print(rows[0])
# {'name': 'Alice', 'age': 30, 'active': True}
```

**Column-Level JSON Parsing**
If a field is typed as `dict` or `list` (in a Dataclass or Pydantic model), the parser **automatically parses the cell value as JSON**.

```python
@dataclass
class Config:
    id: int
    metadata: dict  # Cell: '{"debug": true}' -> Parsed to dict
    tags: list      # Cell: '["a", "b"]'      -> Parsed to list

# Pydantic models also work without Json[] wrapper
class ConfigModel(BaseModel):
    metadata: dict
```

**Limitations:**
*   **JSON Syntax**: The cell content must be valid JSON (e.g. double quotes `{"a": 1}`). Malformed JSON raises a `ValueError`.
*   **Simple Dict Parsing**: `to_models(dict)` does *not* automatically parse inner JSON strings unless you use a custom schema. It only creates a shallow dictionary of strings.

### 4. Pandas Integration & Export

This library is designed to be a bridge between Markdown and Data Science tools like **Pandas**.

**Convert to DataFrame (Easiest Way)**
The cleanest way to create a DataFrame is using `to_models(dict)`. This returns a list of dictionaries that Pandas can ingest directly.

```python
import pandas as pd
from md_spreadsheet_parser import parse_table

markdown = """
| Date       | Sales | Region |
|------------|-------|--------|
| 2023-01-01 | 100   | US     |
| 2023-01-02 | 150   | EU     |
"""

table = parse_table(markdown)

# 1. Convert to list of dicts
data = table.to_models(dict)

# 2. Create DataFrame
df = pd.DataFrame(data)

# 3. Post-Process: Convert types (Pandas usually infers strings initially)
df["Sales"] = pd.to_numeric(df["Sales"])
df["Date"] = pd.to_datetime(df["Date"])

print(df.dtypes)
# Date      datetime64[ns]
# Sales              int64
# Region            object
```

**Convert from Type-Safe Objects**
If you want to validate data **before** creating a DataFrame (e.g., ensuring "Sales" is an integer during parsing), use a `dataclass` and then convert to Pandas.

```python
from dataclasses import dataclass, asdict

@dataclass
class SalesRecord:
    date: str
    amount: int
    region: str

# 1. Parse and Validate (Raises TableValidationError if invalid)
records = parse_table(markdown).to_models(SalesRecord)

# 2. Convert to DataFrame using asdict()
df = pd.DataFrame([asdict(r) for r in records])

# The 'amount' column is already int64 because validation handled conversion
print(df["amount"].dtype) # int64
```

**JSON Export**
All result objects (`Workbook`, `Sheet`, `Table`) have a `.json` property that returns a dictionary structure suitable for serialization.

```python
import json

# Export entire workbook structure
print(json.dumps(workbook.json, indent=2))
```


### 5. Excel Import

Import Excel data (via TSV/CSV or `openpyxl`) with intelligent handling of merged cells and hierarchical headers.

> [!NOTE]
> Importing from TSV/CSV text works with **zero dependencies**. Direct `.xlsx` file loading requires `openpyxl` (a user-managed optional dependency).

**Basic Usage**

🚀 **See the [Cookbook](https://github.com/f-y/md-spreadsheet-parser/blob/main/COOKBOOK.md) for more comprehensive recipes.**

```python
from md_spreadsheet_parser import parse_excel

# From TSV/CSV (Zero Dependency)
table = parse_excel("Name\tAge\nAlice\t30")

# From .xlsx (requires openpyxl)
import openpyxl
wb = openpyxl.load_workbook("data.xlsx")
table = parse_excel(wb.active)
```

**Merged Header Handling**

When Excel exports merged cells, they appear as empty cells. The parser automatically forward-fills these gaps:

```text
Excel (merged headers):
┌─────────────────────────────┬────────┐
│      Category (3 cols)      │  Info  │
├─────────┬─────────┬─────────┼────────┤
│    A    │    B    │    C    │   D    │
└─────────┴─────────┴─────────┴────────┘

          ↓ parse_excel()

Markdown:
| Category | Category | Category | Info |
|----------|----------|----------|------|
| A        | B        | C        | D    |
```

**2-Row Hierarchical Headers**

For complex headers with parent-child relationships, use `ExcelParsingSchema(header_rows=2)`:

```text
Excel (2-row header):
┌───────────────────┬───────────────────┐
│       Info        │      Metrics      │  ← Row 1 (Parent)
├─────────┬─────────┼─────────┬─────────┤
│  Name   │   ID    │  Score  │  Rank   │  ← Row 2 (Child)
├─────────┼─────────┼─────────┼─────────┤
│  Alice  │   001   │   95    │    1    │
└─────────┴─────────┴─────────┴─────────┘

          ↓ parse_excel(schema=ExcelParsingSchema(header_rows=2))

Markdown:
| Info - Name | Info - ID | Metrics - Score | Metrics - Rank |
|-------------|-----------|-----------------|----------------|
| Alice       | 001       | 95              | 1              |
```

> **Note:** Currently supports up to 2 header rows. For deeper hierarchies, pre-process your data before parsing.

**Excel to Structured Objects (The "Killer" Feature)**

Don't just convert to text—convert Excel directly to valid, type-safe Python objects in one step.

```python
@dataclass
class SalesRecord:
    category: str
    item: str
    amount: int  # Automatic string-to-int conversion

# 1. Parse Excel (handles merged cells automatically)
# 2. Validate & Convert to objects
records = parse_excel(ws).to_models(SalesRecord)

# Now you have clean, typed data
assert records[0].amount == 1000
```

**Configuration**

Use `ExcelParsingSchema` to customize parsing behavior:

```python
from md_spreadsheet_parser import parse_excel, ExcelParsingSchema

schema = ExcelParsingSchema(
    header_rows=2,
    fill_merged_headers=True,
    header_separator=" / "
)

table = parse_excel(source, schema)
```

| Option | Default | Description |
|--------|---------|-------------|
| `header_rows` | `1` | Number of header rows (1 or 2). |
| `fill_merged_headers` | `True` | Forward-fill empty header cells. |
| `header_separator` | `" - "` | Separator for flattened 2-row headers. |
| `delimiter` | `"\t"` | Column separator for TSV/CSV. |


### 6. Markdown Generation (Round-Trip)

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

### 7. Advanced Features

**Metadata Extraction Configuration**
By default, the parser captures table names (level 3 headers) and descriptions. You can customize this behavior with `MultiTableParsingSchema`.

```python
from md_spreadsheet_parser import MultiTableParsingSchema

schema = MultiTableParsingSchema(
    table_header_level=3,     # Treat ### Header as table name
    capture_description=True  # Capture text between header and table
)
# Pass schema to parse_workbook...
```

### 8. Advanced Type Conversion

You can customize how string values are converted to Python objects by passing a `ConversionSchema` to `to_models()`. This is useful for internationalization (I18N) and handling custom types.

**Internationalization (I18N): Custom Boolean Pairs**

Configure which string pairs map to `True`/`False` (case-insensitive).

```python
from md_spreadsheet_parser import parse_table, ConversionSchema

markdown = """
| User | Active? |
| --- | --- |
| Tanaka | はい |
| Suzuki | いいえ |
"""

# Configure "はい" -> True, "いいえ" -> False
schema = ConversionSchema(
    boolean_pairs=(("はい", "いいえ"),)
)

users = parse_table(markdown).to_models(User, conversion_schema=schema)
# Tanaka.active is True
```

**Custom Type Converters**

Register custom conversion functions for specific types. You can use **ANY Python type** as a key, including:

- **Built-ins**: `int`, `float`, `bool` (to override default behavior)
- **Standard Library**: `Decimal`, `datetime`, `date`, `ZoneInfo`, `UUID`
- **Custom Classes**: Your own data classes or objects

Example using standard library types and a custom class:

```python
from dataclasses import dataclass
from uuid import UUID
from zoneinfo import ZoneInfo
from md_spreadsheet_parser import ConversionSchema, parse_table

@dataclass
class Color:
    r: int
    g: int
    b: int

@dataclass
class Config:
    timezone: ZoneInfo
    session_id: UUID
    theme_color: Color

markdown = """
| Timezone | Session ID | Theme Color |
| --- | --- | --- |
| Asia/Tokyo | 12345678-1234-5678-1234-567812345678 | 255,0,0 |
"""

schema = ConversionSchema(
    custom_converters={
        # Standard Library Types
        ZoneInfo: lambda v: ZoneInfo(v),
        UUID: lambda v: UUID(v),
        # Custom Class
        Color: lambda v: Color(*map(int, v.split(",")))
    }
)

data = parse_table(markdown).to_models(Config, conversion_schema=schema)
# data[0].timezone is ZoneInfo("Asia/Tokyo")
# data[0].theme_color is Color(255, 0, 0)
```

**Field-Specific Converters**

For granular control, you can define converters for specific field names, which take precedence over type-based converters.

```python
def parse_usd(val): ...
def parse_jpy(val): ...

schema = ConversionSchema(
    # Type-based defaults (Low priority)
    custom_converters={
        Decimal: parse_usd 
    },
    # Field-name overrides (High priority)
    field_converters={
        "price_jpy": parse_jpy,
        "created_at": lambda x: datetime.strptime(x, "%Y/%m/%d")
    }
)

# price_usd (no override) -> custom_converters (parse_usd)
# price_jpy (override)    -> field_converters (parse_jpy)
data = parse_table(markdown).to_models(Product, conversion_schema=schema)
```

**Standard Converters Library**

For common patterns (currencies, lists), you can use the built-in helper functions in `md_spreadsheet_parser.converters` instead of writing your own.

```python
from md_spreadsheet_parser.converters import (
    to_decimal_clean,        # Handles "$1,000", "¥500" -> Decimal
    make_datetime_converter, # Factory for parse/TZ logic
    make_list_converter,     # "a,b,c" -> ["a", "b", "c"]
    make_bool_converter      # Custom strict boolean sets
)

schema = ConversionSchema(
    custom_converters={
        # Currency: removes $, ¥, €, £, comma, space
        Decimal: to_decimal_clean,
        # DateTime: ISO format default, attach Tokyo TZ if naive
        datetime: make_datetime_converter(tz=ZoneInfo("Asia/Tokyo")),
        # Lists: Split by comma, strip whitespace
        list: make_list_converter(separator=",")
    },
    field_converters={
        # Custom boolean for specific field
        "is_valid": make_bool_converter(true_values=["OK"], false_values=["NG"])
    }
)
```

### 9. Robustness (Handling Malformed Tables)

The parser is designed to handle imperfect markdown tables gracefully.

*   **Missing Columns**: Rows with fewer columns than the header are automatically **padded** with empty strings.
*   **Extra Columns**: Rows with more columns than the header are automatically **truncated**.

```python
from md_spreadsheet_parser import parse_table

markdown = """
| A | B |
|---|---|
| 1 |       <-- Missing column
| 1 | 2 | 3 <-- Extra column
"""

table = parse_table(markdown)

print(table.rows)
# [['1', ''], ['1', '2']]
```

This ensures that `table.rows` always matches the structure of `table.headers`, preventing crashes during iteration or validation.

### 10. In-Cell Line Break Support

The parser automatically converts HTML line breaks to Python newlines (`\n`). This enables handling multiline cells naturally.

**Supported Tags (Case-Insensitive):**
- `<br>`
- `<br/>`
- `<br />`

```python
markdown = "| Line1<br>Line2 |"
table = parse_table(markdown)
# table.rows[0][0] == "Line1\nLine2"
```

**Round-Trip Support:**
When generating Markdown (e.g., `table.to_markdown()`), Python newlines (`\n`) are automatically converted back to `<br>` tags to preserve the table structure.

To disable this, set `convert_br_to_newline=False` in `ParsingSchema`.

### 11. Performance & Scalability (Streaming API)

**Do you really have a 10GB Markdown file?**

Probably not. We sincerely hope you don't. Markdown wasn't built for that.

But *if you do*—perhaps you're generating extensive logs or auditing standard converters—this library has your back. While Excel gives up after 1,048,576 rows, `md-spreadsheet-parser` supports streaming processing for files of **unlimited size**, keeping memory usage constant.

**scan_tables_iter**:
This function reads the file line-by-line and yields `Table` objects as they are found. It does **not** load the entire file into memory.

```python
from md_spreadsheet_parser import scan_tables_iter

# Process a massive log file (e.g., 10GB)
# Memory usage remains low (only the size of a single table block)
for table in scan_tables_iter("huge_server_log.md"):
    print(f"Found table with {len(table.rows)} rows")
    
    # Process rows...
    for row in table.rows:
        pass
```

This is ideal for data pipelines, log analysis, and processing exports that are too large to open in standard spreadsheet editors.

### 12. Programmatic Manipulation

The library provides immutable methods to modify the data structure. These methods return a **new instance** of the object with the changes applied, keeping the original object unchanged.

**Workbook Operations**
```python
# Add a new sheet (creates a default table with headers A, B, C)
new_wb = workbook.add_sheet("New Sheet")

# Rename a sheet
new_wb = workbook.rename_sheet(sheet_index=0, new_name("Budget 2024"))

# Delete a sheet
new_wb = workbook.delete_sheet(sheet_index=1)
```

**Sheet Operations**
```python
# Rename sheet (direct method)
new_sheet = sheet.rename("Q1 Data")

# Update table metadata
new_sheet = sheet.update_table_metadata(
    table_index=0, 
    name="Expenses", 
    description="Monthly expense report"
)
```

**Table Operations**
```python
# Update a cell (automatically expands table if index is out of bounds)
new_table = table.update_cell(row_idx=5, col_idx=2, value="Updated")

# Delete a row (structural delete)
new_table = table.delete_row(row_idx=2)

# Clear column data (keeps headers and row structure, empties cells)
new_table = table.clear_column_data(col_idx=3)
```

### 13. Visual Metadata Persistence

The library supports persisting visual state (like column widths and filter settings) without altering the Markdown table structure itself. This is achieved via a hidden HTML comment appended after the table.

```markdown
| A | B |
|---|---|
| 1 | 2 |

<!-- md-spreadsheet-table-metadata: {"columnWidths": [100, 200]} -->
```

This ensures that:
1.  **Clean Data**: The table remains standard Markdown, readable by any renderer.
2.  **Rich State**: Compatible tools (like our VS Code Extension) can read the comment to restore UI state (column widths, hidden columns, etc.).
3.  **Robustness**: The parser automatically associates this metadata with the preceding table, even if separated by blank lines.

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
- `--table-header-level`: Set table header level (default: 3).
- `--capture-description`: Capture table descriptions (default: True).
- `--column-separator`: Character used to separate columns (default: `|`).
- `--header-separator-char`: Character used in the separator row (default: `-`).
- `--no-outer-pipes`: Allow tables without outer pipes (default: False).
- `--no-strip-whitespace`: Do not strip whitespace from cell values (default: False).
- `--no-br-conversion`: Disable automatic conversion of `<br>` tags to newlines (default: False).

## Configuration

Customize parsing behavior using `ParsingSchema` and `MultiTableParsingSchema`.

| Option | Default | Description |
| :--- | :--- | :--- |
| `column_separator` | `\|` | Character used to separate columns. |
| `header_separator_char` | `-` | Character used in the separator row. |
| `require_outer_pipes` | `True` | If `True`, generated markdown tables will include outer pipes. |
| `strip_whitespace` | `True` | If `True`, whitespace is stripped from cell values. |
| `convert_br_to_newline` | `True` | If `True`, `<br>` tags are converted to `\n` (and back). |
| `root_marker` | `# Tables` | (MultiTable) Marker indicating start of data section. |
| `sheet_header_level` | `2` | (MultiTable) Header level for sheets. |
| `table_header_level` | `3` | (MultiTable) Header level for tables. |
| `capture_description` | `True` | (MultiTable) Capture text between header and table. |

## Ecosystem
 
This parser is the core foundation of a new ecosystem: **Text-Based Spreadsheet Management**.

It powers **[PengSheets](https://marketplace.visualstudio.com/items?itemName=f-y.peng-sheets)**, a rich VS Code extension that provides a full GUI Spreadsheet Editor for Markdown files.

**The Vision: "Excel-like UX, Git-native Data"**
By combining a high-performance editor with this robust parser, we aim to solve the long-standing problem of managing binary spreadsheet files in software projects.
*   **For Humans**: Edit data with a comfortable, familiar UI (cell formatting, improved navigation, visual feedback).
*   **For Machines**: Data is saved as clean, diff-able Markdown that this library can parse, validate, and convert into Python objects instantaneously.

## License

This project is licensed under the [MIT License](https://github.com/f-y/md-spreadsheet-parser/blob/main/LICENSE).
