# Changelog

## [0.6.0] - 2025-12-23

### 🚀 New Features

Add Excel parsing support with merged cell handling

New functions:
- `parse_excel()`: Parse Excel data from Worksheet, TSV/CSV string, or 2D array
- `parse_excel_text()`: Core function for processing 2D string arrays

Features:
- Forward-fill for merged header cells
- 2-row header flattening ("Parent - Child" format)
- Auto-detect openpyxl.Worksheet if installed
Added a script `scripts/build_pyc_wheel.py` to generate optimized wheels containing pre-compiled bytecode (`.pyc` only) for faster loading in Pyodide environments (specifically for the VS Code extension).

See GitHub Releases:
https://github.com/f-y/md-spreadsheet-parser/releases