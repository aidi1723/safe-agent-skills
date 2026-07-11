"""Shared hard boundary for every intent text parsing entry point."""

MAX_TASK_SCAN_CHARS = 20_000


def bound_task_text(text: str) -> str:
    """Return the only source region intent parsers may inspect."""
    return text[:MAX_TASK_SCAN_CHARS]
