from dataclasses import dataclass, field
from typing import Callable, Any


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


# Default schema for standard Markdown tables (GFM style)
DEFAULT_SCHEMA = ParsingSchema()


@dataclass(frozen=True)
class MultiTableParsingSchema(ParsingSchema):
    """
    Configuration for parsing multiple tables (workbook mode).
    Inherits from ParsingSchema.

    Attributes:
        root_marker (str): The marker indicating the start of the data section. Defaults to "# Tables".
        sheet_header_level (int): The markdown header level for sheets. Defaults to 2 (e.g. `## Sheet`).
        table_header_level (int | None): The markdown header level for tables. If None, table names are not extracted. Defaults to None.
        capture_description (bool): Whether to capture text between the table header and the table as a description. Defaults to False.
    """

    root_marker: str = "# Tables"
    sheet_header_level: int = 2
    table_header_level: int | None = 3
    capture_description: bool = True

    def __post_init__(self):
        if self.capture_description and self.table_header_level is None:
            raise ValueError(
                "capture_description=True requires table_header_level to be set"
            )


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
    )
    custom_converters: dict[type, Callable[[str], Any]] = field(default_factory=dict)
    field_converters: dict[str, Callable[[str], Any]] = field(default_factory=dict)


DEFAULT_CONVERSION_SCHEMA = ConversionSchema()


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
