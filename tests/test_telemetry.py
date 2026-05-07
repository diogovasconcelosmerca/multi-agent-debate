"""Tests for the telemetry context manager + JSONL log."""

from __future__ import annotations

import json

import pytest

from core import telemetry


@pytest.fixture(autouse=True)
def isolated_log(tmp_path, monkeypatch):
    """Redirect the JSONL log path into a temp dir for each test."""
    log_path = tmp_path / "llm_calls.jsonl"
    monkeypatch.setattr(telemetry, "CALL_LOG_PATH", log_path)
    yield log_path


def _read(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def test_record_llm_call_writes_ok_entry(isolated_log):
    with telemetry.record_llm_call("ollama", "llama3.2", "proponent", 100) as ctx:
        ctx["response"] = "x" * 50
    rows = _read(isolated_log)
    assert len(rows) == 1
    row = rows[0]
    assert row["backend"] == "ollama"
    assert row["model"] == "llama3.2"
    assert row["role"] == "proponent"
    assert row["status"] == "ok"
    assert row["usage"]["prompt_chars"] == 100
    assert row["usage"]["response_chars"] == 50


def test_record_llm_call_writes_error_entry_on_exception(isolated_log):
    with pytest.raises(RuntimeError):
        with telemetry.record_llm_call("groq", "llama-3.3-70b", "critic", 200):
            raise RuntimeError("boom")
    rows = _read(isolated_log)
    assert len(rows) == 1
    assert rows[0]["status"] == "error"
    assert "boom" in rows[0]["error"]


def test_record_llm_call_supports_explicit_timeout_status(isolated_log):
    with telemetry.record_llm_call("gemini", "gemini-2.0-flash", "judge", 50) as ctx:
        ctx["status"] = "timeout"
    rows = _read(isolated_log)
    assert rows[0]["status"] == "timeout"
