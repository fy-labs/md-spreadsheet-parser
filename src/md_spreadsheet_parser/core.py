import re
from .schemas import (
    ParsingSchema,
    ParseResult,
    DEFAULT_SCHEMA,
    Sheet,
    Workbook,
    MultiTableParsingSchema,
    Table,
)


def clean_cell(cell_content: str, schema: ParsingSchema) -> str:
    """
    Cleans a single cell content based on the schema.

    Args:
        cell_content (str): The raw content of the cell.
        schema (ParsingSchema): The schema configuration.

    Returns:
        str: The cleaned cell content.
    """
    if schema.strip_whitespace:
        return cell_content.strip()
    return cell_content


def parse_row(line: str, schema: ParsingSchema) -> list[str]:
    """
    Parses a single line into a list of cell values.

    Args:
        line (str): The raw line string.
        schema (ParsingSchema): The schema configuration.

    Returns:
        list[str]: A list of cell values.
    """
    parts = line.split(schema.column_separator)

    if not parts:
        return []

    start_idx = 0
    end_idx = len(parts)

    if parts and parts[0].strip() == "":
        start_idx = 1

    if parts and len(parts) > 1 and parts[-1].strip() == "":
        end_idx = -1

    cleaned_parts = parts[start_idx:end_idx]

    return [clean_cell(p, schema) for p in cleaned_parts]


def is_separator_row(row_cells: list[str], schema: ParsingSchema) -> bool:
    """
    Determines if a parsed row is a header separator row (e.g. `---|---`).

    Args:
        row_cells (list[str]): The list of cell values in the row.
        schema (ParsingSchema): The schema configuration.

    Returns:
        bool: True if the row is a separator row, False otherwise.
    """
    if not row_cells:
        return False

    for cell in row_cells:
        content = cell.strip()
        if not content:
            continue

        valid_chars = set(schema.header_separator_char + ": ")
        if not set(content).issubset(valid_chars):
            return False

        if schema.header_separator_char not in content:
            return False

    return True


def parse_table(text: str, schema: ParsingSchema = DEFAULT_SCHEMA) -> ParseResult:
    """
    Parses a single block of text into a table.

    Args:
        text (str): The markdown text containing the table.
        schema (ParsingSchema, optional): The parsing configuration. Defaults to DEFAULT_SCHEMA.

    Returns:
        ParseResult: The parsed table result containing headers, rows, and metadata.

    Example:
        ```python
        markdown = "| A | B |\\n|---|---|\\n| 1 | 2 |"
        result = parse_table(markdown)
        print(result.headers) # ['A', 'B']
        ```
    """
    lines = text.strip().split("\n")

    headers: list[str] | None = None
    rows: list[list[str]] = []

    potential_header: list[str] | None = None

    for i, line in enumerate(lines):
        line = line.strip()
        if not line:
            continue

        parsed_row = parse_row(line, schema)

        if not parsed_row:
            continue

        if headers is None and potential_header is not None:
            if is_separator_row(parsed_row, schema):
                headers = potential_header
                potential_header = None
                continue
            else:
                rows.append(potential_header)
                potential_header = parsed_row
        elif headers is None and potential_header is None:
            potential_header = parsed_row
        else:
            rows.append(parsed_row)

    if potential_header is not None:
        rows.append(potential_header)

    return ParseResult(
        headers=headers, rows=rows, metadata={"schema_used": str(schema)}
    )


def _extract_tables(text: str, schema: ParsingSchema) -> list[Table]:
    """
    Helper function to extract tables from text based on schema configuration.
    Handles both header-based splitting (if table_header_level is set) and blank-line splitting.
    Internal use only.
    """
    tables: list[Table] = []

    # Check for MultiTableParsingSchema features
    table_header_level = getattr(schema, "table_header_level", None)
    capture_description = getattr(schema, "capture_description", False)

    if table_header_level is not None:
        # Split by table header
        header_prefix = "#" * table_header_level + " "

        lines = text.split("\n")
        current_table_name: str | None = None
        current_table_lines: list[str] = []

        def process_table_block(t_name: str, t_lines: list[str]):
            if not t_lines:
                return

            block_content = "\n".join(t_lines)
            description = None
            table_content = block_content

            if capture_description:
                # Find start of table (first line with pipe)
                block_lines = block_content.split("\n")
                table_start_idx = -1
                for idx, line in enumerate(block_lines):
                    if schema.column_separator in line:
                        table_start_idx = idx
                        break

                if table_start_idx > 0:
                    description = "\n".join(block_lines[:table_start_idx]).strip()
                    if not description:
                        description = None
                    table_content = "\n".join(block_lines[table_start_idx:])
                elif table_start_idx == 0:
                    description = None
                    table_content = block_content
                else:
                    # No table found
                    return

            parse_res = parse_table(table_content, schema)
            if parse_res.headers or parse_res.rows:
                tables.append(
                    Table(
                        name=t_name,
                        description=description,
                        headers=parse_res.headers,
                        rows=parse_res.rows,
                        metadata=parse_res.metadata,
                    )
                )

        for line in lines:
            stripped = line.strip()
            if stripped.startswith(header_prefix):
                if current_table_name is not None:
                    process_table_block(current_table_name, current_table_lines)

                current_table_name = stripped[len(header_prefix) :].strip()
                current_table_lines = []
            else:
                if current_table_name is not None:
                    current_table_lines.append(line)

        if current_table_name is not None:
            process_table_block(current_table_name, current_table_lines)

    else:
        # Legacy behavior: Split by blank lines
        blocks = re.split(r"\n\s*\n", text.strip())

        for block in blocks:
            if not block.strip():
                continue

            if schema.column_separator in block:
                parse_res = parse_table(block, schema)
                if parse_res.headers or parse_res.rows:
                    tables.append(
                        Table(
                            name=None,
                            description=None,
                            headers=parse_res.headers,
                            rows=parse_res.rows,
                            metadata=parse_res.metadata,
                        )
                    )
    return tables


def parse_sheet(text: str, name: str, schema: ParsingSchema = DEFAULT_SCHEMA) -> Sheet:
    """
    Parses a sheet content which may contain multiple tables.
    Supports splitting by table headers and extracting descriptions if configured in schema.

    Args:
        text (str): The content of the sheet.
        name (str): The name of the sheet.
        schema (ParsingSchema, optional): The parsing configuration. Defaults to DEFAULT_SCHEMA.

    Returns:
        Sheet: A Sheet object containing the parsed tables.
    """
    tables = _extract_tables(text, schema)
    return Sheet(name=name, tables=tables)


def parse_workbook(text: str, schema: MultiTableParsingSchema) -> Workbook:
    """
    Parses a full workbook text containing multiple sheets.
    Strictly requires the root_marker to be present. Content before the marker is ignored.

    Args:
        text (str): The full markdown text of the workbook.
        schema (MultiTableParsingSchema): The schema configuration including root marker and header levels.

    Returns:
        Workbook: A Workbook object containing the parsed sheets.

    Example:
        ```python
        markdown = "# Tables\\n## Sheet1\\n| A | B |\\n|---|---|\\n| 1 | 2 |"
        schema = MultiTableParsingSchema()
        workbook = parse_workbook(markdown, schema)
        print(workbook.sheets[0].name) # 'Sheet1'
        ```
    """
    # Find the root marker
    marker_index = text.find(schema.root_marker)
    if marker_index == -1:
        return Workbook(sheets=[])

    content_start = marker_index + len(schema.root_marker)
    content = text[content_start:]

    lines = content.split("\n")

    sheets: list[Sheet] = []
    current_sheet_name: str | None = None
    current_sheet_lines: list[str] = []

    header_prefix = "#" * schema.sheet_header_level + " "

    for line in lines:
        stripped = line.strip()
        if stripped.startswith(header_prefix):
            if current_sheet_name:
                sheet_content = "\n".join(current_sheet_lines)
                sheets.append(parse_sheet(sheet_content, current_sheet_name, schema))

            current_sheet_name = stripped[len(header_prefix) :].strip()
            current_sheet_lines = []
        else:
            if current_sheet_name:
                current_sheet_lines.append(line)

    if current_sheet_name:
        sheet_content = "\n".join(current_sheet_lines)
        sheets.append(parse_sheet(sheet_content, current_sheet_name, schema))

    return Workbook(sheets=sheets)


def scan_tables(text: str, schema: ParsingSchema = DEFAULT_SCHEMA) -> list[Table]:
    """
    Scans the entire text for tables.
    If schema is configured with `table_header_level`, it attempts to extract named tables and descriptions.
    Otherwise, it ignores hierarchy and headers, returning a flat list of all found tables.

    Args:
        text (str): The markdown text to scan.
        schema (ParsingSchema, optional): The parsing configuration. Defaults to DEFAULT_SCHEMA.

    Returns:
        list[Table]: A list of all found Table objects.

    Example:
        ```python
        markdown = "Some text...\\n| A | B |\\n|---|---|\\n| 1 | 2 |"
        tables = scan_tables(markdown)
        print(len(tables)) # 1
        ```
    """
    return _extract_tables(text, schema)
