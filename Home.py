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

_NO_UL = "text-decoration:none !important;text-decoration-line:none !important;border-bottom:none !important;"
st.markdown(f"""
<div class="m-features">
    <a class="m-feat" href="/Interactive_Chat" target="_self" style="{_NO_UL}">
        <div class="m-feat-bar" style="background:{C['accent']};"></div>
        <div class="m-feat-title" style="{_NO_UL}">Interactive Chat</div>
        <div class="m-feat-desc" style="{_NO_UL}">
            Ask a question and watch three agents debate in real time.
            Compare against a single-agent baseline.
        </div>
        <div class="m-feat-cta" style="{_NO_UL}">Open chat →</div>
    </a>
    <a class="m-feat" href="/Experiment_Runner" target="_self" style="{_NO_UL}">
        <div class="m-feat-bar" style="background:{C['agent_b']};"></div>
        <div class="m-feat-title" style="{_NO_UL}">Experiment Runner</div>
        <div class="m-feat-desc" style="{_NO_UL}">
            Batch-run experiments on multiple questions.
            Results are auto-saved for later analysis.
        </div>
        <div class="m-feat-cta" style="{_NO_UL}">Open runner →</div>
    </a>
    <a class="m-feat" href="/Results_Dashboard" target="_self" style="{_NO_UL}">
        <div class="m-feat-bar" style="background:{C['agent_c']};"></div>
        <div class="m-feat-title" style="{_NO_UL}">Results Dashboard</div>
        <div class="m-feat-desc" style="{_NO_UL}">
            Visualise experiment data with interactive charts.
            Export to CSV for your research.
        </div>
        <div class="m-feat-cta" style="{_NO_UL}">Open dashboard →</div>
    </a>
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
            f"Add a {backend_meta['label']} API key in the sidebar (or in Streamlit Cloud → Settings → Secrets) to start running debates.",
            variant="base",
        )
elif not connected:
    if backend_id == "ollama":
        info_banner(
            "Ollama is not reachable. Locally: run `ollama serve`. "
            "On Streamlit Cloud: Ollama can't run there — switch to **Gemini** "
            "in the sidebar (free key at aistudio.google.com/app/apikey).",
            variant="warn",
        )
    elif backend_id == "groq":
        info_banner(
            "Groq is not reachable. The free tier has per-minute and per-day "
            "caps; if you've hit them, switch to **Gemini** in the sidebar — "
            "its free tier is much more generous.",
            variant="warn",
        )
    else:
        info_banner(
            "Gemini is not reachable. Double-check the API key in the sidebar "
            "(or in Streamlit Cloud → ⋯ → Settings → Secrets, key name "
            "`GEMINI_API_KEY`). Get a free key at "
            "[aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey).",
            variant="warn",
        )
else:
    info_banner(
        f"{backend_meta['label']} is ready · open Interactive Chat from the sidebar to begin.",
        variant="ok",
    )
