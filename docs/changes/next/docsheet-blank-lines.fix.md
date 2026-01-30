Preserve leading blank lines in Doc Sheet content

When Doc Sheets have blank lines between the header and text content,
those lines are now correctly preserved in the editor. Previously,
`markdown.strip()` removed both leading and trailing whitespace.
Changed to `markdown.rstrip()` to only remove trailing whitespace.
