from dataclasses import dataclass, field
from typing import Any, Callable


@dataclass(frozen=True)
class ParsingSchema:
    """
    Configuration for parsing markdown tables.
    Designed to be immutable and passed to pure functions.

    Attributes:
        column_separator (str): Character used to separate columns. Defaults to "|".
        header_separator_char (str): Character used in the separator row. Defaults to "-".
        require_outer_pipes (bool): Whether tables must have outer pipes (e.g. `| col |`). Defaults to True.
        strip_whitespace (bool): Whether to strip whitespace from cell values. Defaults to True.
    """

    column_separator: str = "|"
    header_separator_char: str = "-"
    require_outer_pipes: bool = True
    strip_whitespace: bool = True
    convert_br_to_newline: bool = True

    def __post_init__(self):
        # Ensure defaults if None is passed (e.g. from WASM)
        if self.column_separator is None:
            object.__setattr__(self, "column_separator", "|")
        if self.header_separator_char is None:
            object.__setattr__(self, "header_separator_char", "-")
        if self.require_outer_pipes is None:
            object.__setattr__(self, "require_outer_pipes", True)
        if self.strip_whitespace is None:
            object.__setattr__(self, "strip_whitespace", True)
        if self.convert_br_to_newline is None:
            object.__setattr__(self, "convert_br_to_newline", True)


# Default schema for standard Markdown tables (GFM style)
DEFAULT_SCHEMA = ParsingSchema()


@dataclass(frozen=True)
class MultiTableParsingSchema(ParsingSchema):
    """
    Configuration for parsing multiple tables (workbook mode).
    Inherits from ParsingSchema.

    Attributes:
        root_marker (str | None): The marker indicating the start of the data section.
            If None, auto-detection is used: single H1 → Workbook, or fallback to
            "# Tables" / "# Workbook". Defaults to None.
        sheet_header_level (int | None): The markdown header level for sheets.
            If None, derived from workbook_level + 1. Defaults to None.
        table_header_level (int | None): The markdown header level for tables.
            If None, derived from workbook_level + 2. Defaults to None.
        capture_description (bool): Whether to capture text between the table header
            and the table as a description. Defaults to True.
    """

    root_marker: str | None = None
    sheet_header_level: int | None = None
    table_header_level: int | None = None
    capture_description: bool = True

    def __post_init__(self):
        # Handle ParsingSchema defaults manually since they are separate fields in instance
        if self.column_separator is None:
            object.__setattr__(self, "column_separator", "|")
        if self.header_separator_char is None:
            object.__setattr__(self, "header_separator_char", "-")
        if self.require_outer_pipes is None:
            object.__setattr__(self, "require_outer_pipes", True)
        if self.strip_whitespace is None:
            object.__setattr__(self, "strip_whitespace", True)
        if self.convert_br_to_newline is None:
            object.__setattr__(self, "convert_br_to_newline", True)

        # root_marker, sheet_header_level, table_header_level can all be None
        # (auto-detection is handled in parsing.py)

        if self.capture_description is None:
            object.__setattr__(self, "capture_description", True)


@dataclass(frozen=True)
class ConversionSchema:
    """
    Configuration for converting string values to Python types.

    Attributes:
        boolean_pairs: Pairs of strings representing (True, False). Case-insensitive.
                       Example: `(("yes", "no"), ("on", "off"))`.
        custom_converters: Dictionary mapping ANY Python type to a conversion function `str -> Any`.
                           You can specify:
                           - Built-in types: `int`, `float`, `bool` (to override default behavior)
                           - Standard library types: `Decimal`, `datetime`, `date`, `ZoneInfo`
                           - Custom classes: `MyClass`, `Product`
        field_converters: Dictionary mapping field names (str) to conversion functions.
                          Takes precedence over `custom_converters`.
    """

    boolean_pairs: tuple[tuple[str, str], ...] = (
        ("true", "false"),
        ("yes", "no"),
        ("1", "0"),
        ("on", "off"),
        ("[x]", "[ ]"),
    )
    custom_converters: dict[type, Callable[[str], Any]] = field(default_factory=dict)
    field_converters: dict[str, Callable[[str], Any]] = field(default_factory=dict)


DEFAULT_CONVERSION_SCHEMA = ConversionSchema()


DEFAULT_MULTI_TABLE_SCHEMA = MultiTableParsingSchema()


@dataclass(frozen=True)
class ExcelParsingSchema:
    """
    Configuration for parsing Excel-exported data (TSV/CSV or openpyxl).

    Attributes:
        header_rows: Number of header rows (1 or 2).
                     If 2, headers are flattened to "Parent - Child" format.
        fill_merged_headers: Whether to forward-fill empty header cells
                             (for merged cells in Excel exports).
        delimiter: Column separator for TSV/CSV parsing. Default is tab.
        header_separator: Separator used when flattening 2-row headers.
    """

    header_rows: int = 1
    fill_merged_headers: bool = True
    delimiter: str = "\t"
    header_separator: str = " - "

    def __post_init__(self):
        if self.header_rows not in (1, 2):
            raise ValueError("header_rows must be 1 or 2")


DEFAULT_EXCEL_SCHEMA = ExcelParsingSchema()
