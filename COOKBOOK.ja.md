# レシピ集

このガイドでは、一般的なタスクに対する即座の解決策を提供します。

## 目次
1. [インストール](#1-インストール)
2. [ファイルからテーブルを読み込む](#2-ファイルからテーブルを読み込む-推奨)
3. [テキストからテーブルを読み込む](#3-テキストからテーブルを読み込む-シンプル)
4. [Excel 連携](#4-excel-連携)
5. [Pandas 連携](#5-pandas-連携)
6. [プログラムによる編集](#6-プログラムによる編集-excelライク)
7. [フォーマットとLint](#7-フォーマットとlint)
8. [JSON変換](#8-json変換)
9. [型安全な検証](#9-型安全な検証)

## 1. インストール

```bash
pip install md-spreadsheet-parser
```

## 2. ファイルからテーブルを読み込む (推奨)

Markdownファイルからデータを抽出する最も簡単な方法は `scan_tables_from_file` を使用することです。これはファイル構造（`#` や `##` などのヘッダー）に関係なく機能します。

**data.md**
```markdown
| ID | Name |
| -- | ---- |
| 1  | Alice |
| 2  | Bob   |
```

**Python**
```python
from md_spreadsheet_parser import scan_tables_from_file

# Tableオブジェクトのリストを返します
tables = scan_tables_from_file("data.md")

for table in tables:
    print(table.rows)
    # [['1', 'Alice'], ['2', 'Bob']]
```

## 3. テキストからテーブルを読み込む (シンプル)

Markdown文字列がある場合は、`parse_table` を使用します。

```python
from md_spreadsheet_parser import parse_table

markdown = """
| ID | Name |
| -- | ---- |
| 1  | Alice |
"""

table = parse_table(markdown)
print(table.headers) # ['ID', 'Name']
print(table.rows[0]) # ['1', 'Alice']
```

## 4. Excel 連携

### Excel (TSV/CSV) → Markdown

**これが最も簡単な方法です！** Excelのセルをコピーして、文字列として貼り付けるだけです。

ExcelからエクスポートされたTSVまたはCSVデータをMarkdownに変換します。結合されたヘッダーやセル内改行も処理します。

```python
from md_spreadsheet_parser import parse_excel, ExcelParsingSchema

# Excelデータ (TSV形式) を貼り付けます
tsv_data = """
ID\tName\tNotes
1\tAlice\t"Lines
include
newlines"
2\tBob\tSimple
""".strip()

table = parse_excel(tsv_data)
print(table.to_markdown())
```

**結合ヘッダーあり (前方埋め)**
```python
# Excelの結合セルは次のようにエクスポートされます: "Category\t\t\tInfo"
tsv = "Category\t\t\tInfo\nA\tB\tC\tD"
table = parse_excel(tsv)
# Headers: ["Category", "Category", "Category", "Info"]
```

**2行階層ヘッダーあり**
```python
# 親行: "Info\t\tMetrics\t"
# 子行: "Name\tID\tScore\tRank"
tsv = "Info\t\tMetrics\t\nName\tID\tScore\tRank\nAlice\t001\t95\t1"
table = parse_excel(tsv, ExcelParsingSchema(header_rows=2))
# Headers: ["Info - Name", "Info - ID", "Metrics - Score", "Metrics - Rank"]
```

### Excel (.xlsx) → Markdown (with openpyxl)

`openpyxl` がインストールされている場合は、Worksheetを直接渡すことができます。

```python
# pip install openpyxl  # ユーザー管理の依存関係
import openpyxl
from md_spreadsheet_parser import parse_excel, ExcelParsingSchema

wb = openpyxl.load_workbook("report.xlsx", data_only=True)
ws = wb["SalesData"]  # 名前でシートを選択

table = parse_excel(ws, ExcelParsingSchema(header_rows=2))
print(table.to_markdown())
```

## 5. Pandas 連携

このライブラリは、Markdownとデータサイエンスツールの架け橋として機能します。

### Markdown -> Pandas DataFrame

解析されたテーブルを直接辞書のリストに変換し、Pandasに取り込めるようにします。

```python
import pandas as pd
from md_spreadsheet_parser import scan_tables_from_file

tables = scan_tables_from_file("data.md")
df = pd.DataFrame(tables[0].to_models(dict))

print(df)
#   ID   Name
# 0  1  Alice
# 1  2    Bob
```

### Pandas DataFrame -> Markdown

Pandas DataFrame を `Table` オブジェクトに変換してMarkdownを生成します。

```python
import pandas as pd
from md_spreadsheet_parser import Table

# 1. DataFrameのセットアップ
df = pd.DataFrame({
    "ID": [1, 2],
    "Name": ["Alice", "Bob"]
})

# 2. Tableへの変換
# パーサーのためにすべてのデータが文字列化されていることを確認してください
headers = df.columns.tolist()
rows = df.astype(str).values.tolist()

table = Table(headers=headers, rows=rows)

# 3. Markdownの生成
print(table.to_markdown())
# | ID | Name |
# | --- | --- |
# | 1 | Alice |
# | 2 | Bob |
```

## 6. プログラムによる編集 (Excelライク)

テーブルを読み込み、ロジック（数式など）に基づいて値を変更し、保存し直すことができます。

```python
from md_spreadsheet_parser import parse_table

markdown = """
| Item | Price | Qty | Total |
|---|---|---|---|
| Apple | 100 | 2 | |
| Banana | 50 | 3 | |
"""

table = parse_table(markdown)

# "Total" 列の更新
# 1. 基本的な文字列解析 (または安全な型のために to_models を使用)
new_rows = []
for row in table.rows:
    price = int(row[1])
    qty = int(row[2])
    total = price * qty
    
    # 更新されたTotalを含む新しい行を作成
    new_rows.append([row[0], row[1], row[2], str(total)])

# 2. 更新されたテーブルの作成
updated_table = Table(headers=table.headers, rows=new_rows)
print(updated_table.to_markdown())
```

## 7. フォーマットとLint

乱雑で配置のずれたMarkdownテーブルを読み込み、完璧にフォーマットして出力します。

```python
from md_spreadsheet_parser import parse_table

# 乱雑な入力
messy_markdown = """
|Name|Age|
|---|---|
|Alice|30|
|Bob|25|
"""

table = parse_table(messy_markdown)

# きれいなMarkdownを出力
print(table.to_markdown())
# | Name | Age |
# | --- | --- |
# | Alice | 30 |
# | Bob | 25 |
```

## 8. JSON変換

テーブルを直接JSON文字列またはAPI利用のための辞書のリストに変換します。

```python
import json
from md_spreadsheet_parser import parse_table

markdown = """
| ID | Status |
| -- | ------ |
| 1  | Open   |
"""

table = parse_table(markdown)

# 辞書のリストに変換
data = table.to_models(dict)

# JSONへのダンプ
print(json.dumps(data, indent=2))
# [
#   {
#     "ID": "1",
#     "Status": "Open"
#   }
# ]
```

## 9. 型安全な検証

ルーズなテキストを強く型付けされたPythonオブジェクトに変換します。

```python
from dataclasses import dataclass
from md_spreadsheet_parser import parse_table

@dataclass
class User:
    id: int
    name: str
    active: bool = True

markdown = """
| id | name | active |
| -- | ---- | ------ |
| 1  | Alice| yes    |
| 2  | Bob  | no     |
"""

users = parse_table(markdown).to_models(User)

for user in users:
    print(f"{user.name} (Active: {user.active})")
    # Alice (Active: True)
    # Bob (Active: False)
```
