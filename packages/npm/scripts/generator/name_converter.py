"""Name conversion utilities for Python/WIT/TypeScript naming conventions."""

import re


def to_kebab_case(name: str) -> str:
    """Convert PascalCase or camelCase to kebab-case.

    Examples:
        >>> to_kebab_case("ParsingSchema")
        'parsing-schema'
        >>> to_kebab_case("MultiTableParsingSchema")
        'multi-table-parsing-schema'
    """
    # Insert hyphen before uppercase letters (except at start)
    return re.sub(r"(?<!^)(?=[A-Z])", "-", name).lower()


def to_camel_case(name: str) -> str:
    """Convert snake_case to camelCase.

    Examples:
        >>> to_camel_case("parse_table")
        'parseTable'
        >>> to_camel_case("scan_tables_from_file")
        'scanTablesFromFile'
    """
    return re.sub(r"_([a-z])", lambda g: g.group(1).upper(), name)


def to_snake_case(name: str) -> str:
    """Convert kebab-case to snake_case.

    Examples:
        >>> to_snake_case("parsing-schema")
        'parsing_schema'
    """
    return name.replace("-", "_")


def to_wit_name(class_name: str) -> str:
    """Convert Python class name to WIT type name.

    Examples:
        >>> to_wit_name("ParsingSchema")
        'parsing-schema'
        >>> to_wit_name("Table")
        'table'
    """
    return to_kebab_case(class_name)


def kebab_to_camel(name: str) -> str:
    """Convert kebab-case to camelCase.

    Examples:
        >>> kebab_to_camel("parse-table")
        'parseTable'
        >>> kebab_to_camel("scan-tables-from-file")
        'scanTablesFromFile'
    """
    return re.sub(r"-([a-z])", lambda g: g.group(1).upper(), name)


def to_ts_field_name(py_name: str) -> str:
    """Convert Python snake_case field name to TypeScript camelCase.

    Examples:
        >>> to_ts_field_name("column_separator")
        'columnSeparator'
    """
    return to_camel_case(py_name)


def to_adapter_fn_name(wit_name: str, prefix: str = "convert") -> str:
    """Generate adapter function name from WIT type name.

    Examples:
        >>> to_adapter_fn_name("parsing-schema")
        'convert_parsing_schema'
        >>> to_adapter_fn_name("table", "unwrap")
        'unwrap_table'
    """
    return f"{prefix}_{to_snake_case(wit_name)}"
