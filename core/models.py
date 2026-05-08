"""
Pydantic schemas for every payload that crosses an MADS boundary.

These models are the *contract* between layers. Every dict that flows
between the engines, the storage layer, and the UI is round-tripped
through one of these classes so we get:

  * runtime validation of LLM-produced output (scores must be 1–5,
    word counts must be non-negative, dimensions must be the canonical
    four, etc.);
  * a single source of truth for field names — refactors that drop or
    rename a field will fail loudly in tests and CI rather than at the
    UI;
  * cheap JSON serialisation via `.model_dump_json()` for the storage
    layer and the structured-logging telemetry stream.

Pydantic v2 is required (declared in `requirements.txt`). All models
are explicitly opt-in to extra fields via `model_config` so an upstream
LLM that hallucinates a key cannot silently corrupt persisted data.
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, NonNegativeInt, field_validator

from core.config import EVALUATION_DIMENSIONS

Backend = Literal["ollama", "groq", "gemini", "openrouter"]
Winner = Literal["debate", "baseline", "tie"]


# ---------------------------------------------------------------------------
# Telemetry
# ---------------------------------------------------------------------------


class TokenUsage(BaseModel):
    """Approximate token accounting based on character counts.

    Real token counts require provider-specific tokenisers; we use a
    deterministic char-based heuristic so the same call costed against
    Ollama and Groq yields comparable numbers. Multiplying by 0.25
    (≈ chars per token for English text) gives a usable signal for the
    dashboard without adding tiktoken to the dependency tree.
    """

    prompt_chars: NonNegativeInt
    response_chars: NonNegativeInt

    @property
    def approx_prompt_tokens(self) -> int:
        return self.prompt_chars // 4

    @property
    def approx_response_tokens(self) -> int:
        return self.response_chars // 4

    @property
    def approx_total_tokens(self) -> int:
        return self.approx_prompt_tokens + self.approx_response_tokens


class LlmCallLog(BaseModel):
    """One structured log line per LLM call. Persisted to JSONL."""

    model_config = ConfigDict(extra="forbid")

    timestamp: datetime
    backend: Backend
    model: str
    role: str  # "proponent" | "critic" | "judge" | "evaluator" | "baseline"
    elapsed_ms: NonNegativeInt
    status: Literal["ok", "error", "timeout"]
    usage: TokenUsage
    error: str | None = None


# ---------------------------------------------------------------------------
# Evaluation
# ---------------------------------------------------------------------------


class LlmScores(BaseModel):
    """1–5 scores produced by the LLM-as-judge evaluator."""

    model_config = ConfigDict(extra="ignore")  # tolerate hallucinated keys

    coherence: int = Field(ge=1, le=5)
    reasoning_depth: int = Field(ge=1, le=5)
    completeness: int = Field(ge=1, le=5)
    clarity: int = Field(ge=1, le=5)

    def as_dict(self) -> dict[str, int]:
        return {dim: getattr(self, dim) for dim in EVALUATION_DIMENSIONS}


class Heuristics(BaseModel):
    word_count: NonNegativeInt
    response_length: NonNegativeInt
    unique_concepts: NonNegativeInt


class Evaluation(BaseModel):
    baseline_scores: dict[str, int]
    debate_scores: dict[str, int]
    baseline_heuristics: Heuristics
    debate_heuristics: Heuristics
    deltas: dict[str, int]
    winner: Winner

    @field_validator("baseline_scores", "debate_scores", "deltas")
    @classmethod
    def _has_all_dimensions(cls, v: dict[str, int]) -> dict[str, int]:
        missing = [d for d in EVALUATION_DIMENSIONS if d not in v]
        if missing:
            raise ValueError(f"missing evaluation dimensions: {missing}")
        return v


# ---------------------------------------------------------------------------
# Engine outputs
# ---------------------------------------------------------------------------


class BaselineResult(BaseModel):
    response: str
    elapsed_seconds: float = Field(ge=0)


class RoundData(BaseModel):
    round: int = Field(ge=1)
    proposal: str
    proposal_time: float = Field(ge=0)
    critique: str
    critique_time: float = Field(ge=0)
    revision: str
    revision_time: float = Field(ge=0)


class DebateResult(BaseModel):
    rounds: list[RoundData]
    judgment: str
    judgment_time: float = Field(ge=0)
    total_elapsed_seconds: float = Field(ge=0)


class ExperimentRecord(BaseModel):
    """The canonical persisted unit — what gets written to data/outputs/."""

    model_config = ConfigDict(extra="ignore")

    experiment_id: str
    timestamp: str
    question: str
    domain: str
    model: str
    temperature: float = Field(ge=0, le=2)
    debate_rounds: int = Field(ge=1)
    baseline: BaselineResult
    debate: DebateResult
    evaluation: Evaluation
