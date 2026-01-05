from decimal import Decimal
from typing import Callable, Iterable
from datetime import datetime
import re

try:
    from zoneinfo import ZoneInfo
except ImportError:
    # Python 3.8 support or fallback
    # In this library we assume Python 3.10+ based on user environment but good to be safe?
    # User env is 3.12.12. ZoneInfo is standard.
    from zoneinfo import ZoneInfo


def to_decimal_clean(value: str) -> Decimal:
    """
    Convert a string to Decimal, removing common currency symbols and grouping separators.
    Removes: '$', '¥', '€', '£', ',', ' ' (space), '_'
    """
    clean_val = re.sub(r"[ $¥€£,_]", "", value)
    if not clean_val:
        # What should empty string be?
        # Usually schema validation handles empty string via Optional[Decimal] -> None.
        # If we are here, it's likely a non-empty string or expected to be a value.
        # But if the string was just "$", it becomes empty.
        raise ValueError(f"Cannot convert '{value}' to Decimal")

    return Decimal(clean_val)


def make_datetime_converter(
    fmt: str | None = None, tz: ZoneInfo | None = None
) -> Callable[[str], datetime]:
    """
    Create a converter function for datetime.

    Args:
        fmt: str format for strptime. If None, uses datetime.fromisoformat().
        tz: ZoneInfo to attach (if naive) or convert to (if aware).

    Returns:
        Function that accepts a string and returns a datetime.
    """

    def converter(value: str) -> datetime:
        value = value.strip()
        if fmt:
            dt = datetime.strptime(value, fmt)
        else:
            dt = datetime.fromisoformat(value)

        if tz:
            if dt.tzinfo is None:
                # Attach timezone if naive
                dt = dt.replace(tzinfo=tz)
            else:
                # Convert timezone if aware
                dt = dt.astimezone(tz)
        return dt

    return converter


def make_list_converter(
    separator: str = ",", strip_items: bool = True, distinct: bool = False
) -> Callable[[str], list[str]]:
    """
    Create a converter that splits a string into a list.

    Args:
        separator: Character/string to split by. Default ",".
        strip_items: Whether to strip whitespace from each item. Default True.
        distinct: Whether to remove duplicates (maintaining order). Default False.

    Returns:
        Function that accepts a string and returns a list of strings.
    """

    def converter(value: str) -> list[str]:
        if not value:
            return []

        parts = value.split(separator)
        if strip_items:
            parts = [p.strip() for p in parts]

        if distinct:
            seen = set()
            deduper = []
            for p in parts:
                if p not in seen:
                    deduper.append(p)
                    seen.add(p)
            parts = deduper

        return parts

    return converter


def make_bool_converter(
    true_values: Iterable[str] = ("true", "yes", "1", "on"),
    false_values: Iterable[str] = ("false", "no", "0", "off"),
) -> Callable[[str], bool]:
    """
    Create a strict boolean converter.

    Args:
        true_values: List of case-insensitive strings treated as True.
        false_values: List of case-insensitive strings treated as False.

    Returns:
        Function that returns bool or raises ValueError.
    """
    t_set = {v.lower() for v in true_values}
    f_set = {v.lower() for v in false_values}

    def converter(value: str) -> bool:
        lower = value.strip().lower()
        if lower in t_set:
            return True
        if lower in f_set:
            return False
        raise ValueError(f"Invalid boolean value: '{value}'")

    return converter
