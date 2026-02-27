from md_spreadsheet_parser.yaml_parser import (
    extract_frontmatter,
    parse_yaml_frontmatter,
)


def test_extract_frontmatter():
    markdown = "---\ntitle: test\n---\n# Heading\ncontent"
    frontmatter, remaining = extract_frontmatter(markdown)
    assert frontmatter == "title: test"
    assert remaining == "# Heading\ncontent"

    markdown_no_frontmatter = "# Heading\ncontent"
    frontmatter, remaining = extract_frontmatter(markdown_no_frontmatter)
    assert frontmatter is None
    assert remaining == "# Heading\ncontent"

    markdown_empty_frontmatter = "---\n---\n# Heading"
    frontmatter, remaining = extract_frontmatter(markdown_empty_frontmatter)
    assert frontmatter == ""
    assert remaining == "# Heading"


def test_parse_yaml_frontmatter_scalars():
    yaml_text = """
    string1: value
    string2: "quoted value"
    string3: 'single quoted'
    int1: 42
    int2: -10
    float1: 3.14
    bool1: true
    bool2: False
    """
    result = parse_yaml_frontmatter(yaml_text)
    assert result == {
        "string1": "value",
        "string2": "quoted value",
        "string3": "single quoted",
        "int1": 42,
        "int2": -10,
        "float1": 3.14,
        "bool1": True,
        "bool2": False,
    }


def test_parse_yaml_frontmatter_comments():
    yaml_text = """
    # This is a comment
    key1: value1 # inline comment
    key2: "value # with hash"
    """
    result = parse_yaml_frontmatter(yaml_text)
    assert result == {"key1": "value1", "key2": "value # with hash"}


def test_parse_yaml_frontmatter_lists():
    yaml_text = """
    list1:
      - item1
      - item2
    list2:
      - 1
      - true
    """
    result = parse_yaml_frontmatter(yaml_text)
    assert result == {"list1": ["item1", "item2"], "list2": [1, True]}


def test_parse_yaml_frontmatter_dicts():
    yaml_text = """
    dict1:
      key1: val1
      key2: 2
    dict2:
      nested:
        key: val
    """
    result = parse_yaml_frontmatter(yaml_text)
    assert result == {
        "dict1": {"key1": "val1", "key2": 2},
        "dict2": {"nested": {"key": "val"}},
    }


def test_parse_yaml_frontmatter_multiline():
    yaml_text = """
    desc: |
      Line 1
      Line 2
        Indented
    other: val
    """
    result = parse_yaml_frontmatter(yaml_text)
    assert result == {"desc": "Line 1\nLine 2\n  Indented", "other": "val"}


def test_parse_yaml_frontmatter_mixed():
    yaml_text = """
    # Book Metadata Block
    title: My Book # The title of the book
    author:
      name: John Doe
      tags:
        - author
        - writer # He writes a lot
    chapters:
      # List of chapters
      - Chapter 1
      - Chapter 2
    summary: |
      A great book.
      Read it now.
    published: true # is it out?
    """
    result = parse_yaml_frontmatter(yaml_text)
    assert result == {
        "title": "My Book",
        "author": {"name": "John Doe", "tags": ["author", "writer"]},
        "chapters": ["Chapter 1", "Chapter 2"],
        "summary": "A great book.\nRead it now.",
        "published": True,
    }
