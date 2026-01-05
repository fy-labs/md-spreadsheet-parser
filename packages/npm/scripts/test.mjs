
import { parseWorkbook, parseTable, Table, Workbook } from '../dist/index.js';
import { z } from 'zod';

console.log("--- Starting Tests ---");

const markdown = `
# Test Workbook

# Tables

## Sheet1

| A | B |
|---|---|
| 1 | 2 |
`;

try {
    const rawWorkbook = parseWorkbook(markdown, undefined);
    const workbook = new Workbook(rawWorkbook);
    //console.log('Parsed Workbook:', JSON.stringify(workbook, null, 2));

    if (!workbook || !workbook.sheets) {
        throw new Error("Invalid workbook structure");
    }

    if (workbook.sheets.length !== 1) {
        throw new Error(`Expected 1 sheet, got ${workbook.sheets.length}`);
    }

    const sheet = workbook.sheets[0];
    if (sheet.tables.length !== 1) {
        throw new Error(`Expected 1 table, got ${sheet.tables.length}`);
    }

    const table = sheet.tables[0];
    console.log(`Sheet: ${sheet.name}, Table Rows: ${table.rows.length}`);

    if (table.rows.length !== 1) {
        throw new Error(`Expected 1 row, got ${table.rows.length}`);
    }

    // Verify Generator

    const schema = {
        columnSeparator: "|",
        headerSeparatorChar: "-",
        requireOuterPipes: true,
        stripWhitespace: true,
        convertBrToNewline: true,
        rootMarker: "",
        sheetHeaderLevel: 2,
        tableHeaderLevel: undefined, // Option<s32> can be undefined
        captureDescription: false
    };

    const generated = workbook.toMarkdown(schema);

    if (!generated.includes('| A | B |')) {
        throw new Error("Generated markdown missing headers");
    }
    console.log('✅ Generator Test Passed');

    // Verify toModels (Adapter) using ParsingSchema
    // Create a table that matches ParsingSchema fields
    const schemaMarkdown = `
| column_separator | header_separator_char | require_outer_pipes | strip_whitespace | convert_br_to_newline |
| ---------------- | --------------------- | ------------------- | ---------------- | --------------------- |
| ,                | =                     | true                | true             | true                  |
`;
    // We can use parseTable directly (but it is function, not method on sheet)
    const schemaTable = parseTable(schemaMarkdown, undefined);

    // Call toModels with "ParsingSchema"
    // Note: We use the flat function tableToModels because the Table class wrapper isn't automatically attached to objects returned by parseTable
    // The schemaTable returned by parseTable is a `WitTable[]` (list of tables).
    // The flat function expects a single WitTable possibly? No, `tableToModels` adapter takes `WitTable`.
    // Wait, parseTable returns array. We should pass the first element.
    const tableInstance = Array.isArray(schemaTable) ? schemaTable[0] : schemaTable;

    const jsonList = new Table(tableInstance).toModels("ParsingSchema", undefined);
    console.log("toModels result:", jsonList);

    if (jsonList.length !== 1) {
        throw new Error("Expected 1 model");
    }
    const model = jsonList[0];

    // field names in ParsingSchema are snake_case in Python
    // normalized header "column_separator" -> matches field "column_separator"
    if (model.column_separator !== ",") {
        throw new Error(`Expected comma, got ${model.column_separator}`);
    }
    console.log('✅ toModels Test Passed');


    // Verify toModels (Adapter) using Zod
    console.log("--- Zod Support Test ---");

    const schemaMarkdownForZod = `
| column_separator | header_separator_char | require_outer_pipes | strip_whitespace | convert_br_to_newline |
| ---------------- | --------------------- | ------------------- | ---------------- | --------------------- |
| ,                | =                     | true                | true             | true                  |
`;

    // parseTable returns WitTable[]
    const rawTables = parseTable(schemaMarkdownForZod);

    if (!rawTables) {
        throw new Error("parseTable returned falsy value");
    }

    let tableData = Array.isArray(rawTables) ? rawTables[0] : rawTables;
    // If it's not an array, maybe it's the table itself?

    // We wrap the raw data in the Table class to use the OO API
    const wrapper = new Table(tableData);

    const ZodSchema = z.object({
        column_separator: z.string(),
        require_outer_pipes: z.coerce.boolean(),
        // Note: input is string "true", z.boolean() might fail if not coerced?
        // z.coerce.boolean() handles "true" -> true.
        convert_br_to_newline: z.coerce.boolean()
    });

    const zodModels = wrapper.toModels(ZodSchema);
    console.log("Zod toModels result:", zodModels);

    if (zodModels[0].require_outer_pipes !== true) {
        throw new Error("Zod coerce boolean failed");
    }
    console.log("✅ Zod Integration Test Passed");

    console.log(`✅ Test Passed`);

} catch (e) {
    console.error("❌ Test Failed:", e);
    process.exit(1);
}
