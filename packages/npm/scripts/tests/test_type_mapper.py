"""Tests for type_mapper module."""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from generator.type_mapper import (
    is_json_type,
    map_python_to_wit,
    map_wit_to_ts,
)


class TestIsJsonType:
    def test_dict_any(self):
        assert is_json_type("dict[str, Any]") is True

    def test_plain_dict(self):
        assert is_json_type("dict") is True

    def test_optional_dict(self):
        assert is_json_type("dict[str, Any] | None") is True

    def test_string_not_json(self):
        assert is_json_type("str") is False

    def test_list_not_json(self):
        assert is_json_type("list[str]") is False


class TestMapPythonToWit:
    def test_primitive_str(self):
        result = map_python_to_wit("str", set())
        assert result == ("string", "__FIELD__")

    def test_primitive_int(self):
        result = map_python_to_wit("int", set())
        assert result == ("s32", "__FIELD__")

    def test_primitive_bool(self):
        result = map_python_to_wit("bool", set())
        assert result == ("bool", "__FIELD__")

    def test_primitive_float(self):
        result = map_python_to_wit("float", set())
        assert result == ("float64", "__FIELD__")

    def test_optional_str(self):
        result = map_python_to_wit("str | None", set())
        assert result[0] == "option<string>"
        assert result[1] == "__FIELD__"

    def test_list_str(self):
        result = map_python_to_wit("list[str]", set())
        assert result == ("list<string>", "__FIELD__")

    def test_dict_any(self):
        result = map_python_to_wit("dict[str, Any]", set())
        assert result == ("string", "json.dumps(__FIELD__ or {})")

    def test_known_model(self):
        models = {"Table", "Sheet", "Workbook"}
        result = map_python_to_wit("Table", models)
        assert result == ("table", "convert_table(__FIELD__)")

    def test_unknown_type_fallback(self):
        result = map_python_to_wit("UnknownType", set())
        assert result == ("string", "str(__FIELD__)")

    def test_list_of_model(self):
        models = {"Table"}
        result = map_python_to_wit("list[Table]", models)
        assert result[0] == "list<table>"
        assert "convert_table" in result[1]


class TestMapWitToTs:
    def test_string(self):
        assert map_wit_to_ts("string") == "string"

    def test_s32(self):
        assert map_wit_to_ts("s32") == "number"

    def test_bool(self):
        assert map_wit_to_ts("bool") == "boolean"

    def test_list(self):
        assert map_wit_to_ts("list<string>") == "any[]"

    def test_option(self):
        assert map_wit_to_ts("option<string>") == "any"

    def test_unknown(self):
        assert map_wit_to_ts("custom-type") == "any"
