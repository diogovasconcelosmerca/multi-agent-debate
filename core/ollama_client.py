"""
Backward-compatibility shim.

All client logic now lives in core.llm_client.
This module re-exports the classes so existing imports keep working.
"""

from core.llm_client import (  # noqa: F401
    GroqClient,
    LlmConnectionError,
    OllamaClient,
    OllamaConnectionError,
    get_client,
)
