"""Independent evaluation for hybrid router v2 multi-intent routes."""

from __future__ import annotations

import json
import math
from collections import Counter
from collections import defaultdict, deque
from collections.abc import Callable
from pathlib import Path
from typing import Any


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
OPTIONAL_FIELDS = {"expected_status"}
EXPECTED_LABELING = {
    "method": "manual_review",
    "reviewer_role": "independent_dataset_review",
    "generated_from_router": False,
    "reviewed_at": "2026-07-10",
}


class DatasetValidationError(ValueError):
    pass


class EvaluatorError(RuntimeError):
    pass


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
    if not isinstance(payload, dict) or set(payload) != {"labeling", "cases"}:
        raise DatasetValidationError(
            "evaluation dataset must be an object containing only labeling and cases"
        )
    if payload["labeling"] != EXPECTED_LABELING:
        raise DatasetValidationError("evaluation dataset labeling metadata is invalid")
    cases = payload["cases"]
    if not isinstance(cases, list):
        raise DatasetValidationError("cases must be a list")
    validated = [
        _validate_case(case, index, allowed_scenarios)
        for index, case in enumerate(cases)
    ]
    if len(validated) != EXPECTED_CASE_COUNT:
        raise DatasetValidationError(
            f"expected exactly {EXPECTED_CASE_COUNT} cases, found {len(validated)}"
        )
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
    if len(set(case["expected_scenarios"])) != len(case["expected_scenarios"]):
        raise DatasetValidationError(f"{prefix}.expected_scenarios must not contain duplicates")
    if len(set(case["forbidden_scenarios"])) != len(case["forbidden_scenarios"]):
        raise DatasetValidationError(f"{prefix}.forbidden_scenarios must not contain duplicates")
    if known_scenarios is not None:
        unknown = sorted(set(case["expected_scenarios"]) - known_scenarios)
        if unknown:
            raise DatasetValidationError(
                f"{prefix}.expected_scenarios contains unknown ids: {', '.join(unknown)}"
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
            raise DatasetValidationError(
                f"{edge_prefix} endpoints must exist in expected_intents"
            )
        normalized_edges.append([edge[0], edge[1]])
    if len({tuple(edge) for edge in normalized_edges}) != len(normalized_edges):
        raise DatasetValidationError(f"{prefix}.required_dependency_edges has duplicates")
    expected_status = case.get("expected_status")
    if expected_status is not None and (
        not isinstance(expected_status, str) or expected_status not in EXPECTED_STATUSES
    ):
        raise DatasetValidationError(f"{prefix}.expected_status is invalid")
    return dict(case)


def _require_nonempty_string(value: object, field: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise DatasetValidationError(f"{field} must be a nonempty string")


def _require_string_list(value: object, field: str, *, nonempty: bool = False) -> None:
    if not isinstance(value, list) or not all(
        isinstance(item, str) and bool(item.strip()) for item in value
    ):
        raise DatasetValidationError(f"{field} must be a list of nonempty strings")
    if nonempty and not value:
        raise DatasetValidationError(f"{field} must not be empty")


def evaluate_router_v2(
    cases: list[dict[str, Any]],
    *,
    route_builder: Callable[[dict[str, Any]], dict[str, Any]],
    known_scenarios: set[str] | None = None,
) -> dict[str, Any]:
    intent_exact = 0
    scenario_true_positive = 0
    scenario_predicted = 0
    scenario_expected = 0
    forbidden_hits = 0
    forbidden_total = 0
    dependency_hits = 0
    dependency_total = 0
    dag_valid = 0
    results = []

    for case in cases:
        try:
            route = route_builder(case)
            result = _evaluate_case(case, route)
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
        dag_valid += counts["dag_valid"]
        results.append(result)

    case_count = len(cases)
    precision = _quality_ratio(scenario_true_positive, scenario_predicted, scenario_expected)
    recall = _quality_ratio(scenario_true_positive, scenario_expected, scenario_predicted)
    f1 = 0.0 if precision + recall == 0 else 2 * precision * recall / (precision + recall)
    metrics = {
        "multi_intent_exact_match": _ratio(intent_exact, case_count, empty=1.0),
        "scenario_precision": precision,
        "scenario_recall": recall,
        "scenario_f1": f1,
        "forbidden_scenario_false_positive_rate": _ratio(
            forbidden_hits, forbidden_total, empty=0.0
        ),
        "dependency_edge_recall": _ratio(dependency_hits, dependency_total, empty=1.0),
        "dag_validity": _ratio(dag_valid, case_count, empty=1.0),
    }
    if not all(math.isfinite(value) for value in metrics.values()):
        raise EvaluatorError("metrics must be finite")
    expected_scenario_coverage = sorted(
        {scenario for case in cases for scenario in case["expected_scenarios"]}
    )
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
            "dependency_total": dependency_total,
            "dag_valid_cases": dag_valid,
        },
        "scenario_coverage": {
            "expected_scenarios": expected_scenario_coverage,
            "uncovered_scenarios": sorted(
                (known_scenarios or set()) - set(expected_scenario_coverage)
            ),
        },
        "dag_definition": (
            "Valid means an acyclic ready execution graph for complete routes, or a blocked "
            "execution graph when expected_status explicitly declares blocked."
        ),
        "cases": results,
    }


def _evaluate_case(case: dict[str, Any], route: object) -> dict[str, Any]:
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
    actual_edges = _dependency_pairs(route, intents)
    expected_edges = {tuple(edge) for edge in case["required_dependency_edges"]}
    dag_is_valid = _dag_is_valid(route, case.get("expected_status"))
    topology_acyclic = _graph_topology_is_acyclic(route)
    graph_status = route["execution_graph"].get("status")
    if case.get("expected_status") != "blocked" and (
        not topology_acyclic or graph_status == "blocked"
    ):
        raise EvaluatorError(f"unexpected invalid DAG for case {case['id']}")

    issues = []
    if actual_intents != expected_intents:
        issues.append(
            {"id": "intent_order_mismatch", "expected": expected_intents, "actual": actual_intents}
        )
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
        issues.append(
            {"id": "status_mismatch", "expected": expected_status, "actual": actual_status}
        )
    if not dag_is_valid:
        issues.append({"id": "expected_blocked_dag"})

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
            "dependency_total": len(expected_edges),
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
        if not isinstance(intent.get("id"), str) or not intent["id"]:
            raise EvaluatorError("intent id must be nonempty")
        if not isinstance(intent.get("task_type"), str) or not intent["task_type"]:
            raise EvaluatorError("intent task_type must be nonempty")
    return intents


def _dependency_pairs(route: dict[str, Any], intents: list[dict[str, Any]]) -> set[tuple[str, str]]:
    graph = route.get("execution_graph")
    if not isinstance(graph, dict):
        raise EvaluatorError("execution_graph must be an object")
    nodes = graph.get("nodes")
    edges = graph.get("edges")
    if not isinstance(nodes, list) or not isinstance(edges, list):
        raise EvaluatorError("execution_graph nodes and edges must be lists")
    type_by_intent = {intent["id"]: intent["task_type"] for intent in intents}
    node_types: dict[str, set[str]] = {}
    for node in nodes:
        if not isinstance(node, dict) or not isinstance(node.get("id"), str):
            raise EvaluatorError("execution graph node is malformed")
        intent_ids = node.get("intent_ids")
        if not isinstance(intent_ids, list) or not all(isinstance(item, str) for item in intent_ids):
            raise EvaluatorError("execution graph node intent_ids must be strings")
        node_types[node["id"]] = {type_by_intent[item] for item in intent_ids if item in type_by_intent}
    pairs = set()
    for edge in edges:
        if not isinstance(edge, dict):
            raise EvaluatorError("execution graph edge is malformed")
        if edge.get("type") not in DEPENDENCY_EDGE_TYPES:
            continue
        source_types = node_types.get(edge.get("from"), set())
        target_types = node_types.get(edge.get("to"), set())
        pairs.update((source, target) for source in source_types for target in target_types)
    return pairs


def _dag_is_valid(route: dict[str, Any], expected_status: str | None) -> bool:
    graph = route.get("execution_graph")
    if not isinstance(graph, dict):
        raise EvaluatorError("execution_graph must be an object")
    status = graph.get("status")
    acyclic = graph.get("acyclic")
    routing_status = route.get("routing_status")
    if not isinstance(acyclic, bool) or not isinstance(status, str):
        raise EvaluatorError("execution graph status and acyclic fields are malformed")
    if expected_status == "blocked":
        return status == "blocked"
    return acyclic and status == "ready" and routing_status in {"complete", "incomplete"}


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
