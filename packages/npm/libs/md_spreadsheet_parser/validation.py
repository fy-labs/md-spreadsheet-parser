import json
import types
from dataclasses import fields, is_dataclass
from typing import TYPE_CHECKING, Any, Type, TypeVar, get_args, get_origin, is_typeddict

if TYPE_CHECKING:
    from .models import Table
from .schemas import DEFAULT_CONVERSION_SCHEMA, ConversionSchema
from .utils import normalize_header

T = TypeVar("T")


class TableValidationError(Exception):
    """
    Exception raised when table validation fails.
    Contains a list of errors found during validation.
    """

    def __init__(self, errors: list[str]):
        self.errors = errors
        super().__init__(
            f"Validation failed with {len(errors)} errors:\n" + "\n".join(errors)
        )


def _convert_value(
    value: str, target_type: Type, schema: ConversionSchema = DEFAULT_CONVERSION_SCHEMA
) -> Any:
    """
    Converts a string value to the target type.
    Supports int, float, bool, str, and Optional types.
    """
    # Check custom converters first
    if target_type in schema.custom_converters:
        return schema.custom_converters[target_type](value)

    origin = get_origin(target_type)
    args = get_args(target_type)

    # Handle Optional[T] (Union[T, None])
    # Robust check for Union-like types
    if origin is not None and (origin is types.UnionType or "Union" in str(origin)):
        if type(None) in args:
            if not value.strip():
                return None
            # Find the non-None type
            for arg in args:
                if arg is not type(None):
                    return _convert_value(value, arg, schema)

    # Handle basic types
    if target_type is int:
        if not value.strip():
            raise ValueError("Empty value for int field")
        return int(value)

    if target_type is float:
        if not value.strip():
            raise ValueError("Empty value for float field")
        return float(value)

    if target_type is bool:
        lower_val = value.lower().strip()
        for true_val, false_val in schema.boolean_pairs:
            if lower_val == true_val.lower():
                return True
            if lower_val == false_val.lower():
                return False

        raise ValueError(f"Invalid boolean value: '{value}'")

    if target_type is str:
        return value

    # JSON Parsing for dict/list
    # Logic: If target is strict dict or list, try parsing as JSON
    # This covers dict, list, dict[str, Any], list[int], etc.
    if origin in (dict, list) or target_type in (dict, list):
        if not value.strip():
            # Empty string -> Empty dict/list? Or None?
            # Let's say empty string is not valid JSON, so strictly it should fail or return empty type.
            # For user friendliness, let's treat empty string as empty container if not Optional
            # For user friendliness, let's treat empty string as empty container if not Optional
            if origin:
                return origin()  # type: ignore
            if target_type is dict:
                return {}
            if target_type is list:
                return []
            return target_type()  # type: ignore
        try:
            return json.loads(value)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON for {target_type}: {e}")

    # Fallback for other types (or if type hint is missing)
    return value


# --- Pydantic Support (Optional) ---

try:
    from pydantic import BaseModel

    HAS_PYDANTIC = True
except ImportError:
    HAS_PYDANTIC = False
    HAS_PYDANTIC = False
    BaseModel = object  # type: ignore


def _validate_table_dataclass(
    table: "Table",
    schema_cls: Type[T],
    conversion_schema: ConversionSchema,
) -> list[T]:
    """
    Validates a Table using standard dataclasses.
    """
    # Map headers to fields
    cls_fields = {f.name: f for f in fields(schema_cls)}  # type: ignore
    header_map: dict[int, str] = {}  # column_index -> field_name

    normalized_headers = [normalize_header(h) for h in (table.headers or [])]

    for idx, header in enumerate(normalized_headers):
        if header in cls_fields:
            header_map[idx] = header

    # Process rows
    results: list[T] = []
    errors: list[str] = []

    for row_idx, row in enumerate(table.rows):
        row_data = {}
        row_errors = []

        for col_idx, cell_value in enumerate(row):
            if col_idx in header_map:
                field_name = header_map[col_idx]
                field_def = cls_fields[field_name]

                try:
                    # Check for field-specific converter first
                    if field_name in conversion_schema.field_converters:
                        converter = conversion_schema.field_converters[field_name]
                        converted_value = converter(cell_value)
                    else:
                        converted_value = _convert_value(
                            cell_value,
                            field_def.type,  # type: ignore
                            conversion_schema,  # type: ignore
                        )
                    row_data[field_name] = converted_value
                except ValueError as e:
                    row_errors.append(f"Column '{field_name}': {str(e)}")
                except Exception:
                    row_errors.append(
                        f"Column '{field_name}': Failed to convert '{cell_value}' to {field_def.type}"
                    )

        if row_errors:
            for err in row_errors:
                errors.append(f"Row {row_idx + 1}: {err}")
            continue

        try:
            obj = schema_cls(**row_data)
            results.append(obj)
        except TypeError as e:
            # This catches missing required arguments
            errors.append(f"Row {row_idx + 1}: {str(e)}")

    if errors:
        raise TableValidationError(errors)

    return results


def _validate_table_typeddict(
    table: "Table",
    schema_cls: Type[T],
    conversion_schema: ConversionSchema,
) -> list[T]:
    """
    Validates a Table using TypedDict.
    """
    # TypedDict annotations
    # __annotations__ or __required_keys__ / __optional_keys__ behavior
    # For simplicity, we trust __annotations__ for type hints
    annotations = schema_cls.__annotations__

    header_map: dict[int, str] = {}
    normalized_headers = [normalize_header(h) for h in (table.headers or [])]

    # Map headers to TypedDict keys
    # Prioritize exact match, then normalized match
    # TypedDict doesn't support 'alias' natively usually, so simple mapping
    for idx, header in enumerate(normalized_headers):
        # 1. Check direct match with key names (normalized)
        for key in annotations:
            if normalize_header(key) == header:
                header_map[idx] = key
                break

    results: list[T] = []
    errors: list[str] = []

    for row_idx, row in enumerate(table.rows):
        row_data = {}
        row_errors = []

        for col_idx, cell_value in enumerate(row):
            if col_idx in header_map:
                key = header_map[col_idx]
                target_type = annotations[key]

                try:
                    if key in conversion_schema.field_converters:
                        converter = conversion_schema.field_converters[key]
                        converted_value = converter(cell_value)
                    else:
                        converted_value = _convert_value(
                            cell_value, target_type, conversion_schema
                        )
                    row_data[key] = converted_value
                except Exception as e:
                    row_errors.append(f"Column '{key}': {str(e)}")

        if row_errors:
            for err in row_errors:
                errors.append(f"Row {row_idx + 1}: {err}")
            continue

        # Create TypedDict (it's just a dict at runtime)
        # We should check required keys if using TypedDict features (Python 3.9+)
        # But for now, simple dict construction
        try:
            # Basic check: Missing keys?
            # TypedDict doesn't complain on instantiation (it's a dict),
            # but static type checkers do.
            # We should probably validate required keys if possible, but let's keep it simple for now.
            results.append(row_data)  # type: ignore
        except Exception as e:
            errors.append(f"Row {row_idx + 1}: {str(e)}")

    if errors:
        raise TableValidationError(errors)

    return results


def _validate_table_dict(
    table: "Table",
    conversion_schema: ConversionSchema,
) -> list[dict[str, Any]]:
    """
    Converts a Table to a list of dicts.
    Keys are derived from headers.
    """
    # normalized_headers = [normalize_header(h) for h in table.headers]

    # Use original header names or normalized?
    # Usually users prefer original headers as keys if they passed 'dict'.
    # But wait, validate_table usually normalizes.
    # Let's use the actual header string from the table as the key,
    # but normalize for field_converter lookups.

    results = []

    for row in table.rows:
        row_data = {}
        for idx, cell_value in enumerate(row):
            if table.headers and idx < len(table.headers):
                original_header = table.headers[idx]
                key_for_conversion = normalize_header(original_header)

                # Check converters
                if key_for_conversion in conversion_schema.field_converters:
                    converter = conversion_schema.field_converters[key_for_conversion]
                    try:
                        val = converter(cell_value)
                    except Exception:
                        val = (
                            cell_value  # Fallback or Raise? Let's fallback for raw dict
                        )
                else:
                    val = cell_value

                row_data[original_header] = val
        results.append(row_data)

    return results


def validate_table(
    table: "Table",
    schema_cls: Type[T],
    conversion_schema: ConversionSchema = DEFAULT_CONVERSION_SCHEMA,
) -> list[T]:
    """
    Validates a Table object against a dataclass OR Pydantic schema.

    Args:
        table: The Table object to validate.
        schema_cls: The dataclass or Pydantic model type to validate against.
        conversion_schema: Configuration for type conversion.

    Returns:
        list[T]: A list of validated instances.

    Raises:
        ValueError: If schema_cls is not a valid schema.
        TableValidationError: If validation fails.
    """
    # Check for Pydantic Model
    if HAS_PYDANTIC and BaseModel and issubclass(schema_cls, BaseModel):
        if not table.headers:
            raise TableValidationError(["Table has no headers"])
        # Import adapter lazily to avoid unused imports when pydantic is not used
        # (though we checked HAS_PYDANTIC so it exists)
        from .pydantic_adapter import validate_table_pydantic

        return validate_table_pydantic(table, schema_cls, conversion_schema)  # type: ignore

    # Check for Dataclass
    if is_dataclass(schema_cls):
        if not table.headers:
            raise TableValidationError(["Table has no headers"])
        return _validate_table_dataclass(table, schema_cls, conversion_schema)

    # Check for TypedDict
    if is_typeddict(schema_cls):
        if not table.headers:
            raise TableValidationError(["Table has no headers"])
        return _validate_table_typeddict(table, schema_cls, conversion_schema)

    # Check for simple dict
    # We compare schema_cls against dict type
    if schema_cls is dict:
        if not table.headers:
            raise TableValidationError(["Table has no headers"])
        return _validate_table_dict(table, conversion_schema)  # type: ignore

    raise ValueError(
        f"{schema_cls} must be a dataclass, Pydantic model, TypedDict, or dict"
    )
