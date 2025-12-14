from dataclasses import dataclass
from typing import TypedDict

import pytest
from md_spreadsheet_parser.models import Sheet, Table, Workbook
from md_spreadsheet_parser.validation import TableValidationError

# Mock Pydantic availability
try:
    from pydantic import BaseModel  # type: ignore

    HAS_PYDANTIC = True
except ImportError:
    HAS_PYDANTIC = False

    class BaseModel:  # type: ignore
        pass


def create_table(headers, rows, name=None, description=None):
    return Table(headers=headers, rows=rows, name=name, description=description)


# --- 1. Simple Dict Conversion ---
def test_to_models_dict():
    headers = ["Name", "Age", "Active"]
    rows = [["Alice", "30", "true"], ["Bob", "25", "false"]]
    table = create_table(headers, rows)

    result = table.to_models(dict)

    assert len(result) == 2
    assert result[0] == {"Name": "Alice", "Age": "30", "Active": "true"}
    assert result[1] == {"Name": "Bob", "Age": "25", "Active": "false"}


# --- 2. TypedDict Conversion ---
class UserDict(TypedDict):
    name: str
    age: int
    active: bool


def test_to_models_typeddict():
    headers = ["name", "age", "active"]
    rows = [["Alice", "30", "true"], ["Bob", "25", "false"]]
    table = create_table(headers, rows)

    result = table.to_models(UserDict)

    assert len(result) == 2
    assert result[0]["name"] == "Alice"
    assert result[0]["age"] == 30
    assert result[0]["active"] is True
    assert result[1]["active"] is False


# --- 3. Dataclass Column JSON ---
@dataclass
class ConfigData:
    id: int
    metadata: dict
    tags: list


def test_dataclass_column_json():
    headers = ["id", "metadata", "tags"]
    rows = [["1", '{"debug": true}', '["a", "b"]'], ["2", '{"debug": false}', '["c"]']]
    table = create_table(headers, rows)

    result = table.to_models(ConfigData)

    assert len(result) == 2
    assert result[0].metadata == {"debug": True}
    assert result[0].tags == ["a", "b"]
    assert result[1].metadata == {"debug": False}


def test_dataclass_column_json_invalid():
    headers = ["id", "metadata", "tags"]
    rows = [["1", "invalid-json", "[]"]]
    table = create_table(headers, rows)

    with pytest.raises(TableValidationError) as exc:
        table.to_models(ConfigData)

    assert "Invalid JSON" in str(exc.value)


# --- 4. Pydantic Column JSON ---
if HAS_PYDANTIC:

    class ConfigModel(BaseModel):
        id: int
        metadata: dict
        tags: list

    def test_pydantic_column_json():
        headers = ["id", "metadata", "tags"]
        rows = [
            ["1", '{"debug": true}', '["a", "b"]'],
            ["2", '{"debug": false}', '["c"]'],
        ]
        table = create_table(headers, rows)

        result = table.to_models(ConfigModel)

        assert len(result) == 2
        assert result[0].metadata == {"debug": True}
        assert result[0].tags == ["a", "b"]
        assert result[1].metadata == {"debug": False}

    def test_pydantic_column_json_invalid():
        headers = ["id", "metadata", "tags"]
        rows = [["1", "invalid-json", "[]"]]
        table = create_table(headers, rows)

        # Pydantic validation error expected, wrapped in TableValidationError
        with pytest.raises(TableValidationError):
            table.to_models(ConfigModel)

# --- 5. JSON Property Export (Serialization) ---
# from md_spreadsheet_parser.models import Sheet, Workbook


def test_json_property_structure():
    headers = ["Name", "Score"]
    rows = [["Alice", "10"], ["Bob", "20"]]
    table = create_table(headers, rows, name="Stats", description="Test Description")

    # Table.json
    t_json = table.json
    assert t_json["name"] == "Stats"
    assert t_json["description"] == "Test Description"
    assert t_json["headers"] == headers
    assert t_json["rows"] == rows
    assert isinstance(t_json["metadata"], dict)

    # Sheet.json
    sheet = Sheet(name="Sheet1", tables=[table])
    s_json = sheet.json
    assert s_json["name"] == "Sheet1"
    assert len(s_json["tables"]) == 1
    assert s_json["tables"][0] == t_json

    # Workbook.json
    workbook = Workbook(sheets=[sheet])
    w_json = workbook.json
    assert len(w_json["sheets"]) == 1
    assert w_json["sheets"][0] == s_json


# --- 6. Pandas Simulation (to_models(dict)) ---
def test_pandas_simulation():
    # Simulate data suitable for Pandas DataFrame
    # Mixed types as strings, relying on Pandas (or user) to cast
    headers = ["Date", "Value", "IsActive"]
    rows = [["2023-01-01", "100.5", "True"], ["2023-01-02", "200", "False"]]
    table = create_table(headers, rows)

    result = table.to_models(dict)

    # Should be list of dicts with raw strings
    assert len(result) == 2
    assert result[0] == {"Date": "2023-01-01", "Value": "100.5", "IsActive": "True"}
    assert result[1] == {"Date": "2023-01-02", "Value": "200", "IsActive": "False"}

    # This structure is exactly what pd.DataFrame(result) expects
