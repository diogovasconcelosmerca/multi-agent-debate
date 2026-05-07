"""Tests for the JSON parsing and Gemini text extraction helpers."""

from __future__ import annotations

import pytest

from core.llm_client import LlmConnectionError, _extract_gemini_text, _parse_json


def test_parse_json_plain():
    assert _parse_json('{"coherence": 4, "clarity": 5}') == {"coherence": 4, "clarity": 5}


def test_parse_json_strips_markdown_fence():
    raw = "```json\n{\"a\": 1}\n```"
    assert _parse_json(raw) == {"a": 1}


def test_parse_json_strips_unlabelled_fence():
    raw = "```\n{\"a\": 1}\n```"
    assert _parse_json(raw) == {"a": 1}


def test_parse_json_returns_error_marker_on_invalid():
    out = _parse_json("not json at all")
    assert out["_error"] == "json_parse_failed"
    assert out["_raw"] == "not json at all"


def test_extract_gemini_text_happy_path():
    payload = {
        "candidates": [
            {"content": {"parts": [{"text": "hello "}, {"text": "world"}]}}
        ]
    }
    assert _extract_gemini_text(payload) == "hello world"


def test_extract_gemini_text_empty_candidates_returns_empty():
    assert _extract_gemini_text({"candidates": []}) == ""


def test_extract_gemini_text_raises_on_block_reason():
    payload = {"candidates": [], "promptFeedback": {"blockReason": "SAFETY"}}
    with pytest.raises(LlmConnectionError):
        _extract_gemini_text(payload)
