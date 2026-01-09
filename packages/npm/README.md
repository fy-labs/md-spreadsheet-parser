# md-spreadsheet-parser (NPM)

<p align="center">
  <img src="https://img.shields.io/badge/wasm-powered-purple.svg" alt="WASM Powered" />
  <a href="https://github.com/f-y/md-spreadsheet-parser/blob/main/LICENSE">
    <img src="https://img.shields.io/badge/license-MIT-blue.svg" alt="License" />
  </a>
</p>

**md-spreadsheet-parser** is a robust Markdown table parser and manipulator for Node.js.
It is powered by the [Python Core](https://github.com/f-y/md-spreadsheet-parser) compiled to WebAssembly, ensuring 100% logic parity with the Python version while running natively in Node.js.

## Features

- **🚀 High Performance**: Pre-compiled WASM binary (initialized in ~160ms).
- **💪 Robust Parsing**: Handles GFM tables, missing columns, and escaped pipes correctly.
- **🛠️ Spreadsheet Operations**: Edit cells, add/remove rows, and re-generate Markdown programmatically.
- **🛡️ Type-Safe Validation**: Validate table data against schemas (Plain Object or Zod).
- **📂 File System Support**: Direct file reading capabilities.

## Installation

```bash
npm install md-spreadsheet-parser
```

## Usage Guide

### 1. Basic Parsing (String)

Parse a Markdown table string into a structured `Table` object.

```javascript
import { parseTable } from 'md-spreadsheet-parser';

const markdown = `
| Name | Age |
| --- | --- |
| Alice | 30 |
`;

const table = parseTable(markdown);
console.log(table.rows); // [ [ 'Alice', '30' ] ]
```

### 2. File System Usage

You can parse files directly without reading them into a string first.

```javascript
import { parseWorkbookFromFile, scanTablesFromFile } from 'md-spreadsheet-parser';

// Parse entire workbook (multiple sheets)
const workbook = parseWorkbookFromFile('./data.md');
console.log(`Parsed ${workbook.sheets.length} sheets`);

// Validating contents using Lookup API
const sheet = workbook.getSheet('Sheet1');
if (sheet) {
    const table = sheet.getTable(0); // Get first table
    console.log(table.headers);
}

// Or just scan for all tables in a file
const tables = scanTablesFromFile('./readme.md');
console.log(`Found ${tables.length} tables`);
```

### 3. Programmatic Editing

Table objects are mutable (CoW-like behavior internally). You can modify them and export back to Markdown.

```javascript
import { parseTable } from 'md-spreadsheet-parser';

const table = parseTable("| Item | Price |\n|---|---|\n| Apple | 100 |");

// Update Cell (Row 0, Col 1)
table.updateCell(0, 1, "150");

// Convert back to Markdown
console.log(table.toMarkdown());
// | Item | Price |
// | --- | --- |
// | Apple | 150 |
```

### 4. Type-Safe Validation (toModels)

You can convert string-based table data into typed objects.

#### Basic Usage (Plain Object Schema)
You can provide a simple schema object with converter functions.

```javascript
const markdown = `
| id | active |
| -- | ------ |
| 1  | yes    |
`;
const table = parseTable(markdown);

// Define Schema
const UserSchema = {
    id: (val) => Number(val),
    active: (val) => val === 'yes'
};

const users = table.toModels(UserSchema);
console.log(users);
// [ { id: 1, active: true } ]
```

#### Advanced Usage (Zod)
For robust validation, use [Zod](https://zod.dev/).

```javascript
import { z } from 'zod';

const UserZodSchema = z.object({
    id: z.coerce.number(),
    active: z.string().transform(v => v === 'yes')
});

const users = table.toModels(UserZodSchema);
// [ { id: 1, active: true } ]
```

## API Documentation

Since this package is a direct wrapper around the Python core, the fundamental concepts are identical. The API naming conventions are adapted for JavaScript (camelCase instead of snake_case).

- **Core Documentation**: [Python User Guide](https://github.com/f-y/md-spreadsheet-parser#usage)
- **Cookbook**: [Common Recipes](https://github.com/f-y/md-spreadsheet-parser/blob/main/COOKBOOK.md)

### Key Function Mappings

| Python (Core) | JavaScript (NPM) | Description |
|---|---|---|
| `parse_table(md)` | `parseTable(md)` | Parse a single table string |
| `parse_workbook(md)` | `parseWorkbook(md)` | Parse entire workbook string |
| `scan_tables(md)` | `scanTables(md)` | Extract all tables from string |
| `parse_workbook_from_file(path)` | `parseWorkbookFromFile(path)` | Parse file to Workbook |
| `scan_tables_from_file(path)` | `scanTablesFromFile(path)` | Extract tables from file |
| `Table.to_markdown()` | `Table.toMarkdown()` | Generate Markdown |
| `Table.update_cell(r, c, v)` | `Table.updateCell(r, c, v)` | Update specific cell |
| `Table.to_models(schema)` | `Table.toModels(schema)` | Convert to typed objects |
| `Workbook.get_sheet(name)` | `Workbook.getSheet(name)` | Get sheet by name |
| `Sheet.get_table(index)` | `Sheet.getTable(index)` | Get table by index |

## Limitations

The following Python features are **not available** in the NPM package:

| Feature | Reason |
|---------|--------|
| `parse_excel()` / `parseExcel()` | Excel file parsing requires `openpyxl`, which is not compatible with WASM |

For Excel file operations, use the [Python package](https://github.com/f-y/md-spreadsheet-parser) directly.

## Architecture

This package uses `componentize-py` to bundle the Python library as a WASM Component.
For more details, see [ARCHITECTURE.md](./ARCHITECTURE.md).

## License

MIT
