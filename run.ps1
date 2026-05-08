# Local launcher for MADS on Windows.
#
# Usage:
#   .\run.ps1          (in PowerShell, from the project root)
#
# Activates the venv and starts Streamlit pointing at Home.py.
# Keys for Groq / Gemini are read from .streamlit/secrets.toml
# automatically — no need to paste them in the sidebar each time.

Set-Location $PSScriptRoot
.\venv\Scripts\activate
streamlit run Home.py
