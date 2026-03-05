import json
from typing import TYPE_CHECKING

from .schemas import DEFAULT_SCHEMA, MultiTableParsingSchema, ParsingSchema
from .yaml_parser import generate_yaml_frontmatter

if TYPE_CHECKING:
    from .models import Sheet, Table, Workbook


def generate_table_markdown(
    table: "Table", schema: ParsingSchema = DEFAULT_SCHEMA
) -> str:
    """
    Generates a Markdown string representation of the table.

    Args:
        table: The Table object.
        schema (ParsingSchema, optional): Configuration for formatting.

    Returns:
        str: The Markdown string.
    """
    lines = []

    # Handle metadata (name and description) if MultiTableParsingSchema
    if isinstance(schema, MultiTableParsingSchema):
        table_level = schema.table_header_level
        if table.name and table_level is not None:
            lines.append(f"{'#' * table_level} {table.name}")
            lines.append("")  # Empty line after name

        if table.description and schema.capture_description:
            lines.append(table.description)
            lines.append("")  # Empty line after description

    # Build table

    pipe = schema.column_separator or "|"

    def _prepare_cell(cell: str) -> str:
        """Prepare cell for markdown generation."""
        if schema.convert_br_to_newline and "\n" in cell:
            return cell.replace("\n", "<br>")
        return cell

    def _format_cell(cell: str) -> str:
        """Format cell with surrounding spaces. Empty cells get single space."""
        if cell:
            return f" {cell} "
        return " "

    def _build_row(cells: list[str]) -> str:
        """Build a pipe-delimited row from formatted cells."""
        formatted = [_format_cell(c) for c in cells]
        row_str = pipe.join(formatted)
        if schema.require_outer_pipes:
            row_str = f"{pipe}{row_str}{pipe}"
        return row_str

    # Headers
    if table.headers:
        processed_headers = [_prepare_cell(h) for h in table.headers]
        lines.append(_build_row(processed_headers))

        # Separator row
        separator_cells = []
        separator_char = schema.header_separator_char or "-"
        for i, _ in enumerate(table.headers):
            alignment = "default"
            if table.alignments and i < len(table.alignments):
                # Ensure we handle potentially None values if list has gaps (unlikely by design but safe)
                alignment = table.alignments[i] or "default"

            # Construct separator cell based on alignment
            # Use 3 hyphens as base
            if alignment == "left":
                cell = ":" + separator_char * 3
            elif alignment == "right":
                cell = separator_char * 3 + ":"
            elif alignment == "center":
                cell = ":" + separator_char * 3 + ":"
            else:
                # default
                cell = separator_char * 3

            separator_cells.append(cell)

        lines.append(_build_row(separator_cells))

    # Rows
    for row in table.rows:
        processed_row = [_prepare_cell(cell) for cell in row]
        lines.append(_build_row(processed_row))

    # Append Metadata if present
    if table.metadata and "visual" in table.metadata:
        metadata_json = json.dumps(table.metadata["visual"], ensure_ascii=False)
        comment = f"<!-- md-spreadsheet-table-metadata: {metadata_json} -->"
        lines.append("")
        lines.append(comment)

    return "\n".join(lines)


def generate_sheet_markdown(
    sheet: "Sheet", schema: ParsingSchema = DEFAULT_SCHEMA
) -> str:
    """
    Generates a Markdown string representation of the sheet.

    For doc sheets (type="doc"), outputs the content directly.
    For table sheets (type="table"), outputs table markdown.

    Args:
        sheet: The Sheet object.
        schema (ParsingSchema, optional): Configuration for formatting.

    Returns:
        str: The Markdown string.
    """
    lines = []

    if isinstance(schema, MultiTableParsingSchema):
        sheet_level = schema.sheet_header_level or 2
        lines.append(f"{'#' * sheet_level} {sheet.name}")
        lines.append("")

    # For doc sheets, output content directly
    if sheet.sheet_type == "doc" and sheet.content is not None:
        lines.append(sheet.content)
    else:
        # Table sheet: output tables
        for i, table in enumerate(sheet.tables):
            lines.append(generate_table_markdown(table, schema))
            if i < len(sheet.tables) - 1:
                lines.append("")  # Empty line between tables

    # Append Sheet Metadata if present (at the end)
    if isinstance(schema, MultiTableParsingSchema) and sheet.metadata:
        lines.append("")
        metadata_json = json.dumps(sheet.metadata, ensure_ascii=False)
        comment = f"<!-- md-spreadsheet-sheet-metadata: {metadata_json} -->"
        lines.append(comment)

    return "\n".join(lines)


# Keys in workbook.metadata that are used for round-trip control
# and should not be serialized into the HTML comment
_METADATA_INTERNAL_KEYS = {"header_type", "frontmatter"}


def generate_workbook_markdown(
    workbook: "Workbook", schema: MultiTableParsingSchema
) -> str:
    """
    Generates a Markdown string representation of the workbook.

    Args:
        workbook: The Workbook object.
        schema (MultiTableParsingSchema): Configuration for formatting.

    Returns:
        str: The Markdown string.
    """
    lines = []
    metadata = workbook.metadata or {}
    is_frontmatter = metadata.get("header_type") == "frontmatter"

    if is_frontmatter:
        # Output YAML frontmatter block
        frontmatter_data = metadata.get("frontmatter", {})
        if frontmatter_data:
            lines.append(generate_yaml_frontmatter(frontmatter_data))
            lines.append("")
    elif schema.root_marker:
        lines.append(schema.root_marker)
        lines.append("")
    else:
        # Default: generate root marker from workbook name
        root_marker_level = (
            schema.sheet_header_level - 1 if schema.sheet_header_level else 1
        )
        lines.append(f"{'#' * root_marker_level} {workbook.name}")
        lines.append("")

    if workbook.root_content:
        lines.append(workbook.root_content)
        lines.append("")

    for i, sheet in enumerate(workbook.sheets):
        lines.append(generate_sheet_markdown(sheet, schema))
        if i < len(workbook.sheets) - 1:
            lines.append("")  # Empty line between sheets

    # Append Workbook Metadata if present (excluding internal keys)
    comment_metadata = {
        k: v for k, v in metadata.items() if k not in _METADATA_INTERNAL_KEYS
    }
    if comment_metadata:
        # Ensure separation from last sheet
        if lines and lines[-1] != "":
            lines.append("")

        metadata_json = json.dumps(comment_metadata, ensure_ascii=False)
        comment = f"<!-- md-spreadsheet-workbook-metadata: {metadata_json} -->"
        lines.append(comment)

    return "\n".join(lines)
