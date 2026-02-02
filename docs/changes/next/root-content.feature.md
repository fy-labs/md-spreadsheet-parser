# Workbook Root Content Support

Added support for capturing and restoring content located immediately after a Workbook (H1) header.

- **Feature**: `Workbook` model now has a `root_content` field.
- **Parser**: Text between the Workbook header and the first Sheet header is now captured as `root_content`.
- **Generator**: `root_content` is included in the generated markdown, enabling better round-trip support for workbooks with introductory text.
