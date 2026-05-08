"""
Streamlit Cloud compatibility shim.

Streamlit Cloud deployments often pin the *main file* to ``app.py`` (it
is one of Streamlit's auto-discovered defaults, alongside
``streamlit_app.py``). The canonical entry point for this project is
``Home.py`` — that filename is what gives the sidebar nav its "Home"
label.

Rather than force every existing deployment to be reconfigured after
the rename, we keep this shim so both names route to the same code.

Streamlit re-executes the entry script on every interaction; running
Home.py via :func:`runpy.run_path` reproduces that lifecycle exactly.
"""

from __future__ import annotations

import runpy
from pathlib import Path

_HOME = Path(__file__).resolve().parent / "Home.py"
runpy.run_path(str(_HOME), run_name="__main__")
