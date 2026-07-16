from __future__ import annotations

import json
import math
from collections import Counter
from collections import deque
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
ACCEPTANCE_THRESHOLDS = {
    "forbidden_skill_false_positive_rate": ("lt", 0.02),
    "forbidden_scenario_false_positive_rate": ("lt", 0.02),
    "dag_validity": ("ge", 0.98),
    "dependency_edge_recall": ("ge", 0.70),
    "multi_intent_exact_match": ("ge", 0.92),
    "scenario_f1": ("ge", 0.96),
    "skill_f1": ("ge", 0.96),
    "recall_at_3": ("ge", 0.95),
    "top_1_accuracy": ("ge", 0.90),
    "no_skill_accuracy": ("ge", 0.90),
    "exact_selected_set_accuracy": ("ge", 0.85),
}

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
_CAPABILITY_NAME_SET = set(_SKILL_CAPABILITIES.values())
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


class EvaluatorError(ValueError):
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
    *,
    redact_expected_labels: bool = False,
) -> dict[str, Any]:
    scored = []
    for case in cases:
        try:
            route = route_builder(case)
            scored.append(_score_case(case, route))
        except EvaluatorError:
            raise
        except Exception as exc:
            case_id = case.get("id", "<unknown>") if isinstance(case, dict) else "<unknown>"
            raise EvaluatorError(f"case {case_id} failed: {exc}") from exc

    metrics = _aggregate_metrics(scored)
    by_category = {
        category: _aggregate_metrics(
            [item for item in scored if item["category"] == category]
        )
        for category in sorted({item["category"] for item in scored})
    }
    by_split = {
        split: _aggregate_metrics([item for item in scored if item["split"] == split])
        for split in sorted({item["split"] for item in scored})
    }
    cases_out = [
        {
            "id": item["id"],
            "category": item["category"],
            "passed": item["passed"],
            "failure_dimensions": item["failure_dimensions"],
        }
        if redact_expected_labels
        else item
        for item in scored
    ]
    report = {
        "status": "ok",
        "case_count": len(scored),
        "metrics": metrics,
        "metrics_by_category": by_category,
        "metrics_by_split": by_split,
        "acceptance": acceptance_gate(metrics),
        "cases": cases_out,
    }
    try:
        json.dumps(report, allow_nan=False)
    except (TypeError, ValueError) as exc:
        raise EvaluatorError("evaluation report must be finite JSON") from exc
    return report


def acceptance_gate(metrics: dict[str, float]) -> dict[str, Any]:
    checks = []
    for name, (operator, threshold) in ACCEPTANCE_THRESHOLDS.items():
        value = metrics.get(name)
        valid = (
            not isinstance(value, bool)
            and isinstance(value, (int, float))
            and math.isfinite(value)
        )
        passed = bool(
            valid
            and (value < threshold if operator == "lt" else value >= threshold)
        )
        checks.append(
            {
                "metric": name,
                "operator": operator,
                "threshold": threshold,
                "value": value if valid else None,
                "passed": passed,
            }
        )
    return {
        "status": "passed" if all(item["passed"] for item in checks) else "failed",
        "checks": checks,
    }


def _score_case(case: dict[str, Any], route: object) -> dict[str, Any]:
    if not isinstance(route, dict):
        raise EvaluatorError("route must be an object")
    need = route.get("need_decision")
    selection = route.get("selection")
    graph = route.get("execution_graph")
    candidates = route.get("candidates")
    if not (
        isinstance(need, dict)
        and isinstance(selection, dict)
        and isinstance(graph, dict)
        and isinstance(candidates, list)
    ):
        raise EvaluatorError("route is missing a v3 routing record")

    candidate_names = []
    for index, item in enumerate(candidates):
        if not isinstance(item, dict):
            raise EvaluatorError(f"candidates[{index}] must be an object")
        name = item.get("skill")
        if not isinstance(name, str) or not name:
            raise EvaluatorError("candidate names must be nonempty strings")
        if name not in _CANDIDATE_NAME_SET:
            raise EvaluatorError("candidate Skills must remain inside the cohort")
        score = item.get("final_score")
        if (
            isinstance(score, bool)
            or not isinstance(score, (int, float))
            or not math.isfinite(score)
        ):
            raise EvaluatorError("candidate final scores must be finite numbers")
        candidate_names.append(name)
    if len(candidate_names) != len(set(candidate_names)):
        raise EvaluatorError("candidate names must be unique")

    selected_items = selection.get("selected_skills")
    if not isinstance(selected_items, list):
        raise EvaluatorError("selection.selected_skills must be a list")
    actual_skills = []
    for index, item in enumerate(selected_items):
        if not isinstance(item, dict):
            raise EvaluatorError(
                f"selection.selected_skills[{index}] must be an object"
            )
        name = item.get("name")
        if not isinstance(name, str) or not name:
            raise EvaluatorError("selected Skill names must be nonempty strings")
        if name not in _CANDIDATE_NAME_SET:
            raise EvaluatorError("selected Skills must remain inside the cohort")
        actual_skills.append(name)
    if len(actual_skills) != len(set(actual_skills)):
        raise EvaluatorError("selected Skill names must be unique")
    if not set(actual_skills).issubset(candidate_names):
        raise EvaluatorError("selected Skills must appear in candidates")

    decision = need.get("decision")
    if not isinstance(decision, str) or decision not in NEED_VALUES:
        raise EvaluatorError("need decision is invalid")
    actual_intents = need.get("required_capabilities")
    if not isinstance(actual_intents, list) or not all(
        isinstance(item, str) and bool(item) for item in actual_intents
    ):
        raise EvaluatorError("need capabilities must be nonempty strings")
    if len(actual_intents) != len(set(actual_intents)):
        raise EvaluatorError("need capabilities must be unique")
    if not set(actual_intents).issubset(_CAPABILITY_NAME_SET):
        raise EvaluatorError("need capabilities must remain inside the cohort")
    _validate_evaluated_need(decision, actual_intents)

    routing_status = route.get("routing_status")
    if not isinstance(routing_status, str) or routing_status not in STATUS_VALUES:
        raise EvaluatorError("routing status is invalid")
    reasons = _selection_reasons(selection)
    actual_reason = _validate_route_coherence(
        decision,
        routing_status,
        actual_skills,
        reasons,
        graph,
    )
    actual_edges, dag_valid, graph_skills = _skill_edges_and_dag(graph)
    if (
        routing_status == "blocked"
        and actual_reason not in graph["reason_codes"]
    ):
        raise EvaluatorError("blocked route reason must match the execution graph")
    if graph.get("status") == "ready" and set(graph_skills) != set(actual_skills):
        raise EvaluatorError("ready graph nodes must match selected Skills")

    required = set(case["required_skills"])
    allowed = set(case["allowed_skills"])
    forbidden = set(case["forbidden_skills"])
    selected = set(actual_skills)
    accepted = required | allowed
    expected_intents = set(case["expected_intents"])
    actual_intent_set = set(actual_intents)
    expected_edges = {tuple(edge) for edge in case["expected_dependency_edges"]}
    failure_dimensions = []
    if decision != case["expected_need"]:
        failure_dimensions.append("need_decision")
    if routing_status != case["expected_status"]:
        failure_dimensions.append("routing_status")
    if case["expected_reason"] and actual_reason != case["expected_reason"]:
        failure_dimensions.append("routing_reason")
    if expected_intents != actual_intent_set:
        failure_dimensions.append("intent_capabilities")
    if required - selected:
        failure_dimensions.append("required_skill_recall")
    if selected - accepted:
        failure_dimensions.append("unexpected_skill")
    if selected & forbidden:
        failure_dimensions.append("forbidden_skill")
    if expected_edges - actual_edges:
        failure_dimensions.append("dependency_edge")
    if not dag_valid:
        failure_dimensions.append("dag_validity")

    return {
        "id": case["id"],
        "category": case["category"],
        "split": case["split"],
        "passed": not failure_dimensions,
        "failure_dimensions": failure_dimensions,
        "required_skills": sorted(required),
        "allowed_skills": sorted(allowed),
        "forbidden_skills": sorted(forbidden),
        "actual_skills": actual_skills,
        "expected_intents": sorted(expected_intents),
        "actual_intents": sorted(actual_intent_set),
        "expected_need": case["expected_need"],
        "actual_need": decision,
        "expected_status": case["expected_status"],
        "actual_status": routing_status,
        "expected_reason": case["expected_reason"],
        "actual_reason": actual_reason,
        "top_three": candidate_names[:3],
        "actual_edges": [list(edge) for edge in sorted(actual_edges)],
        "expected_edges": [list(edge) for edge in sorted(expected_edges)],
        "dag_valid": dag_valid,
    }


def _validate_evaluated_need(decision: str, capabilities: list[str]) -> None:
    if decision in {"none", "clarify"} and capabilities:
        raise EvaluatorError(f"need decision {decision} cannot require capabilities")
    if decision == "single" and len(capabilities) != 1:
        raise EvaluatorError("single need requires exactly one capability")
    if decision == "composite" and len(capabilities) < 2:
        raise EvaluatorError("composite need requires multiple capabilities")


def _selection_reasons(selection: dict[str, Any]) -> dict[str, str]:
    reasons = {}
    for field in ("clarification_reason", "abstention_reason", "failure_reason"):
        value = selection.get(field)
        if not isinstance(value, str):
            raise EvaluatorError(f"selection.{field} must be a string")
        reasons[field] = value
    return reasons


def _validate_route_coherence(
    decision: str,
    routing_status: str,
    selected_skills: list[str],
    reasons: dict[str, str],
    graph: dict[str, Any],
) -> str:
    graph_status = graph.get("status")
    clarification = reasons["clarification_reason"]
    abstention = reasons["abstention_reason"]
    failure = reasons["failure_reason"]
    if routing_status == "none":
        if decision != "none" or selected_skills or not abstention:
            raise EvaluatorError("none routing status is incoherent")
        if clarification or failure:
            raise EvaluatorError("none routing status has an unrelated reason")
        actual_reason = abstention
    elif routing_status == "clarify":
        if decision == "none" or not clarification:
            raise EvaluatorError("clarify routing status is incoherent")
        if abstention or failure:
            raise EvaluatorError("clarify routing status has an unrelated reason")
        actual_reason = clarification
    elif routing_status == "complete":
        if decision not in {"single", "composite"}:
            raise EvaluatorError("complete routing status is incoherent")
        if clarification or abstention or failure:
            raise EvaluatorError("complete routing status must not contain a reason")
        actual_reason = ""
    elif routing_status == "incomplete":
        if decision not in {"single", "composite"} or not failure:
            raise EvaluatorError("incomplete routing status is incoherent")
        if abstention:
            raise EvaluatorError("incomplete routing status has an unrelated reason")
        actual_reason = failure
    else:
        if decision not in {"single", "composite"} or not failure:
            raise EvaluatorError("blocked routing status is incoherent")
        if abstention:
            raise EvaluatorError("blocked routing status has an unrelated reason")
        actual_reason = failure

    expected_graph_status = "blocked" if routing_status == "blocked" else "ready"
    if graph_status != expected_graph_status:
        raise EvaluatorError("routing and execution graph statuses are incoherent")
    return actual_reason


_METRIC_NAMES = (
    "skill_precision",
    "skill_recall",
    "skill_f1",
    "scenario_f1",
    "recall_at_3",
    "top_1_accuracy",
    "mean_reciprocal_rank",
    "no_skill_accuracy",
    "exact_selected_set_accuracy",
    "multi_intent_exact_match",
    "forbidden_skill_false_positive_rate",
    "forbidden_scenario_false_positive_rate",
    "dependency_edge_recall",
    "dag_validity",
    "status_accuracy",
)


def _aggregate_metrics(items: list[dict[str, Any]]) -> dict[str, float]:
    if not items:
        return {
            name: (
                0.0
                if name
                in {
                    "forbidden_skill_false_positive_rate",
                    "forbidden_scenario_false_positive_rate",
                }
                else 1.0
            )
            for name in _METRIC_NAMES
        }

    true_positive = false_positive = false_negative = 0
    intent_tp = intent_fp = intent_fn = 0
    recalled_at_three = required_total = 0
    reciprocal_rank_total = 0.0
    positive_case_count = top_one_correct = 0
    no_skill_total = no_skill_correct = 0
    exact = multi_total = multi_exact = 0
    forbidden_total = forbidden_hits = 0
    dependency_total = dependency_hits = 0
    dag_valid = status_correct = 0
    for item in items:
        required = set(item["required_skills"])
        allowed = set(item["allowed_skills"])
        actual = set(item["actual_skills"])
        accepted = required | allowed
        true_positive += len(actual & accepted)
        false_positive += len(actual - accepted)
        false_negative += len(required - actual)

        expected_intents = set(item["expected_intents"])
        actual_intents = set(item["actual_intents"])
        intent_tp += len(expected_intents & actual_intents)
        intent_fp += len(actual_intents - expected_intents)
        intent_fn += len(expected_intents - actual_intents)

        if required:
            positive_case_count += 1
            top_one_correct += bool(
                item["top_three"] and item["top_three"][0] in accepted
            )
            for skill in required:
                required_total += 1
                if skill in item["top_three"]:
                    rank = item["top_three"].index(skill) + 1
                    recalled_at_three += 1
                    reciprocal_rank_total += 1 / rank

        if item["expected_need"] == "none":
            no_skill_total += 1
            no_skill_correct += item["actual_need"] == "none"
        exact += required.issubset(actual) and actual.issubset(accepted)
        if len(item["expected_intents"]) > 1:
            multi_total += 1
            multi_exact += expected_intents == actual_intents

        forbidden = set(item["forbidden_skills"])
        forbidden_total += len(forbidden)
        forbidden_hits += len(actual & forbidden)
        expected_edges = {tuple(edge) for edge in item["expected_edges"]}
        actual_edges = {tuple(edge) for edge in item["actual_edges"]}
        dependency_total += len(expected_edges)
        dependency_hits += len(expected_edges & actual_edges)
        dag_valid += bool(item["dag_valid"])
        status_correct += item["expected_status"] == item["actual_status"]

    precision = _ratio(true_positive, true_positive + false_positive, 1.0)
    recall = _ratio(true_positive, true_positive + false_negative, 1.0)
    intent_precision = _ratio(intent_tp, intent_tp + intent_fp, 1.0)
    intent_recall = _ratio(intent_tp, intent_tp + intent_fn, 1.0)
    forbidden_rate = _ratio(forbidden_hits, forbidden_total, 0.0)
    metrics = {
        "skill_precision": precision,
        "skill_recall": recall,
        "skill_f1": _f1(precision, recall),
        "scenario_f1": _f1(intent_precision, intent_recall),
        "recall_at_3": _ratio(recalled_at_three, required_total, 1.0),
        "top_1_accuracy": _ratio(top_one_correct, positive_case_count, 1.0),
        "mean_reciprocal_rank": _ratio(
            reciprocal_rank_total, required_total, 1.0
        ),
        "no_skill_accuracy": _ratio(no_skill_correct, no_skill_total, 1.0),
        "exact_selected_set_accuracy": exact / len(items),
        "multi_intent_exact_match": _ratio(multi_exact, multi_total, 1.0),
        "forbidden_skill_false_positive_rate": forbidden_rate,
        "forbidden_scenario_false_positive_rate": forbidden_rate,
        "dependency_edge_recall": _ratio(
            dependency_hits, dependency_total, 1.0
        ),
        "dag_validity": dag_valid / len(items),
        "status_accuracy": status_correct / len(items),
    }
    if not all(math.isfinite(value) for value in metrics.values()):
        raise EvaluatorError("metrics must be finite")
    return metrics


def _skill_edges_and_dag(
    graph: dict[str, Any],
) -> tuple[set[tuple[str, str]], bool, list[str]]:
    nodes = graph.get("nodes")
    edges = graph.get("edges")
    if not isinstance(nodes, list) or not isinstance(edges, list):
        raise EvaluatorError("execution graph nodes and edges must be lists")
    status = graph.get("status")
    if status not in {"ready", "blocked"}:
        raise EvaluatorError("execution graph status is invalid")
    declared = graph.get("acyclic")
    if not isinstance(declared, bool):
        raise EvaluatorError("execution graph acyclic must be boolean")
    reason_codes = graph.get("reason_codes")
    if not isinstance(reason_codes, list) or not all(
        isinstance(reason, str) and bool(reason) for reason in reason_codes
    ):
        raise EvaluatorError("execution graph reason_codes must be nonempty strings")
    if len(reason_codes) != len(set(reason_codes)):
        raise EvaluatorError("execution graph reason_codes must be unique")

    skill_by_id = {}
    graph_skills = []
    for index, node in enumerate(nodes):
        if not isinstance(node, dict):
            raise EvaluatorError(f"execution graph nodes[{index}] must be an object")
        node_id = node.get("id")
        skill = node.get("skill")
        if not isinstance(node_id, str) or not node_id:
            raise EvaluatorError("execution graph node IDs must be nonempty strings")
        if not isinstance(skill, str) or not skill:
            raise EvaluatorError("execution graph node Skills must be nonempty strings")
        if skill not in _CANDIDATE_NAME_SET:
            raise EvaluatorError("execution graph node Skills must remain inside the cohort")
        if node_id in skill_by_id:
            raise EvaluatorError("execution graph node IDs must be unique")
        if skill in graph_skills:
            raise EvaluatorError("execution graph node Skills must be unique")
        skill_by_id[node_id] = skill
        graph_skills.append(skill)

    indegree = {node_id: 0 for node_id in skill_by_id}
    outgoing = {node_id: [] for node_id in skill_by_id}
    skill_edges = set()
    edge_records = set()
    for index, edge in enumerate(edges):
        if not isinstance(edge, dict):
            raise EvaluatorError(f"execution graph edges[{index}] must be an object")
        source = edge.get("from")
        target = edge.get("to")
        edge_type = edge.get("type")
        evidence = edge.get("evidence")
        if source not in indegree or target not in indegree:
            raise EvaluatorError("execution graph edge references an unknown node")
        if source == target:
            raise EvaluatorError("execution graph edge must not be a self edge")
        if not isinstance(edge_type, str) or not edge_type:
            raise EvaluatorError("execution graph edge type must be nonempty")
        if not isinstance(evidence, str) or not evidence:
            raise EvaluatorError("execution graph edge evidence must be nonempty")
        record = (source, target, edge_type, evidence)
        if record in edge_records:
            raise EvaluatorError("execution graph edges must be unique")
        edge_records.add(record)
        outgoing[source].append(target)
        indegree[target] += 1
        skill_edges.add((skill_by_id[source], skill_by_id[target]))

    ready = deque(sorted(node_id for node_id, degree in indegree.items() if degree == 0))
    visited = 0
    while ready:
        node_id = ready.popleft()
        visited += 1
        for target in sorted(outgoing[node_id]):
            indegree[target] -= 1
            if indegree[target] == 0:
                ready.append(target)
    computed_acyclic = visited == len(indegree)

    if status == "blocked":
        if declared or nodes or edges or not reason_codes:
            raise EvaluatorError("blocked execution graph is incoherent")
        return skill_edges, True, graph_skills
    if reason_codes:
        raise EvaluatorError("ready execution graph must not contain reason codes")
    if not computed_acyclic:
        raise EvaluatorError("unexpected cycle in execution graph")
    if declared != computed_acyclic:
        raise EvaluatorError("execution graph acyclic declaration mismatches topology")
    return skill_edges, True, graph_skills


def _ratio(numerator: float, denominator: float, empty: float) -> float:
    value = empty if denominator == 0 else numerator / denominator
    if not math.isfinite(value):
        raise EvaluatorError("metric ratios must be finite")
    return value


def _f1(precision: float, recall: float) -> float:
    value = (
        0.0
        if precision + recall == 0
        else 2 * precision * recall / (precision + recall)
    )
    if not math.isfinite(value):
        raise EvaluatorError("metric F1 values must be finite")
    return value
