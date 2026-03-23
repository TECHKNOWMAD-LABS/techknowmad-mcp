"""Shared fixtures and mock helpers for the techknowmad-mcp test suite."""
import pytest
import json
from unittest.mock import MagicMock, AsyncMock


@pytest.fixture
def sample_population():
    """Sample genetic algorithm population."""
    return [
        {"fitness": 0.8, "genes": [0.5, 0.3, 0.9]},
        {"fitness": 0.6, "genes": [0.2, 0.7, 0.4]},
        {"fitness": 0.4, "genes": [0.1, 0.1, 0.1]},
        {"fitness": 0.9, "genes": [0.9, 0.8, 0.7]},
    ]


@pytest.fixture
def sample_nodes():
    """Sample graph nodes."""
    return [
        {"id": "A", "label": "Node A"},
        {"id": "B", "label": "Node B"},
        {"id": "C", "label": "Node C"},
        {"id": "D", "label": "Node D"},
    ]


@pytest.fixture
def sample_edges():
    """Sample graph edges."""
    return [
        {"source": "A", "target": "B", "weight": 1.0},
        {"source": "B", "target": "C", "weight": 2.0},
        {"source": "C", "target": "D", "weight": 1.5},
    ]


@pytest.fixture
def sample_graph_data(sample_nodes, sample_edges):
    """Sample graph dict with nodes and edges."""
    return {
        "nodes": sample_nodes,
        "edges": sample_edges,
    }


@pytest.fixture
def simple_python_code():
    """Sample Python code for test generation."""
    return """
def calculate_total(items):
    '''Calculate total of items.'''
    return sum(items)

def validate_input(data):
    '''Validate input data.'''
    if data is None:
        raise ValueError("Data cannot be None")
    return True

def process_record(record):
    '''Process a single record.'''
    return {"processed": True, "id": record.get("id")}
"""


@pytest.fixture
def sample_test_cases():
    """Sample benchmark test cases."""
    return [
        {"input": 5, "expected": 5},
        {"input": 0, "expected": 0},
        {"input": "hello", "expected": "hello"},
        {"input": True, "expected": True},
        {"input": [1, 2], "expected": [1, 2]},
    ]


def make_mock_tool_result(data: dict):
    """Create a mock tool result with JSON content."""
    mock = MagicMock()
    mock.text = json.dumps(data)
    return [mock]
