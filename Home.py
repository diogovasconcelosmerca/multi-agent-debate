"""
MADS — Multi-Agent Debate System.

Home page: hero, pipeline overview, and the global sidebar that lets you
choose a backend (Ollama / Groq / Gemini), supply credentials, and pick a
model. The selected client is stored in `st.session_state` so the other
pages reuse it without re-instantiating.
"""

import sys
from pathlib import Path

import streamlit as st

_PROJECT_ROOT = Path(__file__).resolve().parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from core.sidebar import render_sidebar
from core.theme import (
    C,
    favicon_uri,
    info_banner,
    inject_premium_css,
    logo_img,
)

st.set_page_config(
    page_title="MADS — Multi-Agent Debate",
    page_icon=favicon_uri(),
    layout="wide",
    initial_sidebar_state="expanded",
)

inject_premium_css()

state = render_sidebar()
client = state["client"]
connected = state["connected"]
backend_meta = state["backend_meta"]
backend_id = state["backend"]


# ---------------------------------------------------------------------------
# Hero
# ---------------------------------------------------------------------------

backend_dot_color = C["success"] if connected else C["error"]
hero_tags = f'''
<div class="m-hero-meta">
    <span class="m-tag"><span class="m-tag-dot" style="background:{backend_dot_color};"></span>{backend_meta["label"]}</span>
    <span class="m-tag">Model · <code>{state["model"]}</code></span>
    <span class="m-tag">Rounds · {state["rounds"]}</span>
</div>
'''

st.markdown(f"""
<div class="m-hero">
    {logo_img(56)}
    <div class="m-hero-eyebrow">Multi-Agent Debate System</div>
    <h1 class="m-hero-title">Better answers, by <span class="m-hero-accent">debate</span>.</h1>
    <p class="m-hero-sub">
        Compare a single-agent baseline against a propose / critique / revise / judge
        pipeline. Same model, same prompt — measurably different reasoning.
    </p>
    {hero_tags}
</div>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Features
# ---------------------------------------------------------------------------

st.markdown(f"""
<div class="m-features">
    <div class="m-feat">
        <div class="m-feat-bar" style="background:{C['accent']};"></div>
        <div class="m-feat-title">Interactive Chat</div>
        <div class="m-feat-desc">
            Ask a question and watch three agents debate in real time.
            Compare against a single-agent baseline.
        </div>
    </div>
    <div class="m-feat">
        <div class="m-feat-bar" style="background:{C['agent_b']};"></div>
        <div class="m-feat-title">Experiment Runner</div>
        <div class="m-feat-desc">
            Batch-run experiments on multiple questions.
            Results are auto-saved for later analysis.
        </div>
    </div>
    <div class="m-feat">
        <div class="m-feat-bar" style="background:{C['agent_c']};"></div>
        <div class="m-feat-title">Results Dashboard</div>
        <div class="m-feat-desc">
            Visualise experiment data with interactive charts.
            Export to CSV for your research.
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Pipeline
# ---------------------------------------------------------------------------

st.markdown(f"""
<div class="m-flow">
    <div class="m-flow-label">Debate Pipeline</div>
    <div class="m-flow-step">
        <div class="m-flow-num" style="background:{C['agent_a']}18;color:{C['agent_a']};">1</div>
        <div class="m-flow-text"><strong>Proponent</strong> generates an initial answer</div>
    </div>
    <div class="m-flow-line"></div>
    <div class="m-flow-step">
        <div class="m-flow-num" style="background:{C['agent_b']}18;color:{C['agent_b']};">2</div>
        <div class="m-flow-text"><strong>Critic</strong> identifies flaws, biases, and gaps</div>
    </div>
    <div class="m-flow-line"></div>
    <div class="m-flow-step">
        <div class="m-flow-num" style="background:{C['agent_a']}18;color:{C['agent_a']};">3</div>
        <div class="m-flow-text"><strong>Proponent</strong> revises based on the critique</div>
    </div>
    <div class="m-flow-line"></div>
    <div class="m-flow-step">
        <div class="m-flow-num" style="background:{C['agent_c']}18;color:{C['agent_c']};">4</div>
        <div class="m-flow-text"><strong>Judge</strong> synthesises the final balanced answer</div>
    </div>
</div>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Connection feedback
# ---------------------------------------------------------------------------

if client is None:
    if backend_id == "ollama":
        info_banner("No Ollama client available — internal error.", variant="warn")
    else:
        info_banner(
            f"Add a {backend_meta['label']} API key in the sidebar to start running debates.",
            variant="base",
        )
elif not connected:
    if backend_id == "ollama":
        info_banner(
            "Ollama is not reachable. Run `ollama serve`, then refresh this page.",
            variant="warn",
        )
    else:
        info_banner(
            f"{backend_meta['label']} is not reachable. Double-check the API key and try again.",
            variant="warn",
        )
else:
    info_banner(
        f"{backend_meta['label']} is ready · open Interactive Chat from the sidebar to begin.",
        variant="ok",
    )
