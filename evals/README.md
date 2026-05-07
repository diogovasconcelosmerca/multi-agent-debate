# Evals — golden-dataset regression suite

`evals/run_eval.py` runs MADS against a small **golden dataset** of
questions and gates each response on three checks:

| Gate | What it catches |
|---|---|
| **Keyword coverage** | Drift / off-topic answers (response misses the expected concepts) |
| **Length floor** | Truncated stubs and one-line replies |
| **LLM-as-judge** | Subjective regressions the deterministic gates miss |

The deterministic gates are stable across runs; the judge step is
provided for richer signal during development and is opt-out via
`--no-judge`.

## Run it

```bash
# default: local Ollama
python evals/run_eval.py

# cloud — pick a backend and supply a key
GEMINI_API_KEY=AIza... python evals/run_eval.py --backend gemini

# fast iteration (no LLM-as-judge step)
python evals/run_eval.py --no-judge
```

Exits non-zero if any record fails the deterministic gates, so the
script is safe to wire into a pre-merge hook or a nightly job. We
deliberately do **not** run a live-model eval inside GitHub Actions —
it would burn free-tier quota on every PR; the unit tests in
`tests/` cover the surface that doesn't need a real LLM.

## Why this dataset?

The five records were chosen to span **different kinds of weakness**
that single-agent baselines tend to exhibit:

- `ethics_trolley` — gets the model to actually weigh competing
  frameworks instead of picking one and over-justifying it.
- `science_entropy` — cross-domain bridge (physics → software).
- `tech_caching` — engineering depth: do you know the failure modes,
  or just the term "caching"?
- `planning_career` — structured output (30/60/90), tests scaffolding.
- `philosophy_consciousness` — dual-side argument before commitment;
  the strongest debate-vs-baseline differentiator.

If you extend the dataset, keep entries **diverse** along this axis,
not redundant. Five well-chosen records discriminate better than
fifty similar ones.
