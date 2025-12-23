# Cookbook

This guide provides immediate solutions for common tasks.

## Table of Contents
1. [Installation](#1-installation)
2. [Read Tables from File](#2-read-tables-from-file-recommended)
3. [Read Table from Text](#3-read-table-from-text-simple)
4. [Excel Integration](#4-excel-integration)
5. [Pandas Integration](#5-pandas-integration)
6. [Programmatic Editing](#6-programmatic-editing-excel-like)
7. [Formatting & Linting](#7-formatting--linting)
8. [JSON Conversion](#8-json-conversion)
9. [Type-Safe Validation](#9-type-safe-validation)

## 1. Installation

```bash
pip install md-spreadsheet-parser
```

## 2. Read Tables from File (Recommended)

The easiest way to extract data from a Markdown file is using `scan_tables_from_file`. This works regardless of the file structure (ignoring headers like `#` or `##`).

**data.md**
```markdown
| ID | Name |
| -- | ---- |
| 1  | Alice |
| 2  | Bob   |
```

**Python**
```python
from md_spreadsheet_parser import scan_tables_from_file

# Returns a list of Table objects
tables = scan_tables_from_file("data.md")

for table in tables:
    print(table.rows)
    # [['1', 'Alice'], ['2', 'Bob']]
```

## 3. Read Table from Text (Simple)

If you have a markdown string, use `parse_table`.

```python
from md_spreadsheet_parser import parse_table

markdown = """
| ID | Name |
| -- | ---- |
| 1  | Alice |
"""

table = parse_table(markdown)
print(table.headers) # ['ID', 'Name']
print(table.rows[0]) # ['1', 'Alice']
```

## 4. Excel Integration

### Excel (TSV/CSV) → Markdown

**This is the easiest method!** Just copy cells from Excel and paste them as a string.

Convert Excel-exported TSV or CSV data to Markdown. Handles merged headers and in-cell newlines.

```python
from md_spreadsheet_parser import parse_excel, ExcelParsingSchema

# Paste your Excel data (TSV format)
tsv_data = """
ID\tName\tNotes
1\tAlice\t"Lines
include
newlines"
2\tBob\tSimple
""".strip()

table = parse_excel(tsv_data)
print(table.to_markdown())
```

**With Merged Headers (Forward-Fill)**
```python
# Excel merged cells export as: "Category\t\t\tInfo"
tsv = "Category\t\t\tInfo\nA\tB\tC\tD"
table = parse_excel(tsv)
# Headers: ["Category", "Category", "Category", "Info"]
```

**With 2-Row Hierarchical Headers**
```python
# Parent row: "Info\t\tMetrics\t"
# Child row:  "Name\tID\tScore\tRank"
tsv = "Info\t\tMetrics\t\nName\tID\tScore\tRank\nAlice\t001\t95\t1"
table = parse_excel(tsv, ExcelParsingSchema(header_rows=2))
# Headers: ["Info - Name", "Info - ID", "Metrics - Score", "Metrics - Rank"]
```

### Excel (.xlsx) → Markdown (with openpyxl)

If you have `openpyxl` installed, you can pass Worksheets directly.

```python
# pip install openpyxl  # User-managed dependency
import openpyxl
from md_spreadsheet_parser import parse_excel, ExcelParsingSchema

wb = openpyxl.load_workbook("report.xlsx", data_only=True)
ws = wb["SalesData"]  # Select sheet by name

table = parse_excel(ws, ExcelParsingSchema(header_rows=2))
print(table.to_markdown())
```

## 5. Pandas Integration

This library acts as a bridge between Markdown and Data Science tools.

### Markdown -> Pandas DataFrame

Convert parsed tables directly to a list of dictionaries, which Pandas can ingest.

```python
import pandas as pd
from md_spreadsheet_parser import scan_tables_from_file

tables = scan_tables_from_file("data.md")
df = pd.DataFrame(tables[0].to_models(dict))

print(df)
#   ID   Name
# 0  1  Alice
# 1  2    Bob
```

### Pandas DataFrame -> Markdown

Convert a Pandas DataFrame into a `Table` object to generate Markdown.

```python
import pandas as pd
from md_spreadsheet_parser import Table

# 1. Setup your DataFrame
df = pd.DataFrame({
    "ID": [1, 2],
    "Name": ["Alice", "Bob"]
})

# 2. Convert to Table
# Ensure all data is stringified for the parser
headers = df.columns.tolist()
rows = df.astype(str).values.tolist()

table = Table(headers=headers, rows=rows)

# 3. Generate Markdown
print(table.to_markdown())
# | ID | Name |
# | --- | --- |
# | 1 | Alice |
# | 2 | Bob |
```

## 6. Programmatic Editing (Excel-like)

You can load a table, modify values based on logic (e.g., formulas), and save it back.

```python
from md_spreadsheet_parser import parse_table

markdown = """
| Item | Price | Qty | Total |
|---|---|---|---|
| Apple | 100 | 2 | |
| Banana | 50 | 3 | |
"""

table = parse_table(markdown)

# Update "Total" column
# 1. basic string parsing (or use to_models for type safety)
new_rows = []
for row in table.rows:
    price = int(row[1])
    qty = int(row[2])
    total = price * qty
    
    # Create new row with updated total
    new_rows.append([row[0], row[1], row[2], str(total)])

# 2. Create new table with updates
updated_table = Table(headers=table.headers, rows=new_rows)
print(updated_table.to_markdown())
```

## 7. Formatting & Linting

Read a messy, misaligned Markdown table and output it perfectly formatted.

```python
from md_spreadsheet_parser import parse_table

# Messy input
messy_markdown = """
|Name|Age|
|---|---|
|Alice|30|
|Bob|25|
"""

table = parse_table(messy_markdown)

# Output clean Markdown
print(table.to_markdown())
# | Name | Age |
# | --- | --- |
# | Alice | 30 |
# | Bob | 25 |
```

## 8. JSON Conversion

Convert a table directly to a JSON string or list of dictionaries for API usage.

```python
import json
from md_spreadsheet_parser import parse_table

markdown = """
| ID | Status |
| -- | ------ |
| 1  | Open   |
"""

table = parse_table(markdown)

# Convert to list of dicts
data = table.to_models(dict)

# Dump to JSON
print(json.dumps(data, indent=2))
# [
#   {
#     "ID": "1",
#     "Status": "Open"
#   }
# ]
```

## 9. Type-Safe Validation

Convert loose text into strongly-typed Python objects.

```python
from dataclasses import dataclass
from md_spreadsheet_parser import parse_table

@dataclass
class User:
    id: int
    name: str
    active: bool = True

markdown = """
| id | name | active |
| -- | ---- | ------ |
| 1  | Alice| yes    |
| 2  | Bob  | no     |
"""

users = parse_table(markdown).to_models(User)

for user in users:
    print(f"{user.name} (Active: {user.active})")
    # Alice (Active: True)
    # Bob (Active: False)
```
