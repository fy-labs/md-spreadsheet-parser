# NPM Package Development Guide

This guide documents the development workflow for the `md-spreadsheet-parser` NPM package.

## Prerequisites

- Python 3.11+ with `uv` package manager
- Node.js 20+
- The repository root is `md-spreadsheet-suite/md-spreadsheet-parser`

## Development Workflow

### 1. Adding New Python Features

When adding new methods to `Table`, `Sheet`, or `Workbook` in Python:

```bash
# 1. Edit Python source
cd md-spreadsheet-parser
# Edit src/md_spreadsheet_parser/models.py

# 2. Add Python tests
# Edit tests/core/test_models.py

# 3. Run Python tests
uv run pytest tests/core/test_models.py -v

# 4. Run static analysis  
uv run pyright

# 5. Create release fragment
# Create docs/changes/next/<topic>.<type>.md
```

### 2. Building the NPM Package

The NPM package auto-generates TypeScript bindings from Python source.

```bash
cd md-spreadsheet-parser

# Build Python wheel (outputs to dist/)
uv build -o dist

# Build NPM package
cd packages/npm
npm run build
```

> **Note**: `npm run build` uses the wheel from `md-spreadsheet-parser/dist/`. If multiple wheel versions exist, remove old ones to ensure the latest is used.

### 3. Running NPM Tests

```bash
npm test
```

Tests are located in `tests/`:

| File | Description |
|------|-------------|
| `helpers.mjs` | Assert functions (`assertMetadataIsObject`, etc.) |
| `parsing.test.mjs` | `parseTable`, `parseWorkbook`, `scanTables` |
| `table.test.mjs` | Table class methods |
| `sheet.test.mjs` | Sheet class methods |
| `workbook.test.mjs` | Workbook class methods |
| `tomodels.test.mjs` | `toModels` with schemas |
| `runner.mjs` | Test runner |

### 4. Adding NPM Tests

When adding new methods, mirror the Python test structure:

```javascript
// Example: Testing Table.rename()
const tableForRename = new Table({
    headers: ["H1", "H2"],
    rows: [["a", "b"]],
    name: "Old",
    metadata: { key: "value" }  // Include metadata for type safety
});

const renamedTable = tableForRename.rename("New");

// Verify the operation
assert(renamedTable.name === "New", "rename should change name");

// CRITICAL: Verify metadata is object, not string
assertMetadataIsObject(renamedTable.metadata, "metadata after rename");
assertEqual(renamedTable.metadata, { key: "value" }, "metadata value");
```

> **Key Pattern**: Always verify `metadata` remains an `object` type after operations. This catches type conversion bugs that occur during WASM serialization.

### 5. API Patterns

#### Replace Operations

`replaceTable` and `replaceSheet` accept both instances and plain objects:

```javascript
// Both work - auto-conversion handles instances
sheet.replaceTable(0, newTable);
sheet.replaceTable(0, { headers: [...], rows: [...] });

workbook.replaceSheet(0, newSheet);
workbook.replaceSheet(0, { name: "...", tables: [...] });
```

The generator auto-detects model arguments and converts them via `toDTO()` before WASM call.

#### Mutation Methods

Methods that mutate (`updateCell`, `rename`, etc.) use the Model Reconstruction Pattern:
- Return `this` for chaining
- Reconstruct internal state from WASM response
- Preserve metadata as object

## Troubleshooting

### Wrong Wheel Version Used

If new methods are missing after build:

```bash
# Check which wheel is being used
npm run build 2>&1 | grep "Using wheel"

# Remove old wheels
rm dist/md_spreadsheet_parser-*.whl

# Copy latest wheel
cp ../dist/md_spreadsheet_parser-<version>.whl dist/

# Rebuild
npm run build
```

### Metadata Becomes String

If `metadata` is returned as a JSON string instead of object:
1. Check that the constructor properly parses JSON fields
2. Verify the adapter layer uses correct `convert_*` functions
3. Use `assertMetadataIsObject` in tests to catch this early

### Fields Missing in TypeScript Wrapper

If new fields added to Python models are not accessible in TypeScript:

1. **Check WIT definition** (`wit/generated.wit`):
   - Verify the field is defined in the WIT record
   - Example: `sheet-type: option<string>`

2. **Check Python adapter** (`src/generated_adapter.py`):
   - Verify `convert_*` function includes the field
   - Example: `res.sheet_type = str(obj.sheet_type) if obj.sheet_type is not None else None`

3. **Check TypeScript constructor** (`src/index.ts`):
   - Verify the field assignment includes snake_case fallback
   - Example: `this.sheetType = data.sheetType ?? data.sheet_type;`

4. **Check the `.json` getter** (Critical!):
   - The `.json` getter in TypeScript classes **must explicitly list all fields**
   - This is the most common cause of missing fields in client applications
   
   ```typescript
   // ❌ WRONG: Missing sheetType and content
   get json(): any {
       return {
           name: this.name,
           tables: (this.tables || []).map(...),
           metadata: this.metadata ?? {},
       };
   }
   
   // ✅ CORRECT: All fields included
   get json(): any {
       return {
           name: this.name,
           tables: (this.tables || []).map(...),
           sheetType: this.sheetType,
           content: this.content,
           metadata: this.metadata ?? {},
       };
   }
   ```

5. **Fix in `generate_wit.py`**:
   - The `.json` getter is generated in `generate_wit.py` around line 843-870
   - Add new fields to the appropriate class's `.json` getter template

## Verification Checklist

Before committing NPM package changes:

- [ ] Python tests pass: `uv run pytest`
- [ ] Pyright passes: `uv run pyright`
- [ ] NPM build succeeds: `npm run build`
- [ ] NPM tests pass: `npm test`
- [ ] Generator tests pass: `uv run pytest packages/npm/scripts/tests/`
- [ ] API coverage verified: `uv run python scripts/verify_api_coverage.py`

## See Also

- [ARCHITECTURE.md](./ARCHITECTURE.md) - Technical internals
- [README.md](./README.md) - Usage documentation
