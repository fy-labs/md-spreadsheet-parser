import re
from pathlib import Path
from typing import Any

import griffe

from generator.renderer import render_ts_wrapper

class WitGenerator:
    def __init__(self):
        self.definitions = []
        self.adapter_functions = []
        # We need a shared pool of known models across all modules for mapping
        self.known_models = set()
        self.world_exports = []
        self.app_methods = []
        self.global_functions = []  # Metadata for global functions
        self.discovered_models = {}  # name -> {fields: [], methods: []}

    def is_json_type(self, py_type_str: str) -> bool:
        py_type = py_type_str.strip()
        if py_type.startswith("dict[") and "Any" in py_type:
            return True
        if py_type == "dict":
            return True
        return False

    def register_models(self, modules: list[Any]):
        """Pre-scan modules to register known class names for type mapping"""
        for mod in modules:
            for name, member in mod.members.items():
                if member.is_alias:
                    continue
                if (
                    member.is_class
                    and not name.startswith("_")
                    and not name.endswith("JSON")
                ):
                    self.known_models.add(name)

    def scan_module_for_records(self, module):
        # Topologically sorted list of models we want to expose
        for name, member in module.members.items():
            # Skip aliases (imports from other modules)
            if member.is_alias:
                continue

            if not member.is_class:
                continue

            # Skip private
            if name.startswith("_"):
                continue

            # Skip JSON TypedDicts
            if name.endswith("JSON"):
                continue

            # Skip explicitly imported Exceptions if any

            # We assume it's a dataclass-like model we want to expose
            wit_name = re.sub(r"(?<!^)(?=[A-Z])", "-", name).lower()

            self.generate_record(module, name, wit_name)

    def scan_module_for_functions(self, module):
        # Do NOT reset lists here, we want to accumulate across modules
        # self.world_exports = []
        # self.app_methods = []

        module_path = module.path

        for name, member in module.members.items():
            # CRITICAL: Check alias first to avoid resolution error
            if member.is_alias:
                continue

            if not member.is_function:
                continue
            if name.startswith("_"):
                continue

            # Use griffe to get parameters and return annotation
            params = member.parameters
            # params is a Parameters object (list-like)

            wit_params = []
            py_call_args = []

            for param in params:
                if param.name == "self" or param.name == "cls":
                    continue

                # Check annotation
                if not param.annotation:
                    continue  # Skip untyped for safety

                py_type = str(param.annotation)
                wit_type, adapter_tmpl = self.map_type(py_type)

                # Handle default values -> make optional in WIT
                if param.default is not None and "option<" not in wit_type:
                    wit_type = f"option<{wit_type}>"

                wit_param_name = param.name.replace("_", "-")
                wit_params.append(f"{wit_param_name}: {wit_type}")

                py_call_args.append(param.name)

            # Return type
            ret_type = "string"  # default
            if member.returns:
                rt = str(member.returns)
                wit_ret, _ = self.map_type(rt)
                ret_type = wit_ret

            # WIT Export
            wit_params_str = ", ".join(wit_params)
            wit_name = name.replace("_", "-")
            self.world_exports.append(
                f"export {wit_name}: func({wit_params_str}) -> {ret_type};"
            )

            # Store for TS Wrapper
            self.global_functions.append(
                {
                    "name": name,
                    "wit_name": wit_name,
                    "params": params,
                    "ret": member.returns,  # Griffe expression
                }
            )

            # App Method
            # Use dynamic module path
            call_expr = f"{module_path}.{name}(**kwargs)"

            # Generate wrapper method
            # We type args as Any=None to accept whatever WIT sends (including None for options)
            method_args = [
                p.name + ": Any = None" for p in params if p.name not in ("self", "cls")
            ]

            # Construct kwargs to invoke the underlying function, skipping None values so defaults trigger
            method_body = "        kwargs = {}\n"
            for p in params:
                if p.name in ("self", "cls"):
                    continue
                # Determine if unwrap is needed
                val_expr = p.name
                if p.annotation:
                    py_type = str(p.annotation).strip()
                    clean_type = (
                        py_type.replace(" | None", "").replace("Optional[", "")[:-1]
                        if "Optional[" in py_type
                        else py_type.replace(" | None", "")
                    )

                    if clean_type in self.known_models:
                        uw_name = (
                            re.sub(r"(?<!^)(?=[A-Z])", "-", clean_type)
                            .lower()
                            .replace("-", "_")
                        )
                        val_expr = f"unwrap_{uw_name}({p.name})"
                    elif "type[" in clean_type or "Type[" in clean_type:
                        # Handle type[T] -> resolve_model_class
                        val_expr = f"resolve_model_class({p.name})"
                    elif clean_type.startswith("list["):
                        inner = clean_type[5:-1]
                        if inner in self.known_models:
                            uw_name = (
                                re.sub(r"(?<!^)(?=[A-Z])", "-", inner)
                                .lower()
                                .replace("-", "_")
                            )
                            val_expr = f"[unwrap_{uw_name}(x) for x in {p.name}]"

                # If valid param, add to kwargs if not None
                method_body += f"        if {p.name} is not None: kwargs['{p.name}'] = {val_expr}\n"

            # Determine converter for return
            if member.returns:
                _, adapter_tmpl = self.map_type(str(member.returns))
                # adapter expects the value expression
                final_expr = adapter_tmpl.replace("__FIELD__", call_expr)
            else:
                final_expr = call_expr

            method_def = f"    def {name}(self, {', '.join(method_args)}):\n"
            method_def += method_body
            method_def += f"        return {final_expr}"
            self.app_methods.append(method_def)

    def map_type(self, py_type_str: str) -> tuple[str, str]:
        """
        Maps Python type string to (WIT type, Adapter transformation).
        Adapter transformation is a format string like "__FIELD__", "json.dumps(__FIELD__)", etc.
        """
        # Clean up
        py_type = py_type_str.strip()

        # Handle Optional ( | None)
        if " | None" in py_type or "Optional[" in py_type:
            inner = (
                py_type.replace(" | None", "").replace("Optional[", "")[:-1]
                if "Optional[" in py_type
                else py_type.replace(" | None", "")
            )
            wit_type, adapter = self.map_type(inner)
            return (
                f"option<{wit_type}>",
                adapter,
            )

        # Handle List
        if py_type.startswith("list["):
            inner = py_type[5:-1]
            wit_type, adapter = self.map_type(inner)
            if adapter == "__FIELD__":
                return f"list<{wit_type}>", "__FIELD__"
            else:
                tmpl = adapter.replace("__FIELD__", "x")
                return f"list<{wit_type}>", f"[{tmpl} for x in __FIELD__]"

        # Handle Dict (Any) -> JSON string
        if py_type.startswith("dict[") and "Any" in py_type:
            return "string", "json.dumps(__FIELD__ or {})"

        # Handle simple dict without brackets (sometimes annotation is just 'dict')
        if py_type == "dict":
            return "string", "json.dumps(__FIELD__ or {})"

        # Primitives
        if py_type == "str":
            return "string", "__FIELD__"
        if py_type == "int":
            return "s32", "__FIELD__"
        if py_type == "bool":
            return "bool", "__FIELD__"
        if py_type == "float":
            return "float64", "__FIELD__"

        # Check against our known models to allow generic mapping
        if py_type in self.known_models:
            # It's one of ours!
            # WIT name inference
            wit_name = re.sub(r"(?<!^)(?=[A-Z])", "-", py_type).lower()
            adapter_fn = f"convert_{wit_name.replace('-', '_')}"
            return wit_name, f"{adapter_fn}(__FIELD__)"

        # Special case for AlignmentType alias
        if py_type == "AlignmentType":
            return "alignment-type", "convert_alignment_type(__FIELD__)"

        # Default fallback
        # print(f"Warning: Unknown type {py_type}, falling back to string")
        return "string", "str(__FIELD__)"

    def get_all_members(self, cls, module):
        members = {}
        for base in cls.bases:
            # Simple inheritance within same module
            if isinstance(base, griffe.ExprName):
                if base.name in module.members:
                    base_cls = module.members[base.name]
                    members.update(self.get_all_members(base_cls, module))

        for name, m in cls.members.items():
            members[name] = m
        return members

    def generate_record(self, module, class_name: str, wit_name: str):
        # Resolve all members including inherited ones
        obj = module.members[class_name]
        all_members = self.get_all_members(obj, module)

        fields = []
        adapter_lines = []
        unwrap_lines = []

        # Local class for WIT record
        local_class_name = f"Wit{class_name}"

        self.adapter_functions.append("@dataclass")
        self.adapter_functions.append(f"class {local_class_name}:")

        # Gather relevant fields
        valid_members = {}
        for name, member in all_members.items():
            if name.startswith("_") or name == "json":
                continue
            if member.is_function:
                continue
            if hasattr(member, "is_property") and member.is_property:
                continue
            if not hasattr(member, "annotation"):
                continue
            valid_members[name] = member

        for name, member in valid_members.items():
            py_type = str(member.annotation)
            wit_type, adapter_tmpl = self.map_type(py_type)

            # Check defaults
            has_default = getattr(member, "value", None) is not None
            # If default exists, ensure optional in WIT
            if has_default and "option<" not in wit_type:
                wit_type = f"option<{wit_type}>"

            # Kebab-case for WIT field
            wit_field = name.replace("_", "-")

            # Python attribute for the local class
            py_attr_name = name

            fields.append(f"{wit_field}: {wit_type}")
            self.adapter_functions.append(f"    {py_attr_name}: Any = None")

        # Store for TS generation
        if class_name not in self.discovered_models:
            self.discovered_models[class_name] = {"fields": [], "methods": []}

        self.discovered_models[class_name]["fields"] = [
            {
                "js_name": re.sub(
                    r"_([a-z])", lambda g: g.group(1).upper(), name
                ),  # camelCase for TS
                "py_name": name,  # original snake_case for fallback
                "wit_type": self.map_type(str(member.annotation))[0],
                "is_json": self.is_json_type(str(member.annotation)),
                "py_type": str(member.annotation),
            }
            for name, member in valid_members.items()
        ]

        self.adapter_functions.append("")  # End of class

        # Python -> WIT Adapter (convert_...)
        adapter_lines.append(
            f"def convert_{wit_name.replace('-', '_')}(obj: Any) -> {local_class_name}:"
        )
        adapter_lines.append("    if obj is None: return None")
        adapter_lines.append(f"    res = {local_class_name}()")

        for name, member in valid_members.items():
            py_type = str(member.annotation)
            # Default options check
            has_default = getattr(member, "value", None) is not None
            wit_type, adapter_tmpl = self.map_type(py_type)
            if has_default and "option<" not in wit_type:
                wit_type = f"option<{wit_type}>"

            field_access = f"obj.{name}"
            transformation = adapter_tmpl.replace("__FIELD__", field_access)

            if "option<" in wit_type and adapter_tmpl != "__FIELD__":
                # Just safe guard optional access
                transformation = (
                    f"{transformation} if {field_access} is not None else None"
                )

            adapter_lines.append(f"    res.{name} = {transformation}")

        adapter_lines.append("    return res")
        adapter_lines.append("")

        # WIT -> Python Adapter (unwrap_...)
        # We need to construct the REAL Python object.

        real_cls_access = ""
        if "schemas" in module.path:
            real_cls_access = f"schemas.{class_name}"
        elif "models" in module.path:
            real_cls_access = f"models.{class_name}"
        else:
            real_cls_access = f"{module.path}.{class_name}"

        unwrap_lines.append(
            f"def unwrap_{wit_name.replace('-', '_')}(obj: Any) -> Any:"
        )
        unwrap_lines.append("    if obj is None: return None")
        unwrap_lines.append("    kwargs = {}")

        for name, member in valid_members.items():
            py_type = str(member.annotation)
            wit_field_access = f"obj.{name}"

            val_expr = wit_field_access

            # Clean py_type
            clean_type = py_type.strip()
            if " | None" in clean_type or "Optional[" in clean_type:
                clean_type = (
                    clean_type.replace(" | None", "").replace("Optional[", "")[:-1]
                    if "Optional[" in clean_type
                    else clean_type.replace(" | None", "")
                )

            if clean_type in self.known_models:
                uw_name = (
                    re.sub(r"(?<!^)(?=[A-Z])", "-", clean_type)
                    .lower()
                    .replace("-", "_")
                )
                val_expr = f"unwrap_{uw_name}({wit_field_access})"
            elif clean_type.startswith("list["):
                inner = clean_type[5:-1]
                if inner in self.known_models:
                    uw_name = (
                        re.sub(r"(?<!^)(?=[A-Z])", "-", inner).lower().replace("-", "_")
                    )
                    val_expr = f"[unwrap_{uw_name}(x) for x in {wit_field_access}]"
            elif self.is_json_type(py_type):
                val_expr = f"json.loads({wit_field_access})"

            # Use kwargs only if value is present (for defaults)
            unwrap_lines.append(f"    if {wit_field_access} is not None:")
            unwrap_lines.append(f"        kwargs['{name}'] = {val_expr}")

        unwrap_lines.append(f"    return {real_cls_access}(**kwargs)")
        unwrap_lines.append("")

        self.definitions.append(f"record {wit_name} {{")
        for f in fields:
            self.definitions.append(f"    {f},")
        self.definitions.append("}")
        self.definitions.append("")

        self.adapter_functions.extend(adapter_lines)
        self.adapter_functions.extend(unwrap_lines)

    def generate_enum(self, name: str, values: list[str]):
        # We are using string alias strictly now
        wit_name = name.lower().replace("type", "-type")
        self.definitions.append(f"type {wit_name} = string;")
        self.definitions.append("")

        # Adapter for enum
        self.adapter_functions.append(
            f"def convert_{wit_name.replace('-', '_')}(val: str) -> str:"
        )
        self.adapter_functions.append(
            "    # Return string directly as WIT type is string"
        )
        self.adapter_functions.append("    return val")
        self.adapter_functions.append("")

    def scan_class_methods(self, module):
        """Scans classes in the module for methods to expose as flat functions"""
        for name, member in module.members.items():
            if member.is_alias:
                continue
            if not member.is_class:
                continue
            if name.startswith("_") or name.endswith("JSON"):
                continue

            # For each class, scan methods
            class_name = name
            wit_class_prefix = re.sub(r"(?<!^)(?=[A-Z])", "-", class_name).lower()

            for method_name, method in member.members.items():
                if not method.is_function:
                    continue
                if method_name.startswith("_"):
                    continue

                # Check method_name vs property
                # properties are usually attributes in griffe if they are @property?
                # Or function with decorators.
                # member.members[method_name] might be function

                # Filter out pure magic methods, __init__, __post_init__ handled by startswith _

                # Create flat name: class-method
                wit_func_name = f"{wit_class_prefix}-{method_name.replace('_', '-')}"

                self.generate_flat_method(
                    module.path, class_name, method_name, method, wit_func_name
                )

                # Store for TS
                if class_name not in self.discovered_models:
                    self.discovered_models[class_name] = {"fields": [], "methods": []}

                self.discovered_models[class_name]["methods"].append(
                    {
                        "name": method_name,
                        "wit_name": wit_func_name,
                        "params": method.parameters,
                        "ret": method.returns,
                    }
                )

    def generate_flat_method(
        self, module_path, class_name, method_name, method, wit_func_name
    ):
        # Almost same as scan_module_for_functions but 'self' is the first arg
        params = method.parameters

        wit_params = []
        # py_call_args = []

        # We need to handle 'self'. In flat function, self is passed as first arg 'self_obj'
        # typed as the record (WitClass)

        # First param is usually self

        wit_params.append(
            f"self-obj: {re.sub(r'(?<!^)(?=[A-Z])', '-', class_name).lower()}"
        )

        for param in params:
            if param.name in ("self", "cls"):
                continue
            if not param.annotation:
                continue

            py_type = str(param.annotation)
            wit_type, adapter_tmpl = self.map_type(py_type)

            # Special case for type[T]
            if "type[" in py_type or "Type[" in py_type:
                wit_type = "string"

            if param.default is not None and "option<" not in wit_type:
                wit_type = f"option<{wit_type}>"

            wit_param_name = param.name.replace("_", "-")
            wit_params.append(f"{wit_param_name}: {wit_type}")

        # Return type
        ret_type = "string"
        py_ret_type = "str"
        if method.returns:
            py_ret_type = str(method.returns)
            wit_ret, _ = self.map_type(py_ret_type)
            ret_type = wit_ret

            if "list[T]" in py_ret_type or "List[T]" in py_ret_type:
                ret_type = "list<string>"
        else:
            # Void -> Return self (mutation simulation)
            py_ret_type = class_name
            wit_ret, _ = self.map_type(py_ret_type)
            ret_type = wit_ret

        # Export
        wit_params_str = ", ".join(wit_params)
        self.world_exports.append(
            f"export {wit_func_name}: func({wit_params_str}) -> {ret_type};"
        )

        # App method wrapper
        # unwrap self_obj -> call method -> convert result

        # Real Object Construction
        # We assume self_obj is the Wit Record. We need to unwrap it to real Python object.
        uw_self = f"unwrap_{re.sub(r'(?<!^)(?=[A-Z])', '-', class_name).lower().replace('-', '_')}"

        method_args = ["self_obj: Any"] + [
            p.name + ": Any = None" for p in params if p.name not in ("self", "cls")
        ]

        method_body = f"        real_self = {uw_self}(self_obj)\n"
        method_body += "        kwargs = {}\n"

        for p in params:
            if p.name in ("self", "cls"):
                continue

            # Unwrap args logic (copied from scan_module_for_functions)
            val_expr = p.name
            if p.annotation:
                py_type = str(p.annotation).strip()
                clean_type = (
                    py_type.replace(" | None", "").replace("Optional[", "")[:-1]
                    if "Optional[" in py_type
                    else py_type.replace(" | None", "")
                )

                if clean_type in self.known_models:
                    uw_name = (
                        re.sub(r"(?<!^)(?=[A-Z])", "-", clean_type)
                        .lower()
                        .replace("-", "_")
                    )
                    val_expr = f"unwrap_{uw_name}({p.name})"
                elif clean_type.startswith("list["):
                    inner = clean_type[5:-1]
                    if inner in self.known_models:
                        uw_name = (
                            re.sub(r"(?<!^)(?=[A-Z])", "-", inner)
                            .lower()
                            .replace("-", "_")
                        )
                        val_expr = f"[unwrap_{uw_name}(x) for x in {p.name}]"
                elif self.is_json_type(py_type):
                    val_expr = f"json.loads({p.name})"
                elif "type[" in clean_type or "Type[" in clean_type:
                    val_expr = f"resolve_model_class({p.name})"

            method_body += (
                f"        if {p.name} is not None: kwargs['{p.name}'] = {val_expr}\n"
            )

        # Call
        call_expr = f"real_self.{method_name}(**kwargs)"

        # Convert return
        if method.returns:
            _, adapter_tmpl = self.map_type(str(method.returns))
            final_expr = adapter_tmpl.replace("__FIELD__", call_expr)

            # Fix for list[T]
            if "list[T]" in str(method.returns) or "List[T]" in str(method.returns):
                final_expr = f"[json.dumps(dataclasses.asdict(x)) for x in {call_expr}]"

        else:
            # Void -> Return self formatted
            _, adapter_tmpl = self.map_type(class_name)
            conv_expr = adapter_tmpl.replace("__FIELD__", "real_self")
            # Execute call (returns None) then return converted self
            final_expr = f"({call_expr} or {conv_expr})"

        py_func_name = wit_func_name.replace("-", "_")
        method_def = f"    def {py_func_name}(self, {', '.join(method_args)}):\n"
        method_def += method_body
        method_def += f"        return {final_expr}"

        self.app_methods.append(method_def)

    def generate_ts_wrapper(self, output_path: Path):
        """Generate TypeScript wrapper using Jinja2 templates."""
        # Build wasm_imports list
        wasm_imports = []
        for line in self.world_exports:
            match = re.search(r"export ([a-z0-9-]+):", line)
            if match:
                kebab = match.group(1)
                camel = re.sub(r"-([a-z])", lambda g: g.group(1).upper(), kebab)
                wasm_imports.append(f"{camel} as _{camel}")

        # Build global_functions list
        global_functions = self._build_global_functions_data()

        # Build classes list
        classes = self._build_classes_data()

        # Render using template
        content = render_ts_wrapper(wasm_imports, global_functions, classes)

        with open(output_path, "w") as f:
            f.write(content)
        print(f"Generated TS Wrapper: {output_path}")

    def _build_global_functions_data(self) -> list[dict[str, Any]]:
        """Build global functions data for template rendering."""
        global_functions = []
        for func in self.global_functions:
            py_name = func["name"]
            js_name = re.sub(r"_([a-z])", lambda g: g.group(1).upper(), py_name)
            wit_name = func["wit_name"]
            wasm_func_name = re.sub(r"-([a-z])", lambda g: g.group(1).upper(), wit_name)

            args = []
            call_args = []
            resolved_call_args = []
            for p in func["params"]:
                if p.name in ("self", "cls"):
                    continue
                ts_param = re.sub(r"_([a-z])", lambda g: g.group(1).upper(), p.name)
                sig_param = ts_param
                if p.default is not None:
                    sig_param += "?"
                args.append(f"{sig_param}: any")
                call_args.append(ts_param)
                # For file functions, source needs to be resolved
                if ts_param == "source":
                    resolved_call_args.append(f"{ts_param}_resolved")
                else:
                    resolved_call_args.append(ts_param)

            is_file_func = "FromFile" in js_name

            # Determine return wrapper
            ret_py = str(func["ret"]) if func["ret"] else "None"
            return_wrapper = None
            if ret_py != "None":
                clean_ret = (
                    ret_py.replace(" | None", "").replace("Optional[", "")[:-1]
                    if "Optional[" in ret_py
                    else ret_py
                )
                clean_ret = clean_ret.strip("'").strip('"')
                if clean_ret in self.discovered_models:
                    return_wrapper = f"new {clean_ret}(res)"
                elif clean_ret.startswith("list["):
                    inner = clean_ret[5:-1].strip("'").strip('"')
                    if inner in self.discovered_models:
                        return_wrapper = f"res.map((x: any) => new {inner}(x))"

            global_functions.append({
                "js_name": js_name,
                "wasm_func_name": wasm_func_name,
                "args": args,
                "call_args": call_args,
                "resolved_call_args": resolved_call_args,
                "is_file_func": is_file_func,
                "return_wrapper": return_wrapper,
            })
        return global_functions

    def _build_classes_data(self) -> list[dict[str, Any]]:
        """Build classes data for template rendering."""
        classes = []
        for class_name, info in self.discovered_models.items():
            fields = self._build_fields_data(info["fields"])
            methods = self._build_methods_data(class_name, info["methods"])

            classes.append({
                "name": class_name,
                "has_json_getter": class_name in ["Table", "Sheet", "Workbook"],
                "fields": fields,
                "methods": methods,
            })
        return classes

    def _build_fields_data(self, raw_fields: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Build fields data for template rendering."""
        fields = []
        for f in raw_fields:
            fname = f["js_name"]
            pyname = f.get("py_name", fname)
            py_type = f.get("py_type", "")
            wit_type = f["wit_type"]

            # Determine TS type
            ts_type = "any"
            if wit_type == "string":
                ts_type = "string"
            elif "int" in wit_type or "32" in wit_type or "64" in wit_type:
                ts_type = "number"
            elif wit_type == "bool":
                ts_type = "boolean"
            elif wit_type.startswith("list<"):
                ts_type = "any[]"

            # Check if model list
            is_model_list = False
            inner_model = None
            if py_type.startswith("list["):
                match = re.search(r"list\[(.*)\]", py_type)
                if match:
                    inner = match.group(1).strip("'").strip('"')
                    if inner in self.discovered_models:
                        is_model_list = True
                        inner_model = inner

            fields.append({
                "js_name": fname,
                "py_name": pyname,
                "ts_type": ts_type,
                "is_json": f.get("is_json", False),
                "is_model_list": is_model_list,
                "inner_model": inner_model,
            })
        return fields

    def _build_methods_data(
        self, class_name: str, raw_methods: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """Build methods data for template rendering."""
        methods = []
        for m in raw_methods:
            mname = re.sub(r"_([a-z])", lambda g: g.group(1).upper(), m["name"])
            wit_flat_name = m["wit_name"]
            wasm_name = re.sub(r"-([a-z])", lambda g: g.group(1).upper(), wit_flat_name)

            args = []
            call_args = ["dto"]
            model_arg_dtos = []

            for p in m["params"]:
                if p.name in ("self", "cls"):
                    continue
                ts_param = re.sub(r"_([a-z])", lambda g: g.group(1).upper(), p.name)
                sig_param = ts_param
                if p.default is not None:
                    sig_param += "?"
                args.append(f"{sig_param}: any")

                # Check if argument is a known model type
                if p.annotation:
                    clean_type = str(p.annotation).strip()
                    if " | None" in clean_type or "Optional[" in clean_type:
                        clean_type = (
                            clean_type.replace(" | None", "").replace("Optional[", "")[:-1]
                            if "Optional[" in clean_type
                            else clean_type.replace(" | None", "")
                        )
                    clean_type = clean_type.strip("'").strip('"')

                    if clean_type in self.discovered_models:
                        dto_var = f"{ts_param}Dto"
                        model_arg_dtos.append({
                            "var_name": dto_var,
                            "param_name": ts_param,
                            "model_name": clean_type,
                        })
                        call_args.append(dto_var)
                    else:
                        call_args.append(ts_param)
                else:
                    call_args.append(ts_param)

            # Determine return characteristics
            ret_py = str(m["ret"]) if m["ret"] else "None"
            returns_self = False
            returns_model = False
            returns_optional_model = False
            return_model = None
            is_toModels = class_name == "Table" and mname == "toModels"

            if ret_py == "None":
                returns_self = True
            else:
                clean_ret = ret_py
                if clean_ret.startswith("Optional[") and clean_ret.endswith("]"):
                    clean_ret = clean_ret[9:-1]
                if "|" in clean_ret:
                    parts = [p.strip() for p in clean_ret.split("|")]
                    real_types = [p for p in parts if p != "None"]
                    if len(real_types) == 1:
                        clean_ret = real_types[0]
                clean_ret = clean_ret.strip("'").strip('"')

                if clean_ret in self.discovered_models:
                    if clean_ret == class_name:
                        returns_self = True
                    else:
                        is_optional = "None" in ret_py or "Optional" in ret_py
                        if is_optional:
                            returns_optional_model = True
                        else:
                            returns_model = True
                        return_model = clean_ret

            methods.append({
                "name": mname,
                "args": args,
                "call_args": call_args,
                "wasm_name": wasm_name,
                "model_arg_dtos": model_arg_dtos,
                "returns_self": returns_self,
                "returns_model": returns_model,
                "returns_optional_model": returns_optional_model,
                "return_model": return_model,
                "is_toModels": is_toModels,
            })
        return methods


    def generate_wit_file(self, output_path: Path):
        wit_content = "package example:spreadsheet;\n\n"
        wit_content += "interface types {\n"
        for line in self.definitions:
            wit_content += f"    {line}\n"
        wit_content += "}\n\n"

        wit_content += "world spreadsheet-parser {\n"

        # Derive used types from definitions
        record_names = []
        for line in self.definitions:
            if line.startswith("record "):
                record_names.append(line.split(" ")[1])
            if line.startswith("type "):
                parts = line.split(" ")
                if len(parts) > 1 and "=" in parts:
                    record_names.append(parts[1])

        # Use distinct
        used = sorted(list(set(record_names)))
        if used:
            wit_content += f"    use types.{{{', '.join(used)}}};\n"

        for line in self.world_exports:
            wit_content += f"    {line}\n"
        wit_content += "}\n"

        with open(output_path, "w") as f:
            f.write(wit_content)
        print(f"Generated WIT: {output_path}")

    def generate_adapter_file(self, output_path: Path):
        adapter_content = "import json\n"
        adapter_content += "from dataclasses import dataclass, asdict\n"
        adapter_content += "from typing import Any\n"
        adapter_content += "import md_spreadsheet_parser.models as models\n"
        adapter_content += "import md_spreadsheet_parser.schemas as schemas\n\n"

        # Helper for resolving classes
        adapter_content += "def resolve_model_class(name: str) -> Any:\n"
        adapter_content += "    cls = None\n"
        adapter_content += "    if hasattr(models, name):\n"
        adapter_content += "        cls = getattr(models, name)\n"
        adapter_content += "    elif hasattr(schemas, name):\n"
        adapter_content += "        cls = getattr(schemas, name)\n"
        adapter_content += "    if cls:\n"
        adapter_content += "        return cls\n"
        adapter_content += (
            "    raise ValueError(f'Unknown model/schema class: {name}')\n\n"
        )

        for line in self.adapter_functions:
            adapter_content += f"{line}\n"

        with open(output_path, "w") as f:
            f.write(adapter_content)
        print(f"Generated Adapter: {output_path}")

    def generate_app_file(self, output_path: Path):
        app_content = "import md_spreadsheet_parser.parsing\n"
        app_content += "import md_spreadsheet_parser.generator\n"
        app_content += "import md_spreadsheet_parser.loader\n"
        app_content += "import dataclasses\n"
        app_content += "import json\n"
        app_content += "from typing import Any\n"
        app_content += "from generated_adapter import *\n\n"
        app_content += "class WitWorld:\n"
        for method in self.app_methods:
            app_content += f"{method}\n"

        with open(output_path, "w") as f:
            f.write(app_content)
        print(f"Generated App: {output_path}")


def main():
    # packages/npm/scripts/../../src
    base_dir = Path(__file__).parent.parent.parent.parent
    src_dir = base_dir / "src"

    # Load Griffe for multiple modules
    search_paths = [str(src_dir)]
    pkg_models = griffe.load("md_spreadsheet_parser.models", search_paths=search_paths)
    pkg_schemas = griffe.load(
        "md_spreadsheet_parser.schemas", search_paths=search_paths
    )
    pkg_parsing = griffe.load(
        "md_spreadsheet_parser.parsing", search_paths=search_paths
    )
    pkg_generator = griffe.load(
        "md_spreadsheet_parser.generator", search_paths=search_paths
    )
    pkg_loader = griffe.load("md_spreadsheet_parser.loader", search_paths=search_paths)
    # pkg_excel = griffe.load(
    #    "md_spreadsheet_parser.excel", search_paths=search_paths
    # )
    # Excel might require openpyxl which might not be installable in componentize-py env or irrelevant for pure markdown?
    # Actually componentize-py includes dependencies if they are pure python.
    # openpyxl is pure python. But for now let's focus on Markdown Parse/Generate cycle which is core.

    gen = WitGenerator()
    gen.register_models([pkg_models, pkg_schemas])

    # 1. Generate Enums
    gen.generate_enum("AlignmentType", ["left", "center", "right", "default"])

    # 3. Generate Functions from parsing module
    gen.scan_module_for_functions(pkg_parsing)
    gen.scan_module_for_functions(pkg_generator)
    gen.scan_module_for_functions(pkg_loader)

    # 3.5 Scan Class Methods (Flattening)
    gen.scan_class_methods(pkg_models)

    # 2. Generate Records from specific modules
    gen.scan_module_for_records(pkg_models)
    gen.scan_module_for_records(pkg_schemas)

    # ... generate WIT and Adapter ...

    # Generate TS Wrapper
    ts_path = Path(__file__).parent.parent / "src" / "index.ts"
    gen.generate_ts_wrapper(ts_path)
    # We ignore errors in schemas for now or specific ones?
    # schemas contains ParsingSchema, etc.

    # 4. Write WIT
    wit_path = Path(__file__).parent.parent / "wit" / "generated.wit"
    gen.generate_wit_file(wit_path)

    # 5. Write Adapter
    adapter_path = Path(__file__).parent.parent / "src" / "generated_adapter.py"
    gen.generate_adapter_file(adapter_path)

    # 6. Generate app.py
    app_path = Path(__file__).parent.parent / "src" / "app.py"
    gen.generate_app_file(app_path)


if __name__ == "__main__":
    main()
