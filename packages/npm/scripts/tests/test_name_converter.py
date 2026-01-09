"""Tests for name_converter module."""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from generator.name_converter import (
    to_kebab_case,
    to_camel_case,
    to_snake_case,
    to_wit_name,
    to_ts_field_name,
    to_adapter_fn_name,
)


class TestToKebabCase:
    def test_pascal_case(self):
        assert to_kebab_case("ParsingSchema") == "parsing-schema"

    def test_multi_word_pascal(self):
        assert to_kebab_case("MultiTableParsingSchema") == "multi-table-parsing-schema"

    def test_single_word(self):
        assert to_kebab_case("Table") == "table"

    def test_already_lowercase(self):
        assert to_kebab_case("table") == "table"


class TestToCamelCase:
    def test_snake_case(self):
        assert to_camel_case("parse_table") == "parseTable"

    def test_multi_word_snake(self):
        assert to_camel_case("scan_tables_from_file") == "scanTablesFromFile"

    def test_single_word(self):
        assert to_camel_case("parse") == "parse"


class TestToSnakeCase:
    def test_kebab_case(self):
        assert to_snake_case("parsing-schema") == "parsing_schema"


class TestToWitName:
    def test_class_name(self):
        assert to_wit_name("ParsingSchema") == "parsing-schema"

    def test_simple(self):
        assert to_wit_name("Table") == "table"


class TestToTsFieldName:
    def test_snake_to_camel(self):
        assert to_ts_field_name("column_separator") == "columnSeparator"


class TestToAdapterFnName:
    def test_convert(self):
        assert to_adapter_fn_name("parsing-schema") == "convert_parsing_schema"

    def test_unwrap(self):
        assert to_adapter_fn_name("table", "unwrap") == "unwrap_table"


class TestKebabToCamel:
    def test_simple(self):
        from generator.name_converter import kebab_to_camel
        assert kebab_to_camel("parse-table") == "parseTable"

    def test_multi_word(self):
        from generator.name_converter import kebab_to_camel
        assert kebab_to_camel("scan-tables-from-file") == "scanTablesFromFile"

    def test_single_word(self):
        from generator.name_converter import kebab_to_camel
        assert kebab_to_camel("parse") == "parse"
