"""
Shared sidebar — rendered on every page.

Streamlit re-runs each page script in isolation; widgets defined only on
the home page never run when a user navigates straight to a sub-page.
This module centralises the backend / model / sampling controls so every
page produces the same sidebar and populates `st.session_state["client"]`.

Call `render_sidebar()` once near the top of every page, after
`st.set_page_config()` and `inject_premium_css()`.
"""

from __future__ import annotations

import streamlit as st

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
    OPENROUTER_API_KEY,
    OPENROUTER_DEFAULT_MODEL,
    TASK_DOMAINS,
)
from core.llm_client import GeminiClient, GroqClient, OllamaClient, OpenRouterClient
from core.theme import (
    sidebar_brand,
    sidebar_hint,
    sidebar_label,
    sidebar_status,
)


def _default_model_for(backend_id: str) -> str:
    return {
        "ollama": DEFAULT_MODEL,
        "groq": GROQ_DEFAULT_MODEL,
        "gemini": GEMINI_DEFAULT_MODEL,
        "openrouter": OPENROUTER_DEFAULT_MODEL,
    }[backend_id]


def _try_page_link(*paths: str, label: str, icon: str) -> bool:
    """
    Try `st.page_link` against each candidate path until one succeeds.

    `st.page_link` raises StreamlitPageNotFoundError when the path
    isn't a registered page; the entry script's filename varies
    (`Home.py` locally, `app.py` / `streamlit_app.py` via Cloud
    shims), so we try them in order and stop on the first hit.
    """
    for path in paths:
        try:
            st.page_link(path, label=label, icon=icon)
            return True
        except Exception:
            continue
    return False


def _nav(active: str | None = None) -> None:
    """
    Render the four sidebar nav links via `st.page_link`.

    Using Streamlit's native page-link widget gives us **client-side
    routing**: clicking a link reruns the new page's script in place
    instead of forcing a full browser reload, which eliminates the
    white flash users saw between tabs with plain HTML anchors.

    The home link is the awkward one — its path depends on whichever
    entry script Streamlit was launched with. We probe `Home.py`,
    `app.py`, and `streamlit_app.py` in order and use the first one
    that resolves, so the same code works under any of the three
    entry filenames.

    `active` (one of "home" | "chat" | "runner" | "dashboard") is
    accepted for API stability with the previous anchor-based nav,
    but Streamlit highlights the current page on its own — we just
    pass it through.
    """
    del active  # Streamlit handles aria-current on its own.
    _try_page_link(
        "Home.py", "app.py", "streamlit_app.py",
        label="Home", icon=":material/home:",
    )
    st.page_link(
        "pages/1_Interactive_Chat.py",
        label="Interactive Chat", icon=":material/forum:",
    )
    st.page_link(
        "pages/2_Experiment_Runner.py",
        label="Experiment Runner", icon=":material/science:",
    )
    st.page_link(
        "pages/3_Results_Dashboard.py",
        label="Results Dashboard", icon=":material/analytics:",
    )


def _smart_default_backend() -> str:
    """
    Pick the most useful default backend for the current environment.

    On Streamlit Community Cloud there is no Ollama daemon to talk to,
    so the historical "ollama" default lands the user on an offline
    page. If a cloud key has been provisioned via secrets/env we prefer
    that backend instead. Order by free-tier generosity:
      Gemini   — most generous (1M tokens/day on flash-lite)
      Groq     — fastest cloud inference
      OpenRouter — open-weight cloud substitute for Ollama
    """
    if GEMINI_API_KEY:
        return "gemini"
    if GROQ_API_KEY:
        return "groq"
    if OPENROUTER_API_KEY:
        return "openrouter"
    return "ollama"


def render_sidebar(active_page: str | None = None) -> dict:
    """
    Draw the shared sidebar and store the resulting state in session.

    `active_page` (one of "home" | "chat" | "runner" | "dashboard")
    is used to highlight the current entry in the custom nav. Pass
    `None` (default) to skip highlighting.

    Returns a snapshot dict with the connected client, backend id, model,
    and connection state — convenient for the calling page even though the
    same values are also written into `st.session_state`.
    """
    with st.sidebar:
        sidebar_brand()
        _nav(active_page)

        # --- Backend (vertical buttons via radio with custom CSS) -------
        sidebar_label("Backend")
        backend_id = st.radio(
            "backend",
            list(BACKENDS.keys()),
            format_func=lambda bid: BACKENDS[bid]["label"],
            label_visibility="collapsed",
            index=list(BACKENDS.keys()).index(
                st.session_state.get("backend", _smart_default_backend())
            ),
            key="sb_backend",
        )
        st.session_state["backend"] = backend_id
        meta = BACKENDS[backend_id]
        st.markdown(
            f'<div class="m-sb-tagline">{meta["tagline"]}</div>',
            unsafe_allow_html=True,
        )

        # --- Credentials / client construction --------------------------
        client = None

        if backend_id == "ollama":
            client = OllamaClient()
            st.session_state["groq_api_key"] = ""
            st.session_state["gemini_api_key"] = ""
            st.session_state["openrouter_api_key"] = ""

        elif backend_id == "groq":
            sidebar_label("Groq API key")
            groq_key = st.text_input(
                "groq_key",
                value=st.session_state.get("groq_api_key", GROQ_API_KEY),
                type="password",
                placeholder="gsk_...",
                label_visibility="collapsed",
                key="sb_groq_key",
            )
            st.session_state["groq_api_key"] = groq_key
            st.session_state["gemini_api_key"] = ""
            st.session_state["openrouter_api_key"] = ""
            if groq_key:
                client = GroqClient(groq_key)

        elif backend_id == "gemini":
            sidebar_label("Gemini API key")
            gem_key = st.text_input(
                "gem_key",
                value=st.session_state.get("gemini_api_key", GEMINI_API_KEY),
                type="password",
                placeholder="AIza...",
                label_visibility="collapsed",
                key="sb_gem_key",
            )
            st.session_state["gemini_api_key"] = gem_key
            st.session_state["groq_api_key"] = ""
            st.session_state["openrouter_api_key"] = ""
            if gem_key:
                client = GeminiClient(gem_key)

        elif backend_id == "openrouter":
            sidebar_label("OpenRouter API key")
            or_key = st.text_input(
                "or_key",
                value=st.session_state.get("openrouter_api_key", OPENROUTER_API_KEY),
                type="password",
                placeholder="sk-or-...",
                label_visibility="collapsed",
                key="sb_or_key",
            )
            st.session_state["openrouter_api_key"] = or_key
            st.session_state["groq_api_key"] = ""
            st.session_state["gemini_api_key"] = ""
            if or_key:
                client = OpenRouterClient(or_key)

        # --- Connection status -----------------------------------------
        connected = False
        if client is not None:
            connected = client.check_connection()
            sidebar_status(connected, label=meta["label"])
            st.session_state["client"] = client
        else:
            sidebar_status(False, label=meta["label"])
            st.session_state["client"] = None

        if not connected:
            if backend_id == "ollama":
                # Context-aware: if any cloud key is configured we're
                # almost certainly on Streamlit Cloud, where Ollama can
                # never connect. Tell the user to switch backend
                # rather than to start a daemon they can't run.
                if GEMINI_API_KEY or GROQ_API_KEY or OPENROUTER_API_KEY:
                    sidebar_hint(
                        "Ollama needs a daemon on the same machine as "
                        "the app — it can't run on Streamlit Cloud. "
                        "Switch to <strong>Gemini</strong>, "
                        "<strong>Groq</strong>, or "
                        "<strong>OpenRouter</strong> above."
                    )
                else:
                    sidebar_hint(
                        f"Run <code>ollama serve</code>, then "
                        f"<code>ollama pull {OLLAMA_FAST_MODEL}</code>."
                    )
            elif backend_id == "groq":
                sidebar_hint("Free key at <code>console.groq.com</code>.")
            elif backend_id == "gemini":
                sidebar_hint(
                    "Free key at <code>aistudio.google.com/app/apikey</code>."
                )
            else:  # openrouter
                sidebar_hint(
                    "Free key at <code>openrouter.ai/keys</code>. "
                    "Use models tagged <code>:free</code> for zero cost."
                )

        # --- Model ------------------------------------------------------
        sidebar_label("Model")
        default_model = _default_model_for(backend_id)
        if client and connected:
            models = client.list_models()
            if models:
                # Preserve a previously-chosen model for this backend if it's
                # still in the list, otherwise fall back to the default.
                prev = st.session_state.get(f"model_{backend_id}")
                pick = prev if prev in models else default_model
                idx = next((i for i, m in enumerate(models) if m == pick), 0)
                model = st.selectbox(
                    "model", models, index=idx,
                    label_visibility="collapsed",
                    key=f"sb_model_select_{backend_id}",
                )
            else:
                model = st.text_input(
                    "model", value=default_model,
                    label_visibility="collapsed",
                    key=f"sb_model_text_{backend_id}",
                )
        else:
            model = st.text_input(
                "model", value=default_model,
                label_visibility="collapsed",
                key=f"sb_model_text_{backend_id}",
            )
        st.session_state["model"] = model
        st.session_state[f"model_{backend_id}"] = model

        # --- Sampling --------------------------------------------------
        sidebar_label("Sampling")
        temperature = st.slider(
            "Temperature", 0.0, 2.0,
            st.session_state.get("temperature", DEFAULT_TEMPERATURE),
            step=0.1, key="sb_temp",
        )
        st.session_state["temperature"] = temperature

        rounds = st.slider(
            "Debate rounds", 1, MAX_DEBATE_ROUNDS,
            st.session_state.get("debate_rounds", DEFAULT_DEBATE_ROUNDS),
            key="sb_rounds",
        )
        st.session_state["debate_rounds"] = rounds

        # --- Domain ----------------------------------------------------
        sidebar_label("Domain")
        domain_idx = TASK_DOMAINS.index(st.session_state.get("domain", "General")) \
            if st.session_state.get("domain", "General") in TASK_DOMAINS else 0
        domain = st.selectbox(
            "domain", TASK_DOMAINS, index=domain_idx,
            label_visibility="collapsed", key="sb_domain",
        )
        st.session_state["domain"] = domain

        st.markdown(
            '<div class="m-sb-footer">MADS · v2.1</div>',
            unsafe_allow_html=True,
        )

    return {
        "client": client,
        "connected": connected,
        "backend": backend_id,
        "backend_meta": meta,
        "model": model,
        "temperature": temperature,
        "rounds": rounds,
        "domain": domain,
    }
