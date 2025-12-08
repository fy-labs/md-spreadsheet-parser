from typing import Type, TYPE_CHECKING
from pydantic import BaseModel, ValidationError as PydanticValidationError

from .schemas import ConversionSchema
from .models import Table
from .validation import TableValidationError

def _normalize_header(header: str) -> str:
    """
    Normalizes a header string to match field names (lowercase, snake_case).
    Example: "User Name" -> "user_name"
    """
    return header.lower().replace(" ", "_").strip()

def validate_table_pydantic(
    table: Table,
    schema_cls: Type[BaseModel],
    conversion_schema: ConversionSchema,
) -> list[BaseModel]:
    """
    Validates a Table using Pydantic.
    """
    # Map headers to fields (checking aliases)
    model_fields = schema_cls.model_fields
    
    # helper: find field name by alias or name
    # Pydantic v2 stores alias in FieldInfo
    header_map: dict[int, str] = {}  # column_index -> field_name
    
    # Pre-calculate normalized map of field names/aliases
    # We map normalized_string -> key_to_use_in_dict
    lookup_map = {}
    
    for name, field_info in model_fields.items():
        # By default Pydantic expects the alias if it exists
        # UNLESS populate_by_name=True is set.
        # To be safe and support common case (headers match alias), we prioritize alias.
        
        # If alias is defined, map its normalized version to the ALIAS string
        if field_info.alias:
            lookup_map[_normalize_header(field_info.alias)] = field_info.alias
            
            # Also allow mapping field name if populate_by_name is likely?
            # But we can't easily know the config.
            # Let's support both: normalized(name) -> name 
            # But if collision? Alias usually wins in user intent.
            if _normalize_header(name) not in lookup_map:
                lookup_map[_normalize_header(name)] = name
        else:
            lookup_map[_normalize_header(name)] = name

    normalized_headers = [_normalize_header(h) for h in table.headers]

    for idx, header in enumerate(normalized_headers):
        if header in lookup_map:
            header_map[idx] = lookup_map[header]

    results = []
    errors = []

    for row_idx, row in enumerate(table.rows):
        row_data = {}
        for col_idx, cell_value in enumerate(row):
            if col_idx in header_map:
                target_key = header_map[col_idx]
                
                # Check for field-specific converter first (Library specific override)
                if target_key in conversion_schema.field_converters:
                    converter = conversion_schema.field_converters[target_key]
                    try:
                        val = converter(cell_value)
                        row_data[target_key] = val
                    except Exception as e:
                         errors.append(f"Row {row_idx + 1}: Column '{target_key}' conversion failed: {e}")
                else:
                    if cell_value.strip() == "":
                        row_data[target_key] = None
                    else:
                        row_data[target_key] = cell_value

        try:
            obj = schema_cls(**row_data)
            results.append(obj)
        except PydanticValidationError as e:
            # Format Pydantic errors nicely
            for err in e.errors():
                loc = ".".join(map(str, err["loc"]))
                msg = err["msg"]
                errors.append(f"Row {row_idx + 1}: Field '{loc}' - {msg}")

    if errors:
        raise TableValidationError(errors)

    return results
