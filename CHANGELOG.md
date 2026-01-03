# Changelog

## [1.0.1] - 2026-01-03

### 🔧 Maintenance

---
type: chore
---

**Metadata**: Updated PyPI Development Status to **Production/Stable**.

## [1.0.0] - 2026-01-03

### 📚 Documentation

---
type: docs
---

**Documentation**: Added announcement for the official VS Code Extension **PengSheets** release.
Remove outdated roadmap and features section from READMEs.
Complete README.ja.md translation and update metadata tag example in README.md.

## [0.8.1] - 2026-01-01

### 🚀 New Features

# i18n support and Japanese documentation

Added Japanese translation for `README.md` and `COOKBOOK.md`.
Configured `mkdocs-static-i18n` to support bilingual documentation (English/Japanese).
Added language switcher with globe icon to the documentation site.

### 🔧 Maintenance

### Tests

- Added robustness test `test_root_marker_robustness.py` to verify behavior when `# Tables` root marker is missing.

## [0.8.0] - 2025-12-30

### ⚠️ Breaking Changes

### Metadata Tag Update (Breaking)

- **BREAKING**: Renamed `<!-- md-spreadsheet-metadata: ... -->` to `<!-- md-spreadsheet-table-metadata: ... -->` for consistency.
- Backward compatibility for the old tag has been dropped. Existing files with the old tag will still be parsed as tables, but the visual metadata (column widths, validation, etc.) will be ignored until manually updated.

### 📚 Documentation

Added SECURITY.md with reporting instructions.

## [0.7.2] - 2025-12-27

### 🚀 New Features

Add GitHub Actions workflows for PyPI and TestPyPI publishing.

## [0.7.1] - 2025-12-24

### 🐛 Bug Fixes

### Workbook Metadata Location

- **Fix**: Relaxed the location requirement for Workbook metadata. It can now appear anywhere in the file (e.g., before additional documentation sections), not just at the strictly last non-empty line.

## [0.7.0] - 2025-12-24

### 🚀 New Features

### Workbook Metadata Support

Added `metadata` field to the `Workbook` model, allowing arbitrary data storage at the workbook level. This aligns the `Workbook` model with `Sheet` and `Table` models.

```python
wb = Workbook(sheets=[], metadata={"author": "Alice"})
# Metadata is persisted at the end of the file:
# <!-- md-spreadsheet-workbook-metadata: {"author": "Alice"} -->
```

### 🐛 Bug Fixes

### Excel Parsing Improvements

- **Fix**: Improved hierarchical header flattening for vertically merged cells (e.g., prohibiting trailing separators like `Status - `).
- **Enhancement**: Cleaner string conversion for Excel numbers; integer-floats (e.g., `1.0`) are now automatically converted to valid integers (`"1"`) instead of preserving the decimal (`"1.0"`).

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