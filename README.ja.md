# Markdown Spreadsheet Parser

<p align="center">
  <a href="https://github.com/f-y/md-spreadsheet-parser/blob/main/LICENSE">
    <img src="https://img.shields.io/badge/license-MIT-blue.svg" alt="License" />
  </a>
  <a href="https://pypi.org/project/md-spreadsheet-parser/">
    <img src="https://img.shields.io/badge/pypi-v0.8.0-blue" alt="PyPI" />
  </a>
  <a href="https://pepy.tech/projects/md-spreadsheet-parser"><img src="https://static.pepy.tech/personalized-badge/md-spreadsheet-parser?period=total&units=INTERNATIONAL_SYSTEM&left_color=GREY&right_color=BLUE&left_text=downloads" alt="PyPI Downloads"></a>
  <a href="https://github.com/f-y/md-spreadsheet-parser">
    <img src="https://img.shields.io/badge/repository-github-blue.svg" alt="Repository" />
  </a>
  <a href="https://github.com/f-y/md-spreadsheet-parser/actions?query=workflow%3ATests">
    <img src="https://github.com/f-y/md-spreadsheet-parser/workflows/Tests/badge.svg" alt="Build Status" />
  </a>
</p>

<p align="center">
  <strong>Markdownテーブル操作に特化したPythonライブラリ。ExcelからMarkdownへの変換、テーブルの解析、型安全な検証など。堅牢で依存関係ゼロ</strong>
</p>

---

**md-spreadsheet-parser** は、Markdownのテーブルを単なるテキストからファーストクラスのデータ構造へと昇華させます。スプレッドシートの手軽さとPythonの強力さを兼ね備え、正確かつ依存関係ゼロのエンジンでテーブルの解析、検証、操作を実現します。

🚀 **すぐに使いたいですか？** [Cookbook](https://github.com/f-y/md-spreadsheet-parser/blob/main/COOKBOOK.ja.md) には、コピー＆ペーストで使えるレシピ（Excel変換、Pandas連携、Markdownテーブル操作など）が満載です。

## 目次

- [機能](#機能)
- [インストール](#インストール)
- [使い方](#使い方)
    - [1. 基本的な解析](#1-基本的な解析)
    - [2. 型安全な検証](#2-型安全な検証-推奨)
        - [Pydantic連携](#pydantic連携)
    - [3. JSONと辞書への変換](#3-jsonと辞書への変換)
    - [4. Pandas連携とエクスポート](#4-pandas連携とエクスポート)
    - [5. Excelインポート](#5-excelインポート)
    - [6. Markdown生成](#6-markdown生成-ラウンドトリップ)
    - [7. 高度な機能](#7-高度な機能)
    - [8. 高度な型変換](#8-高度な型変換)
    - [9. 堅牢性](#9-堅牢性-不正なテーブルの処理)
    - [10. セル内改行のサポート](#10-セル内改行のサポート)
    - [11. パフォーマンスとスケーラビリティ](#11-パフォーマンスとスケーラビリティ-ストリーミングapi)
    - [12. プログラムによる操作](#12-プログラムによる操作)
    - [13. ビジュアルメタデータの永続化](#13-ビジュアルメタデータの永続化)
    - [コマンドラインインターフェース (CLI)](#コマンドラインインターフェース-cli)
- [設定](#設定)
- [今後のロードマップ](#今後のロードマップ)
- [ライセンス](#ライセンス)

## 機能

- **純粋なPythonと依存関係ゼロ**: 軽量でポータブルです。**AWS Lambda Layers** や制約のある環境に最適です。**WebAssembly (Pyodide)** を含む、Pythonが動作する場所ならどこでも動作します。
- **型安全な検証**: ルーズなMarkdownテーブルを、自動型変換を含む強力に型付けされたPythonの `dataclasses` に変換します。カスタマイズ可能なブール値ロジック (I18N) やカスタム型コンバータもサポートします。
- **データベースとしてのMarkdown**: MarkdownファイルをGit管理された設定やマスターデータとして扱えます。スキーマと型を自動的に検証し、手書きテーブルの人為的ミスを防ぎます。
- **ラウンドトリップサポート**: オブジェクトへの解析、データの変更、Markdownへの再生成が可能です。エディタの実装に最適です。
- **GFM準拠**: 列の配置 (`:--`, `:--:`, `--:`) やインラインコード内のパイプ (`` `|` ``) の正しい処理など、GitHub Flavored Markdown (GFM) 仕様をサポートしています。
- **堅牢な解析**: 不正なテーブル（列の欠落や過剰）やエスケープ文字を適切に処理します。
- **マルチテーブル・ワークブック**: 単一ファイルからの複数のシートやテーブルの解析、およびメタデータをサポートします。
- **JSONとDictのサポート**: 列レベルのJSON解析と、`dict`/`TypedDict` への直接変換をサポートします。
- **Pandas連携**: MarkdownテーブルからDataFrameをシームレスに作成できます。
- **Excelインポートとデータクリーニング**: Excel/TSV/CSVをMarkdownに変換し、結合セルをインテリジェントに処理します。階層ヘッダーのフラット化やギャップの埋め合わせを自動的に行い、「汚い」スプレッドシートをきれいな構造化データに変換します。
- **JSONフレンドリー**: 辞書/JSONへのエクスポートが容易で、他のツールとの連携も簡単です。

## インストール

```bash
pip install md-spreadsheet-parser
```

## 使い方

### 1. 基本的な解析

**単一のテーブル**
標準的なMarkdownテーブルを構造化オブジェクトに解析します。

```python
from md_spreadsheet_parser import parse_table

markdown = """
| Name | Age |
| --- | --- |
| Alice | 30 |
| Bob | 25 |
"""

result = parse_table(markdown)

print(result.headers)
# ['Name', 'Age']

print(result.rows)
# [['Alice', '30'], ['Bob', '25']]
```

**複数のテーブル (ワークブック)**
複数のシート（セクション）を含むファイルを解析します。デフォルトでは、ルートマーカーとして `# Tables`、シート用には `## Sheet Name` を探します。

```python
from md_spreadsheet_parser import parse_workbook, MultiTableParsingSchema

markdown = """
# Tables

## Users
| ID | Name |
| -- | ---- |
| 1  | Alice|

## Products
| ID | Item |
| -- | ---- |
| A  | Apple|
"""

# デフォルトスキーマを使用
schema = MultiTableParsingSchema()
workbook = parse_workbook(markdown, schema)

for sheet in workbook.sheets:
    print(f"Sheet: {sheet.name}")
    for table in sheet.tables:
        print(table.rows)
```

**ルックアップAPIとメタデータ**
シートやテーブルを名前で直接取得し、説明などの解析されたメタデータにアクセスできます。

```python
from md_spreadsheet_parser import parse_workbook

markdown = """
# Tables

## Sales Data

### Q1 Results
Financial performance for the first quarter.

| Year | Revenue |
| ---- | ------- |
| 2023 | 1000    |
"""

workbook = parse_workbook(markdown)

# 名前でアクセス
sheet = workbook.get_sheet("Sales Data")
if sheet:
    # 名前でテーブルを取得 (### Header から)
    table = sheet.get_table("Q1 Results")
    
    print(table.description)
    # "Financial performance for the first quarter."
    
    print(table.rows)
    # [['2023', '1000']]
```

**シンプルなスキャンインターフェース**
ドキュメントの構造（シートやヘッダー）を無視して、ファイル内の *すべての* テーブルを抽出したい場合は、`scan_tables` を使用します。

```python
from md_spreadsheet_parser import scan_tables

markdown = """
| ID | Name |
| -- | ---- |
| 1  | Alice|

... text ...

| ID | Item |
| -- | ---- |
| A  | Apple|
"""

# 見つかったすべてのテーブルのフラットリストを返す
tables = scan_tables(markdown)
print(len(tables)) # 2
```

**ファイル読み込みヘルパー**

利便性のため、`_from_file` バリアントを使用して、ファイルパス (`str` または `Path`) やファイルライクオブジェクトから直接解析できます：

```python
from md_spreadsheet_parser import parse_workbook_from_file

# 簡単でクリーン
workbook = parse_workbook_from_file("data.md")
```

利用可能なヘルパー:
- `parse_table_from_file(path_or_file)`
- `parse_workbook_from_file(path_or_file)`
- `scan_tables_from_file(path_or_file)`

### GFM機能のサポート

パーサーは、テーブルに関するGitHub Flavored Markdown (GFM) 仕様に厳密に準拠しています。

**列の配置**
区切り行の配置マーカーは解析され、保持されます。

```python
markdown = """
| Left | Center | Right |
| :--- | :----: | ----: |
| 1    | 2      | 3     |
"""
table = parse_table(markdown)
print(table.alignments)
# ["left", "center", "right"]
```

**コード内のパイプとエスケープ**
インラインコードブロック（バッククォート）内のパイプ `|` や、`\` でエスケープされたパイプは、列区切りではなくコンテンツとして正しく扱われます。

```python
markdown = """
| Code  | Escaped |
| ----- | ------- |
| `a|b` | \|      |
"""
table = parse_table(markdown)
# table.rows[0] == ["`a|b`", "|"]
```

### 2. 型安全な検証 (推奨)

このライブラリの最も強力な機能は、`dataclasses` を使用して、ルーズなMarkdownテーブルを強く型付けされたPythonオブジェクトに変換することです。これにより、データの妥当性が保証され、扱いやすくなります。

```python
from dataclasses import dataclass
from md_spreadsheet_parser import parse_table, TableValidationError

@dataclass
class User:
    name: str
    age: int
    is_active: bool = True

markdown = """
| Name | Age | Is Active |
|---|---|---|
| Alice | 30 | yes |
| Bob | 25 | no |
"""

try:
    # ワンステップで解析と検証
    users = parse_table(markdown).to_models(User)
    
    for user in users:
        print(f"{user.name} is {user.age} years old.")
        # Alice is 30 years old.
        # Bob is 25 years old.

except TableValidationError as e:
    print(e)
```

**機能:**
*   **型変換**: 文字列を標準的なルールで自動的に `int`, `float`, `bool` に変換します。
*   **ブール値の処理 (デフォルト)**: 標準的なペア `true/false`, `yes/no`, `on/off`, `1/0` を即座にサポートします。（カスタマイズについては [高度な型変換](#8-高度な型変換) を参照）。
*   **オプションフィールド**: 空文字列を `None` に変換することで `Optional[T]` を処理します。
*   **検証**: データがスキーマに一致しない場合、詳細なエラーを発生させます。

### Pydantic連携

より高度な検証（メール形式、範囲、正規表現）を行うには、dataclassesの代わりに [Pydantic](https://docs.pydantic.dev/) モデルを使用できます。`pydantic` がインストールされている場合、この機能は自動的に有効になります。

```python
from pydantic import BaseModel, Field, EmailStr

class User(BaseModel):
    name: str = Field(alias="User Name")
    age: int = Field(gt=0)
    email: EmailStr

# 自動的にPydanticモデルを検出し、検証に使用します
users = parse_table(markdown).to_models(User)
```

パーサーはPydanticの `alias` と `Field` 制約を尊重します。

### 3. JSONと辞書への変換

完全なDataclassやPydanticモデルを定義したくない場合や、JSON文字列を含む列がある場合の対応です。

**シンプルな辞書出力**
テーブルを辞書のリストに直接変換します。キーはヘッダーから派生します。

```python
# list[dict[str, Any]] を返します (値は生の文字列です)
rows = parse_table(markdown).to_models(dict)
print(rows[0])
# {'Name': 'Alice', 'Age': '30'}
```

**TypedDict サポート**
軽量な型安全性のために `TypedDict` を使用します。パーサーは型アノテーションを使用して値を自動的に変換します。

```python
from typing import TypedDict

class User(TypedDict):
    name: str
    age: int
    active: bool

rows = parse_table(markdown).to_models(User)
print(rows[0])
# {'name': 'Alice', 'age': 30, 'active': True}
```

**列レベルのJSON解析**
フィールドが `dict` または `list` として型付けされている場合（DataclassまたはPydanticモデル内）、パーサーは **セルの値を自動的にJSONとして解析** します。

```python
@dataclass
class Config:
    id: int
    metadata: dict  # セル: '{"debug": true}' -> dictに解析
    tags: list      # セル: '["a", "b"]'      -> listに解析

# PydanticモデルもJson[]ラッパーなしで動作します
class ConfigModel(BaseModel):
    metadata: dict
```

**制限事項:**
*   **JSON構文**: セルの内容は有効なJSONである必要があります（例: ダブルクォート `{"a": 1}`）。不正なJSONは `ValueError` を発生させます。
*   **単純な辞書解析**: `to_models(dict)` は、カスタムスキーマを使用しない限り、内部のJSON文字列を自動的には解析 *しません*。文字列の浅い辞書を作成するだけです。

### 4. Pandas連携とエクスポート

このライブラリは、Markdownと **Pandas** などのデータサイエンスツールの架け橋となるように設計されています。

**DataFrameへの変換 (最も簡単な方法)**
DataFrameを作成する最もきれいな方法は、`to_models(dict)` を使用することです。これはPandasが直接取り込める辞書のリストを返します。

```python
import pandas as pd
from md_spreadsheet_parser import parse_table

markdown = """
| Date       | Sales | Region |
|------------|-------|--------|
| 2023-01-01 | 100   | US     |
| 2023-01-02 | 150   | EU     |
"""

table = parse_table(markdown)

# 1. 辞書のリストに変換
data = table.to_models(dict)

# 2. DataFrameの作成
df = pd.DataFrame(data)

# 3. 後処理: 型変換 (Pandasは通常、最初は文字列として推論します)
df["Sales"] = pd.to_numeric(df["Sales"])
df["Date"] = pd.to_datetime(df["Date"])

print(df.dtypes)
# Date      datetime64[ns]
# Sales              int64
# Region            object
```

**型安全なオブジェクトからの変換**
DataFrameを作成する **前** にデータを検証したい場合（例: 解析中に "Sales" が整数であることを保証する）は、`dataclass` を使用してからPandasに変換します。

```python
from dataclasses import dataclass, asdict

@dataclass
class SalesRecord:
    date: str
    amount: int
    region: str

# 1. 解析と検証 (無効な場合はTableValidationErrorが発生)
records = parse_table(markdown).to_models(SalesRecord)

# 2. asdict()を使用してDataFrameに変換
df = pd.DataFrame([asdict(r) for r in records])

# 'amount' 列は検証時に変換されているため、すでにint64です
print(df["amount"].dtype) # int64
```

**JSONエクスポート**
すべての結果オブジェクト (`Workbook`, `Sheet`, `Table`) には、シリアライズに適した辞書構造を返す `.json` プロパティがあります。

```python
import json

# ワークブック構造全体をエクスポート
print(json.dumps(workbook.json, indent=2))
```


### 5. Excelインポート

結合セルや階層ヘッダーをインテリジェントに処理して、Excelデータ（TSV/CSVまたは `openpyxl` 経由）をインポートします。

> [!NOTE]
> TSV/CSVテキストからのインポートは **依存関係ゼロ** で動作します。`.xlsx` ファイルの直接読み込みには `openpyxl`（ユーザー管理のオプション依存関係）が必要です。

**基本的な使い方**

🚀 **より包括的なレシピについては [Cookbook](https://github.com/f-y/md-spreadsheet-parser/blob/main/COOKBOOK.ja.md) をご覧ください。**

```python
from md_spreadsheet_parser import parse_excel

# TSV/CSVから (依存関係ゼロ)
table = parse_excel("Name\tAge\nAlice\t30")

# .xlsxから (openpyxlが必要)
import openpyxl
wb = openpyxl.load_workbook("data.xlsx")
table = parse_excel(wb.active)
```

**結合ヘッダーの処理**

Excelが結合セルをエクスポートすると、それらは空のセルとして表示されます。パーサーはこれらのギャップを自動的に前方埋めします：

```text
Excel (結合ヘッダー):
┌─────────────────────────────┬────────┐
│      Category (3 cols)      │  Info  │
├─────────┬─────────┬─────────┼────────┤
│    A    │    B    │    C    │   D    │
└─────────┴─────────┴─────────┴────────┘

          ↓ parse_excel()

Markdown:
| Category | Category | Category | Info |
|----------|----------|----------|------|
| A        | B        | C        | D    |
```

**2行階層ヘッダー**

親子関係のある複雑なヘッダーには、`ExcelParsingSchema(header_rows=2)` を使用します：

```text
Excel (2行ヘッダー):
┌───────────────────┬───────────────────┐
│       Info        │      Metrics      │  ← Row 1 (Parent)
├─────────┬─────────┼─────────┬─────────┤
│  Name   │   ID    │  Score  │  Rank   │  ← Row 2 (Child)
├─────────┼─────────┼─────────┼─────────┤
│  Alice  │   001   │   95    │    1    │
└─────────┴─────────┴─────────┴─────────┘

          ↓ parse_excel(schema=ExcelParsingSchema(header_rows=2))

Markdown:
| Info - Name | Info - ID | Metrics - Score | Metrics - Rank |
|-------------|-----------|-----------------|----------------|
| Alice       | 001       | 95              | 1              |
```

> **注:** 現在、最大2行のヘッダー行をサポートしています。より深い階層の場合は、解析前にデータを前処理してください。

**Excelから構造化オブジェクトへ（「キラー」機能）**

単にテキストに変換するだけでなく、Excelをワンステップで有効で型安全なPythonオブジェクトに直接変換します。

```python
@dataclass
class SalesRecord:
    category: str
    item: str
    amount: int  # 文字列からintへの自動変換

# 1. Excelを解析 (結合セルを自動的に処理)
# 2. 検証とオブジェクトへの変換
records = parse_excel(ws).to_models(SalesRecord)

# これできれいな型付きデータが得られます
assert records[0].amount == 1000
```

**設定**

解析動作をカスタマイズするには `ExcelParsingSchema` を使用します：

```python
from md_spreadsheet_parser import parse_excel, ExcelParsingSchema

schema = ExcelParsingSchema(
    header_rows=2,
    fill_merged_headers=True,
    header_separator=" / "
)

table = parse_excel(source, schema)
```

| オプション | デフォルト | 説明 |
|--------|---------|-------------|
| `header_rows` | `1` | ヘッダー行の数 (1 or 2)。 |
| `fill_merged_headers` | `True` | 空のヘッダーセルを前方埋めします。 |
| `header_separator` | `" - "` | フラット化された2行ヘッダーの区切り文字。 |
| `delimiter` | `"\t"` | TSV/CSVの列区切り文字。 |


### 6. Markdown生成 (ラウンドトリップ)

解析されたオブジェクトを変更し、`to_markdown()` を使用してMarkdown文字列に戻すことができます。これにより、完全な「解析 -> 変更 -> 生成」のワークフローが可能になります。

```python
from md_spreadsheet_parser import parse_table, ParsingSchema

markdown = "| A | B |\n|---|---| \n| 1 | 2 |"
table = parse_table(markdown)

# データの変更
table.rows.append(["3", "4"])

# Markdownの生成
# スキーマを使用して出力形式をカスタマイズできます
schema = ParsingSchema(require_outer_pipes=True)
print(table.to_markdown(schema))
# | A | B |
# | --- | --- |
# | 1 | 2 |
# | 3 | 4 |
```

### 7. 高度な機能

**メタデータ抽出の設定**
デフォルトでは、パーサーはテーブル名（レベル3ヘッダー）と説明をキャプチャします。`MultiTableParsingSchema` でこの動作をカスタマイズできます。

```python
from md_spreadsheet_parser import MultiTableParsingSchema

schema = MultiTableParsingSchema(
    table_header_level=3,     # ### Header をテーブル名として扱う
    capture_description=True  # ヘッダーとテーブルの間のテキストをキャプチャ
)
# parse_workbook にスキーマを渡す...
```

### 8. 高度な型変換

`to_models()` に `ConversionSchema` を渡すことで、文字列値がPythonオブジェクトに変換される方法をカスタマイズできます。これは国際化 (I18N) やカスタム型の処理に役立ちます。

**国際化 (I18N): カスタムブール値ペア**

どの文字列ペアを `True`/`False` にマッピングするかを設定します（大文字小文字を区別しません）。

```python
from md_spreadsheet_parser import parse_table, ConversionSchema

markdown = """
| User | Active? |
| --- | --- |
| Tanaka | はい |
| Suzuki | いいえ |
"""

# "はい" -> True, "いいえ" -> False を設定
schema = ConversionSchema(
    boolean_pairs=(("はい", "いいえ"),)
)

users = parse_table(markdown).to_models(User, conversion_schema=schema)
# Tanaka.active is True
```

**カスタム型コンバータ**

特定の型のカスタム変換関数を登録します。以下を含む **任意のPython型** をキーとして使用できます：

- **組み込み**: `int`, `float`, `bool` (デフォルト動作の上書き)
- **標準ライブラリ**: `Decimal`, `datetime`, `date`, `ZoneInfo`, `UUID`
- **カスタムクラス**: 独自のデータクラスやオブジェクト

標準ライブラリの型とカスタムクラスを使用した例：

```python
from dataclasses import dataclass
from uuid import UUID
from zoneinfo import ZoneInfo
from md_spreadsheet_parser import ConversionSchema, parse_table

@dataclass
class Color:
    r: int
    g: int
    b: int

@dataclass
class Config:
    timezone: ZoneInfo
    session_id: UUID
    theme_color: Color

markdown = """
| Timezone | Session ID | Theme Color |
| --- | --- | --- |
| Asia/Tokyo | 12345678-1234-5678-1234-567812345678 | 255,0,0 |
"""

schema = ConversionSchema(
    custom_converters={
        # 標準ライブラリ型
        ZoneInfo: lambda v: ZoneInfo(v),
        UUID: lambda v: UUID(v),
        # カスタムクラス
        Color: lambda v: Color(*map(int, v.split(",")))
    }
)

data = parse_table(markdown).to_models(Config, conversion_schema=schema)
# data[0].timezone is ZoneInfo("Asia/Tokyo")
# data[0].theme_color is Color(255, 0, 0)
```

**フィールド固有のコンバータ**

詳細な制御のために、特定のフィールド名に対するコンバータを定義でき、これらは型ベースのコンバータよりも優先されます。

```python
def parse_usd(val): ...
def parse_jpy(val): ...

schema = ConversionSchema(
    # 型ベースのデフォルト (低優先度)
    custom_converters={
        Decimal: parse_usd 
    },
    # フィールド名のオーバーライド (高優先度)
    field_converters={
        "price_jpy": parse_jpy,
        "created_at": lambda x: datetime.strptime(x, "%Y/%m/%d")
    }
)

# price_usd (オーバーライドなし) -> custom_converters (parse_usd)
# price_jpy (オーバーライド)    -> field_converters (parse_jpy)
data = parse_table(markdown).to_models(Product, conversion_schema=schema)
```

**標準コンバータライブラリ**

一般的なパターン（通貨、リスト）については、独自に記述する代わりに、`md_spreadsheet_parser.converters` にある組み込みヘルパー関数を使用できます。

```python
from md_spreadsheet_parser.converters import (
    to_decimal_clean,        # "$1,000", "¥500" -> Decimal
    make_datetime_converter, # 解析/TZロジックのファクトリ
    make_list_converter,     # "a,b,c" -> ["a", "b", "c"]
    make_bool_converter      # カスタムの厳密なブール値セット
)

schema = ConversionSchema(
    custom_converters={
        # 通貨: $, ¥, €, £, カンマ, スペースを削除
        Decimal: to_decimal_clean,
        # DateTime: ISO形式デフォルト, ナイーブな場合はTokyo TZを付与
        datetime: make_datetime_converter(tz=ZoneInfo("Asia/Tokyo")),
        # リスト: カンマで分割, 空白を除去
        list: make_list_converter(separator=",")
    },
    field_converters={
        # 特定のフィールドに対するカスタムブール値
        "is_valid": make_bool_converter(true_values=["OK"], false_values=["NG"])
    }
)
```

### 9. 堅牢性 (不正なテーブルの処理)

パーサーは、不完全なMarkdownテーブルを適切に処理するように設計されています。

*   **列の欠落**: ヘッダーよりも列が少ない行は、自動的に空文字列で **パディング** されます。
*   **余分な列**: ヘッダーよりも列が多い行は、自動的に **切り捨て** られます。

```python
from md_spreadsheet_parser import parse_table

markdown = """
| A | B |
|---|---|
| 1 |       <-- 列の欠落
| 1 | 2 | 3 <-- 余分な列
"""

table = parse_table(markdown)

print(table.rows)
# [['1', ''], ['1', '2']]
```

これにより、`table.rows` は常に `table.headers` の構造と一致することが保証され、反復や検証中のクラッシュを防ぎます。

### 10. セル内改行のサポート

パーサーは、HTMLの改行タグを自動的にPythonの改行 (`\n`) に変換します。これにより、複数行のセルを自然に扱うことができます。

**サポートされているタグ (大文字小文字区別なし):**
- `<br>`
- `<br/>`
- `<br />`

```python
markdown = "| Line1<br>Line2 |"
table = parse_table(markdown)
# table.rows[0][0] == "Line1\nLine2"
```

**ラウンドトリップサポート:**
Markdownを生成する場合（例: `table.to_markdown()`）、Pythonの改行 (`\n`) は、テーブル構造を維持するために自動的に `<br>` タグに変換されます。

これを無効にするには、`ParsingSchema` で `convert_br_to_newline=False` を設定します。

### 11. パフォーマンスとスケーラビリティ (ストリーミングAPI)

**本当に10GBのMarkdownファイルがありますか？**

おそらくないでしょう。そうでないことを心から願っています。Markdownはそのために作られたものではありません。

しかし *万が一ある場合* —たとえば、膨大なログを生成していたり、標準コンバータの監査を行っている場合—このライブラリはあなたをサポートします。Excelが1,048,576行で諦める一方で、`md-spreadsheet-parser` は **無制限のサイズ** のファイルに対するストリーミング処理をサポートし、メモリ使用量を一定に保ちます。

**scan_tables_iter**:
この関数はファイルを行ごとに読み込み、`Table` オブジェクトが見つかるたびにyieldします。ファイル全体をメモリに読み込むことは **ありません**。

```python
from md_spreadsheet_parser import scan_tables_iter

# 巨大なログファイルを処理 (例: 10GB)
# メモリ使用量は低いまま (単一のテーブルブロックのサイズのみ)
for table in scan_tables_iter("huge_server_log.md"):
    print(f"Found table with {len(table.rows)} rows")
    
    # 行の処理...
    for row in table.rows:
        pass
```

これは、データパイプライン、ログ分析、および標準的なスプレッドシートエディタで開くには大きすぎるエクスポートの処理に最適です。

### 12. プログラムによる操作

このライブラリは、データ構造を変更するための不変メソッドを提供します。これらのメソッドは、変更が適用された **新しいインスタンス** を返し、元のオブジェクトは変更しません。

**ワークブック操作**
```python
# 新しいシートの追加 (ヘッダーA, B, Cを持つデフォルトテーブルを作成)
new_wb = workbook.add_sheet("New Sheet")

# シート名の変更
new_wb = workbook.rename_sheet(sheet_index=0, new_name("Budget 2024"))

# シートの削除
new_wb = workbook.delete_sheet(sheet_index=1)
```

**シート操作**
```python
# シート名の変更 (直接メソッド)
new_sheet = sheet.rename("Q1 Data")

# テーブルメタデータの更新
new_sheet = sheet.update_table_metadata(
    table_index=0, 
    name="Expenses", 
    description="Monthly expense report"
)
```

**テーブル操作**
```python
# セルの更新 (インデックスが範囲外の場合、自動的にテーブルを拡張)
new_table = table.update_cell(row_idx=5, col_idx=2, value="Updated")

# 行の削除 (構造的な削除)
new_table = table.delete_row(row_idx=2)

# 列データのクリア (ヘッダーと行構造は保持し、セルを空にする)
new_table = table.clear_column_data(col_idx=3)
```

### 13. ビジュアルメタデータの永続化

このライブラリは、Markdownテーブルの構造自体を変更することなく、ビジュアル状態（列幅やフィルタ設定など）を永続化することをサポートしています。これは、テーブルの後に追加される隠しHTMLコメントによって実現されます。

```markdown
| A | B |
|---|---|
| 1 | 2 |

<!-- md-spreadsheet-table-metadata: {"columnWidths": [100, 200]} -->
```

これにより、以下のことが保証されます：
1.  **クリーンなデータ**: テーブルは標準的なMarkdownのままであり、どのレンダラーでも読み取ることができます。
2.  **リッチな状態**: 互換性のあるツール（私たちが提供するVS Code拡張機能など）は、このコメントを読み取ってUIの状態（列幅、非表示列など）を復元できます。
3.  **堅牢性**: パーサーは、空行で区切られていても、このメタデータを直前のテーブルに自動的に関連付けます。

### コマンドラインインターフェース (CLI)

`md-spreadsheet-parser` コマンドを使用してMarkdownファイルを解析し、JSONを出力できます。これは、データを他のツールにパイプ処理する場合に便利です。

```bash
# ファイルから読み込む
md-spreadsheet-parser input.md

# 標準入力（パイプ）から読み込む
cat input.md | md-spreadsheet-parser
```

**オプション:**
- `--scan`: ワークブック構造を無視してすべてのテーブルをスキャンします（テーブルのリストを返します）。
- `--root-marker`: ルートマーカーを設定します（デフォルト: `# Tables`）。
- `--sheet-header-level`: シートのヘッダーレベルを設定します（デフォルト: 2）。
- `--table-header-level`: テーブルのヘッダーレベルを設定します（デフォルト: 3）。
- `--capture-description`: テーブルの説明をキャプチャします（デフォルト: True）。
- `--column-separator`: 列の区切りに使用する文字（デフォルト: `|`）。
- `--header-separator-char`: 区切り行で使用する文字（デフォルト: `-`）。
- `--no-outer-pipes`: 外側のパイプがないテーブルを許可します（デフォルト: False）。
- `--no-strip-whitespace`: セルの値から空白を除去しません（デフォルト: False）。
- `--no-br-conversion`: `<br>` タグの改行への自動変換を無効にします（デフォルト: False）。

## 設定 (Configuration)

`ParsingSchema` と `MultiTableParsingSchema` を使用して、解析動作をカスタマイズできます。

| オプション | デフォルト | 説明 |
| :--- | :--- | :--- |
| `column_separator` | `\|` | 列の区切りに使用する文字。 |
| `header_separator_char` | `-` | 区切り行で使用する文字。 |
| `require_outer_pipes` | `True` | `True` の場合、生成されるMarkdownテーブルに外側のパイプが含まれます。 |
| `strip_whitespace` | `True` | `True` の場合、セルの値から空白が除去されます。 |
| `convert_br_to_newline` | `True` | `True` の場合、`<br>` タグは `\n` に変換されます（逆も同様）。 |
| `root_marker` | `# Tables` | (MultiTable) データセクションの開始を示すマーカー。 |
| `sheet_header_level` | `2` | (MultiTable) シートのヘッダーレベル。 |
| `table_header_level` | `3` | (MultiTable) テーブルのヘッダーレベル。 |
| `capture_description` | `True` | (MultiTable) ヘッダーとテーブルの間のテキストをキャプチャします。 |

## 今後のロードマップ (Future Roadmap)

このパーサーは、新しいエコシステムである **テキストベースの表計算管理** の中核となる基盤です。

Markdownファイルの完全なGUIスプレッドシートエディタとして機能する **リッチなVS Code拡張機能** のリリースを準備しています。

> [!NOTE]
> **近日公開**: VS Code拡張機能の公式リリースは、このライブラリの **v1.0.0** とともにここで発表されます。お楽しみに！

**ビジョン: "ExcelのようなUX、Gitネイティブなデータ"**
高パフォーマンスなエディタとこの堅牢なパーサーを組み合わせることで、ソフトウェアプロジェクトにおけるバイナリスプレッドシートファイルの管理という長年の問題を解決することを目指しています。
*   **人間のために**: 快適で馴染みのあるUI（セルの書式設定、改善されたナビゲーション、視覚的なフィードバック）でデータを編集できます。
*   **マシンのために**: データはクリーンで差分可能なMarkdownとして保存され、このライブラリが瞬時に解析、検証、Pythonオブジェクトへの変換を行います。

## ライセンス

このプロジェクトは [MIT License](https://github.com/f-y/md-spreadsheet-parser/blob/main/LICENSE) の下でライセンスされています。
