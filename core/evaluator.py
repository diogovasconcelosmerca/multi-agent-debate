"""
Response evaluation module.

Two evaluation strategies are combined:
  1. LLM-as-judge  — the same Ollama model scores responses 1-5 on four
                     dimensions (coherence, reasoning depth, completeness, clarity).
  2. Heuristic     — simple Python-based metrics (word count, response length,
                     unique concept count).

The scores from both strategies are returned together so the UI and
dashboard can display them side by side.
"""

from __future__ import annotations

import logging

from core.config import EVALUATION_DIMENSIONS, EVALUATION_TEMPERATURE
from core.ollama_client import OllamaClient
from core.prompts import EVALUATOR_SYSTEM, build_evaluation_prompt
from core.utils import count_unique_concepts, word_count

logger = logging.getLogger(__name__)


def _default_scores() -> dict[str, int]:
    """Neutral scores used as fallback when LLM evaluation fails."""
    return {dim: 3 for dim in EVALUATION_DIMENSIONS}


def _clamp(value, lo: int = 1, hi: int = 5) -> int:
    """Ensure a score is an integer within [lo, hi]."""
    try:
        return max(lo, min(hi, int(value)))
    except (TypeError, ValueError):
        return 3


def evaluate_response(
    response: str,
    question: str,
    model: str,
    client: OllamaClient | None = None,
) -> dict:
    """
    Evaluate a single response using LLM-as-judge + heuristics.

    Returns
    -------
    dict with keys:
        llm_scores : dict[str, int]  — 1-5 scores per dimension
        heuristics : dict[str, int]  — word_count, response_length, unique_concepts
    """
    if client is None:
        client = OllamaClient()

    # --- LLM-as-judge ---------------------------------------------------
    try:
        raw = client.generate_json(
            prompt=build_evaluation_prompt(question, response),
            model=model,
            system=EVALUATOR_SYSTEM,
            temperature=EVALUATION_TEMPERATURE,
        )
        if "_error" in raw:
            logger.warning("LLM evaluation returned invalid JSON; using defaults.")
            llm_scores = _default_scores()
        else:
            llm_scores = {
                dim: _clamp(raw.get(dim, 3))
                for dim in EVALUATION_DIMENSIONS
            }
    except Exception:
        logger.exception("LLM evaluation failed; using default scores.")
        llm_scores = _default_scores()

    # --- Heuristic metrics ----------------------------------------------
    heuristics = {
        "word_count": word_count(response),
        "response_length": len(response),
        "unique_concepts": count_unique_concepts(response),
    }

    return {"llm_scores": llm_scores, "heuristics": heuristics}


def compare_responses(
    question: str,
    baseline_response: str,
    debate_response: str,
    model: str,
    client: OllamaClient | None = None,
) -> dict:
    """
    Evaluate both responses and compute a comparison summary.

    Returns
    -------
    dict with keys:
        baseline_scores    : dict — LLM scores for the baseline
        debate_scores      : dict — LLM scores for the debate
        baseline_heuristics: dict
        debate_heuristics  : dict
        deltas             : dict — (debate − baseline) per dimension
        winner             : str  — "debate", "baseline", or "tie"
    """
    if client is None:
        client = OllamaClient()

    b_eval = evaluate_response(baseline_response, question, model, client)
    d_eval = evaluate_response(debate_response, question, model, client)

    b_scores = b_eval["llm_scores"]
    d_scores = d_eval["llm_scores"]

    deltas = {dim: d_scores[dim] - b_scores[dim] for dim in EVALUATION_DIMENSIONS}
    debate_wins = sum(1 for v in deltas.values() if v > 0)
    baseline_wins = sum(1 for v in deltas.values() if v < 0)

    if debate_wins > baseline_wins:
        winner = "debate"
    elif baseline_wins > debate_wins:
        winner = "baseline"
    else:
        winner = "tie"

    return {
        "baseline_scores": b_scores,
        "debate_scores": d_scores,
        "baseline_heuristics": b_eval["heuristics"],
        "debate_heuristics": d_eval["heuristics"],
        "deltas": deltas,
        "winner": winner,
    }
