from dataclasses import dataclass
from typing import Any, TypedDict

from .schemas import ParsingSchema, MultiTableParsingSchema, DEFAULT_SCHEMA
from .validation import validate_table
from .generator import (
    generate_table_markdown,
    generate_sheet_markdown,
    generate_workbook_markdown,
)


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

    def to_models[T](self, schema_cls: type[T]) -> list[T]:
        """
        Converts the table rows into a list of dataclass instances, performing validation and type conversion.

        Args:
            schema_cls (type[T]): The dataclass type to validate against.

        Returns:
            list[T]: A list of validated dataclass instances.

        Raises:
            ValueError: If schema_cls is not a dataclass.
            TableValidationError: If validation fails for any row or if the table has no headers.
        """
        return validate_table(self, schema_cls)

    def to_markdown(self, schema: ParsingSchema = DEFAULT_SCHEMA) -> str:
        """
        Generates a Markdown string representation of the table.

        Args:
            schema (ParsingSchema, optional): Configuration for formatting.

        Returns:
            str: The Markdown string.
        """
        return generate_table_markdown(self, schema)


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

    def to_markdown(self, schema: ParsingSchema = DEFAULT_SCHEMA) -> str:
        """
        Generates a Markdown string representation of the sheet.

        Args:
            schema (ParsingSchema, optional): Configuration for formatting.

        Returns:
            str: The Markdown string.
        """
        return generate_sheet_markdown(self, schema)


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

    def to_markdown(self, schema: MultiTableParsingSchema) -> str:
        """
        Generates a Markdown string representation of the workbook.

        Args:
            schema (MultiTableParsingSchema): Configuration for formatting.

        Returns:
            str: The Markdown string.
        """
        return generate_workbook_markdown(self, schema)
