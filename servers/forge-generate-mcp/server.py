"""forge-generate-mcp — Generate code and artifacts."""

import json
import re
from typing import Any

import mcp.types as types
from mcp.server import Server

app = Server("forge-generate-mcp")


def _extract_identifiers(spec: str) -> tuple[list[str], list[str]]:
    """Extract potential function and class names from a spec."""
    # Class signals: words after "class", capitalized, or ending in er/or/ion/Manager/Service
    class_signals = {
        "class",
        "service",
        "manager",
        "handler",
        "processor",
        "controller",
        "model",
    }
    func_signals = {
        "function",
        "method",
        "def",
        "calculate",
        "compute",
        "process",
        "get",
        "set",
        "create",
        "update",
        "delete",
        "fetch",
        "parse",
        "validate",
        "transform",
    }

    classes = []
    functions = []
    words_lower = spec.lower()

    for signal in class_signals:
        if signal in words_lower:
            # Use capitalized signal as class name
            classes.append(signal.capitalize() + "Base")

    for signal in func_signals:
        if signal in words_lower:
            functions.append(signal + "_item")

    # Fallback
    if not classes:
        classes = ["GeneratedClass"]
    if not functions:
        functions = ["process_data", "run"]

    return classes[:3], functions[:5]


def _generate_code_logic(spec: str, language: str, style: str) -> dict:
    """Generate a code skeleton from spec."""
    classes, functions = _extract_identifiers(spec)
    lang = language.lower()

    lines = []

    if lang == "python":
        lines.append(f'"""Generated from spec: {spec[:80]}"""')
        lines.append("from typing import Any")
        lines.append("")

        if style == "class-based":
            for cls in classes[:2]:
                lines.append(f"class {cls}:")
                lines.append('    """Auto-generated class."""')
                lines.append("")
                lines.append("    def __init__(self) -> None:")
                lines.append("        pass")
                lines.append("")
                for fn in functions[:2]:
                    lines.append(f"    def {fn}(self, data: Any) -> Any:")
                    lines.append('        """Process data."""')
                    lines.append("        raise NotImplementedError")
                    lines.append("")
        else:
            for fn in functions[:3]:
                lines.append(f"def {fn}(data: Any) -> Any:")
                lines.append(f'    """Generated function: {fn}."""')
                lines.append("    raise NotImplementedError")
                lines.append("")

    elif lang in ("javascript", "typescript"):
        type_hint = ": any" if lang == "typescript" else ""
        lines.append(f"// Generated from spec: {spec[:80]}")
        lines.append("")
        if style == "class-based":
            for cls in classes[:2]:
                lines.append(f"class {cls} {{")
                for fn in functions[:2]:
                    lines.append(f"  {fn}(data{type_hint}){type_hint} {{")
                    lines.append("    throw new Error('Not implemented');")
                    lines.append("  }")
                lines.append("}")
                lines.append("")
        else:
            for fn in functions[:3]:
                lines.append(f"function {fn}(data{type_hint}){type_hint} {{")
                lines.append("  throw new Error('Not implemented');")
                lines.append("}")
                lines.append("")

    elif lang == "go":
        lines.append(f"// Generated from spec: {spec[:80]}")
        lines.append("package main")
        lines.append("")
        for fn in functions[:3]:
            fn_go = "".join(w.capitalize() for w in fn.split("_"))
            lines.append(f"func {fn_go}(data interface{{}}) interface{{}} {{")
            lines.append('\tpanic("not implemented")')
            lines.append("}")
            lines.append("")

    elif lang == "rust":
        lines.append(f"// Generated from spec: {spec[:80]}")
        lines.append("")
        for fn in functions[:3]:
            lines.append(f"fn {fn}(data: &str) -> String {{")
            lines.append(f'    todo!("implement {fn}")')
            lines.append("}")
            lines.append("")
    else:
        # Generic
        for fn in functions[:3]:
            lines.append(f"# {fn}(data) -> result")
            lines.append(f"# TODO: implement {fn}")
            lines.append("")

    code = "\n".join(lines)
    return {
        "spec": spec[:200],
        "language": language,
        "style": style,
        "code": code,
        "classes_detected": classes,
        "functions_detected": functions,
    }


def _generate_schema_logic(data_description: str, format: str) -> dict:
    """Generate a schema from a data description."""
    # Parse field hints from description
    words = data_description.lower().split()
    fields: dict[str, str] = {}

    # Type inference heuristics
    type_keywords = {
        "id": "string",
        "uuid": "string",
        "name": "string",
        "title": "string",
        "description": "string",
        "email": "string",
        "url": "string",
        "count": "integer",
        "number": "integer",
        "age": "integer",
        "quantity": "integer",
        "price": "number",
        "amount": "number",
        "score": "number",
        "rate": "number",
        "active": "boolean",
        "enabled": "boolean",
        "flag": "boolean",
        "is_": "boolean",
        "date": "string",
        "timestamp": "string",
        "created": "string",
        "updated": "string",
        "list": "array",
        "items": "array",
        "tags": "array",
        "children": "array",
    }

    for word in words:
        word_clean = re.sub(r"[^a-z_]", "", word)
        if not word_clean:
            continue
        for kw, typ in type_keywords.items():
            if kw in word_clean:
                fields[word_clean] = typ
                break
        else:
            if len(word_clean) > 2:
                fields[word_clean] = "string"

    # Limit to reasonable number
    fields = dict(list(fields.items())[:8])

    schema_lines = []
    fmt = format.lower()

    if fmt == "json-schema":
        schema_obj = {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "type": "object",
            "properties": {name: {"type": typ} for name, typ in fields.items()},
            "required": list(fields.keys()),
        }
        schema_str = json.dumps(schema_obj, indent=2)

    elif fmt == "pydantic":
        schema_lines.append("from pydantic import BaseModel")
        schema_lines.append("from typing import Optional, List")
        schema_lines.append("")

        type_map = {
            "string": "str",
            "integer": "int",
            "number": "float",
            "boolean": "bool",
            "array": "List[str]",
        }
        schema_lines.append("class GeneratedModel(BaseModel):")
        if fields:
            for name, typ in fields.items():
                py_type = type_map.get(typ, "str")
                schema_lines.append(f"    {name}: {py_type}")
        else:
            schema_lines.append("    pass")
        schema_str = "\n".join(schema_lines)

    elif fmt == "typescript":
        type_map = {
            "string": "string",
            "integer": "number",
            "number": "number",
            "boolean": "boolean",
            "array": "string[]",
        }
        schema_lines.append("interface GeneratedSchema {")
        for name, typ in fields.items():
            ts_type = type_map.get(typ, "string")
            schema_lines.append(f"  {name}: {ts_type};")
        schema_lines.append("}")
        schema_str = "\n".join(schema_lines)

    else:
        schema_str = json.dumps({"type": "object", "fields": fields}, indent=2)

    return {
        "data_description": data_description[:200],
        "format": format,
        "schema": schema_str,
        "fields_detected": fields,
    }


def _generate_tests_logic(code: str, framework: str, count: int) -> dict:
    """Generate test stubs from code."""
    # Extract function names from code
    if "def " in code:
        pattern = r"def\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\("
    elif "function " in code or "=>" in code:
        pattern = r"(?:function\s+([a-zA-Z_][a-zA-Z0-9_]*)|const\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*=)"
    else:
        pattern = r"(?:def|fn|func)\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*[\(\{]"

    matches = re.findall(pattern, code)
    # Flatten tuples from alternation groups
    function_names = []
    for m in matches:
        if isinstance(m, tuple):
            function_names.extend([n for n in m if n])
        else:
            function_names.append(m)

    # Remove test functions and private functions from stubs
    function_names = [
        f
        for f in function_names
        if not f.startswith("test_") and not f.startswith("__")
    ][:count]

    if not function_names:
        function_names = ["generated_function"]

    fw = framework.lower()
    test_lines = []

    if fw == "pytest":
        test_lines.append('"""Auto-generated tests."""')
        test_lines.append("import pytest")
        test_lines.append("")
        for fn in function_names:
            test_lines.append(f"def test_{fn}():")
            test_lines.append(f'    """Test {fn}."""')
            test_lines.append(f"    # TODO: implement test for {fn}")
            test_lines.append(f"    result = {fn}()")
            test_lines.append("    assert result is not None")
            test_lines.append("")

    elif fw == "jest":
        test_lines.append("// Auto-generated tests")
        for fn in function_names:
            test_lines.append(f"test('{fn} works correctly', () => {{")
            test_lines.append(f"  // TODO: implement test for {fn}")
            test_lines.append(f"  const result = {fn}();")
            test_lines.append("  expect(result).toBeDefined();")
            test_lines.append("});")
            test_lines.append("")

    elif fw == "unittest":
        test_lines.append('"""Auto-generated tests."""')
        test_lines.append("import unittest")
        test_lines.append("")
        test_lines.append("class GeneratedTests(unittest.TestCase):")
        test_lines.append("")
        for fn in function_names:
            test_lines.append(f"    def test_{fn}(self):")
            test_lines.append(f'        """Test {fn}."""')
            test_lines.append(f"        # TODO: implement test for {fn}")
            test_lines.append("        self.fail('Not implemented')")
            test_lines.append("")
        test_lines.append("")
        test_lines.append("if __name__ == '__main__':")
        test_lines.append("    unittest.main()")

    else:
        for fn in function_names:
            test_lines.append(f"# test_{fn}: verify {fn} returns expected result")

    test_file = "\n".join(test_lines)
    return {
        "framework": framework,
        "functions_found": function_names,
        "test_count": len(function_names),
        "test_file": test_file,
    }


@app.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="generate_code",
            description="Generate a code skeleton from a spec description in the specified language",
            inputSchema={
                "type": "object",
                "properties": {
                    "spec": {
                        "type": "string",
                        "description": "Natural language description of what to generate",
                    },
                    "language": {
                        "type": "string",
                        "description": "Target language: python, javascript, typescript, go, rust",
                    },
                    "style": {
                        "type": "string",
                        "description": "Code style: functional, class-based, minimal",
                    },
                },
                "required": ["spec", "language", "style"],
            },
        ),
        types.Tool(
            name="generate_schema",
            description="Generate a data schema from a description in json-schema, pydantic, or typescript format",
            inputSchema={
                "type": "object",
                "properties": {
                    "data_description": {
                        "type": "string",
                        "description": "Description of the data structure",
                    },
                    "format": {
                        "type": "string",
                        "description": "Schema format: json-schema, pydantic, typescript",
                    },
                },
                "required": ["data_description", "format"],
            },
        ),
        types.Tool(
            name="generate_tests",
            description="Generate test stubs from code by parsing function names",
            inputSchema={
                "type": "object",
                "properties": {
                    "code": {
                        "type": "string",
                        "description": "Source code to generate tests for",
                    },
                    "framework": {
                        "type": "string",
                        "description": "Test framework: pytest, jest, unittest",
                    },
                    "count": {
                        "type": "integer",
                        "description": "Maximum number of test stubs to generate",
                    },
                },
                "required": ["code", "framework", "count"],
            },
        ),
    ]


@app.call_tool()
async def handle_call_tool(
    name: str, arguments: dict[str, Any]
) -> list[types.TextContent]:
    if name == "generate_code":
        result = _generate_code_logic(
            arguments["spec"], arguments["language"], arguments["style"]
        )
        return [types.TextContent(type="text", text=json.dumps(result))]
    elif name == "generate_schema":
        result = _generate_schema_logic(
            arguments["data_description"], arguments["format"]
        )
        return [types.TextContent(type="text", text=json.dumps(result))]
    elif name == "generate_tests":
        result = _generate_tests_logic(
            arguments["code"], arguments["framework"], arguments["count"]
        )
        return [types.TextContent(type="text", text=json.dumps(result))]
    raise ValueError(f"Unknown tool: {name}")
