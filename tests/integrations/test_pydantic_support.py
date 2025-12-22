import pytest
from pydantic import BaseModel, Field
from typing import Optional
from md_spreadsheet_parser import parse_table, TableValidationError


class User(BaseModel):
    name: str = Field(alias="User Name")
    age: int = Field(gt=0, description="Age must be positive")
    email: Optional[str] = None
    is_active: bool = True


def test_pydantic_basic_validation():
    markdown = """
| User Name | Age | Email | Is Active |
| --- | --- | --- | --- |
| Alice | 30 | alice@example.com | yes |
| Bob | 25 | | no |
"""
    users = parse_table(markdown).to_models(User)
    assert len(users) == 2
    assert users[0].name == "Alice"
    assert users[0].age == 30
    assert users[0].email == "alice@example.com"
    assert users[0].is_active is True

    assert users[1].name == "Bob"
    assert users[1].age == 25
    assert users[1].email is None
    assert users[1].is_active is False


def test_pydantic_validation_error():
    markdown = """
| User Name | Age |
| --- | --- |
| Invalid | -5 |
"""
    with pytest.raises(TableValidationError) as excinfo:
        parse_table(markdown).to_models(User)

    error_msg = str(excinfo.value)
    assert "Row 1: Field 'age' - Input should be greater than 0" in error_msg


def test_pydantic_missing_required_field():
    markdown = """
| Age |
| --- |
| 30 |
"""
    # Name is missing
    with pytest.raises(TableValidationError) as excinfo:
        parse_table(markdown).to_models(User)

    assert "Field 'User Name' - Field required" in str(excinfo.value)


def test_pydantic_extra_fields_ignored():
    # Pydantic ignores extra fields by default unless Config says prohibited
    markdown = """
| User Name | Age | Extra |
| --- | --- | --- |
| Alice | 30 | foo |
"""
    users = parse_table(markdown).to_models(User)
    assert len(users) == 1
    assert users[0].name == "Alice"
