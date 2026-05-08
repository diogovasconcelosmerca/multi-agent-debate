"""
Unified LLM client interface.

Supports three backends:
  - Ollama  (local, free, requires `ollama serve`)
  - Groq    (cloud, free tier, requires API key from console.groq.com)
  - Gemini  (cloud, generous free tier, requires API key from aistudio.google.com)

All backends expose the same `generate` / `generate_json` / `list_models` /
`check_connection` surface so the debate, baseline, and evaluator engines
work with any of them without any code changes.
"""

from __future__ import annotations

import json
import logging
import time
from typing import Any

import requests

from core.config import GENERATE_TIMEOUT, OLLAMA_BASE_URL
from core.telemetry import record_llm_call

logger = logging.getLogger(__name__)


# Sliding-window retry budget for rate-limited cloud calls. The free
# tiers we target (Groq, Gemini) cap us per minute; one debate fires
# ~10 calls in 20 s so a brief pause is usually enough to recover.
_RATE_LIMIT_RETRIES = 2
_RATE_LIMIT_BACKOFF_S = (4, 10)  # progressive: 4 s, then 10 s


class LlmConnectionError(RuntimeError):
    """Raised when the LLM backend is unreachable or returns an error."""


# Keep backward-compatible alias
OllamaConnectionError = LlmConnectionError


# -----------------------------------------------------------------------
# Ollama backend
# -----------------------------------------------------------------------

class OllamaClient:
    """Synchronous client for the Ollama REST API (local)."""

    BACKEND = "ollama"
    DISPLAY_NAME = "Ollama"

    def __init__(self, base_url: str = OLLAMA_BASE_URL):
        self.base_url = base_url.rstrip("/")
        self._session = requests.Session()

    def check_connection(self) -> bool:
        try:
            resp = self._session.get(f"{self.base_url}/api/tags", timeout=5)
            return resp.status_code == 200
        except requests.ConnectionError:
            return False
        except requests.Timeout:
            return False

    def list_models(self) -> list[str]:
        try:
            resp = self._session.get(f"{self.base_url}/api/tags", timeout=5)
            resp.raise_for_status()
            models = resp.json().get("models", [])
            return sorted(m["name"] for m in models)
        except (requests.ConnectionError, requests.Timeout, KeyError):
            return []

    def generate(
        self,
        prompt: str,
        model: str,
        system: str = "",
        temperature: float = 0.7,
        timeout: int = GENERATE_TIMEOUT,
        role: str = "agent",
    ) -> str:
        payload: dict[str, Any] = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": temperature},
        }
        if system:
            payload["system"] = system

        prompt_chars = len(prompt) + len(system)
        with record_llm_call("ollama", model, role, prompt_chars) as ctx:
            try:
                resp = self._session.post(
                    f"{self.base_url}/api/generate",
                    json=payload,
                    timeout=timeout,
                )
                resp.raise_for_status()
                text = resp.json()["response"]
                ctx["response"] = text
                return text
            except requests.ConnectionError as exc:
                ctx["status"] = "error"
                raise LlmConnectionError(
                    "Cannot reach Ollama at "
                    f"{self.base_url}. Run `ollama serve` and try again."
                ) from exc
            except requests.Timeout as exc:
                ctx["status"] = "timeout"
                raise LlmConnectionError(
                    f"Ollama timed out after {timeout}s. Try a smaller model "
                    "(e.g. `ollama pull llama3.2:1b`) or fewer debate rounds."
                ) from exc

    def generate_json(
        self,
        prompt: str,
        model: str,
        system: str = "",
        temperature: float = 0.2,
        timeout: int = GENERATE_TIMEOUT,
        role: str = "evaluator",
    ) -> dict:
        full_prompt = prompt + "\n\nReturn ONLY valid JSON. No extra text."
        raw = self.generate(
            prompt=full_prompt, model=model, system=system,
            temperature=temperature, timeout=timeout, role=role,
        )
        return _parse_json(raw)


# -----------------------------------------------------------------------
# Groq backend
# -----------------------------------------------------------------------

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"

# Free-tier models currently active on Groq (Jan 2026).
# Mixtral was retired; keep this list in sync with console.groq.com/docs/models.
GROQ_MODELS = [
    "llama-3.3-70b-versatile",
    "llama-3.1-8b-instant",
    "gemma2-9b-it",
]


class GroqClient:
    """Synchronous client for the Groq cloud API (OpenAI-compatible)."""

    BACKEND = "groq"
    DISPLAY_NAME = "Groq"

    def __init__(self, api_key: str):
        self.api_key = api_key
        self._session = requests.Session()
        self._session.headers.update({
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        })

    def check_connection(self) -> bool:
        try:
            resp = self._session.get(
                "https://api.groq.com/openai/v1/models",
                timeout=8,
            )
            return resp.status_code == 200
        except (requests.ConnectionError, requests.Timeout):
            return False

    def list_models(self) -> list[str]:
        try:
            resp = self._session.get(
                "https://api.groq.com/openai/v1/models",
                timeout=8,
            )
            resp.raise_for_status()
            data = resp.json().get("data", [])
            return sorted(m["id"] for m in data if m.get("active", True))
        except Exception:
            return list(GROQ_MODELS)

    def generate(
        self,
        prompt: str,
        model: str,
        system: str = "",
        temperature: float = 0.7,
        timeout: int = GENERATE_TIMEOUT,
        role: str = "agent",
    ) -> str:
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        # Cap at 1024 tokens — the prompts ask for 150–280 word answers,
        # so anything more is likely the model rambling and burning quota.
        # The evaluator returns a tiny JSON, so this is comfortable headroom.
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": 1024,
        }

        prompt_chars = len(prompt) + len(system)
        with record_llm_call("groq", model, role, prompt_chars) as ctx:
            attempt = 0
            while True:
                try:
                    resp = self._session.post(
                        GROQ_API_URL,
                        json=payload,
                        timeout=timeout,
                    )
                    resp.raise_for_status()
                    text = resp.json()["choices"][0]["message"]["content"]
                    ctx["response"] = text
                    return text
                except requests.ConnectionError as exc:
                    ctx["status"] = "error"
                    raise LlmConnectionError(
                        "Cannot connect to Groq API. Check your internet connection."
                    ) from exc
                except requests.Timeout as exc:
                    ctx["status"] = "timeout"
                    raise LlmConnectionError(
                        f"Groq request timed out after {timeout}s."
                    ) from exc
                except requests.HTTPError as exc:
                    status = getattr(exc.response, "status_code", "?")
                    body = getattr(exc.response, "text", "")[:200]
                    if status == 429 and attempt < _RATE_LIMIT_RETRIES:
                        wait = _RATE_LIMIT_BACKOFF_S[attempt]
                        logger.info("Groq 429 — backing off %ss (attempt %d)", wait, attempt + 1)
                        time.sleep(wait)
                        attempt += 1
                        continue
                    ctx["status"] = "error"
                    if status == 401:
                        raise LlmConnectionError(
                            "Invalid Groq API key. Get one free at console.groq.com."
                        ) from exc
                    if status == 429:
                        raise LlmConnectionError(
                            "Groq rate limit reached even after retries. "
                            "Wait a minute, switch model, or try Gemini."
                        ) from exc
                    if status in (402, 403):
                        raise LlmConnectionError(
                            "Groq quota exhausted on this key. Try the Gemini "
                            "backend or a local Ollama model."
                        ) from exc
                    raise LlmConnectionError(
                        f"Groq API error ({status}): {body}"
                    ) from exc

    def generate_json(
        self,
        prompt: str,
        model: str,
        system: str = "",
        temperature: float = 0.2,
        timeout: int = GENERATE_TIMEOUT,
        role: str = "evaluator",
    ) -> dict:
        full_prompt = prompt + "\n\nReturn ONLY valid JSON. No extra text."
        raw = self.generate(
            prompt=full_prompt, model=model, system=system,
            temperature=temperature, timeout=timeout, role=role,
        )
        return _parse_json(raw)


# -----------------------------------------------------------------------
# Gemini backend (Google AI Studio — generous free tier)
# -----------------------------------------------------------------------

GEMINI_API_BASE = "https://generativelanguage.googleapis.com/v1beta"

# Gemini free-tier models (as of Jan 2026). Flash variants are fastest;
# Pro has a smaller free quota but is the strongest reasoner.
GEMINI_MODELS = [
    "gemini-2.0-flash",
    "gemini-2.0-flash-lite",
    "gemini-1.5-flash",
    "gemini-1.5-flash-8b",
    "gemini-1.5-pro",
]


class GeminiClient:
    """Synchronous client for the Google Gemini REST API."""

    BACKEND = "gemini"
    DISPLAY_NAME = "Gemini"

    def __init__(self, api_key: str):
        self.api_key = api_key
        self._session = requests.Session()
        self._session.headers.update({"Content-Type": "application/json"})

    # The API key is passed as a query parameter on every call.
    def _params(self) -> dict[str, str]:
        return {"key": self.api_key}

    def check_connection(self) -> bool:
        try:
            resp = self._session.get(
                f"{GEMINI_API_BASE}/models",
                params=self._params(),
                timeout=8,
            )
            return resp.status_code == 200
        except (requests.ConnectionError, requests.Timeout):
            return False

    def list_models(self) -> list[str]:
        try:
            resp = self._session.get(
                f"{GEMINI_API_BASE}/models",
                params=self._params(),
                timeout=8,
            )
            resp.raise_for_status()
            data = resp.json().get("models", [])
            ids: list[str] = []
            for m in data:
                name = m.get("name", "")
                # API returns names like "models/gemini-2.0-flash"; strip the prefix.
                short = name.split("/", 1)[1] if name.startswith("models/") else name
                methods = m.get("supportedGenerationMethods", [])
                # Only keep models that can actually generate content.
                if "generateContent" in methods and short:
                    ids.append(short)
            # Surface the curated default list at the top, then anything else.
            preferred = [m for m in GEMINI_MODELS if m in ids]
            extras = sorted(m for m in ids if m not in preferred)
            return preferred + extras or list(GEMINI_MODELS)
        except Exception:
            return list(GEMINI_MODELS)

    def generate(
        self,
        prompt: str,
        model: str,
        system: str = "",
        temperature: float = 0.7,
        timeout: int = GENERATE_TIMEOUT,
        role: str = "agent",
    ) -> str:
        # Gemini accepts a top-level systemInstruction object.
        # 1024 token cap matches the Groq client — prompts target
        # 150–280 word answers, so anything more is the model rambling.
        payload: dict[str, Any] = {
            "contents": [{"role": "user", "parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": 1024,
            },
        }
        if system:
            payload["systemInstruction"] = {"parts": [{"text": system}]}

        url = f"{GEMINI_API_BASE}/models/{model}:generateContent"
        prompt_chars = len(prompt) + len(system)
        with record_llm_call("gemini", model, role, prompt_chars) as ctx:
            attempt = 0
            while True:
                try:
                    resp = self._session.post(
                        url, params=self._params(), json=payload, timeout=timeout,
                    )
                    resp.raise_for_status()
                    data = resp.json()
                    text = _extract_gemini_text(data)
                    ctx["response"] = text
                    return text
                except requests.ConnectionError as exc:
                    ctx["status"] = "error"
                    raise LlmConnectionError(
                        "Cannot connect to Gemini API. Check your internet connection."
                    ) from exc
                except requests.Timeout as exc:
                    ctx["status"] = "timeout"
                    raise LlmConnectionError(
                        f"Gemini request timed out after {timeout}s."
                    ) from exc
                except requests.HTTPError as exc:
                    status = getattr(exc.response, "status_code", "?")
                    body = getattr(exc.response, "text", "")[:300]
                    # 429: respect the per-minute rate limit by sleeping
                    # then retrying. The free-tier window is 60 s, but
                    # short backoffs usually clear quota for the next
                    # debate step.
                    if status == 429 and attempt < _RATE_LIMIT_RETRIES:
                        wait = _RATE_LIMIT_BACKOFF_S[attempt]
                        logger.info("Gemini 429 — backing off %ss (attempt %d)", wait, attempt + 1)
                        time.sleep(wait)
                        attempt += 1
                        continue
                    ctx["status"] = "error"
                    if status in (400, 401, 403) and "API key" in body:
                        raise LlmConnectionError(
                            "Invalid Gemini API key. Get one free at "
                            "aistudio.google.com/app/apikey."
                        ) from exc
                    if status == 429:
                        raise LlmConnectionError(
                            "Gemini rate limit reached on the free tier even "
                            "after retries. Wait ~60 s, switch to "
                            "`gemini-2.0-flash-lite` (30 RPM), or try Groq."
                        ) from exc
                    if status == 404:
                        raise LlmConnectionError(
                            f"Gemini model `{model}` not found. Pick another from "
                            "the model list."
                        ) from exc
                    raise LlmConnectionError(
                        f"Gemini API error ({status}): {body}"
                    ) from exc

    def generate_json(
        self,
        prompt: str,
        model: str,
        system: str = "",
        temperature: float = 0.2,
        timeout: int = GENERATE_TIMEOUT,
        role: str = "evaluator",
    ) -> dict:
        full_prompt = prompt + "\n\nReturn ONLY valid JSON. No extra text."
        raw = self.generate(
            prompt=full_prompt, model=model, system=system,
            temperature=temperature, timeout=timeout, role=role,
        )
        return _parse_json(raw)


# -----------------------------------------------------------------------
# Shared helpers
# -----------------------------------------------------------------------

def _extract_gemini_text(data: dict) -> str:
    """Pull the response text out of a Gemini generateContent payload.

    Surfaces every empty-content corner case as an explicit error
    rather than returning an empty string — silent empties were
    confusing users who saw a "complete" status but no answer.
    """
    candidates = data.get("candidates") or []
    if not candidates:
        feedback = data.get("promptFeedback", {})
        reason = feedback.get("blockReason")
        if reason:
            raise LlmConnectionError(f"Gemini blocked the request: {reason}.")
        raise LlmConnectionError(
            "Gemini returned no candidates. The model may be temporarily "
            "unavailable — try again or pick another model."
        )
    cand = candidates[0]
    parts = cand.get("content", {}).get("parts", []) or []
    text = "".join(p.get("text", "") for p in parts).strip()
    if text:
        return text
    # No text — translate the finishReason into something actionable.
    reason = cand.get("finishReason", "")
    if reason == "MAX_TOKENS":
        raise LlmConnectionError(
            "Gemini hit the output token cap before producing text. "
            "Try a shorter question or a smaller model (gemini-2.0-flash-lite)."
        )
    if reason in ("SAFETY", "RECITATION"):
        raise LlmConnectionError(
            f"Gemini refused the request ({reason}). Reword the question."
        )
    if reason and reason != "STOP":
        raise LlmConnectionError(
            f"Gemini returned no text (finishReason={reason})."
        )
    return ""


def _parse_json(raw: str) -> dict:
    """Parse JSON from LLM output, handling markdown fences."""
    text = raw.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        lines = [ln for ln in lines if not ln.strip().startswith("```")]
        text = "\n".join(lines).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        logger.warning("Failed to parse LLM JSON output: %s", text[:200])
        return {"_error": "json_parse_failed", "_raw": raw}


def get_client(
    backend: str = "ollama",
    api_key: str = "",
) -> OllamaClient | GroqClient | GeminiClient:
    """Factory function to create the appropriate LLM client."""
    backend = (backend or "ollama").lower()
    if backend == "groq":
        if not api_key:
            raise LlmConnectionError(
                "Groq API key is required. Get one free at console.groq.com."
            )
        return GroqClient(api_key)
    if backend == "gemini":
        if not api_key:
            raise LlmConnectionError(
                "Gemini API key is required. Get one free at "
                "aistudio.google.com/app/apikey."
            )
        return GeminiClient(api_key)
    return OllamaClient()
