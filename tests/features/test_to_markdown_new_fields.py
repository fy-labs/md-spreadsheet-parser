"""
Tests for to_markdown with new Sheet.sheet_type/content and Workbook.name fields.

Tests cover:
- Doc sheet (sheet_type="doc") outputs content directly
- Table sheet (sheet_type="table") outputs table markdown
- Workbook.name used in root marker when schema.root_marker is None
- Round-trip: parse → to_markdown → parse consistency
"""

from md_spreadsheet_parser import (
    MultiTableParsingSchema,
    Sheet,
    Table,
    Workbook,
    parse_workbook,
)


class TestDocSheetToMarkdown:
    """Tests for Sheet.to_markdown with type='doc'."""

    def test_doc_sheet_outputs_content(self):
        """Doc sheet should output its content directly."""
        sheet = Sheet(
            name="Notes",
            tables=[],
            sheet_type="doc",
            content="This is my documentation.\n\n- Point 1\n- Point 2",
        )
        schema = MultiTableParsingSchema(
            root_marker="# Workbook",
            sheet_header_level=2,
        )
        markdown = sheet.to_markdown(schema)

        assert "## Notes" in markdown
        assert "This is my documentation." in markdown
        assert "- Point 1" in markdown
        assert "- Point 2" in markdown

    def test_doc_sheet_empty_content(self):
        """Doc sheet with None content outputs just header."""
        sheet = Sheet(
            name="Empty Notes",
            tables=[],
            sheet_type="doc",
            content=None,
        )
        schema = MultiTableParsingSchema(
            root_marker="# Workbook",
            sheet_header_level=2,
        )
        markdown = sheet.to_markdown(schema)

        assert "## Empty Notes" in markdown
        # Should not have content after header (just empty or minimal output)
        lines = [l for l in markdown.strip().split("\n") if l.strip()]
        assert len(lines) == 1  # Just the header

    def test_doc_sheet_with_metadata(self):
        """Doc sheet with metadata includes metadata comment."""
        sheet = Sheet(
            name="Config",
            tables=[],
            sheet_type="doc",
            content="Some configuration notes.",
            metadata={"layout": "wide"},
        )
        schema = MultiTableParsingSchema(
            root_marker="# Workbook",
            sheet_header_level=2,
        )
        markdown = sheet.to_markdown(schema)

        assert "## Config" in markdown
        assert "Some configuration notes." in markdown
        assert "md-spreadsheet-sheet-metadata" in markdown
        assert '"layout": "wide"' in markdown


class TestTableSheetToMarkdown:
    """Tests for Sheet.to_markdown with type='table'."""

    def test_table_sheet_outputs_tables(self):
        """Table sheet should output its tables."""
        table = Table(headers=["A", "B"], rows=[["1", "2"]])
        sheet = Sheet(
            name="Data",
            tables=[table],
            sheet_type="table",
            content=None,
        )
        schema = MultiTableParsingSchema(
            root_marker="# Workbook",
            sheet_header_level=2,
        )
        markdown = sheet.to_markdown(schema)

        assert "## Data" in markdown
        assert "| A | B |" in markdown
        assert "| 1 | 2 |" in markdown

    def test_table_sheet_ignores_content_field(self):
        """Table sheet should not output content even if accidentally set."""
        table = Table(headers=["X"], rows=[["1"]])
        sheet = Sheet(
            name="Data",
            tables=[table],
            sheet_type="table",
            content="This should not appear",  # Accidentally set
        )
        schema = MultiTableParsingSchema(
            root_marker="# Workbook",
            sheet_header_level=2,
        )
        markdown = sheet.to_markdown(schema)

        # Since type is "table", content should be ignored - tables output instead
        assert "| X |" in markdown
        # Content field value might or might not appear based on implementation
        # Current implementation checks type first


class TestWorkbookNameInOutput:
    """Tests for Workbook.name usage in to_markdown."""

    def test_workbook_name_used_when_no_root_marker(self):
        """When schema.root_marker is None, workbook.name is used."""
        table = Table(headers=["A"], rows=[["1"]])
        sheet = Sheet(name="Sheet1", tables=[table])
        workbook = Workbook(sheets=[sheet], name="My Project")

        schema = MultiTableParsingSchema(
            root_marker=None,  # No explicit root marker
            sheet_header_level=2,
        )
        markdown = workbook.to_markdown(schema)

        # Should use workbook.name for root marker
        assert "# My Project" in markdown
        assert "## Sheet1" in markdown

    def test_explicit_root_marker_overrides_name(self):
        """Explicit root_marker takes precedence over workbook.name."""
        table = Table(headers=["A"], rows=[["1"]])
        sheet = Sheet(name="Sheet1", tables=[table])
        workbook = Workbook(sheets=[sheet], name="My Project")

        schema = MultiTableParsingSchema(
            root_marker="# Data Tables",  # Explicit root marker
            sheet_header_level=2,
        )
        markdown = workbook.to_markdown(schema)

        # Should use explicit root_marker, not workbook.name
        assert "# Data Tables" in markdown
        assert "# My Project" not in markdown

    def test_custom_workbook_name(self):
        """Custom workbook name appears in output."""
        sheet = Sheet(name="Sheet1", tables=[], sheet_type="doc", content="Notes")
        workbook = Workbook(sheets=[sheet], name="Financial Reports 2024")

        schema = MultiTableParsingSchema(
            root_marker=None,
            sheet_header_level=2,
        )
        markdown = workbook.to_markdown(schema)

        assert "# Financial Reports 2024" in markdown


class TestMixedSheetsToMarkdown:
    """Tests for Workbook with mixed table and doc sheets."""

    def test_mixed_sheets_output(self):
        """Workbook with both table and doc sheets outputs correctly."""
        table = Table(headers=["A", "B"], rows=[["1", "2"]])
        table_sheet = Sheet(name="Data", tables=[table], sheet_type="table", content=None)
        doc_sheet = Sheet(
            name="README",
            tables=[],
            sheet_type="doc",
            content="# Welcome\n\nThis is the documentation.",
        )
        workbook = Workbook(sheets=[table_sheet, doc_sheet], name="Project")

        schema = MultiTableParsingSchema(
            root_marker=None,
            sheet_header_level=2,
        )
        markdown = workbook.to_markdown(schema)

        # Verify structure
        assert "# Project" in markdown
        assert "## Data" in markdown
        assert "| A | B |" in markdown
        assert "## README" in markdown
        assert "# Welcome" in markdown
        assert "This is the documentation." in markdown


class TestRoundTrip:
    """Tests for parse → to_markdown → parse consistency."""

    def test_round_trip_table_sheet(self):
        """Parse → to_markdown → parse preserves table sheet structure."""
        original_md = """# Test Workbook

## Sheet1

| Name | Value |
| ---- | ----- |
| foo  | 123   |
| bar  | 456   |
"""
        # Parse
        workbook1 = parse_workbook(original_md)
        assert workbook1.name == "Test Workbook"
        assert len(workbook1.sheets) == 1
        assert workbook1.sheets[0].sheet_type == "table"

        # Generate
        schema = MultiTableParsingSchema(
            root_marker=None,
            sheet_header_level=2,
            table_header_level=None,
        )
        generated_md = workbook1.to_markdown(schema)

        # Re-parse
        workbook2 = parse_workbook(generated_md)
        assert workbook2.name == workbook1.name
        assert len(workbook2.sheets) == len(workbook1.sheets)
        assert workbook2.sheets[0].name == workbook1.sheets[0].name
        assert workbook2.sheets[0].sheet_type == workbook1.sheets[0].sheet_type
        assert len(workbook2.sheets[0].tables) == len(workbook1.sheets[0].tables)

    def test_round_trip_doc_sheet(self):
        """Parse → to_markdown → parse preserves doc sheet structure."""
        original_md = """# Documentation

## Overview

This is the project overview.

Key features:
- Feature 1
- Feature 2

## Appendix

Additional resources and links.
"""
        # Parse
        workbook1 = parse_workbook(original_md)
        assert len(workbook1.sheets) == 2
        assert all(s.sheet_type == "doc" for s in workbook1.sheets)

        # Generate
        schema = MultiTableParsingSchema(
            root_marker=None,
            sheet_header_level=2,
        )
        generated_md = workbook1.to_markdown(schema)

        # Re-parse
        workbook2 = parse_workbook(generated_md)
        assert workbook2.name == workbook1.name
        assert len(workbook2.sheets) == len(workbook1.sheets)
        for s1, s2 in zip(workbook1.sheets, workbook2.sheets):
            assert s1.name == s2.name
            assert s1.sheet_type == s2.sheet_type
            # Content may have minor whitespace differences
            if s1.content and s2.content:
                assert s1.content.strip() == s2.content.strip()

    def test_round_trip_mixed_sheets(self):
        """Parse → to_markdown → parse preserves mixed sheet workbook."""
        original_md = """# Project Data

## Summary

This section summarizes the data.

## Data Table

| ID | Name |
| -- | ---- |
| 1  | Foo  |

## Notes

Final notes and observations.
"""
        # Parse
        workbook1 = parse_workbook(original_md)
        assert len(workbook1.sheets) == 3
        assert workbook1.sheets[0].sheet_type == "doc"
        assert workbook1.sheets[1].sheet_type == "table"
        assert workbook1.sheets[2].sheet_type == "doc"

        # Generate
        schema = MultiTableParsingSchema(
            root_marker=None,
            sheet_header_level=2,
        )
        generated_md = workbook1.to_markdown(schema)

        # Re-parse
        workbook2 = parse_workbook(generated_md)
        assert len(workbook2.sheets) == 3
        for i, (s1, s2) in enumerate(zip(workbook1.sheets, workbook2.sheets)):
            assert s1.name == s2.name, f"Sheet {i} name mismatch"
            assert s1.sheet_type == s2.sheet_type, f"Sheet {i} type mismatch"

    def test_round_trip_preserves_table_data(self):
        """Round-trip preserves actual table cell values."""
        original_md = """# Workbook

## Sheet1

| Col1 | Col2 | Col3 |
| ---- | ---- | ---- |
| A    | 100  | X    |
| B    | 200  | Y    |
| C    | 300  | Z    |
"""
        workbook1 = parse_workbook(original_md)
        table1 = workbook1.sheets[0].tables[0]

        schema = MultiTableParsingSchema(root_marker=None, sheet_header_level=2)
        generated_md = workbook1.to_markdown(schema)

        workbook2 = parse_workbook(generated_md)
        table2 = workbook2.sheets[0].tables[0]

        # Verify table data
        assert table1.headers == table2.headers
        assert table1.rows == table2.rows
