"""Internal, nonserialized evidence produced by bounded intent span analysis."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


EVIDENCE_CONTEXTS = frozenset({"action", "descriptive", "how_to", "ambiguous"})
EVIDENCE_POLARITIES = frozenset({"positive", "negative", "mixed"})
RELEASE_MODES = frozenset({"none", "readiness", "action"})
RELATION_MODES = frozenset(
    {"single", "enumeration", "parallel", "explicit_sequence"}
)


@dataclass(frozen=True)
class IntentEvidence:
    """Profile and relation evidence aligned by index with an internal intent."""

    task_type: str
    context: str
    polarity: str
    release_mode: str
    relation_mode: str
    matched_signals: tuple[str, ...]
    matched_score: int


def validate_intent_evidence(
    evidence: Any,
    expected_task_types: tuple[str, ...],
) -> list[str]:
    """Validate internal evidence without accepting lookalike records."""
    if not isinstance(evidence, tuple):
        return ["intent evidence must be a tuple of IntentEvidence records"]
    if not evidence:
        return []
    if len(evidence) != len(expected_task_types):
        return ["intent evidence count must match intent count"]

    errors: list[str] = []
    for index, (item, task_type) in enumerate(
        zip(evidence, expected_task_types, strict=True), start=1
    ):
        if type(item) is not IntentEvidence:
            errors.append(f"intent evidence {index} must be an IntentEvidence")
            continue
        if item.task_type != task_type:
            errors.append(f"intent evidence {index} task type does not match intent")
        if item.context not in EVIDENCE_CONTEXTS:
            errors.append(f"intent evidence {index} has invalid context")
        if item.polarity not in EVIDENCE_POLARITIES:
            errors.append(f"intent evidence {index} has invalid polarity")
        if item.release_mode not in RELEASE_MODES:
            errors.append(f"intent evidence {index} has invalid release mode")
        if item.relation_mode not in RELATION_MODES:
            errors.append(f"intent evidence {index} has invalid relation mode")
        if not isinstance(item.matched_signals, tuple) or any(
            not isinstance(signal, str) or not signal
            for signal in item.matched_signals
        ):
            errors.append(f"intent evidence {index} has invalid matched signals")
        if (
            isinstance(item.matched_score, bool)
            or not isinstance(item.matched_score, int)
            or item.matched_score < 0
        ):
            errors.append(f"intent evidence {index} has invalid matched score")
    return errors
