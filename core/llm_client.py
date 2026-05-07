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
from typing import Any

import requests

from core.config import GENERATE_TIMEOUT, OLLAMA_BASE_URL

logger = logging.getLogger(__name__)


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
    ) -> str:
        payload: dict[str, Any] = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": temperature},
        }
        if system:
            payload["system"] = system

        try:
            resp = self._session.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=timeout,
            )
            resp.raise_for_status()
            return resp.json()["response"]
        except requests.ConnectionError as exc:
            raise LlmConnectionError(
                "Cannot reach Ollama at "
                f"{self.base_url}. Run `ollama serve` and try again."
            ) from exc
        except requests.Timeout as exc:
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
    ) -> dict:
        full_prompt = prompt + "\n\nReturn ONLY valid JSON. No extra text."
        raw = self.generate(
            prompt=full_prompt, model=model, system=system,
            temperature=temperature, timeout=timeout,
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
    ) -> str:
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": 4096,
        }

        try:
            resp = self._session.post(
                GROQ_API_URL,
                json=payload,
                timeout=timeout,
            )
            resp.raise_for_status()
            return resp.json()["choices"][0]["message"]["content"]
        except requests.ConnectionError as exc:
            raise LlmConnectionError(
                "Cannot connect to Groq API. Check your internet connection."
            ) from exc
        except requests.Timeout as exc:
            raise LlmConnectionError(
                f"Groq request timed out after {timeout}s."
            ) from exc
        except requests.HTTPError as exc:
            status = getattr(exc.response, "status_code", "?")
            body = getattr(exc.response, "text", "")[:200]
            if status == 401:
                raise LlmConnectionError(
                    "Invalid Groq API key. Get one free at console.groq.com."
                ) from exc
            if status == 429:
                raise LlmConnectionError(
                    "Groq rate limit reached. Wait a moment, switch model, "
                    "or try the Gemini backend."
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
    ) -> dict:
        full_prompt = prompt + "\n\nReturn ONLY valid JSON. No extra text."
        raw = self.generate(
            prompt=full_prompt, model=model, system=system,
            temperature=temperature, timeout=timeout,
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
    ) -> str:
        # Gemini accepts a top-level systemInstruction object.
        payload: dict[str, Any] = {
            "contents": [{"role": "user", "parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": 4096,
            },
        }
        if system:
            payload["systemInstruction"] = {"parts": [{"text": system}]}

        url = f"{GEMINI_API_BASE}/models/{model}:generateContent"
        try:
            resp = self._session.post(
                url, params=self._params(), json=payload, timeout=timeout,
            )
            resp.raise_for_status()
            data = resp.json()
            return _extract_gemini_text(data)
        except requests.ConnectionError as exc:
            raise LlmConnectionError(
                "Cannot connect to Gemini API. Check your internet connection."
            ) from exc
        except requests.Timeout as exc:
            raise LlmConnectionError(
                f"Gemini request timed out after {timeout}s."
            ) from exc
        except requests.HTTPError as exc:
            status = getattr(exc.response, "status_code", "?")
            body = getattr(exc.response, "text", "")[:300]
            if status in (400, 401, 403) and "API key" in body:
                raise LlmConnectionError(
                    "Invalid Gemini API key. Get one free at "
                    "aistudio.google.com/app/apikey."
                ) from exc
            if status == 429:
                raise LlmConnectionError(
                    "Gemini rate limit reached on the free tier. "
                    "Wait a minute or switch to a flash-lite model."
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
    ) -> dict:
        full_prompt = prompt + "\n\nReturn ONLY valid JSON. No extra text."
        raw = self.generate(
            prompt=full_prompt, model=model, system=system,
            temperature=temperature, timeout=timeout,
        )
        return _parse_json(raw)


# -----------------------------------------------------------------------
# Shared helpers
# -----------------------------------------------------------------------

def _extract_gemini_text(data: dict) -> str:
    """Pull the response text out of a Gemini generateContent payload."""
    candidates = data.get("candidates") or []
    if not candidates:
        # Surface block reasons (safety filter, recitation, etc.) instead
        # of returning an empty string silently.
        feedback = data.get("promptFeedback", {})
        reason = feedback.get("blockReason")
        if reason:
            raise LlmConnectionError(f"Gemini blocked the request: {reason}.")
        return ""
    parts = candidates[0].get("content", {}).get("parts", []) or []
    return "".join(p.get("text", "") for p in parts).strip()


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
