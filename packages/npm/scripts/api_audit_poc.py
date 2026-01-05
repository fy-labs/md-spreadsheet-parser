import inspect
import os
import sys
from pathlib import Path

# Add libs to path to load the installed package
current_dir = Path(__file__).parent
libs_dir = current_dir.parent / "libs"
sys.path.insert(0, str(libs_dir))

try:
    import md_spreadsheet_parser
    import md_spreadsheet_parser.models
except ImportError:
    print(
        "Error: Could not import md_spreadsheet_parser. Make sure it is installed in 'libs'."
    )
    sys.exit(1)


def get_public_api():
    api = {"functions": [], "classes": []}

    # Inspect top-level __init__
    for name, obj in inspect.getmembers(md_spreadsheet_parser):
        if name.startswith("_"):
            continue
        if inspect.isfunction(obj):
            sig = inspect.signature(obj)
            api["functions"].append(f"{name}{sig}")
        elif inspect.isclass(obj):
            # focus on models for now
            if obj.__module__.startswith("md_spreadsheet_parser"):
                api["classes"].append(name)

    return api


def main():
    print("--- Python Public API ---")
    api = get_public_api()

    print("\n[Functions]")
    for f in api["functions"]:
        print(f"  {f}")

    print("\n[Classes (Models)]")
    for c in api["classes"]:
        print(f"  {c}")

    print("\n--- Current WIT Interface ---")
    wit_path = current_dir.parent / "wit" / "parser.wit"
    if wit_path.exists():
        with open(wit_path) as f:
            print(f.read())
    else:
        print("wit/parser.wit not found")


if __name__ == "__main__":
    main()
