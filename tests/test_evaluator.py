"""Tests for evaluator score validation and comparison logic."""

from __future__ import annotations

from unittest.mock import MagicMock

from core.evaluator import (
    _coerce_int,
    _default_scores,
    _validate_scores,
    compare_responses,
    evaluate_response,
)


def test_default_scores_are_neutral():
    s = _default_scores()
    assert all(v == 3 for v in s.values())
    assert set(s.keys()) == {"coherence", "reasoning_depth", "completeness", "clarity"}


def test_coerce_int_handles_strings_and_floats():
    assert _coerce_int("4") == 4
    assert _coerce_int(4.0) == 4
    assert _coerce_int("nope") == 3
    assert _coerce_int(None) == 3


def test_validate_scores_clamps_out_of_range():
    out = _validate_scores({"coherence": 9, "reasoning_depth": 0,
                            "completeness": 4, "clarity": 5})
    assert out["coherence"] == 5
    assert out["reasoning_depth"] == 1
    assert out["completeness"] == 4
    assert out["clarity"] == 5


def test_validate_scores_fills_missing_keys_with_default():
    out = _validate_scores({"coherence": 4})
    assert out["coherence"] == 4
    assert out["reasoning_depth"] == 3
    assert out["completeness"] == 3
    assert out["clarity"] == 3


def _mock_client(scores: dict[str, int]):
    client = MagicMock()
    client.generate_json.return_value = scores
    return client


def test_evaluate_response_validates_llm_output():
    client = _mock_client({"coherence": 5, "reasoning_depth": 4,
                           "completeness": 4, "clarity": 5})
    out = evaluate_response("Q?", "A.", "model", client)
    assert out["llm_scores"] == {
        "coherence": 5, "reasoning_depth": 4,
        "completeness": 4, "clarity": 5,
    }
    assert "word_count" in out["heuristics"]


def test_compare_responses_picks_winner():
    client = MagicMock()
    # First call → baseline scores; second call → debate scores
    client.generate_json.side_effect = [
        {"coherence": 3, "reasoning_depth": 3, "completeness": 3, "clarity": 3},
        {"coherence": 4, "reasoning_depth": 4, "completeness": 4, "clarity": 4},
    ]
    out = compare_responses("Q?", "baseline", "debate", "model", client)
    assert out["winner"] == "debate"
    assert all(v == 1 for v in out["deltas"].values())


def test_compare_responses_ties_correctly():
    client = MagicMock()
    same = {"coherence": 3, "reasoning_depth": 3, "completeness": 3, "clarity": 3}
    client.generate_json.side_effect = [same, dict(same)]
    out = compare_responses("Q?", "a", "b", "model", client)
    assert out["winner"] == "tie"
