### Workbook Metadata Support

Added `metadata` field to the `Workbook` model, allowing arbitrary data storage at the workbook level. This aligns the `Workbook` model with `Sheet` and `Table` models.

```python
wb = Workbook(sheets=[], metadata={"author": "Alice"})
# Metadata is persisted at the end of the file:
# <!-- md-spreadsheet-workbook-metadata: {"author": "Alice"} -->
```
