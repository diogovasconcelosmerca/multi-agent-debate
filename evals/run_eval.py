"""
Golden-dataset eval runner.

For every record in ``golden_dataset.json`` this script runs both the
single-agent baseline and the multi-agent debate, then scores each
output against three deterministic checks:

  1. **Keyword coverage** — fraction of ``expected_keywords`` present
     (case-insensitive) in the response. Catches regressions where an
     answer drifts off-topic.
  2. **Length floor** — response meets the dataset's
     ``expected_word_count_min``. Catches regressions where the model
     starts returning truncated stubs.
  3. **LLM-as-judge** — same evaluator the dashboard uses. Catches
     regressions in subjective quality even when the deterministic
     checks pass.

The runner exits non-zero if any record fails the deterministic gates.
That makes it suitable for both ad-hoc local use and CI smoke tests
(though full eval runs against a live model are typically out of scope
for hosted CI).

Usage:
    # against the local Ollama instance
    python evals/run_eval.py

    # specify a different backend / model
    BACKEND=gemini MODEL=gemini-2.0-flash GEMINI_API_KEY=... python evals/run_eval.py

    # only evaluate the deterministic gates (skip LLM-as-judge for speed)
    python evals/run_eval.py --no-judge
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

# Make `core.*` importable when running this file directly.
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.baseline_engine import run_baseline
from core.config import EVALUATION_DIMENSIONS
from core.debate_engine import run_debate
from core.evaluator import compare_responses
from core.llm_client import LlmConnectionError, get_client

DATASET = Path(__file__).resolve().parent / "golden_dataset.json"


def keyword_coverage(text: str, expected: list[str]) -> float:
    if not expected:
        return 1.0
    lc = text.lower()
    hits = sum(1 for kw in expected if kw.lower() in lc)
    return hits / len(expected)


def length_ok(text: str, floor: int) -> bool:
    return len(text.split()) >= floor


def main() -> int:
    parser = argparse.ArgumentParser(description="MADS golden-dataset eval runner.")
    parser.add_argument("--backend", default=os.environ.get("BACKEND", "ollama"))
    parser.add_argument("--model", default=os.environ.get("MODEL"))
    parser.add_argument("--rounds", type=int, default=1)
    parser.add_argument(
        "--no-judge", action="store_true",
        help="Skip the LLM-as-judge step (deterministic gates only).",
    )
    parser.add_argument(
        "--coverage-floor", type=float, default=0.5,
        help="Fail a record if keyword coverage is below this fraction.",
    )
    args = parser.parse_args()

    api_key = ""
    if args.backend == "groq":
        api_key = os.environ.get("GROQ_API_KEY", "")
    elif args.backend == "gemini":
        api_key = os.environ.get("GEMINI_API_KEY", "")

    try:
        client = get_client(args.backend, api_key)
    except LlmConnectionError as exc:
        print(f"  ✗ cannot construct client: {exc}", file=sys.stderr)
        return 2

    if not client.check_connection():
        print(
            f"  ✗ {args.backend} backend is not reachable. "
            "Skipping eval.", file=sys.stderr,
        )
        return 2

    model = args.model or _default_model_for(args.backend)
    records = json.loads(DATASET.read_text(encoding="utf-8"))

    print(f"Running {len(records)} records on {args.backend}/{model}, "
          f"rounds={args.rounds}, judge={'off' if args.no_judge else 'on'}\n")

    failures: list[str] = []
    summary = []

    for rec in records:
        print(f"=== {rec['id']} — {rec['domain']} ===")
        print(f"  Q: {rec['question'][:90]}...")

        # 1. Run baseline + debate
        b = run_baseline(rec["question"], model, 0.7, rec["domain"], client)
        d = run_debate(rec["question"], model, 0.7, args.rounds, rec["domain"], client)

        b_text = b["response"]
        d_text = d["judgment"]

        # 2. Deterministic gates
        b_cov = keyword_coverage(b_text, rec["expected_keywords"])
        d_cov = keyword_coverage(d_text, rec["expected_keywords"])
        b_len_ok = length_ok(b_text, rec["expected_word_count_min"])
        d_len_ok = length_ok(d_text, rec["expected_word_count_min"])

        # 3. LLM-as-judge (optional)
        winner = "—"
        avg_delta = 0.0
        if not args.no_judge:
            ev = compare_responses(rec["question"], b_text, d_text, model, client)
            winner = ev["winner"]
            avg_delta = sum(ev["deltas"][d] for d in EVALUATION_DIMENSIONS) / 4

        # 4. Report
        print(
            f"  baseline: cov={b_cov:.0%} len_ok={b_len_ok} t={b['elapsed_seconds']:.1f}s\n"
            f"  debate:   cov={d_cov:.0%} len_ok={d_len_ok} "
            f"t={d['total_elapsed_seconds']:.1f}s  winner={winner}  Δavg={avg_delta:+.2f}"
        )

        passed = (
            b_cov >= args.coverage_floor and d_cov >= args.coverage_floor
            and b_len_ok and d_len_ok
        )
        if not passed:
            failures.append(rec["id"])
            print("  ✗ FAIL\n")
        else:
            print("  ✓ PASS\n")

        summary.append({
            "id": rec["id"],
            "baseline_coverage": b_cov,
            "debate_coverage": d_cov,
            "baseline_words": len(b_text.split()),
            "debate_words": len(d_text.split()),
            "winner": winner,
            "avg_delta": round(avg_delta, 2),
        })

    print("=" * 60)
    print(f"Passed: {len(records) - len(failures)}/{len(records)}")
    if failures:
        print(f"Failed: {failures}")
        return 1
    print("All records passed deterministic gates.")
    return 0


def _default_model_for(backend: str) -> str:
    return {
        "ollama": "llama3.2",
        "groq": "llama-3.3-70b-versatile",
        "gemini": "gemini-2.0-flash",
    }[backend]


if __name__ == "__main__":
    raise SystemExit(main())
