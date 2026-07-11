"""Strict, finite metric primitives for router quality evaluation."""

from __future__ import annotations

import math
from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class ClassificationCounts:
    true_positive: int = 0
    false_positive: int = 0
    false_negative: int = 0

    def __post_init__(self) -> None:
        for field_name in ("true_positive", "false_positive", "false_negative"):
            value = getattr(self, field_name)
            if type(value) is not int or value < 0:
                raise ValueError(f"{field_name} must be an exact nonnegative integer")


def finite_ratio(numerator: int, denominator: int, *, empty: float) -> float:
    """Return a finite bounded ratio with an explicit empty-set value."""

    if type(numerator) is not int or numerator < 0:
        raise ValueError("numerator must be an exact nonnegative integer")
    if type(denominator) is not int or denominator < 0:
        raise ValueError("denominator must be an exact nonnegative integer")
    if numerator > denominator:
        raise ValueError("numerator must not exceed denominator")
    if (
        type(empty) not in {int, float}
        or isinstance(empty, bool)
        or not math.isfinite(empty)
        or not 0.0 <= empty <= 1.0
    ):
        raise ValueError("empty must be finite and between zero and one")
    result = float(empty) if denominator == 0 else numerator / denominator
    if not math.isfinite(result):
        raise ValueError("ratio must be finite")
    return result


def macro_classification_metrics(
    expected: list[set[str]],
    actual: list[set[str]],
) -> dict[str, Any]:
    """Calculate per-label and arithmetic macro metrics over the label union."""

    if not isinstance(expected, list) or not isinstance(actual, list) or len(expected) != len(actual):
        raise ValueError("expected and actual must be lists with equal length")
    for collection_name, collection in (("expected", expected), ("actual", actual)):
        for labels in collection:
            if type(labels) is not set or not all(type(label) is str and label for label in labels):
                raise ValueError(f"{collection_name} entries must be sets of nonempty strings")

    labels = sorted(set().union(*expected, *actual)) if expected or actual else []
    per_label: dict[str, dict[str, Any]] = {}
    for label in labels:
        counts = ClassificationCounts(
            true_positive=sum(label in wanted and label in emitted for wanted, emitted in zip(expected, actual)),
            false_positive=sum(label not in wanted and label in emitted for wanted, emitted in zip(expected, actual)),
            false_negative=sum(label in wanted and label not in emitted for wanted, emitted in zip(expected, actual)),
        )
        precision = finite_ratio(
            counts.true_positive,
            counts.true_positive + counts.false_positive,
            empty=0.0,
        )
        recall = finite_ratio(
            counts.true_positive,
            counts.true_positive + counts.false_negative,
            empty=0.0,
        )
        f1 = 0.0 if precision + recall == 0 else 2 * precision * recall / (precision + recall)
        per_label[label] = {
            "counts": asdict(counts),
            "precision": precision,
            "recall": recall,
            "f1": f1,
        }

    if not labels:
        return {"precision": 1.0, "recall": 1.0, "f1": 1.0, "per_label": {}}
    label_count = len(labels)
    return {
        "precision": sum(item["precision"] for item in per_label.values()) / label_count,
        "recall": sum(item["recall"] for item in per_label.values()) / label_count,
        "f1": sum(item["f1"] for item in per_label.values()) / label_count,
        "per_label": per_label,
    }
