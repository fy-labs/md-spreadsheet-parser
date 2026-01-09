"""Template renderer for code generation using Jinja2."""

from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader


# Template directory
TEMPLATES_DIR = Path(__file__).parent.parent / "templates"


def create_jinja_env() -> Environment:
    """Create a Jinja2 environment configured for code generation."""
    return Environment(
        loader=FileSystemLoader(str(TEMPLATES_DIR)),
        trim_blocks=True,
        lstrip_blocks=True,
        keep_trailing_newline=True,
    )


def render_template(template_name: str, **context: Any) -> str:
    """Render a template with the given context.

    Args:
        template_name: Name of the template file (e.g., "index.ts.jinja2")
        **context: Variables to pass to the template

    Returns:
        Rendered template as string
    """
    env = create_jinja_env()
    template = env.get_template(template_name)
    return template.render(**context)


def render_ts_wrapper(
    wasm_imports: list[str],
    global_functions: list[dict[str, Any]],
    classes: list[dict[str, Any]],
) -> str:
    """Render the TypeScript wrapper (index.ts).

    Args:
        wasm_imports: List of WASM import statements
        global_functions: Metadata for global functions
        classes: Metadata for classes to generate

    Returns:
        Generated TypeScript code
    """
    return render_template(
        "index.ts.jinja2",
        wasm_imports=wasm_imports,
        global_functions=global_functions,
        classes=classes,
    )


def render_adapter(records: list[dict[str, Any]]) -> str:
    """Render the Python adapter (generated_adapter.py).

    Args:
        records: Metadata for records to generate convert/unwrap functions

    Returns:
        Generated Python adapter code
    """
    return render_template(
        "adapter.py.jinja2",
        records=records,
    )


def render_wit_file(
    definitions: list[str],
    exports: list[str],
    used_types: list[str],
) -> str:
    """Render the WIT file (generated.wit).

    Args:
        definitions: List of WIT type definitions
        exports: List of WIT export statements
        used_types: List of types used in the world

    Returns:
        Generated WIT file content
    """
    return render_template(
        "generated.wit.jinja2",
        definitions=definitions,
        exports=exports,
        used_types=used_types,
    )


def render_app_file(methods: list[str]) -> str:
    """Render the app wrapper (app.py).

    Args:
        methods: List of method definitions for WitWorld class

    Returns:
        Generated app.py content
    """
    return render_template(
        "app.py.jinja2",
        methods=methods,
    )
