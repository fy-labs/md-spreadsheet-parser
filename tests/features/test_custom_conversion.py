from dataclasses import dataclass
from decimal import Decimal
from typing import Optional

import pytest
from md_spreadsheet_parser import ConversionSchema, parse_table


@dataclass
class User:
    name: str
    is_active: bool
    score: int
    price: Optional[Decimal] = None


def test_custom_boolean_pairs_japanese() -> None:
    """
    Test using Japanese boolean pairs (Hai/Iie).
    """
    markdown = """
| Name | Is Active | Score |
| --- | --- | --- |
| Tanaka | Hai | 100 |
| Suzuki | Iie | 50 |
"""
    # Define schema with ONLY japanese pairs
    schema = ConversionSchema(boolean_pairs=(("hai", "iie"),))

    table = parse_table(markdown)
    users = table.to_models(User, conversion_schema=schema)

    assert users[0].is_active is True
    assert users[1].is_active is False


def test_strict_boolean_pairs_rejection() -> None:
    """
    Test that if we define specific pairs, other pairs (like yes/no) are rejected.
    """
    markdown = """
| Name | Is Active | Score |
| --- | --- | --- |
| Alice | Yes | 10 |
"""
    # Schema knowing only Hai/Iie
    schema = ConversionSchema(boolean_pairs=(("hai", "iie"),))

    table = parse_table(markdown)

    with pytest.raises(Exception) as excinfo:
        table.to_models(User, conversion_schema=schema)

    # Validation error should mention invalid boolean
    assert "Invalid boolean value: 'Yes'" in str(excinfo.value)


def test_default_pairs_mixing() -> None:
    """
    Test that default schema allows mixing different standard pairs (yes/no, 1/0, true/false).
    """
    markdown = """
| Name | Is Active | Score |
| --- | --- | --- |
| A | Yes | 1 |
| B | 0   | 2 |
| C | True | 3 |
| D | off | 4 |
"""
    table = parse_table(markdown)
    # Default schema used implicitly
    users = table.to_models(User)

    assert users[0].is_active is True  # Yes
    assert users[1].is_active is False  # 0
    assert users[2].is_active is True  # True
    assert users[3].is_active is False  # off


def test_custom_type_converter() -> None:
    """
    Test registering a custom converter for Decimal.
    """
    markdown = """
| Name | Is Active | Score | Price |
| --- | --- | --- | --- |
| ItemA | yes | 1 | $10.50 |
| ItemB | yes | 1 | 2,000 |
"""

    def parse_currency(value: str) -> Decimal:
        clean = value.replace("$", "").replace(",", "").strip()
        return Decimal(clean)

    schema = ConversionSchema(custom_converters={Decimal: parse_currency})

    table = parse_table(markdown)
    users = table.to_models(User, conversion_schema=schema)

    assert users[0].price == Decimal("10.50")
    assert users[1].price == Decimal("2000")


def test_case_insensitivity() -> None:
    """
    Test that boolean pairs are case insensitive.
    """
    markdown = """
| Name | Is Active | Score |
| --- | --- | --- |
| A | はい | 1 |
| B | いいえ | 0 |
"""
    schema = ConversionSchema(boolean_pairs=(("はい", "いいえ"),))

    table = parse_table(markdown)
    users = table.to_models(User, conversion_schema=schema)

    assert users[0].is_active is True
    assert users[1].is_active is False


def test_field_specific_converter() -> None:
    """
    Test using different converters for different fields of the same type.
    """

    @dataclass
    class Product:
        price_usd: Decimal
        price_jpy: Decimal

    markdown = """
| Price USD | Price JPY |
| --- | --- |
| $10 | ¥1,000 |
"""

    def parse_usd(v: str) -> Decimal:
        return Decimal(v.replace("$", "").strip())

    def parse_jpy(v: str) -> Decimal:
        return Decimal(v.replace("¥", "").replace(",", "").strip())

    schema = ConversionSchema(
        field_converters={"price_usd": parse_usd, "price_jpy": parse_jpy}
    )

    table = parse_table(markdown)
    products = table.to_models(Product, conversion_schema=schema)

    assert products[0].price_usd == Decimal("10")
    assert products[0].price_jpy == Decimal("1000")


def test_field_converter_overrides_type_converter() -> None:
    """
    Test that a field-specific converter takes precedence over the type-based converter.
    """

    @dataclass
    class Item:
        val1: int
        val2: int  # Special

    markdown = """
| Val1 | Val2 |
| --- | --- |
| 10 | 10 |
"""

    def parse_double(v: str) -> int:
        return int(v) * 2

    schema = ConversionSchema(
        custom_converters={int: lambda x: int(x)},  # Standard logic explicitly
        field_converters={"val2": parse_double},
    )

    table = parse_table(markdown)
    items = table.to_models(Item, conversion_schema=schema)

    assert items[0].val1 == 10  # Uses default/type converter (10)
    assert items[0].val2 == 20  # Uses field converter (10 * 2)


def test_advanced_custom_types() -> None:
    """
    Test conversion for standard library types (ZoneInfo, UUID) and custom classes.
    """
    try:
        from zoneinfo import ZoneInfo
    except ImportError:
        # ZoneInfo is available in Python 3.9+
        # If running on older python (unlikely for this project), skip this part or mock it
        pytest.skip("ZoneInfo not available")

    from uuid import UUID

    @dataclass
    class Color:
        r: int
        g: int
        b: int

    @dataclass
    class AdvancedConfig:
        timezone: ZoneInfo
        session_id: UUID
        theme_color: Color

    markdown = """
| Timezone | Session ID | Theme Color |
| --- | --- | --- |
| Asia/Tokyo | 12345678-1234-5678-1234-567812345678 | 255,0,0 |
"""

    def parse_color(v: str) -> Color:
        r, g, b = map(int, v.split(","))
        return Color(r, g, b)

    schema = ConversionSchema(
        custom_converters={
            ZoneInfo: lambda v: ZoneInfo(v),
            UUID: lambda v: UUID(v),
            Color: parse_color,
        }
    )

    table = parse_table(markdown)
    configs = table.to_models(AdvancedConfig, conversion_schema=schema)

    config = configs[0]

    assert isinstance(config.timezone, ZoneInfo)
    assert config.timezone.key == "Asia/Tokyo"

    assert isinstance(config.session_id, UUID)
    assert str(config.session_id) == "12345678-1234-5678-1234-567812345678"

    assert isinstance(config.theme_color, Color)
    assert config.theme_color.r == 255
    assert config.theme_color.g == 0
    assert config.theme_color.b == 0
