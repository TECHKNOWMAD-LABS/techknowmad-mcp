# forge-generate-mcp

**Generate Code and Artifacts MCP Server**

## Overview

forge-generate-mcp provides code generation tools that create skeletons, schemas, and test stubs from natural language specifications. It uses keyword detection to infer structure from descriptions.

## Tools

### `generate_code`
Generates a code skeleton from a spec description.
- Detects function and class names from spec keywords
- Produces language-specific syntax (python, javascript, typescript, go, rust)
- Style options: "functional", "class-based", "minimal"
- Returns a code string with proper structure

### `generate_schema`
Generates a data schema from a description.
- Parses field names and infers types from keywords
- Formats: "json-schema", "pydantic", "typescript"
- Returns a complete schema string

### `generate_tests`
Generates test stubs from existing code.
- Parses function names using regex
- Frameworks: "pytest", "jest", "unittest"
- `count` controls max stubs generated
- Returns a complete test file string

## Use Cases
- Scaffolding new services rapidly
- Schema-first API development
- TDD test stub generation
- Boilerplate elimination
- Spec-to-code translation
