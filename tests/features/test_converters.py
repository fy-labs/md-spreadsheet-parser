from datetime import datetime
from decimal import Decimal
from zoneinfo import ZoneInfo
import pytest
from md_spreadsheet_parser.converters import (
    to_decimal_clean,
    make_datetime_converter,
    make_list_converter,
    make_bool_converter,
)

# --- Currency/Decimal Tests ---


def test_to_decimal_clean():
    assert to_decimal_clean("100") == Decimal("100")
    assert to_decimal_clean("1,000") == Decimal("1000")
    assert to_decimal_clean("$10.50") == Decimal("10.50")
    assert to_decimal_clean("¥50,000") == Decimal("50000")
    assert to_decimal_clean(" £ 200 ") == Decimal("200")
    assert to_decimal_clean("€1_000.00") == Decimal("1000.00")


def test_to_decimal_clean_error():
    with pytest.raises(ValueError):
        to_decimal_clean("$")  # Empty after clean

    with pytest.raises(Exception):  # invalid literal for Decimal
        to_decimal_clean("abc")


# --- DateTime Tests ---


def test_datetime_factory_iso():
    conv = make_datetime_converter()  # Default ISO
    assert conv("2023-01-01") == datetime(2023, 1, 1)
    assert conv("2023-01-01T12:00:00") == datetime(2023, 1, 1, 12, 0, 0)


def test_datetime_factory_format():
    conv = make_datetime_converter(fmt="%Y/%m/%d")
    assert conv("2023/12/31") == datetime(2023, 12, 31)


def test_datetime_factory_timezone_attach():
    tz = ZoneInfo("Asia/Tokyo")
    conv = make_datetime_converter(tz=tz)

    # Input naive -> attach TZ
    dt = conv("2023-01-01T00:00:00")
    assert dt.tzinfo == tz
    assert dt.hour == 0


def test_datetime_factory_timezone_convert():
    tokyo = ZoneInfo("Asia/Tokyo")
    # utc = ZoneInfo("UTC")

    # Convert logic: Input Aware (UTC) -> Output (Tokyo)
    input_str = "2023-01-01T00:00:00+00:00"  # Midnight UTC

    conv = make_datetime_converter(tz=tokyo)
    dt = conv(input_str)

    assert dt.tzinfo == tokyo
    assert dt.hour == 9  # Tokyo is UTC+9


# --- List Tests ---


def test_list_factory():
    conv = make_list_converter()
    assert conv("a,b,c") == ["a", "b", "c"]
    assert conv(" a , b ") == ["a", "b"]
    assert conv("") == []


def test_list_factory_separator():
    conv = make_list_converter(separator=";")
    assert conv("a;b") == ["a", "b"]


def test_list_factory_distinct():
    conv = make_list_converter(distinct=True)
    assert conv("a,b,a,c") == ["a", "b", "c"]


# --- Boolean Tests ---


def test_bool_factory():
    conv = make_bool_converter(true_values=["OK"], false_values=["NG"])
    assert conv("ok") is True
    assert conv("OK") is True
    assert conv("ng") is False

    with pytest.raises(ValueError):
        conv("yes")  # Standard value not included
