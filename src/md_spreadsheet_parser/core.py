from typing import List, Tuple, Optional
import re
from .schemas import ParsingSchema, ParseResult, DEFAULT_SCHEMA, Sheet, Workbook, MultiTableParsingSchema

def clean_cell(cell_content: str, schema: ParsingSchema) -> str:
    """
    Cleans a single cell content based on the schema.
    """
    if schema.strip_whitespace:
        return cell_content.strip()
    return cell_content

def parse_row(line: str, schema: ParsingSchema) -> List[str]:
    """
    Parses a single line into a list of cell values.
    """
    parts = line.split(schema.column_separator)
    
    if not parts:
        return []
        
    start_idx = 0
    end_idx = len(parts)
    
    if parts and parts[0].strip() == "":
        start_idx = 1
    
    if parts and len(parts) > 1 and parts[-1].strip() == "":
        end_idx = -1
        
    cleaned_parts = parts[start_idx:end_idx]
    
    return [clean_cell(p, schema) for p in cleaned_parts]

def is_separator_row(row_cells: List[str], schema: ParsingSchema) -> bool:
    """
    Determines if a parsed row is a header separator row (e.g. ---|---).
    """
    if not row_cells:
        return False
        
    for cell in row_cells:
        content = cell.strip()
        if not content:
            continue
            
        valid_chars = set(schema.header_separator_char + ": ")
        if not set(content).issubset(valid_chars):
            return False
            
        if schema.header_separator_char not in content:
            return False
            
    return True

def parse_table(text: str, schema: ParsingSchema = DEFAULT_SCHEMA) -> ParseResult:
    """
    Parses a single block of text into a table.
    """
    lines = text.strip().split('\n')
    
    headers: Optional[List[str]] = None
    rows: List[List[str]] = []
    
    potential_header: Optional[List[str]] = None
    
    for i, line in enumerate(lines):
        line = line.strip()
        if not line:
            continue
            
        parsed_row = parse_row(line, schema)
        
        if not parsed_row:
            continue
            
        if headers is None and potential_header is not None:
            if is_separator_row(parsed_row, schema):
                headers = potential_header
                potential_header = None
                continue 
            else:
                rows.append(potential_header)
                potential_header = parsed_row
        elif headers is None and potential_header is None:
            potential_header = parsed_row
        else:
            rows.append(parsed_row)
            
    if potential_header is not None:
        rows.append(potential_header)
        
    return ParseResult(
        headers=headers,
        rows=rows,
        metadata={"schema_used": str(schema)}
    )

def parse_sheet(text: str, name: str, schema: ParsingSchema = DEFAULT_SCHEMA) -> Sheet:
    """
    Parses a sheet content which may contain multiple tables separated by blank lines.
    """
    # Split by blank lines (2 or more newlines) to separate blocks
    # We use regex to split by one or more empty lines
    blocks = re.split(r'\n\s*\n', text.strip())
    
    tables: List[ParseResult] = []
    
    for block in blocks:
        if not block.strip():
            continue
            
        # Heuristic: A block is a table if it contains the column separator
        if schema.column_separator in block:
            table = parse_table(block, schema)
            # Only add if it has content
            if table.headers or table.rows:
                tables.append(table)
                
    return Sheet(name=name, tables=tables)

def parse_workbook(text: str, schema: MultiTableParsingSchema) -> Workbook:
    """
    Parses a full workbook text containing multiple sheets.
    Strictly requires the root_marker to be present. Content before the marker is ignored.
    """
    # Find the root marker
    marker_index = text.find(schema.root_marker)
    if marker_index == -1:
        # Marker not found, return empty workbook or raise error?
        # For now, return empty workbook as it doesn't match the format
        return Workbook(sheets=[])
        
    # Slice the text to start from the marker
    # We add the length of marker to skip it, but we might want to keep newlines after it
    content_start = marker_index + len(schema.root_marker)
    content = text[content_start:]
    
    lines = content.split('\n')
    
    sheets: List[Sheet] = []
    current_sheet_name: Optional[str] = None
    current_sheet_lines: List[str] = []
    
    header_prefix = "#" * schema.sheet_header_level + " "
    
    for line in lines:
        stripped = line.strip()
        if stripped.startswith(header_prefix):
            # New sheet found
            # Save previous sheet
            if current_sheet_name:
                sheet_content = "\n".join(current_sheet_lines)
                sheets.append(parse_sheet(sheet_content, current_sheet_name, schema))
            
            # Start new sheet
            current_sheet_name = stripped[len(header_prefix):].strip()
            current_sheet_lines = []
        else:
            # Add to current sheet
            if current_sheet_name:
                current_sheet_lines.append(line)
                
    # Add the last sheet
    if current_sheet_name:
        sheet_content = "\n".join(current_sheet_lines)
        sheets.append(parse_sheet(sheet_content, current_sheet_name, schema))
        
    return Workbook(sheets=sheets)
