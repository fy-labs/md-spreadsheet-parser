# Changelog

## [1.2.2] - 2026-01-23

### 📚 Documentation

docs: Add PengSheets announcement and update NPM READMEs

- **Core**: Added PengSheets announcement to `README.md` and `README.ja.md`.
- **Core**: Fixed invalid `update_table_metadata` example in `README.md`.
- **NPM**: Added `packages/npm/README.ja.md` (Japanese translation).
- **NPM**: Updated logic parity claims and Excel limitations text.

## [1.2.1] - 2026-01-22

### 🐛 Bug Fixes

Ensure JSON output for CLI and metadata uses Unicode characters instead of escape sequences (e.g. Japanese).

## [1.2.0] - 2026-01-10

### 🚀 New Features

Added consistent CRUD operation methods to Workbook, Sheet, and Table models:

**Workbook**:
- `move_sheet(from_index, to_index)` - reorder sheets
- `replace_sheet(index, sheet)` - replace sheet at index
- `rename_sheet(index, new_name)` - rename sheet at index

**Sheet**:
- `rename(new_name)` - rename the sheet
- `add_table(name?)` - append a new empty table
- `delete_table(index)` - remove table at index
- `replace_table(index, table)` - replace table at index
- `move_table(from_index, to_index)` - reorder tables

**Table**:
- `rename(new_name)` - rename the table
- `move_row(from_index, to_index)` - reorder rows
- `move_column(from_index, to_index)` - reorder columns
## NPM Package E2E Test Restructuring and Coverage Expansion

Comprehensive improvements to the NPM package testing infrastructure:

### Test Restructuring
- Migrated from monolithic `scripts/test.mjs` to modular `tests/` directory
- Split tests into dedicated files: `parsing.test.mjs`, `table.test.mjs`, `sheet.test.mjs`, `workbook.test.mjs`, `tomodels.test.mjs`
- Added shared `helpers.mjs` with assertion utilities and `runner.mjs` test orchestrator

### API Improvements
- `replaceTable` and `replaceSheet` now auto-convert model instances to DTO (no explicit `.toDTO()` required)
- Full API parity with Python: users can pass `Table`/`Sheet` instances directly

### Test Coverage Expansion (204 → 235 assertions)
- Added tests for: `deleteRow`, `deleteColumn`, `insertRow`, `insertColumn`, `clearColumnData`
- Added `Sheet.getTable` tests
- Added `parseTableFromFile`, `parseWorkbookFromFile`, `scanTablesFromFile` function verification

### Documentation
- Created `DEVELOPMENT.md` documenting the Python-to-NPM workflow
Added comprehensive E2E tests for NPM package (118 test cases) covering parseTable, parseWorkbook, scanTables, Table/Sheet/Workbook methods, deep metadata type verification, toModels with Plain Object and Zod schemas, and mutation API return values. Also improved .gitignore documentation, fixed verify_api_coverage.py, and added Limitations section to README documenting parseExcel unavailability.

## [1.1.11] - 2026-01-09

### 🐛 Bug Fixes

Fixed `Object.assign(this, res)` usage in NPM package causing `metadata` to remain as a JSON string.

The TypeScript wrapper generator (`scripts/generate_wit.py`) now produces proper hydration code that reconstructs objects via the constructor, ensuring:
- `metadata` is parsed from JSON string to `Record<string, any>` (matching Python's `dict[str, any]`)
- Nested models (e.g., `Sheet` within `Workbook`, `Table` within `Sheet`) are properly instantiated as class instances

## [1.1.10] - 2026-01-08

### 🐛 Bug Fixes

Fixed nested models in NPM package constructors to properly wrap child elements.

- Sheet constructor now wraps tables array items as Table instances
- Workbook constructor now wraps sheets array items as Sheet instances
- This ensures `json` getter recursively returns objects with proper metadata types
- Previously, nested metadata was returned as strings instead of objects

## [1.1.9] - 2026-01-08

### 🚀 New Features

Added `json` getter to Table, Sheet, and Workbook classes in the NPM package.

- The `json` getter mirrors Python's `.json` property
- Returns a JSON-compatible plain object representation
- Recursively converts nested models (e.g., Sheet.json includes all tables.json)

## [1.1.8] - 2026-01-07

### 🐛 Bug Fixes

Fixed WASM loading in Vite dev mode by using `import.meta.url` for proper path resolution.

- Modified build script to post-process JCO transpile output
- Replaced relative path `fetch('./parser.core.wasm')` with `fetch(new URL('./parser.core.wasm', import.meta.url))`
- This ensures WASM files are correctly resolved in both bundled and development environments

## [1.1.7] - 2026-01-07

### 🚀 New Features

NPM package now builds and works correctly in browser environments (Vite, Webpack, etc.).

- Core APIs (`parseTable`, `parseWorkbook`, `scanTables`, etc.) work seamlessly in both Node.js and browser environments
- File-based APIs (`parseTableFromFile`, `parseWorkbookFromFile`, `scanTablesFromFile`) are now async functions that:
  - Work correctly in Node.js with lazy WASI filesystem initialization
  - Throw a clear error message in browser environments with guidance to use string-based alternatives
- Fixed `_addPreopen is not exported` error when using Vite or other browser bundlers

## [1.1.6] - 2026-01-07

### 🐛 Bug Fixes

Fixed `Workbook.to_markdown()` to accept an optional `schema` argument, defaulting to a standard `MultiTableParsingSchema`. This aligns the API with `Sheet.to_markdown()` and `Table.to_markdown()`.

## [1.1.5] - 2026-01-06

### 🐛 Bug Fixes

Reduced NPM package size by excluding redundant intermediate WASM files.

## [1.1.4] - 2026-01-06

### 🐛 Bug Fixes

---
title: Fix WASI File Access
type: fix
---

Fixed an issue where `parseWorkbookFromFile` failed with `FileNotFoundError` in the NPM package environment.

- Configured WASI preopens to map the system root (e.g., `/` on macOS, `C:\` on Windows) to the Guest root.
- Implemented `resolveToVirtualPath` to automatically resolve relative paths against the Host's CWD and absolute paths against the system root.
- `parseWorkbookFromFile` now correctly handles both relative and absolute paths in Node.js environments.

## [1.1.3] - 2026-01-05

### 🐛 Bug Fixes

Fixed a critical bug in the NPM package where `Workbook.getSheet()` and `Sheet.getTable()` returned plain objects instead of class instances. Now verifies that proper `Sheet` and `Table` instances are returned, restoring API compatibility.
Also fixed an issue where optional return types (like `optional<Sheet>`) were not correctly handled in the wrapper.

## [1.1.2] - 2026-01-05

### 🐛 Bug Fixes

Move `@bytecodealliance/preview2-shim` to `dependencies` to ensure it is available at runtime. This fixes `ERR_MODULE_NOT_FOUND` when using the package in a fresh environment.

## [1.1.1] - 2026-01-05

### 🔧 Maintenance

Update NPM publishing workflow to use Trusted Publishing (OIDC) instead of secret tokens.

## [1.1.0] - 2026-01-05

### 🚀 New Features

### NPM Package Support (WASM/Python Bridge)

Introduced comprehensive support for building an NPM package (`md-spreadsheet-parser`) powered by the Python core via WebAssembly (WASM).

*   **WASM Compilation**: Uses `componentize-py` to compile the Python library into a WASM Component, enabling usage in Node.js environments.
*   **TypeScript Wrappers**: Automatically generates high-fidelity TypeScript class wrappers that mirror the Python object model (API Parity).
    *   Python `Table`, `Workbook`, `Sheet` classes are fully exposed in TypeScript.
    *   Methods like `toMarkdown`, `updateCell`, and `addSheet` are available directly on TypeScript objects.
*   **Seamless Integration**:
    *   **JSON Marshalling**: Metadata dictionaries are automatically handled (serialized/deserialized) across the boundary.
    *   **Optional Arguments**: Python default arguments are correctly mapped to optional TypeScript parameters (e.g., `schema?`).
    *   **Client-Side Mapping**: `Table.toModels` supports passing browser-side schema classes or Zod-like validators.
*   **Verification**: Added a robust verification environment (`verification-env`) ensuring cross-language compatibility.

### 🐛 Bug Fixes

# Fix table metadata tag recognition

Fixed a bug in `parsing.py` where the parser was incorrectly looking for `<!-- md-spreadsheet-metadata: ... -->` instead of `<!-- md-spreadsheet-table-metadata: ... -->` when extracting tables from blocks. This ensures consistency with the generator and specification.

### 🔧 Maintenance

---
type: chore
---

**Metadata**: Updated PyPI Development Status to **Production/Stable**.

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