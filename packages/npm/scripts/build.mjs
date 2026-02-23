
import { execa } from 'execa';
import { rm, mkdir, readFile, writeFile } from 'node:fs/promises';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const rootDir = join(__dirname, '..', '..', '..', '..'); // Workspace root (md-spreadsheet-suite)
const pkgDir = join(__dirname, '..');

// Helper to run commands
async function run(file, args = [], options = {}) {
    const cmdStr = `${file} ${args.join(' ')}`;
    console.log(`> ${cmdStr}`);

    // Default options
    const defaultOptions = {
        cwd: pkgDir,
        stdio: 'inherit',
        shell: true // Use shell to resolve commands like 'uv'
    };

    console.log(`PATH: ${process.env.PATH}`);
    try {
        await execa(file, args, { ...defaultOptions, ...options });
    } catch (e) {
        console.error(`Command failed: ${cmdStr}`);
        process.exit(1);
    }
}

async function main() {
    // 1. Cleanup
    console.log('--- Cleaning ---');
    await rm(join(pkgDir, 'dist'), { recursive: true, force: true });
    await rm(join(pkgDir, 'libs'), { recursive: true, force: true });
    await mkdir(join(pkgDir, 'dist'), { recursive: true });
    await mkdir(join(pkgDir, 'libs'), { recursive: true });

    // 2. Build Python Wheel
    console.log('--- Building Python Wheel ---');

    // Resolve uv path just in case
    let uvPath = 'uv';
    try {
        const { stdout } = await execa('which', ['uv'], { shell: true });
        uvPath = stdout.trim();
        console.log(`Using uv at: ${uvPath}`);
    } catch {
        console.warn('Could not find uv with "which", falling back to "uv"');
    }

    // We run `uv build` in the root (where pyproject.toml is)
    // SKIPPED: Running via subprocess might hang or fail in some envs. Assume external build.
    // await run(uvPath, ['build'], { cwd: join(rootDir, 'md-spreadsheet-parser') });

    // 3. Extract Wheel
    console.log('--- Extracting Wheel ---');
    // Find the latest wheel from md-spreadsheet-parser/dist (parser's dist, not workspace root)
    const parserDir = join(__dirname, '..', '..', '..'); // md-spreadsheet-parser root
    const { stdout } = await execa('ls', [join(parserDir, 'dist', '*.whl')], { shell: true });
    const wheel = stdout.trim().split('\n')[0];

    if (!wheel) {
        console.error('No wheels found!');
        process.exit(1);
    }
    console.log(`Using wheel: ${wheel}`);
    await run('unzip', ['-o', wheel, '-d', join(pkgDir, 'libs')]);

    // 4. Generate WIT & Adapter
    console.log('--- Generating WIT & Adapter ---');
    await run('uv', ['run', '--with', 'griffe', 'python3', 'scripts/generate_wit.py']);

    // 5. Componentize (Create .wasm)
    console.log('--- Componentizing to WASM ---');
    // We pass PYTHONPATH so componentize-py finds the unzipped libs
    await run(
        'uv',
        ['run', '--with', 'componentize-py', '--', 'componentize-py', '-d', 'wit', '-w', 'spreadsheet-parser', 'componentize', '-p', 'libs', '-p', 'src', '-o', 'dist/parser.wasm', 'app'],
        {
            cwd: pkgDir,
            env: { ...process.env, PYTHONPATH: 'libs' }
        }
    );

    // 5. Transpile (Create JS)
    console.log('--- Transpiling to JS ---');
    await run('npx', ['jco', 'transpile', 'dist/parser.wasm', '-o', 'dist']);

    // 5.1 Post-process: Fix WASM fetch paths for Vite dev mode compatibility
    console.log('--- Fixing WASM fetch paths for Vite compatibility ---');
    const parserJsPath = join(pkgDir, 'dist', 'parser.js');
    let parserJs = await readFile(parserJsPath, 'utf-8');

    // Replace: fetch('./parser.core.wasm') -> fetch(new URL('./parser.core.wasm', import.meta.url))
    // This pattern matches various forms like fetch('parser.core.wasm') or fetch('./parser.core.wasm')
    const fetchPattern = /fetch\(\s*(['"])(\.\/)?(parser\.core\d*\.wasm)\1\s*\)/g;
    parserJs = parserJs.replace(fetchPattern, (match, quote, prefix, filename) => {
        return `fetch(new URL('./${filename}', import.meta.url))`;
    });

    await writeFile(parserJsPath, parserJs);
    console.log('  Fixed WASM fetch paths to use import.meta.url');

    // 5.5 Cleanup intermediate WASM
    console.log('--- Removing intermediate WASM ---');
    await rm(join(pkgDir, 'dist', 'parser.wasm'));

    // 6. Compile TypeScript
    console.log('--- Compiling TypeScript ---');
    await run('npx', ['tsc']);

    console.log('--- Build Complete ---');
}

main().catch(err => {
    console.error(err);
    process.exit(1);
});
