import json
from typing import TYPE_CHECKING

from .schemas import DEFAULT_SCHEMA, MultiTableParsingSchema, ParsingSchema

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
        if table.name and schema.table_header_level is not None:
            lines.append(f"{'#' * schema.table_header_level} {table.name}")
            lines.append("")  # Empty line after name

        if table.description and schema.capture_description:
            lines.append(table.description)
            lines.append("")  # Empty line after description

    # Build table
    sep = f" {schema.column_separator} "

    def _prepare_cell(cell: str) -> str:
        """Prepare cell for markdown generation."""
        if schema.convert_br_to_newline and "\n" in cell:
            return cell.replace("\n", "<br>")
        return cell

    # Headers
    if table.headers:
        # Add outer pipes if required
        processed_headers = [_prepare_cell(h) for h in table.headers]
        header_row = sep.join(processed_headers)
        if schema.require_outer_pipes:
            header_row = (
                f"{schema.column_separator} {header_row} {schema.column_separator}"
            )
        lines.append(header_row)

        # Separator row
        separator_cells = []
        for i, _ in enumerate(table.headers):
            alignment = "default"
            if table.alignments and i < len(table.alignments):
                # Ensure we handle potentially None values if list has gaps (unlikely by design but safe)
                alignment = table.alignments[i] or "default"

            # Construct separator cell based on alignment
            # Use 3 hyphens as base
            if alignment == "left":
                cell = ":" + schema.header_separator_char * 3
            elif alignment == "right":
                cell = schema.header_separator_char * 3 + ":"
            elif alignment == "center":
                cell = ":" + schema.header_separator_char * 3 + ":"
            else:
                # default
                cell = schema.header_separator_char * 3

            separator_cells.append(cell)

        separator_row = sep.join(separator_cells)
        if schema.require_outer_pipes:
            separator_row = (
                f"{schema.column_separator} {separator_row} {schema.column_separator}"
            )
        lines.append(separator_row)

    # Rows
    for row in table.rows:
        processed_row = [_prepare_cell(cell) for cell in row]
        row_str = sep.join(processed_row)
        if schema.require_outer_pipes:
            row_str = f"{schema.column_separator} {row_str} {schema.column_separator}"
        lines.append(row_str)

    # Append Metadata if present
    if table.metadata and "visual" in table.metadata:
        metadata_json = json.dumps(table.metadata["visual"])
        comment = f"<!-- md-spreadsheet-table-metadata: {metadata_json} -->"
        lines.append("")
        lines.append(comment)

    return "\n".join(lines)


def generate_sheet_markdown(
    sheet: "Sheet", schema: ParsingSchema = DEFAULT_SCHEMA
) -> str:
    """
    Generates a Markdown string representation of the sheet.

    Args:
        sheet: The Sheet object.
        schema (ParsingSchema, optional): Configuration for formatting.

    Returns:
        str: The Markdown string.
    """
    lines = []

    if isinstance(schema, MultiTableParsingSchema):
        lines.append(f"{'#' * schema.sheet_header_level} {sheet.name}")
        lines.append("")

    for i, table in enumerate(sheet.tables):
        lines.append(generate_table_markdown(table, schema))
        if i < len(sheet.tables) - 1:
            lines.append("")  # Empty line between tables

    # Append Sheet Metadata if present (at the end)
    if isinstance(schema, MultiTableParsingSchema) and sheet.metadata:
        lines.append("")
        metadata_json = json.dumps(sheet.metadata)
        comment = f"<!-- md-spreadsheet-sheet-metadata: {metadata_json} -->"
        lines.append(comment)

    return "\n".join(lines)


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

    if schema.root_marker:
        lines.append(schema.root_marker)
        lines.append("")

    for i, sheet in enumerate(workbook.sheets):
        lines.append(generate_sheet_markdown(sheet, schema))
        if i < len(workbook.sheets) - 1:
            lines.append("")  # Empty line between sheets

    # Append Workbook Metadata if present
    if workbook.metadata:
        # Ensure separation from last sheet
        if lines and lines[-1] != "":
            lines.append("")

        metadata_json = json.dumps(workbook.metadata)
        comment = f"<!-- md-spreadsheet-workbook-metadata: {metadata_json} -->"
        lines.append(comment)

    return "\n".join(lines)
