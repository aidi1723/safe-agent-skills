"""Independent evaluation for hybrid router v2 multi-intent routes."""

from __future__ import annotations

import json
import math
from collections import Counter
from collections import defaultdict, deque
from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Any

from .router_quality_metrics import finite_ratio
from .router_quality_metrics import macro_classification_metrics


CATEGORY_DISTRIBUTION = {
    "compound": 40,
    "sequential": 20,
    "vague_context": 15,
    "negative": 10,
    "multilingual_typo_paraphrase": 10,
    "safety_sensitive": 5,
}
EXPECTED_CASE_COUNT = 100
DEPENDENCY_EDGE_TYPES = {
    "intent_verification_dependency",
    "intent_completion_dependency",
}
INCOMPLETE_GRAPH_REASONS = {
    "incomplete_composition",
    "missing_required_capability",
}
EXPECTED_STATUSES = {"complete", "incomplete", "blocked"}
TRUSTED_SCENARIO_IDS = {
    "agent-long-term-memory-governance",
    "agent-planning-orchestration",
    "agent-role-library-governance",
    "agentic-media-production",
    "claude-skills-backlog-coverage",
    "code-review-hardening",
    "codebase-change-lifecycle",
    "codebase-graph-intelligence",
    "commerce-listing-growth",
    "content-seo-publication",
    "content-video-production",
    "data-analysis-report",
    "design-md-system-governance",
    "document-to-knowledge-base",
    "industry-application-orchestration",
    "investment-research-diligence",
    "multi-platform-research-discovery",
    "open-source-release",
    "private-communication-governance",
    "rag-agent-knowledge-app",
    "security-agent-guardrails",
    "skill-router-quality-review",
    "website-build-launch",
}
REQUIRED_FIELDS = {
    "id",
    "category",
    "task",
    "expected_intents",
    "expected_scenarios",
    "required_dependency_edges",
    "forbidden_scenarios",
}
OPTIONAL_FIELDS = {"expected_status", "forbidden_skills"}
EXPECTED_LABELING = {
    "method": "manual_review",
    "reviewer_role": "independent_dataset_review",
    "generated_from_router": False,
    "reviewed_at": "2026-07-10",
}
LEGACY_ROUTER_EVAL_V2_FIELDS = {
    "schema_version",
    "dataset",
    "split",
    "case_count",
    "cases",
}
_MISSING_SUPPORT = object()


class DatasetValidationError(ValueError):
    pass


class EvaluatorError(RuntimeError):
    pass


def _is_exact_nonblank_string(value: object) -> bool:
    return type(value) is str and bool(value) and value == value.strip()


def _is_legacy_router_eval_v2(payload: object) -> bool:
    if not isinstance(payload, dict):
        return False
    cases = payload.get("cases")
    case_count = payload.get("case_count")
    valid_envelope = (
        LEGACY_ROUTER_EVAL_V2_FIELDS.issubset(payload)
        and "labeling" not in payload
        and payload.get("schema_version") == 2
        and isinstance(payload.get("dataset"), str)
        and bool(payload["dataset"])
        and payload.get("split") == "regression"
        and isinstance(cases, list)
        and isinstance(case_count, int)
        and not isinstance(case_count, bool)
        and case_count == len(cases)
    )
    if not valid_envelope:
        return False
    case_ids = [case.get("id") if isinstance(case, dict) else None for case in cases]
    invalid_case_id = any(not isinstance(case_id, str) or not case_id for case_id in case_ids)
    return not invalid_case_id and len(case_ids) == len(set(case_ids))


def load_eval_dataset_v2(
    path: Path,
    known_scenarios: set[str] | None = None,
) -> list[dict[str, Any]]:
    allowed_scenarios = TRUSTED_SCENARIO_IDS if known_scenarios is None else known_scenarios
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise DatasetValidationError(f"unable to read evaluation dataset: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise DatasetValidationError(f"invalid evaluation JSON: {exc}") from exc
    if _is_legacy_router_eval_v2(payload):
        raise DatasetValidationError(
            "this is a router-eval dataset; use router-eval. "
            "router-eval-v2 expects the multi-intent gold/suite contract"
        )
    if not isinstance(payload, dict) or set(payload) != {"labeling", "cases"}:
        raise DatasetValidationError("evaluation dataset must be an object containing only labeling and cases")
    if payload["labeling"] != EXPECTED_LABELING:
        raise DatasetValidationError("evaluation dataset labeling metadata is invalid")
    cases = payload["cases"]
    if not isinstance(cases, list):
        raise DatasetValidationError("cases must be a list")
    validated = [_validate_case(case, index, allowed_scenarios) for index, case in enumerate(cases)]
    if len(validated) != EXPECTED_CASE_COUNT:
        raise DatasetValidationError(f"expected exactly {EXPECTED_CASE_COUNT} cases, found {len(validated)}")
    ids = [case["id"] for case in validated]
    duplicates = sorted(case_id for case_id, count in Counter(ids).items() if count > 1)
    if duplicates:
        raise DatasetValidationError(f"duplicate case ids: {', '.join(duplicates)}")
    distribution = Counter(case["category"] for case in validated)
    if distribution != Counter(CATEGORY_DISTRIBUTION):
        raise DatasetValidationError(
            f"category distribution must be {CATEGORY_DISTRIBUTION}, found {dict(distribution)}"
        )
    return validated


def dataset_identity_v2(case_count: int) -> dict[str, object]:
    """Return stable identity fields for an already validated v2 dataset."""

    if type(case_count) is not int or case_count <= 0:
        raise DatasetValidationError("dataset identity case_count must be a positive integer")
    return {
        "case_count": case_count,
        "labeling_method": EXPECTED_LABELING["method"],
        "labeling_reviewed_at": EXPECTED_LABELING["reviewed_at"],
        "labeling_reviewer_role": EXPECTED_LABELING["reviewer_role"],
    }


def _validate_case(
    case: object,
    index: int,
    known_scenarios: set[str] | None,
) -> dict[str, Any]:
    prefix = f"cases[{index}]"
    if not isinstance(case, dict):
        raise DatasetValidationError(f"{prefix} must be an object")
    fields = set(case)
    missing = sorted(REQUIRED_FIELDS - fields)
    unknown = sorted(fields - REQUIRED_FIELDS - OPTIONAL_FIELDS)
    if missing:
        raise DatasetValidationError(f"{prefix} missing fields: {', '.join(missing)}")
    if unknown:
        raise DatasetValidationError(f"{prefix} has unknown fields: {', '.join(unknown)}")
    _require_nonempty_string(case["id"], f"{prefix}.id")
    _require_nonempty_string(case["task"], f"{prefix}.task")
    category = case["category"]
    if not isinstance(category, str) or category not in CATEGORY_DISTRIBUTION:
        raise DatasetValidationError(f"{prefix}.category is invalid")
    _require_string_list(case["expected_intents"], f"{prefix}.expected_intents", nonempty=True)
    if len(set(case["expected_intents"])) != len(case["expected_intents"]):
        raise DatasetValidationError(f"{prefix}.expected_intents must not contain duplicates")
    _require_string_list(case["expected_scenarios"], f"{prefix}.expected_scenarios")
    _require_string_list(case["forbidden_scenarios"], f"{prefix}.forbidden_scenarios")
    forbidden_skills = case.get("forbidden_skills", [])
    if not isinstance(forbidden_skills, list) or not all(
        _is_exact_nonblank_string(name) for name in forbidden_skills
    ):
        raise DatasetValidationError(f"{prefix}.forbidden_skills must be a list of exact nonempty strings")
    if len(set(forbidden_skills)) != len(forbidden_skills):
        raise DatasetValidationError(f"{prefix}.forbidden_skills must not contain duplicates")
    if len(set(case["expected_scenarios"])) != len(case["expected_scenarios"]):
        raise DatasetValidationError(f"{prefix}.expected_scenarios must not contain duplicates")
    if len(set(case["forbidden_scenarios"])) != len(case["forbidden_scenarios"]):
        raise DatasetValidationError(f"{prefix}.forbidden_scenarios must not contain duplicates")
    if known_scenarios is not None:
        unknown = sorted(set(case["expected_scenarios"]) - known_scenarios)
        if unknown:
            raise DatasetValidationError(f"{prefix}.expected_scenarios contains unknown ids: {', '.join(unknown)}")
        unknown_forbidden = sorted(set(case["forbidden_scenarios"]) - known_scenarios)
        if unknown_forbidden:
            raise DatasetValidationError(
                f"{prefix}.forbidden_scenarios contains unknown ids: {', '.join(unknown_forbidden)}"
            )
    overlap = set(case["expected_scenarios"]) & set(case["forbidden_scenarios"])
    if overlap:
        raise DatasetValidationError(f"{prefix} expected and forbidden scenarios overlap")
    edges = case["required_dependency_edges"]
    if not isinstance(edges, list):
        raise DatasetValidationError(f"{prefix}.required_dependency_edges must be a list")
    normalized_edges: list[list[str]] = []
    for edge_index, edge in enumerate(edges):
        edge_prefix = f"{prefix}.required_dependency_edges[{edge_index}]"
        if not isinstance(edge, list) or len(edge) != 2:
            raise DatasetValidationError(f"{edge_prefix} must be a two-item list")
        _require_nonempty_string(edge[0], f"{edge_prefix}[0]")
        _require_nonempty_string(edge[1], f"{edge_prefix}[1]")
        if edge[0] == edge[1]:
            raise DatasetValidationError(f"{edge_prefix} must not be a self edge")
        if edge[0] not in case["expected_intents"] or edge[1] not in case["expected_intents"]:
            raise DatasetValidationError(f"{edge_prefix} endpoints must exist in expected_intents")
        normalized_edges.append([edge[0], edge[1]])
    if len({tuple(edge) for edge in normalized_edges}) != len(normalized_edges):
        raise DatasetValidationError(f"{prefix}.required_dependency_edges has duplicates")
    expected_status = case.get("expected_status")
    if expected_status is not None and (
        not isinstance(expected_status, str) or expected_status not in EXPECTED_STATUSES
    ):
        raise DatasetValidationError(f"{prefix}.expected_status is invalid")
    return {**case, "forbidden_skills": list(forbidden_skills)}


def _require_nonempty_string(value: object, field: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise DatasetValidationError(f"{field} must be a nonempty string")


def _require_string_list(value: object, field: str, *, nonempty: bool = False) -> None:
    if not isinstance(value, list) or not all(isinstance(item, str) and bool(item.strip()) for item in value):
        raise DatasetValidationError(f"{field} must be a list of nonempty strings")
    if nonempty and not value:
        raise DatasetValidationError(f"{field} must not be empty")


def evaluate_router_v2(
    cases: list[dict[str, Any]],
    *,
    route_builder: Callable[[dict[str, Any]], dict[str, Any]],
    known_scenarios: set[str] | None = None,
    bundle_required_capabilities: object = _MISSING_SUPPORT,
    core_bundle_contract_counts: object = _MISSING_SUPPORT,
) -> dict[str, Any]:
    capability_context = _validate_bundle_required_capabilities(bundle_required_capabilities)
    expected_scenarios = {
        scenario_id
        for case in cases
        for scenario_id in case["expected_scenarios"]
    }
    missing_capability_context = sorted(expected_scenarios - set(capability_context))
    if missing_capability_context:
        raise EvaluatorError(
            "missing required capability context for expected scenarios: "
            + ", ".join(missing_capability_context)
        )
    core_contract_covered, core_contract_total = _validate_support_counts(
        core_bundle_contract_counts,
        "core bundle contract",
    )
    intent_exact = 0
    scenario_true_positive = 0
    scenario_predicted = 0
    scenario_expected = 0
    forbidden_hits = 0
    forbidden_total = 0
    dependency_hits = 0
    dependency_total = 0
    dependency_predicted = 0
    required_capability_hits = 0
    required_capability_total = 0
    forbidden_skill_hits = 0
    forbidden_skill_total = 0
    high_confidence_error_cases = 0
    high_confidence_cases = 0
    dag_valid = 0
    results = []
    expected_task_types: list[set[str]] = []
    actual_task_types: list[set[str]] = []

    for case in cases:
        try:
            route = route_builder(case)
            result = _evaluate_case(case, route, capability_context)
        except EvaluatorError:
            raise
        except Exception as exc:
            raise EvaluatorError(f"case {case.get('id', '<unknown>')} failed: {exc}") from exc
        counts = result.pop("counts")
        intent_exact += counts["intent_exact"]
        scenario_true_positive += counts["scenario_true_positive"]
        scenario_predicted += counts["scenario_predicted"]
        scenario_expected += counts["scenario_expected"]
        forbidden_hits += counts["forbidden_hits"]
        forbidden_total += counts["forbidden_total"]
        dependency_hits += counts["dependency_hits"]
        dependency_total += counts["dependency_total"]
        dependency_predicted += counts["dependency_predicted"]
        required_capability_hits += counts["required_capability_hits"]
        required_capability_total += counts["required_capability_total"]
        forbidden_skill_hits += counts["forbidden_skill_hits"]
        forbidden_skill_total += counts["forbidden_skill_total"]
        high_confidence_error_cases += counts["high_confidence_error"]
        high_confidence_cases += counts["high_confidence_case"]
        dag_valid += counts["dag_valid"]
        expected_task_types.append(set(case["expected_intents"]))
        actual_task_types.append(set(result["actual_intents"]))
        results.append(result)

    case_count = len(cases)
    precision = _quality_ratio(scenario_true_positive, scenario_predicted, scenario_expected)
    recall = _quality_ratio(scenario_true_positive, scenario_expected, scenario_predicted)
    f1 = 0.0 if precision + recall == 0 else 2 * precision * recall / (precision + recall)
    task_type_metrics = macro_classification_metrics(expected_task_types, actual_task_types)
    metrics = {
        "multi_intent_exact_match": _ratio(intent_exact, case_count, empty=1.0),
        "scenario_precision": precision,
        "scenario_recall": recall,
        "scenario_f1": f1,
        "task_type_macro_precision": task_type_metrics["precision"],
        "task_type_macro_recall": task_type_metrics["recall"],
        "task_type_macro_f1": task_type_metrics["f1"],
        "required_capability_recall": finite_ratio(
            required_capability_hits,
            required_capability_total,
            empty=1.0,
        ),
        "forbidden_scenario_false_positive_rate": _ratio(forbidden_hits, forbidden_total, empty=0.0),
        "forbidden_skill_false_positive_rate": finite_ratio(
            forbidden_skill_hits,
            forbidden_skill_total,
            empty=0.0,
        ),
        "dependency_edge_precision": finite_ratio(
            dependency_hits,
            dependency_predicted,
            empty=1.0 if dependency_total == 0 else 0.0,
        ),
        "dependency_edge_recall": finite_ratio(dependency_hits, dependency_total, empty=1.0),
        "dag_validity": _ratio(dag_valid, case_count, empty=1.0),
        "high_confidence_error_rate": finite_ratio(
            high_confidence_error_cases,
            high_confidence_cases,
            empty=0.0,
        ),
        "core_bundle_contract_coverage": finite_ratio(
            core_contract_covered,
            core_contract_total,
            empty=0.0,
        ),
    }
    if not all(math.isfinite(value) for value in metrics.values()):
        raise EvaluatorError("metrics must be finite")
    expected_scenario_coverage = sorted({scenario for case in cases for scenario in case["expected_scenarios"]})
    return {
        "schema_version": 1,
        "case_count": case_count,
        "category_counts": dict(sorted(Counter(case["category"] for case in cases).items())),
        "metrics": metrics,
        "counts": {
            "intent_exact_cases": intent_exact,
            "scenario_true_positive": scenario_true_positive,
            "scenario_predicted": scenario_predicted,
            "scenario_expected": scenario_expected,
            "forbidden_hits": forbidden_hits,
            "forbidden_total": forbidden_total,
            "dependency_hits": dependency_hits,
            "dependency_predicted": dependency_predicted,
            "dependency_total": dependency_total,
            "required_capability_hits": required_capability_hits,
            "required_capability_total": required_capability_total,
            "forbidden_skill_hits": forbidden_skill_hits,
            "forbidden_skill_total": forbidden_skill_total,
            "high_confidence_error_cases": high_confidence_error_cases,
            "high_confidence_cases": high_confidence_cases,
            "task_type_label_count": len(task_type_metrics["per_label"]),
            "task_type_by_label": [
                {
                    "task_type": task_type,
                    **task_type_metrics["per_label"][task_type]["counts"],
                }
                for task_type in sorted(task_type_metrics["per_label"])
            ],
            "core_bundle_contract_covered": core_contract_covered,
            "core_bundle_contract_total": core_contract_total,
            "core_bundle_contract_available": core_contract_total > 0,
            "required_capability_context_available": True,
            "dag_valid_cases": dag_valid,
        },
        "scenario_coverage": {
            "expected_scenarios": expected_scenario_coverage,
            "uncovered_scenarios": sorted((known_scenarios or set()) - set(expected_scenario_coverage)),
        },
        "dag_definition": (
            "Valid means complete routes have an acyclic ready graph, while incomplete "
            "or blocked routes have an empty, topologically acyclic blocked graph with "
            "an incomplete_composition or missing_required_capability compiler reason."
        ),
        "cases": results,
    }


def _evaluate_case(
    case: dict[str, Any],
    route: object,
    bundle_required_capabilities: dict[str, tuple[str, ...]],
) -> dict[str, Any]:
    if not isinstance(route, dict):
        raise EvaluatorError("route must be an object")
    intents = _route_intents(route)
    actual_intents = [intent["task_type"] for intent in intents]
    expected_intents = case["expected_intents"]
    selected = route.get("selected_scenarios")
    if not isinstance(selected, list):
        raise EvaluatorError("selected_scenarios must be a list")
    actual_scenarios = []
    for selection in selected:
        if not isinstance(selection, dict):
            raise EvaluatorError("selected scenario must be an object")
        scenario_id = selection.get("scenario_id")
        if not isinstance(scenario_id, str) or not scenario_id:
            raise EvaluatorError("selected scenario id must be nonempty")
        actual_scenarios.append(scenario_id)
    actual_scenario_set = set(actual_scenarios)
    expected_scenario_set = set(case["expected_scenarios"])
    forbidden_set = set(case["forbidden_scenarios"])
    actual_skill_names = _selected_skill_names(route)
    forbidden_skill_set = set(case.get("forbidden_skills", []))
    expected_capabilities = {
        (scenario_id, capability)
        for scenario_id in case["expected_scenarios"]
        for capability in bundle_required_capabilities.get(scenario_id, ())
    }
    covered_capabilities = _covered_capabilities(route)
    actual_edges = _dependency_pairs(route, intents)
    expected_edges = {tuple(edge) for edge in case["required_dependency_edges"]}
    topology_acyclic = _graph_topology_is_acyclic(route)
    dag_is_valid, dag_issues = _dag_assessment(
        route,
        topology_acyclic,
    )
    if case.get("expected_status") != "blocked" and not dag_is_valid:
        raise EvaluatorError(f"unexpected invalid DAG for case {case['id']}")

    issues = list(dag_issues)
    if actual_intents != expected_intents:
        issues.append({"id": "intent_order_mismatch", "expected": expected_intents, "actual": actual_intents})
    missing_scenarios = sorted(expected_scenario_set - actual_scenario_set)
    unexpected_scenarios = sorted(actual_scenario_set - expected_scenario_set)
    if missing_scenarios:
        issues.append({"id": "missing_scenarios", "scenarios": missing_scenarios})
    if unexpected_scenarios:
        issues.append({"id": "unexpected_scenarios", "scenarios": unexpected_scenarios})
    forbidden_selected = sorted(actual_scenario_set & forbidden_set)
    if forbidden_selected:
        issues.append({"id": "forbidden_scenarios_selected", "scenarios": forbidden_selected})
    missing_edges = sorted(expected_edges - actual_edges)
    if missing_edges:
        issues.append({"id": "missing_dependency_edges", "edges": [list(edge) for edge in missing_edges]})
    expected_status = case.get("expected_status")
    actual_status = route.get("routing_status")
    if expected_status is not None and actual_status != expected_status:
        issues.append({"id": "status_mismatch", "expected": expected_status, "actual": actual_status})
    if not dag_is_valid:
        issues.append({"id": "expected_blocked_dag"})
    forbidden_skills_selected = sorted(actual_skill_names & forbidden_skill_set)
    if forbidden_skills_selected:
        issues.append({"id": "forbidden_skills_selected", "skills": forbidden_skills_selected})

    high_confidence_case = any(intent["confidence"] >= 0.80 for intent in intents)
    high_confidence_error = high_confidence_case and set(actual_intents) != set(expected_intents)

    return {
        "id": case["id"],
        "category": case["category"],
        "actual_intents": actual_intents,
        "actual_scenarios": sorted(actual_scenario_set),
        "actual_dependency_edges": [list(edge) for edge in sorted(actual_edges)],
        "routing_status": actual_status,
        "dag_valid": dag_is_valid,
        "topology_acyclic": topology_acyclic,
        "issues": issues,
        "counts": {
            "intent_exact": int(actual_intents == expected_intents),
            "scenario_true_positive": len(actual_scenario_set & expected_scenario_set),
            "scenario_predicted": len(actual_scenario_set),
            "scenario_expected": len(expected_scenario_set),
            "forbidden_hits": len(actual_scenario_set & forbidden_set),
            "forbidden_total": len(forbidden_set),
            "dependency_hits": len(actual_edges & expected_edges),
            "dependency_predicted": len(actual_edges),
            "dependency_total": len(expected_edges),
            "required_capability_hits": len(expected_capabilities & covered_capabilities),
            "required_capability_total": len(expected_capabilities),
            "forbidden_skill_hits": len(actual_skill_names & forbidden_skill_set),
            "forbidden_skill_total": len(forbidden_skill_set),
            "high_confidence_error": int(high_confidence_error),
            "high_confidence_case": int(high_confidence_case),
            "dag_valid": int(dag_is_valid),
        },
    }


def _route_intents(route: dict[str, Any]) -> list[dict[str, Any]]:
    intent_graph = route.get("intent_graph")
    if not isinstance(intent_graph, dict) or not isinstance(intent_graph.get("intents"), list):
        raise EvaluatorError("intent_graph.intents must be a list")
    intents = intent_graph["intents"]
    for intent in intents:
        if not isinstance(intent, dict):
            raise EvaluatorError("intent must be an object")
        if not _is_exact_nonblank_string(intent.get("id")):
            raise EvaluatorError("intent id must be nonempty")
        if not _is_exact_nonblank_string(intent.get("task_type")):
            raise EvaluatorError("intent task_type must be nonempty")
        confidence = intent.get("confidence")
        if type(confidence) not in {int, float} or not math.isfinite(confidence) or not 0.0 <= confidence <= 1.0:
            raise EvaluatorError("intent confidence must be a finite number between zero and one")
    return intents


def _selected_skill_names(route: dict[str, Any]) -> set[str]:
    selected_skills = route.get("selected_skills")
    if not isinstance(selected_skills, list):
        raise EvaluatorError("selected_skills must be a list")
    names = []
    for selected_skill in selected_skills:
        if not isinstance(selected_skill, dict) or not _is_exact_nonblank_string(selected_skill.get("name")):
            raise EvaluatorError("selected skill name must be an exact nonempty string")
        names.append(selected_skill["name"])
    if len(names) != len(set(names)):
        raise EvaluatorError("selected skill names must be unique")
    return set(names)


def _covered_capabilities(route: dict[str, Any]) -> set[tuple[str, str]]:
    resolution = route.get("capability_resolution")
    if not isinstance(resolution, dict):
        raise EvaluatorError("capability_resolution must be an object")
    capabilities = resolution.get("capabilities")
    if not isinstance(capabilities, list):
        raise EvaluatorError("capability_resolution.capabilities must be a list")
    covered: set[tuple[str, str]] = set()
    observed: set[tuple[str, str]] = set()
    for item in capabilities:
        valid = (
            isinstance(item, dict)
            and _is_exact_nonblank_string(item.get("scenario_id"))
            and _is_exact_nonblank_string(item.get("capability"))
            and type(item.get("required")) is bool
            and item.get("status") in {"covered", "missing"}
            and isinstance(item.get("skills"), list)
            and all(_is_exact_nonblank_string(name) for name in item["skills"])
        )
        if not valid:
            raise EvaluatorError("capability resolution entry is malformed")
        key = (item["scenario_id"], item["capability"])
        if key in observed:
            raise EvaluatorError("capability resolution entries must be unique")
        observed.add(key)
        if item["status"] == "covered":
            covered.add(key)
    return covered


def _validate_bundle_required_capabilities(
    context: object,
) -> dict[str, tuple[str, ...]]:
    if context is _MISSING_SUPPORT:
        raise EvaluatorError("bundle required capability context must be provided explicitly")
    if not isinstance(context, Mapping):
        raise EvaluatorError("bundle required capability context must be a mapping")
    validated: dict[str, tuple[str, ...]] = {}
    for scenario_id, capabilities in context.items():
        if not _is_exact_nonblank_string(scenario_id):
            raise EvaluatorError("bundle capability scenario id must be an exact nonempty string")
        if type(capabilities) not in {list, tuple} or not all(
            _is_exact_nonblank_string(capability) for capability in capabilities
        ):
            raise EvaluatorError(
                "bundle required capabilities must be lists or tuples of exact nonempty strings"
            )
        if len(capabilities) != len(set(capabilities)):
            raise EvaluatorError("bundle required capabilities must be unique")
        validated[scenario_id] = tuple(capabilities)
    return dict(sorted(validated.items()))


def _validate_support_counts(counts: object, label: str) -> tuple[int, int]:
    if counts is _MISSING_SUPPORT:
        raise EvaluatorError(f"{label} counts must be provided explicitly")
    if type(counts) is not tuple or len(counts) != 2:
        raise EvaluatorError(f"{label} counts must be a two-item tuple")
    numerator, denominator = counts
    try:
        finite_ratio(numerator, denominator, empty=1.0)
    except ValueError as exc:
        raise EvaluatorError(f"{label} counts are invalid: {exc}") from exc
    return numerator, denominator


def _dependency_pairs(route: dict[str, Any], intents: list[dict[str, Any]]) -> set[tuple[str, str]]:
    graph = route.get("execution_graph")
    if not isinstance(graph, dict):
        raise EvaluatorError("execution_graph must be an object")
    nodes = graph.get("nodes")
    edges = graph.get("edges")
    if not isinstance(nodes, list) or not isinstance(edges, list):
        raise EvaluatorError("execution_graph nodes and edges must be lists")
    type_by_intent = {intent["id"]: intent["task_type"] for intent in intents}
    nodes_by_id: dict[str, dict[str, Any]] = {}
    node_types: dict[str, set[str]] = {}
    for node in nodes:
        if not isinstance(node, dict) or not _is_exact_nonblank_string(node.get("id")):
            raise EvaluatorError("execution graph node is malformed")
        intent_ids = node.get("intent_ids")
        valid_ids = (
            isinstance(intent_ids, list)
            and bool(intent_ids)
            and all(_is_exact_nonblank_string(item) for item in intent_ids)
            and len(intent_ids) == len(set(intent_ids))
            and not (set(intent_ids) - set(type_by_intent))
        )
        if not valid_ids:
            raise EvaluatorError("execution graph node intent_ids are invalid")
        nodes_by_id[node["id"]] = node
        node_types[node["id"]] = {type_by_intent[item] for item in intent_ids}
    pairs = set()
    for edge in edges:
        if not isinstance(edge, dict):
            raise EvaluatorError("execution graph edge is malformed")
        if edge.get("type") not in DEPENDENCY_EDGE_TYPES:
            continue
        source_id = edge.get("from")
        target_id = edge.get("to")
        if not _is_exact_nonblank_string(source_id) or not _is_exact_nonblank_string(target_id):
            raise EvaluatorError("dependency edge endpoints must be nonempty strings")
        if source_id not in nodes_by_id or target_id not in nodes_by_id:
            raise EvaluatorError("dependency edge references an unknown node")
        source_types = node_types[source_id]
        target_types = node_types[target_id]
        pairs.update((source, target) for source in source_types for target in target_types)
    return pairs


def _dag_assessment(
    route: dict[str, Any],
    topology_acyclic: bool,
) -> tuple[bool, list[dict[str, Any]]]:
    graph = route.get("execution_graph")
    if not isinstance(graph, dict):
        raise EvaluatorError("execution_graph must be an object")
    status = graph.get("status")
    declared_acyclic = graph.get("acyclic")
    routing_status = route.get("routing_status")
    reason_codes = graph.get("reason_codes")
    if not isinstance(declared_acyclic, bool) or not isinstance(status, str):
        raise EvaluatorError("execution graph status and acyclic fields are malformed")
    if not isinstance(reason_codes, list) or not all(type(reason) is str and reason for reason in reason_codes):
        raise EvaluatorError("execution graph reason_codes must be nonempty strings")
    issues = _source_intent_graph_issues(route)
    if routing_status in {"incomplete", "blocked"}:
        if status != "blocked":
            issues.append(
                {
                    "id": "blocked_status_incoherent",
                    "execution_graph_status": status,
                    "routing_status": routing_status,
                }
            )
        if len(reason_codes) != 1 or reason_codes[0] not in INCOMPLETE_GRAPH_REASONS:
            issues.append(
                {
                    "id": "invalid_incomplete_graph_reason",
                    "reason_codes": reason_codes,
                    "allowed_reasons": sorted(INCOMPLETE_GRAPH_REASONS),
                }
            )
        if not topology_acyclic:
            issues.append(
                {
                    "id": "blocked_graph_cycle",
                    "computed": topology_acyclic,
                }
            )
        if declared_acyclic:
            issues.append({"id": "acyclic_flag_mismatch", "declared": True, "expected": False})
        nodes = graph.get("nodes")
        edges = graph.get("edges")
        if nodes or edges:
            issues.append(
                {
                    "id": "blocked_graph_not_empty",
                    "node_count": len(nodes) if isinstance(nodes, list) else None,
                    "edge_count": len(edges) if isinstance(edges, list) else None,
                }
            )
        return not issues, issues
    if reason_codes:
        issues.append({"id": "unexpected_ready_graph_reason", "reason_codes": reason_codes})
    if routing_status == "complete" and status == "ready":
        nodes = graph.get("nodes")
        if not nodes:
            issues.append({"id": "empty_ready_graph"})
        else:
            source_intent_ids = {intent["id"] for intent in route["intent_graph"]["intents"]}
            covered_intent_ids = {intent_id for node in nodes for intent_id in node["intent_ids"]}
            missing_intent_ids = sorted(source_intent_ids - covered_intent_ids)
            if missing_intent_ids:
                issues.append(
                    {
                        "id": "missing_source_intent_coverage",
                        "intent_ids": missing_intent_ids,
                    }
                )
    if declared_acyclic != topology_acyclic:
        issues.append(
            {
                "id": "acyclic_flag_mismatch",
                "declared": declared_acyclic,
                "computed": topology_acyclic,
            }
        )
    valid = not issues and topology_acyclic and status == "ready" and routing_status == "complete"
    return valid, issues


def _source_intent_graph_issues(route: dict[str, Any]) -> list[dict[str, Any]]:
    intent_graph = route.get("intent_graph")
    if not isinstance(intent_graph, dict):
        raise EvaluatorError("intent_graph must be an object")
    intents = intent_graph.get("intents")
    if not isinstance(intents, list):
        raise EvaluatorError("intent_graph.intents must be a list")
    if not intents:
        return [{"id": "source_intent_graph_invalid", "reason": "empty_intent_graph"}]
    intent_ids: list[str] = []
    dependencies: dict[str, list[str]] = {}
    for intent in intents:
        if not isinstance(intent, dict):
            raise EvaluatorError("intent must be an object")
        intent_id = intent.get("id")
        depends_on = intent.get("depends_on")
        if not _is_exact_nonblank_string(intent_id):
            raise EvaluatorError("intent id must be nonempty")
        if not isinstance(depends_on, list) or not all(
            _is_exact_nonblank_string(dependency_id) for dependency_id in depends_on
        ):
            return [
                {
                    "id": "source_intent_graph_invalid",
                    "reason": "malformed_dependencies",
                    "intent_id": intent_id,
                }
            ]
        intent_ids.append(intent_id)
        dependencies[intent_id] = depends_on
    if len(intent_ids) != len(set(intent_ids)):
        return [{"id": "source_intent_graph_invalid", "reason": "duplicate_intent_ids"}]
    known_ids = set(intent_ids)
    for intent_id, dependency_ids in dependencies.items():
        unknown = set(dependency_ids) - known_ids
        if unknown:
            return [
                {
                    "id": "source_intent_graph_invalid",
                    "reason": "unknown_dependency",
                    "intent_id": intent_id,
                    "dependency_ids": sorted(unknown),
                }
            ]
    indegree = {intent_id: 0 for intent_id in intent_ids}
    outgoing: dict[str, list[str]] = defaultdict(list)
    for intent_id, dependency_ids in dependencies.items():
        for dependency_id in set(dependency_ids):
            outgoing[dependency_id].append(intent_id)
            indegree[intent_id] += 1
    ready = deque(sorted(intent_id for intent_id, degree in indegree.items() if degree == 0))
    visited = 0
    while ready:
        intent_id = ready.popleft()
        visited += 1
        for dependent_id in sorted(outgoing[intent_id]):
            indegree[dependent_id] -= 1
            if indegree[dependent_id] == 0:
                ready.append(dependent_id)
    if visited != len(intent_ids):
        return [{"id": "source_intent_graph_cycle"}]
    return []


def _graph_topology_is_acyclic(route: dict[str, Any]) -> bool:
    graph = route.get("execution_graph")
    if not isinstance(graph, dict):
        raise EvaluatorError("execution_graph must be an object")
    nodes = graph.get("nodes")
    edges = graph.get("edges")
    if not isinstance(nodes, list) or not isinstance(edges, list):
        raise EvaluatorError("execution_graph nodes and edges must be lists")
    node_ids = []
    for node in nodes:
        if not isinstance(node, dict) or not isinstance(node.get("id"), str):
            raise EvaluatorError("execution graph node is malformed")
        node_ids.append(node["id"])
    if len(node_ids) != len(set(node_ids)):
        raise EvaluatorError("execution graph node ids must be unique")
    indegree = {node_id: 0 for node_id in node_ids}
    outgoing: dict[str, list[str]] = defaultdict(list)
    for edge in edges:
        if not isinstance(edge, dict):
            raise EvaluatorError("execution graph edge is malformed")
        source = edge.get("from")
        target = edge.get("to")
        if source not in indegree or target not in indegree:
            raise EvaluatorError("execution graph edge references an unknown node")
        outgoing[source].append(target)
        indegree[target] += 1
    ready = deque(sorted(node_id for node_id, degree in indegree.items() if degree == 0))
    visited = 0
    while ready:
        node_id = ready.popleft()
        visited += 1
        for target in sorted(outgoing[node_id]):
            indegree[target] -= 1
            if indegree[target] == 0:
                ready.append(target)
    return visited == len(node_ids)


def _ratio(numerator: int, denominator: int, *, empty: float) -> float:
    return empty if denominator == 0 else numerator / denominator


def _quality_ratio(matches: int, denominator: int, opposite_total: int) -> float:
    if denominator:
        return matches / denominator
    return 1.0 if opposite_total == 0 else 0.0
