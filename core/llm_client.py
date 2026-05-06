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
import re
from typing import Any

import requests
import groq

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

# Free-tier models available on Groq
GROQ_MODELS = [
    "llama-3.3-70b-versatile",
    "llama-3.1-8b-instant",
    "gemma2-9b-it",
    "mixtral-8x7b-32768",
]


class GroqClient:
    """Synchronous client for the Groq cloud API using official sdk."""

    BACKEND = "groq"

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.client = groq.Groq(api_key=api_key)

    def check_connection(self) -> bool:
        try:
            self.client.models.list()
            return True
        except Exception:
            return False

    def list_models(self) -> list[str]:
        try:
            models_page = self.client.models.list()
            return sorted(m.id for m in models_page.data if m.active)
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

        try:
            completion = self.client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=4096,
                timeout=timeout,
            )
            return completion.choices[0].message.content or ""
        except groq.APIConnectionError as exc:
            raise LlmConnectionError(
                "Cannot connect to Groq API. Check your internet connection."
            ) from exc
        except groq.APITimeoutError as exc:
            raise LlmConnectionError(
                f"Groq request timed out after {timeout}s."
            ) from exc
        except groq.AuthenticationError as exc:
            raise LlmConnectionError(
                "Invalid Groq API key. Get one free at console.groq.com"
            ) from exc
        except groq.RateLimitError as exc:
            raise LlmConnectionError(
                "Groq rate limit exceeded. Wait a moment and try again."
            ) from exc
        except groq.APIError as exc:
            raise LlmConnectionError(
                f"Groq API error: {exc}"
            ) from exc

    def generate_json(
        self,
        prompt: str,
        model: str,
        system: str = "",
        temperature: float = 0.2,
        timeout: int = GENERATE_TIMEOUT,
    ) -> dict:
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        try:
            completion = self.client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=4096,
                timeout=timeout,
                response_format={"type": "json_object"},
            )
            raw = completion.choices[0].message.content or "{}"
            return _parse_json(raw)
        except Exception as e:
            # Fallback to standard prompt if json_object is not supported by the model
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
    """Parse JSON from LLM output, handling markdown fences and unstructured text around it."""
    text = raw.strip()

    # Try to extract content inside markdown JSON blocks
    match = re.search(r"```(?:json)?\s*(.*?)\s*```", text, re.DOTALL)
    if match:
        text = match.group(1).strip()
    else:
        # If no markdown block, try to find the first '{' and last '}'
        start_idx = text.find("{")
        end_idx = text.rfind("}")
        if start_idx != -1 and end_idx != -1 and end_idx >= start_idx:
            text = text[start_idx:end_idx+1].strip()

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
