# Changelog

## [0.5.0] - 2025-12-22

### 🚀 New Features

Implemented support for GitHub Flavored Markdown (GFM) table alignment syntax (e.g. `| :--- | :---: | ---: |`).
The `Table` model now has an `alignments` attribute, and the parser/generator preserves this information during round-trip operations.

### 🐛 Bug Fixes

Implemented compliant GFM pipe handling. The parser now correctly treats pipes inside inline code blocks (e.g., `` `|` ``) as literal text rather than column separators.
This involved replacing the internal regex-based row splitter with a new state-aware parsing logic.

## [0.4.3] - 2025-12-22

### 📚 Documentation

Updated README.md to highlight suitability for AWS Lambda (Zero Dependency) and the "Markdown as Database" concept based on user feedback.
---
type: docs
---

Added `mkdocs-git-revision-date-localized-plugin` to generate accurate `lastmod` dates in `sitemap.xml` for better SEO and Google Search Console integration.

## [0.4.2] - 2025-12-21

### 📚 Documentation

Update PyPI package keywords to improve discoverability for Excel-related and zero-dependency use cases.

## [0.4.1] - 2025-12-21

### 📚 Documentation

Update PyPI package description to highlight zero-dependency parsing and Excel conversion features.

## [0.4.0] - 2025-12-21

### 🐛 Bug Fixes

Fix bug where headers in markdown code blocks were incorrectly interpreted as document structure (e.g., `# Tables` or `## Sheet 1` inside a code block). The parser now correctly ignores any headers inside fenced code blocks.

## [0.3.3] - 2025-12-19

### 🐛 Bug Fixes

### Fixed Docs Links for PyPI

Updated `README.md` to use absolute GitHub URLs for the Cookbook and License. This ensures links work correctly when viewed on the PyPI project page (which does not host the relative files).

### 📚 Documentation

### Added Cookbook to Documentation

Integrated the new `COOKBOOK.md` into the MkDocs site navigation for better accessibility.

## [0.3.2] - 2025-12-19

### 📚 Documentation

### Added Cookbook

Added a new `COOKBOOK.md` file with recipes for common tasks:
- Fast installation
- Reading tables from files (one-liner)
- Pandas integration (DataFrame <-> Markdown <-> Excel/TSV)
- Programmatic Editing (Excel-like calculations)
- Code Formatting & Linting for tables
- JSON Conversion
- Simple Type-Safe Validation examples

Also added a prominent link to the guide at the top of `README.md`.

## [0.3.1] - 2025-12-17

### 🚀 New Features

### CI/CD Implementation

- **Added**: GitHub Actions workflow (`.github/workflows/tests.yml`) to run unit tests (`pytest`) for `md-spreadsheet-parser` on push and pull request.
- **Added**: Build status badge to `md-spreadsheet-parser/README.md`.

### 🐛 Bug Fixes

### Fix CI/CD Workflow

- **Fixed**: Corrected `paths` and `working-directory` configuration in GitHub Actions workflow to run properly in the `md-spreadsheet-parser` repository root.