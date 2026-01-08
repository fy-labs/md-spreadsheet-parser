Added `json` getter to Table, Sheet, and Workbook classes in the NPM package.

- The `json` getter mirrors Python's `.json` property
- Returns a JSON-compatible plain object representation
- Recursively converts nested models (e.g., Sheet.json includes all tables.json)
