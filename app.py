"""
MADS -- Multi-Agent Debate System
"""

import sys
from pathlib import Path

import streamlit as st

_PROJECT_ROOT = Path(__file__).resolve().parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from core.config import (
    DEFAULT_DEBATE_ROUNDS,
    DEFAULT_MODEL,
    DEFAULT_TEMPERATURE,
    GROQ_API_KEY,
    GROQ_DEFAULT_MODEL,
    MAX_DEBATE_ROUNDS,
    TASK_DOMAINS,
)
from core.llm_client import GroqClient, OllamaClient, get_client
from core.theme import C, favicon_uri, inject_premium_css, logo_img, sidebar_brand, sidebar_status

st.set_page_config(
    page_title="MADS",
    page_icon=favicon_uri(),
    layout="wide",
    initial_sidebar_state="expanded",
)

inject_premium_css()

# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------

with st.sidebar:
    sidebar_brand()

    # Backend selector
    st.markdown(f'<div style="font-size:9px;font-weight:600;text-transform:uppercase;letter-spacing:0.08em;color:{C["text_3"]};margin:8px 0 4px 0;">Backend</div>', unsafe_allow_html=True)
    backend = st.radio(
        "backend",
        ["Ollama (local)", "Groq (cloud)"],
        horizontal=True,
        label_visibility="collapsed",
    )
    st.session_state["backend"] = "groq" if "Groq" in backend else "ollama"

    if st.session_state["backend"] == "groq":
        groq_key = st.text_input(
            "GROQ API KEY",
            value=GROQ_API_KEY,
            type="password",
            help="Free at console.groq.com",
        )
        st.session_state["groq_api_key"] = groq_key
        if groq_key:
            client = GroqClient(groq_key)
        else:
            client = None
    else:
        client = OllamaClient()
        st.session_state["groq_api_key"] = ""

    if client:
        connected = client.check_connection()
        sidebar_status(connected)
        st.session_state["client"] = client

        models = client.list_models() if connected else []
        if models:
            default_model = GROQ_DEFAULT_MODEL if st.session_state["backend"] == "groq" else DEFAULT_MODEL
            idx = 0
            for i, m in enumerate(models):
                if m == default_model:
                    idx = i
                    break
            model = st.selectbox("MODEL", models, index=idx)
        else:
            model = st.text_input(
                "MODEL",
                value=GROQ_DEFAULT_MODEL if st.session_state["backend"] == "groq" else DEFAULT_MODEL,
            )
        st.session_state["model"] = model
    else:
        sidebar_status(False)
        st.session_state["model"] = GROQ_DEFAULT_MODEL

    temperature = st.slider("TEMPERATURE", 0.0, 2.0, DEFAULT_TEMPERATURE, step=0.1)
    st.session_state["temperature"] = temperature

    rounds = st.slider("ROUNDS", 1, MAX_DEBATE_ROUNDS, DEFAULT_DEBATE_ROUNDS)
    st.session_state["debate_rounds"] = rounds

    domain = st.selectbox("DOMAIN", TASK_DOMAINS, index=0)
    st.session_state["domain"] = domain

    st.markdown("---")
    st.markdown(
        f'<div style="font-size:10px;color:{C["text_4"]};text-align:center;">v2.0</div>',
        unsafe_allow_html=True,
    )

# ---------------------------------------------------------------------------
# Hero
# ---------------------------------------------------------------------------

st.markdown(f"""
<div class="m-hero">
    {logo_img(48)}
    <h1 class="m-hero-title">Multi-Agent <span class="m-hero-accent">Debate</span></h1>
    <p class="m-hero-sub">
        Does structured debate between AI agents produce better answers
        than a single model? Test that hypothesis with open-source LLMs
        -- locally via Ollama or in the cloud via Groq.
    </p>
</div>
""", unsafe_allow_html=True)

st.markdown(f"""
<style>.m-hero img {{ margin: 0 auto; }}</style>
""", unsafe_allow_html=True)

# Features
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

# Pipeline
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

if not st.session_state.get("client"):
    st.markdown(f"""
    <div class="m-banner m-banner-base" style="margin-top:1.5rem;">
        <span>No backend connected. Select Ollama (local) or enter a Groq API key in the sidebar.</span>
    </div>
    """, unsafe_allow_html=True)
elif not connected:
    backend_name = "Groq" if st.session_state["backend"] == "groq" else "Ollama"
    st.markdown(f"""
    <div class="m-banner m-banner-base" style="margin-top:1.5rem;">
        <span>{backend_name} is not connected. {"Check your API key." if backend_name == "Groq" else "Run <code>ollama serve</code> and refresh."}</span>
    </div>
    """, unsafe_allow_html=True)
