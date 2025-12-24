import json
from md_spreadsheet_parser import (
    MultiTableParsingSchema,
    ParsingSchema,
    Sheet,
    Table,
    Workbook,
    parse_sheet,
    parse_table,
    parse_workbook,
)


# ==========================================
# Workbook Model Metadata Tests
# ==========================================


def test_workbook_metadata_init():
    """Verify Workbook can be initialized with metadata."""
    wb = Workbook(sheets=[], metadata={"author": "Alice", "version": 1})
    assert wb.metadata == {"author": "Alice", "version": 1}
    assert wb.json["metadata"] == {"author": "Alice", "version": 1}


def test_workbook_metadata_default():
    """Verify Workbook metadata defaults to empty dict if not provided."""
    wb = Workbook(sheets=[])
    assert wb.metadata == {}
    assert wb.json["metadata"] == {}


def test_workbook_metadata_json_serialization():
    """Verify metadata is correctly included in JSON output."""
    wb = Workbook(sheets=[], metadata={"key": "value", "nested": {"a": 1}})
    json_output = wb.json
    assert "metadata" in json_output
    assert json_output["metadata"]["key"] == "value"
    assert json_output["metadata"]["nested"]["a"] == 1


def test_hierarchy_metadata():
    """
    Verify metadata can exist at all levels (Workbook -> Sheet -> Table).
    Tests pattern coverage:
    - Workbook: Yes
    - Sheet: Yes
    - Table: Yes/No
    """
    t1_meta = Table(headers=["A"], rows=[["1"]], metadata={"source": "api"})
    t2_no_meta = Table(headers=["B"], rows=[["2"]])  # metadata default None -> {}

    s1 = Sheet(name="S1", tables=[t1_meta, t2_no_meta], metadata={"sheet_id": 101})

    wb = Workbook(sheets=[s1], metadata={"env": "prod"})

    # Check Workbook
    assert wb.metadata is not None
    assert wb.metadata["env"] == "prod"

    # Check Sheet
    sheet = wb.sheets[0]
    assert sheet.metadata is not None
    assert sheet.metadata["sheet_id"] == 101

    # Check Tables
    assert sheet.tables[0].metadata is not None
    assert sheet.tables[0].metadata["source"] == "api"
    assert sheet.tables[1].metadata == {}


def test_workbook_immutability_with_metadata():
    """Verify metadata doesn't break frozen dataclass behavior (via copy/replace)."""
    wb = Workbook(sheets=[], metadata={"v": 1})

    # Simulating a "migration" or update which returns a new workbook
    from dataclasses import replace

    new_wb = replace(wb, metadata={"v": 2})

    assert wb.metadata is not None
    assert wb.metadata["v"] == 1
    assert new_wb.metadata is not None
    assert new_wb.metadata["v"] == 2


# ==========================================
# Workbook Metadata Persistence Tests
# ==========================================


def test_parse_workbook_metadata_at_end():
    """Verify parsing Workbook metadata from the end of the file."""
    markdown = """# Tables

## Sheet1

| A | B |
|---|---|
| 1 | 2 |

<!-- md-spreadsheet-workbook-metadata: {"author": "Alice"} -->"""

    wb = parse_workbook(markdown)
    assert wb.metadata == {"author": "Alice"}
    assert len(wb.sheets) == 1
    assert wb.sheets[0].name == "Sheet1"


def test_generate_workbook_metadata_at_end():
    """Verify generation appends Workbook metadata to the end."""
    wb = Workbook(
        sheets=[Sheet("Sheet1", tables=[Table(["A"], [["1"]])])],
        metadata={"version": 1.0},
    )

    md = wb.to_markdown(MultiTableParsingSchema())

    expected_suffix = '<!-- md-spreadsheet-workbook-metadata: {"version": 1.0} -->'
    assert md.strip().endswith(expected_suffix)
    assert "# Sheet1" in md


def test_metadata_conflict_resolution():
    """
    Verify strict separation between Sheet metadata (last sheet) and Workbook metadata.
    Scenario:
    - Sheet1
    - Sheet Metadata
    - Workbook Metadata
    """

    sheet_meta = {"sheet_key": "s_val"}
    wb_meta = {"wb_key": "w_val"}

    markdown = f"""# Tables

## Sheet1

| A |
|---|
| 1 |

<!-- md-spreadsheet-sheet-metadata: {json.dumps(sheet_meta)} -->
<!-- md-spreadsheet-workbook-metadata: {json.dumps(wb_meta)} -->"""

    wb = parse_workbook(markdown)

    # Verify Workbook Metadata
    assert wb.metadata == wb_meta

    # Verify Sheet Metadata
    assert len(wb.sheets) == 1
    sheet = wb.sheets[0]
    assert sheet.metadata == sheet_meta


def test_metadata_roundtrip():
    """Verify Parse(Generate(WB)) == WB with metadata."""
    wb = Workbook(
        sheets=[
            Sheet(
                "S1",
                tables=[Table(["A"], [["1"]], metadata={"visual": {"t": 1}})],
                metadata={"s": 1},
            )
        ],
        metadata={"w": 1, "nested": {"a": [1, 2]}},
    )

    schema = MultiTableParsingSchema()
    generated_md = wb.to_markdown(schema)
    parsed_wb = parse_workbook(generated_md, schema)

    assert parsed_wb.metadata == wb.metadata
    assert parsed_wb.sheets[0].metadata == wb.sheets[0].metadata

    # Table metadata is persisted if under "visual"
    t_parsed = parsed_wb.sheets[0].tables[0]
    t_orig = wb.sheets[0].tables[0]

    assert t_parsed.metadata is not None
    assert t_orig.metadata is not None

    assert t_parsed.metadata["visual"] == t_orig.metadata["visual"]


# ==========================================
# Component (Sheet/Table) Metadata Persistence Tests
# ==========================================


def test_table_metadata_persistence_generation():
    """Verify Table.to_markdown generates metadata comment."""
    metadata = {"key": "value", "num": 123}
    # Metadata must be under "visual" key for Table to include it in output
    # (Current implementation limitation/design for Tables)
    table_metadata = {"visual": metadata}

    table = Table(headers=["A"], rows=[["1"]], metadata=table_metadata)

    md = table.to_markdown(ParsingSchema())

    # Check for metadata comment
    expected_comment = f"<!-- md-spreadsheet-metadata: {json.dumps(metadata)} -->"
    assert expected_comment in md


def test_table_metadata_persistence_parsing():
    """Verify parse_table extracts metadata comment."""
    metadata = {"key": "value", "num": 123}
    markdown = f"""| A |
|---|
| 1 |

<!-- md-spreadsheet-metadata: {json.dumps(metadata)} -->"""

    table = parse_table(markdown)

    assert table.metadata is not None
    assert "visual" in table.metadata
    assert table.metadata["visual"] == metadata
    assert table.headers == ["A"]
    assert table.rows == [["1"]]


def test_nested_table_metadata_persistence():
    """Verify Table metadata handles nested JSON structures."""
    nested_meta = {"config": {"color": "red", "visible": True}}
    table_metadata = {"visual": nested_meta}

    table = Table(headers=["A"], rows=[["1"]], metadata=table_metadata)

    md = table.to_markdown(ParsingSchema())
    parsed_table = parse_table(md)

    assert parsed_table.metadata is not None
    assert parsed_table.metadata["visual"] == nested_meta


def test_sheet_metadata_persistence_generation():
    """Verify Sheet.to_markdown generates metadata comment."""
    metadata = {"sheet_id": "s1", "protected": True}

    sheet = Sheet(
        name="Sheet1", tables=[Table(headers=["A"], rows=[["1"]])], metadata=metadata
    )

    md = sheet.to_markdown(MultiTableParsingSchema())

    # Check for metadata comment
    expected_comment = f"<!-- md-spreadsheet-sheet-metadata: {json.dumps(metadata)} -->"
    assert expected_comment in md
    assert "## Sheet1" in md


def test_sheet_metadata_persistence_parsing():
    """Verify parse_sheet extracts metadata comment."""
    metadata = {"sheet_id": "s1", "protected": True}

    markdown = f"""
| A |
|---|
| 1 |

<!-- md-spreadsheet-sheet-metadata: {json.dumps(metadata)} -->
"""

    sheet = parse_sheet(markdown, "Sheet1", MultiTableParsingSchema())

    assert sheet.metadata == metadata
    assert len(sheet.tables) == 1
    assert sheet.tables[0].headers == ["A"]


def test_sheet_and_table_metadata_integration():
    """Verify both Sheet and Table metadata co-exist correctly."""
    sheet_meta = {"s": 1}
    table_meta = {"t": 2}

    markdown = f"""
| A |
|---|
| 1 |

<!-- md-spreadsheet-metadata: {json.dumps(table_meta)} -->

<!-- md-spreadsheet-sheet-metadata: {json.dumps(sheet_meta)} -->
"""

    sheet = parse_sheet(markdown, "Sheet1", MultiTableParsingSchema())

    assert sheet.metadata == sheet_meta
    assert len(sheet.tables) == 1
    # Table parsing puts implicit "schema_used" in metadata, and visual metadata under "visual"
    t_meta = sheet.tables[0].metadata
    assert t_meta is not None
    assert t_meta["visual"] == table_meta
