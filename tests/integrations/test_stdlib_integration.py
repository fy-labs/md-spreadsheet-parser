import csv
import json
import io
from dataclasses import dataclass
from typing import List
from md_spreadsheet_parser import Table, parse_table


def test_json_workflow():
    """
    Verify integration with json module.
    Scenario: Table -> dict -> JSON string -> API response structure
    """
    table = Table(headers=["id", "name"], rows=[["1", "Alice"], ["2", "Bob"]])

    # Convert to list of dicts
    data = table.to_models(dict)

    # Serialize
    json_str = json.dumps(data, sort_keys=True)

    expected = '[{"id": "1", "name": "Alice"}, {"id": "2", "name": "Bob"}]'
    assert json_str == expected


def test_csv_workflow():
    """
    Verify integration with csv module.
    Scenario: Table -> csv.writer -> CSV string
    """
    table = Table(headers=["Name", "Role"], rows=[["Alice", "Dev"], ["Bob", "Manager"]])

    output = io.StringIO()
    writer = csv.writer(output)

    # Write header
    if table.headers:
        writer.writerow(table.headers)

    # Write rows
    writer.writerows(table.rows)

    csv_content = output.getvalue().strip().replace("\r\n", "\n")
    expected = "Name,Role\nAlice,Dev\nBob,Manager"
    assert csv_content == expected


@dataclass
class ConfigMeta:
    priority: int
    tags: List[str]


@dataclass
class AppConfig:
    env: str
    meta: ConfigMeta


def test_dataclass_nested_parsing():
    """
    Verify parsing nested JSON data into nested Dataclasses.
    This simulates loading complex configuration from a Markdown table.
    """
    markdown = """
| Env | Meta |
| --- | --- |
| prod | {"priority": 1, "tags": ["stable", "v1"]} |
| dev  | {"priority": 2, "tags": ["wip"]} |
"""

    # The parser should automatically handle the nested dict parsing from JSON cell
    # However, converting that dict to a nested dataclass (ConfigMeta) requires
    # the dataclass system to handle it.
    # md-spreadsheet-parser's `to_models` standard conversion flattens basic types.
    # It does NOT recursively instatiate nested dataclasses from dicts automatically
    # unless we provide a specific converter or the library supports it natively.

    # Checking library behavior: dacite or similar is often needed for nested dataclass from dict.
    # MD Spreadsheet Parser 0.6.0 documentation says:
    # "If a field is typed as dict or list ... parser automatically parses the cell value as JSON"
    # It does not explicitly say it instantiates nested Dataclasses.
    # So we expect 'meta' to be a dict, unless we add a custom converter.

    # Let's verify the "dict" behavior first, effectively integrating with Python's type system.

    @dataclass
    class AppConfigDict:
        env: str
        meta: dict  # Parsed as dict

    configs = parse_table(markdown).to_models(AppConfigDict)

    assert configs[0].env == "prod"
    assert configs[0].meta == {"priority": 1, "tags": ["stable", "v1"]}
    assert isinstance(configs[0].meta, dict)

    # Now verify explicit nested conversion if we wanted it
    # We can use a custom converter for the complex type
    from md_spreadsheet_parser import ConversionSchema

    def meta_converter(val: str) -> ConfigMeta:
        d = json.loads(val)
        return ConfigMeta(priority=d["priority"], tags=d["tags"])

    schema = ConversionSchema(custom_converters={ConfigMeta: meta_converter})

    complex_configs = parse_table(markdown).to_models(
        AppConfig, conversion_schema=schema
    )

    assert isinstance(complex_configs[0].meta, ConfigMeta)
    assert complex_configs[0].meta.tags == ["stable", "v1"]
