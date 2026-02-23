# Development Guide

This document provides a comprehensive guide for developers contributing to `md-spreadsheet-parser`.
It focuses on maintaining code quality, ensuring type safety, and following a consistent development workflow.

## 1. Environment Setup

We use **[uv](https://github.com/astral-sh/uv)** for dependency management and virtual environments.

### Prerequisites
- Python 3.12+
- `uv` installed

### Setup Command
Clone the repository and sync dependencies:

```bash
git clone https://github.com/f-y/md-spreadsheet-parser.git
cd md-spreadsheet-parser
uv sync
```
This creates a virtual environment in `.venv` with all dev dependencies (`pytest`, `ruff`, `mypy`, `pandas-stubs` etc.).

## 2. Quality Assurance Tools

We enforce strict quality standards using the following tools.
**You must ensure all checks pass locally before opening a Pull Request.**

### Linting & Formatting (Ruff)
We use `ruff` (configured in `pyproject.toml`) for both linting and formatting.

```bash
# Check for lint errors
uv run ruff check .

# Auto-fix lint errors
uv run ruff check --fix .

# Check formatting
uv run ruff format --check .

# Auto-format code
uv run ruff format .
```

### 3. Static Analysis
We use **Pyright** for static type checking (replacing Mypy for performance).

```bash
uv run pyright
```

Ensure your code passes type checks before committing.
- Use `type: ignore` sparingly and only when necessary (e.g., dynamically updated attributes).
- For Pydantic/Pandas integration, ensure stubs are installed or checks are guarded.

### 4. Release Notes Workflow
To ensure accurate and comprehensive release notes, we use a **Fragment-based** approach.

#### Adding a Change Note
When you implement a feature or fix a bug:
1.  Create a new Markdown file in `docs/changes/next/`.
2.  Name the file `<issue_id>.<type>.md` (or `<short_desc>.<type>.md` if no issue).
    - Types:
        - `feature`: New functionality (implies **Minor** version bump).
        - `fix`: Bug fix (implies **Patch** version bump).
        - `docs`: Documentation improvements.
        - `breaking`: Backward incompatible changes (implies **Major** version bump).
    - Example: `123.feature.md` or `metadata-persistence.fix.md`.
3.  Write a clear, user-facing summary of the change in the file.

#### Release Process
The release process is handled by the maintainers using internal automation tools.

When a release is triggered:
1.  **Fragment Collection**: Validation and collection of all fragment files from `docs/changes/next/`.
2.  **Changelog Generation**: These fragments are compiled into the `CHANGELOG.md`.
3.  **Cleanup**: The used fragments are archived to `docs/changes/archive/`.
4.  **Publishing**: The package is tagged and published to PyPI.

As a contributor, you only need to ensure your changes are accompanied by a correct fragment file.

### Testing (Pytest)
We use `pytest` for unit and integration testing.

```bash
# Run all tests
uv run pytest

# Run with coverage (optional)
uv run pytest --cov=src
```

## 3. Development Workflow

### A. Implementing Features/Fixes
1.  **Branching**: Create a feature branch from `main`.
2.  **TDD**: Write a failing test case in `tests/` reproducing the bug or defining the new feature.
3.  **Implement**: Write code to pass the test.
4.  **Verify**: Run the full suite (`pytest`, `ruff`, `mypy`).

### B. Project Structure
- `src/md_spreadsheet_parser/`: Core library code.
    - `schemas.py`: Configuration schemas (Dataclasses).
    - `models.py`: Data structures (Table, Workbook).
    - `parser.py`: Core parsing logic.
    - `generator.py`: Markdown generation logic.
    - `validation.py`: Type validation and conversion logic.
- `tests/`: Structured test suite (see [Test Architecture](#5-test-architecture)).

## 5. Test Architecture

The test suite is structured to categorize tests by their architectural role, ensuring scalability and clarity. We follow a **layered testing strategy**:

*   **`tests/core/`**: **Core Logic**. Tests for the fundamental parsing and generation capabilities (Parsing, Generator, Models). These verify the library's primary responsibility: `Markdown <-> Object`.
*   **`tests/features/`**: **Feature Subsystems**. Tests for distinct, isolated features that extend the core (Metadata systems, Streaming, CLI, Validation).
*   **`tests/integrations/`**: **Ecosystem Adapters**. Tests verifying compatibility with external libraries (Pandas, Pydantic, JSON) to ensure the library fits into the broader Python data ecosystem.
*   **`tests/scenarios/`**: **Quality Assurance**. Tests specifically designed to break the parser (Malformed inputs, Edge cases, Fuzzing-like mixed inputs) to ensure robustness without cluttering functional tests.

### File Organization Guidelines
*   **One Feature, One File**: In `tests/features/`, group all tests related to a specific feature (including happy paths, edge cases, and regression tests) into a single file (e.g., `test_metadata.py`).
*   **Don't Fragment by Scenario**: Avoid creating separate files for specific bug fixes or scenarios (e.g., `test_metadata_gaps.py`) unless the test logic requires a completely different setup or the file size exceeds ~500 lines.
*   **Clear Naming**: Use `test_<feature_name>.py`.

## 6. Pull Request Checklist

When submitting a PR, please confirm:

- [ ] **Tests**: New tests added for new features? All existing tests pass?
- [ ] **Linting**: `uv run ruff check .` passes with no errors?
- [ ] **Formatting**: Code is formatted via `uv run ruff format .`?
- [ ] **Typing**: `uv run mypy .` passes with "Success: no issues found"?
- [ ] **Documentation**: `README.md` updated if public API changed?

## 7. Documentation & i18n

We support bilingual documentation (English and Japanese) using `mkdocs-static-i18n`.

### Directory Structure (Proxy Pattern)
To ensure documentation is visible on GitHub while maintaining a clean MkDocs structure, we use a "Root Source, Docs Proxy" pattern for key files:

*   **Source of Truth**: Located in the project root.
    *   `README.md` / `README.ja.md`
    *   `COOKBOOK.md` / `COOKBOOK.ja.md`
*   **MkDocs Proxy**: Located in `docs/`, taking advantage of `mkdocs-include-markdown-plugin`.
    *   `docs/index.md` -> includes `../README.md`
    *   `docs/index.ja.md` -> includes `../README.ja.md`
    *   `docs/COOKBOOK.md` -> includes `../COOKBOOK.md` (Note: Ensure sync if not already proxy)

### Adding Translations
When updating documentation, please attempt to update both English and Japanese versions. If you cannot provide a translation:
1.  Copy the English content to the `*.ja.md` file.
2.  Add a `> [!NOTE]` indicating that the content is not yet translated.

### Naming Convention
*   English (Default): `filename.md`
*   Japanese: `filename.ja.md`
