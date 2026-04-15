"""
Persistence layer — save and load experiment results.

Each experiment is stored as a single JSON file in data/outputs/.
A CSV summary index in data/results/summary.csv is maintained for
fast loading into pandas / the dashboard page.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import pandas as pd

from core.config import OUTPUTS_DIR, RESULTS_DIR

logger = logging.getLogger(__name__)

# Columns kept in the lightweight CSV summary
_SUMMARY_COLUMNS = [
    "experiment_id",
    "timestamp",
    "question",
    "domain",
    "model",
    "temperature",
    "debate_rounds",
    "baseline_time",
    "debate_time",
    "baseline_coherence",
    "baseline_reasoning_depth",
    "baseline_completeness",
    "baseline_clarity",
    "debate_coherence",
    "debate_reasoning_depth",
    "debate_completeness",
    "debate_clarity",
]


# ------------------------------------------------------------------
# Save
# ------------------------------------------------------------------

def save_result(result: dict[str, Any]) -> Path:
    """
    Persist a full experiment result.

    1. Write the complete dict as a pretty-printed JSON file.
    2. Append a summary row to the CSV index.

    Returns the path to the saved JSON file.
    """
    exp_id = result["experiment_id"]
    json_path = OUTPUTS_DIR / f"{exp_id}.json"

    # Full JSON
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    # CSV summary row
    _append_summary_row(result)

    logger.info("Saved experiment %s to %s", exp_id, json_path)
    return json_path


def _append_summary_row(result: dict[str, Any]) -> None:
    """Extract a flat summary row and append it to the CSV index."""
    evaluation = result.get("evaluation", {})
    b_scores = evaluation.get("baseline_scores", {})
    d_scores = evaluation.get("debate_scores", {})

    row = {
        "experiment_id": result.get("experiment_id"),
        "timestamp": result.get("timestamp"),
        "question": result.get("question", "")[:200],
        "domain": result.get("domain"),
        "model": result.get("model"),
        "temperature": result.get("temperature"),
        "debate_rounds": result.get("debate_rounds"),
        "baseline_time": result.get("baseline", {}).get("elapsed_seconds"),
        "debate_time": result.get("debate", {}).get("total_elapsed_seconds"),
        "baseline_coherence": b_scores.get("coherence"),
        "baseline_reasoning_depth": b_scores.get("reasoning_depth"),
        "baseline_completeness": b_scores.get("completeness"),
        "baseline_clarity": b_scores.get("clarity"),
        "debate_coherence": d_scores.get("coherence"),
        "debate_reasoning_depth": d_scores.get("reasoning_depth"),
        "debate_completeness": d_scores.get("completeness"),
        "debate_clarity": d_scores.get("clarity"),
    }

    csv_path = RESULTS_DIR / "summary.csv"
    df_row = pd.DataFrame([row])

    if csv_path.exists():
        df_row.to_csv(csv_path, mode="a", header=False, index=False)
    else:
        df_row.to_csv(csv_path, index=False)


# ------------------------------------------------------------------
# Load
# ------------------------------------------------------------------

def load_result(experiment_id: str) -> dict[str, Any]:
    """Load a single experiment result by its ID."""
    json_path = OUTPUTS_DIR / f"{experiment_id}.json"
    with open(json_path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_all_results() -> list[dict[str, Any]]:
    """Load every experiment JSON, sorted by timestamp (newest first)."""
    results = []
    for path in sorted(OUTPUTS_DIR.glob("*.json"), reverse=True):
        try:
            with open(path, "r", encoding="utf-8") as f:
                results.append(json.load(f))
        except (json.JSONDecodeError, OSError) as exc:
            logger.warning("Skipping corrupt file %s: %s", path, exc)
    return results


def load_summary_df() -> pd.DataFrame:
    """Load the CSV summary index as a DataFrame."""
    csv_path = RESULTS_DIR / "summary.csv"
    if not csv_path.exists():
        return pd.DataFrame(columns=_SUMMARY_COLUMNS)
    return pd.read_csv(csv_path)


def export_results_csv(results: list[dict[str, Any]], path: Path) -> Path:
    """Export a list of result dicts to a flat CSV file at the given path."""
    rows = []
    for r in results:
        evaluation = r.get("evaluation", {})
        b_scores = evaluation.get("baseline_scores", {})
        d_scores = evaluation.get("debate_scores", {})
        rows.append({
            "experiment_id": r.get("experiment_id"),
            "timestamp": r.get("timestamp"),
            "question": r.get("question"),
            "domain": r.get("domain"),
            "model": r.get("model"),
            "baseline_response": r.get("baseline", {}).get("response", ""),
            "debate_response": r.get("debate", {}).get("judgment", ""),
            "baseline_time": r.get("baseline", {}).get("elapsed_seconds"),
            "debate_time": r.get("debate", {}).get("total_elapsed_seconds"),
            **{f"baseline_{k}": v for k, v in b_scores.items()},
            **{f"debate_{k}": v for k, v in d_scores.items()},
        })
    df = pd.DataFrame(rows)
    df.to_csv(path, index=False)
    return path
