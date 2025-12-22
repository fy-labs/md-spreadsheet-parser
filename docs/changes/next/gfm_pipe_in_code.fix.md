Implemented compliant GFM pipe handling. The parser now correctly treats pipes inside inline code blocks (e.g., `` `|` ``) as literal text rather than column separators.
This involved replacing the internal regex-based row splitter with a new state-aware parsing logic.
