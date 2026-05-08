"""
Streamlit Cloud compatibility shim — same as app.py.

Streamlit Cloud auto-discovers ``streamlit_app.py``; we ship one so a
fresh deployment "just works" without reconfiguring the main file.
See app.py for the rationale.
"""

from __future__ import annotations

import runpy
from pathlib import Path

_HOME = Path(__file__).resolve().parent / "Home.py"
runpy.run_path(str(_HOME), run_name="__main__")
