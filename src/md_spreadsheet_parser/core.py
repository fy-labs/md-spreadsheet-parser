import re
from dataclasses import replace

from .models import Table, Workbook, Sheet
from .schemas import ParsingSchema, MultiTableParsingSchema, DEFAULT_SCHEMA


def clean_cell(cell: str, schema: ParsingSchema) -> str:
    """
    Clean a cell value by stripping whitespace and unescaping the separator.
    """
    if schema.strip_whitespace:
        cell = cell.strip()

    if schema.convert_br_to_newline:
        # Replace <br>, <br/>, <br /> (case-insensitive) with \n
        cell = re.sub(r"<br\s*/?>", "\n", cell, flags=re.IGNORECASE)

    # Unescape the column separator (e.g. \| -> |)
    # We also need to handle \\ -> \
    # Simple replacement for now: replace \<sep> with <sep>
    if "\\" in cell:
        cell = cell.replace(f"\\{schema.column_separator}", schema.column_separator)

    return cell


def parse_row(line: str, schema: ParsingSchema) -> list[str] | None:
    """
    Parse a single line into a list of cell values.
    Handles escaped separators.
    """
    line = line.strip()
    if not line:
        return None

    # Use regex to split by separator, but ignore escaped separators.
    # Pattern: (?<!\\)SEPARATOR
    # We must escape the separator itself for regex usage.
    sep_pattern = re.escape(schema.column_separator)
    pattern = f"(?<!\\\\){sep_pattern}"

    parts = re.split(pattern, line)

    # Handle outer pipes if present
    # If the line starts/ends with a separator (and it wasn't escaped),
    # split will produce empty strings at start/end.
    if len(parts) > 1:
        if parts[0].strip() == "":
            parts = parts[1:]
        if parts and parts[-1].strip() == "":
            parts = parts[:-1]

    # Clean cells
    cleaned_parts = [clean_cell(part, schema) for part in parts]
    return cleaned_parts


def is_separator_row(row: list[str], schema: ParsingSchema) -> bool:
    """
    Check if a row is a separator row (e.g. |---|---|).
    """
    # A separator row typically contains only hyphens, colons, and spaces.
    # It must have at least one hyphen.
    for cell in row:
        # Remove expected chars
        cleaned = (
            cell.replace(schema.header_separator_char, "").replace(":", "").strip()
        )
        if cleaned:
            return False
        # Must contain at least one separator char (usually '-')
        if schema.header_separator_char not in cell:
            return False
    return True


def parse_table(markdown: str, schema: ParsingSchema = DEFAULT_SCHEMA) -> Table:
    """
    Parse a markdown table into a Table object.

    Args:
        markdown: The markdown string containing the table.
        schema: Configuration for parsing.

    Returns:
        Table object with headers and rows.
    """
    lines = markdown.strip().split("\n")
    headers: list[str] | None = None
    rows: list[list[str]] = []

    # Buffer for potential header row until we confirm it's a header with a separator
    potential_header: list[str] | None = None

    for line in lines:
        line = line.strip()
        if not line:
            continue

        parsed_row = parse_row(line, schema)

        if parsed_row is None:
            continue

        if headers is None and potential_header is not None:
            if is_separator_row(parsed_row, schema):
                headers = potential_header
                potential_header = None
                continue
            else:
                # Previous row was not a header, treat as data
                rows.append(potential_header)
                potential_header = parsed_row
        elif headers is None and potential_header is None:
            potential_header = parsed_row
        else:
            rows.append(parsed_row)

    if potential_header is not None:
        rows.append(potential_header)

    # Normalize rows to match header length
    if headers:
        header_len = len(headers)
        normalized_rows = []
        for row in rows:
            if len(row) < header_len:
                # Pad with empty strings
                row.extend([""] * (header_len - len(row)))
            elif len(row) > header_len:
                # Truncate
                row = row[:header_len]
            normalized_rows.append(row)
        rows = normalized_rows

    return Table(headers=headers, rows=rows, metadata={"schema_used": str(schema)})


def _extract_tables_simple(
    lines: list[str], schema: ParsingSchema, start_line_offset: int
) -> list[Table]:
    """
    Extract tables by splitting lines by blank lines.
    Used for content within a block or when no table header level is set.
    """
    tables: list[Table] = []
    current_block: list[str] = []
    block_start = 0

    for idx, line in enumerate(lines):
        if not line.strip():
            if current_block:
                # Process block
                block_text = "\n".join(current_block)
                if schema.column_separator in block_text:
                    table = parse_table(block_text, schema)
                    if table.rows or table.headers:
                        table = replace(
                            table,
                            start_line=start_line_offset + block_start,
                            end_line=start_line_offset + idx,
                        )
                        tables.append(table)
                current_block = []
            block_start = idx + 1
        else:
            if not current_block:
                block_start = idx
            current_block.append(line)

    # Last block
    if current_block:
        block_text = "\n".join(current_block)
        if schema.column_separator in block_text:
            table = parse_table(block_text, schema)
            if table.rows or table.headers:
                table = replace(
                    table,
                    start_line=start_line_offset + block_start,
                    end_line=start_line_offset + len(lines),
                )
                tables.append(table)

    return tables


def _extract_tables(
    text: str, schema: MultiTableParsingSchema, start_line_offset: int = 0
) -> list[Table]:
    """
    Extract tables from text.
    If table_header_level is set, splits by that header.
    Otherwise, splits by blank lines.
    """
    if schema.table_header_level is None:
        return _extract_tables_simple(text.split("\n"), schema, start_line_offset)

    # Split by table header
    header_prefix = "#" * schema.table_header_level + " "
    lines = text.split("\n")
    tables: list[Table] = []

    current_table_lines: list[str] = []
    current_table_name: str | None = None
    current_description_lines: list[str] = []
    current_block_start_line = start_line_offset

    def process_table_block(end_line_idx: int):
        if not current_table_lines:
            return
            
        # Try to separate description from table content
        # Simple heuristic: find the first line that looks like a table row
        table_start_idx = -1
        for idx, line in enumerate(current_table_lines):
            if schema.column_separator in line:
                table_start_idx = idx
                break

        if table_start_idx != -1:
            # Description is everything before table start
            desc_lines = (
                current_description_lines
                + current_table_lines[:table_start_idx]
            )
            
            # Content is everything after (and including) table start
            content_lines = current_table_lines[table_start_idx:]
            
            # Logic adjustment:
            # If named, content starts at header_line + 1.
            # If unnamed, content starts at current_block_start_line.
            offset_correction = 1 if current_table_name else 0
            
            # Absolute start line of the content part
            abs_content_start = start_line_offset + current_block_start_line + offset_correction + table_start_idx

            # Parse tables from the content lines
            block_tables = _extract_tables_simple(content_lines, schema, abs_content_start)

            if block_tables:
                # The first table found gets the name and description
                first_table = block_tables[0]
                
                description = (
                    "\n".join(line.strip() for line in desc_lines if line.strip())
                    if schema.capture_description
                    else None
                )
                if description == "":
                    description = None

                first_table = replace(
                    first_table,
                    name=current_table_name,
                    description=description
                )
                block_tables[0] = first_table
                
                # Append all found tables
                tables.extend(block_tables)

    for idx, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith(header_prefix):
            process_table_block(idx)
            current_table_name = stripped[len(header_prefix) :].strip()
            current_table_lines = []
            current_description_lines = []
            current_block_start_line = idx
        else:
            # Accumulate lines regardless of whether we have a name
            current_table_lines.append(line)

    process_table_block(len(lines))

    return tables


def parse_sheet(
    markdown: str, name: str, schema: MultiTableParsingSchema, start_line_offset: int = 0
) -> Sheet:
    """
    Parse a sheet (section) containing one or more tables.
    """
    tables = _extract_tables(markdown, schema, start_line_offset)
    return Sheet(name=name, tables=tables)


def parse_workbook(
    markdown: str, schema: MultiTableParsingSchema = MultiTableParsingSchema()
) -> Workbook:
    """
    Parse a markdown document into a Workbook.
    """
    lines = markdown.split("\n")
    sheets: list[Sheet] = []

    # Find root marker
    start_index = 0
    if schema.root_marker:
        found = False
        for i, line in enumerate(lines):
            if line.strip() == schema.root_marker:
                start_index = i + 1
                found = True
                break
        if not found:
            return Workbook(sheets=[])

    # Split by sheet headers
    header_prefix = "#" * schema.sheet_header_level + " "

    current_sheet_name: str | None = None
    current_sheet_lines: list[str] = []
    current_sheet_start_line = start_index

    for idx, line in enumerate(lines[start_index:], start=start_index):
        stripped = line.strip()

        # Check if line is a header
        if stripped.startswith("#"):
            # Count header level
            level = 0
            for char in stripped:
                if char == "#":
                    level += 1
                else:
                    break

            # If header level is less than sheet_header_level (e.g. # vs ##),
            # it indicates a higher-level section, so we stop parsing the workbook.
            if level < schema.sheet_header_level:
                break

        if stripped.startswith(header_prefix):
            if current_sheet_name:
                sheet_content = "\n".join(current_sheet_lines)
                # The content starts at current_sheet_start_line + 1 (header line)
                # Wait, current_sheet_lines collected lines AFTER the header.
                # So the offset for content is current_sheet_start_line + 1.
                sheets.append(
                    parse_sheet(
                        sheet_content,
                        current_sheet_name,
                        schema,
                        start_line_offset=current_sheet_start_line + 1,
                    )
                )

            current_sheet_name = stripped[len(header_prefix) :].strip()
            current_sheet_lines = []
            current_sheet_start_line = idx
        else:
            if current_sheet_name:
                current_sheet_lines.append(line)

    if current_sheet_name:
        sheet_content = "\n".join(current_sheet_lines)
        sheets.append(
            parse_sheet(
                sheet_content,
                current_sheet_name,
                schema,
                start_line_offset=current_sheet_start_line + 1,
            )
        )

    return Workbook(sheets=sheets)


def scan_tables(
    markdown: str, schema: MultiTableParsingSchema | None = None
) -> list[Table]:
    """
    Scan a markdown document for all tables, ignoring sheet structure.

    Args:
        markdown: The markdown text.
        schema: Optional schema. If None, uses default MultiTableParsingSchema.

    Returns:
    """
    if schema is None:
        schema = MultiTableParsingSchema()

    return _extract_tables(markdown, schema)


from typing import Union, TextIO
from pathlib import Path


def _read_content(source: Union[str, Path, TextIO]) -> str:
    """Helper to read content from file path or file object."""
    if isinstance(source, (str, Path)):
        with open(source, "r", encoding="utf-8") as f:
            return f.read()
    if hasattr(source, "read"):
        return source.read()
    raise ValueError(f"Invalid source type: {type(source)}")


def parse_table_from_file(
    source: Union[str, Path, TextIO], schema: ParsingSchema = DEFAULT_SCHEMA
) -> Table:
    """
    Parse a markdown table from a file.
    
    Args:
        source: File path (str/Path) or file-like object.
        schema: Parsing configuration.
    """
    content = _read_content(source)
    return parse_table(content, schema)


def parse_workbook_from_file(
    source: Union[str, Path, TextIO], 
    schema: MultiTableParsingSchema = MultiTableParsingSchema()
) -> Workbook:
    """
    Parse a markdown workbook from a file.
    
    Args:
        source: File path (str/Path) or file-like object.
        schema: Parsing configuration.
    """
    content = _read_content(source)
    return parse_workbook(content, schema)


def scan_tables_from_file(
    source: Union[str, Path, TextIO], 
    schema: MultiTableParsingSchema | None = None
) -> list[Table]:
    """
    Scan a markdown file for all tables.
    
    Args:
        source: File path (str/Path) or file-like object.
        schema: Optional schema.
    """
    content = _read_content(source)
    return scan_tables(content, schema)


from typing import Iterator, Iterable

def _iter_lines(source: Union[str, Path, TextIO, Iterable[str]]) -> Iterator[str]:
    """Helper to iterate lines from various sources."""
    if isinstance(source, (str, Path)):
        # If it's a file path, valid file
        with open(source, "r", encoding="utf-8") as f:
            yield from f
    elif hasattr(source, "read") or isinstance(source, Iterable):
        # File object or list of strings
        # If it's a file object, iterating it yields lines
        for line in source:
            yield line
    else:
        raise ValueError(f"Invalid source type for iteration: {type(source)}")


def scan_tables_iter(
    source: Union[str, Path, TextIO, Iterable[str]], 
    schema: MultiTableParsingSchema | None = None
) -> Iterator[Table]:
    """
    Stream tables from a source (file path, file object, or iterable) one by one.
    This allows processing files larger than memory, provided that individual tables fit in memory.
    
    Args:
        source: File path, open file object, or iterable of strings.
        schema: Parsing configuration.
        
    Yields:
        Table objects found in the stream.
    """
    if schema is None:
        schema = MultiTableParsingSchema()

    header_prefix = None
    if schema.table_header_level is not None:
        header_prefix = "#" * schema.table_header_level + " "

    current_lines: list[str] = []
    current_name: str | None = None
    # We track line number manually for metadata
    current_line_idx = 0
    # Start of the current block
    block_start_line = 0

    def parse_and_yield(lines: list[str], name: str | None, start_offset: int) -> Iterator[Table]:
        if not lines:
            return
        
        # Check if block looks like a table (has separator)
        block_text = "".join(lines) # lines already contain \n usually from file iteration?
        # File iteration includes \n. strip() won't remove internal chars.
        # But _extract_tables splits by \n, so it gets lines without \n.
        # Let's normalize: join then internal logic splits? 
        # Or better: `lines` here are strings. If they have \n at end, we should probably strip it for logic consistency with parse_table?
        # parse_table does split('\n').
        
        if schema.column_separator not in block_text:
            return

        # Simple extraction logic similar to process_table_block
        # Note: We can't reuse _extract_tables because it expects full text.
        # We reuse parsing logic.
        
        # Split description vs table
        # We need list of lines stripped of newline for index finding
        stripped_lines = [l.rstrip("\n") for l in lines]
        
        table_start_idx = -1
        for idx, line in enumerate(stripped_lines):
            if schema.column_separator in line:
                table_start_idx = idx
                break
        
        if table_start_idx != -1:
            desc_lines = stripped_lines[:table_start_idx]
            table_lines = stripped_lines[table_start_idx:]
            
            table_text = "\n".join(table_lines)
            table = parse_table(table_text, schema)
            
            if table.rows or table.headers:
                description = None
                if schema.capture_description:
                    desc_text = "\n".join(d.strip() for d in desc_lines if d.strip())
                    if desc_text:
                        description = desc_text
                
                table = replace(
                    table,
                    name=name,
                    description=description,
                    start_line=start_offset + table_start_idx,
                    end_line=start_offset + len(lines)
                )
                yield table

    for line in _iter_lines(source):
        # normalize: file iter yields line with \n
        stripped_line = line.strip()
        
        is_header = header_prefix and stripped_line.startswith(header_prefix)
        is_block_end = (stripped_line == "") and (schema.table_header_level is None)
        # Actually, if we use headers, blank lines don't necessarily end the *named* block,
        # but in `_extract_tables`, we accumulate lines until next header.
        # But `_extract_tables` THEN splits that block by blank lines (via _extract_tables_simple).
        # So essentially: blank line ALWAYS ends a *Table*, but maybe not the *Section*.
        # For infinite streaming, we should yield as soon as a table ends (blank line).
        
        if is_header:
            # New section starts. Yield previous buffer if any.
            yield from parse_and_yield(current_lines, current_name, block_start_line)
            
            current_name = stripped_line[len(header_prefix):].strip()
            current_lines = []
            block_start_line = current_line_idx
            
        elif stripped_line == "":
            # Blank line.
            # If we are strictly header-based, blank lines might separate tables within same section?
            # Yes. So we should assume blank line ends a table.
            # But we must persist `current_name` across blank lines until next header.
            yield from parse_and_yield(current_lines, current_name, block_start_line)
            current_lines = []
            # block_start_line for NEXT block will be current_line_idx + 1
            block_start_line = current_line_idx + 1
            
        else:
            current_lines.append(line)
            
        current_line_idx += 1

    # End of stream
    yield from parse_and_yield(current_lines, current_name, block_start_line)
