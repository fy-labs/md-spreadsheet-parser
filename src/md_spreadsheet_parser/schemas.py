from dataclasses import dataclass
from typing import Any, TypedDict


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


@dataclass(frozen=True)
class ParseResult:
    """
    Structured result of the parsing operation (internal use).

    Attributes:
        headers (list[str] | None): List of header names, or None if no header row found.
        rows (list[list[str]]): List of rows, where each row is a list of cell values.
        metadata (dict[str, Any]): Additional metadata about the parsing process.
    """

    headers: list[str] | None
    rows: list[list[str]]
    metadata: dict[str, Any]


# Default schema for standard Markdown tables (GFM style)
DEFAULT_SCHEMA = ParsingSchema()


class TableJSON(TypedDict):
    """
    JSON-compatible dictionary representation of a Table.
    """

    name: str | None
    description: str | None
    headers: list[str] | None
    rows: list[list[str]]
    metadata: dict[str, Any]


class SheetJSON(TypedDict):
    """
    JSON-compatible dictionary representation of a Sheet.
    """

    name: str
    tables: list[TableJSON]


class WorkbookJSON(TypedDict):
    """
    JSON-compatible dictionary representation of a Workbook.
    """

    sheets: list[SheetJSON]


@dataclass(frozen=True)
class Table:
    """
    Represents a parsed table with optional metadata.

    Attributes:
        headers (list[str] | None): List of column headers, or None if the table has no headers.
        rows (list[list[str]]): List of data rows.
        name (str | None): Name of the table (e.g. from a header). Defaults to None.
        description (str | None): Description of the table. Defaults to None.
        metadata (dict[str, Any] | None): Arbitrary metadata. Defaults to None.
    """

    headers: list[str] | None
    rows: list[list[str]]
    name: str | None = None
    description: str | None = None
    metadata: dict[str, Any] | None = None

    def __post_init__(self):
        if self.metadata is None:
            # Hack to allow default value for mutable type in frozen dataclass
            object.__setattr__(self, "metadata", {})

    @property
    def json(self) -> TableJSON:
        """
        Returns a JSON-compatible dictionary representation of the table.

        Returns:
            TableJSON: A dictionary containing the table data.
        """
        return {
            "name": self.name,
            "description": self.description,
            "headers": self.headers,
            "rows": self.rows,
            "metadata": self.metadata if self.metadata is not None else {},
        }


@dataclass(frozen=True)
class Sheet:
    """
    Represents a single sheet containing tables.

    Attributes:
        name (str): Name of the sheet.
        tables (list[Table]): List of tables contained in this sheet.
    """

    name: str
    tables: list[Table]

    @property
    def json(self) -> SheetJSON:
        """
        Returns a JSON-compatible dictionary representation of the sheet.

        Returns:
            SheetJSON: A dictionary containing the sheet data.
        """
        return {"name": self.name, "tables": [t.json for t in self.tables]}

    def get_table(self, name: str) -> Table | None:
        """
        Retrieve a table by its name.

        Args:
            name (str): The name of the table to retrieve.

        Returns:
            Table | None: The table object if found, otherwise None.
        """
        for table in self.tables:
            if table.name == name:
                return table
        return None


@dataclass(frozen=True)
class Workbook:
    """
    Represents a collection of sheets (multi-table output).

    Attributes:
        sheets (list[Sheet]): List of sheets in the workbook.
    """

    sheets: list[Sheet]

    @property
    def json(self) -> WorkbookJSON:
        """
        Returns a JSON-compatible dictionary representation of the workbook.

        Returns:
            WorkbookJSON: A dictionary containing the workbook data.
        """
        return {"sheets": [s.json for s in self.sheets]}

    def get_sheet(self, name: str) -> Sheet | None:
        """
        Retrieve a sheet by its name.

        Args:
            name (str): The name of the sheet to retrieve.

        Returns:
            Sheet | None: The sheet object if found, otherwise None.
        """
        for sheet in self.sheets:
            if sheet.name == name:
                return sheet
        return None


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
