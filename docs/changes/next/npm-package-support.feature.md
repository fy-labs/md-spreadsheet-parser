### NPM Package Support (WASM/Python Bridge)

Introduced comprehensive support for building an NPM package (`md-spreadsheet-parser`) powered by the Python core via WebAssembly (WASM).

*   **WASM Compilation**: Uses `componentize-py` to compile the Python library into a WASM Component, enabling usage in Node.js environments.
*   **TypeScript Wrappers**: Automatically generates high-fidelity TypeScript class wrappers that mirror the Python object model (API Parity).
    *   Python `Table`, `Workbook`, `Sheet` classes are fully exposed in TypeScript.
    *   Methods like `toMarkdown`, `updateCell`, and `addSheet` are available directly on TypeScript objects.
*   **Seamless Integration**:
    *   **JSON Marshalling**: Metadata dictionaries are automatically handled (serialized/deserialized) across the boundary.
    *   **Optional Arguments**: Python default arguments are correctly mapped to optional TypeScript parameters (e.g., `schema?`).
    *   **Client-Side Mapping**: `Table.toModels` supports passing browser-side schema classes or Zod-like validators.
*   **Verification**: Added a robust verification environment (`verification-env`) ensuring cross-language compatibility.
