#!/usr/bin/env bash
# Local launcher for MADS on macOS / Linux.
#
# Usage:
#   ./run.sh    (from the project root)
#
# Activates the venv and starts Streamlit pointing at Home.py.
# Keys for Groq / Gemini are read from .streamlit/secrets.toml
# automatically — no need to paste them in the sidebar each time.

set -euo pipefail
cd "$(dirname "$0")"
# shellcheck disable=SC1091
source venv/bin/activate
streamlit run Home.py
