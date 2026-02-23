from md_spreadsheet_parser import MultiTableParsingSchema


def test_schema_with_explicit_root_marker_and_none_table_level():
    """
    Test that MultiTableParsingSchema allows table_header_level=None
    when root_marker is explicitly set (backward compatible behavior).
    """
    schema = MultiTableParsingSchema(
        root_marker="# Tables", capture_description=False, table_header_level=None
    )
    assert schema.table_header_level is None
    assert schema.capture_description is False


def test_valid_schema_configuration():
    """
    Test that a valid configuration passes.
    """
    schema = MultiTableParsingSchema(
        root_marker="# Tables", capture_description=True, table_header_level=3
    )
    assert schema.capture_description is True
    assert schema.table_header_level == 3


def test_auto_detection_schema_defaults():
    """
    Test that schema with all None values (auto-detection mode) works.
    """
    schema = MultiTableParsingSchema()
    assert schema.root_marker is None
    assert schema.sheet_header_level is None
    assert schema.table_header_level is None
    assert schema.capture_description is True
