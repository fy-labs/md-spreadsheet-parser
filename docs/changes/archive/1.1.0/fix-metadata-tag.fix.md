# Fix table metadata tag recognition

Fixed a bug in `parsing.py` where the parser was incorrectly looking for `<!-- md-spreadsheet-metadata: ... -->` instead of `<!-- md-spreadsheet-table-metadata: ... -->` when extracting tables from blocks. This ensures consistency with the generator and specification.
