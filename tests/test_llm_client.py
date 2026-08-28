import json
import sys
from unittest.mock import MagicMock

# Mock dependencies not available in the environment
mock_requests = MagicMock()
sys.modules["requests"] = mock_requests
sys.modules["streamlit"] = MagicMock()

from core.llm_client import _parse_json

def test_parse_json_valid():
    """Verify it parses a simple valid JSON string."""
    raw = '{"key": "value", "number": 123}'
    expected = {"key": "value", "number": 123}
    assert _parse_json(raw) == expected

def test_parse_json_with_fences():
    """Verify it correctly strips markdown fences and parses the JSON."""
    raw = "```json\n" + '{"key": "value"}' + "\n```"
    expected = {"key": "value"}
    assert _parse_json(raw) == expected

    raw_no_lang = "```\n" + '{"key": "value"}' + "\n```"
    assert _parse_json(raw_no_lang) == expected

def test_parse_json_invalid():
    """Verify it returns a dictionary with _error and _raw keys when given malformed JSON."""
    raw = '{"key": "value", missing_quotes: 123}'
    result = _parse_json(raw)
    assert result["_error"] == "json_parse_failed"
    assert result["_raw"] == raw

def test_parse_json_empty():
    """Verify it handles empty strings by returning the error dictionary."""
    raw = ""
    result = _parse_json(raw)
    assert result["_error"] == "json_parse_failed"
    assert result["_raw"] == raw

def test_parse_json_garbage_with_fences():
    """Verify it handles markdown fences containing non-JSON content."""
    raw = "```json\nNot a JSON\n```"
    result = _parse_json(raw)
    assert result["_error"] == "json_parse_failed"
    assert result["_raw"] == raw
