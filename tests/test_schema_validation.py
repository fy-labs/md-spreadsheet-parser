import pytest
from md_spreadsheet_parser import MultiTableParsingSchema


def test_invalid_schema_configuration():
    """
    Test that MultiTableParsingSchema raises ValueError when
    capture_description is True but table_header_level is None.
    """
    with pytest.raises(
        ValueError,
        match="capture_description=True requires table_header_level to be set",
    ):
        MultiTableParsingSchema(capture_description=True, table_header_level=None)


def test_valid_schema_configuration():
    """
    Test that a valid configuration passes.
    """
    schema = MultiTableParsingSchema(capture_description=True, table_header_level=3)
    assert schema.capture_description is True
    assert schema.table_header_level == 3
