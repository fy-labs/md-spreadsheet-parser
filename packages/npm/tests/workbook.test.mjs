/**
 * Workbook Class Tests for md-spreadsheet-parser NPM Package
 * 
 * Mirrors Python tests/core/test_models.py Workbook section.
 * All tests verify metadata preservation as object type.
 */

import { parseWorkbook, Sheet, Table, Workbook } from '../dist/index.js';
import {
    assert,
    assertType,
    assertNotNull,
    assertInstanceOf,
    assertEqual,
    assertArrayEqual,
    assertMetadataIsObject
} from './helpers.mjs';

export function runWorkbookTests() {
    console.log("\n📦 Workbook Class Tests");
    console.log("-".repeat(40));

    const simpleWorkbookMd = `
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

    try {
        const raw = parseWorkbook(simpleWorkbookMd);
        const wb = new Workbook(raw);

        // Basic structure
        assertNotNull(wb, "Workbook");
        assert(Array.isArray(wb.sheets), "sheets should be array");
        assert(wb.sheets.length === 2, `Expected 2 sheets, got ${wb.sheets.length}`);

        // json getter
        const json = wb.json;
        assertNotNull(json, "Workbook.json");
        assertType(json, "object", "Workbook.json");
        assert(Array.isArray(json.sheets), "json.sheets should be array");

        // toMarkdown
        const md = wb.toMarkdown();
        assertType(md, "string", "Workbook.toMarkdown");
        assert(md.includes("# Tables"), "toMarkdown should contain root marker");
        assert(md.includes("## Sheet1"), "toMarkdown should contain sheet header");

        // getSheet
        const s1 = wb.getSheet("Sheet1");
        assertNotNull(s1, "getSheet('Sheet1')");
        assertInstanceOf(s1, Sheet, "getSheet result");

        // metadata is object
        assertMetadataIsObject(wb.metadata, "Workbook.metadata");

        // ============================================================
        // addSheet - Mirrors Python test_workbook_add_sheet (enhanced)
        // ============================================================

        const wbForAdd = new Workbook({
            sheets: [],
            metadata: { wb_key: "wb_value" }
        });

        const afterAdd = wbForAdd.addSheet("New Sheet");

        assert(afterAdd.sheets.length === 1, "sheets count after addSheet");
        assert(afterAdd.sheets[0].name === "New Sheet", "new sheet name");
        assert(afterAdd.sheets[0].tables.length === 1, "new sheet has default table");
        assertArrayEqual(afterAdd.sheets[0].tables[0].headers, ["A", "B", "C"], "default table headers");

        // Verify workbook metadata preserved
        assertMetadataIsObject(afterAdd.metadata, "metadata after addSheet");
        assertEqual(afterAdd.metadata, { wb_key: "wb_value" }, "metadata value after addSheet");

        // ============================================================
        // deleteSheet - Mirrors Python test_workbook_delete_sheet (enhanced)
        // ============================================================

        const wbForDelete = new Workbook({
            sheets: [
                { name: "S1", tables: [], metadata: { s1_key: "s1_value" } },
                { name: "S2", tables: [], metadata: { s2_key: "s2_value" } }
            ],
            metadata: { wb_key: "wb_value" }
        });

        const afterDelete = wbForDelete.deleteSheet(0);

        assert(afterDelete.sheets.length === 1, "sheets count after deleteSheet");
        assert(afterDelete.sheets[0].name === "S2", "remaining sheet name");

        // Verify metadata preserved
        assertMetadataIsObject(afterDelete.metadata, "metadata after deleteSheet");
        assertMetadataIsObject(afterDelete.sheets[0].metadata, "remaining sheet metadata");

        // ============================================================
        // moveSheet - Mirrors Python test_workbook_move_sheet
        // ============================================================

        const wbForMove = new Workbook({
            sheets: [
                {
                    name: "S1",
                    tables: [{
                        headers: ["H1"],
                        rows: [["data"]],
                        name: "T1",
                        metadata: { table_key: "table_value" },
                        alignments: ["left"]
                    }],
                    metadata: { s1_key: "s1_value" }
                },
                { name: "S2", tables: [], metadata: { s2_key: "s2_value" } },
                { name: "S3", tables: [], metadata: { s3_key: "s3_value" } }
            ],
            metadata: { wb_key: "wb_value" }
        });

        const afterMove = wbForMove.moveSheet(0, 2);

        // Verify order changed
        const sheetNames = afterMove.sheets.map(s => s.name);
        assertArrayEqual(sheetNames, ["S2", "S3", "S1"], "sheet order after moveSheet");

        // Verify workbook metadata preserved
        assertMetadataIsObject(afterMove.metadata, "metadata after moveSheet");
        assertEqual(afterMove.metadata, { wb_key: "wb_value" }, "metadata value after moveSheet");

        // Verify sheet metadata preserved after move
        assertMetadataIsObject(afterMove.sheets[2].metadata, "moved sheet metadata");
        assertEqual(afterMove.sheets[2].metadata, { s1_key: "s1_value" }, "moved sheet metadata value");

        // Verify nested table metadata preserved
        assertMetadataIsObject(afterMove.sheets[2].tables[0].metadata, "nested table metadata");
        assertEqual(afterMove.sheets[2].tables[0].metadata, { table_key: "table_value" }, "nested table metadata value");

        // ============================================================
        // replaceSheet - Mirrors Python test_workbook_replace_sheet
        // ============================================================

        const wbForReplace = new Workbook({
            sheets: [
                { name: "S1", tables: [], metadata: { s1_key: "s1_value" } },
                { name: "S2", tables: [], metadata: { s2_key: "s2_value" } }
            ],
            metadata: { wb_key: "wb_value" }
        });

        const newSheet = new Sheet({
            name: "Replaced",
            tables: [],
            metadata: { new_key: "new_value" }
        });

        const afterReplace = wbForReplace.replaceSheet(0, newSheet);

        // Verify replacement
        assert(afterReplace.sheets[0].name === "Replaced", "replaced sheet name");
        assert(afterReplace.sheets[1].name === "S2", "other sheet name");

        // Verify workbook metadata preserved
        assertMetadataIsObject(afterReplace.metadata, "metadata after replaceSheet");
        assertEqual(afterReplace.metadata, { wb_key: "wb_value" }, "metadata value after replaceSheet");

        // Verify new sheet metadata is correct
        assertMetadataIsObject(afterReplace.sheets[0].metadata, "new sheet metadata");
        assertEqual(afterReplace.sheets[0].metadata, { new_key: "new_value" }, "new sheet metadata value");

        // Verify untouched sheet metadata preserved
        assertEqual(afterReplace.sheets[1].metadata, { s2_key: "s2_value" }, "untouched sheet metadata");

        // ============================================================
        // renameSheet - Mirrors Python test_workbook_rename_sheet
        // ============================================================

        const wbForRename = new Workbook({
            sheets: [{
                name: "S1",
                tables: [{
                    headers: ["H1"],
                    rows: [["data"]],
                    name: "T1",
                    metadata: { table_key: "table_value" }
                }],
                metadata: { sheet_key: "sheet_value" }
            }],
            metadata: { wb_key: "wb_value" }
        });

        const afterRename = wbForRename.renameSheet(0, "NewName");

        // Verify name changed
        assert(afterRename.sheets[0].name === "NewName", "renamed sheet name");

        // Verify workbook metadata preserved
        assertMetadataIsObject(afterRename.metadata, "metadata after renameSheet");
        assertEqual(afterRename.metadata, { wb_key: "wb_value" }, "metadata value after renameSheet");

        // Verify sheet metadata preserved
        assertMetadataIsObject(afterRename.sheets[0].metadata, "sheet metadata after renameSheet");
        assertEqual(afterRename.sheets[0].metadata, { sheet_key: "sheet_value" }, "sheet metadata value");

        // Verify nested table preserved
        assert(afterRename.sheets[0].tables[0].name === "T1", "nested table name");
        assertEqual(afterRename.sheets[0].tables[0].metadata, { table_key: "table_value" }, "nested table metadata");

        // Test: rootContent
        const wbWithRootContent = parseWorkbook(`# Root Content WB

This is root content.

## Sheet1
`);
        assert(wbWithRootContent.rootContent === "This is root content.", "rootContent should be captured");
        assert(wbWithRootContent.json.rootContent === "This is root content.", "json.rootContent should be present");

        console.log("   ✅ Workbook tests verified");
    } catch (e) {
        console.error("   ❌ Workbook tests failed:", e);
    }
}
