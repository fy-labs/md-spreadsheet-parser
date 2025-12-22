from md_spreadsheet_parser.models import Table
from md_spreadsheet_parser.parsing import parse_table


def test_parse_alignment():
    markdown = """
| Left | Center | Right | Default |
| :--- | :---: | ---: | --- |
| L | C | R | D |
"""
    table = parse_table(markdown)
    assert table.alignments == ["left", "center", "right", "default"]


def test_parse_alignment_mixed_separators():
    # Test with varying number of hyphens
    markdown = """
| A | B |
|:- | -:|
| 1 | 2 |
"""
    table = parse_table(markdown)
    assert table.alignments == ["left", "right"]


def test_round_trip_alignment():
    markdown = """
| A | B | C |
| :--- | :---: | ---: |
| 1 | 2 | 3 |
"""
    table = parse_table(markdown)
    generated = table.to_markdown()

    # Check if generated markdown contains correct separators
    assert "| :--- | :---: | ---: |" in generated

    # Check if reparsing yields same alignments
    table2 = parse_table(generated)
    assert table2.alignments == ["left", "center", "right"]


def test_alignment_mutation_insert_column():
    table = Table(headers=["A", "B"], rows=[["1", "2"]], alignments=["left", "right"])

    # Insert at middle
    new_table = table.insert_column(1)

    assert new_table.headers == ["A", "", "B"]
    assert new_table.alignments == [
        "left",
        "default",
        "right",
    ]  # inserted should be default/empty/None depending on implementation.
    # My implementation inserts "default" for new column data.
    # Let's check models.py implementation.
    # `new_alignments.insert(col_idx, "")` -> Yes, empty string implies default.


def test_alignment_mutation_delete_column():
    table = Table(
        headers=["A", "B", "C"],
        rows=[["1", "2", "3"]],
        alignments=["left", "center", "right"],
    )

    new_table = table.delete_column(1)

    assert new_table.headers == ["A", "C"]
    assert new_table.alignments == ["left", "right"]


def test_alignment_mutation_update_cell_expand():
    # Start with valid table
    table = Table(headers=["A"], rows=[["1"]], alignments=["left"])

    # Update cell at column 2 (index 2), expanding table
    # A | (implicit) | (new)
    new_table = table.update_cell(0, 2, "Val")

    # Headers are NOT automatically expanded when body is updated
    assert new_table.headers is not None
    assert len(new_table.headers) == 1
    # But alignments SHOULD track the maximum width of data for consistency?
    # Or should they match headers?
    # Current implementation expands alignments if row expands beyond current alignment width.
    assert new_table.alignments is not None
    assert len(new_table.alignments) == 3
    assert new_table.alignments[0] == "left"
    assert new_table.alignments[1] in [None, "default"]  # expansion uses default
    assert new_table.alignments[2] in [None, "default"]  # match default


def test_alignment_mutation_without_headers():
    # Table without headers can still have alignments if manually set,
    # but mutation logic often relies on headers length logic.
    # If headers is None, alignments behavior should be safe.
    table = Table(headers=None, rows=[["1", "2"]], alignments=["left", "right"])

    # Update cell causing expansion
    new_table = table.update_cell(0, 2, "3")
    # Logic in update_cell: if self.headers is None...
    # It creates headers if we are implicitly creating them? No.
    # update_cell for body only updates rows if headers is None.
    # Ah, wait. `update_cell` implementation:
    # `width = len(self.headers) if self.headers else ...`
    # ...
    # `if col_idx >= current_width: ... if self.alignments is not None: ...`

    # So if alignments exists, it should expand.
    # Note: rows[0] access should be safe as we init with data
    assert len(new_table.rows[0]) == 3
    assert new_table.alignments is not None
    assert len(new_table.alignments) == 3
    assert new_table.alignments[0] == "left"
