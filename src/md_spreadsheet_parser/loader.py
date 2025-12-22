from typing import Union, TextIO, Iterator, Iterable
from pathlib import Path
from dataclasses import replace

from .models import Table, Workbook
from .schemas import ParsingSchema, MultiTableParsingSchema, DEFAULT_SCHEMA
from .parsing import parse_table, parse_workbook, scan_tables


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
    schema: MultiTableParsingSchema = MultiTableParsingSchema(),
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
    source: Union[str, Path, TextIO], schema: MultiTableParsingSchema | None = None
) -> list[Table]:
    """
    Scan a markdown file for all tables.

    Args:
        source: File path (str/Path) or file-like object.
        schema: Optional schema.
    """
    content = _read_content(source)
    return scan_tables(content, schema)


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
    schema: MultiTableParsingSchema | None = None,
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

    def parse_and_yield(
        lines: list[str], name: str | None, start_offset: int
    ) -> Iterator[Table]:
        if not lines:
            return

        # Check if block looks like a table (has separator)
        block_text = "".join(lines)

        if schema.column_separator not in block_text:
            return

        # Simple extraction logic similar to process_table_block
        # We reuse parsing logic.

        # Split description vs table
        # We need list of lines stripped of newline for index finding
        stripped_lines = [line_val.rstrip("\n") for line_val in lines]

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
                    end_line=start_offset + len(lines),
                )
                yield table

    for line in _iter_lines(source):
        # normalize: file iter yields line with \n
        stripped_line = line.strip()

        is_header = header_prefix and stripped_line.startswith(header_prefix)

        if is_header:
            # New section starts. Yield previous buffer if any.
            yield from parse_and_yield(current_lines, current_name, block_start_line)

            assert header_prefix is not None
            current_name = stripped_line[len(header_prefix) :].strip()
            current_lines = []
            block_start_line = current_line_idx

        elif stripped_line == "":
            # Blank line.
            yield from parse_and_yield(current_lines, current_name, block_start_line)
            current_lines = []
            # block_start_line for NEXT block will be current_line_idx + 1
            block_start_line = current_line_idx + 1

        else:
            current_lines.append(line)

        current_line_idx += 1

    # End of stream
    yield from parse_and_yield(current_lines, current_name, block_start_line)
