"""
Interactive Chat -- chat-style debate view with all visual upgrades.
"""

import sys
from pathlib import Path

import streamlit as st

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from core.baseline_engine import run_baseline
from core.debate_engine import run_debate
from core.evaluator import compare_responses
from core.llm_client import LlmConnectionError
from core.storage import save_result
from core.theme import (
    C,
    chat_message,
    favicon_uri,
    inject_premium_css,
    metric_card,
    page_header,
    radar_chart_html,
    section_header,
    step_indicator,
    typing_indicator,
    winner_banner,
)
from core.utils import format_timestamp, generate_experiment_id

st.set_page_config(page_title="MADS -- Chat", page_icon=favicon_uri(), layout="wide")
inject_premium_css()


def _s(key, default):
    return st.session_state.get(key, default)


def _get_client():
    """Retrieve the shared client from session state."""
    client = st.session_state.get("client")
    if client is None:
        st.error("No LLM backend connected. Go to the Home page and configure Ollama or Groq in the sidebar.")
        st.stop()
    return client


page_header("Interactive Chat", "Ask a question. Watch the agents debate. Compare results.")

# ---------------------------------------------------------------------------
# Input
# ---------------------------------------------------------------------------

question = st.text_area(
    "question",
    height=100,
    placeholder="Enter your question here...",
    label_visibility="collapsed",
)

st.markdown('<div style="height:4px;"></div>', unsafe_allow_html=True)
col_b, col_d, col_both = st.columns(3)
run_baseline_btn = col_b.button("Baseline Only", use_container_width=True)
run_debate_btn = col_d.button("Debate Only", use_container_width=True)
run_both_btn = col_both.button("Run Both", type="primary", use_container_width=True)

if not question and (run_baseline_btn or run_debate_btn or run_both_btn):
    st.warning("Enter a question first.")
    st.stop()

model = _s("model", "llama3.2")
temperature = _s("temperature", 0.7)
rounds = _s("debate_rounds", 1)
domain = _s("domain", "General")
client = _get_client()

# Pipeline step names
STEPS = ["Proposal", "Critique", "Revision", "Judgment"]

# ---------------------------------------------------------------------------
# Baseline
# ---------------------------------------------------------------------------

if run_baseline_btn or run_both_btn:
    if question:
        chat_message("You", "Question", question, align="right")
        with st.status("Running baseline...", expanded=False) as status:
            try:
                baseline_result = run_baseline(question, model, temperature, domain, client)
                status.update(label=f"Baseline -- {baseline_result['elapsed_seconds']:.1f}s", state="complete")
                st.session_state["baseline_result"] = baseline_result
            except LlmConnectionError as e:
                status.update(label="Failed", state="error")
                st.error(str(e))
                st.stop()

# ---------------------------------------------------------------------------
# Debate (chat-style with step indicator + typing indicators)
# ---------------------------------------------------------------------------

if run_debate_btn or run_both_btn:
    if question:
        if not (run_baseline_btn or run_both_btn):
            chat_message("You", "Question", question, align="right")

        section_header("Debate", "multi-agent discussion")

        # Step progress indicator
        step_ph = st.empty()
        step_ph.markdown("")

        # Chat thread container
        chat_container = st.container()
        typing_ph = st.empty()

        current_step = {"index": 0}

        def on_step(step_name: str, step_data: dict) -> None:
            with chat_container:
                if step_name == "proposal":
                    current_step["index"] = 1
                    step_ph.empty()
                    with step_ph.container():
                        step_indicator(STEPS, active=-1, completed=1)
                    chat_message(
                        "Agent A", "Proponent",
                        step_data.get("proposal", ""),
                        step_data.get("proposal_time"),
                    )
                elif step_name == "critique":
                    current_step["index"] = 2
                    step_ph.empty()
                    with step_ph.container():
                        step_indicator(STEPS, active=-1, completed=2)
                    chat_message(
                        "Agent B", "Critic",
                        step_data.get("critique", ""),
                        step_data.get("critique_time"),
                    )
                elif step_name == "revision":
                    current_step["index"] = 3
                    step_ph.empty()
                    with step_ph.container():
                        step_indicator(STEPS, active=-1, completed=3)
                    chat_message(
                        "Agent A", "Revision",
                        step_data.get("revision", ""),
                        step_data.get("revision_time"),
                    )
                elif step_name == "judgment":
                    current_step["index"] = 4
                    step_ph.empty()
                    with step_ph.container():
                        step_indicator(STEPS, active=-1, completed=4)
                    chat_message(
                        "Agent C", "Judge",
                        step_data.get("judgment", ""),
                        step_data.get("judgment_time"),
                    )

        # Show initial step indicator
        with step_ph.container():
            step_indicator(STEPS, active=0, completed=0)

        try:
            debate_result = run_debate(
                question, model, temperature, rounds, domain, client, on_step=on_step
            )
            typing_ph.empty()
            st.session_state["debate_result"] = debate_result
        except LlmConnectionError as e:
            typing_ph.empty()
            st.error(str(e))
            st.stop()

# ---------------------------------------------------------------------------
# Results -- tabbed comparison
# ---------------------------------------------------------------------------

baseline_result = st.session_state.get("baseline_result")
debate_result = st.session_state.get("debate_result")

if baseline_result or debate_result:
    section_header("Results")

    tab_baseline, tab_debate = st.tabs(["Baseline (Single Agent)", "Debate (Multi-Agent)"])

    with tab_baseline:
        if baseline_result:
            chat_message(
                "Agent A", "Baseline Response",
                baseline_result["response"],
                baseline_result["elapsed_seconds"],
            )
        else:
            st.markdown(f'''
            <div class="m-empty">
                <div class="m-empty-title">Baseline not run</div>
                <div class="m-empty-sub">Click "Run Both" or "Baseline Only" to generate.</div>
            </div>
            ''', unsafe_allow_html=True)

    with tab_debate:
        if debate_result:
            # Show the full conversation thread
            for rd in debate_result["rounds"]:
                chat_message("Agent A", "Proposal", rd["proposal"], rd["proposal_time"])
                chat_message("Agent B", "Critique", rd["critique"], rd["critique_time"])
                chat_message("Agent A", "Revision", rd["revision"], rd["revision_time"])
            chat_message("Agent C", "Final Judgment", debate_result["judgment"], debate_result["judgment_time"])
        else:
            st.markdown(f'''
            <div class="m-empty">
                <div class="m-empty-title">Debate not run</div>
                <div class="m-empty-sub">Click "Run Both" or "Debate Only" to generate.</div>
            </div>
            ''', unsafe_allow_html=True)

    # ------------------------------------------------------------------
    # Evaluation with radar chart
    # ------------------------------------------------------------------
    if baseline_result and debate_result:
        section_header("Evaluation", "LLM-as-Judge scores (1 to 5)")

        with st.spinner("Scoring..."):
            try:
                evaluation = compare_responses(
                    question,
                    baseline_result["response"],
                    debate_result["judgment"],
                    model,
                    client,
                )
                st.session_state["evaluation"] = evaluation
            except LlmConnectionError as e:
                st.error(f"Evaluation failed: {e}")
                evaluation = None

        if evaluation:
            b_scores = evaluation["baseline_scores"]
            d_scores = evaluation["debate_scores"]
            deltas = evaluation["deltas"]

            winner_banner(evaluation["winner"])

            # Score table + radar chart side by side
            col_table, col_radar = st.columns([3, 2])

            with col_table:
                rows = ""
                for dim in b_scores:
                    label = dim.replace("_", " ").title()
                    b, d, delta = b_scores[dim], d_scores[dim], deltas[dim]
                    cls = "m-pos" if delta > 0 else "m-neg" if delta < 0 else "m-neu"
                    sign = "+" if delta > 0 else ""
                    rows += f'<tr><td style="font-weight:500;color:{C["text_1"]};">{label}</td><td style="text-align:center;">{b}</td><td style="text-align:center;">{d}</td><td style="text-align:center;" class="{cls}">{sign}{delta}</td></tr>'

                st.markdown(f'''
                <table class="m-score-table">
                    <thead><tr>
                        <th>Dimension</th>
                        <th style="text-align:center;">Baseline</th>
                        <th style="text-align:center;">Debate</th>
                        <th style="text-align:center;">Delta</th>
                    </tr></thead>
                    <tbody>{rows}</tbody>
                </table>
                ''', unsafe_allow_html=True)

            with col_radar:
                st.markdown(radar_chart_html(b_scores, d_scores), unsafe_allow_html=True)

            # Heuristic metrics
            st.markdown('<div style="height:12px;"></div>', unsafe_allow_html=True)
            bh = evaluation["baseline_heuristics"]
            dh = evaluation["debate_heuristics"]
            m1, m2, m3, m4 = st.columns(4)
            with m1:
                metric_card("Baseline words", str(bh["word_count"]))
            with m2:
                metric_card("Debate words", str(dh["word_count"]))
            with m3:
                metric_card("Baseline concepts", str(bh["unique_concepts"]))
            with m4:
                metric_card("Debate concepts", str(dh["unique_concepts"]))

            st.markdown('<div style="height:12px;"></div>', unsafe_allow_html=True)
            if st.button("Save experiment", type="primary"):
                exp_id = generate_experiment_id()
                save_result({
                    "experiment_id": exp_id,
                    "timestamp": format_timestamp(),
                    "question": question,
                    "domain": domain,
                    "model": model,
                    "temperature": temperature,
                    "debate_rounds": rounds,
                    "baseline": baseline_result,
                    "debate": debate_result,
                    "evaluation": evaluation,
                })
                st.success(f"Saved as {exp_id}")
