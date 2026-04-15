"""
Unified LLM client interface.

Supports two backends:
  - Ollama (local, free, requires `ollama serve`)
  - Groq   (cloud, free tier, requires API key from console.groq.com)

Both backends expose the same interface so the debate/baseline engines
work with either one without any code changes.
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

    def __init__(self, base_url: str = OLLAMA_BASE_URL):
        self.base_url = base_url.rstrip("/")
        self._session = requests.Session()

    def check_connection(self) -> bool:
        try:
            resp = self._session.get(f"{self.base_url}/api/tags", timeout=5)
            return resp.status_code == 200
        except requests.ConnectionError:
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
                "Cannot connect to Ollama. Is it running?"
            ) from exc
        except requests.Timeout as exc:
            raise LlmConnectionError(
                f"Ollama request timed out after {timeout}s."
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

# Free-tier models available on Groq
GROQ_MODELS = [
    "llama-3.3-70b-versatile",
    "llama-3.1-8b-instant",
    "gemma2-9b-it",
    "mixtral-8x7b-32768",
]


class GroqClient:
    """Synchronous client for the Groq cloud API (OpenAI-compatible)."""

    BACKEND = "groq"

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
        except requests.ConnectionError:
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
                    "Invalid Groq API key. Get one free at console.groq.com"
                ) from exc
            elif status == 429:
                raise LlmConnectionError(
                    "Groq rate limit exceeded. Wait a moment and try again."
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
# Shared helpers
# -----------------------------------------------------------------------

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


def get_client(backend: str = "ollama", api_key: str = "") -> OllamaClient | GroqClient:
    """Factory function to create the appropriate LLM client."""
    if backend == "groq":
        if not api_key:
            raise LlmConnectionError("Groq API key is required. Get one free at console.groq.com")
        return GroqClient(api_key)
    return OllamaClient()
