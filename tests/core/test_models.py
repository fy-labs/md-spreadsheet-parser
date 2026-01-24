"""
Tests for md_spreadsheet_parser.models module.

These tests verify that all model operations (Table, Sheet, Workbook) correctly
preserve all properties including metadata. Property preservation validation is
critical for NPM package migration where metadata type issues have occurred.
"""

from md_spreadsheet_parser.models import Sheet, Table, Workbook

# ============================================================================
# Table Tests
# ============================================================================


def test_table_update_cell_body():
    """Verify update_cell on body cells works correctly."""
    table = Table(headers=["A", "B"], rows=[["1", "2"]])

    # Update existing
    t2 = table.update_cell(0, 1, "Updated")
    assert t2.rows[0][1] == "Updated"
    # Original unchanged
    assert table.rows[0][1] == "2"

    # Expand rows
    t3 = table.update_cell(2, 0, "New Row")
    assert len(t3.rows) == 3
    assert t3.rows[2][0] == "New Row"
    assert t3.rows[1][0] == ""  # Intermediate was padded

    # Expand cols
    t4 = table.update_cell(0, 3, "New Col")
    assert len(t4.rows[0]) == 4
    assert t4.rows[0][3] == "New Col"


def test_table_update_cell_header():
    """Verify update_cell on header row works correctly."""
    table = Table(headers=["A", "B"], rows=[])

    t2 = table.update_cell(-1, 0, "X")
    assert t2.headers is not None
    assert t2.headers[0] == "X"

    # Expand header
    t3 = table.update_cell(-1, 3, "D")
    assert t3.headers is not None
    assert len(t3.headers) == 4
    assert t3.headers[3] == "D"


def test_table_delete_row():
    """Verify delete_row removes the correct row."""
    table = Table(headers=["A", "B"], rows=[["1", "2"], ["3", "4"]])

    # Delete first row
    t2 = table.delete_row(0)
    assert len(t2.rows) == 1
    assert t2.rows[0] == ["3", "4"]

    # Delete out of bounds (noop)
    t3 = table.delete_row(99)
    assert len(t3.rows) == 2


def test_table_delete_column():
    """Verify delete_column removes the correct column."""
    table = Table(headers=["A", "B", "C"], rows=[["1", "2", "3"]])

    # Delete column B (index 1)
    t2 = table.delete_column(1)
    assert t2.headers == ["A", "C"]
    assert t2.rows[0] == ["1", "3"]

    # Delete out of bounds (noop)
    t3 = table.delete_column(99)
    assert t3.headers == ["A", "B", "C"]


def test_table_clear_column_data():
    """Verify clear_column_data clears data but preserves headers."""
    table = Table(headers=["A", "B"], rows=[["1", "2"], ["3", "4"]])

    # Clear column A (index 0)
    t2 = table.clear_column_data(0)

    # Headers remain
    assert t2.headers == ["A", "B"]

    # Data cleared
    assert t2.rows[0][0] == ""
    assert t2.rows[1][0] == ""

    # Other column intact
    assert t2.rows[0][1] == "2"
    assert t2.rows[1][1] == "4"


def test_table_rename():
    """Verify rename preserves all properties including metadata."""
    table = Table(
        headers=["H1", "H2"],
        rows=[["a", "b"], ["c", "d"]],
        name="Old",
        description="Original description",
        metadata={"key1": "value1", "nested": {"inner": "data"}},
        alignments=["left", "right"],
        start_line=10,
        end_line=15,
    )

    new_table = table.rename("New")

    # Verify name changed
    assert new_table.name == "New"

    # Verify all properties preserved
    assert new_table.headers == ["H1", "H2"]
    assert new_table.rows == [["a", "b"], ["c", "d"]]
    assert new_table.description == "Original description"
    assert new_table.alignments == ["left", "right"]
    assert new_table.start_line == 10
    assert new_table.end_line == 15

    # Verify metadata preserved (type, value, and nested structure)
    assert new_table.metadata == {"key1": "value1", "nested": {"inner": "data"}}
    assert isinstance(new_table.metadata, dict)
    assert isinstance(new_table.metadata["nested"], dict)


def test_table_move_row():
    """Verify move_row preserves all properties including metadata."""
    table = Table(
        headers=["H1", "H2"],
        rows=[["a1", "a2"], ["b1", "b2"], ["c1", "c2"]],
        name="TestTable",
        description="Test description",
        metadata={"key": "value"},
        alignments=["left", "center"],
        start_line=5,
        end_line=10,
    )

    new_table = table.move_row(0, 2)

    # Verify row order changed
    assert new_table.rows == [["b1", "b2"], ["c1", "c2"], ["a1", "a2"]]

    # Verify all other properties preserved
    assert new_table.headers == ["H1", "H2"]
    assert new_table.name == "TestTable"
    assert new_table.description == "Test description"
    assert new_table.alignments == ["left", "center"]
    assert new_table.start_line == 5
    assert new_table.end_line == 10

    # Verify metadata preserved
    assert new_table.metadata == {"key": "value"}
    assert isinstance(new_table.metadata, dict)


def test_table_move_column():
    """Verify move_column preserves all properties including metadata."""
    table = Table(
        headers=["A", "B", "C"],
        rows=[["1", "2", "3"], ["4", "5", "6"]],
        name="TestTable",
        description="Test description",
        metadata={"key": "value", "array": [1, 2, 3]},
        alignments=["left", "center", "right"],
        start_line=1,
        end_line=5,
    )

    new_table = table.move_column(0, 2)

    # Verify column order changed in headers and all rows
    assert new_table.headers == ["B", "C", "A"]
    assert new_table.rows == [["2", "3", "1"], ["5", "6", "4"]]

    # Verify alignments moved with columns
    assert new_table.alignments == ["center", "right", "left"]

    # Verify all other properties preserved
    assert new_table.name == "TestTable"
    assert new_table.description == "Test description"
    assert new_table.start_line == 1
    assert new_table.end_line == 5

    # Verify metadata preserved (type, value, and array)
    assert new_table.metadata == {"key": "value", "array": [1, 2, 3]}
    assert isinstance(new_table.metadata, dict)
    assert isinstance(new_table.metadata["array"], list)


# ============================================================================
# Sheet Tests
# ============================================================================


def test_sheet_rename():
    """Verify rename preserves all properties including metadata and tables."""
    t1 = Table(
        headers=["H1"],
        rows=[["data"]],
        name="T1",
        metadata={"table_key": "table_value"},
    )
    sheet = Sheet(name="Old", tables=[t1], metadata={"sheet_key": "sheet_value"})

    new_sheet = sheet.rename("New")

    # Verify name changed
    assert new_sheet.name == "New"

    # Verify metadata preserved (type and value)
    assert new_sheet.metadata == {"sheet_key": "sheet_value"}
    assert isinstance(new_sheet.metadata, dict)

    # Verify tables preserved
    assert len(new_sheet.tables) == 1
    assert new_sheet.tables[0].name == "T1"
    assert new_sheet.tables[0].metadata == {"table_key": "table_value"}


def test_sheet_add_table():
    """Verify add_table preserves existing tables and metadata."""
    t1 = Table(
        headers=["H1", "H2"],
        rows=[["a", "b"]],
        name="Existing",
        metadata={"existing_key": "existing_value"},
    )
    sheet = Sheet(name="S", tables=[t1], metadata={"sheet_key": "sheet_value"})

    new_sheet = sheet.add_table("MyTable")

    # Verify table added
    assert len(new_sheet.tables) == 2
    assert new_sheet.tables[1].name == "MyTable"
    assert new_sheet.tables[1].headers == ["A", "B", "C"]  # Default headers

    # Verify sheet metadata preserved
    assert new_sheet.metadata == {"sheet_key": "sheet_value"}
    assert isinstance(new_sheet.metadata, dict)

    # Verify existing table unchanged
    assert new_sheet.tables[0].name == "Existing"
    assert new_sheet.tables[0].metadata == {"existing_key": "existing_value"}
    assert isinstance(new_sheet.tables[0].metadata, dict)


def test_sheet_delete_table():
    """Verify delete_table preserves remaining tables and all metadata."""
    t1 = Table(
        headers=["A"],
        rows=[["1"]],
        name="T1",
        metadata={"t1_key": "t1_value"},
        description="Table 1 description",
    )
    t2 = Table(
        headers=["B"],
        rows=[["2"]],
        name="T2",
        metadata={"t2_key": "t2_value"},
        description="Table 2 description",
    )
    sheet = Sheet(name="S", tables=[t1, t2], metadata={"sheet_key": "sheet_value"})

    new_sheet = sheet.delete_table(0)

    # Verify deletion
    assert len(new_sheet.tables) == 1
    assert new_sheet.tables[0].name == "T2"

    # Verify sheet metadata preserved
    assert new_sheet.metadata == {"sheet_key": "sheet_value"}
    assert isinstance(new_sheet.metadata, dict)

    # Verify remaining table fully preserved
    assert new_sheet.tables[0].metadata == {"t2_key": "t2_value"}
    assert isinstance(new_sheet.tables[0].metadata, dict)
    assert new_sheet.tables[0].description == "Table 2 description"
    assert new_sheet.tables[0].rows == [["2"]]


def test_sheet_replace_table():
    """Verify replace_table preserves sheet metadata and other tables."""
    t1 = Table(headers=["A"], rows=[], name="T1", metadata={"t1_key": "t1_value"})
    t2 = Table(headers=["B"], rows=[], name="T2", metadata={"t2_key": "t2_value"})
    sheet = Sheet(name="S", tables=[t1, t2], metadata={"sheet_key": "sheet_value"})

    replacement = Table(
        headers=["X", "Y"],
        rows=[["x1", "y1"]],
        name="Replaced",
        metadata={"new_key": "new_value"},
        description="New description",
    )
    new_sheet = sheet.replace_table(0, replacement)

    # Verify replacement
    assert new_sheet.tables[0].name == "Replaced"
    assert new_sheet.tables[0].metadata == {"new_key": "new_value"}
    assert new_sheet.tables[0].description == "New description"
    assert new_sheet.tables[0].headers == ["X", "Y"]

    # Verify sheet metadata preserved
    assert new_sheet.metadata == {"sheet_key": "sheet_value"}
    assert isinstance(new_sheet.metadata, dict)

    # Verify other table unchanged
    assert new_sheet.tables[1].name == "T2"
    assert new_sheet.tables[1].metadata == {"t2_key": "t2_value"}


def test_sheet_move_table():
    """Verify move_table preserves all table properties including metadata."""
    t1 = Table(
        headers=["A"],
        rows=[["1"]],
        name="T1",
        metadata={"t1_key": "t1_value"},
        alignments=["left"],
    )
    t2 = Table(
        headers=["B"],
        rows=[["2"]],
        name="T2",
        metadata={"t2_key": "t2_value"},
        alignments=["center"],
    )
    t3 = Table(
        headers=["C"],
        rows=[["3"]],
        name="T3",
        metadata={"t3_key": "t3_value"},
        alignments=["right"],
    )
    sheet = Sheet(name="S", tables=[t1, t2, t3], metadata={"sheet_key": "sheet_value"})

    new_sheet = sheet.move_table(0, 2)

    # Verify order changed
    assert [t.name for t in new_sheet.tables] == ["T2", "T3", "T1"]

    # Verify sheet metadata preserved
    assert new_sheet.metadata == {"sheet_key": "sheet_value"}
    assert isinstance(new_sheet.metadata, dict)

    # Verify all table properties preserved after move
    moved_table = new_sheet.tables[2]  # T1 is now at index 2
    assert moved_table.metadata == {"t1_key": "t1_value"}
    assert isinstance(moved_table.metadata, dict)
    assert moved_table.alignments == ["left"]
    assert moved_table.rows == [["1"]]


# ============================================================================
# Workbook Tests
# ============================================================================


def test_workbook_add_sheet():
    """Verify add_sheet creates sheet with default structure."""
    wb = Workbook(sheets=[], metadata={"wb_key": "wb_value"})
    new_wb = wb.add_sheet("New Sheet")

    assert len(new_wb.sheets) == 1
    assert new_wb.sheets[0].name == "New Sheet"
    assert len(new_wb.sheets[0].tables) == 1
    assert new_wb.sheets[0].tables[0].headers == ["A", "B", "C"]

    # Verify workbook metadata preserved
    assert new_wb.metadata == {"wb_key": "wb_value"}
    assert isinstance(new_wb.metadata, dict)


def test_workbook_delete_sheet():
    """Verify delete_sheet preserves remaining sheets and metadata."""
    s1 = Sheet(name="S1", tables=[], metadata={"s1_key": "s1_value"})
    s2 = Sheet(name="S2", tables=[], metadata={"s2_key": "s2_value"})
    wb = Workbook(sheets=[s1, s2], metadata={"wb_key": "wb_value"})

    new_wb = wb.delete_sheet(0)

    assert len(new_wb.sheets) == 1
    assert new_wb.sheets[0].name == "S2"

    # Verify metadata preserved
    assert new_wb.metadata == {"wb_key": "wb_value"}
    assert isinstance(new_wb.metadata, dict)
    assert new_wb.sheets[0].metadata == {"s2_key": "s2_value"}


def test_workbook_move_sheet():
    """Verify move_sheet preserves all properties including metadata."""
    t1 = Table(
        headers=["H1"],
        rows=[["data"]],
        name="T1",
        metadata={"table_key": "table_value"},
        alignments=["left"],
    )
    s1 = Sheet(name="S1", tables=[t1], metadata={"s1_key": "s1_value"})
    s2 = Sheet(name="S2", tables=[], metadata={"s2_key": "s2_value"})
    s3 = Sheet(name="S3", tables=[], metadata={"s3_key": "s3_value"})
    wb = Workbook(sheets=[s1, s2, s3], metadata={"wb_key": "wb_value"})

    new_wb = wb.move_sheet(0, 2)

    # Verify order changed
    assert [s.name for s in new_wb.sheets] == ["S2", "S3", "S1"]

    # Verify workbook metadata preserved
    assert new_wb.metadata == {"wb_key": "wb_value"}
    assert isinstance(new_wb.metadata, dict)

    # Verify sheet metadata preserved after move
    assert new_wb.sheets[2].metadata == {"s1_key": "s1_value"}
    assert isinstance(new_wb.sheets[2].metadata, dict)

    # Verify nested table metadata preserved
    assert new_wb.sheets[2].tables[0].metadata == {"table_key": "table_value"}
    assert isinstance(new_wb.sheets[2].tables[0].metadata, dict)


def test_workbook_replace_sheet():
    """Verify replace_sheet preserves all properties including metadata."""
    s1 = Sheet(name="S1", tables=[], metadata={"s1_key": "s1_value"})
    s2 = Sheet(name="S2", tables=[], metadata={"s2_key": "s2_value"})
    wb = Workbook(sheets=[s1, s2], metadata={"wb_key": "wb_value"})

    new_sheet = Sheet(name="Replaced", tables=[], metadata={"new_key": "new_value"})
    new_wb = wb.replace_sheet(0, new_sheet)

    # Verify replacement
    assert new_wb.sheets[0].name == "Replaced"
    assert new_wb.sheets[1].name == "S2"

    # Verify workbook metadata preserved
    assert new_wb.metadata == {"wb_key": "wb_value"}
    assert isinstance(new_wb.metadata, dict)

    # Verify new sheet metadata is correct
    assert new_wb.sheets[0].metadata == {"new_key": "new_value"}
    assert isinstance(new_wb.sheets[0].metadata, dict)

    # Verify untouched sheet metadata preserved
    assert new_wb.sheets[1].metadata == {"s2_key": "s2_value"}


def test_workbook_rename_sheet():
    """Verify rename_sheet preserves all sheet properties including metadata."""
    t1 = Table(
        headers=["H1"],
        rows=[["data"]],
        name="T1",
        metadata={"table_key": "table_value"},
    )
    s1 = Sheet(name="S1", tables=[t1], metadata={"sheet_key": "sheet_value"})
    wb = Workbook(sheets=[s1], metadata={"wb_key": "wb_value"})

    new_wb = wb.rename_sheet(0, "NewName")

    # Verify name changed
    assert new_wb.sheets[0].name == "NewName"

    # Verify workbook metadata preserved
    assert new_wb.metadata == {"wb_key": "wb_value"}
    assert isinstance(new_wb.metadata, dict)

    # Verify sheet metadata preserved
    assert new_wb.sheets[0].metadata == {"sheet_key": "sheet_value"}
    assert isinstance(new_wb.sheets[0].metadata, dict)

    # Verify nested table preserved
    assert new_wb.sheets[0].tables[0].name == "T1"
    assert new_wb.sheets[0].tables[0].metadata == {"table_key": "table_value"}


def test_workbook_to_markdown():
    """Verify to_markdown works without arguments."""
    table = Table(headers=["A"], rows=[["1"]])
    sheet = Sheet(name="Sheet1", tables=[table])
    workbook = Workbook(sheets=[sheet])

    markdown = workbook.to_markdown()
    assert isinstance(markdown, str)
    # With new auto-detection, default workbook name is "Workbook"
    assert "# Workbook" in markdown
