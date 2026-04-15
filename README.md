# MADS -- Multi-Agent Debate System

[![Streamlit](https://img.shields.io/badge/Streamlit-1.30+-FF4B4B?logo=streamlit&logoColor=white)](https://streamlit.io)
[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?logo=python&logoColor=white)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Ollama](https://img.shields.io/badge/Ollama-Local%20LLMs-000000?logo=data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIyNCIgaGVpZ2h0PSIyNCIgdmlld0JveD0iMCAwIDI0IDI0Ij48Y2lyY2xlIGN4PSIxMiIgY3k9IjEyIiByPSIxMCIgZmlsbD0id2hpdGUiLz48L3N2Zz4=)](https://ollama.com)
[![Groq](https://img.shields.io/badge/Groq-Cloud%20Fallback-F55036)](https://console.groq.com)

An experimental platform that compares **single-agent** LLM responses against **multi-agent debate** responses, measuring whether structured argumentation between AI agents produces higher-quality answers.

Built as an academic research tool with a production-quality UI.

---

## Hypothesis

> *Does a structured propose-critique-revise-judge pipeline among multiple AI agents produce measurably better responses than a single agent answering the same question?*

MADS tests this by running both approaches side-by-side and evaluating them with LLM-as-Judge scoring across four dimensions.

---

## Demo

| Interactive Chat | Results Dashboard |
|:---:|:---:|
| ![Chat View](docs/assets/chat_preview.png) | ![Dashboard](docs/assets/dashboard_preview.png) |

> To add your own screenshots: run the app, take screenshots, and save them in `docs/assets/`.

---

## Architecture

```
                          +------------------+
                          |   User Question  |
                          +--------+---------+
                                   |
                    +--------------+--------------+
                    |                             |
            +-------v-------+           +---------v---------+
            |   BASELINE    |           |   DEBATE PIPELINE |
            | (Single Agent)|           |                   |
            +-------+-------+           |  Agent A: Propose |
                    |                   |        |          |
                    |                   |  Agent B: Critique |
                    |                   |        |          |
                    |                   |  Agent A: Revise   |
                    |                   |        |          |
                    |                   |  Agent C: Judge    |
                    +-------+-----------+---------+---------+
                            |                     |
                    +-------v---------------------v-------+
                    |         LLM-as-Judge Evaluator       |
                    |  Coherence | Reasoning | Completeness |
                    |            | Clarity   | Heuristics   |
                    +-------------------------------------+
```

### Agent Roles

| Agent | Role | Behaviour |
|-------|------|-----------|
| **Agent A** | Proponent | Generates the best initial answer, then revises based on critique |
| **Agent B** | Critic | Identifies logical flaws, biases, missing perspectives, and risks |
| **Agent C** | Judge | Synthesises proposal + critique + revision into a balanced final answer |

### Evaluation

Each response is scored 1-5 on four dimensions by an LLM evaluator:

- **Coherence** -- logical consistency and organisation
- **Reasoning Depth** -- multi-step, evidence-based thinking
- **Completeness** -- coverage of all relevant aspects
- **Clarity** -- readability and structure

Supplemented by heuristic metrics: word count, response length, and unique concept count.

---

## Features

- **Chat-style debate view** -- watch agents message each other in real time, like a group chat
- **Step progress indicator** -- visual pipeline showing which stage the debate is at
- **Animated transitions** -- fade-in messages, typing indicators, hover micro-interactions
- **Glass-morphism UI** -- modern frosted-glass aesthetic with dark theme
- **Tabbed comparison** -- switch between baseline and debate results
- **Radar chart** -- visual score comparison across all dimensions
- **Batch experiments** -- run multiple questions and auto-save results
- **Interactive dashboard** -- Plotly charts, box plots, latency analysis, CSV export
- **Dual backend** -- run locally with Ollama or in the cloud with Groq (free tier)
- **Portfolio-ready** -- deployable to Streamlit Community Cloud

---

## Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| Frontend | Streamlit | Interactive web UI |
| LLM (local) | Ollama | Free, private, offline inference |
| LLM (cloud) | Groq API | Free tier, fast cloud inference |
| Visualisation | Plotly + Custom SVG | Charts, radar diagrams |
| Data | Pandas + JSON/CSV | Persistence and analysis |
| Language | Python 3.11+ | Core logic |

---

## Quick Start

### Option A: Local with Ollama (fully offline)

```bash
# 1. Install Ollama
#    https://ollama.com/download

# 2. Pull a model
ollama pull llama3.2

# 3. Start Ollama
ollama serve

# 4. Clone and run
git clone https://github.com/diogovasconcelosmerca/multi-agent-debate.git
cd multi-agent-debate
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # macOS/Linux
pip install -r requirements.txt
streamlit run app.py
```

### Option B: Cloud with Groq (no install needed)

```bash
# 1. Get a free API key at https://console.groq.com

# 2. Clone and run
git clone https://github.com/diogovasconcelosmerca/multi-agent-debate.git
cd multi-agent-debate
pip install -r requirements.txt
streamlit run app.py

# 3. In the sidebar, select "Groq (cloud)" and paste your API key
```

### Option C: Streamlit Community Cloud (live demo)

1. Fork this repo on GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Deploy `app.py` from your fork
4. Add `GROQ_API_KEY` in the Streamlit Secrets settings
5. Share the link in your portfolio

---

## Project Structure

```
multi_agent_debate/
|-- app.py                          # Streamlit entry point + sidebar config
|-- pages/
|   |-- 1_Interactive_Chat.py       # Chat-style debate view with all upgrades
|   |-- 2_Experiment_Runner.py      # Batch experiment runner
|   +-- 3_Results_Dashboard.py      # Results visualisation + radar chart
|-- core/
|   |-- config.py                   # Centralised configuration
|   |-- llm_client.py              # Unified LLM client (Ollama + Groq)
|   |-- ollama_client.py            # Backward-compatibility shim
|   |-- prompts.py                  # All agent prompt templates
|   |-- baseline_engine.py          # Single-agent engine
|   |-- debate_engine.py            # Multi-agent debate orchestration
|   |-- evaluator.py                # LLM-judge + heuristic scoring
|   |-- storage.py                  # JSON/CSV persistence layer
|   |-- theme.py                    # Design system (CSS, components, SVGs)
|   +-- utils.py                    # Timer, formatting, text utilities
|-- data/
|   |-- inputs/sample_questions.json  # 15 curated questions across 7 domains
|   |-- outputs/                      # Saved experiment JSONs (gitignored)
|   +-- results/                      # CSV summary index (gitignored)
|-- docs/
|   |-- architecture.md
|   |-- methodology.md
|   |-- experiments.md
|   +-- user_guide.md
|-- .streamlit/
|   +-- config.toml                 # Streamlit theme configuration
|-- requirements.txt
|-- LICENSE
+-- README.md
```

---

## How It Works

### 1. Debate Pipeline

```python
# Simplified flow (see core/debate_engine.py for full implementation)

proposal  = agent_a.generate(question)           # Step 1: Propose
critique  = agent_b.generate(question, proposal)  # Step 2: Critique
revision  = agent_a.generate(question, proposal, critique)  # Step 3: Revise
judgment  = agent_c.generate(question, proposal, critique, revision)  # Step 4: Judge
```

### 2. Evaluation

```python
# LLM-as-Judge scores each response independently (see core/evaluator.py)
baseline_scores = evaluate(question, baseline_response)   # {coherence: 3, ...}
debate_scores   = evaluate(question, debate_response)     # {coherence: 4, ...}
deltas          = debate_scores - baseline_scores          # {coherence: +1, ...}
```

### 3. Dual Backend

The `LlmClient` interface abstracts over Ollama and Groq:

```python
# Both clients expose the same API
client = OllamaClient()          # Local inference via Ollama
client = GroqClient(api_key)     # Cloud inference via Groq

# The engines don't care which backend is used
result = run_debate(question, model, client=client)
```

---

## Configuration

| Setting | Default | Description |
|---------|---------|-------------|
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama server address |
| `GROQ_API_KEY` | (env var) | Free API key from console.groq.com |
| `DEFAULT_MODEL` | `llama3.2` | Default model for Ollama |
| `GROQ_DEFAULT_MODEL` | `llama-3.3-70b-versatile` | Default model for Groq |
| `DEFAULT_TEMPERATURE` | `0.7` | Sampling temperature |
| `MAX_DEBATE_ROUNDS` | `3` | Maximum propose-critique-revise cycles |
| `GENERATE_TIMEOUT` | `120s` | Timeout per LLM call |

---

## Sample Results

After running experiments, the dashboard shows:

- **Score comparison** bar charts (baseline vs debate per dimension)
- **Radar chart** overlaying both score profiles
- **Distribution** box plots across experiments
- **Latency** analysis (baseline is faster; debate is deeper)
- **Full data table** with CSV export

---

## Academic Context

This project explores research questions in:

- **Agentic AI** -- multi-agent architectures and inter-agent coordination
- **Reasoning improvement** -- whether structured debate enhances LLM reasoning quality
- **AI alignment** -- using adversarial critique to reduce errors and biases
- **Experimental methodology** -- systematic A/B comparison with quantitative metrics
- **LLM evaluation** -- LLM-as-Judge reliability and heuristic metric correlation

### Key References

- Du, Y. et al. (2023). *Improving Factuality and Reasoning in Language Models through Multiagent Debate*. arXiv:2305.14325
- Liang, T. et al. (2023). *Encouraging Divergent Thinking in Large Language Models through Multi-Agent Debate*. arXiv:2305.19118
- Zheng, L. et al. (2023). *Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena*. arXiv:2306.05685
- Chan, C. et al. (2023). *ChatEval: Towards Better LLM-based Evaluators through Multi-Agent Debate*. arXiv:2308.07201

---

## Deployment to Streamlit Cloud

1. Push this repo to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io) and sign in with GitHub
3. Select your repo, branch `main`, and main file `app.py`
4. In **Advanced settings > Secrets**, add:
   ```toml
   GROQ_API_KEY = "gsk_your_key_here"
   ```
5. Click **Deploy**

The app will auto-detect Groq when `GROQ_API_KEY` is set as a secret.

---

## Future Work

- Benchmark integration (MMLU, TruthfulQA, HumanEval)
- Multi-model debates (different LLMs for different agents)
- Human evaluation interface for side-by-side rating
- Token-level streaming for real-time response display
- Advanced metrics: semantic similarity, factual verification
- Persistent user sessions and experiment history

---

## License

MIT License. See [LICENSE](LICENSE) for details.

---

<p align="center">
  <sub>Built with Streamlit, Ollama, and Groq</sub>
</p>
