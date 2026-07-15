from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any, Callable

from .need_gate import CAPABILITY_SKILL
from .skill_candidates import HIGH_FREQUENCY_ENTRY_NAMES
from .skill_candidates import HIGH_FREQUENCY_SKILL_NAMES


CASE_KEYS = {
    "id",
    "split",
    "category",
    "query",
    "expected_need",
    "expected_intents",
    "required_skills",
    "allowed_skills",
    "forbidden_skills",
    "expected_dependency_edges",
    "expected_status",
    "expected_reason",
}
CATEGORY_COUNTS = {
    "single_positive": 48,
    "near_miss": 24,
    "no_skill": 16,
    "multi_skill": 16,
    "dependency_conflict": 16,
}
NEED_VALUES = {"none", "single", "composite", "clarify"}
STATUS_VALUES = {"none", "clarify", "complete", "incomplete", "blocked"}

_TOP_LEVEL_KEYS = {"schema_version", "cohort", "labeling", "cases"}
_CANDIDATE_NAME_SET = set(HIGH_FREQUENCY_SKILL_NAMES)
_EXPECTED_COHORT = {
    "entry_names": list(HIGH_FREQUENCY_ENTRY_NAMES),
    "candidate_names": list(HIGH_FREQUENCY_SKILL_NAMES),
}
_EXPECTED_LABELING = {
    "method": "manual_review",
    "reviewer_role": "independent_dataset_review",
    "generated_from_router": False,
    "reviewed_at": "2026-07-15",
    "runtime_examples_visible_during_labeling": False,
}
_COHORT_CAPABILITY_ITEMS = [
    (capability, skill)
    for capability, skill in CAPABILITY_SKILL.items()
    if skill in HIGH_FREQUENCY_SKILL_NAMES
]
_SKILL_CAPABILITIES = {
    skill: capability for capability, skill in _COHORT_CAPABILITY_ITEMS
}
if (
    len(_COHORT_CAPABILITY_ITEMS) != len(HIGH_FREQUENCY_SKILL_NAMES)
    or set(_SKILL_CAPABILITIES) != _CANDIDATE_NAME_SET
):
    raise RuntimeError("high-frequency capabilities must map one-to-one to the cohort")
_CATEGORY_ID_PREFIXES = {
    "single_positive": "hf-single",
    "near_miss": "hf-near",
    "no_skill": "hf-none",
    "multi_skill": "hf-multi",
    "dependency_conflict": "hf-dependency",
}
_EXPECTED_IDS_BY_CATEGORY = {
    category: {
        f"{_CATEGORY_ID_PREFIXES[category]}-{number:03d}"
        for number in range(1, count + 1)
    }
    for category, count in CATEGORY_COUNTS.items()
}
_EXPECTED_CASE_COUNT = sum(CATEGORY_COUNTS.values())
_SPLIT_VALUES = {"validation", "final_test"}
_REASON_REQUIRED_STATUSES = {"clarify", "incomplete", "blocked"}


class DatasetValidationError(ValueError):
    pass


def load_eval_dataset_v3(path: Path) -> list[dict[str, Any]]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise DatasetValidationError(f"unable to read evaluation dataset: {exc}") from exc
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise DatasetValidationError(f"invalid evaluation JSON: {exc}") from exc

    if not isinstance(payload, dict) or set(payload) != _TOP_LEVEL_KEYS:
        raise DatasetValidationError(
            "evaluation dataset must contain only schema_version, cohort, labeling, and cases"
        )
    if type(payload["schema_version"]) is not int or payload["schema_version"] != 1:
        raise DatasetValidationError("evaluation dataset schema_version must be 1")
    if payload["cohort"] != _EXPECTED_COHORT:
        raise DatasetValidationError("evaluation dataset cohort is invalid")
    labeling = payload["labeling"]
    if (
        not isinstance(labeling, dict)
        or labeling != _EXPECTED_LABELING
        or type(labeling.get("generated_from_router")) is not bool
        or type(labeling.get("runtime_examples_visible_during_labeling")) is not bool
    ):
        raise DatasetValidationError("evaluation dataset labeling metadata is invalid")

    cases = payload["cases"]
    if not isinstance(cases, list):
        raise DatasetValidationError("cases must be a list")
    validated = [_validate_case(case, index) for index, case in enumerate(cases)]
    _validate_dataset_shape(validated)
    return validated


def _validate_case(case: object, index: int) -> dict[str, Any]:
    prefix = f"cases[{index}]"
    if not isinstance(case, dict):
        raise DatasetValidationError(f"{prefix} must be an object")
    if set(case) != CASE_KEYS:
        missing = sorted(CASE_KEYS - set(case))
        unknown = sorted(set(case) - CASE_KEYS)
        detail = []
        if missing:
            detail.append(f"missing fields: {', '.join(missing)}")
        if unknown:
            detail.append(f"unknown fields: {', '.join(unknown)}")
        raise DatasetValidationError(f"{prefix} {'; '.join(detail)}")

    case_id = _require_nonempty_string(case["id"], f"{prefix}.id")
    query = _require_nonempty_string(case["query"], f"{prefix}.query")
    split = case["split"]
    category = case["category"]
    expected_need = case["expected_need"]
    expected_status = case["expected_status"]
    expected_reason = case["expected_reason"]

    if not isinstance(split, str) or split not in _SPLIT_VALUES:
        raise DatasetValidationError(f"{prefix}.split is invalid")
    if not isinstance(category, str) or category not in CATEGORY_COUNTS:
        raise DatasetValidationError(f"{prefix}.category is invalid")
    if case_id not in _EXPECTED_IDS_BY_CATEGORY[category]:
        raise DatasetValidationError(f"{prefix}.id is invalid for its category")
    case_number = int(case_id.rsplit("-", 1)[1])
    expected_split = "validation" if case_number % 2 else "final_test"
    if split != expected_split:
        raise DatasetValidationError(f"{prefix}.split does not match id parity")
    if not isinstance(expected_need, str) or expected_need not in NEED_VALUES:
        raise DatasetValidationError(f"{prefix}.expected_need is invalid")
    if not isinstance(expected_status, str) or expected_status not in STATUS_VALUES:
        raise DatasetValidationError(f"{prefix}.expected_status is invalid")
    if not isinstance(expected_reason, str):
        raise DatasetValidationError(f"{prefix}.expected_reason must be a string")

    expected_intents = _require_unique_string_list(
        case["expected_intents"], f"{prefix}.expected_intents"
    )
    required_skills = _require_unique_string_list(
        case["required_skills"], f"{prefix}.required_skills"
    )
    allowed_skills = _require_unique_string_list(
        case["allowed_skills"], f"{prefix}.allowed_skills"
    )
    forbidden_skills = _require_unique_string_list(
        case["forbidden_skills"], f"{prefix}.forbidden_skills"
    )
    for field, values in (
        ("required_skills", required_skills),
        ("allowed_skills", allowed_skills),
        ("forbidden_skills", forbidden_skills),
    ):
        unknown = sorted(set(values) - _CANDIDATE_NAME_SET)
        if unknown:
            raise DatasetValidationError(
                f"{prefix}.{field} contains out-of-cohort skills: {', '.join(unknown)}"
            )
    if set(required_skills) & set(forbidden_skills):
        raise DatasetValidationError(f"{prefix} required and forbidden skills overlap")
    if set(allowed_skills) & set(forbidden_skills):
        raise DatasetValidationError(f"{prefix} allowed and forbidden skills overlap")

    mapped_intents = [_SKILL_CAPABILITIES[skill] for skill in required_skills]
    if expected_intents != mapped_intents:
        raise DatasetValidationError(
            f"{prefix}.expected_intents must match required_skills"
        )
    _validate_need_coherence(prefix, expected_need, required_skills)
    _validate_status_coherence(prefix, expected_status, expected_need, expected_reason)
    _validate_edges(case["expected_dependency_edges"], required_skills, prefix)

    validated = dict(case)
    validated["query"] = query
    return validated


def _validate_need_coherence(
    prefix: str,
    expected_need: str,
    required_skills: list[str],
) -> None:
    required_count = len(required_skills)
    if expected_need in {"none", "clarify"} and required_count:
        raise DatasetValidationError(
            f"{prefix}.expected_need {expected_need} cannot require skills"
        )
    if expected_need == "single" and required_count != 1:
        raise DatasetValidationError(
            f"{prefix}.expected_need single requires exactly one skill"
        )
    if expected_need == "composite" and required_count < 2:
        raise DatasetValidationError(
            f"{prefix}.expected_need composite requires multiple skills"
        )


def _validate_status_coherence(
    prefix: str,
    expected_status: str,
    expected_need: str,
    expected_reason: str,
) -> None:
    if expected_status == "none" and expected_need != "none":
        raise DatasetValidationError(f"{prefix}.expected_status none requires need none")
    if expected_status == "clarify" and expected_need != "clarify":
        raise DatasetValidationError(
            f"{prefix}.expected_status clarify requires need clarify"
        )
    if expected_status in {"complete", "incomplete"} and expected_need not in {
        "single",
        "composite",
    }:
        raise DatasetValidationError(
            f"{prefix}.expected_status {expected_status} requires a skill selection"
        )
    if expected_status in _REASON_REQUIRED_STATUSES and not expected_reason.strip():
        raise DatasetValidationError(
            f"{prefix}.expected_status {expected_status} requires expected_reason"
        )


def _validate_edges(value: object, required_skills: list[str], prefix: str) -> None:
    field = f"{prefix}.expected_dependency_edges"
    if not isinstance(value, list):
        raise DatasetValidationError(f"{field} must be a list")
    normalized: list[tuple[str, str]] = []
    required = set(required_skills)
    for index, edge in enumerate(value):
        edge_prefix = f"{field}[{index}]"
        if not isinstance(edge, list) or len(edge) != 2:
            raise DatasetValidationError(f"{edge_prefix} must be a two-item list")
        source = _require_nonempty_string(edge[0], f"{edge_prefix}[0]")
        target = _require_nonempty_string(edge[1], f"{edge_prefix}[1]")
        if source == target:
            raise DatasetValidationError(f"{edge_prefix} must not be a self edge")
        if source not in required or target not in required:
            raise DatasetValidationError(
                f"{edge_prefix} endpoints must exist in required_skills"
            )
        normalized.append((source, target))
    if len(normalized) != len(set(normalized)):
        raise DatasetValidationError(f"{field} must not contain duplicates")


def _validate_dataset_shape(cases: list[dict[str, Any]]) -> None:
    if len(cases) != _EXPECTED_CASE_COUNT:
        raise DatasetValidationError(
            f"expected exactly {_EXPECTED_CASE_COUNT} cases, found {len(cases)}"
        )
    ids = [case["id"] for case in cases]
    if len(ids) != len(set(ids)):
        raise DatasetValidationError("case ids must be unique")
    expected_ids = set().union(*_EXPECTED_IDS_BY_CATEGORY.values())
    if set(ids) != expected_ids:
        raise DatasetValidationError("case ids do not match the fixed evaluation cohort")
    queries = [_normalize_query(case["query"]) for case in cases]
    if len(queries) != len(set(queries)):
        raise DatasetValidationError("normalized case queries must be unique")

    category_counts = Counter(case["category"] for case in cases)
    if category_counts != Counter(CATEGORY_COUNTS):
        raise DatasetValidationError(
            f"category counts must be {CATEGORY_COUNTS}, found {dict(category_counts)}"
        )
    split_counts = Counter(case["split"] for case in cases)
    if split_counts != Counter({"validation": 60, "final_test": 60}):
        raise DatasetValidationError(
            "split counts must be validation=60 and final_test=60"
        )
    for category, count in CATEGORY_COUNTS.items():
        category_splits = Counter(
            case["split"] for case in cases if case["category"] == category
        )
        expected = Counter({"validation": count // 2, "final_test": count // 2})
        if category_splits != expected:
            raise DatasetValidationError(
                f"category {category} must be evenly balanced across splits"
            )


def _require_nonempty_string(value: object, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise DatasetValidationError(f"{field} must be a nonempty string")
    return value


def _require_unique_string_list(value: object, field: str) -> list[str]:
    if not isinstance(value, list) or not all(
        isinstance(item, str) and bool(item.strip()) for item in value
    ):
        raise DatasetValidationError(f"{field} must be a list of nonempty strings")
    if len(value) != len(set(value)):
        raise DatasetValidationError(f"{field} must not contain duplicates")
    return value


def _normalize_query(query: str) -> str:
    return " ".join(query.casefold().split())


def evaluate_router_v3(
    cases: list[dict[str, Any]],
    route_builder: Callable[[dict[str, Any]], dict[str, Any]],
) -> dict[str, Any]:
    raise NotImplementedError("router v3 evaluation is not complete")
