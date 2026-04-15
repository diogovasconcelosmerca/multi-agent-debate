# Methodology

## Research Question

> Does a structured multi-agent debate among LLM-based agents produce higher-quality responses than a single-agent approach, as measured by coherence, reasoning depth, completeness, and clarity?

## Hypothesis

**H1**: Multi-agent debate responses will score higher than single-agent responses on at least 3 of 4 evaluation dimensions (coherence, reasoning depth, completeness, clarity), particularly for complex questions involving ethical dilemmas, planning, and multi-faceted reasoning.

**H0** (null): There is no significant difference in response quality between single-agent and multi-agent debate approaches.

## Experimental Design

### Independent Variable

The response generation method:
- **Baseline** — single agent (Proponent persona) generates one response
- **Debate** — three agents (Proponent → Critic → Proponent revision → Judge) generate a debated response

### Dependent Variables

1. **Coherence** (1–5) — logical consistency and organisation
2. **Reasoning Depth** (1–5) — depth of multi-step reasoning
3. **Completeness** (1–5) — coverage of relevant aspects
4. **Clarity** (1–5) — readability and communication quality

### Control Variables

- Same model for all agents and evaluation
- Same temperature setting
- Same system prompt base (Proponent) for both baseline and debate Agent A
- Same question set across conditions

## Evaluation Methods

### LLM-as-Judge

The primary evaluation method uses the same LLM to score responses on the four dimensions. This approach is based on Zheng et al. (2023), who demonstrated that LLM judges correlate well with human preferences.

**Configuration**: temperature = 0.2 (for consistency), structured JSON output, score range 1–5.

**Limitations**:
- **Self-evaluation bias**: the model may favour its own style regardless of actual quality
- **Position bias**: the order of presentation can affect scores
- **Inconsistency**: small models may produce variable scores across runs
- **Scale compression**: models tend to avoid extreme scores (1 or 5)

### Heuristic Metrics

Complementary objective metrics that require no LLM evaluation:

| Metric | Description | Rationale |
|--------|-------------|-----------|
| Word count | Number of words in the response | Proxy for thoroughness |
| Response length | Character count | Raw output volume |
| Unique concepts | Distinct non-stop-word terms (>4 chars) | Proxy for conceptual breadth |

### Timing Metrics

| Metric | Description |
|--------|-------------|
| Baseline latency | Wall-clock time for single-agent response |
| Debate latency | Total wall-clock time for all debate steps |
| Per-step timing | Individual timing for proposal, critique, revision, judgment |

## Question Categories

Questions are drawn from domains where reasoning depth matters:

| Domain | Rationale | Example |
|--------|-----------|---------|
| Ethics | Requires weighing competing values | "Should AI be used in criminal sentencing?" |
| Philosophy | Demands abstract reasoning | "Does free will exist?" |
| Science | Needs factual accuracy + explanation | "Explain quantum entanglement" |
| Planning | Involves multi-step strategy | "Design a carbon-neutral city plan" |
| Problem Solving | Requires trade-off analysis | "How to reduce misinformation without censorship?" |

## Comparison Framework

For each experiment, the system computes:

1. **Per-dimension scores** for both baseline and debate
2. **Deltas** (debate − baseline) for each dimension
3. **Winner determination**: whichever mode wins more dimensions

Aggregated across experiments:
- Mean scores per dimension per mode
- Score distributions (box plots)
- Win rate (% of experiments where debate > baseline)
- Latency ratio (debate time / baseline time)

## Limitations

1. **Single evaluator model**: Using the same model for generation and evaluation introduces bias. Ideally, a stronger external model or human evaluators would assess quality.

2. **Small model capabilities**: Local models (7B–14B parameters) have limited reasoning ability. Results may differ significantly with larger models.

3. **Non-deterministic output**: Even with fixed temperature, LLM outputs vary between runs. Statistical significance requires multiple runs per question.

4. **Prompt sensitivity**: Results depend heavily on prompt design. Different prompt formulations could yield different outcomes.

5. **Limited metric objectivity**: LLM-as-judge scores are subjective by nature. Heuristic metrics (word count, concepts) are crude proxies.

6. **No ground truth**: For open-ended questions, there is no definitive correct answer to compare against.

## References

- Du, Y., Li, S., Torralba, A., Tenenbaum, J. B., & Mordatch, I. (2023). _Improving Factuality and Reasoning in Language Models through Multiagent Debate_. arXiv:2305.14325.
- Liang, T., He, Z., Jiao, W., et al. (2023). _Encouraging Divergent Thinking in Large Language Models through Multi-Agent Debate_. arXiv:2305.19118.
- Zheng, L., Chiang, W.-L., Sheng, Y., et al. (2023). _Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena_. NeurIPS 2023.
- Chan, C., Chen, W., Su, Y., et al. (2023). _ChatEval: Towards Better LLM-based Evaluators through Multi-Agent Debate_. arXiv:2308.07201.
