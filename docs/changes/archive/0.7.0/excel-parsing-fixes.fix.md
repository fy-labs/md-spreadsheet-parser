### Excel Parsing Improvements

- **Fix**: Improved hierarchical header flattening for vertically merged cells (e.g., prohibiting trailing separators like `Status - `).
- **Enhancement**: Cleaner string conversion for Excel numbers; integer-floats (e.g., `1.0`) are now automatically converted to valid integers (`"1"`) instead of preserving the decimal (`"1.0"`).
