Implemented support for GitHub Flavored Markdown (GFM) table alignment syntax (e.g. `| :--- | :---: | ---: |`).
The `Table` model now has an `alignments` attribute, and the parser/generator preserves this information during round-trip operations.
