"""
Pytest fixtures + path setup so tests can `import core...` without an editable install.
"""

import sys
from pathlib import Path

# Make the project root importable.
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
