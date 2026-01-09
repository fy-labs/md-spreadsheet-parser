"""Tests for scanner module."""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest

from generator.scanner import (
    register_known_models,
    scan_module_for_classes,
    scan_module_for_functions,
    scan_class_methods,
)


class MockMember:
    """Mock for griffe member objects."""

    def __init__(
        self,
        name: str,
        is_alias: bool = False,
        is_class: bool = False,
        is_function: bool = False,
        annotation: str | None = None,
        returns: str | None = None,
        parameters: list = None,
        members: dict = None,
        value: object = None,
    ):
        self.name = name
        self.is_alias = is_alias
        self.is_class = is_class
        self.is_function = is_function
        self.annotation = annotation
        self.returns = returns
        self.parameters = parameters or []
        self.members = members or {}
        self.value = value


class MockParameter:
    """Mock for griffe Parameter objects."""

    def __init__(self, name: str, annotation: str | None = None, default: object = None):
        self.name = name
        self.annotation = annotation
        self.default = default


class MockModule:
    """Mock for griffe Module objects."""

    def __init__(self, path: str, members: dict):
        self.path = path
        self.members = members


class TestRegisterKnownModels:
    def test_registers_classes(self):
        module = MockModule(
            "test.module",
            {
                "Table": MockMember("Table", is_class=True),
                "Sheet": MockMember("Sheet", is_class=True),
            },
        )
        result = register_known_models([module])
        assert "Table" in result
        assert "Sheet" in result

    def test_skips_aliases(self):
        module = MockModule(
            "test.module",
            {
                "ImportedClass": MockMember("ImportedClass", is_alias=True, is_class=True),
            },
        )
        result = register_known_models([module])
        assert "ImportedClass" not in result

    def test_skips_private_classes(self):
        module = MockModule(
            "test.module",
            {
                "_PrivateClass": MockMember("_PrivateClass", is_class=True),
            },
        )
        result = register_known_models([module])
        assert "_PrivateClass" not in result

    def test_skips_json_typedicts(self):
        module = MockModule(
            "test.module",
            {
                "TableJSON": MockMember("TableJSON", is_class=True),
            },
        )
        result = register_known_models([module])
        assert "TableJSON" not in result


class TestScanModuleForClasses:
    def test_extracts_class_with_fields(self):
        table_class = MockMember(
            "Table",
            is_class=True,
            members={
                "name": MockMember("name", annotation="str"),
                "metadata": MockMember("metadata", annotation="dict[str, Any]"),
            },
        )
        module = MockModule("test.module", {"Table": table_class})
        known_models = {"Table"}

        result = scan_module_for_classes(module, known_models)

        assert len(result) == 1
        assert result[0]["class_name"] == "Table"
        assert result[0]["wit_name"] == "table"
        assert len(result[0]["fields"]) == 2


class TestScanModuleForFunctions:
    def test_extracts_function_with_params(self):
        parse_func = MockMember(
            "parse_table",
            is_function=True,
            parameters=[
                MockParameter("content", "str"),
                MockParameter("schema", "ParsingSchema | None", default="None"),
            ],
            returns="list[Table]",
        )
        module = MockModule("test.parsing", {"parse_table": parse_func})
        known_models = {"Table", "ParsingSchema"}

        result = scan_module_for_functions(module, known_models)

        assert len(result) == 1
        assert result[0]["name"] == "parse_table"
        assert result[0]["wit_name"] == "parse-table"
        assert len(result[0]["params"]) == 2

    def test_skips_private_functions(self):
        module = MockModule(
            "test.module",
            {
                "_private_func": MockMember("_private_func", is_function=True),
            },
        )
        result = scan_module_for_functions(module, set())
        assert len(result) == 0


class TestScanClassMethods:
    def test_extracts_class_methods(self):
        table_class = MockMember(
            "Table",
            is_class=True,
            members={
                "to_markdown": MockMember(
                    "to_markdown",
                    is_function=True,
                    parameters=[MockParameter("self")],
                    returns="str",
                ),
            },
        )
        module = MockModule("test.models", {"Table": table_class})
        known_models = {"Table"}

        result = scan_class_methods(module, known_models)

        assert len(result) == 1
        assert result[0]["class_name"] == "Table"
        assert result[0]["method_name"] == "to_markdown"
        assert result[0]["wit_func_name"] == "table-to-markdown"
