import pytest
from md_spreadsheet_parser.models import Table

try:
    import pandas as pd

    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False
    pd = None  # type: ignore


@pytest.mark.skipif(not HAS_PANDAS, reason="Pandas not installed")
def test_pandas_dataframe_from_dict():
    """
    Verify that table.to_models(dict) produces a structure compatible with pd.DataFrame.
    """
    assert pd is not None
    headers = ["Date", "Sales", "Region"]
    rows = [["2023-01-01", "100", "US"], ["2023-01-02", "150", "EU"]]
    table = Table(headers=headers, rows=rows)

    # 1. Convert to dicts
    data = table.to_models(dict)

    # 2. Create DataFrame
    df = pd.DataFrame(data)

    # 3. Verify DataFrame content
    assert len(df) == 2
    assert list(df.columns) == headers
    assert df.iloc[0]["Date"] == "2023-01-01"
    assert df.iloc[0]["Sales"] == "100"  # Defaults to string because we didn't cast
    assert df.iloc[0]["Region"] == "US"


@pytest.mark.skipif(not HAS_PANDAS, reason="Pandas not installed")
def test_pandas_dataframe_type_inference():
    """
    Verify that simple integer strings are correctly handled by DataFrame
    even if passed as strings initially (Pandas usually keeps them as objects unless cast,
    but we check structure).
    """
    assert pd is not None
    headers = ["ID", "Score"]
    rows = [["1", "10.5"], ["2", "20.0"]]
    table = Table(headers=headers, rows=rows)

    data = table.to_models(dict)
    df = pd.DataFrame(data)

    # Pandas default behavior for dict of strings is object dtype
    # Users usually allow inference or cast manually.
    # Let's verify we can cast easily.
    df["ID"] = pd.to_numeric(df["ID"])
    df["Score"] = pd.to_numeric(df["Score"])

    assert df["ID"].dtype == "int64"
    assert df["Score"].dtype == "float64"
    assert df.iloc[0]["ID"] == 1
    assert df.iloc[0]["Score"] == 10.5


@pytest.mark.skipif(not HAS_PANDAS, reason="Pandas not installed")
def test_pandas_from_dataclasses():
    from dataclasses import asdict, dataclass

    @dataclass
    class SalesData:
        date: str
        amount: int

    assert pd is not None
    headers = ["date", "amount"]
    rows = [["2023-01-01", "100"], ["2023-01-02", "200"]]
    table = Table(headers=headers, rows=rows)

    # Parse to typed objects
    models = table.to_models(SalesData)

    # Convert to DataFrame
    df = pd.DataFrame([asdict(m) for m in models])

    assert len(df) == 2
    assert df["amount"].dtype == "int64"  # Should be int because dataclass converted it
    assert df.iloc[0]["amount"] == 100
