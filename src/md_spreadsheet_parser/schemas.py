from dataclasses import dataclass


@dataclass(frozen=True)
class ParsingSchema:
    """
    Configuration for parsing markdown tables.
    Designed to be immutable and passed to pure functions.

    Attributes:
        column_separator (str): Character used to separate columns. Defaults to "|".
        header_separator_char (str): Character used in the separator row. Defaults to "-".
        require_outer_pipes (bool): Whether tables must have outer pipes (e.g. `| col |`). Defaults to False.
        strip_whitespace (bool): Whether to strip whitespace from cell values. Defaults to True.
    """

    column_separator: str = "|"
    header_separator_char: str = "-"
    require_outer_pipes: bool = False
    strip_whitespace: bool = True


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
    table_header_level: int | None = None
    capture_description: bool = False

    def __post_init__(self):
        if self.capture_description and self.table_header_level is None:
            raise ValueError(
                "capture_description=True requires table_header_level to be set"
            )
