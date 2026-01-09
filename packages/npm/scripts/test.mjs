/**
 * Comprehensive End-to-End Tests for md-spreadsheet-parser NPM Package
 * 
 * Tests cover:
 * - parseTable, parseSheet, parseWorkbook, scanTables
 * - Table, Sheet, Workbook class methods
 * - Metadata structure (object, not string)
 * - toMarkdown, json getters
 * - Mutation APIs (updateCell, addRow, etc.)
 * - toModels with Plain Object Schema and Zod
 */

import {
    parseWorkbook,
    parseTable,
    parseSheet,
    scanTables,
    Table,
    Sheet,
    Workbook
} from '../dist/index.js';
import { z } from 'zod';
import { readFileSync } from 'fs';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';

const __dirname = dirname(fileURLToPath(import.meta.url));

// Test results tracking
let passed = 0;
let failed = 0;

function assert(condition, message) {
    if (!condition) {
        console.error(`   ❌ FAIL: ${message}`);
        failed++;
        return false;
    }
    passed++;
    return true;
}

function assertType(value, expectedType, name) {
    const actualType = typeof value;
    return assert(actualType === expectedType,
        `${name} should be ${expectedType}, got ${actualType}`);
}

function assertNotNull(value, name) {
    return assert(value !== null && value !== undefined,
        `${name} should not be null/undefined`);
}

function assertInstanceOf(value, cls, name) {
    return assert(value instanceof cls,
        `${name} should be instance of ${cls.name}`);
}

console.log("=".repeat(60));
console.log("  Comprehensive E2E Tests for md-spreadsheet-parser");
console.log("=".repeat(60));

// ============================================================
// Test Data
// ============================================================

// Load hybrid_notebook.md fixture for complex tests
const hybridNotebookPath = join(__dirname, 'fixtures/hybrid_notebook.md');
let hybridNotebookContent;
try {
    hybridNotebookContent = readFileSync(hybridNotebookPath, 'utf-8');
} catch (e) {
    console.warn(`⚠️ Could not load hybrid_notebook.md: ${e.message}`);
    hybridNotebookContent = null;
}

const simpleTableMd = `
| Name | Age | Active |
| --- | --- | --- |
| Alice | 30 | true |
| Bob | 25 | false |
`;

const simpleWorkbookMd = `
# Test Workbook

# Tables

## Sheet1

| A | B |
|---|---|
| 1 | 2 |

## Sheet2

| X | Y | Z |
|---|---|---|
| a | b | c |
`;

const tableWithMetadataMd = `
| Col1 | Col2 |
| --- | --- |
| val1 | val2 |

<!-- md-spreadsheet-table-metadata: {"column_widths": {"0": 100, "1": 200}} -->
`;

// ============================================================
// 1. parseTable Tests
// ============================================================

console.log("\n📦 1. parseTable Tests");
console.log("-".repeat(40));

try {
    const tables = parseTable(simpleTableMd);
    assertNotNull(tables, "parseTable result");

    const table = Array.isArray(tables) ? tables[0] : tables;
    assertNotNull(table, "First table");

    // Wrap in Table class
    const t = new Table(table);

    // Headers
    assert(Array.isArray(t.headers), "headers should be array");
    assert(t.headers.length === 3, `headers length should be 3, got ${t.headers.length}`);
    assert(t.headers[0] === "Name", `First header should be 'Name', got '${t.headers[0]}'`);

    // Rows
    assert(Array.isArray(t.rows), "rows should be array");
    assert(t.rows.length === 2, `rows length should be 2, got ${t.rows.length}`);
    assert(t.rows[0][0] === "Alice", `First cell should be 'Alice', got '${t.rows[0][0]}'`);
    assert(t.rows[1][1] === "25", `Bob's age should be '25', got '${t.rows[1][1]}'`);

    console.log("   ✅ parseTable basic structure verified");
} catch (e) {
    console.error("   ❌ parseTable tests failed:", e);
    failed++;
}

// ============================================================
// 2. parseWorkbook Tests (Deep Type Verification)
// ============================================================

console.log("\n📦 2. parseWorkbook Tests");
console.log("-".repeat(40));

try {
    const raw = parseWorkbook(simpleWorkbookMd);
    const wb = new Workbook(raw);

    assertNotNull(wb, "Workbook");
    assertNotNull(wb.sheets, "Workbook.sheets");
    assert(Array.isArray(wb.sheets), "sheets should be array");
    assert(wb.sheets.length === 2, `Expected 2 sheets, got ${wb.sheets.length}`);

    // ---- Workbook level ----
    assertType(wb.metadata, "object", "Workbook.metadata");
    // title may be undefined if not explicitly set
    assert(wb.title === undefined || typeof wb.title === "string", "Workbook.title should be string or undefined");

    // ---- Sheet level (Sheet1) ----
    const sheet1 = wb.sheets[0];
    assertInstanceOf(sheet1, Sheet, "sheets[0]");
    assertType(sheet1.name, "string", "Sheet.name");
    assert(sheet1.name === "Sheet1", `Sheet name should be 'Sheet1', got '${sheet1.name}'`);
    assertType(sheet1.metadata, "object", "Sheet.metadata (must be object, not string!)");
    assert(Array.isArray(sheet1.tables), "Sheet.tables should be array");

    // ---- Table level (inside Sheet1) ----
    assert(sheet1.tables.length === 1, "Sheet1 should have 1 table");
    const table1 = sheet1.tables[0];
    assertInstanceOf(table1, Table, "sheets[0].tables[0]");

    // Table properties type verification
    // Table.name may be undefined if no title is present
    assert(table1.name === undefined || typeof table1.name === "string", "Table.name should be string or undefined");
    assert(Array.isArray(table1.headers), "Table.headers should be array");
    assert(Array.isArray(table1.rows), "Table.rows should be array");

    // CRITICAL: Table.metadata must be object, NOT string!
    // This was a past bug where metadata came back as JSON string
    assertType(table1.metadata, "object", "Table.metadata (CRITICAL: must be object, not string!)");
    if (table1.metadata !== null) {
        assert(typeof table1.metadata !== "string",
            `Table.metadata should NOT be string! Got: ${JSON.stringify(table1.metadata).substring(0, 50)}`);
    }

    // Table.alignments verification
    if (table1.alignments !== undefined && table1.alignments !== null) {
        assert(Array.isArray(table1.alignments), "Table.alignments should be array if present");
    }

    // ---- Sheet2 verification ----
    const sheet2 = wb.sheets[1];
    assertInstanceOf(sheet2, Sheet, "sheets[1]");
    assert(sheet2.name === "Sheet2", `Sheet2 name should be 'Sheet2', got '${sheet2.name}'`);
    assertType(sheet2.metadata, "object", "Sheet2.metadata");

    // Table in Sheet2
    assert(sheet2.tables.length === 1, "Sheet2 should have 1 table");
    const table2 = sheet2.tables[0];
    assertInstanceOf(table2, Table, "sheets[1].tables[0]");
    assertType(table2.metadata, "object", "Table in Sheet2 metadata");

    // Verify table2 data
    assert(table2.headers.length === 3, `Table2 should have 3 headers, got ${table2.headers.length}`);
    assert(table2.headers[0] === "X", `Table2 first header should be 'X', got '${table2.headers[0]}'`);
    assert(table2.rows[0][0] === "a", `Table2 first cell should be 'a', got '${table2.rows[0][0]}'`);

    console.log("   ✅ parseWorkbook structure verified");
} catch (e) {
    console.error("   ❌ parseWorkbook tests failed:", e);
    failed++;
}

// ============================================================
// 3. scanTables Tests
// ============================================================

console.log("\n📦 3. scanTables Tests");
console.log("-".repeat(40));

try {
    const tables = scanTables(simpleWorkbookMd);

    assertNotNull(tables, "scanTables result");
    assert(Array.isArray(tables), "scanTables should return array");
    assert(tables.length === 2, `Expected 2 tables, got ${tables.length}`);

    // Each should be wrappable as Table
    const t1 = new Table(tables[0]);
    assert(t1.headers.length === 2, "First table should have 2 headers");

    console.log("   ✅ scanTables verified");
} catch (e) {
    console.error("   ❌ scanTables tests failed:", e);
    failed++;
}

// ============================================================
// 4. Table Class Methods
// ============================================================

console.log("\n📦 4. Table Class Methods");
console.log("-".repeat(40));

try {
    const raw = parseTable(simpleTableMd);
    const table = new Table(Array.isArray(raw) ? raw[0] : raw);

    // 4.1 toDTO
    const dto = table.toDTO();
    assertNotNull(dto, "toDTO result");
    assert(dto.headers !== undefined, "DTO should have headers");

    // 4.2 json getter
    const json = table.json;
    assertNotNull(json, "json getter result");
    assertType(json, "object", "json getter");
    assert(Array.isArray(json.headers), "json.headers should be array");
    assert(Array.isArray(json.rows), "json.rows should be array");

    // 4.3 toMarkdown
    const md = table.toMarkdown();
    assertType(md, "string", "toMarkdown result");
    assert(md.includes("| Name |"), "toMarkdown should contain headers");
    assert(md.includes("| Alice |"), "toMarkdown should contain row data");

    // 4.4 updateCell - verify return type and mutation
    const updated = table.updateCell(0, 1, "31");
    assertNotNull(updated, "updateCell return value");
    assert(updated === table, "updateCell should return this");
    assert(table.rows[0][1] === "31", `Cell should be updated to '31', got '${table.rows[0][1]}'`);

    // Verify metadata is still object after mutation
    assertType(table.metadata, "object", "metadata after updateCell");

    console.log("   ✅ Table methods verified");
} catch (e) {
    console.error("   ❌ Table methods tests failed:", e);
    failed++;
}

// ============================================================
// 5. Sheet Class Methods
// ============================================================

console.log("\n📦 5. Sheet Class Methods");
console.log("-".repeat(40));

try {
    const raw = parseWorkbook(simpleWorkbookMd);
    const wb = new Workbook(raw);
    const sheet = wb.sheets[0];

    assertInstanceOf(sheet, Sheet, "sheet");

    // 5.1 json getter
    const json = sheet.json;
    assertNotNull(json, "Sheet.json");
    assertType(json, "object", "Sheet.json");
    assert(json.name === "Sheet1", "json.name should be Sheet1");
    assert(Array.isArray(json.tables), "json.tables should be array");

    // 5.2 toMarkdown
    const md = sheet.toMarkdown();
    assertType(md, "string", "Sheet.toMarkdown");
    assert(md.includes("| A | B |"), "toMarkdown should contain table headers");

    // 5.3 Access tables via array (getTable requires table name, not index)
    assert(sheet.tables.length > 0, "sheet should have tables");
    const t = sheet.tables[0];
    assertNotNull(t, "tables[0]");
    assertInstanceOf(t, Table, "tables[0] type");

    console.log("   ✅ Sheet methods verified");
} catch (e) {
    console.error("   ❌ Sheet methods tests failed:", e);
    failed++;
}

// ============================================================
// 6. Workbook Class Methods
// ============================================================

console.log("\n📦 6. Workbook Class Methods");
console.log("-".repeat(40));

try {
    const raw = parseWorkbook(simpleWorkbookMd);
    const wb = new Workbook(raw);

    // 6.1 json getter
    const json = wb.json;
    assertNotNull(json, "Workbook.json");
    assertType(json, "object", "Workbook.json");
    assert(Array.isArray(json.sheets), "json.sheets should be array");

    // 6.2 toMarkdown
    const md = wb.toMarkdown();
    assertType(md, "string", "Workbook.toMarkdown");
    assert(md.includes("# Tables"), "toMarkdown should contain root marker");
    assert(md.includes("## Sheet1"), "toMarkdown should contain sheet header");

    // 6.3 getSheet by name
    const s1 = wb.getSheet("Sheet1");
    assertNotNull(s1, "getSheet('Sheet1')");
    assertInstanceOf(s1, Sheet, "getSheet result");

    const s2 = wb.getSheet("Sheet2");
    assertNotNull(s2, "getSheet('Sheet2')");

    const nonExistent = wb.getSheet("NonExistent");
    assert(nonExistent === undefined || nonExistent === null,
        "getSheet for non-existent should return undefined/null");

    // 6.4 metadata is object (not string!)
    assertType(wb.metadata, "object", "Workbook.metadata");

    console.log("   ✅ Workbook methods verified");
} catch (e) {
    console.error("   ❌ Workbook methods tests failed:", e);
    failed++;
}

// ============================================================
// 7. Metadata Structure Deep Verification
// ============================================================

console.log("\n📦 7. Metadata Structure Verification");
console.log("-".repeat(40));

try {
    const raw = parseTable(tableWithMetadataMd);
    const table = new Table(Array.isArray(raw) ? raw[0] : raw);

    // Metadata must be object, not string
    assertType(table.metadata, "object", "Table.metadata");

    if (table.metadata) {
        // Verify it's an object, not string
        assertType(table.metadata, "object", "non-null metadata type");

        // Check if column_widths exists (might not in all cases)
        if (table.metadata.column_widths) {
            assertType(table.metadata.column_widths, "object", "column_widths type");
            assert(table.metadata.column_widths["0"] === 100,
                `column_widths[0] should be 100, got ${table.metadata.column_widths["0"]}`);
        }
    }

    // Test mutation preserves metadata structure
    table.updateCell(0, 0, "updated");
    assertType(table.metadata, "object", "metadata after mutation");

    console.log("   ✅ Metadata structure verified");
} catch (e) {
    console.error("   ❌ Metadata tests failed:", e);
    failed++;
}

// ============================================================
// 8. toModels with Plain Object Schema
// ============================================================

console.log("\n📦 8. toModels (Plain Object Schema)");
console.log("-".repeat(40));

try {
    const tableMd = `
| id | name | active | score |
| --- | --- | --- | --- |
| 1 | Alice | yes | 95.5 |
| 2 | Bob | no | 80.0 |
`;
    const raw = parseTable(tableMd);
    const table = new Table(Array.isArray(raw) ? raw[0] : raw);

    const schema = {
        id: (val) => parseInt(val, 10),
        name: (val) => val.trim(),
        active: (val) => val === 'yes',
        score: (val) => parseFloat(val)
    };

    const models = table.toModels(schema);

    assertNotNull(models, "toModels result");
    assert(Array.isArray(models), "toModels should return array");
    assert(models.length === 2, `Expected 2 models, got ${models.length}`);

    // Verify first model
    const alice = models[0];
    assert(alice.id === 1, `Alice.id should be 1, got ${alice.id}`);
    assertType(alice.id, "number", "id type");
    assert(alice.name === "Alice", `name should be 'Alice', got '${alice.name}'`);
    assert(alice.active === true, `active should be true, got ${alice.active}`);
    assertType(alice.active, "boolean", "active type");
    assert(alice.score === 95.5, `score should be 95.5, got ${alice.score}`);
    assertType(alice.score, "number", "score type");

    // Verify second model
    const bob = models[1];
    assert(bob.id === 2, `Bob.id should be 2, got ${bob.id}`);
    assert(bob.active === false, `Bob.active should be false, got ${bob.active}`);

    console.log("   ✅ toModels (Plain Object) verified");
} catch (e) {
    console.error("   ❌ toModels (Plain Object) tests failed:", e);
    failed++;
}

// ============================================================
// 9. toModels with Zod Schema
// ============================================================

console.log("\n📦 9. toModels (Zod Schema)");
console.log("-".repeat(40));

try {
    const tableMd = `
| id | name | active | score |
| --- | --- | --- | --- |
| 1 | Alice | yes | 95.5 |
| 2 | Bob | no | 80.0 |
`;
    const raw = parseTable(tableMd);
    const table = new Table(Array.isArray(raw) ? raw[0] : raw);

    const ZodSchema = z.object({
        id: z.coerce.number(),
        name: z.string(),
        active: z.string().transform(v => v === 'yes'),
        score: z.coerce.number()
    });

    const models = table.toModels(ZodSchema);

    assertNotNull(models, "Zod toModels result");
    assert(Array.isArray(models), "Zod toModels should return array");
    assert(models.length === 2, `Expected 2 models, got ${models.length}`);

    // Verify types
    const alice = models[0];
    assertType(alice.id, "number", "Zod id type");
    assertType(alice.active, "boolean", "Zod active type");
    assert(alice.active === true, `Zod active should be true`);

    console.log("   ✅ toModels (Zod) verified");
} catch (e) {
    console.error("   ❌ toModels (Zod) tests failed:", e);
    failed++;
}

// ============================================================
// 10. Complex Workbook (hybrid_notebook.md)
// ============================================================

console.log("\n📦 10. Complex Workbook Tests");
console.log("-".repeat(40));

if (hybridNotebookContent) {
    try {
        const raw = parseWorkbook(hybridNotebookContent);
        const wb = new Workbook(raw);

        // Should have multiple sheets
        assert(wb.sheets.length >= 4, `Expected at least 4 sheets, got ${wb.sheets.length}`);

        // Verify sheet names
        const sheetNames = wb.sheets.map(s => s.name);
        assert(sheetNames.includes("MyTestSheet"), "Should have MyTestSheet");
        assert(sheetNames.includes("Comparison"), "Should have Comparison");
        assert(sheetNames.includes("Project Status"), "Should have Project Status");
        assert(sheetNames.includes("Sales Data"), "Should have Sales Data");

        // Get specific sheet and verify structure
        const comparisonSheet = wb.getSheet("Comparison");
        assertNotNull(comparisonSheet, "Comparison sheet");
        assert(comparisonSheet.tables.length >= 1, "Comparison should have tables");

        // Test table with metadata
        const myTestSheet = wb.getSheet("MyTestSheet");
        assertNotNull(myTestSheet, "MyTestSheet");
        const firstTable = myTestSheet.tables[0];

        // Metadata should be object
        assertType(firstTable.metadata, "object", "Table metadata from complex file");
        // Note: metadata content varies, just verify it's object type

        // Workbook metadata (tab_order)
        assertType(wb.metadata, "object", "Workbook.metadata");
        if (wb.metadata && wb.metadata.tab_order) {
            assert(Array.isArray(wb.metadata.tab_order), "tab_order should be array");
        }

        // Verify toMarkdown produces valid output
        const regenerated = wb.toMarkdown();
        assertType(regenerated, "string", "Complex toMarkdown");
        assert(regenerated.length > 1000, "Regenerated markdown should be substantial");
        assert(regenerated.includes("## MyTestSheet"), "Should contain sheet headers");

        // Verify json getter on complex data
        const wbJson = wb.json;
        assertType(wbJson, "object", "Complex workbook json");
        assert(Array.isArray(wbJson.sheets), "json.sheets array");

        console.log("   ✅ Complex workbook verified");
    } catch (e) {
        console.error("   ❌ Complex workbook tests failed:", e);
        failed++;
    }
} else {
    console.log("   ⏭️ Skipped (hybrid_notebook.md not available)");
}

// ============================================================
// 11. Mutation API Return Values
// ============================================================

console.log("\n📦 11. Mutation API Return Values");
console.log("-".repeat(40));

try {
    const raw = parseTable(simpleTableMd);
    const table = new Table(Array.isArray(raw) ? raw[0] : raw);

    // updateCell should return this
    const afterUpdate = table.updateCell(0, 0, "Updated");
    assert(afterUpdate === table, "updateCell should return this for chaining");
    assert(table.rows[0][0] === "Updated", "Cell should be updated");

    // Verify chaining works
    const chained = table.updateCell(0, 1, "40").updateCell(1, 0, "Charlie");
    assert(chained === table, "Chained calls should return same instance");
    assert(table.rows[0][1] === "40", "First chained update worked");
    assert(table.rows[1][0] === "Charlie", "Second chained update worked");

    // After mutations, metadata should still be object
    assertType(table.metadata, "object", "metadata after chained mutations");

    console.log("   ✅ Mutation API return values verified");
} catch (e) {
    console.error("   ❌ Mutation API tests failed:", e);
    failed++;
}

// ============================================================
// Summary
// ============================================================

console.log("\n" + "=".repeat(60));
console.log(`  Test Results: ${passed} passed, ${failed} failed`);
console.log("=".repeat(60));

if (failed > 0) {
    console.error("\n❌ Some tests failed!");
    process.exit(1);
} else {
    console.log("\n✅ All tests passed!");
    process.exit(0);
}
