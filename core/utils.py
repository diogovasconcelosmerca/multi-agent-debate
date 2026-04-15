"""
Small utility helpers used across the project.
"""

import random
import string
import time
from datetime import datetime, timezone


class Timer:
    """Context manager that measures wall-clock elapsed time in seconds."""

    def __enter__(self):
        self.start = time.perf_counter()
        self.elapsed = 0.0
        return self

    def __exit__(self, *exc):
        self.elapsed = time.perf_counter() - self.start
        return False


def format_timestamp() -> str:
    """Return an ISO-8601 UTC timestamp string."""
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def generate_experiment_id() -> str:
    """Generate a short unique experiment identifier, e.g. exp_20260406_143022_a1b2."""
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    suffix = "".join(random.choices(string.ascii_lowercase + string.digits, k=4))
    return f"exp_{ts}_{suffix}"


def word_count(text: str) -> int:
    """Count words in a text string."""
    return len(text.split())


def truncate_text(text: str, max_chars: int = 500) -> str:
    """Truncate text for display purposes, appending '...' if trimmed."""
    if len(text) <= max_chars:
        return text
    return text[:max_chars].rstrip() + "..."


# A minimal English stop-word set for the unique-concepts heuristic.
_STOP_WORDS = frozenset(
    "a an the is are was were be been being have has had do does did "
    "will would shall should may might can could must need dare "
    "i me my we our you your he him his she her it its they them their "
    "this that these those who whom which what where when how why "
    "and but or nor not so yet for if then else also too very "
    "in on at to from by with of as into about between through during "
    "up down out off over under again further once here there all each "
    "both few more most other some such no any every own same than "
    "just only still already even much many well also back".split()
)


def count_unique_concepts(text: str) -> int:
    """
    Naive heuristic: count distinct 'concept words' — words longer than
    4 characters that are not common stop-words.  This is NOT NLP-grade;
    it gives a rough proxy for conceptual breadth.
    """
    words = set()
    for token in text.lower().split():
        # strip basic punctuation
        cleaned = token.strip(".,;:!?\"'()[]{}-/")
        if len(cleaned) > 4 and cleaned not in _STOP_WORDS:
            words.add(cleaned)
    return len(words)
