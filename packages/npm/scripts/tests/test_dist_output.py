"""Tests for generated dist output (index.ts and related files)."""

import sys
from pathlib import Path
import re

# Find the dist directory
DIST_DIR = Path(__file__).parent.parent.parent / "dist"
SRC_DIR = Path(__file__).parent.parent.parent / "src"


class TestDistIndexTs:
    """Tests for the generated index.ts file."""

    def test_index_ts_exists(self):
        """Verify index.ts is generated."""
        index_path = SRC_DIR / "index.ts"
        assert index_path.exists(), f"index.ts not found at {index_path}"

    def test_exports_required_classes(self):
        """Verify all required classes are exported."""
        index_path = SRC_DIR / "index.ts"
        content = index_path.read_text()

        required_classes = ["Table", "Sheet", "Workbook", "ParsingSchema", "MultiTableParsingSchema"]
        for cls in required_classes:
            assert f"export class {cls}" in content, f"Missing export for class {cls}"

    def test_exports_required_functions(self):
        """Verify all required functions are exported."""
        index_path = SRC_DIR / "index.ts"
        content = index_path.read_text()

        required_funcs = ["parseTable", "parseWorkbook", "parseSheet", "scanTables"]
        for func in required_funcs:
            assert f"export function {func}" in content or f"export async function {func}" in content, \
                f"Missing export for function {func}"

    def test_hydration_pattern_used(self):
        """Verify mutation methods use hydration pattern, not direct Object.assign(this, res)."""
        index_path = SRC_DIR / "index.ts"
        content = index_path.read_text()

        # Find all Object.assign(this, ...) usages
        assigns = re.findall(r"Object\.assign\(this, (\w+)\)", content)

        # All should be hydrated, not raw 'res'
        for assign_var in assigns:
            assert assign_var == "hydrated", \
                f"Found Object.assign(this, {assign_var}) - should use 'hydrated' not '{assign_var}'"

    def test_metadata_json_parsing(self):
        """Verify constructors parse metadata from JSON string."""
        index_path = SRC_DIR / "index.ts"
        content = index_path.read_text()

        # Check for JSON.parse pattern for metadata
        assert "JSON.parse(data.metadata)" in content, "Missing JSON.parse for metadata in constructor"

    def test_nested_model_wrapping(self):
        """Verify nested models (sheets in Workbook, tables in Sheet) are wrapped."""
        index_path = SRC_DIR / "index.ts"
        content = index_path.read_text()

        assert "new Sheet(x)" in content, "Missing Sheet wrapping in Workbook"
        assert "new Table(x)" in content, "Missing Table wrapping in Sheet"


class TestDistJsOutput:
    """Tests for the generated JavaScript output."""

    def test_parser_js_exists(self):
        """Verify parser.js is generated."""
        parser_path = DIST_DIR / "parser.js"
        assert parser_path.exists(), f"parser.js not found at {parser_path}"

    def test_index_js_exists(self):
        """Verify index.js (compiled from index.ts) exists."""
        # After tsc compile, index.js should be in dist
        index_js = DIST_DIR / "index.js"
        assert index_js.exists(), f"index.js not found at {index_js}"


class TestDistWasmOutput:
    """Tests for WASM files."""

    def test_wasm_core_exists(self):
        """Verify core WASM file exists."""
        wasm_files = list(DIST_DIR.glob("*.wasm"))
        assert len(wasm_files) > 0, "No WASM files found in dist"

    def test_wasm_not_too_large(self):
        """Verify WASM files aren't unexpectedly large (regression test)."""
        total_size = sum(f.stat().st_size for f in DIST_DIR.glob("*.wasm"))
        # Should be under 50MB total (currently ~38MB)
        max_size_mb = 50
        assert total_size < max_size_mb * 1024 * 1024, \
            f"WASM files total {total_size / 1024 / 1024:.1f}MB, expected < {max_size_mb}MB"
