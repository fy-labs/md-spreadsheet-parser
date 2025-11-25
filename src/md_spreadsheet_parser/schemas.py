from dataclasses import dataclass
from typing import Any, Dict, List, Optional, TypedDict

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
    headers: Optional[List[str]]
    rows: List[List[str]]
    metadata: Dict[str, Any]



# Default schema for standard Markdown tables (GFM style)
DEFAULT_SCHEMA = ParsingSchema()

class TableJSON(TypedDict):
    name: Optional[str]
    description: Optional[str]
    headers: Optional[List[str]]
    rows: List[List[str]]
    metadata: Dict[str, Any]

class SheetJSON(TypedDict):
    name: str
    tables: List[TableJSON]

class WorkbookJSON(TypedDict):
    sheets: List[SheetJSON]

@dataclass(frozen=True)
class Table:
    """
    Represents a parsed table with optional metadata.
    """
    headers: Optional[List[str]]
    rows: List[List[str]]
    name: Optional[str] = None
    description: Optional[str] = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            # Hack to allow default value for mutable type in frozen dataclass
            object.__setattr__(self, 'metadata', {})

    @property
    def json(self) -> TableJSON:
        return {
            "name": self.name,
            "description": self.description,
            "headers": self.headers,
            "rows": self.rows,
            "metadata": self.metadata
        }

@dataclass(frozen=True)
class Sheet:
    """
    Represents a single sheet containing tables.
    """
    name: str
    tables: List[Table]

    @property
    def json(self) -> SheetJSON:
        return {
            "name": self.name,
            "tables": [t.json for t in self.tables]
        }

@dataclass(frozen=True)
class Workbook:
    """
    Represents a collection of sheets (multi-table output).
    """
    sheets: List[Sheet]

    @property
    def json(self) -> WorkbookJSON:
        return {
            "sheets": [s.json for s in self.sheets]
        }

@dataclass(frozen=True)
class MultiTableParsingSchema(ParsingSchema):
    """
    Configuration for parsing multiple tables (workbook mode).
    """
    root_marker: str = "# Tables"
    sheet_header_level: int = 2  # e.g. ## SheetName
    table_header_level: Optional[int] = None  # e.g. ### TableName
    capture_description: bool = False


