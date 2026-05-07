"""
MADS -- Multi-Agent Debate System

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

from core.config import (
    BACKENDS,
    DEFAULT_DEBATE_ROUNDS,
    DEFAULT_MODEL,
    DEFAULT_TEMPERATURE,
    GEMINI_API_KEY,
    GEMINI_DEFAULT_MODEL,
    GROQ_API_KEY,
    GROQ_DEFAULT_MODEL,
    MAX_DEBATE_ROUNDS,
    OLLAMA_FAST_MODEL,
    TASK_DOMAINS,
)
from core.llm_client import GeminiClient, GroqClient, OllamaClient
from core.theme import (
    C,
    favicon_uri,
    info_banner,
    inject_premium_css,
    logo_img,
    sidebar_brand,
    sidebar_hint,
    sidebar_label,
    sidebar_status,
)

st.set_page_config(
    page_title="MADS — Multi-Agent Debate",
    page_icon=favicon_uri(),
    layout="wide",
    initial_sidebar_state="expanded",
)

inject_premium_css()


# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------

_BACKEND_LABEL_TO_ID = {meta["label"]: bid for bid, meta in BACKENDS.items()}
_BACKEND_LABELS = list(_BACKEND_LABEL_TO_ID.keys())


def _default_model_for(backend_id: str) -> str:
    return {
        "ollama": DEFAULT_MODEL,
        "groq": GROQ_DEFAULT_MODEL,
        "gemini": GEMINI_DEFAULT_MODEL,
    }[backend_id]


with st.sidebar:
    sidebar_brand()

    # --- Backend (segmented) --------------------------------------------
    sidebar_label("Backend")
    backend_label = st.radio(
        "backend",
        _BACKEND_LABELS,
        horizontal=True,
        label_visibility="collapsed",
        index=0,
    )
    backend_id = _BACKEND_LABEL_TO_ID[backend_label]
    st.session_state["backend"] = backend_id

    meta = BACKENDS[backend_id]
    st.markdown(
        f'<div class="m-sb-hint" style="margin:6px 0 4px 0;">'
        f'<strong style="color:{C["text_2"]};font-weight:600;">{meta["tagline"]}</strong><br>{meta["help"]}'
        f'</div>',
        unsafe_allow_html=True,
    )

    # --- Credentials / client construction ------------------------------
    client = None

    if backend_id == "ollama":
        client = OllamaClient()
        st.session_state["groq_api_key"] = ""
        st.session_state["gemini_api_key"] = ""

    elif backend_id == "groq":
        sidebar_label("Groq API key")
        groq_key = st.text_input(
            "groq_key",
            value=GROQ_API_KEY,
            type="password",
            placeholder="gsk_...",
            label_visibility="collapsed",
        )
        st.session_state["groq_api_key"] = groq_key
        st.session_state["gemini_api_key"] = ""
        if groq_key:
            client = GroqClient(groq_key)

    elif backend_id == "gemini":
        sidebar_label("Gemini API key")
        gem_key = st.text_input(
            "gem_key",
            value=GEMINI_API_KEY,
            type="password",
            placeholder="AIza...",
            label_visibility="collapsed",
        )
        st.session_state["gemini_api_key"] = gem_key
        st.session_state["groq_api_key"] = ""
        if gem_key:
            client = GeminiClient(gem_key)

    # --- Connection status ----------------------------------------------
    connected = False
    if client is not None:
        connected = client.check_connection()
        sidebar_status(connected, label=meta["label"])
        st.session_state["client"] = client
    else:
        sidebar_status(False, label=meta["label"])
        st.session_state["client"] = None

    # Backend-specific hint when not connected
    if not connected:
        if backend_id == "ollama":
            sidebar_hint(
                "Run <code>ollama serve</code>, then <code>ollama pull "
                f"{OLLAMA_FAST_MODEL}</code> for the fastest experience."
            )
        elif backend_id == "groq":
            sidebar_hint("Free key at <code>console.groq.com</code>.")
        elif backend_id == "gemini":
            sidebar_hint("Free key at <code>aistudio.google.com/app/apikey</code>.")

    # --- Model -----------------------------------------------------------
    sidebar_label("Model")
    if client and connected:
        models = client.list_models()
        default_model = _default_model_for(backend_id)
        if models:
            idx = next((i for i, m in enumerate(models) if m == default_model), 0)
            model = st.selectbox("model", models, index=idx, label_visibility="collapsed")
        else:
            model = st.text_input("model", value=default_model, label_visibility="collapsed")
    else:
        model = st.text_input(
            "model",
            value=_default_model_for(backend_id),
            label_visibility="collapsed",
        )
    st.session_state["model"] = model

    # --- Tunables --------------------------------------------------------
    sidebar_label("Sampling")
    temperature = st.slider("Temperature", 0.0, 2.0, DEFAULT_TEMPERATURE, step=0.1)
    st.session_state["temperature"] = temperature

    rounds = st.slider("Debate rounds", 1, MAX_DEBATE_ROUNDS, DEFAULT_DEBATE_ROUNDS)
    st.session_state["debate_rounds"] = rounds

    sidebar_label("Domain")
    domain = st.selectbox("domain", TASK_DOMAINS, index=0, label_visibility="collapsed")
    st.session_state["domain"] = domain

    st.markdown(
        '<div class="m-sb-footer">MADS · v2.1</div>',
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# Hero
# ---------------------------------------------------------------------------

# Live state pills under the hero so users immediately see what's wired up.
backend_meta = BACKENDS[st.session_state["backend"]]
backend_dot_color = C["success"] if connected else C["error"]
hero_tags = f'''
<div class="m-hero-meta">
    <span class="m-tag"><span class="m-tag-dot" style="background:{backend_dot_color};"></span>{backend_meta["label"]}</span>
    <span class="m-tag">Model · {st.session_state.get("model","")}</span>
    <span class="m-tag">Rounds · {st.session_state.get("debate_rounds", 1)}</span>
</div>
'''

st.markdown(f"""
<div class="m-hero">
    {logo_img(48)}
    <h1 class="m-hero-title">Multi-Agent <span class="m-hero-accent">Debate</span></h1>
    <p class="m-hero-sub">
        Does structured debate between AI agents produce better answers
        than a single model? Test that hypothesis with open-source LLMs —
        locally via Ollama, or in the cloud via Groq or Gemini.
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
