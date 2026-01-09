"""Tests for Jinja2 template rendering."""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest

try:
    from jinja2 import Environment, FileSystemLoader
    JINJA2_AVAILABLE = True
except ImportError:
    JINJA2_AVAILABLE = False

TEMPLATES_DIR = Path(__file__).parent.parent / "templates"


@pytest.fixture
def jinja_env():
    """Create Jinja2 environment for template testing."""
    if not JINJA2_AVAILABLE:
        pytest.skip("Jinja2 not installed")
    return Environment(
        loader=FileSystemLoader(str(TEMPLATES_DIR)),
        trim_blocks=True,
        lstrip_blocks=True,
    )


class TestTsClassTemplate:
    def test_simple_class_renders(self, jinja_env):
        """Test that ts_class template renders without errors."""
        template = jinja_env.get_template("partials/ts_class.jinja2")
        result = template.render(
            cls={
                "name": "TestTable",
                "fields": [
                    {"js_name": "name", "ts_type": "string", "is_json": False, "is_model_list": False},
                    {"js_name": "metadata", "ts_type": "any", "is_json": True, "is_model_list": False},
                ],
                "has_json_getter": False,
                "methods": [],
            }
        )
        assert "export class TestTable" in result
        assert "constructor(data?: Partial<TestTable>)" in result
        assert "toDTO()" in result

    def test_json_field_parsing(self, jinja_env):
        """Test that JSON fields get proper parsing in constructor."""
        template = jinja_env.get_template("partials/ts_class.jinja2")
        result = template.render(
            cls={
                "name": "Table",
                "fields": [
                    {"js_name": "metadata", "ts_type": "any", "is_json": True, "is_model_list": False},
                ],
                "has_json_getter": False,
                "methods": [],
            }
        )
        assert "JSON.parse(data.metadata)" in result

    def test_model_list_wrapping(self, jinja_env):
        """Test that list of models gets wrapped properly."""
        template = jinja_env.get_template("partials/ts_class.jinja2")
        result = template.render(
            cls={
                "name": "Sheet",
                "fields": [
                    {"js_name": "tables", "ts_type": "any[]", "is_json": False, "is_model_list": True, "inner_model": "Table"},
                ],
                "has_json_getter": False,
                "methods": [],
            }
        )
        assert "new Table(x)" in result


class TestTsMethodTemplate:
    def test_method_with_self_return(self, jinja_env):
        """Test that methods returning self use hydration pattern."""
        template = jinja_env.get_template("partials/ts_method.jinja2")
        result = template.render(
            cls={"name": "Table"},
            method={
                "name": "updateCell",
                "args": ["rowIdx: any", "colIdx: any", "value: any"],
                "wasm_name": "tableUpdateCell",
                "call_args": ["dto", "rowIdx", "colIdx", "value"],
                "returns_self": True,
                "is_toModels": False,
                "returns_optional_model": False,
                "returns_model": False,
            }
        )
        assert "const hydrated = new Table(res)" in result
        assert "Object.assign(this, hydrated)" in result
        assert "return this" in result


class TestIndexTemplate:
    def test_template_exists(self, jinja_env):
        """Ensure main index.ts template exists."""
        template = jinja_env.get_template("index.ts.jinja2")
        assert template is not None

    def test_basic_structure(self, jinja_env):
        """Test that index.ts template has expected boilerplate."""
        template = jinja_env.get_template("index.ts.jinja2")
        result = template.render(
            wasm_imports=["parseTable as _parseTable"],
            global_functions=[],
            classes=[],
        )
        assert "import { parseTable as _parseTable }" in result
        assert "ensureNodeEnvironment" in result
        assert "resolveToVirtualPath" in result
