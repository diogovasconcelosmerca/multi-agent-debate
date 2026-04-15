# Architecture

## System Overview

The Multi-Agent Debate System follows a modular, layered architecture designed for clarity, testability, and academic presentation.

```
┌─────────────────────────────────────────────────────┐
│                 Streamlit Interface                  │
│   app.py  │  Interactive Chat  │  Runner  │  Dashboard │
├─────────────────────────────────────────────────────┤
│              Application Logic Layer                │
│   baseline_engine.py  │  debate_engine.py           │
│   evaluator.py        │  storage.py                 │
├─────────────────────────────────────────────────────┤
│              Foundation Layer                       │
│   ollama_client.py  │  prompts.py  │  config.py     │
├─────────────────────────────────────────────────────┤
│              External Service                       │
│   Ollama (local LLM inference)                      │
└─────────────────────────────────────────────────────┘
```

## Component Descriptions

### Foundation Layer

| Module | Responsibility |
|--------|---------------|
| `config.py` | Centralised constants — paths, defaults, model settings, evaluation dimensions |
| `ollama_client.py` | HTTP wrapper around Ollama's REST API (`/api/generate`, `/api/tags`) |
| `prompts.py` | All prompt templates and builder functions for every agent |
| `utils.py` | Small utilities — Timer, timestamp formatting, heuristic metrics |

### Application Logic Layer

| Module | Responsibility |
|--------|---------------|
| `baseline_engine.py` | Runs a single LLM call using the Proponent persona |
| `debate_engine.py` | Orchestrates the multi-agent debate flow with callback support |
| `evaluator.py` | LLM-as-judge scoring + heuristic metrics + comparison logic |
| `storage.py` | JSON persistence per experiment + CSV summary index |

### Interface Layer

| Page | Responsibility |
|------|---------------|
| `app.py` | Entry point, sidebar configuration, welcome page |
| `1_Interactive_Chat.py` | Real-time single question Q&A with debate visualisation |
| `2_Experiment_Runner.py` | Batch execution with progress tracking |
| `3_Results_Dashboard.py` | Charts, tables, filtering, CSV export |

## Agent Architecture

### Debate Flow

```
User Question
     │
     ├──── Baseline Path ────────────────────────► Single Response
     │
     └──── Debate Path
              │
              ▼
         Agent A: Proposal  (system: PROPONENT_SYSTEM)
              │
              ▼
         Agent B: Critique  (system: CRITIC_SYSTEM)
              │
              ▼
         Agent A: Revision  (system: PROPONENT_SYSTEM)
              │
              ▼
         Agent C: Judgment  (system: JUDGE_SYSTEM)
              │
              ▼
         Final Debate Response
```

### Multi-Round Extension

For `rounds > 1`, the propose→critique→revise cycle repeats. Each subsequent round uses the previous revision as the new starting proposal. The Judge only sees the final round's data to avoid context window overflow.

## Design Decisions

### 1. No orchestration frameworks

We deliberately avoid LangChain, LangGraph, AutoGen, and similar frameworks. The debate logic is approximately 80 lines of Python in `debate_engine.py`. This makes the system:
- Easy to understand and explain in an academic context
- Free from framework-specific abstractions
- Simple to debug and modify

### 2. Non-streaming LLM calls

We use `stream: false` in Ollama API calls. This simplifies:
- Timing measurement (single response, not token-by-token)
- Error handling (one request/response cycle)
- Testing (predictable output format)

Streaming can be added in v2 for better UX.

### 3. Callback pattern for UI updates

`debate_engine.run_debate()` accepts an optional `on_step` callback. This allows the Streamlit pages to update in real time without the engine importing or depending on Streamlit. Clean separation of concerns.

### 4. JSON + CSV persistence

Each experiment is saved as a self-contained JSON file (complete data, easy to inspect). A CSV summary is maintained in parallel for fast DataFrame loading in the dashboard. This avoids the complexity of a database while keeping data accessible.

### 5. LLM-as-judge evaluation

We use the same model to evaluate responses — a well-established technique (Zheng et al., 2023). Known limitations:
- Self-evaluation bias (the model may favour its own style)
- Inconsistency with small models

Mitigations: low temperature (0.2), score clamping, JSON validation, heuristic fallback.

### 6. Fair baseline comparison

The baseline uses the same Proponent system prompt as Agent A in the debate. This ensures the baseline and debate start from the same "expert" persona, making the comparison fair.

## Data Flow

```
User Input → Sidebar Config → Session State
                                    │
                    ┌───────────────┼───────────────┐
                    ▼               ▼               ▼
              run_baseline()   run_debate()    (parallel)
                    │               │
                    ▼               ▼
              baseline_result  debate_result
                    │               │
                    └───────┬───────┘
                            ▼
                    compare_responses()
                            │
                            ▼
                    evaluation_result
                            │
                            ▼
                    save_result() → JSON + CSV
```
