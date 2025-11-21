import json
from md_spreadsheet_parser import (
    parse_table, 
    parse_workbook, 
    DEFAULT_SCHEMA, 
    MultiTableParsingSchema,
    Workbook
)

def test_simple_table():
    markdown = """
| Header 1 | Header 2 |
| --- | --- |
| Cell 1 | Cell 2 |
| Cell 3 | Cell 4 |
"""
    result = parse_table(markdown)
    
    assert result.headers == ["Header 1", "Header 2"]
    assert len(result.rows) == 2
    assert result.rows[0] == ["Cell 1", "Cell 2"]
    assert result.rows[1] == ["Cell 3", "Cell 4"]

def test_no_header_table():
    markdown = """
| Cell 1 | Cell 2 |
| Cell 3 | Cell 4 |
"""
    result = parse_table(markdown)
    
    assert result.headers is None
    assert len(result.rows) == 2
    assert result.rows[0] == ["Cell 1", "Cell 2"]

def test_alignment_row():
    markdown = """
| H1 | H2 | H3 |
| :--- | :---: | ---: |
| L | C | R |
"""
    result = parse_table(markdown)
    assert result.headers == ["H1", "H2", "H3"]
    assert result.rows[0] == ["L", "C", "R"]

def test_json_output():
    markdown = """
| Name | Age |
| --- | --- |
| Alice | 30 |
"""
    result = parse_table(markdown)
    
    # Convert to dict for JSON serialization check
    output = {
        "headers": result.headers,
        "rows": result.rows
    }
    
    json_str = json.dumps(output)
    assert "Alice" in json_str
    assert "30" in json_str

def test_multi_table_workbook():
    markdown = """
# Tables

## Sheet 1

| Col A | Col B |
| --- | --- |
| 1 | 2 |

## Sheet 2

| Col X | Col Y |
| --- | --- |
| 9 | 8 |

| Col Z |
| --- |
| 7 |
"""
    schema = MultiTableParsingSchema()
    workbook = parse_workbook(markdown, schema)
    
    assert len(workbook.sheets) == 2
    
    sheet1 = workbook.sheets[0]
    assert sheet1.name == "Sheet 1"
    assert len(sheet1.tables) == 1
    assert sheet1.tables[0].headers == ["Col A", "Col B"]
    assert sheet1.tables[0].rows[0] == ["1", "2"]
    
    sheet2 = workbook.sheets[1]
    assert sheet2.name == "Sheet 2"
    assert len(sheet2.tables) == 2
    assert sheet2.tables[0].headers == ["Col X", "Col Y"]
    assert sheet2.tables[1].headers == ["Col Z"]

def test_workbook_strict_root():
    markdown = """
This content should be ignored.
# Tables

## Sheet 1
| A |
|---|
| 1 |
"""
    schema = MultiTableParsingSchema()
    workbook = parse_workbook(markdown, schema)
    assert len(workbook.sheets) == 1
    assert workbook.sheets[0].name == "Sheet 1"

def test_workbook_missing_root():
    markdown = """
## Sheet 1
| A |
|---|
| 1 |
"""
    schema = MultiTableParsingSchema()
    workbook = parse_workbook(markdown, schema)
    assert len(workbook.sheets) == 0

def test_workbook_json_structure():
    markdown = """
# Tables

## MySheet

| A |
|---|
| 1 |
"""
    schema = MultiTableParsingSchema()
    workbook = parse_workbook(markdown, schema)
    
    # Simulate JSON serialization
    def workbook_to_dict(wb: Workbook):
        return {
            "sheets": [
                {
                    "name": sheet.name,
                    "tables": [
                        {
                            "headers": t.headers,
                            "rows": t.rows
                        } for t in sheet.tables
                    ]
                } for sheet in wb.sheets
            ]
        }
        
    data = workbook_to_dict(workbook)
    assert data["sheets"][0]["name"] == "MySheet"
    assert data["sheets"][0]["tables"][0]["headers"] == ["A"]
