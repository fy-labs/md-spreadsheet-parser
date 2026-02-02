import re
from pathlib import Path
from typing import Any

import griffe


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
        # Imports mapping (kebab-case export -> camelCase import)
        # We import WASM functions with an underscore prefix to use them internally
        wasm_imports = []
        for line in self.world_exports:
            match = re.search(r"export ([a-z0-9-]+):", line)
            if match:
                kebab = match.group(1)
                camel = re.sub(r"-([a-z])", lambda g: g.group(1).upper(), kebab)
                wasm_imports.append(f"{camel} as _{camel}")

        content = f"import {{ {', '.join(wasm_imports)} }} from '../dist/parser.js';\n"
        content += "import { clientSideToModels } from './client-adapters.js';\n\n"
        
        # Browser-compatible environment detection and lazy initialization
        content += "// Environment detection\n"
        content += "// @ts-ignore - process may not be defined in browser\n"
        content += "const isNode = typeof process !== 'undefined'\n"
        content += "    && typeof process.versions !== 'undefined'\n"
        content += "    && typeof process.versions.node !== 'undefined';\n\n"
        
        content += "// Lazily loaded Node.js modules (only in Node.js environment)\n"
        content += "let _pathModule: any = null;\n"
        content += "let _nodeInitialized = false;\n\n"
        
        content += "/**\n"
        content += " * Ensures Node.js environment is initialized for file system operations.\n"
        content += " * Throws an error in browser environments.\n"
        content += " */\n"
        content += "async function ensureNodeEnvironment(): Promise<void> {\n"
        content += "    if (!isNode) {\n"
        content += "        throw new Error(\n"
        content += "            'File system operations (parseTableFromFile, parseWorkbookFromFile, scanTablesFromFile) ' +\n"
        content += "            'are not supported in browser environments. ' +\n"
        content += "            'Use parseTable(), parseWorkbook(), or scanTables() with string content instead.'\n"
        content += "        );\n"
        content += "    }\n"
        content += "    if (_nodeInitialized) return;\n\n"
        content += "    // Dynamic imports for Node.js only\n"
        content += "    const [pathModule, processModule, fsShim] = await Promise.all([\n"
        content += "        import('node:path'),\n"
        content += "        import('node:process'),\n"
        content += "        import('@bytecodealliance/preview2-shim/filesystem')\n"
        content += "    ]);\n\n"
        content += "    _pathModule = pathModule.default || pathModule;\n"
        content += "    const proc = processModule.default || processModule;\n"
        content += "    const root = _pathModule.parse(proc.cwd()).root;\n"
        content += "    // @ts-ignore - _addPreopen is an internal function\n"
        content += "    (fsShim as any)._addPreopen('/', root);\n"
        content += "    _nodeInitialized = true;\n"
        content += "}\n\n"
        
        content += "function resolveToVirtualPath(p: string): string {\n"
        content += "    if (!_pathModule) {\n"
        content += "        throw new Error('Node.js modules not initialized. Call ensureNodeEnvironment() first.');\n"
        content += "    }\n"
        content += "    return _pathModule.resolve(p);\n"
        content += "}\n\n"

        # Generate Wrapper Functions
        for func in self.global_functions:
            py_name = func["name"]
            # CamelCase JS name
            js_name = re.sub(r"_([a-z])", lambda g: g.group(1).upper(), py_name)

            # Find the internal WASM function name
            wit_name = func["wit_name"]
            wasm_func_name = re.sub(r"-([a-z])", lambda g: g.group(1).upper(), wit_name)

            # Args
            args = []
            call_args = []
            for p in func["params"]:
                if p.name in ("self", "cls"):
                    continue
                ts_param = re.sub(r"_([a-z])", lambda g: g.group(1).upper(), p.name)
                sig_param = ts_param
                if p.default is not None:
                    sig_param += "?"
                args.append(f"{sig_param}: any")  # TODO types
                call_args.append(ts_param)

            # Check if this is a file-based function (requires async for browser compatibility)
            is_file_func = "FromFile" in js_name
            
            if is_file_func:
                # Async function signature for file operations
                content += f"export async function {js_name}({', '.join(args)}): Promise<any> {{\n"
                content += "    await ensureNodeEnvironment();\n"
                for idx, arg_name in enumerate(call_args):
                    if arg_name == "source":
                        content += f"    const {arg_name}_resolved = resolveToVirtualPath({arg_name});\n"
                        call_args[idx] = f"{arg_name}_resolved"
            else:
                # Regular sync function
                content += f"export function {js_name}({', '.join(args)}): any {{\n"

            content += f"    const res = _{wasm_func_name}({', '.join(call_args)});\n"

            # Return wrapping
            ret_py = str(func["ret"]) if func["ret"] else "None"
            if ret_py != "None":
                clean_ret = (
                    ret_py.replace(" | None", "").replace("Optional[", "")[:-1]
                    if "Optional[" in ret_py
                    else ret_py
                )
                clean_ret = clean_ret.strip("'").strip('"')

                # list[Table] -> Table[] wrapping logic?
                # For now handling direct return of Models
                if clean_ret in self.discovered_models:
                    content += f"    return new {clean_ret}(res);\n"
                elif clean_ret.startswith("list["):
                    inner = clean_ret[5:-1].strip("'").strip('"')
                    if inner in self.discovered_models:
                        content += f"    return res.map((x: any) => new {inner}(x));\n"
                    else:
                        content += "    return res;\n"
                else:
                    content += "    return res;\n"
            else:
                content += "    return res;\n"

            content += "}\n\n"

        # Generate TS Classes
        for class_name, info in self.discovered_models.items():
            content += f"\nexport class {class_name} {{\n"

            # Fields
            for f in info["fields"]:
                fname = f["js_name"]
                # Type mapping needed for TS properties?
                # Simplify: explicit typing or 'any' for now, or infer from WIT type
                # list<string> -> string[]
                t = f["wit_type"]
                ts_type = "any"
                if t == "string":
                    ts_type = "string"
                elif "int" in t or "32" in t or "64" in t:
                    ts_type = "number"
                elif t == "bool":
                    ts_type = "boolean"
                elif t.startswith("list<"):
                    ts_type = "any[]"  # TODO recursive

                content += f"    {fname}: {ts_type} | undefined;\n"

            # Constructor
            content += "\n    constructor(data?: Partial<" + class_name + "> & Record<string, any>) {\n"
            content += "        if (data) {\n"
            for f in info["fields"]:
                fname = f["js_name"]
                pyname = f.get("py_name", fname)  # Use py_name for snake_case fallback
                py_type = f.get("py_type", "")
                
                if f.get("is_json"):
                    # Robust handling: parse string if string, else use as is
                    # Fallback to snake_case field name for WASM bridge compatibility
                    content += f"            {{\n"
                    content += f"                const val = data.{fname} ?? data.{pyname};\n"
                    content += f"                this.{fname} = (typeof val === 'string') ? JSON.parse(val) : val;\n"
                    content += f"            }}\n"
                elif py_type.startswith("list["):
                    # Check if it's a list of models that need wrapping
                    match = re.search(r"list\[(.*)\]", py_type)
                    if match:
                        inner = match.group(1).strip("'").strip('"')
                        if inner in self.discovered_models:
                            # Wrap each item in the appropriate class
                            # Fallback to snake_case field name
                            content += f"            this.{fname} = ((data.{fname} ?? data.{pyname}) || []).map((x: any) => x instanceof {inner} ? x : new {inner}(x));\n"
                        else:
                            content += f"            this.{fname} = data.{fname} ?? data.{pyname};\n"
                    else:
                        content += f"            this.{fname} = data.{fname} ?? data.{pyname};\n"
                else:
                    # Fallback to snake_case field name for WASM bridge compatibility
                    content += f"            this.{fname} = data.{fname} ?? data.{pyname};\n"
            content += "        }\n"
            content += "    }\n"

            # toDTO Method
            content += "\n    toDTO(): any {\n"
            content += "        const dto = { ...this } as any;\n"
            for f in info["fields"]:
                fname = f["js_name"]
                if f.get("is_json"):
                    content += f"        if (dto.{fname}) dto.{fname} = JSON.stringify(dto.{fname});\n"
                
                # Check for list[Model] recursion
                py_type = f.get("py_type", "")
                if py_type.startswith("list["):
                    match = re.search(r"list\[(.*)\]", py_type)
                    if match:
                        inner = match.group(1).strip("'").strip('"')
                        if inner in self.discovered_models:
                            content += f"        if (dto.{fname}) dto.{fname} = dto.{fname}.map((x: any) => x.toDTO ? x.toDTO() : x);\n"

            content += "        return dto;\n"
            content += "    }\n"

            # Generate json getter for Table, Sheet, Workbook
            # This mirrors Python's .json property
            if class_name in ["Table", "Sheet", "Workbook"]:
                content += "\n    /**\n"
                content += "     * Returns a JSON-compatible plain object representation.\n"
                content += "     * Mirrors Python's .json property.\n"
                content += "     */\n"
                content += "    get json(): any {\n"
                
                if class_name == "Table":
                    content += "        return {\n"
                    content += "            name: this.name,\n"
                    content += "            description: this.description,\n"
                    content += "            headers: this.headers,\n"
                    content += "            rows: this.rows,\n"
                    content += "            metadata: this.metadata ?? {},\n"
                    content += "            startLine: this.startLine,\n"
                    content += "            endLine: this.endLine,\n"
                    content += "            alignments: this.alignments,\n"
                    content += "        };\n"
                elif class_name == "Sheet":
                    content += "        return {\n"
                    content += "            name: this.name,\n"
                    content += "            tables: (this.tables || []).map((t: any) => t.json ? t.json : t),\n"
                    content += "            sheetType: this.sheetType,\n"
                    content += "            content: this.content,\n"
                    content += "            metadata: this.metadata ?? {},\n"
                    content += "        };\n"
                elif class_name == "Workbook":
                    content += "        return {\n"
                    content += "            sheets: (this.sheets || []).map((s: any) => s.json ? s.json : s),\n"
                    content += "            metadata: this.metadata ?? {},\n"
                    content += "            rootContent: this.rootContent,\n"
                    content += "        };\n"
                
                content += "    }\n"

            # Methods
            for m in info["methods"]:
                mname = re.sub(r"_([a-z])", lambda g: g.group(1).upper(), m["name"])
                wit_flat_name = m["wit_name"]
                # camelCase import name
                import_name = re.sub(
                    r"-([a-z])", lambda g: g.group(1).upper(), wit_flat_name
                )

                # Params
                # self is implicit in TS
                args = []
                call_args = ["this"]  # pass self object to flat function
                model_arg_conversions = []  # Track model arguments that need toDTO

                for p in m["params"]:
                    if p.name in ("self", "cls"):
                        continue

                    ts_param = re.sub(r"_([a-z])", lambda g: g.group(1).upper(), p.name)

                    # Simple TS signature
                    sig_param = ts_param
                    if p.default is not None:
                        sig_param += "?"

                    args.append(f"{sig_param}: any")  # TODO specific types
                    
                    # Check if argument is a known model type (Table, Sheet, etc.)
                    if p.annotation:
                        clean_type = str(p.annotation).strip()
                        # Remove Optional wrapper
                        if " | None" in clean_type or "Optional[" in clean_type:
                            clean_type = (
                                clean_type.replace(" | None", "").replace("Optional[", "")[:-1]
                                if "Optional[" in clean_type
                                else clean_type.replace(" | None", "")
                            )
                        clean_type = clean_type.strip("'").strip('"')
                        
                        if clean_type in self.discovered_models:
                            # This is a model argument - add conversion
                            dto_var = f"{ts_param}Dto"
                            model_arg_conversions.append(
                                f"        const {dto_var} = {ts_param} instanceof {clean_type} ? {ts_param}.toDTO() : {ts_param};"
                            )
                            call_args.append(dto_var)
                        else:
                            call_args.append(ts_param)
                    else:
                        call_args.append(ts_param)

                content += f"\n    {mname}({', '.join(args)}): any {{\n"

                # Conversion of results if
                # Fix type error: cast this to any
                call_args[0] = "(this as any)"

                # Create flattened DTO for calling WASM if we are passing 'this' (param named self_obj)
                # Use toDTO to handle deep conversion
                content += "        const dto = this.toDTO();\n"
                call_args[0] = "dto"
                
                # Add model argument conversions
                for conversion in model_arg_conversions:
                    content += f"{conversion}\n"

                if class_name == "Table" and mname == "toModels":
                    content += "        const clientRes = clientSideToModels(this.headers, this.rows || [], schemaCls);\n"
                    content += "        if (clientRes) {\n"
                    content += "            return clientRes;\n"
                    content += "        }\n"
                    content += (
                        f"        const res = _{import_name}({', '.join(call_args)});\n"
                    )
                    content += "        return res.map((x: string) => JSON.parse(x));\n"
                    content += "    }\n"
                    continue
                else:
                    content += (
                        f"        const res = _{import_name}({', '.join(call_args)});\n"
                    )

                # Check return type for wrapping
                ret_py = str(m["ret"]) if m["ret"] else "None"

                if ret_py == "None":
                    # Mutation simulation: update this with result
                    # Use constructor to properly hydrate (parse JSON metadata, wrap nested models)
                    content += f"        const hydrated = new {class_name}(res);\n"
                    content += "        Object.assign(this, hydrated);\n"
                    content += "        return this;\n"
                else:
                    # More robust cleaning
                    clean_ret = ret_py
                    
                    # Handle Optional[T] wrapper
                    if clean_ret.startswith("Optional[") and clean_ret.endswith("]"):
                        clean_ret = clean_ret[9:-1]

                    # Handle Union (A | B) logic - usually it's T | None
                    if "|" in clean_ret:
                        parts = [p.strip() for p in clean_ret.split("|")]
                        # specific filter for None
                        real_types = [p for p in parts if p != "None"]
                        if len(real_types) == 1:
                            clean_ret = real_types[0]
                    
                    clean_ret = clean_ret.strip("'").strip('"')  # 'Table' -> Table

                    if clean_ret in self.discovered_models:
                        if clean_ret == class_name:
                            # Use constructor to properly hydrate (parse JSON metadata, wrap nested models)
                            content += f"        const hydrated = new {class_name}(res);\n"
                            content += "        Object.assign(this, hydrated);\n"
                            content += "        return this;\n"
                        else:
                            is_optional = "None" in ret_py or "Optional" in ret_py
                            if is_optional:
                                content += f"        return res ? new {clean_ret}(res) : undefined;\n"
                            else:
                                content += f"        return new {clean_ret}(res);\n"
                    else:
                        content += "        return res;\n"

                content += "    }\n"

            content += "}\n"

        with open(output_path, "w") as f:
            f.write(content)
        print(f"Generated TS Wrapper: {output_path}")

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
