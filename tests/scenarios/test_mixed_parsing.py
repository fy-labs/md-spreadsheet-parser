from md_spreadsheet_parser import MultiTableParsingSchema, parse_workbook


def test_mixed_header_levels():
    markdown = """
# Tables

## Users

### User Table

This is a user table.

| ID | Name |
| --- | --- |
| 1 | Alice |
| 2 | Bob |

## Products

| ID | Item |
| -- | ---- |
| A  | Apple|
"""
    schema = MultiTableParsingSchema(table_header_level=3, capture_description=True)
    workbook = parse_workbook(markdown, schema)

    assert len(workbook.sheets) == 2

    # Verify Sheet 1: Users
    users_sheet = workbook.sheets[0]
    assert users_sheet.name == "Users"
    assert len(users_sheet.tables) == 1

    user_table = users_sheet.tables[0]
    assert user_table.name == "User Table"
    assert user_table.description is not None
    assert "This is a user table." in user_table.description
    assert user_table.headers == ["ID", "Name"]
    assert len(user_table.rows) == 2
    assert user_table.rows[0] == ["1", "Alice"]

    # Verify Sheet 2: Products
    products_sheet = workbook.sheets[1]
    assert products_sheet.name == "Products"
    # This assertion checks if the unnamed table is captured
    assert len(products_sheet.tables) == 1

    product_table = products_sheet.tables[0]
    assert product_table.name is None  # Should have no name
    assert product_table.headers == ["ID", "Item"]
    assert len(product_table.rows) == 1
    assert product_table.rows[0] == ["A", "Apple"]
