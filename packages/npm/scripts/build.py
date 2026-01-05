import os
import shutil
import subprocess
import sys
from pathlib import Path

# Paths
current_dir = Path(__file__).parent
pkg_dir = current_dir.parent
root_dir = pkg_dir.parent.parent


def run(cmd, cwd=None, env=None):
    print(f"> {' '.join(cmd)}")
    try:
        if env:
            # Merge with current env
            current_env = os.environ.copy()
            current_env.update(env)
            env = current_env

        # Prevent hanging on stdin
        subprocess.run(cmd, cwd=cwd, env=env, check=True, stdin=subprocess.DEVNULL)
    except subprocess.CalledProcessError as e:
        print(f"Error running command: {e}")
        sys.exit(1)
    except FileNotFoundError as e:
        print(f"Command not found: {e}")
        sys.exit(1)


def main():
    print("--- Cleaning ---")
    dist_dir = pkg_dir / "dist"
    libs_dir = pkg_dir / "libs"

    if dist_dir.exists():
        shutil.rmtree(dist_dir)
    if libs_dir.exists():
        shutil.rmtree(libs_dir)
    dist_dir.mkdir()
    libs_dir.mkdir()

    print("--- Building Python Wheel ---")
    # Using 'uv' directly. Ensure it's in PATH or use full path if needed.
    # root_dir is the repo root, which is where pyproject.toml is.
    # SKIPPED: Running this via subprocess hangs. Assume wheel is built externally.
    # run(["uv", "build"], cwd=root_dir)

    print("--- Extracting Wheel ---")
    wheels = list((root_dir / "dist").glob("*.whl"))
    if not wheels:
        print("No wheels found!")
        sys.exit(1)

    # Sort by modification time to get the latest
    latest_wheel = max(wheels, key=os.path.getctime)
    print(f"Using wheel: {latest_wheel}")

    run(["pip", "install", "-t", str(libs_dir), str(latest_wheel)])

    print("--- Componentizing to WASM ---")
    # Copy src/app.py to root to avoid PYTHONPATH issues
    shutil.copy("src/app.py", "app.py")

    try:
        run(
            [
                "uv",
                "run",
                "--with",
                "componentize-py",
                "--",
                "componentize-py",
                "-d",
                "wit",
                "-w",
                "spreadsheet-parser",
                "componentize",
                "-p",
                "libs",
                "-p",
                ".",
                "-o",
                "dist/parser.wasm",
                "app",
            ],
            cwd=pkg_dir,
        )
    finally:
        if os.path.exists("app.py"):
            os.remove("app.py")

    print("--- Transpiling to JS ---")
    # npx needs to affect the current package
    run(["npx", "jco", "transpile", "dist/parser.wasm", "-o", "dist"], cwd=pkg_dir)

    print("--- Build Complete ---")


if __name__ == "__main__":
    main()
