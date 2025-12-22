import json
import subprocess


CLI_CMD = ["uv", "run", "md-spreadsheet-parser"]


def test_cli_stdin():
    markdown = """
# Tables

## Sheet1
| A |
|---|
| 1 |
"""
    result = subprocess.run(
        CLI_CMD,
        input=markdown,
        capture_output=True,
        text=True,
        check=True,
    )

    data = json.loads(result.stdout)
    assert len(data["sheets"]) == 1
    assert data["sheets"][0]["name"] == "Sheet1"
    assert data["sheets"][0]["tables"][0]["rows"] == [["1"]]


def test_cli_file(tmp_path):
    markdown = """
# Tables

## Sheet1
| B |
|---|
| 2 |
"""
    file_path = tmp_path / "test.md"
    file_path.write_text(markdown, encoding="utf-8")

    result = subprocess.run(
        CLI_CMD + [str(file_path)],
        capture_output=True,
        text=True,
        check=True,
    )

    data = json.loads(result.stdout)
    assert len(data["sheets"]) == 1
    assert data["sheets"][0]["tables"][0]["rows"] == [["2"]]


def test_cli_args():
    markdown = """
# Custom Root

## Sheet1
| C |
|---|
| 3 |
"""
    result = subprocess.run(
        CLI_CMD + ["--root-marker", "# Custom Root"],
        input=markdown,
        capture_output=True,
        text=True,
        check=True,
    )

    data = json.loads(result.stdout)
    assert len(data["sheets"]) == 1
    assert data["sheets"][0]["tables"][0]["rows"] == [["3"]]


def test_cli_error_missing_file():
    result = subprocess.run(
        CLI_CMD + ["nonexistent.md"],
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0
    assert "not found" in result.stderr


def test_cli_error_invalid_config():
    result = subprocess.run(
        CLI_CMD + ["--capture-description"],  # Missing --table-header-level
        input="",
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0
    assert "requires --table-header-level" in result.stderr


def test_cli_scan():
    markdown = """
Some text.

| A |
|---|
| 1 |

More text.

| B |
|---|
| 2 |
"""
    result = subprocess.run(
        CLI_CMD + ["--scan"],
        input=markdown,
        capture_output=True,
        text=True,
        check=True,
    )

    data = json.loads(result.stdout)
    assert isinstance(data, list)
    assert len(data) == 2
    assert data[0]["headers"] == ["A"]
    assert data[1]["headers"] == ["B"]


def test_cli_no_br_conversion():
    markdown = "| A |\n|---|\n| Line1<br>Line2 |"
    result = subprocess.run(
        CLI_CMD + ["--scan", "--no-br-conversion"],
        input=markdown,
        capture_output=True,
        text=True,
        check=True,
    )
    data = json.loads(result.stdout)
    # With conversion disabled, <br> persists
    assert data[0]["rows"][0] == ["Line1<br>Line2"]


def test_cli_no_strip_whitespace():
    markdown = "| A |\n|---|\n|  Value  |"
    result = subprocess.run(
        CLI_CMD + ["--scan", "--no-strip-whitespace"],
        input=markdown,
        capture_output=True,
        text=True,
        check=True,
    )
    data = json.loads(result.stdout)
    # With strip disabled, spaces persist
    assert data[0]["rows"][0] == ["  Value  "]
