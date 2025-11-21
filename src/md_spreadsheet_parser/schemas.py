from dataclasses import dataclass
from typing import Optional

@dataclass(frozen=True)
class ParsingSchema:
    """
    Configuration for parsing markdown tables.
    Designed to be immutable and passed to pure functions.
    """
    column_separator: str = "|"
    header_separator_char: str = "-"
    require_outer_pipes: bool = False
    strip_whitespace: bool = True
    
    # Future extensibility:
    # quote_char: Optional[str] = None
    # escape_char: Optional[str] = "\\"

@dataclass(frozen=True)
class ParseResult:
    """
    Structured result of the parsing operation.
    """
    headers: Optional[list[str]]
    rows: list[list[str]]
    metadata: dict

# Default schema for standard Markdown tables (GFM style)
DEFAULT_SCHEMA = ParsingSchema()

@dataclass(frozen=True)
class Sheet:
    """
    Represents a single sheet containing tables.
    """
    name: str
    tables: list[ParseResult]

@dataclass(frozen=True)
class Workbook:
    """
    Represents a collection of sheets (multi-table output).
    """
    sheets: list[Sheet]

@dataclass(frozen=True)
class MultiTableParsingSchema(ParsingSchema):
    """
    Configuration for parsing multiple tables (workbook mode).
    """
    root_marker: str = "# Tables"
    sheet_header_level: int = 2  # e.g. ## SheetName

