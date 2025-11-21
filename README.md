# Markdown Spreadsheet Parser

A lightweight, pure Python library for parsing Markdown tables into structured data.
Designed to be portable and run in WebAssembly environments (like Pyodide in VS Code extensions).

## Features

- **Pure Python**: Zero dependencies, runs anywhere Python runs (including WASM).
- **Structured Output**: Converts Markdown tables into JSON-friendly objects with headers and rows.
- **Configurable**: Supports different table styles via schemas.

## Installation

```bash
pip install md-spreadsheet-parser
```

## Usage

```python
from md_spreadsheet_parser import parse

markdown = """
| Name | Age |
| --- | --- |
| Alice | 30 |
| Bob | 25 |
"""

result = parse(markdown)

print(result.headers)
# ['Name', 'Age']

print(result.rows)
# [['Alice', '30'], ['Bob', '25']]
```

## License

MIT
