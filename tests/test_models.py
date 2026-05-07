"""Schema-level tests for core.models."""

from __future__ import annotations

from datetime import UTC

import pytest
from pydantic import ValidationError

from core.models import (
    BaselineResult,
    DebateResult,
    Evaluation,
    ExperimentRecord,
    Heuristics,
    LlmCallLog,
    LlmScores,
    RoundData,
    TokenUsage,
)


def test_llm_scores_rejects_out_of_range():
    with pytest.raises(ValidationError):
        LlmScores(coherence=6, reasoning_depth=3, completeness=4, clarity=4)
    with pytest.raises(ValidationError):
        LlmScores(coherence=0, reasoning_depth=3, completeness=4, clarity=4)


def test_llm_scores_as_dict_round_trip():
    s = LlmScores(coherence=4, reasoning_depth=3, completeness=5, clarity=4)
    d = s.as_dict()
    assert d == {"coherence": 4, "reasoning_depth": 3, "completeness": 5, "clarity": 4}


def test_evaluation_requires_all_dimensions():
    with pytest.raises(ValidationError):
        Evaluation(
            baseline_scores={"coherence": 3},  # missing 3 dims
            debate_scores={"coherence": 4, "reasoning_depth": 4, "completeness": 4, "clarity": 4},
            baseline_heuristics=Heuristics(word_count=10, response_length=50, unique_concepts=5),
            debate_heuristics=Heuristics(word_count=20, response_length=100, unique_concepts=10),
            deltas={"coherence": 1, "reasoning_depth": 1, "completeness": 1, "clarity": 1},
            winner="debate",
        )


def test_token_usage_token_estimates():
    u = TokenUsage(prompt_chars=400, response_chars=1200)
    assert u.approx_prompt_tokens == 100
    assert u.approx_response_tokens == 300
    assert u.approx_total_tokens == 400


def test_experiment_record_validates_full_payload():
    rec = ExperimentRecord.model_validate({
        "experiment_id": "exp_test_0001",
        "timestamp": "2026-01-01T00:00:00+00:00",
        "question": "What is intelligence?",
        "domain": "Philosophy",
        "model": "llama3.2",
        "temperature": 0.7,
        "debate_rounds": 1,
        "baseline": BaselineResult(response="x", elapsed_seconds=1.0).model_dump(),
        "debate": DebateResult(
            rounds=[RoundData(
                round=1, proposal="p", proposal_time=1.0,
                critique="c", critique_time=1.0,
                revision="r", revision_time=1.0,
            )],
            judgment="j", judgment_time=1.0, total_elapsed_seconds=4.0,
        ).model_dump(),
        "evaluation": {
            "baseline_scores": {"coherence": 3, "reasoning_depth": 3, "completeness": 3, "clarity": 3},
            "debate_scores": {"coherence": 4, "reasoning_depth": 4, "completeness": 4, "clarity": 4},
            "baseline_heuristics": {"word_count": 5, "response_length": 30, "unique_concepts": 2},
            "debate_heuristics": {"word_count": 10, "response_length": 60, "unique_concepts": 4},
            "deltas": {"coherence": 1, "reasoning_depth": 1, "completeness": 1, "clarity": 1},
            "winner": "debate",
        },
    })
    assert rec.evaluation.winner == "debate"
    assert rec.debate.rounds[0].round == 1


def test_llm_call_log_round_trips_to_json():
    from datetime import datetime

    entry = LlmCallLog(
        timestamp=datetime(2026, 1, 1, tzinfo=UTC),
        backend="ollama",
        model="llama3.2",
        role="proponent",
        elapsed_ms=4321,
        status="ok",
        usage=TokenUsage(prompt_chars=200, response_chars=800),
        error=None,
    )
    encoded = entry.model_dump_json()
    decoded = LlmCallLog.model_validate_json(encoded)
    assert decoded == entry
