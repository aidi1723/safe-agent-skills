"""Fail-closed production quality gates for router evaluation reports."""

from __future__ import annotations

import math
from typing import Any


PRODUCTION_THRESHOLDS: dict[str, tuple[str, float]] = {
    "task_type_macro_f1": ("minimum", 0.90),
    "scenario_f1": ("minimum", 0.88),
    "required_capability_recall": ("minimum", 0.97),
    "forbidden_scenario_false_positive_rate": ("maximum", 0.005),
    "forbidden_skill_false_positive_rate": ("maximum", 0.005),
    "multi_intent_exact_match": ("minimum", 0.80),
    "dag_validity": ("minimum", 1.0),
    "high_confidence_error_rate": ("maximum", 0.02),
    "core_bundle_contract_coverage": ("minimum", 0.80),
    "dependency_edge_recall": ("minimum", 0.90),
}

_SUPPORT_REQUIREMENTS: dict[str, tuple[tuple[str, str], ...]] = {
    "task_type_macro_f1": (("task_type_label_count", "positive_int"),),
    "scenario_f1": (("scenario_expected", "positive_int"),),
    "required_capability_recall": (
        ("required_capability_context_available", "true"),
        ("required_capability_total", "positive_int"),
    ),
    "forbidden_scenario_false_positive_rate": (("forbidden_total", "positive_int"),),
    "forbidden_skill_false_positive_rate": (("forbidden_skill_total", "positive_int"),),
    "multi_intent_exact_match": (("case_count", "positive_int"),),
    "dag_validity": (("case_count", "positive_int"),),
    "high_confidence_error_rate": (("high_confidence_cases", "positive_int"),),
    "core_bundle_contract_coverage": (
        ("core_bundle_contract_available", "true"),
        ("core_bundle_contract_total", "positive_int"),
    ),
    "dependency_edge_recall": (("dependency_total", "positive_int"),),
}


def build_quality_gate(
    metrics: dict[str, Any],
    *,
    dataset_identity: object,
    review_identity: object,
    support_counts: dict[str, Any] | None = None,
) -> dict[str, object]:
    """Build an auditable production decision without trusting empty evidence."""

    metric_source = metrics if type(metrics) is dict else {}
    support_source = support_counts if type(support_counts) is dict else {}
    failed_gates: set[str] = set()
    missing_gates: set[str] = set()
    metric_gates: dict[str, dict[str, object]] = {}
    support_evidence: dict[str, dict[str, object]] = {}

    for name in sorted(PRODUCTION_THRESHOLDS):
        direction, threshold = PRODUCTION_THRESHOLDS[name]
        raw_value = metric_source.get(name)
        value = _quality_value(raw_value)
        requirements = {
            field: support_source.get(field) if _valid_support(support_source.get(field), kind) else None
            for field, kind in _SUPPORT_REQUIREMENTS[name]
        }
        supported = all(
            _valid_support(support_source.get(field), kind)
            for field, kind in _SUPPORT_REQUIREMENTS[name]
        )
        support_evidence[name] = {
            "status": "available" if supported else "missing",
            "requirements": requirements,
        }

        if value is None or not supported:
            status = "missing"
            missing_gates.add(name)
        else:
            passed = value >= threshold if direction == "minimum" else value <= threshold
            status = "pass" if passed else "fail"
            if not passed:
                failed_gates.add(name)
        metric_gates[name] = {
            "status": status,
            "value": value,
            "threshold": threshold,
            "direction": direction,
        }

    valid_dataset_identity = _flat_identity(dataset_identity, allow_empty=False)
    if valid_dataset_identity is None:
        missing_gates.add("dataset_identity")
        valid_dataset_identity = {}
    valid_review_identity = _flat_identity(review_identity, allow_empty=False)
    if valid_review_identity is None:
        missing_gates.add("independent_label_review")
        valid_review_identity = {}

    failed = sorted(failed_gates)
    missing = sorted(missing_gates)
    return {
        "production_ready": not failed and not missing,
        "metric_gates": metric_gates,
        "failed_gates": failed,
        "missing_gates": missing,
        "dataset_identity": valid_dataset_identity,
        "review_identity": valid_review_identity,
        "support_evidence": support_evidence,
    }


def _quality_value(value: object) -> int | float | None:
    if type(value) not in {int, float}:
        return None
    if not math.isfinite(value) or not 0.0 <= value <= 1.0:
        return None
    return value


def _valid_support(value: object, kind: str) -> bool:
    if kind == "positive_int":
        return type(value) is int and value > 0
    if kind == "true":
        return type(value) is bool and value is True
    raise AssertionError(f"unknown support requirement: {kind}")


def _flat_identity(identity: object, *, allow_empty: bool) -> dict[str, object] | None:
    if type(identity) is not dict or (not allow_empty and not identity):
        return None
    normalized: dict[str, object] = {}
    for key, value in identity.items():
        if type(key) is not str or not key or key != key.strip():
            return None
        if type(value) is str:
            if not value or value != value.strip():
                return None
        elif type(value) is float:
            if not math.isfinite(value):
                return None
        elif type(value) not in {int, bool} and value is not None:
            return None
        normalized[key] = value
    return dict(sorted(normalized.items()))
