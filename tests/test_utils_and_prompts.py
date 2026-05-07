"""Tests for sanitisation, heuristics, and prompt assembly."""

from __future__ import annotations

from core.prompts import (
    build_critic_prompt,
    build_evaluation_prompt,
    build_proponent_prompt,
)
from core.utils import (
    MAX_QUESTION_CHARS,
    count_unique_concepts,
    sanitize_user_text,
    word_count,
)


def test_sanitize_strips_control_chars():
    raw = "hello\x01\x02 world\x07"
    assert sanitize_user_text(raw) == "hello world"


def test_sanitize_keeps_newlines_and_tabs():
    raw = "line1\nline2\tindented"
    assert sanitize_user_text(raw) == "line1\nline2\tindented"


def test_sanitize_collapses_excessive_newlines():
    raw = "a\n\n\n\n\nb"
    assert sanitize_user_text(raw) == "a\n\nb"


def test_sanitize_truncates_long_input():
    raw = "x" * (MAX_QUESTION_CHARS + 500)
    out = sanitize_user_text(raw)
    assert len(out) <= MAX_QUESTION_CHARS + 1  # + ellipsis
    assert out.endswith("…")


def test_sanitize_handles_empty_input():
    assert sanitize_user_text("") == ""
    assert sanitize_user_text("   \n\t  ") == ""


def test_word_count_basic():
    assert word_count("the quick brown fox") == 4
    assert word_count("") == 0


def test_unique_concepts_filters_stopwords_and_short_words():
    text = "the cat sat on a comfortable cushion near the window"
    # comfortable, cushion, window are >4 chars and not in stopwords
    assert count_unique_concepts(text) == 3


def test_build_proponent_prompt_includes_question_and_domain():
    p = build_proponent_prompt("Why is the sky blue?", domain="Science")
    assert "[Domain: Science]" in p
    assert "Why is the sky blue?" in p


def test_build_proponent_prompt_omits_general_domain():
    p = build_proponent_prompt("Q", domain="General")
    assert "[Domain:" not in p


def test_build_critic_prompt_sanitises_inputs():
    # Embed control chars that should be stripped before the prompt is built
    dirty_q = "What is X\x01?"
    dirty_p = "Answer\x07."
    out = build_critic_prompt(dirty_q, dirty_p)
    assert "\x01" not in out
    assert "\x07" not in out


def test_build_evaluation_prompt_truncates_long_response():
    huge = "x" * 20000
    out = build_evaluation_prompt("Q?", huge)
    # The response section is sanitised at 8000 chars max
    assert len(out) < 12000
    assert out.endswith("clarity.")
