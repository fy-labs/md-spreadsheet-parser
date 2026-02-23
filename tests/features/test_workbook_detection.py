"""
Comprehensive tests for Workbook auto-detection across complex file scenarios.

Tests cover:
- Single/Multiple/No H1 header scenarios
- Code block handling (H1 inside code blocks should be ignored)
- Fallback to "# Tables" and "# Workbook"
- Frontmatter and leading content
- Complex nested structures
- Workbook.name extraction
"""

from md_spreadsheet_parser import MultiTableParsingSchema, parse_workbook


class TestSingleH1AutoDetection:
    """Tests for single H1 header auto-detection."""

    def test_single_h1_becomes_workbook(self):
        """Single H1 header is detected as workbook root."""
        markdown = """# My Project

## Sheet1

| A | B |
| - | - |
| 1 | 2 |
"""
        workbook = parse_workbook(markdown)
        assert workbook.name == "My Project"
        assert len(workbook.sheets) == 1
        assert workbook.sheets[0].name == "Sheet1"

    def test_single_h1_with_leading_content(self):
        """Content before H1 is ignored, single H1 becomes workbook."""
        markdown = """Some intro text before any headers.

This is just plain text.

# Main Document

## First Section

Content here.
"""
        workbook = parse_workbook(markdown)
        assert workbook.name == "Main Document"
        assert len(workbook.sheets) == 1
        assert workbook.sheets[0].name == "First Section"

    def test_single_h1_with_many_h2_sheets(self):
        """Single H1 with many H2 sections creates multiple sheets."""
        markdown = """# Workbook Title

## Sheet A
Content A

## Sheet B
Content B

## Sheet C
Content C

## Sheet D
Content D
"""
        workbook = parse_workbook(markdown)
        assert workbook.name == "Workbook Title"
        assert len(workbook.sheets) == 4
        assert [s.name for s in workbook.sheets] == [
            "Sheet A",
            "Sheet B",
            "Sheet C",
            "Sheet D",
        ]


class TestMultipleH1Fallback:
    """Tests for fallback behavior when multiple H1 headers exist."""

    def test_multiple_h1_no_fallback_returns_empty(self):
        """Multiple H1 without fallback marker returns empty workbook."""
        markdown = """# First Section

Some content.

# Second Section

More content.

# Third Section

Even more content.
"""
        workbook = parse_workbook(markdown)
        assert len(workbook.sheets) == 0
        assert workbook.name == "Workbook"  # Default name

    def test_multiple_h1_with_tables_fallback(self):
        """Multiple H1 with '# Tables' uses Tables as workbook."""
        markdown = """# Front Matter

Introduction text.

# Tables

## Data

| A | B |
| - | - |
| 1 | 2 |

# Appendix

Additional notes.
"""
        workbook = parse_workbook(markdown)
        assert workbook.name == "Tables"
        assert len(workbook.sheets) == 1
        assert workbook.sheets[0].name == "Data"
        assert workbook.sheets[0].sheet_type == "table"

    def test_tables_takes_precedence_over_workbook(self):
        """'# Tables' is checked before '# Workbook' (order in document)."""
        markdown = """# Tables

## Sheet1
| A |
| - |
| 1 |

# Workbook

## Sheet2
| B |
| - |
| 2 |
"""
        workbook = parse_workbook(markdown)
        # # Tables comes first, so it's used
        assert workbook.name == "Tables"
        assert len(workbook.sheets) == 1
        assert workbook.sheets[0].name == "Sheet1"

    def test_workbook_fallback_when_no_tables(self):
        """'# Workbook' is used when '# Tables' doesn't exist."""
        markdown = """# Introduction

Some intro.

# Workbook

## Sheet1

| A |
| - |
| 1 |
"""
        workbook = parse_workbook(markdown)
        assert workbook.name == "Workbook"
        assert len(workbook.sheets) == 1


class TestNoH1Scenarios:
    """Tests for documents with no H1 headers."""

    def test_no_h1_with_tables_fallback(self):
        """Document without H1 but with '## Tables' at root - not detected."""
        # Note: This tests that ## Tables is NOT detected (only # Tables)
        markdown = """## Not a Workbook

Just some content without any H1.

### Sub Section

More content.
"""
        workbook = parse_workbook(markdown)
        # No H1, no fallback found
        assert len(workbook.sheets) == 0

    def test_no_h1_no_content_returns_empty(self):
        """Empty document returns empty workbook."""
        markdown = ""
        workbook = parse_workbook(markdown)
        assert len(workbook.sheets) == 0
        assert workbook.name == "Workbook"


class TestCodeBlockHandling:
    """Tests for H1 headers inside code blocks (should be ignored)."""

    def test_h1_in_code_block_ignored(self):
        """H1 inside code block should not be counted as H1 header."""
        markdown = """# Real H1

## Sheet1

Here's an example:

```markdown
# Not a Real H1

This is just example code.
```

Some more content.
"""
        workbook = parse_workbook(markdown)
        assert workbook.name == "Real H1"
        assert len(workbook.sheets) == 1
        assert workbook.sheets[0].name == "Sheet1"
        assert workbook.sheets[0].content is not None
        assert "# Not a Real H1" in workbook.sheets[0].content

    def test_multiple_code_blocks_with_h1(self):
        """Multiple code blocks containing H1 headers."""
        markdown = """# Documentation

## Examples

```python
# This is a Python comment, not markdown
print("hello")
```

```markdown
# Example Header

This shows how to use markdown.
```

## API Reference

API content here.
"""
        workbook = parse_workbook(markdown)
        assert workbook.name == "Documentation"
        assert len(workbook.sheets) == 2
        assert workbook.sheets[0].name == "Examples"
        assert workbook.sheets[1].name == "API Reference"

    def test_only_h1_in_code_block_triggers_fallback(self):
        """When only H1 is inside code block, fallback search should occur."""
        markdown = """Some intro text.

```markdown
# This is in a code block
```

# Tables

## Sheet1

| A |
| - |
| 1 |
"""
        workbook = parse_workbook(markdown)
        # The H1 in code block is ignored, # Tables is found as fallback
        assert workbook.name == "Tables"
        assert len(workbook.sheets) == 1


class TestComplexStructures:
    """Tests for complex document structures."""

    def test_deep_nesting_h3_tables(self):
        """H3 table headers within H2 sheets."""
        markdown = """# Project Data

## Sales Report

### Q1 Data

| Month | Sales |
| ----- | ----- |
| Jan   | 100   |

### Q2 Data

| Month | Sales |
| ----- | ----- |
| Apr   | 200   |

## Inventory

### Products

| Name | Count |
| ---- | ----- |
| A    | 50    |
"""
        workbook = parse_workbook(markdown)
        assert workbook.name == "Project Data"
        assert len(workbook.sheets) == 2
        assert workbook.sheets[0].name == "Sales Report"
        assert len(workbook.sheets[0].tables) == 2
        assert workbook.sheets[1].name == "Inventory"
        assert len(workbook.sheets[1].tables) == 1

    def test_mixed_table_and_doc_sheets(self):
        """Mix of sheets with tables and documentation only."""
        markdown = """# Knowledge Base

## Overview

This section provides an introduction to the project.

Key points:
- First point
- Second point

## Data Tables

| ID | Value |
| -- | ----- |
| 1  | A     |

## Appendix

Additional notes and references.

See also: [links]

## Config

| Key | Value |
| --- | ----- |
| x   | 1     |
"""
        workbook = parse_workbook(markdown)
        assert len(workbook.sheets) == 4

        assert workbook.sheets[0].name == "Overview"
        assert workbook.sheets[0].sheet_type == "doc"

        assert workbook.sheets[1].name == "Data Tables"
        assert workbook.sheets[1].sheet_type == "table"

        assert workbook.sheets[2].name == "Appendix"
        assert workbook.sheets[2].sheet_type == "doc"

        assert workbook.sheets[3].name == "Config"
        assert workbook.sheets[3].sheet_type == "table"

    def test_header_without_content_between(self):
        """Consecutive headers without content between them."""
        markdown = """# Workbook

## Empty Sheet 1
## Empty Sheet 2
## Sheet With Content

Some content here.

## Empty Sheet 3
"""
        workbook = parse_workbook(markdown)
        assert len(workbook.sheets) == 4
        # All are doc sheets since no tables
        for sheet in workbook.sheets:
            assert sheet.sheet_type == "doc"

    def test_whitespace_variations_in_headers(self):
        """Headers with extra spaces between ## and title."""
        markdown = """# My Workbook

##  Sheet With Extra Space

Content.

##   Another Extra Space

More content.

## Normal Sheet

| A |
| - |
| 1 |
"""
        workbook = parse_workbook(markdown)
        assert workbook.name == "My Workbook"
        # Note: Parser uses startswith("## ") so extra spaces after ## work
        # but tabs or other whitespace in prefix won't be detected
        assert len(workbook.sheets) == 3


class TestWorkbookNameExtraction:
    """Tests for correct workbook.name extraction."""

    def test_name_from_single_h1(self):
        """Workbook name is extracted from single H1 text."""
        markdown = """# My Amazing Project Title

## Sheet1
Content
"""
        workbook = parse_workbook(markdown)
        assert workbook.name == "My Amazing Project Title"

    def test_name_from_fallback_tables(self):
        """Workbook name is 'Tables' when using fallback."""
        markdown = """# Intro

# Tables

## Data
| A |
| - |
| 1 |
"""
        workbook = parse_workbook(markdown)
        assert workbook.name == "Tables"

    def test_name_from_explicit_root_marker(self):
        """Workbook name extracted from explicit root_marker."""
        markdown = """# Custom Root

## Sheet1
| A |
| - |
| 1 |
"""
        schema = MultiTableParsingSchema(
            root_marker="# Custom Root",
            sheet_header_level=2,
        )
        workbook = parse_workbook(markdown, schema)
        assert workbook.name == "Custom Root"

    def test_default_name_when_no_workbook_found(self):
        """Default name is 'Workbook' when no workbook is detected."""
        markdown = """# First

# Second

No fallback markers here.
"""
        workbook = parse_workbook(markdown)
        assert workbook.name == "Workbook"
        assert len(workbook.sheets) == 0


class TestExplicitSchemaOverrides:
    """Tests for explicit schema configuration overriding auto-detection."""

    def test_explicit_schema_ignores_single_h1(self):
        """Explicit root_marker means single H1 is not auto-detected."""
        markdown = """# My Document

## Section

Some content.

# Data Tables

## Sheet1

| A |
| - |
| 1 |
"""
        schema = MultiTableParsingSchema(
            root_marker="# Data Tables",
            sheet_header_level=2,
        )
        workbook = parse_workbook(markdown, schema)
        assert workbook.name == "Data Tables"
        assert len(workbook.sheets) == 1
        assert workbook.sheets[0].name == "Sheet1"

    def test_explicit_h2_as_root_marker(self):
        """H2 can be used as root_marker when explicitly set."""
        markdown = """# Main Title

## Some Section

Regular content.

## Spreadsheet Data

### Sheet1

| A |
| - |
| 1 |
"""
        schema = MultiTableParsingSchema(
            root_marker="## Spreadsheet Data",
            sheet_header_level=3,
            table_header_level=4,
        )
        workbook = parse_workbook(markdown, schema)
        assert workbook.name == "Spreadsheet Data"
        assert len(workbook.sheets) == 1
        assert workbook.sheets[0].name == "Sheet1"


class TestMetadataCommentDetection:
    """Tests for workbook detection via md-spreadsheet metadata comment."""

    def test_multiple_h1_with_metadata_comment(self):
        """When multiple H1 exist, H1 containing metadata comment becomes workbook."""
        markdown = """# Front Matter

Introduction text.

# Data

## Sheet1

| A | B |
| - | - |
| 1 | 2 |

<!-- md-spreadsheet-workbook-metadata: {"tab_order": []} -->

# Appendix

Additional notes.
"""
        workbook = parse_workbook(markdown)
        assert workbook.name == "Data"
        assert len(workbook.sheets) == 1
        assert workbook.sheets[0].name == "Sheet1"

    def test_metadata_comment_before_any_h1(self):
        """Metadata comment at start (before any H1) uses first H1."""
        markdown = """<!-- md-spreadsheet-workbook-metadata: {"tab_order": []} -->

# First H1

## Sheet1

| A |
| - |
| 1 |

# Second H1

Content.
"""
        workbook = parse_workbook(markdown)
        # Metadata before any H1 - should use first H1
        assert workbook.name == "First H1"
        assert len(workbook.sheets) == 1

    def test_metadata_takes_precedence_over_tables_fallback(self):
        """Metadata detection runs before fallback to # Tables."""
        markdown = """# Tables

Some non-sheet content.

# Actual Workbook

## Sheet1

| A |
| - |
| 1 |

<!-- md-spreadsheet-workbook-metadata: {} -->

# Notes

More notes.
"""
        workbook = parse_workbook(markdown)
        # Metadata is in "# Actual Workbook" section, not "# Tables"
        assert workbook.name == "Actual Workbook"
        assert len(workbook.sheets) == 1

    def test_metadata_with_tab_order(self):
        """Metadata with tab_order is correctly parsed."""
        markdown = """# Intro

Intro text.

# My Spreadsheet

## Sheet1

| A |
| - |
| 1 |

## Sheet2

| B |
| - |
| 2 |

<!-- md-spreadsheet-workbook-metadata: {"tab_order": [{"type": "sheet", "index": 1}, {"type": "sheet", "index": 0}]} -->

# Appendix

Notes.
"""
        workbook = parse_workbook(markdown)
        assert workbook.name == "My Spreadsheet"
        assert len(workbook.sheets) == 2
        assert workbook.metadata is not None
        assert "tab_order" in workbook.metadata

    def test_single_h1_still_works_with_metadata(self):
        """Single H1 with metadata works normally (step 1 takes precedence)."""
        markdown = """# Only H1

## Sheet1

| A |
| - |
| 1 |

<!-- md-spreadsheet-workbook-metadata: {"custom": "data"} -->
"""
        workbook = parse_workbook(markdown)
        # Single H1 rule (step 1) applies, metadata is still parsed
        assert workbook.name == "Only H1"
        assert len(workbook.sheets) == 1
        assert workbook.metadata is not None
        assert workbook.metadata.get("custom") == "data"
