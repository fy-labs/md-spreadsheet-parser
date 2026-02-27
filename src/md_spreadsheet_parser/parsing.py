import json
import re
from dataclasses import replace
from typing import Any

from .models import AlignmentType, Sheet, Table, Workbook
from .schemas import DEFAULT_SCHEMA, MultiTableParsingSchema, ParsingSchema
from .yaml_parser import extract_frontmatter, parse_yaml_frontmatter


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
    col_sep = schema.column_separator or "|"
    if "\\" in cell:
        cell = cell.replace(f"\\{col_sep}", col_sep)

    return cell

    return cell


def split_row_gfm(line: str, separator: str) -> list[str]:
    """
    Split a line by separator, respecting GFM rules:
    - Ignore separators inside inline code (backticks).
    - Ignore escaped separators.
    """
    parts: list[str] = []
    current_part: list[str] = []
    in_code = False
    i = 0
    n = len(line)

    while i < n:
        char = line[i]

        if char == "\\":
            # Escape character
            # If we are NOT in code, this might be escaping the separator.
            # We keep the backslash for clean_cell to handle (e.g. \| -> |).
            # But we must treat the next specific char as literal for splitting purposes.
            current_part.append(char)
            if i + 1 < n:
                # Add the next char unconditionally (skip separator check for it)
                current_part.append(line[i + 1])
                i += 2
                continue
            else:
                # Trailing backslash
                i += 1
                continue

        if char == "`":
            in_code = not in_code

        if char == separator and not in_code:
            # Found a valid separator
            parts.append("".join(current_part))
            current_part = []
        else:
            current_part.append(char)

        i += 1

    # Append the last part
    parts.append("".join(current_part))
    return parts


def parse_row(line: str, schema: ParsingSchema) -> list[str] | None:
    """
    Parse a single line into a list of cell values.
    Handles escaped separators and GFM validation (pipes in code).
    """
    line = line.strip()
    if not line:
        return None

    # Use state-aware splitter instead of regex
    parts = split_row_gfm(line, schema.column_separator)

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


def parse_separator_row(
    row: list[str], schema: ParsingSchema
) -> list[AlignmentType] | None:
    """
    Check if a row is a separator row. If so, return the list of alignments.
    Returns None if it is not a separator row.
    """
    alignments: list[AlignmentType] = []
    is_separator = True

    for cell in row:
        cell = cell.strip()
        # Verify it resembles a separator (---, :---, :---:, ---:)
        # Must contain at least one separator char
        if schema.header_separator_char not in cell:
            is_separator = False
            break

        # Remove expected chars to check validity
        cleaned = (
            cell.replace(schema.header_separator_char, "").replace(":", "").strip()
        )
        if cleaned:
            # Contains unexpected characters
            is_separator = False
            break

        # Determine alignment
        starts_col = cell.startswith(":")
        ends_col = cell.endswith(":")

        if starts_col and ends_col:
            alignments.append("center")
        elif ends_col:
            alignments.append("right")
        elif starts_col:
            alignments.append("left")
        else:
            alignments.append("default")

    if is_separator:
        return alignments
    return None


def is_separator_row(row: list[str], schema: ParsingSchema) -> bool:
    """
    Deprecated: wrapper around parse_separator_row for backward compatibility if needed,
    or just refactor usage.
    """
    return parse_separator_row(row, schema) is not None


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
    alignments: list[AlignmentType] | None = None
    potential_header: list[str] | None = None
    visual_metadata: dict | None = None

    # Buffer for potential header row until we confirm it's a header with a separator
    potential_header: list[str] | None = None

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Check for metadata comment
        metadata_match = re.match(
            r"^<!-- md-spreadsheet-table-metadata: (.*) -->$", line
        )
        if metadata_match:
            try:
                json_content = metadata_match.group(1)
                visual_metadata = json.loads(json_content)
                continue
            except json.JSONDecodeError:
                # If invalid JSON, treat as normal text/comment (or ignore?)
                # For robustness, we ignore it as metadata but let parse_row handle it or skip?
                # Usually comments are ignored by parse_row if they don't look like tables?
                # parse_row will likely return ["<!-- ... -->"].
                # If we want to hide it from table data, we should continue here even if error?
                # User constraint: "if user manually edits... handle gracefully".
                # Let's log/ignore and continue, effectively stripping bad metadata lines from table data.
                continue

        parsed_row = parse_row(line, schema)

        if parsed_row is None:
            continue

        if headers is None and potential_header is not None:
            detected_alignments = parse_separator_row(parsed_row, schema)
            if detected_alignments is not None:
                headers = potential_header
                alignments: list[AlignmentType] | None = detected_alignments
                potential_header = None
                continue
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

    metadata: dict[str, Any] = {"schema_used": str(schema)}
    if visual_metadata:
        metadata["visual"] = visual_metadata

    return Table(headers=headers, rows=rows, metadata=metadata, alignments=alignments)


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
                if (
                    schema.column_separator in block_text
                    or "<!-- md-spreadsheet-table-metadata:" in block_text
                ):
                    table = parse_table(block_text, schema)
                    if table.rows or table.headers:
                        table = replace(
                            table,
                            start_line=start_line_offset + block_start,
                            end_line=start_line_offset + idx,
                        )
                        tables.append(table)
                    elif table.metadata and "visual" in table.metadata and tables:
                        last_table = tables[-1]
                        last_metadata = last_table.metadata or {}
                        current_vis = last_metadata.get("visual", {})
                        new_vis = current_vis.copy()
                        new_vis.update(table.metadata["visual"])

                        updated_md = last_metadata.copy()
                        updated_md["visual"] = new_vis

                        tables[-1] = replace(last_table, metadata=updated_md)
                current_block = []
                # Tables that are only metadata (and no previous table) are ignored (orphan)
            block_start = idx + 1
        else:
            if not current_block:
                block_start = idx
            current_block.append(line)

    # Last block
    if current_block:
        block_text = "\n".join(current_block)
        if (
            schema.column_separator in block_text
            or "<!-- md-spreadsheet-table-metadata:" in block_text
        ):
            table = parse_table(block_text, schema)
            if table.rows or table.headers:
                table = replace(
                    table,
                    start_line=start_line_offset + block_start,
                    end_line=start_line_offset + len(lines),
                )
                tables.append(table)
            elif table.metadata and "visual" in table.metadata and tables:
                last_table = tables[-1]
                last_metadata = last_table.metadata or {}
                current_vis = last_metadata.get("visual", {})
                new_vis = current_vis.copy()
                new_vis.update(table.metadata["visual"])

                updated_md = last_metadata.copy()
                updated_md["visual"] = new_vis

                tables[-1] = replace(last_table, metadata=updated_md)

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
                current_description_lines + current_table_lines[:table_start_idx]
            )

            # Content is everything after (and including) table start
            content_lines = current_table_lines[table_start_idx:]

            # Logic adjustment:
            # If named, content starts at header_line + 1.
            # If unnamed, content starts at current_block_start_line.
            offset_correction = 1 if current_table_name else 0

            # Absolute start line of the content part
            abs_content_start = (
                start_line_offset
                + current_block_start_line
                + offset_correction
                + table_start_idx
            )

            # Parse tables from the content lines
            block_tables = _extract_tables_simple(
                content_lines, schema, abs_content_start
            )

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
                    first_table, name=current_table_name, description=description
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
    markdown: str,
    name: str,
    schema: MultiTableParsingSchema,
    start_line_offset: int = 0,
) -> Sheet:
    """
    Parse a sheet (section) containing one or more tables.

    If the section contains valid tables, sheet_type="table" and content=None.
    If no tables are found, sheet_type="doc" and content stores the raw markdown.
    """
    metadata: dict[str, Any] | None = None

    # Scan for sheet metadata
    # We prioritize the first match if multiple exist (though usually only one)
    metadata_match = re.search(
        r"^<!-- md-spreadsheet-sheet-metadata: (.*) -->$", markdown, re.MULTILINE
    )
    if metadata_match:
        try:
            metadata = json.loads(metadata_match.group(1))
        except json.JSONDecodeError:
            pass  # Ignore invalid JSON

    tables = _extract_tables(markdown, schema, start_line_offset)

    # Determine sheet type based on whether tables were found
    if tables:
        # Table sheet: store tables but not raw content
        return Sheet(
            name=name,
            tables=tables,
            sheet_type="table",
            content=None,
            metadata=metadata,
        )
    else:
        # Doc sheet: no tables, store the raw markdown content
        return Sheet(
            name=name,
            tables=[],
            sheet_type="doc",
            content=markdown.rstrip() if markdown.strip() else None,
            metadata=metadata,
        )


def parse_workbook(
    markdown: str, schema: MultiTableParsingSchema = MultiTableParsingSchema()
) -> Workbook:
    """
    Parse a markdown document into a Workbook.

    When schema.root_marker is None, auto-detection is used:
    1. If a single H1 header exists, it becomes the Workbook.
    2. If md-spreadsheet metadata comment exists, the H1 containing it becomes Workbook.
    3. Fallback to searching for "# Tables" or "# Workbook".
    4. If not found, return empty Workbook.

    When root_marker/sheet_header_level/table_header_level are None,
    they are auto-calculated from the detected workbook level.
    """
    frontmatter_text, remaining_markdown = extract_frontmatter(markdown)
    frontmatter_metadata: dict[str, Any] = {}
    if frontmatter_text is not None:
        frontmatter_metadata = parse_yaml_frontmatter(frontmatter_text)

    # If the frontmatter does not have a title, it does not constitute a Workbook,
    # and its metadata should not be implicitly merged into subsequent Workbooks.
    if "title" not in frontmatter_metadata:
        frontmatter_metadata = {}

    lines = remaining_markdown.split("\n")
    sheets: list[Sheet] = []
    metadata: dict[str, Any] | None = None

    # Check for Workbook metadata at the end of the file
    # Scan for Workbook metadata anywhere in the file
    # We filter it out from the lines so it doesn't interfere with sheet content
    filtered_lines: list[str] = []
    wb_metadata_pattern = re.compile(
        r"^<!-- md-spreadsheet-workbook-metadata: (.*) -->$"
    )

    for line in lines:
        stripped = line.strip()
        match = wb_metadata_pattern.match(stripped)
        if match:
            try:
                metadata = json.loads(match.group(1))
            except json.JSONDecodeError:
                pass
            # Skip adding this line to filtered_lines
        else:
            filtered_lines.append(line)

    lines = filtered_lines

    # Isolate frontmatter in sub-dict for round-trip fidelity
    if frontmatter_metadata:
        if metadata is None:
            metadata = {}
        metadata["header_type"] = "frontmatter"
        metadata["frontmatter"] = frontmatter_metadata

    # Determine root marker and header levels
    root_marker = schema.root_marker
    workbook_name = "Workbook"
    workbook_level = 1  # Default H1

    virtual_root = False
    if root_marker is None and "title" in frontmatter_metadata:
        title_val = str(frontmatter_metadata["title"]).strip()
        if title_val:
            root_marker = "# " + title_val
            workbook_name = title_val
            workbook_level = 1
            virtual_root = True

    if root_marker is None:
        # Auto-detection mode
        # Find all H1 headers (not in code blocks)
        h1_headers: list[tuple[int, str]] = []  # (line_index, header_text)
        in_code_block = False

        for i, line in enumerate(lines):
            stripped = line.strip()
            if stripped.startswith("```"):
                in_code_block = not in_code_block
            elif (
                not in_code_block
                and stripped.startswith("# ")
                and not stripped.startswith("## ")
            ):
                # This is an H1 header (starts with "# " but not "## ")
                header_text = stripped[2:].strip()
                h1_headers.append((i, header_text))

        if len(h1_headers) == 1:
            # Single H1: use it as workbook
            root_marker = h1_headers[0][1]
            workbook_name = root_marker
            root_marker = "# " + root_marker
            workbook_level = 1
        elif metadata is not None and len(h1_headers) > 0:
            # Step 3: If md-spreadsheet metadata exists, find the H1 that contains it
            # The metadata comment should be inside a section, so we find the H1
            # header that precedes the metadata comment location.
            # Since we already extracted metadata, we need to find which H1 section
            # contains it by re-scanning the original lines.

            # Re-scan original lines to find metadata line index
            original_lines = markdown.split("\n")
            metadata_line_idx = None
            for i, line in enumerate(original_lines):
                stripped = line.strip()
                if wb_metadata_pattern.match(stripped):
                    metadata_line_idx = i
                    break

            if metadata_line_idx is not None:
                # Find the H1 header that precedes this metadata line
                # Map original line indices to filtered line indices
                selected_h1 = None
                for line_idx, header_text in h1_headers:
                    # h1_headers contains indices in filtered_lines
                    # Need to find corresponding original index
                    # Actually, h1_headers was built from filtered_lines (after metadata removal)
                    # So we need to re-scan original to find H1 before metadata
                    pass

                # Simpler approach: scan original lines for H1 headers before metadata
                in_code_block = False
                for i in range(metadata_line_idx - 1, -1, -1):
                    stripped = original_lines[i].strip()
                    if stripped.startswith("```"):
                        in_code_block = not in_code_block
                    elif (
                        not in_code_block
                        and stripped.startswith("# ")
                        and not stripped.startswith("## ")
                    ):
                        # Found the H1 header that contains the metadata
                        header_text = stripped[2:].strip()
                        root_marker = "# " + header_text
                        workbook_name = header_text
                        workbook_level = 1
                        selected_h1 = header_text
                        break

                if selected_h1 is None:
                    # Metadata exists but no H1 before it - use first H1
                    if h1_headers:
                        root_marker = h1_headers[0][1]
                        workbook_name = root_marker
                        root_marker = "# " + root_marker
                        workbook_level = 1
            else:
                # Shouldn't happen since metadata was found
                pass

        if root_marker is None:
            # Multiple or no H1: fallback to "# Tables" or "# Workbook"
            in_code_block = False
            for i, line in enumerate(lines):
                stripped = line.strip()
                if stripped.startswith("```"):
                    in_code_block = not in_code_block
                elif not in_code_block:
                    if stripped == "# Tables":
                        root_marker = "# Tables"
                        workbook_name = "Tables"
                        workbook_level = 1
                        break
                    elif stripped == "# Workbook":
                        root_marker = "# Workbook"
                        workbook_name = "Workbook"
                        workbook_level = 1
                        break
            if root_marker is None:
                # No workbook found
                return Workbook(sheets=[], name=workbook_name, metadata=metadata)
    else:
        # Explicit root_marker: extract name and level from it
        if root_marker.startswith("#"):
            level = 0
            for char in root_marker:
                if char == "#":
                    level += 1
                else:
                    break
            workbook_level = level
            workbook_name = root_marker[level:].strip()

    # Calculate header levels if not explicitly set
    # Only auto-calculate from workbook_level if root_marker was auto-detected
    # When root_marker is explicit, honor the explicit None values (meaning "no headers")
    root_marker_auto_detected = schema.root_marker is None

    if schema.sheet_header_level is not None:
        sheet_header_level = schema.sheet_header_level
    elif root_marker_auto_detected:
        sheet_header_level = workbook_level + 1
    else:
        # Explicit root_marker but no sheet_header_level: default to 2
        sheet_header_level = 2

    if schema.table_header_level is not None:
        table_header_level: int | None = schema.table_header_level
    elif root_marker_auto_detected:
        table_header_level = workbook_level + 2
    else:
        # Explicit root_marker but no table_header_level: keep as None (no table headers)
        table_header_level = None

    # Create an effective schema with resolved values
    effective_schema = replace(
        schema,
        root_marker=root_marker,
        sheet_header_level=sheet_header_level,
        table_header_level=table_header_level,
    )

    # Find root marker
    start_index = 0
    workbook_start_line: int | None = None
    in_code_block = False
    found = False

    if virtual_root:
        start_index = 0
        workbook_start_line = 0
        found = True
    else:
        for i, line in enumerate(lines):
            stripped = line.strip()
            if stripped.startswith("```"):
                in_code_block = not in_code_block

            if not in_code_block and stripped == root_marker:
                start_index = i + 1
                workbook_start_line = i
                found = True
                break

    if not found:
        return Workbook(sheets=[], name=workbook_name, metadata=metadata)

    # Split by sheet headers
    header_prefix = "#" * sheet_header_level + " "

    current_sheet_name: str | None = None
    current_sheet_lines: list[str] = []
    current_sheet_start_line = start_index

    # Reset code block state for the second pass
    # If we started after a root marker, check if that root marker line was just a marker.
    # We assume valid markdown structure where root marker is not inside a code block (handled above).
    in_code_block = False

    # Capture root content (text between workbook header and first sheet header)
    root_content_lines: list[str] = []

    # Track workbook section end line
    # If loop breaks due to another H1, end is line before that H1
    # Otherwise end is the last line of the file
    workbook_end_line: int | None = None

    for idx, line in enumerate(lines[start_index:], start=start_index):
        stripped = line.strip()

        if stripped.startswith("```"):
            in_code_block = not in_code_block

        if in_code_block:
            # Just collect lines if we are in a sheet or root content
            if current_sheet_name:
                current_sheet_lines.append(line)
            else:
                root_content_lines.append(line)
            workbook_end_line = idx + 1  # Track last line in section
            continue

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
            if level < sheet_header_level:
                # workbook_end_line is already set to last processed line
                break

            # If header match sheet_header_level, it's a new sheet
            if level == sheet_header_level and stripped.startswith(header_prefix):
                if current_sheet_name:
                    sheet_content = "\n".join(current_sheet_lines)
                    sheets.append(
                        parse_sheet(
                            sheet_content,
                            current_sheet_name,
                            effective_schema,
                            start_line_offset=current_sheet_start_line + 1,
                        )
                    )

                current_sheet_name = stripped[len(header_prefix) :].strip()
                current_sheet_lines = []
                current_sheet_start_line = idx
                workbook_end_line = idx + 1
                continue

        # Not a sheet header
        if current_sheet_name:
            current_sheet_lines.append(line)
        else:
            # We are in root content area (between Workbook header and first Sheet)
            root_content_lines.append(line)

        workbook_end_line = idx + 1  # Track last line processed (exclusive end)

    if current_sheet_name:
        sheet_content = "\n".join(current_sheet_lines)
        sheets.append(
            parse_sheet(
                sheet_content,
                current_sheet_name,
                effective_schema,
                start_line_offset=current_sheet_start_line + 1,
            )
        )

    # If no lines were processed, end_line is start_line + 1
    if workbook_end_line is None:
        workbook_end_line = (
            workbook_start_line + 1 if workbook_start_line is not None else None
        )

    root_content: str | None = None
    if root_content_lines:
        content = "\n".join(root_content_lines)
        if content.strip():
            root_content = content.strip()

    return Workbook(
        sheets=sheets,
        name=workbook_name,
        start_line=workbook_start_line,
        end_line=workbook_end_line,
        metadata=metadata,
        root_content=root_content,
    )


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
