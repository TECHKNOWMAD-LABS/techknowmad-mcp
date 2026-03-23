"""Extended tests for forge-generate-mcp — targeting 90%+ coverage."""
import json
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../.."))

from servers.forge_generate_mcp.server import (
    _extract_identifiers,
    _generate_code_logic,
    _generate_schema_logic,
    _generate_tests_logic,
    handle_call_tool,
)


class TestExtractIdentifiers:
    def test_class_signal_detected(self):
        classes, _ = _extract_identifiers("build a service manager")
        assert len(classes) > 0

    def test_function_signal_detected(self):
        _, functions = _extract_identifiers("calculate the total and validate input")
        assert len(functions) > 0

    def test_no_signals_returns_fallback(self):
        classes, functions = _extract_identifiers("xyz zyx abc")
        assert classes == ["GeneratedClass"]
        assert len(functions) > 0

    def test_multiple_class_signals(self):
        classes, _ = _extract_identifiers("build a service and a handler and a manager")
        assert len(classes) <= 3


class TestGenerateCodeLogic:
    def test_python_functional(self):
        result = _generate_code_logic("calculate and validate data", "python", "functional")
        assert result["language"] == "python"
        assert "def " in result["code"]
        assert result["style"] == "functional"

    def test_python_class_based(self):
        result = _generate_code_logic("service manager for processing data", "python", "class-based")
        assert "class " in result["code"]

    def test_javascript_functional(self):
        result = _generate_code_logic("process and get data", "javascript", "functional")
        assert "function " in result["code"]

    def test_javascript_class_based(self):
        result = _generate_code_logic("service handler", "javascript", "class-based")
        assert "class " in result["code"]

    def test_typescript_functional(self):
        result = _generate_code_logic("get data", "typescript", "functional")
        assert ": any" in result["code"]

    def test_typescript_class_based(self):
        result = _generate_code_logic("service handler", "typescript", "class-based")
        assert "class " in result["code"]

    def test_go_language(self):
        result = _generate_code_logic("process item", "go", "functional")
        assert result["language"] == "go"
        assert "package main" in result["code"]

    def test_rust_language(self):
        result = _generate_code_logic("process item", "rust", "functional")
        assert result["language"] == "rust"
        assert "fn " in result["code"]

    def test_unknown_language_generic(self):
        result = _generate_code_logic("do something", "cobol", "functional")
        assert result["language"] == "cobol"
        assert "TODO" in result["code"]

    def test_long_spec_truncated(self):
        long_spec = "x" * 500
        result = _generate_code_logic(long_spec, "python", "functional")
        assert len(result["spec"]) <= 200

    def test_result_has_all_keys(self):
        result = _generate_code_logic("test spec", "python", "functional")
        assert "code" in result
        assert "classes_detected" in result
        assert "functions_detected" in result


class TestGenerateSchemaLogic:
    def test_json_schema_format(self):
        result = _generate_schema_logic("user with name email and age", "json-schema")
        schema = json.loads(result["schema"])
        assert schema["type"] == "object"
        assert "properties" in schema

    def test_pydantic_format(self):
        result = _generate_schema_logic("product with name price and count", "pydantic")
        assert "BaseModel" in result["schema"]
        assert "class GeneratedModel" in result["schema"]

    def test_typescript_format(self):
        result = _generate_schema_logic("entity with id name and active flag", "typescript")
        assert "interface GeneratedSchema" in result["schema"]

    def test_unknown_format_fallback(self):
        result = _generate_schema_logic("thing with id", "graphql")
        assert "type" in result["schema"]

    def test_fields_detected(self):
        result = _generate_schema_logic("user with name email age and active", "json-schema")
        assert len(result["fields_detected"]) > 0

    def test_type_inference_integer(self):
        result = _generate_schema_logic("item with count quantity and age", "json-schema")
        schema = json.loads(result["schema"])
        props = schema["properties"]
        # At least one integer field detected
        assert any(v["type"] == "integer" for v in props.values())

    def test_type_inference_boolean(self):
        result = _generate_schema_logic("user with active enabled flag", "json-schema")
        schema = json.loads(result["schema"])
        props = schema["properties"]
        assert any(v["type"] == "boolean" for v in props.values())

    def test_long_description_truncated(self):
        long_desc = "x " * 300
        result = _generate_schema_logic(long_desc, "json-schema")
        assert len(result["data_description"]) <= 200

    def test_pydantic_int_type_mapping(self):
        result = _generate_schema_logic("record with count and age", "pydantic")
        assert "int" in result["schema"]

    def test_pydantic_float_type_mapping(self):
        result = _generate_schema_logic("product with price and amount", "pydantic")
        assert "float" in result["schema"]

    def test_typescript_number_type(self):
        result = _generate_schema_logic("item with price count", "typescript")
        assert "number" in result["schema"]


class TestGenerateTestsLogic:
    def test_pytest_framework(self):
        code = "def calculate_total(items): pass\ndef validate_input(data): pass"
        result = _generate_tests_logic(code, "pytest", 5)
        assert "def test_calculate_total" in result["test_file"]
        assert "import pytest" in result["test_file"]

    def test_jest_framework(self):
        code = "function processData(input) { return input; }"
        result = _generate_tests_logic(code, "jest", 5)
        assert "test(" in result["test_file"]
        assert "expect(" in result["test_file"]

    def test_unittest_framework(self):
        code = "def my_function(x): return x"
        result = _generate_tests_logic(code, "unittest", 5)
        assert "unittest.TestCase" in result["test_file"]
        assert "def test_my_function" in result["test_file"]

    def test_unknown_framework_fallback(self):
        code = "def my_function(x): return x"
        result = _generate_tests_logic(code, "mocha", 5)
        assert "test_file" in result

    def test_count_limit_respected(self):
        code = "\n".join([f"def func_{i}(x): pass" for i in range(20)])
        result = _generate_tests_logic(code, "pytest", 3)
        assert result["test_count"] <= 3

    def test_no_functions_found_fallback(self):
        code = "# no functions here\nx = 1"
        result = _generate_tests_logic(code, "pytest", 5)
        assert result["test_count"] >= 1  # fallback function name

    def test_skips_private_functions(self):
        code = "def __init__(self): pass\ndef _private(): pass\ndef public(): pass"
        result = _generate_tests_logic(code, "pytest", 5)
        assert "test_public" in result["test_file"]
        # __init__ and _private not included (__ prefix filter)
        assert "test___init__" not in result["test_file"]

    def test_javascript_pattern_matching(self):
        code = "const processItem = (x) => x;\nfunction fetchData(url) { return url; }"
        result = _generate_tests_logic(code, "jest", 5)
        assert result["test_count"] > 0

    def test_functions_found_returned(self):
        code = "def alpha(x): pass\ndef beta(y): pass"
        result = _generate_tests_logic(code, "pytest", 5)
        assert "alpha" in result["functions_found"]
        assert "beta" in result["functions_found"]


@pytest.mark.asyncio
class TestHandleCallToolMCP:
    async def test_generate_code_python(self):
        result = await handle_call_tool(
            "generate_code",
            {"spec": "calculate sum of list", "language": "python", "style": "functional"},
        )
        data = json.loads(result[0].text)
        assert data["language"] == "python"

    async def test_generate_schema_json(self):
        result = await handle_call_tool(
            "generate_schema",
            {"data_description": "user with name and email", "format": "json-schema"},
        )
        data = json.loads(result[0].text)
        schema = json.loads(data["schema"])
        assert schema["type"] == "object"

    async def test_generate_tests_pytest(self):
        result = await handle_call_tool(
            "generate_tests",
            {"code": "def add(a, b): return a + b", "framework": "pytest", "count": 3},
        )
        data = json.loads(result[0].text)
        assert "test_add" in data["test_file"]

    async def test_unknown_tool_raises(self):
        with pytest.raises(ValueError, match="Unknown tool"):
            await handle_call_tool("nonexistent", {})
