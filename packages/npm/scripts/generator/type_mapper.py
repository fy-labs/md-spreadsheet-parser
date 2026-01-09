"""Type mapping utilities for Python -> WIT -> TypeScript type conversion."""

import re
from typing import Literal

from .name_converter import to_adapter_fn_name, to_kebab_case

# Types that should be serialized as JSON strings
JSON_TYPES = frozenset(["dict[str, Any]", "dict", "Dict[str, Any]", "dict[str, any]"])


def is_json_type(py_type_str: str) -> bool:
    """Check if a Python type should be serialized as JSON in WIT.

    Examples:
        >>> is_json_type("dict[str, Any]")
        True
        >>> is_json_type("str")
        False
    """
    clean_type = py_type_str.strip()

    # Handle Optional wrapper
    if " | None" in clean_type:
        clean_type = clean_type.replace(" | None", "")
    if clean_type.startswith("Optional[") and clean_type.endswith("]"):
        clean_type = clean_type[9:-1]

    return clean_type in JSON_TYPES or clean_type.startswith("dict[")


def map_python_to_wit(
    py_type_str: str, known_models: set[str]
) -> tuple[str, str]:
    """Map Python type annotation to (WIT type, adapter transformation).

    The adapter transformation is a format string where __FIELD__ is replaced
    with the actual field access expression.

    Args:
        py_type_str: Python type annotation string
        known_models: Set of known model class names (e.g., {"Table", "Sheet"})

    Returns:
        Tuple of (wit_type, adapter_template)

    Examples:
        >>> map_python_to_wit("str", set())
        ('string', '__FIELD__')
        >>> map_python_to_wit("int", set())
        ('s32', '__FIELD__')
        >>> map_python_to_wit("dict[str, Any]", set())
        ('string', 'json.dumps(__FIELD__ or {})')
        >>> map_python_to_wit("Table", {"Table", "Sheet"})
        ('table', 'convert_table(__FIELD__)')
    """
    py_type = py_type_str.strip()

    # Handle Optional (T | None)
    if " | None" in py_type or "Optional[" in py_type:
        inner = _extract_optional_inner(py_type)
        wit_type, adapter = map_python_to_wit(inner, known_models)
        return (f"option<{wit_type}>", adapter)

    # Handle List
    if py_type.startswith("list["):
        inner = py_type[5:-1]
        wit_type, adapter = map_python_to_wit(inner, known_models)
        if adapter == "__FIELD__":
            return f"list<{wit_type}>", "__FIELD__"
        else:
            tmpl = adapter.replace("__FIELD__", "x")
            return f"list<{wit_type}>", f"[{tmpl} for x in __FIELD__]"

    # Handle Dict (Any) -> JSON string
    if py_type.startswith("dict[") and "Any" in py_type:
        return "string", "json.dumps(__FIELD__ or {})"

    # Handle simple dict without brackets
    if py_type == "dict":
        return "string", "json.dumps(__FIELD__ or {})"

    # Primitive mappings
    primitives: dict[str, tuple[str, str]] = {
        "str": ("string", "__FIELD__"),
        "int": ("s32", "__FIELD__"),
        "bool": ("bool", "__FIELD__"),
        "float": ("float64", "__FIELD__"),
    }
    if py_type in primitives:
        return primitives[py_type]

    # Known model classes
    if py_type in known_models:
        wit_name = to_kebab_case(py_type)
        adapter_fn = to_adapter_fn_name(wit_name, "convert")
        return wit_name, f"{adapter_fn}(__FIELD__)"

    # Special case for AlignmentType alias
    if py_type == "AlignmentType":
        return "alignment-type", "convert_alignment_type(__FIELD__)"

    # Default fallback
    return "string", "str(__FIELD__)"


def map_wit_to_ts(wit_type: str) -> str:
    """Map WIT type to TypeScript type annotation.

    Examples:
        >>> map_wit_to_ts("string")
        'string'
        >>> map_wit_to_ts("s32")
        'number'
        >>> map_wit_to_ts("list<string>")
        'any[]'
    """
    if wit_type == "string":
        return "string"
    if wit_type in ("s32", "s64", "u32", "u64", "float32", "float64"):
        return "number"
    if wit_type == "bool":
        return "boolean"
    if wit_type.startswith("list<"):
        return "any[]"
    if wit_type.startswith("option<"):
        return "any"
    return "any"


def _extract_optional_inner(py_type: str) -> str:
    """Extract the inner type from Optional[T] or T | None."""
    if " | None" in py_type:
        return py_type.replace(" | None", "")
    if py_type.startswith("Optional[") and py_type.endswith("]"):
        return py_type[9:-1]
    return py_type
