Fixed WASM loading in Vite dev mode by using `import.meta.url` for proper path resolution.

- Modified build script to post-process JCO transpile output
- Replaced relative path `fetch('./parser.core.wasm')` with `fetch(new URL('./parser.core.wasm', import.meta.url))`
- This ensures WASM files are correctly resolved in both bundled and development environments
