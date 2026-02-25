import re
from typing import Any

# Pattern to extract YAML frontmatter. (?:(.*?)\n)? allows empty frontmatter block
_FRONTMATTER_PATTERN = re.compile(
    r"^---\n(?:(.*?)\n)?---(?:\n|$)", re.DOTALL | re.MULTILINE
)


def extract_frontmatter(markdown: str) -> tuple[str | None, str]:
    """
    Extracts the YAML frontmatter block from the beginning of a markdown document.

    Returns:
        tuple[str | None, str]: (frontmatter_content, remaining_markdown)
    """
    match = _FRONTMATTER_PATTERN.match(markdown)
    if match:
        content = match.group(1) if match.group(1) is not None else ""
        return content, markdown[match.end() :]
    return None, markdown


def _strip_inline_comment(val: str) -> str:
    """Safely strip inline comments from a value string."""
    val = val.strip()
    if not val:
        return val

    # If it's fully quoted, don't strip internal comments
    if (val.startswith('"') and val.endswith('"')) or (
        val.startswith("'") and val.endswith("'")
    ):
        return val

    in_single = False
    in_double = False
    for i, char in enumerate(val):
        if char == "'" and not in_double:
            in_single = not in_single
        elif char == '"' and not in_single:
            in_double = not in_double
        elif char == "#" and not in_single and not in_double:
            # Check if it's preceded by space or is at the start
            if i == 0 or val[i - 1] in (" ", "\t"):
                return val[:i].strip()
    return val


def parse_yaml_frontmatter(yaml_text: str) -> dict[str, Any]:
    """
    Parses a safe subset of YAML commonly used in frontmatter into a Python dictionary.

    Supported features (Zero-dependency custom parser):
    - Key-value pairs (dict)
    - Block sequences (lists starting with '-')
    - Scalars: quoted and unquoted strings, integers, booleans (true/false)
    - Comments (lines starting with '#' or inline '#')
    - Multiline literal blocks ('|')
    - Nested dictionaries via indentation
    """
    if not yaml_text.strip():
        return {}

    lines = yaml_text.split("\n")
    return _parse_yaml_lines(lines, 0, len(lines), 0)[0]


def _parse_yaml_lines(
    lines: list[str], start_idx: int, end_idx: int, base_indent: int
) -> tuple[dict[str, Any], int]:
    """
    Recursively parse YAML lines into a dictionary.
    Returns the parsed dictionary and the next line index to process.
    """
    result: dict[str, Any] = {}
    i = start_idx

    # State tracking for multiline strings
    current_key = None
    multiline_buffer: list[str] = []
    in_multiline = False
    multiline_indent = 0

    while i < end_idx:
        line = lines[i]

        # Handle multiline collection
        if in_multiline:
            # Check if we should exit multiline
            if not line.strip() or len(line) - len(line.lstrip()) >= multiline_indent:
                if current_key:
                    multiline_buffer.append(line)
                i += 1
                continue
            else:
                # End of multiline
                if current_key is not None:
                    # Remove trailing empty lines and join
                    while multiline_buffer and not multiline_buffer[-1].strip():
                        multiline_buffer.pop()
                    # Strip base indent from multiline buffer
                    cleaned_buffer = [
                        line_str[multiline_indent:]
                        if line_str.startswith(" " * multiline_indent)
                        else line_str.lstrip()
                        for line_str in multiline_buffer
                    ]
                    result[current_key] = "\n".join(cleaned_buffer)
                in_multiline = False
                current_key = None
                multiline_buffer = []

        stripped = line.strip()

        # Skip empty lines or pure comments
        if not stripped or stripped.startswith("#"):
            i += 1
            continue

        # Determine indentation
        indent = len(line) - len(line.lstrip())

        # If we hit an unindented line, and we are in a recursive call, return
        if indent < base_indent:
            break

        parts = stripped.split(":", 1)
        if len(parts) == 1:
            # Malformed line or continuation (not supported outside multiline)
            i += 1
            continue

        key = parts[0].strip()
        raw_val = parts[1].strip() if len(parts) > 1 else ""

        stripped_val = _strip_inline_comment(raw_val)

        if stripped_val == "":
            # Could be start of dict, list, or multiline string
            next_line_idx = i + 1
            while next_line_idx < end_idx and (
                not lines[next_line_idx].strip()
                or lines[next_line_idx].strip().startswith("#")
            ):
                next_line_idx += 1

            if next_line_idx < end_idx:
                next_line = lines[next_line_idx]
                next_indent = len(next_line) - len(next_line.lstrip())
                next_stripped = next_line.strip()

                if next_indent > indent:
                    if next_stripped.startswith("- "):
                        # Parse list
                        parsed_list, new_idx = _parse_yaml_list(
                            lines, next_line_idx, end_idx, next_indent
                        )
                        result[key] = parsed_list
                        i = new_idx
                        continue
                    else:
                        # Parse nested dict
                        parsed_dict, new_idx = _parse_yaml_lines(
                            lines, next_line_idx, end_idx, next_indent
                        )
                        result[key] = parsed_dict
                        i = new_idx
                        continue
                else:
                    result[key] = None
                    i += 1
                    continue
            else:
                result[key] = None
                i += 1
                continue

        elif stripped_val == "|":
            # Start of multiline literal sequence
            in_multiline = True
            current_key = key

            # Find the indentation of the first non-empty line
            next_line_idx = i + 1
            while next_line_idx < end_idx and (
                not lines[next_line_idx].strip()
                or lines[next_line_idx].strip().startswith("#")
            ):
                next_line_idx += 1

            if next_line_idx < end_idx:
                multiline_indent = len(lines[next_line_idx]) - len(
                    lines[next_line_idx].lstrip()
                )
                if multiline_indent <= indent:
                    # Invalid multiline indent, fallback
                    in_multiline = False
                    result[key] = ""
            else:
                in_multiline = False
                result[key] = ""
            i += 1
            continue
        else:
            # Inline scalar value
            result[key] = _parse_scalar(stripped_val)

        i += 1

    # Flush multiline
    if in_multiline and current_key is not None:
        while multiline_buffer and not multiline_buffer[-1].strip():
            multiline_buffer.pop()
        cleaned_buffer = [
            line_str[multiline_indent:]
            if line_str.startswith(" " * multiline_indent)
            else line_str.lstrip()
            for line_str in multiline_buffer
        ]
        result[current_key] = "\n".join(cleaned_buffer)

    return result, i


def _parse_yaml_list(
    lines: list[str], start_idx: int, end_idx: int, base_indent: int
) -> tuple[list[Any], int]:
    """Parse a YAML block sequence recursively."""
    result: list[Any] = []
    i = start_idx

    while i < end_idx:
        line = lines[i]
        stripped = line.strip()

        if not stripped or stripped.startswith("#"):
            i += 1
            continue

        indent = len(line) - len(line.lstrip())
        if indent < base_indent:
            break

        if stripped.startswith("- "):
            raw_val = stripped[2:].strip()
            stripped_val = _strip_inline_comment(raw_val)

            if stripped_val == "":
                # Could be nested structure or empty item
                next_line_idx = i + 1
                while next_line_idx < end_idx and (
                    not lines[next_line_idx].strip()
                    or lines[next_line_idx].strip().startswith("#")
                ):
                    next_line_idx += 1

                if next_line_idx < end_idx:
                    next_line = lines[next_line_idx]
                    next_indent = len(next_line) - len(next_line.lstrip())

                    if next_indent > indent:
                        parsed_dict, new_idx = _parse_yaml_lines(
                            lines, next_line_idx, end_idx, next_indent
                        )
                        result.append(parsed_dict)
                        i = new_idx
                        continue
                    else:
                        result.append(None)
                else:
                    result.append(None)
            else:
                result.append(_parse_scalar(stripped_val))
        else:
            break  # Not a list item anymore

        i += 1

    return result, i


def _parse_scalar(val: str) -> Any:
    """Parses a YAML scalar value to native Python types."""
    # Quoted strings
    if (val.startswith('"') and val.endswith('"')) or (
        val.startswith("'") and val.endswith("'")
    ):
        if len(val) >= 2:
            return val[1:-1]
        return val

    # Booleans
    lower_val = val.lower()
    if lower_val == "true":
        return True
    if lower_val == "false":
        return False

    # Standard integers
    if val.isdigit() or (val.startswith("-") and val[1:].isdigit()):
        try:
            return int(val)
        except ValueError:
            pass

    # Standard floats
    try:
        if "." in val:
            return float(val)
    except ValueError:
        pass

    return val
