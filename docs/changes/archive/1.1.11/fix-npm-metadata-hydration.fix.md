Fixed `Object.assign(this, res)` usage in NPM package causing `metadata` to remain as a JSON string.

The TypeScript wrapper generator (`scripts/generate_wit.py`) now produces proper hydration code that reconstructs objects via the constructor, ensuring:
- `metadata` is parsed from JSON string to `Record<string, any>` (matching Python's `dict[str, any]`)
- Nested models (e.g., `Sheet` within `Workbook`, `Table` within `Sheet`) are properly instantiated as class instances
