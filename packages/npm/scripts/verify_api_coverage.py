import re
import sys
from pathlib import Path
from typing import Set

import griffe


def get_python_public_api(src_dir: Path) -> Set[str]:
    """
    Extracts the set of expected public API signatures (Class.method or Function)
    from the Python source using Griffe.
    """
    api_surface = set()

    search_paths = [str(src_dir)]
    pkg_models = griffe.load("md_spreadsheet_parser.models", search_paths=search_paths)
    pkg_parsing = griffe.load(
        "md_spreadsheet_parser.parsing", search_paths=search_paths
    )
    pkg_loader = griffe.load("md_spreadsheet_parser.loader", search_paths=search_paths)

    # 1. Models and Methods
    for name, member in pkg_models.members.items():
        if member.is_alias or name.startswith("_") or name.endswith("JSON"):
            continue
        if member.is_class:
            # Add Class itself
            # api_surface.add(f"class {name}")

            # Add Public Methods
            for m_name, method in member.members.items():
                if not method.is_function or m_name.startswith("_"):
                    continue
                # Expected TS method name: snake_case -> camelCase
                ts_method = re.sub(r"_([a-z])", lambda g: g.group(1).upper(), m_name)
                api_surface.add(f"{name}.{ts_method}")

    # 2. Standalone Functions
    for name, member in pkg_parsing.members.items():
        if member.is_alias or name.startswith("_") or not member.is_function:
            continue
        ts_func = re.sub(r"_([a-z])", lambda g: g.group(1).upper(), name)
        api_surface.add(f"function {ts_func}")

    for name, member in pkg_loader.members.items():
        if member.is_alias or name.startswith("_") or not member.is_function:
            continue
        ts_func = re.sub(r"_([a-z])", lambda g: g.group(1).upper(), name)
        api_surface.add(f"function {ts_func}")

    return api_surface


def get_typescript_api(ts_file: Path) -> Set[str]:
    """
    Naively parses the index.ts file to find exported classes and methods.
    Returns set of "ClassName.methodName" or "function functionName".
    """
    content = ts_file.read_text()

    found_api = set()

    current_class = None

    # Simple line-based parser
    for line in content.splitlines():
        # Do not strip immediately to preserve indentation for scope detection
        stripped = line.strip()

        # Detect Class
        m_cls = re.match(r"^export class (\w+)", stripped)
        if m_cls:
            current_class = m_cls.group(1)
            continue

        # Detect Method inside Class
        # Expect indentation of 4 spaces
        if current_class:
            # Check for Class End (0 indentation closing brace)
            if line.startswith("}"):
                current_class = None
                continue

            # Method pattern: "    name("
            # We want to match explicitly indented methods to avoid confusing with inner code
            m_method = re.match(r"^    (\w+)\(", line)
            if m_method:
                method_name = m_method.group(1)
                if method_name != "constructor":
                    found_api.add(f"{current_class}.{method_name}")

        # Detect Re-exported Function (from imports)
        # export { parseWorkbook };
        # Actually in index.ts we generate:
        # export { parseWorkbook, scanTables };
        m_exp = re.match(r"export \{ ([^}]+) \};", line)
        if m_exp and not current_class:
            # These are usually the function exports
            # We need to filter out the ones that are NOT classes?
            # In generate_wit.py, we export both Classes and Functions.
            # But functions are imported from dist/parser.js and re-exported.
            # Classes are defined in index.ts.

            # Let's rely on the top-level function check logic.
            # The imports from parser.js are the flat functions + standalone functions.

            # Use generate_wit's logic:
            # Standalone functions are re-exported.
            names = [n.strip() for n in m_exp.group(1).split(",")]
            for n in names:
                # Heuristic: if it looks like a function (camelCase), add it
                # But classes are also exported...
                # Actually, classes are exported via `export class ...`.
                # Re-exports are usually the flattened WASM functions or standalone helpers.
                pass

    # Alternative: Scan for the standalone functions explicitly imported/exported
    # In generate_wit.py:
    # content += f"import {{ {', '.join(imports)} }} from '../dist/parser.js';\n"
    # content += f"export {{ {', '.join(imports)} }};\n\n"

    # We can inspect the re-exports.
    m_reexports = re.search(r"export \{ ([^}]+) \};", content)
    if m_reexports:
        exports = [e.strip() for e in m_reexports.group(1).split(",")]
        for e in exports:
            if not e.startswith("type") and "Interface" not in e:
                # Check if it matches expected standalone functions
                # We assume camelCase functions
                if re.match(r"[a-z][a-zA-Z0-9]*", e):
                    found_api.add(f"function {e}")

    return found_api


def main():
    base_dir = Path(__file__).parent.parent.parent.parent
    src_dir = base_dir / "src"
    ts_file = Path(__file__).parent.parent / "src" / "index.ts"

    print(f"Scanning Python API from: {src_dir}")
    py_api = get_python_public_api(src_dir)
    print(f"Scanning TypeScript API from: {ts_file}")
    ts_api = get_typescript_api(ts_file)

    missing = []

    # Add src to sys.path to import md_spreadsheet_parser
    sys.path.insert(0, str(src_dir))
    from md_spreadsheet_parser.models import Table

    rows = []

    print("\n--- Compliance Check ---")
    for item in sorted(py_api):
        status = "✅ OK"
        ts_name = item
        if item not in ts_api:
            missing.append(item)
            status = "❌ Missing"
            ts_name = "-"

        rows.append([item, item, ts_name, status])

    # Generate Markdown Table Log
    print("\n--- API Coverage Log ---")
    log_table = Table(
        headers=["API Signature", "Python", "TypeScript", "Status"],
        rows=rows,
        name="API Coverage Report",
    )
    print(log_table.to_markdown())

    if missing:
        print("\n❌ API Mismatch! The following items are missing in TypeScript:")
        for m in missing:
            print(f"  - {m}")
        sys.exit(1)
    else:
        print("\n✅ 100% Structural API Compatibility Verified.")
        print(f"   Covered {len(py_api)} public methods/functions.")


if __name__ == "__main__":
    main()
