from md_spreadsheet_parser import (
    MultiTableParsingSchema,
    parse_table,
    parse_workbook,
)


def test_workbook_end_boundary():
    """
    Test that workbook parsing stops when encountering a header that indicates
    the end of the workbook section (e.g. a higher-level header).
    """
    markdown = """
# Tables

## Sheet1
| ID | Name | Role |
|---|---|---|
| 1 | Alice | Admin |
| 2 | Bob | User |

# Next Section
This is unrelated documentation.
| X | Y |
|---|---|
| 9 | 9 |
"""
    schema = MultiTableParsingSchema(root_marker="# Tables", sheet_header_level=2)
    workbook = parse_workbook(markdown, schema)

    # Should have 1 sheet
    assert len(workbook.sheets) == 1
    sheet1 = workbook.sheets[0]
    assert sheet1.name == "Sheet1"

    # Sheet1 should have 1 table
    assert len(sheet1.tables) == 1
    table1 = sheet1.tables[0]
    assert table1.headers == ["ID", "Name", "Role"]
    assert len(table1.rows) == 2
    assert table1.rows[0] == ["1", "Alice", "Admin"]
    assert table1.rows[1] == ["2", "Bob", "User"]


def test_japanese_content():
    """
    Test parsing of Japanese content (headers, values, sheet names).
    """
    markdown = """
| ID | 名前 | 年齢 | 職業 | 備考 |
| -- | -- | -- | -- | -- |
| 1 | 田中 | 30 | エンジニア | リーダー |
| 2 | 佐藤 | 25 | デザイナー | 新卒 |
| 3 | 鈴木 | 40 | マネージャー | 兼務 |
"""
    table = parse_table(markdown)

    assert table.headers == ["ID", "名前", "年齢", "職業", "備考"]
    assert len(table.rows) == 3
    assert table.rows[0] == ["1", "田中", "30", "エンジニア", "リーダー"]
    assert table.rows[2] == ["3", "鈴木", "40", "マネージャー", "兼務"]


def test_emoji_content():
    """
    Test parsing of content with Emojis.
    """
    markdown = """
| Status | Item | Category | Priority |
| --- | --- | --- | --- |
| ✅ | Apple 🍎 | Fruit 🍇 | High ⬆️ |
| ❌ | Banana 🍌 | Fruit 🍇 | Low ⬇️ |
| ⚠️ | Car 🚗 | Vehicle 🚙 | Medium ➡️ |
"""
    table = parse_table(markdown)

    assert table.headers == ["Status", "Item", "Category", "Priority"]
    assert len(table.rows) == 3
    assert table.rows[0] == ["✅", "Apple 🍎", "Fruit 🍇", "High ⬆️"]
    assert table.rows[2] == ["⚠️", "Car 🚗", "Vehicle 🚙", "Medium ➡️"]


def test_workbook_japanese_sheet_names():
    markdown = """
# データ

## ユーザー一覧
| ID | 名前 | メール |
| -- | -- | -- |
| 1  | 太郎 | taro@example.com |
| 2  | 花子 | hanako@example.com |
"""
    schema = MultiTableParsingSchema(root_marker="# データ", sheet_header_level=2)
    workbook = parse_workbook(markdown, schema)

    assert len(workbook.sheets) == 1
    assert workbook.sheets[0].name == "ユーザー一覧"
    assert len(workbook.sheets[0].tables[0].rows) == 2
    assert workbook.sheets[0].tables[0].rows[0] == ["1", "太郎", "taro@example.com"]


def test_parse_workbook_ignores_code_blocks():
    """
    Test that headers inside markdown code blocks are ignored during workbook parsing.
    """
    md = """# Document Title

Comparison of something.

```markdown
# Tables
Here is an example of structure.
```

# Tables

## Sheet 1

| A | B |
|---|---|
| 1 | 2 |
"""
    schema = MultiTableParsingSchema(root_marker="# Tables", sheet_header_level=2)
    workbook = parse_workbook(md, schema)

    # Should ignore the first "# Tables" inside code block and find the second one.
    assert len(workbook.sheets) == 1
    assert workbook.sheets[0].name == "Sheet 1"


def test_parse_sheet_ignores_code_blocks():
    """
    Test that sheet headers inside code blocks are ignored.
    """
    md = """# Tables

## Sheet 1

Some description.

```python
# Not a sheet header
## Not a sheet header
```

| A | B |
|---|---|
| 1 | 2 |

## Sheet 2

| C | D |
|---|---|
| 3 | 4 |
"""
    schema = MultiTableParsingSchema(root_marker="# Tables", sheet_header_level=2)
    workbook = parse_workbook(md, schema)

    assert len(workbook.sheets) == 2
    assert workbook.sheets[0].name == "Sheet 1"
    assert workbook.sheets[1].name == "Sheet 2"
