from dataclasses import dataclass

from md_spreadsheet_parser.models import Table


@dataclass
class TaskRow:
    task_name: str
    completed: bool


def test_gfm_task_list_boolean_conversion():
    table = Table(
        headers=["task_name", "completed"],
        rows=[
            ["Write test", "[x]"],
            ["Implement feature", "[ ]"],
            ["Refactor", "[X]"],
            ["Ship it", "true"],
        ],
    )

    models = table.to_models(TaskRow)

    assert len(models) == 4
    assert models[0].completed is True
    assert models[1].completed is False
    assert models[2].completed is True  # [X] should work (case insensitive)
    assert models[3].completed is True
