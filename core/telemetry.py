"""
Lightweight structured telemetry for every LLM call.

Each `generate()` invocation across the three backends emits one
:class:`LlmCallLog` line. We persist them as JSONL under
``data/logs/llm_calls.jsonl`` for offline analysis and also forward
them to Python's stdlib :mod:`logging` so an operator running the app
in the foreground sees the same stream interleaved with stack traces.

Why JSONL instead of a database? The intended audience for this signal
is a researcher running batches of experiments locally; appending to a
flat file is zero-config, atomic on POSIX, and trivially analysable
with :mod:`pandas` (``pd.read_json('llm_calls.jsonl', lines=True)``).
"""

from __future__ import annotations

import contextlib
import json
import logging
import threading
from collections.abc import Iterator
from datetime import UTC, datetime
from time import perf_counter

from core.config import DATA_DIR
from core.models import Backend, LlmCallLog, TokenUsage

LOG_DIR = DATA_DIR / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)
CALL_LOG_PATH = LOG_DIR / "llm_calls.jsonl"

_logger = logging.getLogger("mads.llm")
_write_lock = threading.Lock()


def _emit(entry: LlmCallLog) -> None:
    """Append one structured entry to the JSONL log."""
    line = entry.model_dump_json()
    with _write_lock:
        with CALL_LOG_PATH.open("a", encoding="utf-8") as fh:
            fh.write(line + "\n")
    _logger.info(line)


@contextlib.contextmanager
def record_llm_call(
    backend: Backend,
    model: str,
    role: str,
    prompt_chars: int,
) -> Iterator[dict]:
    """
    Context manager around a single ``client.generate()`` call.

    Usage::

        with record_llm_call("groq", "llama-3.3-70b", "critic", len(prompt)) as ctx:
            response = client.generate(...)
            ctx["response"] = response

    On exit, an :class:`LlmCallLog` is written. The caller can also set
    ``ctx["status"]`` to ``"timeout"`` or ``"error"`` and ``ctx["error"]``
    with a message; otherwise the manager infers ``ok`` on clean exit
    and ``error`` if an exception propagates.
    """
    started = perf_counter()
    ctx: dict = {"response": "", "status": "ok", "error": None}
    try:
        yield ctx
    except Exception as exc:
        ctx["status"] = "error"
        ctx["error"] = f"{type(exc).__name__}: {exc}"
        elapsed_ms = int((perf_counter() - started) * 1000)
        _emit(
            LlmCallLog(
                timestamp=datetime.now(UTC),
                backend=backend,
                model=model,
                role=role,
                elapsed_ms=elapsed_ms,
                status="error",
                usage=TokenUsage(prompt_chars=prompt_chars, response_chars=0),
                error=ctx["error"],
            )
        )
        raise
    else:
        elapsed_ms = int((perf_counter() - started) * 1000)
        response = ctx.get("response") or ""
        _emit(
            LlmCallLog(
                timestamp=datetime.now(UTC),
                backend=backend,
                model=model,
                role=role,
                elapsed_ms=elapsed_ms,
                status=ctx.get("status", "ok"),
                usage=TokenUsage(
                    prompt_chars=prompt_chars,
                    response_chars=len(response),
                ),
                error=ctx.get("error"),
            )
        )


def load_call_log() -> list[dict]:
    """Read the JSONL log back into memory. Used by tests and the dashboard."""
    if not CALL_LOG_PATH.exists():
        return []
    out: list[dict] = []
    with CALL_LOG_PATH.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                out.append(json.loads(line))
    return out
