# Contributing to MADS

Thanks for taking the time to read this. MADS is a small research-grade
codebase, so the bar for contributions is high in *intent* but low in
*ceremony*. The goal is to keep the project **legible, typed, and
tested** rather than feature-rich.

## Ground rules

1. **One concern per PR.** A clear title + a short description beats a
   thousand-line refactor. If you need to do groundwork before the
   real change, send the groundwork as its own PR first.
2. **Keep the layer contract.** UI code lives in `Home.py` / `pages/`.
   Engine, evaluator, storage, and telemetry live in `core/`. Pages
   may import `core`; `core` must never import from `pages` or
   `Home.py`.
3. **Validate at the boundary.** Anything that crosses a layer is a
   Pydantic model in `core/models.py`. LLM-produced JSON is no
   exception — see how `core/evaluator.py:_validate_scores` clamps
   1–5 and rejects unknown keys.
4. **No silent empty paths.** If a backend returns nothing, raise
   `LlmConnectionError` with a sentence the user can act on (see the
   Gemini handler in `core/llm_client.py`).

## Development setup

```bash
git clone https://github.com/diogovasconcelosmerca/multi-agent-debate.git
cd multi-agent-debate
python -m venv venv
. venv/Scripts/activate              # Windows; use `source venv/bin/activate` on Unix
pip install -e ".[dev]"              # runtime + dev deps from pyproject.toml
streamlit run Home.py                # run the app
```

## Before you push

```bash
ruff check .          # lint   (must pass)
ruff format --check . # format (currently soft-fail in CI)
mypy core             # types  (currently soft-fail in CI)
pytest -q             # 36 unit tests, runs in <2 s, no network
```

CI runs the same four commands on every push and PR.
[Workflow](.github/workflows/ci.yml).

## What's a good first issue?

- **More golden-dataset records** in `evals/golden_dataset.json`.
  Aim for diversity along the *kind of weakness* axis (see
  [evals/README.md](evals/README.md)) — five well-chosen records
  discriminate better than fifty similar ones.
- **A fourth backend.** OpenRouter, Together AI, and Hugging Face
  Inference all have free tiers. The contract is in `core/llm_client.py`:
  implement `generate / generate_json / list_models / check_connection`,
  add a branch in `get_client(...)`, and add an entry to the `BACKENDS`
  table in `core/config.py`. Wire it through `core/sidebar.py` the way
  Gemini is wired today.
- **Streaming responses.** The chat page already calls back per agent
  step; bringing token-level streaming into a single agent's bubble
  would be a satisfying UX upgrade. Start in `core/llm_client.py` —
  Ollama and Groq both support `stream=true`.

## What I'll *not* merge

- **Provider-coupled engines.** The point of MADS is that
  `run_baseline` and `run_debate` don't know which backend they're
  hitting. Don't push provider-specific behaviour into the engines.
- **Hidden mutable state.** If a function needs config, take it as
  an argument or read from `core.config`. Don't reach into
  `st.session_state` from `core/`; that file belongs to the UI.
- **Untyped LLM output.** No new code path that takes raw model output
  and persists it without going through a Pydantic model first.

## Reporting a bug

Open an issue with:
- the question you asked,
- the backend + model you were using,
- the exact error message (a screenshot of the chat page is fine —
  the new error UX shows the real cause inline), and
- one line on what you expected.

If you've hit a 429 or a quota issue from Groq / Gemini, that is
working as intended; the failure mode docs in
[README.md](README.md#why-three-backends) are the place to start.

## License

By contributing you agree your contribution is licensed under the
project's [MIT License](LICENSE).
