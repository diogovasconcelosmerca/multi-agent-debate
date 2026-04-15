"""
Experiment Runner -- batch experiments.
"""

import json
import sys
from pathlib import Path

import streamlit as st

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from core.baseline_engine import run_baseline
from core.config import INPUTS_DIR
from core.debate_engine import run_debate
from core.evaluator import compare_responses
from core.llm_client import LlmConnectionError
from core.storage import save_result
from core.theme import C, favicon_uri, inject_premium_css, page_header
from core.utils import format_timestamp, generate_experiment_id

st.set_page_config(page_title="MADS -- Experiments", page_icon=favicon_uri(), layout="wide")
inject_premium_css()


def _s(key, default):
    return st.session_state.get(key, default)


def _get_client():
    client = st.session_state.get("client")
    if client is None:
        st.error("No LLM backend connected. Go to the Home page and configure Ollama or Groq in the sidebar.")
        st.stop()
    return client


page_header("Experiment Runner", "Batch-run experiments. Results are auto-saved.")

source = st.radio("source", ["Sample questions", "Custom list"], horizontal=True, label_visibility="collapsed")

questions: list[dict] = []

if source == "Sample questions":
    sample_path = INPUTS_DIR / "sample_questions.json"
    if sample_path.exists():
        with open(sample_path, "r", encoding="utf-8") as f:
            questions = json.load(f)
        st.markdown(f'''
        <div class="m-agent" style="border-left-color:{C["accent"]};">
            <div class="m-agent-body">{len(questions)} questions loaded from <code>sample_questions.json</code></div>
        </div>
        ''', unsafe_allow_html=True)
        with st.expander("Preview"):
            for i, q in enumerate(questions):
                st.markdown(f'''
                <div style="padding:4px 0;border-bottom:1px solid {C["border"]};font-size:13px;color:{C["text_2"]};">
                    <span style="color:{C["text_4"]};margin-right:6px;">{i+1}.</span>
                    {q["question"]}
                    <span style="color:{C["accent"]};font-size:10px;margin-left:6px;">{q.get("domain","")}</span>
                </div>
                ''', unsafe_allow_html=True)
    else:
        st.warning("No sample file found.")
else:
    raw = st.text_area("q", height=160, placeholder="One question per line", label_visibility="collapsed")
    if raw.strip():
        domain = _s("domain", "General")
        questions = [{"question": q.strip(), "domain": domain} for q in raw.strip().split("\n") if q.strip()]
        st.markdown(f'''
        <div class="m-agent" style="border-left-color:{C["accent"]};">
            <div class="m-agent-body">{len(questions)} questions ready</div>
        </div>
        ''', unsafe_allow_html=True)

model = _s("model", "llama3.2")
temperature = _s("temperature", 0.7)
rounds = _s("debate_rounds", 1)
client = _get_client()

if questions:
    st.markdown('<div style="height:8px;"></div>', unsafe_allow_html=True)
    if st.button("Run all experiments", type="primary", use_container_width=True):
        progress = st.progress(0, text="Starting...")
        container = st.container()
        completed = errors = 0

        for idx, item in enumerate(questions):
            q, d = item["question"], item.get("domain", "General")
            progress.progress(idx / len(questions), text=f"{idx+1}/{len(questions)} -- {q[:55]}...")
            try:
                b = run_baseline(q, model, temperature, d, client)
                db = run_debate(q, model, temperature, rounds, d, client)
                ev = compare_responses(q, b["response"], db["judgment"], model, client)
                save_result({
                    "experiment_id": generate_experiment_id(), "timestamp": format_timestamp(),
                    "question": q, "domain": d, "model": model,
                    "temperature": temperature, "debate_rounds": rounds,
                    "baseline": b, "debate": db, "evaluation": ev,
                })
                completed += 1
                w = ev.get("winner", "?")
                wc = C["success"] if w == "debate" else C["accent"] if w == "baseline" else C["text_3"]
                with container:
                    st.markdown(f'''
                    <div class="m-result-row">
                        <span style="color:{C["success"]};">&#10003;</span>
                        <span class="m-rr-q">{q[:70]}{"..." if len(q)>70 else ""}</span>
                        <span class="m-rr-badge" style="color:{wc};background:{wc}12;">{w}</span>
                        <span class="m-rr-time">{b["elapsed_seconds"]:.0f}s / {db["total_elapsed_seconds"]:.0f}s</span>
                    </div>
                    ''', unsafe_allow_html=True)
            except Exception as e:
                errors += 1
                with container:
                    st.markdown(f'''
                    <div class="m-result-row" style="border-color:{C["error"]}30;">
                        <span style="color:{C["error"]};">&#10007;</span>
                        <span class="m-rr-q" style="color:{C["error"]};">{q[:60]}... -- {e}</span>
                    </div>
                    ''', unsafe_allow_html=True)

        progress.progress(1.0, text="Complete")
        st.markdown(f'''
        <div class="m-banner {"m-banner-win" if errors == 0 else "m-banner-tie"}">
            <span>{completed} completed, {errors} errors</span>
        </div>
        ''', unsafe_allow_html=True)
