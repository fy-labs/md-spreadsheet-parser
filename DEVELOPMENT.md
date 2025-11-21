# Developer Guide

This document contains information for developers contributing to or maintaining the `md-spreadsheet-parser`.

## Project Overview

This project is designed to be a lightweight, pure Python parser for Markdown tables. It is intended to be compiled into a `.whl` file and run within a WebAssembly environment (Pyodide) inside a VS Code extension.

### Key Design Principles

1.  **Pure Python**: No C-extensions or heavy dependencies. Must run in Pyodide.
2.  **Modular Schemas**: Parsing logic is controlled by `ParsingSchema` objects to support multiple Markdown flavors (GFM, etc.) in the future without rewriting core logic.
3.  **Pure Functions**: The core `parse` function takes input and configuration and returns output without side effects.

## Environment Setup

This project uses `uv` for package management.

1.  **Install uv**:
    ```bash
    curl -LsSf https://astral.sh/uv/install.sh | sh
    ```

2.  **Install Dependencies**:
    ```bash
    uv sync
    ```

## Development Workflow

### Running Tests

We use `pytest` for testing.

```bash
uv run pytest
```

### Type Checking

This project is typed. Ensure `py.typed` is present in the package.

### Building the Package

To create the `.whl` file for distribution (or for the VS Code extension):

```bash
uv run python -m build
```

The output will be in the `dist/` directory.
- `dist/*.whl`: The wheel file to be used in the VS Code extension.
- `dist/*.tar.gz`: Source distribution.

## Integration with VS Code Extension

1.  Build the wheel: `uv run python -m build`
2.  Copy the generated `.whl` file to the `assets/` directory of the VS Code extension.
3.  In the VS Code extension (TypeScript), use `micropip` to install the wheel into the Pyodide environment.

## Project Structure

```
md-spreadsheet-parser/
├── src/
│   └── md_spreadsheet_parser/
│       ├── core.py       # Main parsing logic
│       ├── schemas.py    # Configuration dataclasses
│       └── __init__.py   # Exports
├── tests/                # Pytest tests
├── pyproject.toml        # Project configuration
└── DEVELOPMENT.md        # This file
```
