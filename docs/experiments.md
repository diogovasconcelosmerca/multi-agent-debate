# Experiments Guide

## Running Experiments

### Single Question (Interactive)

1. Launch the app: `streamlit run app.py`
2. Navigate to **Interactive Chat**
3. Configure model, temperature, and rounds in the sidebar
4. Enter a question and click **Run Both & Compare**
5. Review the debate process and evaluation metrics
6. Click **Save this experiment** to persist the result

### Batch Experiments

1. Navigate to **Experiment Runner**
2. Choose a question source:
   - **Sample questions**: loads from `data/inputs/sample_questions.json`
   - **Custom list**: enter questions manually (one per line)
3. Click **Run all experiments**
4. Results are auto-saved as they complete

### Custom Question Sets

Create a JSON file in `data/inputs/` with this format:

```json
[
  {"question": "Your question here", "domain": "Ethics"},
  {"question": "Another question", "domain": "Science"}
]
```

## Viewing Results

### Dashboard

Navigate to **Results Dashboard** to see:
- Average scores comparison (grouped bar chart)
- Score distributions (box plots)
- Latency comparison
- Full data table with all experiments
- CSV export button

### Raw Data

- Individual experiment JSONs: `data/outputs/exp_*.json`
- Summary CSV: `data/results/summary.csv`

## Experiment Variables

### Recommended experiments to run

| Experiment | Variable | Values | Goal |
|------------|----------|--------|------|
| Model comparison | model | llama3.2, mistral, qwen2.5 | Compare debate effectiveness across models |
| Temperature sweep | temperature | 0.3, 0.5, 0.7, 1.0 | Effect of randomness on debate quality |
| Round count | rounds | 1, 2, 3 | Diminishing returns from additional rounds |
| Domain analysis | domain | Ethics, Science, Planning | Which domains benefit most from debate |

### Controlling for variance

Since LLM outputs are non-deterministic, run each configuration **at least 3 times** per question to assess consistency. The dashboard aggregates results, making it easy to compare means and distributions.

## Interpreting Results

### Score deltas

- **Positive delta** (debate > baseline): the debate improved the response
- **Zero delta**: no measurable difference
- **Negative delta** (baseline > debate): the debate produced a worse response

### Expected patterns

Based on the literature (Du et al., 2023):
- Debate tends to improve **completeness** and **reasoning depth** more than clarity
- Debate is most beneficial for complex, multi-faceted questions
- Simple factual questions may not benefit significantly
- More debate rounds show diminishing returns after round 2

### Latency trade-off

Debate requires 4+ LLM calls vs 1 for baseline. Expect:
- 1-round debate: ~4x baseline latency
- 2-round debate: ~7x baseline latency
- The quality improvement must justify this computational cost

## Future Benchmark Ideas

1. **TruthfulQA** — test whether debate reduces hallucination on factual questions
2. **MMLU subsets** — compare accuracy on multi-choice reasoning tasks
3. **BBH (BIG-Bench Hard)** — challenging reasoning tasks where debate may help
4. **Custom ethical dilemmas** — scenarios with no clear right answer, evaluated by humans
5. **Cross-model debate** — use different models for different agents
6. **Human evaluation** — blind side-by-side comparison by human raters
