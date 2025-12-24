from dataclasses import dataclass, replace
from typing import Any, Literal, TypedDict, TypeVar

from .generator import (
    generate_sheet_markdown,
    generate_table_markdown,
    generate_workbook_markdown,
)
from .schemas import (
    DEFAULT_CONVERSION_SCHEMA,
    DEFAULT_SCHEMA,
    ConversionSchema,
    MultiTableParsingSchema,
    ParsingSchema,
)
from .validation import validate_table

T = TypeVar("T")

AlignmentType = Literal["left", "center", "right", "default"]


class TableJSON(TypedDict):
    """
    JSON-compatible dictionary representation of a Table.
    """

    name: str | None
    description: str | None
    headers: list[str] | None
    rows: list[list[str]]
    metadata: dict[str, Any]
    start_line: int | None
    end_line: int | None
    alignments: list[AlignmentType] | None


class SheetJSON(TypedDict):
    """
    JSON-compatible dictionary representation of a Sheet.
    """

    name: str
    tables: list[TableJSON]
    metadata: dict[str, Any]


class WorkbookJSON(TypedDict):
    """
    JSON-compatible dictionary representation of a Workbook.
    """

    sheets: list[SheetJSON]
    metadata: dict[str, Any]


@dataclass(frozen=True)
class Table:
    """
    Represents a parsed table with optional metadata.

    Attributes:
        headers (list[str] | None): List of column headers, or None if the table has no headers.
        rows (list[list[str]]): List of data rows.
        alignments (list[AlignmentType] | None): List of column alignments ('left', 'center', 'right'). Defaults to None.
        name (str | None): Name of the table (e.g. from a header). Defaults to None.
        description (str | None): Description of the table. Defaults to None.
        metadata (dict[str, Any] | None): Arbitrary metadata. Defaults to None.
    """

    headers: list[str] | None
    rows: list[list[str]]
    alignments: list[AlignmentType] | None = None
    name: str | None = None
    description: str | None = None
    metadata: dict[str, Any] | None = None
    start_line: int | None = None
    end_line: int | None = None

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
            "start_line": self.start_line,
            "end_line": self.end_line,
            "alignments": self.alignments,
        }

    def to_models(
        self,
        schema_cls: type[T],
        conversion_schema: ConversionSchema = DEFAULT_CONVERSION_SCHEMA,
    ) -> list[T]:
        """
        Converts the table rows into a list of dataclass instances, performing validation and type conversion.

        Args:
            schema_cls (type[T]): The dataclass type to validate against.
            conversion_schema (ConversionSchema, optional): Configuration for type conversion.

        Returns:
            list[T]: A list of validated dataclass instances.

        Raises:
            ValueError: If schema_cls is not a dataclass.
            TableValidationError: If validation fails for any row or if the table has no headers.
        """
        return validate_table(self, schema_cls, conversion_schema)

    def to_markdown(self, schema: ParsingSchema = DEFAULT_SCHEMA) -> str:
        """
        Generates a Markdown string representation of the table.

        Args:
            schema (ParsingSchema, optional): Configuration for formatting.

        Returns:
            str: The Markdown string.
        """
        return generate_table_markdown(self, schema)

    def update_cell(self, row_idx: int, col_idx: int, value: str) -> "Table":
        """
        Return a new Table with the specified cell updated.
        """
        # Handle header update
        if row_idx == -1:
            if self.headers is None:
                # Determine width from rows if possible, or start fresh
                width = len(self.rows[0]) if self.rows else (col_idx + 1)
                new_headers = [""] * width
                # Ensure width enough
                if col_idx >= len(new_headers):
                    new_headers.extend([""] * (col_idx - len(new_headers) + 1))
            else:
                new_headers = list(self.headers)
                if col_idx >= len(new_headers):
                    new_headers.extend([""] * (col_idx - len(new_headers) + 1))

            # Update alignments if headers grew
            new_alignments = list(self.alignments) if self.alignments else []
            if len(new_headers) > len(new_alignments):
                # Fill with default/None up to new width
                # But we only need as many alignments as columns.
                # If alignments is None, it stays None?
                # Ideally if we start tracking alignments, we should init it?
                # If self.alignments was None, we might keep it None unless explicitly set?
                # Consistent behavior: If alignments is NOT None, expand it.
                if self.alignments is not None:
                    # Cast or explicit type check might be needed for strict type checkers with literals
                    # Using a typed list to satisfy invariant list[AlignmentType]
                    extension: list[AlignmentType] = ["default"] * (
                        len(new_headers) - len(new_alignments)
                    )
                    new_alignments.extend(extension)

            final_alignments = new_alignments if self.alignments is not None else None

            new_headers[col_idx] = value

            return replace(self, headers=new_headers, alignments=final_alignments)

        # Handle Body update
        # 1. Ensure row exists
        new_rows = [list(r) for r in self.rows]

        # Grow rows if needed
        if row_idx >= len(new_rows):
            # Calculate width
            width = (
                len(self.headers)
                if self.headers
                else (len(new_rows[0]) if new_rows else 0)
            )
            if width == 0:
                width = col_idx + 1  # At least cover the new cell

            rows_to_add = row_idx - len(new_rows) + 1
            for _ in range(rows_to_add):
                new_rows.append([""] * width)

        # If columns expanded due to row update, we might need to expand alignments too
        current_width = len(new_rows[0]) if new_rows else 0
        if col_idx >= current_width:
            # This means we are expanding columns
            if self.alignments is not None:
                width_needed = col_idx + 1
                current_align_len = len(self.alignments)
                if width_needed > current_align_len:
                    new_alignments = list(self.alignments)
                    extension: list[AlignmentType] = ["default"] * (
                        width_needed - current_align_len
                    )
                    new_alignments.extend(extension)
                    return replace(
                        self,
                        rows=self._update_rows_cell(new_rows, row_idx, col_idx, value),
                        alignments=new_alignments,
                    )

        return replace(
            self, rows=self._update_rows_cell(new_rows, row_idx, col_idx, value)
        )

    def _update_rows_cell(self, new_rows, row_idx, col_idx, value):
        target_row = new_rows[row_idx]
        if col_idx >= len(target_row):
            target_row.extend([""] * (col_idx - len(target_row) + 1))
        target_row[col_idx] = value
        return new_rows

    def delete_row(self, row_idx: int) -> "Table":
        """
        Return a new Table with the row at index removed.
        """
        new_rows = [list(r) for r in self.rows]
        if 0 <= row_idx < len(new_rows):
            new_rows.pop(row_idx)
        return replace(self, rows=new_rows)

    def delete_column(self, col_idx: int) -> "Table":
        """
        Return a new Table with the column at index removed.
        """
        new_headers = list(self.headers) if self.headers else None
        if new_headers and 0 <= col_idx < len(new_headers):
            new_headers.pop(col_idx)

        new_rows = []
        for row in self.rows:
            new_row = list(row)
            if 0 <= col_idx < len(new_row):
                new_row.pop(col_idx)
            new_rows.append(new_row)

        new_alignments = None
        if self.alignments is not None:
            new_alignments = list(self.alignments)
            if 0 <= col_idx < len(new_alignments):
                new_alignments.pop(col_idx)

        return replace(
            self, headers=new_headers, rows=new_rows, alignments=new_alignments
        )

    def clear_column_data(self, col_idx: int) -> "Table":
        """
        Return a new Table with data in the specified column cleared (set to empty string),
        but headers and column structure preserved.
        """
        # Headers remain unchanged

        new_rows = []
        for row in self.rows:
            new_row = list(row)
            if 0 <= col_idx < len(new_row):
                new_row[col_idx] = ""
            new_rows.append(new_row)

        return replace(self, rows=new_rows)

    def insert_row(self, row_idx: int) -> "Table":
        """
        Return a new Table with an empty row inserted at row_idx.
        Subsequent rows are shifted down.
        """
        new_rows = [list(r) for r in self.rows]

        # Determine width
        width = (
            len(self.headers) if self.headers else (len(new_rows[0]) if new_rows else 0)
        )
        if width == 0:
            width = 1  # Default to 1 column if table is empty

        new_row = [""] * width

        if row_idx < 0:
            row_idx = 0
        if row_idx > len(new_rows):
            row_idx = len(new_rows)

        new_rows.insert(row_idx, new_row)
        return replace(self, rows=new_rows)

    def insert_column(self, col_idx: int) -> "Table":
        """
        Return a new Table with an empty column inserted at col_idx.
        Subsequent columns are shifted right.
        """
        new_headers = list(self.headers) if self.headers else None

        if new_headers:
            if col_idx < 0:
                col_idx = 0
            if col_idx > len(new_headers):
                col_idx = len(new_headers)
            new_headers.insert(col_idx, "")

        new_alignments = None
        if self.alignments is not None:
            new_alignments = list(self.alignments)
            # Pad if needed before insertion?
            if col_idx > len(new_alignments):
                extension: list[AlignmentType] = ["default"] * (
                    col_idx - len(new_alignments)
                )
                new_alignments.extend(extension)
            new_alignments.insert(col_idx, "default")  # Default alignment

        new_rows = []
        for row in self.rows:
            new_row = list(row)
            # Ensure row is long enough before insertion logic?
            # Or just insert.
            # If col_idx is way past end, we might need padding?
            # Standard list.insert handles index > len -> append.
            current_len = len(new_row)
            target_idx = col_idx
            if target_idx > current_len:
                # Pad up to target
                new_row.extend([""] * (target_idx - current_len))
                target_idx = len(new_row)  # Append

            new_row.insert(target_idx, "")
            new_rows.append(new_row)

        return replace(
            self, headers=new_headers, rows=new_rows, alignments=new_alignments
        )


@dataclass(frozen=True)
class Sheet:
    """
    Represents a single sheet containing tables.

    Attributes:
        name (str): Name of the sheet.
        tables (list[Table]): List of tables contained in this sheet.
        metadata (dict[str, Any] | None): Arbitrary metadata (e.g. layout). Defaults to None.
    """

    name: str
    tables: list[Table]
    metadata: dict[str, Any] | None = None

    def __post_init__(self):
        if self.metadata is None:
            # Hack to allow default value for mutable type in frozen dataclass
            object.__setattr__(self, "metadata", {})

    @property
    def json(self) -> SheetJSON:
        """
        Returns a JSON-compatible dictionary representation of the sheet.

        Returns:
            SheetJSON: A dictionary containing the sheet data.
        """
        return {
            "name": self.name,
            "tables": [t.json for t in self.tables],
            "metadata": self.metadata if self.metadata is not None else {},
        }

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
        metadata (dict[str, Any] | None): Arbitrary metadata. Defaults to None.
    """

    sheets: list[Sheet]
    metadata: dict[str, Any] | None = None

    def __post_init__(self):
        if self.metadata is None:
            # Hack to allow default value for mutable type in frozen dataclass
            object.__setattr__(self, "metadata", {})

    @property
    def json(self) -> WorkbookJSON:
        """
        Returns a JSON-compatible dictionary representation of the workbook.

        Returns:
            WorkbookJSON: A dictionary containing the workbook data.
        """
        return {
            "sheets": [s.json for s in self.sheets],
            "metadata": self.metadata if self.metadata is not None else {},
        }

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

    def add_sheet(self, name: str) -> "Workbook":
        """
        Return a new Workbook with a new sheet added.
        """
        # Create new sheet with one empty table as default
        new_table = Table(headers=["A", "B", "C"], rows=[["", "", ""]])
        new_sheet = Sheet(name=name, tables=[new_table])

        new_sheets = list(self.sheets)
        new_sheets.append(new_sheet)

        return replace(self, sheets=new_sheets)

    def delete_sheet(self, index: int) -> "Workbook":
        """
        Return a new Workbook with the sheet at index removed.
        """
        if index < 0 or index >= len(self.sheets):
            raise IndexError("Sheet index out of range")

        new_sheets = list(self.sheets)
        new_sheets.pop(index)

        return replace(self, sheets=new_sheets)
