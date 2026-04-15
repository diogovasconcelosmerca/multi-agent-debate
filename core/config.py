"""
Centralized configuration for the Multi-Agent Debate System.

All constants, default values, and path definitions live here
so they can be imported consistently across modules.
"""

import os
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
INPUTS_DIR = DATA_DIR / "inputs"
OUTPUTS_DIR = DATA_DIR / "outputs"
RESULTS_DIR = DATA_DIR / "results"

# ---------------------------------------------------------------------------
# Ollama (local backend)
# ---------------------------------------------------------------------------
OLLAMA_BASE_URL = "http://localhost:11434"
DEFAULT_MODEL = "llama3.2"
DEFAULT_TEMPERATURE = 0.7
GENERATE_TIMEOUT = 120  # seconds per LLM call

# ---------------------------------------------------------------------------
# Groq (cloud backend — free tier)
# ---------------------------------------------------------------------------
# Check Streamlit secrets first (for Streamlit Cloud), then env vars
def _get_groq_key() -> str:
    try:
        import streamlit as st
        return st.secrets.get("GROQ_API_KEY", os.environ.get("GROQ_API_KEY", ""))
    except Exception:
        return os.environ.get("GROQ_API_KEY", "")

GROQ_API_KEY = _get_groq_key()
GROQ_DEFAULT_MODEL = "llama-3.3-70b-versatile"

# ---------------------------------------------------------------------------
# Debate
# ---------------------------------------------------------------------------
MAX_DEBATE_ROUNDS = 3
DEFAULT_DEBATE_ROUNDS = 1

# ---------------------------------------------------------------------------
# Evaluation
# ---------------------------------------------------------------------------
EVALUATION_DIMENSIONS = [
    "coherence",
    "reasoning_depth",
    "completeness",
    "clarity",
]

EVALUATION_TEMPERATURE = 0.2  # lower temperature for more consistent scoring

# ---------------------------------------------------------------------------
# Task domains (used in the UI for categorization)
# ---------------------------------------------------------------------------
TASK_DOMAINS = [
    "General",
    "Ethics",
    "Philosophy",
    "Science",
    "Technology",
    "Planning",
    "Problem Solving",
    "Creative Writing",
]

# ---------------------------------------------------------------------------
# Ensure data directories exist
# ---------------------------------------------------------------------------
for _dir in (INPUTS_DIR, OUTPUTS_DIR, RESULTS_DIR):
    _dir.mkdir(parents=True, exist_ok=True)
