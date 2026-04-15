"""
Multi-agent debate engine.

Orchestrates the three-agent debate flow:
  Round N (repeated `rounds` times):
    1. Agent A (Proponent) — proposes or revises an answer
    2. Agent B (Critic)    — critiques the proposal
    3. Agent A (Proponent) — revises based on critique
  Final:
    4. Agent C (Judge)     — produces the definitive answer

The engine is UI-agnostic.  An optional `on_step` callback lets callers
(e.g. Streamlit) react to progress without coupling the engine to a framework.
"""

from __future__ import annotations

from typing import Callable

from core.ollama_client import OllamaClient
from core.prompts import (
    CRITIC_SYSTEM,
    JUDGE_SYSTEM,
    PROPONENT_SYSTEM,
    build_critic_prompt,
    build_judge_prompt,
    build_proponent_prompt,
    build_revision_prompt,
)
from core.utils import Timer


def run_debate(
    question: str,
    model: str,
    temperature: float = 0.7,
    rounds: int = 1,
    domain: str = "",
    client: OllamaClient | None = None,
    on_step: Callable[[str, dict], None] | None = None,
) -> dict:
    """
    Execute a full multi-agent debate.

    Parameters
    ----------
    question    : The user's question.
    model       : Ollama model name.
    temperature : Sampling temperature.
    rounds      : Number of propose→critique→revise cycles.
    domain      : Optional task domain for context.
    client      : Shared OllamaClient (created if None).
    on_step     : Callback ``(step_name, step_data) -> None`` for live UI updates.
                  step_name is one of: "proposal", "critique", "revision", "judgment".

    Returns
    -------
    dict with keys:
        rounds               : list[dict]  — per-round data
        judgment              : str         — Agent C's final answer
        judgment_time         : float
        total_elapsed_seconds : float
    """
    if client is None:
        client = OllamaClient()

    def _notify(step: str, data: dict) -> None:
        if on_step is not None:
            on_step(step, data)

    result: dict = {"rounds": []}
    latest_proposal = ""

    with Timer() as total_timer:
        for round_num in range(rounds):
            round_data: dict = {"round": round_num + 1}

            # --- Step 1: Proposal (or re-proposal in round > 0) ----------
            if round_num == 0:
                prompt = build_proponent_prompt(question, domain)
            else:
                # In subsequent rounds the proponent starts from its
                # previous revision, re-evaluated against the critique.
                prompt = build_revision_prompt(
                    question, latest_proposal, round_data.get("critique", "")
                )

            with Timer() as t:
                proposal = client.generate(
                    prompt=prompt,
                    model=model,
                    system=PROPONENT_SYSTEM,
                    temperature=temperature,
                )
            round_data["proposal"] = proposal
            round_data["proposal_time"] = round(t.elapsed, 2)
            _notify("proposal", round_data)

            # --- Step 2: Critique ----------------------------------------
            with Timer() as t:
                critique = client.generate(
                    prompt=build_critic_prompt(question, proposal),
                    model=model,
                    system=CRITIC_SYSTEM,
                    temperature=temperature,
                )
            round_data["critique"] = critique
            round_data["critique_time"] = round(t.elapsed, 2)
            _notify("critique", round_data)

            # --- Step 3: Revision ----------------------------------------
            with Timer() as t:
                revision = client.generate(
                    prompt=build_revision_prompt(question, proposal, critique),
                    model=model,
                    system=PROPONENT_SYSTEM,
                    temperature=temperature,
                )
            round_data["revision"] = revision
            round_data["revision_time"] = round(t.elapsed, 2)
            latest_proposal = revision
            _notify("revision", round_data)

            result["rounds"].append(round_data)

        # --- Step 4: Judgment --------------------------------------------
        last = result["rounds"][-1]
        with Timer() as t:
            judgment = client.generate(
                prompt=build_judge_prompt(
                    question,
                    last["proposal"],
                    last["critique"],
                    last["revision"],
                ),
                model=model,
                system=JUDGE_SYSTEM,
                temperature=temperature,
            )
        result["judgment"] = judgment
        result["judgment_time"] = round(t.elapsed, 2)
        _notify("judgment", result)

    result["total_elapsed_seconds"] = round(total_timer.elapsed, 2)
    return result
