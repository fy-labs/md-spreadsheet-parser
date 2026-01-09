"""Griffe-based module scanning utilities for extracting API metadata."""

import re
from typing import Any

from .name_converter import to_kebab_case
from .type_mapper import map_python_to_wit, is_json_type


def register_known_models(modules: list[Any]) -> set[str]:
    """Pre-scan modules to register known class names for type mapping.

    Args:
        modules: List of griffe Module objects

    Returns:
        Set of class names that are known models
    """
    known_models: set[str] = set()
    for mod in modules:
        for name, member in mod.members.items():
            if member.is_alias:
                continue
            if (
                member.is_class
                and not name.startswith("_")
                and not name.endswith("JSON")
            ):
                known_models.add(name)
    return known_models


def scan_module_for_classes(module, known_models: set[str]) -> list[dict[str, Any]]:
    """Scan a module for classes to expose as records.

    Args:
        module: griffe Module object
        known_models: Set of known model class names

    Returns:
        List of class metadata dicts with keys:
            - class_name: Python class name
            - wit_name: WIT record name (kebab-case)
            - fields: List of field metadata
    """
    classes = []
    for name, member in module.members.items():
        if member.is_alias:
            continue
        if not member.is_class:
            continue
        if name.startswith("_"):
            continue
        if name.endswith("JSON"):
            continue

        wit_name = to_kebab_case(name)
        
        # Extract fields
        fields = []
        for field_name, field_member in member.members.items():
            if field_name.startswith("_"):
                continue
            if not hasattr(field_member, "annotation") or not field_member.annotation:
                continue
            if callable(getattr(field_member, "is_function", None)) and field_member.is_function:
                continue

            py_type = str(field_member.annotation)
            wit_type, adapter_tmpl = map_python_to_wit(py_type, known_models)
            
            fields.append({
                "name": field_name,
                "py_type": py_type,
                "wit_type": wit_type,
                "adapter_tmpl": adapter_tmpl,
                "is_json": is_json_type(py_type),
                "has_default": getattr(field_member, "value", None) is not None,
            })

        classes.append({
            "class_name": name,
            "wit_name": wit_name,
            "fields": fields,
            "module_path": module.path,
        })

    return classes


def scan_module_for_functions(module, known_models: set[str]) -> list[dict[str, Any]]:
    """Scan a module for standalone functions to expose.

    Args:
        module: griffe Module object
        known_models: Set of known model class names

    Returns:
        List of function metadata dicts
    """
    functions = []
    for name, member in module.members.items():
        if member.is_alias:
            continue
        if not member.is_function:
            continue
        if name.startswith("_"):
            continue

        params = []
        for param in member.parameters:
            if param.name in ("self", "cls"):
                continue
            if not param.annotation:
                continue

            py_type = str(param.annotation)
            wit_type, adapter_tmpl = map_python_to_wit(py_type, known_models)
            
            # Handle default values -> make optional in WIT
            has_default = param.default is not None
            if has_default and "option<" not in wit_type:
                wit_type = f"option<{wit_type}>"

            params.append({
                "name": param.name,
                "py_type": py_type,
                "wit_type": wit_type,
                "adapter_tmpl": adapter_tmpl,
                "has_default": has_default,
            })

        # Return type
        ret_type = None
        if member.returns:
            ret_py = str(member.returns)
            ret_wit, ret_adapter = map_python_to_wit(ret_py, known_models)
            ret_type = {
                "py_type": ret_py,
                "wit_type": ret_wit,
                "adapter_tmpl": ret_adapter,
            }

        functions.append({
            "name": name,
            "wit_name": name.replace("_", "-"),
            "params": params,
            "return_type": ret_type,
            "module_path": module.path,
        })

    return functions


def scan_class_methods(module, known_models: set[str]) -> list[dict[str, Any]]:
    """Scan classes for methods to expose as flat functions.

    Args:
        module: griffe Module object
        known_models: Set of known model class names

    Returns:
        List of method metadata dicts
    """
    methods = []
    for class_name, class_member in module.members.items():
        if class_member.is_alias:
            continue
        if not class_member.is_class:
            continue
        if class_name.startswith("_") or class_name.endswith("JSON"):
            continue

        wit_class_prefix = to_kebab_case(class_name)

        for method_name, method in class_member.members.items():
            if not method.is_function:
                continue
            if method_name.startswith("_"):
                continue

            wit_func_name = f"{wit_class_prefix}-{method_name.replace('_', '-')}"

            params = []
            for param in method.parameters:
                if param.name in ("self", "cls"):
                    continue
                if not param.annotation:
                    continue

                py_type = str(param.annotation)
                wit_type, adapter_tmpl = map_python_to_wit(py_type, known_models)

                has_default = param.default is not None
                if has_default and "option<" not in wit_type:
                    wit_type = f"option<{wit_type}>"

                params.append({
                    "name": param.name,
                    "py_type": py_type,
                    "wit_type": wit_type,
                    "adapter_tmpl": adapter_tmpl,
                    "has_default": has_default,
                })

            ret_type = None
            if method.returns:
                ret_py = str(method.returns)
                ret_wit, ret_adapter = map_python_to_wit(ret_py, known_models)
                ret_type = {
                    "py_type": ret_py,
                    "wit_type": ret_wit,
                    "adapter_tmpl": ret_adapter,
                }

            methods.append({
                "class_name": class_name,
                "method_name": method_name,
                "wit_func_name": wit_func_name,
                "params": params,
                "return_type": ret_type,
            })

    return methods
