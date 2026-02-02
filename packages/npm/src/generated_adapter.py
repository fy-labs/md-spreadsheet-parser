import json
from dataclasses import dataclass, asdict
from typing import Any
import md_spreadsheet_parser.models as models
import md_spreadsheet_parser.schemas as schemas

def resolve_model_class(name: str) -> Any:
    cls = None
    if hasattr(models, name):
        cls = getattr(models, name)
    elif hasattr(schemas, name):
        cls = getattr(schemas, name)
    if cls:
        return cls
    raise ValueError(f'Unknown model/schema class: {name}')

def convert_alignment_type(val: str) -> str:
    # Return string directly as WIT type is string
    return val

@dataclass
class WitTable:
    headers: Any = None
    rows: Any = None
    alignments: Any = None
    name: Any = None
    description: Any = None
    metadata: Any = None
    start_line: Any = None
    end_line: Any = None

def convert_table(obj: Any) -> WitTable:
    if obj is None: return None
    res = WitTable()
    res.headers = obj.headers
    res.rows = obj.rows
    res.alignments = [convert_alignment_type(x) for x in obj.alignments] if obj.alignments is not None else None
    res.name = obj.name
    res.description = obj.description
    res.metadata = json.dumps(obj.metadata or {}) if obj.metadata is not None else None
    res.start_line = obj.start_line
    res.end_line = obj.end_line
    return res

def unwrap_table(obj: Any) -> Any:
    if obj is None: return None
    kwargs = {}
    if obj.headers is not None:
        kwargs['headers'] = obj.headers
    if obj.rows is not None:
        kwargs['rows'] = obj.rows
    if obj.alignments is not None:
        kwargs['alignments'] = obj.alignments
    if obj.name is not None:
        kwargs['name'] = obj.name
    if obj.description is not None:
        kwargs['description'] = obj.description
    if obj.metadata is not None:
        kwargs['metadata'] = json.loads(obj.metadata)
    if obj.start_line is not None:
        kwargs['start_line'] = obj.start_line
    if obj.end_line is not None:
        kwargs['end_line'] = obj.end_line
    return models.Table(**kwargs)

@dataclass
class WitSheet:
    name: Any = None
    tables: Any = None
    sheet_type: Any = None
    content: Any = None
    metadata: Any = None

def convert_sheet(obj: Any) -> WitSheet:
    if obj is None: return None
    res = WitSheet()
    res.name = obj.name
    res.tables = [convert_table(x) for x in obj.tables]
    res.sheet_type = str(obj.sheet_type) if obj.sheet_type is not None else None
    res.content = obj.content
    res.metadata = json.dumps(obj.metadata or {}) if obj.metadata is not None else None
    return res

def unwrap_sheet(obj: Any) -> Any:
    if obj is None: return None
    kwargs = {}
    if obj.name is not None:
        kwargs['name'] = obj.name
    if obj.tables is not None:
        kwargs['tables'] = [unwrap_table(x) for x in obj.tables]
    if obj.sheet_type is not None:
        kwargs['sheet_type'] = obj.sheet_type
    if obj.content is not None:
        kwargs['content'] = obj.content
    if obj.metadata is not None:
        kwargs['metadata'] = json.loads(obj.metadata)
    return models.Sheet(**kwargs)

@dataclass
class WitWorkbook:
    sheets: Any = None
    name: Any = None
    start_line: Any = None
    end_line: Any = None
    metadata: Any = None
    root_content: Any = None

def convert_workbook(obj: Any) -> WitWorkbook:
    if obj is None: return None
    res = WitWorkbook()
    res.sheets = [convert_sheet(x) for x in obj.sheets]
    res.name = obj.name
    res.start_line = obj.start_line
    res.end_line = obj.end_line
    res.metadata = json.dumps(obj.metadata or {}) if obj.metadata is not None else None
    res.root_content = obj.root_content
    return res

def unwrap_workbook(obj: Any) -> Any:
    if obj is None: return None
    kwargs = {}
    if obj.sheets is not None:
        kwargs['sheets'] = [unwrap_sheet(x) for x in obj.sheets]
    if obj.name is not None:
        kwargs['name'] = obj.name
    if obj.start_line is not None:
        kwargs['start_line'] = obj.start_line
    if obj.end_line is not None:
        kwargs['end_line'] = obj.end_line
    if obj.metadata is not None:
        kwargs['metadata'] = json.loads(obj.metadata)
    if obj.root_content is not None:
        kwargs['root_content'] = obj.root_content
    return models.Workbook(**kwargs)

@dataclass
class WitParsingSchema:
    column_separator: Any = None
    header_separator_char: Any = None
    require_outer_pipes: Any = None
    strip_whitespace: Any = None
    convert_br_to_newline: Any = None

def convert_parsing_schema(obj: Any) -> WitParsingSchema:
    if obj is None: return None
    res = WitParsingSchema()
    res.column_separator = obj.column_separator
    res.header_separator_char = obj.header_separator_char
    res.require_outer_pipes = obj.require_outer_pipes
    res.strip_whitespace = obj.strip_whitespace
    res.convert_br_to_newline = obj.convert_br_to_newline
    return res

def unwrap_parsing_schema(obj: Any) -> Any:
    if obj is None: return None
    kwargs = {}
    if obj.column_separator is not None:
        kwargs['column_separator'] = obj.column_separator
    if obj.header_separator_char is not None:
        kwargs['header_separator_char'] = obj.header_separator_char
    if obj.require_outer_pipes is not None:
        kwargs['require_outer_pipes'] = obj.require_outer_pipes
    if obj.strip_whitespace is not None:
        kwargs['strip_whitespace'] = obj.strip_whitespace
    if obj.convert_br_to_newline is not None:
        kwargs['convert_br_to_newline'] = obj.convert_br_to_newline
    return schemas.ParsingSchema(**kwargs)

@dataclass
class WitMultiTableParsingSchema:
    column_separator: Any = None
    header_separator_char: Any = None
    require_outer_pipes: Any = None
    strip_whitespace: Any = None
    convert_br_to_newline: Any = None
    root_marker: Any = None
    sheet_header_level: Any = None
    table_header_level: Any = None
    capture_description: Any = None

def convert_multi_table_parsing_schema(obj: Any) -> WitMultiTableParsingSchema:
    if obj is None: return None
    res = WitMultiTableParsingSchema()
    res.column_separator = obj.column_separator
    res.header_separator_char = obj.header_separator_char
    res.require_outer_pipes = obj.require_outer_pipes
    res.strip_whitespace = obj.strip_whitespace
    res.convert_br_to_newline = obj.convert_br_to_newline
    res.root_marker = obj.root_marker
    res.sheet_header_level = obj.sheet_header_level
    res.table_header_level = obj.table_header_level
    res.capture_description = obj.capture_description
    return res

def unwrap_multi_table_parsing_schema(obj: Any) -> Any:
    if obj is None: return None
    kwargs = {}
    if obj.column_separator is not None:
        kwargs['column_separator'] = obj.column_separator
    if obj.header_separator_char is not None:
        kwargs['header_separator_char'] = obj.header_separator_char
    if obj.require_outer_pipes is not None:
        kwargs['require_outer_pipes'] = obj.require_outer_pipes
    if obj.strip_whitespace is not None:
        kwargs['strip_whitespace'] = obj.strip_whitespace
    if obj.convert_br_to_newline is not None:
        kwargs['convert_br_to_newline'] = obj.convert_br_to_newline
    if obj.root_marker is not None:
        kwargs['root_marker'] = obj.root_marker
    if obj.sheet_header_level is not None:
        kwargs['sheet_header_level'] = obj.sheet_header_level
    if obj.table_header_level is not None:
        kwargs['table_header_level'] = obj.table_header_level
    if obj.capture_description is not None:
        kwargs['capture_description'] = obj.capture_description
    return schemas.MultiTableParsingSchema(**kwargs)

@dataclass
class WitConversionSchema:
    boolean_pairs: Any = None
    custom_converters: Any = None
    field_converters: Any = None

def convert_conversion_schema(obj: Any) -> WitConversionSchema:
    if obj is None: return None
    res = WitConversionSchema()
    res.boolean_pairs = str(obj.boolean_pairs) if obj.boolean_pairs is not None else None
    res.custom_converters = json.dumps(obj.custom_converters or {}) if obj.custom_converters is not None else None
    res.field_converters = json.dumps(obj.field_converters or {}) if obj.field_converters is not None else None
    return res

def unwrap_conversion_schema(obj: Any) -> Any:
    if obj is None: return None
    kwargs = {}
    if obj.boolean_pairs is not None:
        kwargs['boolean_pairs'] = obj.boolean_pairs
    if obj.custom_converters is not None:
        kwargs['custom_converters'] = json.loads(obj.custom_converters)
    if obj.field_converters is not None:
        kwargs['field_converters'] = json.loads(obj.field_converters)
    return schemas.ConversionSchema(**kwargs)

@dataclass
class WitExcelParsingSchema:
    header_rows: Any = None
    fill_merged_headers: Any = None
    delimiter: Any = None
    header_separator: Any = None

def convert_excel_parsing_schema(obj: Any) -> WitExcelParsingSchema:
    if obj is None: return None
    res = WitExcelParsingSchema()
    res.header_rows = obj.header_rows
    res.fill_merged_headers = obj.fill_merged_headers
    res.delimiter = obj.delimiter
    res.header_separator = obj.header_separator
    return res

def unwrap_excel_parsing_schema(obj: Any) -> Any:
    if obj is None: return None
    kwargs = {}
    if obj.header_rows is not None:
        kwargs['header_rows'] = obj.header_rows
    if obj.fill_merged_headers is not None:
        kwargs['fill_merged_headers'] = obj.fill_merged_headers
    if obj.delimiter is not None:
        kwargs['delimiter'] = obj.delimiter
    if obj.header_separator is not None:
        kwargs['header_separator'] = obj.header_separator
    return schemas.ExcelParsingSchema(**kwargs)

