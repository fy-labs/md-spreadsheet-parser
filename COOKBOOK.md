# Cookbook

This guide provides immediate solutions for common tasks.

## Table of Contents
1. [Installation](#1-installation)
2. [Read Tables from File](#2-read-tables-from-file-recommended)
3. [Read Table from Text](#3-read-table-from-text-simple)
4. [Pandas / Excel Integration](#4-pandas--excel-integration)
5. [Programmatic Editing](#5-programmatic-editing-excel-like)
6. [Formatting & Linting](#6-formatting--linting)
7. [JSON Conversion](#7-json-conversion)
8. [Type-Safe Validation](#8-type-safe-validation)

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

## 4. Pandas / Excel Integration

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

### Excel (TSV) -> Markdown

One-off script to convert pasted Excel data (TSV) into a Markdown table. Handles quoted values and in-cell newlines correctly.

```python
import csv
import io
from md_spreadsheet_parser import Table

# Paste your Excel data here
tsv_data = """
ID	Name	Notes
1	Alice	"Lines
include
newlines"
2	Bob	Simple
""".strip()

# Use csv module for robust parsing
reader = csv.reader(io.StringIO(tsv_data), delimiter='\t')
rows = list(reader)

if rows:
    headers = rows[0]
    data_rows = rows[1:]
    
    # Generate Markdown
    table = Table(headers=headers, rows=data_rows)
    print(table.to_markdown())
```

## 5. Programmatic Editing (Excel-like)

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

## 6. Formatting & Linting

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

## 7. JSON Conversion

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

## 8. Type-Safe Validation

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
