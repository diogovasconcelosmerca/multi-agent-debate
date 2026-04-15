# User Guide

## Prerequisites

Before using the application, ensure you have:

1. **Python 3.11+** installed
2. **Ollama** installed and running (`ollama serve`)
3. **At least one model** pulled (e.g., `ollama pull llama3.2`)
4. **Dependencies** installed (`pip install -r requirements.txt`)

## Launching the Application

```bash
cd multi_agent_debate
streamlit run app.py
```

The app opens in your browser at `http://localhost:8501`.

## Sidebar Configuration

The sidebar appears on every page and controls all experiment parameters:

| Setting | Description | Recommended |
|---------|-------------|-------------|
| **Model** | The Ollama model to use | Start with a 7B model (llama3.2, mistral) for faster results |
| **Temperature** | Controls randomness (0 = deterministic, 2 = very random) | 0.7 for general use, 0.3 for more focused answers |
| **Debate rounds** | Number of propose→critique→revise cycles | 1 for quick tests, 2 for deeper analysis |
| **Task domain** | Category of the question | Helps the Proponent agent contextualise its answer |

## Interactive Chat

This is the main page for asking individual questions.

### Step by step

1. **Type your question** in the text area
2. Choose an action:
   - **Run Baseline Only** — generates a single-agent response
   - **Run Debate Only** — runs the full multi-agent debate
   - **Run Both & Compare** — runs both and shows evaluation metrics
3. **Watch the debate** unfold in real time (debate steps appear as they complete)
4. **Review results**:
   - Side-by-side comparison of baseline and debate responses
   - Expandable sections showing each debate step
   - Evaluation scores table with deltas
   - Heuristic metrics (word count, unique concepts)
5. **Save the experiment** by clicking the save button

### Tips for good questions

The system works best with questions that:
- Have multiple valid perspectives (ethical dilemmas)
- Require deep reasoning (philosophical questions)
- Involve trade-offs (planning, policy)
- Are open-ended (not simple factual lookups)

### Example questions

- _"What are the ethical implications of using AI in criminal sentencing?"_
- _"Should autonomous vehicles prioritize passenger or pedestrian safety?"_
- _"Design a strategy for a small city to become carbon-neutral in 15 years."_
- _"Does free will exist, or are all human decisions determined by prior causes?"_

## Experiment Runner

Use this page to run multiple questions in batch.

1. Choose **Sample questions** (from `data/inputs/sample_questions.json`) or **Custom list**
2. Click **Run all experiments**
3. Watch progress — each experiment is saved automatically as it completes
4. Review the summary when done

## Results Dashboard

This page visualises all saved experiment results.

### Charts available

- **Average scores** — grouped bar chart comparing baseline vs debate
- **Score distributions** — box plots showing variance
- **Latency comparison** — bar chart of execution times

### Filtering

Use the sidebar filters to narrow results by model or domain.

### Exporting

Click **Download results as CSV** to get a spreadsheet of all experiments.

## Understanding the Evaluation

### LLM-Judge Scores (1–5)

| Dimension | What it measures |
|-----------|-----------------|
| **Coherence** | Logical consistency, well-organised structure |
| **Reasoning Depth** | Multi-step reasoning, depth of analysis |
| **Completeness** | Coverage of all important aspects |
| **Clarity** | Readability, ease of understanding |

### Heuristic Metrics

| Metric | What it indicates |
|--------|-------------------|
| **Word count** | Response thoroughness |
| **Unique concepts** | Breadth of ideas covered |

### Winner Determination

The system counts how many dimensions the debate scores higher than the baseline. If debate wins more dimensions, it is declared the winner (and vice versa).

## Troubleshooting

| Problem | Solution |
|---------|----------|
| "Ollama not reachable" | Run `ollama serve` in a terminal |
| No models in dropdown | Run `ollama pull llama3.2` (or another model) |
| Slow responses | Use a smaller model, or increase `GENERATE_TIMEOUT` in `core/config.py` |
| JSON parse errors in evaluation | Normal with small models — the system falls back to default scores |
| Empty dashboard | Run some experiments first on the Interactive Chat or Experiment Runner page |
