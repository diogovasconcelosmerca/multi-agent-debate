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
# Generation
# ---------------------------------------------------------------------------
DEFAULT_TEMPERATURE = 0.7
# A multi-agent debate is 4 LLM calls per round; small local models on a
# laptop CPU can take 60-90s each. 300s gives them room without hanging the
# UI forever on a stuck request.
GENERATE_TIMEOUT = 300  # seconds per LLM call


# ---------------------------------------------------------------------------
# Secret loading (Streamlit Cloud secrets first, then env vars)
# ---------------------------------------------------------------------------
def _load_secret(name: str) -> str:
    try:
        import streamlit as st
        val = st.secrets.get(name, None)
        if val:
            return val
    except Exception:
        pass
    return os.environ.get(name, "")


# ---------------------------------------------------------------------------
# Ollama (local backend)
# ---------------------------------------------------------------------------
OLLAMA_BASE_URL = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
DEFAULT_MODEL = "qwen3.5:4b"
# Smaller fallback that runs comfortably on CPU-only laptops. qwen3.5
# leads the open-weight 4B class on reasoning benchmarks as of late
# 2025 and supports thinking-mode for free; llama3.2:1b stays as the
# absolute-minimum option for tight RAM budgets.
OLLAMA_FAST_MODEL = "llama3.2:1b"

# ---------------------------------------------------------------------------
# Groq (cloud backend — free tier)
# ---------------------------------------------------------------------------
GROQ_API_KEY = _load_secret("GROQ_API_KEY")
GROQ_DEFAULT_MODEL = "llama-3.3-70b-versatile"

# ---------------------------------------------------------------------------
# Gemini (cloud backend — generous free tier)
# ---------------------------------------------------------------------------
GEMINI_API_KEY = _load_secret("GEMINI_API_KEY")
# Flash-lite has 30 RPM on the free tier (vs 10 for plain flash). Each
# debate fires ~10 LLM calls in a tight burst, so the higher RPM ceiling
# matters more than the marginal quality bump from full flash.
GEMINI_DEFAULT_MODEL = "gemini-2.0-flash-lite"

# ---------------------------------------------------------------------------
# Backend metadata (used by the sidebar UI)
# ---------------------------------------------------------------------------
BACKENDS = {
    "ollama": {
        "id": "ollama",
        "label": "Ollama",
        "tagline": "Local · Offline · Free",
        "help": "Runs on your machine via `ollama serve`. No API key required.",
    },
    "groq": {
        "id": "groq",
        "label": "Groq",
        "tagline": "Cloud · Fast · Free tier",
        "help": "Sub-second 70B inference. Get a key at console.groq.com.",
    },
    "gemini": {
        "id": "gemini",
        "label": "Gemini",
        "tagline": "Cloud · Generous free tier",
        "help": "Google AI Studio. Get a key at aistudio.google.com/app/apikey.",
    },
}

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
