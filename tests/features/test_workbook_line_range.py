"""
Tests for Workbook.start_line and end_line properties.

These properties track the line positions of the workbook section:
- start_line: 0-indexed line number where workbook header (e.g., # Tables) starts (inclusive)
- end_line: 0-indexed line number of workbook section end (exclusive, for use with slice())
"""

from md_spreadsheet_parser import MultiTableParsingSchema, parse_workbook


class TestWorkbookLineRangeWithExplicitMarker:
    """Tests for workbook line range with explicit root marker."""

    def test_basic_workbook_line_range(self):
        """Workbook with # Tables marker should report correct start_line."""
        markdown = """# Tables

## Sheet1

| A |
| - |
| 1 |
"""
        workbook = parse_workbook(markdown)

        # # Tables is on line 0 (0-indexed)
        assert workbook.start_line == 0
        assert workbook.end_line is not None
        assert workbook.end_line >= 0

    def test_workbook_with_content_before_marker(self):
        """Content before # Tables should offset start_line correctly."""
        markdown = """# Introduction

Some introductory text here.

# Tables

## Sheet1

| A |
| - |
| 1 |
"""
        workbook = parse_workbook(markdown)

        # # Tables is on line 4 (after intro header, blank, text, blank)
        assert workbook.start_line == 4
        assert workbook.end_line is not None

    def test_workbook_marker(self):
        """# Workbook marker should be detected correctly."""
        markdown = """# Workbook

## Data

| X |
| - |
| 2 |
"""
        workbook = parse_workbook(markdown)

        assert workbook.name == "Workbook"
        assert workbook.start_line == 0

    def test_explicit_schema_with_custom_marker(self):
        """Explicit schema with custom root marker should work."""
        markdown = """# My Custom Root

## Sheet1

| A |
| - |
| 1 |
"""
        schema = MultiTableParsingSchema(
            root_marker="# My Custom Root",
            sheet_header_level=2,
            table_header_level=3,
        )
        workbook = parse_workbook(markdown, schema)

        assert workbook.start_line == 0
        assert workbook.name == "My Custom Root"


class TestWorkbookLineRangeWithAutoDetection:
    """Tests for workbook line range with automatic detection."""

    def test_single_h1_becomes_workbook(self):
        """When only one H1 exists, it becomes the workbook."""
        markdown = """# My Project

## Sheet1

| A |
| - |
| 1 |
"""
        workbook = parse_workbook(markdown)

        assert workbook.name == "My Project"
        assert workbook.start_line == 0

    def test_tables_keyword_detected(self):
        """# Tables keyword should be auto-detected."""
        markdown = """Some preamble

# Tables

## Sheet1

| A |
| - |
| 1 |
"""
        workbook = parse_workbook(markdown)

        assert workbook.name == "Tables"
        # # Tables is on line 2 (after "Some preamble" and blank line)
        assert workbook.start_line == 2

    def test_workbook_keyword_detected(self):
        """# Workbook keyword should be auto-detected."""
        markdown = """# Workbook

## Data

| A |
| - |
| 1 |
"""
        workbook = parse_workbook(markdown)

        assert workbook.name == "Workbook"
        assert workbook.start_line == 0


class TestWorkbookLineRangeEdgeCases:
    """Edge cases for workbook line range."""

    def test_no_workbook_found_returns_none(self):
        """When no workbook is detected, start_line should be None."""
        markdown = """This is just plain text.

No headers here.
"""
        schema = MultiTableParsingSchema(
            root_marker="# NonExistent",
        )
        workbook = parse_workbook(markdown, schema)

        assert len(workbook.sheets) == 0
        # No workbook found, start_line should be None
        assert workbook.start_line is None

    def test_empty_document(self):
        """Empty document should return None for start_line."""
        markdown = ""
        schema = MultiTableParsingSchema(root_marker="# Tables")
        workbook = parse_workbook(markdown, schema)

        assert workbook.start_line is None

    def test_workbook_end_line_is_exclusive_end(self):
        """end_line should be exclusive (like slice end, suitable for lines[start:end])."""
        markdown = """# Tables

## Sheet1

| A |
| - |
| 1 |
"""
        workbook = parse_workbook(markdown)

        lines = markdown.split("\n")
        # end_line should be len(lines) (exclusive end for slice)
        assert workbook.end_line == len(lines)

    def test_h2_marker_line_range(self):
        """H2-level workbook marker should report correct line."""
        markdown = """# Document Title

## Tables

### Sheet1

| A |
| - |
| 1 |
"""
        schema = MultiTableParsingSchema(
            root_marker="## Tables",
            sheet_header_level=3,
            table_header_level=4,
        )
        workbook = parse_workbook(markdown, schema)

        # ## Tables is on line 2
        assert workbook.start_line == 2


class TestWorkbookJsonIncludesLineRange:
    """Tests that Workbook.json includes startLine/endLine."""

    def test_json_includes_start_end_line(self):
        """Workbook.json should include startLine and endLine when present."""
        markdown = """# Tables

## Sheet1

| A |
| - |
| 1 |
"""
        workbook = parse_workbook(markdown)
        json_data = workbook.json

        assert "startLine" in json_data
        assert "endLine" in json_data
        assert json_data["startLine"] == 0
        assert json_data["endLine"] is not None

    def test_json_omits_line_range_when_none(self):
        """Workbook.json should not include startLine/endLine when None."""
        markdown = ""
        schema = MultiTableParsingSchema(root_marker="# NonExistent")
        workbook = parse_workbook(markdown, schema)
        json_data = workbook.json

        # When None, these should not be present in JSON
        assert "startLine" not in json_data or json_data.get("startLine") is None
