"""
Baseline (single-agent) response engine.

Generates a single LLM response to a question using the Proponent persona,
so the comparison with the debate answer is fair — both start from the same
expert system prompt.
"""

from __future__ import annotations

from core.ollama_client import OllamaClient
from core.prompts import PROPONENT_SYSTEM, build_proponent_prompt
from core.utils import Timer


def run_baseline(
    question: str,
    model: str,
    temperature: float = 0.7,
    domain: str = "",
    client: OllamaClient | None = None,
) -> dict:
    """
    Generate a single-agent answer.

    Returns
    -------
    dict with keys:
        response        : str   — the model's answer
        elapsed_seconds : float — wall-clock time for generation
    """
    if client is None:
        client = OllamaClient()

    prompt = build_proponent_prompt(question, domain)

    with Timer() as t:
        response = client.generate(
            prompt=prompt,
            model=model,
            system=PROPONENT_SYSTEM,
            temperature=temperature,
        )

    return {
        "response": response,
        "elapsed_seconds": round(t.elapsed, 2),
    }
