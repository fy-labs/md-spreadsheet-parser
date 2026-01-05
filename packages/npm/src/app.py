import md_spreadsheet_parser.parsing
import md_spreadsheet_parser.generator
import md_spreadsheet_parser.loader
import dataclasses
import json
from typing import Any
from generated_adapter import *

class WitWorld:
    def clean_cell(self, cell: Any = None, schema: Any = None):
        kwargs = {}
        if cell is not None: kwargs['cell'] = cell
        if schema is not None: kwargs['schema'] = unwrap_parsing_schema(schema)
        return md_spreadsheet_parser.parsing.clean_cell(**kwargs)
    def split_row_gfm(self, line: Any = None, separator: Any = None):
        kwargs = {}
        if line is not None: kwargs['line'] = line
        if separator is not None: kwargs['separator'] = separator
        return md_spreadsheet_parser.parsing.split_row_gfm(**kwargs)
    def parse_row(self, line: Any = None, schema: Any = None):
        kwargs = {}
        if line is not None: kwargs['line'] = line
        if schema is not None: kwargs['schema'] = unwrap_parsing_schema(schema)
        return md_spreadsheet_parser.parsing.parse_row(**kwargs)
    def parse_separator_row(self, row: Any = None, schema: Any = None):
        kwargs = {}
        if row is not None: kwargs['row'] = row
        if schema is not None: kwargs['schema'] = unwrap_parsing_schema(schema)
        return [convert_alignment_type(x) for x in md_spreadsheet_parser.parsing.parse_separator_row(**kwargs)]
    def is_separator_row(self, row: Any = None, schema: Any = None):
        kwargs = {}
        if row is not None: kwargs['row'] = row
        if schema is not None: kwargs['schema'] = unwrap_parsing_schema(schema)
        return md_spreadsheet_parser.parsing.is_separator_row(**kwargs)
    def parse_table(self, markdown: Any = None, schema: Any = None):
        kwargs = {}
        if markdown is not None: kwargs['markdown'] = markdown
        if schema is not None: kwargs['schema'] = unwrap_parsing_schema(schema)
        return convert_table(md_spreadsheet_parser.parsing.parse_table(**kwargs))
    def parse_sheet(self, markdown: Any = None, name: Any = None, schema: Any = None, start_line_offset: Any = None):
        kwargs = {}
        if markdown is not None: kwargs['markdown'] = markdown
        if name is not None: kwargs['name'] = name
        if schema is not None: kwargs['schema'] = unwrap_multi_table_parsing_schema(schema)
        if start_line_offset is not None: kwargs['start_line_offset'] = start_line_offset
        return convert_sheet(md_spreadsheet_parser.parsing.parse_sheet(**kwargs))
    def parse_workbook(self, markdown: Any = None, schema: Any = None):
        kwargs = {}
        if markdown is not None: kwargs['markdown'] = markdown
        if schema is not None: kwargs['schema'] = unwrap_multi_table_parsing_schema(schema)
        return convert_workbook(md_spreadsheet_parser.parsing.parse_workbook(**kwargs))
    def scan_tables(self, markdown: Any = None, schema: Any = None):
        kwargs = {}
        if markdown is not None: kwargs['markdown'] = markdown
        if schema is not None: kwargs['schema'] = unwrap_multi_table_parsing_schema(schema)
        return [convert_table(x) for x in md_spreadsheet_parser.parsing.scan_tables(**kwargs)]
    def generate_table_markdown(self, table: Any = None, schema: Any = None):
        kwargs = {}
        if table is not None: kwargs['table'] = unwrap_table(table)
        if schema is not None: kwargs['schema'] = unwrap_parsing_schema(schema)
        return md_spreadsheet_parser.generator.generate_table_markdown(**kwargs)
    def generate_sheet_markdown(self, sheet: Any = None, schema: Any = None):
        kwargs = {}
        if sheet is not None: kwargs['sheet'] = unwrap_sheet(sheet)
        if schema is not None: kwargs['schema'] = unwrap_parsing_schema(schema)
        return md_spreadsheet_parser.generator.generate_sheet_markdown(**kwargs)
    def generate_workbook_markdown(self, workbook: Any = None, schema: Any = None):
        kwargs = {}
        if workbook is not None: kwargs['workbook'] = unwrap_workbook(workbook)
        if schema is not None: kwargs['schema'] = unwrap_multi_table_parsing_schema(schema)
        return md_spreadsheet_parser.generator.generate_workbook_markdown(**kwargs)
    def parse_table_from_file(self, source: Any = None, schema: Any = None):
        kwargs = {}
        if source is not None: kwargs['source'] = source
        if schema is not None: kwargs['schema'] = unwrap_parsing_schema(schema)
        return convert_table(md_spreadsheet_parser.loader.parse_table_from_file(**kwargs))
    def parse_workbook_from_file(self, source: Any = None, schema: Any = None):
        kwargs = {}
        if source is not None: kwargs['source'] = source
        if schema is not None: kwargs['schema'] = unwrap_multi_table_parsing_schema(schema)
        return convert_workbook(md_spreadsheet_parser.loader.parse_workbook_from_file(**kwargs))
    def scan_tables_from_file(self, source: Any = None, schema: Any = None):
        kwargs = {}
        if source is not None: kwargs['source'] = source
        if schema is not None: kwargs['schema'] = unwrap_multi_table_parsing_schema(schema)
        return [convert_table(x) for x in md_spreadsheet_parser.loader.scan_tables_from_file(**kwargs)]
    def scan_tables_iter(self, source: Any = None, schema: Any = None):
        kwargs = {}
        if source is not None: kwargs['source'] = source
        if schema is not None: kwargs['schema'] = unwrap_multi_table_parsing_schema(schema)
        return str(md_spreadsheet_parser.loader.scan_tables_iter(**kwargs))
    def table_to_models(self, self_obj: Any, schema_cls: Any = None, conversion_schema: Any = None):
        real_self = unwrap_table(self_obj)
        kwargs = {}
        if schema_cls is not None: kwargs['schema_cls'] = resolve_model_class(schema_cls)
        if conversion_schema is not None: kwargs['conversion_schema'] = unwrap_conversion_schema(conversion_schema)
        return [json.dumps(dataclasses.asdict(x)) for x in real_self.to_models(**kwargs)]
    def table_to_markdown(self, self_obj: Any, schema: Any = None):
        real_self = unwrap_table(self_obj)
        kwargs = {}
        if schema is not None: kwargs['schema'] = unwrap_parsing_schema(schema)
        return real_self.to_markdown(**kwargs)
    def table_update_cell(self, self_obj: Any, row_idx: Any = None, col_idx: Any = None, value: Any = None):
        real_self = unwrap_table(self_obj)
        kwargs = {}
        if row_idx is not None: kwargs['row_idx'] = row_idx
        if col_idx is not None: kwargs['col_idx'] = col_idx
        if value is not None: kwargs['value'] = value
        return convert_table(real_self.update_cell(**kwargs))
    def table_delete_row(self, self_obj: Any, row_idx: Any = None):
        real_self = unwrap_table(self_obj)
        kwargs = {}
        if row_idx is not None: kwargs['row_idx'] = row_idx
        return convert_table(real_self.delete_row(**kwargs))
    def table_delete_column(self, self_obj: Any, col_idx: Any = None):
        real_self = unwrap_table(self_obj)
        kwargs = {}
        if col_idx is not None: kwargs['col_idx'] = col_idx
        return convert_table(real_self.delete_column(**kwargs))
    def table_clear_column_data(self, self_obj: Any, col_idx: Any = None):
        real_self = unwrap_table(self_obj)
        kwargs = {}
        if col_idx is not None: kwargs['col_idx'] = col_idx
        return convert_table(real_self.clear_column_data(**kwargs))
    def table_insert_row(self, self_obj: Any, row_idx: Any = None):
        real_self = unwrap_table(self_obj)
        kwargs = {}
        if row_idx is not None: kwargs['row_idx'] = row_idx
        return convert_table(real_self.insert_row(**kwargs))
    def table_insert_column(self, self_obj: Any, col_idx: Any = None):
        real_self = unwrap_table(self_obj)
        kwargs = {}
        if col_idx is not None: kwargs['col_idx'] = col_idx
        return convert_table(real_self.insert_column(**kwargs))
    def sheet_get_table(self, self_obj: Any, name: Any = None):
        real_self = unwrap_sheet(self_obj)
        kwargs = {}
        if name is not None: kwargs['name'] = name
        return convert_table(real_self.get_table(**kwargs))
    def sheet_to_markdown(self, self_obj: Any, schema: Any = None):
        real_self = unwrap_sheet(self_obj)
        kwargs = {}
        if schema is not None: kwargs['schema'] = unwrap_parsing_schema(schema)
        return real_self.to_markdown(**kwargs)
    def workbook_get_sheet(self, self_obj: Any, name: Any = None):
        real_self = unwrap_workbook(self_obj)
        kwargs = {}
        if name is not None: kwargs['name'] = name
        return convert_sheet(real_self.get_sheet(**kwargs))
    def workbook_to_markdown(self, self_obj: Any, schema: Any = None):
        real_self = unwrap_workbook(self_obj)
        kwargs = {}
        if schema is not None: kwargs['schema'] = unwrap_multi_table_parsing_schema(schema)
        return real_self.to_markdown(**kwargs)
    def workbook_add_sheet(self, self_obj: Any, name: Any = None):
        real_self = unwrap_workbook(self_obj)
        kwargs = {}
        if name is not None: kwargs['name'] = name
        return convert_workbook(real_self.add_sheet(**kwargs))
    def workbook_delete_sheet(self, self_obj: Any, index: Any = None):
        real_self = unwrap_workbook(self_obj)
        kwargs = {}
        if index is not None: kwargs['index'] = index
        return convert_workbook(real_self.delete_sheet(**kwargs))
