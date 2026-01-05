import { cleanCell as _cleanCell, splitRowGfm as _splitRowGfm, parseRow as _parseRow, parseSeparatorRow as _parseSeparatorRow, isSeparatorRow as _isSeparatorRow, parseTable as _parseTable, parseSheet as _parseSheet, parseWorkbook as _parseWorkbook, scanTables as _scanTables, generateTableMarkdown as _generateTableMarkdown, generateSheetMarkdown as _generateSheetMarkdown, generateWorkbookMarkdown as _generateWorkbookMarkdown, parseTableFromFile as _parseTableFromFile, parseWorkbookFromFile as _parseWorkbookFromFile, scanTablesFromFile as _scanTablesFromFile, scanTablesIter as _scanTablesIter, tableToModels as _tableToModels, tableToMarkdown as _tableToMarkdown, tableUpdateCell as _tableUpdateCell, tableDeleteRow as _tableDeleteRow, tableDeleteColumn as _tableDeleteColumn, tableClearColumnData as _tableClearColumnData, tableInsertRow as _tableInsertRow, tableInsertColumn as _tableInsertColumn, sheetGetTable as _sheetGetTable, sheetToMarkdown as _sheetToMarkdown, workbookGetSheet as _workbookGetSheet, workbookToMarkdown as _workbookToMarkdown, workbookAddSheet as _workbookAddSheet, workbookDeleteSheet as _workbookDeleteSheet } from '../dist/parser.js';
import { clientSideToModels } from './client-adapters.js';

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

export function parseTableFromFile(source: any, schema?: any): any {
    const res = _parseTableFromFile(source, schema);
    return new Table(res);
}

export function parseWorkbookFromFile(source: any, schema?: any): any {
    const res = _parseWorkbookFromFile(source, schema);
    return new Workbook(res);
}

export function scanTablesFromFile(source: any, schema?: any): any {
    const res = _scanTablesFromFile(source, schema);
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

    toModels(schemaCls: any, conversionSchema?: any): any {
        const dto = { ...this } as any;
        if (dto.metadata) dto.metadata = JSON.stringify(dto.metadata);
        const clientRes = clientSideToModels(this.headers, this.rows || [], schemaCls);
        if (clientRes) {
            return clientRes;
        }
        const res = _tableToModels(dto, schemaCls, conversionSchema);
        return res.map((x: string) => JSON.parse(x));
    }

    toMarkdown(schema?: any): any {
        const dto = { ...this } as any;
        if (dto.metadata) dto.metadata = JSON.stringify(dto.metadata);
        const res = _tableToMarkdown(dto, schema);
        return res;
    }

    updateCell(rowIdx: any, colIdx: any, value: any): any {
        const dto = { ...this } as any;
        if (dto.metadata) dto.metadata = JSON.stringify(dto.metadata);
        const res = _tableUpdateCell(dto, rowIdx, colIdx, value);
        Object.assign(this, res);
        return this;
    }

    deleteRow(rowIdx: any): any {
        const dto = { ...this } as any;
        if (dto.metadata) dto.metadata = JSON.stringify(dto.metadata);
        const res = _tableDeleteRow(dto, rowIdx);
        Object.assign(this, res);
        return this;
    }

    deleteColumn(colIdx: any): any {
        const dto = { ...this } as any;
        if (dto.metadata) dto.metadata = JSON.stringify(dto.metadata);
        const res = _tableDeleteColumn(dto, colIdx);
        Object.assign(this, res);
        return this;
    }

    clearColumnData(colIdx: any): any {
        const dto = { ...this } as any;
        if (dto.metadata) dto.metadata = JSON.stringify(dto.metadata);
        const res = _tableClearColumnData(dto, colIdx);
        Object.assign(this, res);
        return this;
    }

    insertRow(rowIdx: any): any {
        const dto = { ...this } as any;
        if (dto.metadata) dto.metadata = JSON.stringify(dto.metadata);
        const res = _tableInsertRow(dto, rowIdx);
        Object.assign(this, res);
        return this;
    }

    insertColumn(colIdx: any): any {
        const dto = { ...this } as any;
        if (dto.metadata) dto.metadata = JSON.stringify(dto.metadata);
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

    getTable(name: any): any {
        const dto = { ...this } as any;
        if (dto.metadata) dto.metadata = JSON.stringify(dto.metadata);
        const res = _sheetGetTable(dto, name);
        return res;
    }

    toMarkdown(schema?: any): any {
        const dto = { ...this } as any;
        if (dto.metadata) dto.metadata = JSON.stringify(dto.metadata);
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

    getSheet(name: any): any {
        const dto = { ...this } as any;
        if (dto.metadata) dto.metadata = JSON.stringify(dto.metadata);
        const res = _workbookGetSheet(dto, name);
        return res;
    }

    toMarkdown(schema: any): any {
        const dto = { ...this } as any;
        if (dto.metadata) dto.metadata = JSON.stringify(dto.metadata);
        const res = _workbookToMarkdown(dto, schema);
        return res;
    }

    addSheet(name: any): any {
        const dto = { ...this } as any;
        if (dto.metadata) dto.metadata = JSON.stringify(dto.metadata);
        const res = _workbookAddSheet(dto, name);
        Object.assign(this, res);
        return this;
    }

    deleteSheet(index: any): any {
        const dto = { ...this } as any;
        if (dto.metadata) dto.metadata = JSON.stringify(dto.metadata);
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
}
