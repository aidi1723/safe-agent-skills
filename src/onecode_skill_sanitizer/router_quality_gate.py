"""Fail-closed production quality gates for router evaluation reports."""

from __future__ import annotations

import math
import re
from datetime import datetime
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

_DATASET_IDENTITY_FIELDS = {
    "case_count",
    "dataset_sha256",
    "labeling_generated_from_router",
    "labeling_method",
    "labeling_reviewed_at",
    "labeling_reviewer_role",
}
_REVIEW_IDENTITY_FIELDS = {
    "decision",
    "exceptions_count",
    "independence_attestation",
    "reviewed_at",
    "reviewed_case_count",
    "reviewed_commit",
    "reviewer_id",
    "reviewer_role",
    "rule_author_id",
    "suite_id",
    "suite_sha256",
}
_SHA256_PATTERN = re.compile(r"sha256:[0-9a-f]{64}\Z")
_COMMIT_PATTERN = re.compile(r"[0-9a-f]{40}\Z")
_UTC_TIMESTAMP_PATTERN = re.compile(
    r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?Z\Z"
)


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

    valid_dataset_identity = _dataset_identity(dataset_identity)
    if valid_dataset_identity is None:
        missing_gates.add("dataset_identity")
        valid_dataset_identity = {}
    valid_review_identity = _review_identity(review_identity)
    if valid_review_identity is None:
        missing_gates.add("independent_label_review")

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


def _dataset_identity(identity: object) -> dict[str, object] | None:
    if type(identity) is not dict or set(identity) != _DATASET_IDENTITY_FIELDS:
        return None
    if not _matches(identity["dataset_sha256"], _SHA256_PATTERN):
        return None
    if type(identity["case_count"]) is not int or identity["case_count"] <= 0:
        return None
    if identity["labeling_generated_from_router"] is not False:
        return None
    for field in ("labeling_method", "labeling_reviewed_at", "labeling_reviewer_role"):
        if not _exact_nonblank(identity[field]):
            return None
    return {field: identity[field] for field in sorted(_DATASET_IDENTITY_FIELDS)}


def _review_identity(identity: object) -> dict[str, object] | None:
    if type(identity) is not dict or set(identity) != _REVIEW_IDENTITY_FIELDS:
        return None
    for field in ("suite_id", "rule_author_id", "reviewer_id"):
        if not _exact_nonblank(identity[field]):
            return None
    if identity["reviewer_id"] == identity["rule_author_id"]:
        return None
    if not _matches(identity["suite_sha256"], _SHA256_PATTERN):
        return None
    if not _matches(identity["reviewed_commit"], _COMMIT_PATTERN):
        return None
    if identity["reviewer_role"] != "independent_dataset_review":
        return None
    if not _is_iso_utc_timestamp(identity["reviewed_at"]):
        return None
    if identity["decision"] != "accepted":
        return None
    if type(identity["independence_attestation"]) is not bool or not identity["independence_attestation"]:
        return None
    if type(identity["reviewed_case_count"]) is not int or identity["reviewed_case_count"] <= 0:
        return None
    if type(identity["exceptions_count"]) is not int or identity["exceptions_count"] < 0:
        return None
    return {field: identity[field] for field in sorted(_REVIEW_IDENTITY_FIELDS)}


def _exact_nonblank(value: object) -> bool:
    return type(value) is str and bool(value) and value == value.strip()


def _matches(value: object, pattern: re.Pattern[str]) -> bool:
    return type(value) is str and pattern.fullmatch(value) is not None


def _is_iso_utc_timestamp(value: object) -> bool:
    if type(value) is not str or _UTC_TIMESTAMP_PATTERN.fullmatch(value) is None:
        return False
    try:
        datetime.fromisoformat(value.removesuffix("Z") + "+00:00")
    except ValueError:
        return False
    return True
