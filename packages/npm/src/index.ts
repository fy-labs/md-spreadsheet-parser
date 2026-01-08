import { cleanCell as _cleanCell, splitRowGfm as _splitRowGfm, parseRow as _parseRow, parseSeparatorRow as _parseSeparatorRow, isSeparatorRow as _isSeparatorRow, parseTable as _parseTable, parseSheet as _parseSheet, parseWorkbook as _parseWorkbook, scanTables as _scanTables, generateTableMarkdown as _generateTableMarkdown, generateSheetMarkdown as _generateSheetMarkdown, generateWorkbookMarkdown as _generateWorkbookMarkdown, parseTableFromFile as _parseTableFromFile, parseWorkbookFromFile as _parseWorkbookFromFile, scanTablesFromFile as _scanTablesFromFile, scanTablesIter as _scanTablesIter, tableToModels as _tableToModels, tableToMarkdown as _tableToMarkdown, tableUpdateCell as _tableUpdateCell, tableDeleteRow as _tableDeleteRow, tableDeleteColumn as _tableDeleteColumn, tableClearColumnData as _tableClearColumnData, tableInsertRow as _tableInsertRow, tableInsertColumn as _tableInsertColumn, sheetGetTable as _sheetGetTable, sheetToMarkdown as _sheetToMarkdown, workbookGetSheet as _workbookGetSheet, workbookToMarkdown as _workbookToMarkdown, workbookAddSheet as _workbookAddSheet, workbookDeleteSheet as _workbookDeleteSheet } from '../dist/parser.js';
import { clientSideToModels } from './client-adapters.js';

// Environment detection
// @ts-ignore - process may not be defined in browser
const isNode = typeof process !== 'undefined'
    && typeof process.versions !== 'undefined'
    && typeof process.versions.node !== 'undefined';

// Lazily loaded Node.js modules (only in Node.js environment)
let _pathModule: any = null;
let _nodeInitialized = false;

/**
 * Ensures Node.js environment is initialized for file system operations.
 * Throws an error in browser environments.
 */
async function ensureNodeEnvironment(): Promise<void> {
    if (!isNode) {
        throw new Error(
            'File system operations (parseTableFromFile, parseWorkbookFromFile, scanTablesFromFile) ' +
            'are not supported in browser environments. ' +
            'Use parseTable(), parseWorkbook(), or scanTables() with string content instead.'
        );
    }
    if (_nodeInitialized) return;

    // Dynamic imports for Node.js only
    const [pathModule, processModule, fsShim] = await Promise.all([
        import('node:path'),
        import('node:process'),
        import('@bytecodealliance/preview2-shim/filesystem')
    ]);

    _pathModule = pathModule.default || pathModule;
    const proc = processModule.default || processModule;
    const root = _pathModule.parse(proc.cwd()).root;
    // @ts-ignore - _addPreopen is an internal function
    (fsShim as any)._addPreopen('/', root);
    _nodeInitialized = true;
}

function resolveToVirtualPath(p: string): string {
    if (!_pathModule) {
        throw new Error('Node.js modules not initialized. Call ensureNodeEnvironment() first.');
    }
    return _pathModule.resolve(p);
}

export function cleanCell(cell: any, schema: any): any {
    const res = _cleanCell(cell, schema);
    return res;
}

export function splitRowGfm(line: any, separator: any): any {
    const res = _splitRowGfm(line, separator);
    return res;
}

export function parseRow(line: any, schema: any): any {
    const res = _parseRow(line, schema);
    return res;
}

export function parseSeparatorRow(row: any, schema: any): any {
    const res = _parseSeparatorRow(row, schema);
    return res;
}

export function isSeparatorRow(row: any, schema: any): any {
    const res = _isSeparatorRow(row, schema);
    return res;
}

export function parseTable(markdown: any, schema?: any): any {
    const res = _parseTable(markdown, schema);
    return new Table(res);
}

export function parseSheet(markdown: any, name: any, schema: any, startLineOffset?: any): any {
    const res = _parseSheet(markdown, name, schema, startLineOffset);
    return new Sheet(res);
}

export function parseWorkbook(markdown: any, schema?: any): any {
    const res = _parseWorkbook(markdown, schema);
    return new Workbook(res);
}

export function scanTables(markdown: any, schema?: any): any {
    const res = _scanTables(markdown, schema);
    return res.map((x: any) => new Table(x));
}

export function generateTableMarkdown(table: any, schema?: any): any {
    const res = _generateTableMarkdown(table, schema);
    return res;
}

export function generateSheetMarkdown(sheet: any, schema?: any): any {
    const res = _generateSheetMarkdown(sheet, schema);
    return res;
}

export function generateWorkbookMarkdown(workbook: any, schema: any): any {
    const res = _generateWorkbookMarkdown(workbook, schema);
    return res;
}

export async function parseTableFromFile(source: any, schema?: any): Promise<any> {
    await ensureNodeEnvironment();
    const source_resolved = resolveToVirtualPath(source);
    const res = _parseTableFromFile(source_resolved, schema);
    return new Table(res);
}

export async function parseWorkbookFromFile(source: any, schema?: any): Promise<any> {
    await ensureNodeEnvironment();
    const source_resolved = resolveToVirtualPath(source);
    const res = _parseWorkbookFromFile(source_resolved, schema);
    return new Workbook(res);
}

export async function scanTablesFromFile(source: any, schema?: any): Promise<any> {
    await ensureNodeEnvironment();
    const source_resolved = resolveToVirtualPath(source);
    const res = _scanTablesFromFile(source_resolved, schema);
    return res.map((x: any) => new Table(x));
}

export function scanTablesIter(source: any, schema?: any): any {
    const res = _scanTablesIter(source, schema);
    return res;
}


export class Table {
    headers: any | undefined;
    rows: any[] | undefined;
    alignments: any | undefined;
    name: any | undefined;
    description: any | undefined;
    metadata: any | undefined;
    startLine: number | undefined;
    endLine: number | undefined;

    constructor(data?: Partial<Table>) {
        if (data) {
            this.headers = data.headers;
            this.rows = data.rows;
            this.alignments = data.alignments;
            this.name = data.name;
            this.description = data.description;
            this.metadata = (typeof data.metadata === 'string') ? JSON.parse(data.metadata) : data.metadata;
            this.startLine = data.startLine;
            this.endLine = data.endLine;
        }
    }

    toDTO(): any {
        const dto = { ...this } as any;
        if (dto.metadata) dto.metadata = JSON.stringify(dto.metadata);
        return dto;
    }

    /**
     * Returns a JSON-compatible plain object representation.
     * Mirrors Python's .json property.
     */
    get json(): any {
        return {
            name: this.name,
            description: this.description,
            headers: this.headers,
            rows: this.rows,
            metadata: this.metadata ?? {},
            startLine: this.startLine,
            endLine: this.endLine,
            alignments: this.alignments,
        };
    }

    toModels(schemaCls: any, conversionSchema?: any): any {
        const dto = this.toDTO();
        const clientRes = clientSideToModels(this.headers, this.rows || [], schemaCls);
        if (clientRes) {
            return clientRes;
        }
        const res = _tableToModels(dto, schemaCls, conversionSchema);
        return res.map((x: string) => JSON.parse(x));
    }

    toMarkdown(schema?: any): any {
        const dto = this.toDTO();
        const res = _tableToMarkdown(dto, schema);
        return res;
    }

    updateCell(rowIdx: any, colIdx: any, value: any): any {
        const dto = this.toDTO();
        const res = _tableUpdateCell(dto, rowIdx, colIdx, value);
        Object.assign(this, res);
        return this;
    }

    deleteRow(rowIdx: any): any {
        const dto = this.toDTO();
        const res = _tableDeleteRow(dto, rowIdx);
        Object.assign(this, res);
        return this;
    }

    deleteColumn(colIdx: any): any {
        const dto = this.toDTO();
        const res = _tableDeleteColumn(dto, colIdx);
        Object.assign(this, res);
        return this;
    }

    clearColumnData(colIdx: any): any {
        const dto = this.toDTO();
        const res = _tableClearColumnData(dto, colIdx);
        Object.assign(this, res);
        return this;
    }

    insertRow(rowIdx: any): any {
        const dto = this.toDTO();
        const res = _tableInsertRow(dto, rowIdx);
        Object.assign(this, res);
        return this;
    }

    insertColumn(colIdx: any): any {
        const dto = this.toDTO();
        const res = _tableInsertColumn(dto, colIdx);
        Object.assign(this, res);
        return this;
    }
}

export class Sheet {
    name: string | undefined;
    tables: any[] | undefined;
    metadata: any | undefined;

    constructor(data?: Partial<Sheet>) {
        if (data) {
            this.name = data.name;
            this.tables = data.tables;
            this.metadata = (typeof data.metadata === 'string') ? JSON.parse(data.metadata) : data.metadata;
        }
    }

    toDTO(): any {
        const dto = { ...this } as any;
        if (dto.tables) dto.tables = dto.tables.map((x: any) => x.toDTO ? x.toDTO() : x);
        if (dto.metadata) dto.metadata = JSON.stringify(dto.metadata);
        return dto;
    }

    /**
     * Returns a JSON-compatible plain object representation.
     * Mirrors Python's .json property.
     */
    get json(): any {
        return {
            name: this.name,
            tables: (this.tables || []).map((t: any) => t.json ? t.json : t),
            metadata: this.metadata ?? {},
        };
    }

    getTable(name: any): any {
        const dto = this.toDTO();
        const res = _sheetGetTable(dto, name);
        return res ? new Table(res) : undefined;
    }

    toMarkdown(schema?: any): any {
        const dto = this.toDTO();
        const res = _sheetToMarkdown(dto, schema);
        return res;
    }
}

export class Workbook {
    sheets: any[] | undefined;
    metadata: any | undefined;

    constructor(data?: Partial<Workbook>) {
        if (data) {
            this.sheets = data.sheets;
            this.metadata = (typeof data.metadata === 'string') ? JSON.parse(data.metadata) : data.metadata;
        }
    }

    toDTO(): any {
        const dto = { ...this } as any;
        if (dto.sheets) dto.sheets = dto.sheets.map((x: any) => x.toDTO ? x.toDTO() : x);
        if (dto.metadata) dto.metadata = JSON.stringify(dto.metadata);
        return dto;
    }

    /**
     * Returns a JSON-compatible plain object representation.
     * Mirrors Python's .json property.
     */
    get json(): any {
        return {
            sheets: (this.sheets || []).map((s: any) => s.json ? s.json : s),
            metadata: this.metadata ?? {},
        };
    }

    getSheet(name: any): any {
        const dto = this.toDTO();
        const res = _workbookGetSheet(dto, name);
        return res ? new Sheet(res) : undefined;
    }

    toMarkdown(schema?: any): any {
        const dto = this.toDTO();
        const res = _workbookToMarkdown(dto, schema);
        return res;
    }

    addSheet(name: any): any {
        const dto = this.toDTO();
        const res = _workbookAddSheet(dto, name);
        Object.assign(this, res);
        return this;
    }

    deleteSheet(index: any): any {
        const dto = this.toDTO();
        const res = _workbookDeleteSheet(dto, index);
        Object.assign(this, res);
        return this;
    }
}

export class ParsingSchema {
    columnSeparator: string | undefined;
    headerSeparatorChar: string | undefined;
    requireOuterPipes: boolean | undefined;
    stripWhitespace: boolean | undefined;
    convertBrToNewline: boolean | undefined;

    constructor(data?: Partial<ParsingSchema>) {
        if (data) {
            this.columnSeparator = data.columnSeparator;
            this.headerSeparatorChar = data.headerSeparatorChar;
            this.requireOuterPipes = data.requireOuterPipes;
            this.stripWhitespace = data.stripWhitespace;
            this.convertBrToNewline = data.convertBrToNewline;
        }
    }

    toDTO(): any {
        const dto = { ...this } as any;
        return dto;
    }
}

export class MultiTableParsingSchema {
    columnSeparator: string | undefined;
    headerSeparatorChar: string | undefined;
    requireOuterPipes: boolean | undefined;
    stripWhitespace: boolean | undefined;
    convertBrToNewline: boolean | undefined;
    rootMarker: string | undefined;
    sheetHeaderLevel: number | undefined;
    tableHeaderLevel: number | undefined;
    captureDescription: boolean | undefined;

    constructor(data?: Partial<MultiTableParsingSchema>) {
        if (data) {
            this.columnSeparator = data.columnSeparator;
            this.headerSeparatorChar = data.headerSeparatorChar;
            this.requireOuterPipes = data.requireOuterPipes;
            this.stripWhitespace = data.stripWhitespace;
            this.convertBrToNewline = data.convertBrToNewline;
            this.rootMarker = data.rootMarker;
            this.sheetHeaderLevel = data.sheetHeaderLevel;
            this.tableHeaderLevel = data.tableHeaderLevel;
            this.captureDescription = data.captureDescription;
        }
    }

    toDTO(): any {
        const dto = { ...this } as any;
        return dto;
    }
}

export class ConversionSchema {
    booleanPairs: string | undefined;
    customConverters: string | undefined;
    fieldConverters: string | undefined;

    constructor(data?: Partial<ConversionSchema>) {
        if (data) {
            this.booleanPairs = data.booleanPairs;
            this.customConverters = (typeof data.customConverters === 'string') ? JSON.parse(data.customConverters) : data.customConverters;
            this.fieldConverters = (typeof data.fieldConverters === 'string') ? JSON.parse(data.fieldConverters) : data.fieldConverters;
        }
    }

    toDTO(): any {
        const dto = { ...this } as any;
        if (dto.customConverters) dto.customConverters = JSON.stringify(dto.customConverters);
        if (dto.fieldConverters) dto.fieldConverters = JSON.stringify(dto.fieldConverters);
        return dto;
    }
}

export class ExcelParsingSchema {
    headerRows: number | undefined;
    fillMergedHeaders: boolean | undefined;
    delimiter: string | undefined;
    headerSeparator: string | undefined;

    constructor(data?: Partial<ExcelParsingSchema>) {
        if (data) {
            this.headerRows = data.headerRows;
            this.fillMergedHeaders = data.fillMergedHeaders;
            this.delimiter = data.delimiter;
            this.headerSeparator = data.headerSeparator;
        }
    }

    toDTO(): any {
        const dto = { ...this } as any;
        return dto;
    }
}
