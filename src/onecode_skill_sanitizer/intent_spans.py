"""Immutable contracts for bounded intent span decomposition."""

from dataclasses import dataclass


MAX_CANDIDATE_SIGNALS = 128
MAX_EMITTED_INTENTS = 12


@dataclass(frozen=True)
class ProfileSignalSpan:
    start: int
    end: int
    task_type: str
    signal: str
    score: int


@dataclass(frozen=True)
class SpanDecomposition:
    clauses: tuple[str, ...]
    observed_candidate_count: int
    candidate_signal_limit_exceeded: bool
    intent_limit_exceeded: bool
