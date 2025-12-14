from md_spreadsheet_parser.models import Sheet, Table, Workbook


def test_workbook_add_sheet():
    wb = Workbook(sheets=[])
    new_wb = wb.add_sheet("New Sheet")

    assert len(new_wb.sheets) == 1
    assert new_wb.sheets[0].name == "New Sheet"
    assert len(new_wb.sheets[0].tables) == 1
    # Check default table structure
    assert new_wb.sheets[0].tables[0].headers == ["A", "B", "C"]


def test_workbook_delete_sheet():
    s1 = Sheet(name="S1", tables=[])
    s2 = Sheet(name="S2", tables=[])
    wb = Workbook(sheets=[s1, s2])

    new_wb = wb.delete_sheet(0)
    assert len(new_wb.sheets) == 1
    assert new_wb.sheets[0].name == "S2"


def test_table_update_cell_body():
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
    table = Table(headers=["A", "B"], rows=[["1", "2"], ["3", "4"]])

    # Delete first row
    t2 = table.delete_row(0)
    assert len(t2.rows) == 1
    assert t2.rows[0] == ["3", "4"]

    # Delete out of bounds (noop)
    t3 = table.delete_row(99)
    assert len(t3.rows) == 2


def test_table_delete_column():
    table = Table(headers=["A", "B", "C"], rows=[["1", "2", "3"]])

    # Delete column B (index 1)
    t2 = table.delete_column(1)
    assert t2.headers == ["A", "C"]
    assert t2.rows[0] == ["1", "3"]

    # Delete out of bounds (noop)
    t3 = table.delete_column(99)
    assert t3.headers == ["A", "B", "C"]


def test_table_clear_column_data():
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
