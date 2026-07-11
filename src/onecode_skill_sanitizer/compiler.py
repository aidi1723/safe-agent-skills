"""Compile trusted scenario selections into a deterministic global DAG."""

from __future__ import annotations

from collections import defaultdict, deque
import re
from typing import Any

from .candidates import referenced_skill_names, validate_bundles_index
from .composer import ScenarioComposition
from .intent import IntentGraph
from .router import pipeline_stage_for_skill
from .routing_profiles import SCENARIO_PROFILES


_INTENT_ID_RE = re.compile(r"^i[1-9][0-9]*$")
_KNOWN_TASK_TYPES = frozenset(profile["task_type"] for profile in SCENARIO_PROFILES)
_EXPLICIT_VERIFICATION_GATE_RE = re.compile(
    r"\b(?:after\s+verif(?:ication|ying)|once\s+verified)\b|"
    r"(?:验证通过|测试通过)后",
    re.IGNORECASE,
)


def compile_execution_graph(
    intent_graph: IntentGraph,
    composition: ScenarioComposition,
    bundles_index: dict,
    trusted_skill_names: set[str],
) -> dict[str, Any]:
    reason_codes: list[str] = []
    details: list[str] = []
    _validate_intent_graph_boundary(intent_graph, reason_codes, details)
    intents = _validated_intents(intent_graph, reason_codes, details)
    if "invalid_intent_graph" in reason_codes:
        if intents and not _intent_dependencies_are_acyclic(intents):
            _add_reason(reason_codes, "dependency_cycle")
        return _result(False, [], [], reason_codes, details)
    selections = _validated_selections(composition, intents, reason_codes)
    bundles = _validated_bundles(bundles_index, reason_codes)
    trusted_names = (
        trusted_skill_names
        if isinstance(trusted_skill_names, set)
        and all(isinstance(name, str) for name in trusted_skill_names)
        else set()
    )

    scenario_orders: dict[str, tuple[str, ...]] = {}
    for selection in selections:
        scenario_id = selection.scenario_id
        bundle = bundles.get(scenario_id)
        if bundle is None:
            _add_reason(reason_codes, "missing_scenario_bundle")
            continue
        execution_order = bundle.get("execution_order")
        if not isinstance(execution_order, list):
            _add_reason(reason_codes, "malformed_execution_order")
            continue
        if not execution_order:
            _add_reason(reason_codes, "empty_execution_order")
            continue
        if len(execution_order) != len(set(execution_order)):
            _add_reason(reason_codes, "duplicate_skill_name")
            continue
        if (
            bundle.get("status") != "trusted"
            or not referenced_skill_names(bundle).issubset(trusted_names)
        ):
            _add_reason(reason_codes, "untrusted_scenario")
            continue
        scenario_orders[scenario_id] = tuple(execution_order)

    if _has_fatal_precompile_reason(reason_codes):
        return _result(False, [], [], reason_codes, details)

    selected_for_intent: dict[str, str] = {}
    for selection in selections:
        for intent_id in selection.intent_ids:
            if intent_id in selected_for_intent:
                _add_reason(reason_codes, "duplicate_intent_selection")
            else:
                selected_for_intent[intent_id] = selection.scenario_id

    expected_intents = set(intents)
    if set(selected_for_intent) != expected_intents:
        _add_reason(reason_codes, "incomplete_composition")
    if _has_fatal_precompile_reason(reason_codes):
        return _result(False, [], [], reason_codes, details)

    nodes: list[dict[str, Any]] = []
    edges: list[dict[str, str]] = []
    roots: dict[str, str] = {}
    verification_anchors: dict[str, tuple[str, ...]] = {}
    completion_anchors: dict[str, tuple[str, ...]] = {}
    for intent_id in sorted(intents, key=_intent_sort_key):
        scenario_id = selected_for_intent[intent_id]
        node_ids: list[str] = []
        for skill_name in scenario_orders[scenario_id]:
            node_id = f"skill:{intent_id}:{skill_name}"
            node_ids.append(node_id)
            nodes.append(
                {
                    "id": node_id,
                    "intent_ids": [intent_id],
                    "scenario_ids": [scenario_id],
                    "skill": skill_name,
                    "stage": pipeline_stage_for_skill(skill_name),
                    "host_action": skill_name.startswith("execution-"),
                }
            )
        roots[intent_id] = node_ids[0]
        verification_anchors[intent_id] = _terminal_verification_nodes(
            node_ids, nodes
        )
        completion_anchors[intent_id] = (node_ids[-1],)
        edges.extend(
            {"from": source, "to": target, "type": "scenario_order"}
            for source, target in zip(node_ids, node_ids[1:])
        )

    for intent_id in sorted(intents, key=_intent_sort_key):
        dependencies = intents[intent_id].depends_on
        for dependency_id in sorted(set(dependencies), key=_intent_sort_key):
            anchors = verification_anchors[dependency_id]
            if not anchors and _requires_verified_dependency(intents[intent_id]):
                _add_reason(reason_codes, "missing_intent_verification")
                continue
            if anchors:
                edges.extend(
                    {
                        "from": anchor_id,
                        "to": roots[intent_id],
                        "type": "intent_verification_dependency",
                    }
                    for anchor_id in anchors
                )
            edges.extend(
                {
                    "from": anchor_id,
                    "to": roots[intent_id],
                    "type": "intent_completion_dependency",
                }
                for anchor_id in completion_anchors[dependency_id]
            )

    scenario_ranks = {
        scenario_id: {
            skill_name: rank for rank, skill_name in enumerate(execution_order)
        }
        for scenario_id, execution_order in scenario_orders.items()
    }
    nodes.sort(key=lambda node: _node_sort_key(node, scenario_ranks))
    edges = _deduplicate_and_sort_edges(edges)
    acyclic = _is_acyclic(nodes, edges)
    if not acyclic:
        _add_reason(reason_codes, "dependency_cycle")
    return _result(acyclic, nodes, edges, reason_codes, details)


def _requires_verified_dependency(intent: Any) -> bool:
    return (
        intent.task_type not in _KNOWN_TASK_TYPES
        or intent.task_type == "open_source_release"
        or bool(_EXPLICIT_VERIFICATION_GATE_RE.search(intent.summary))
    )


def _validate_intent_graph_boundary(
    intent_graph: IntentGraph,
    reason_codes: list[str],
    details: list[str],
) -> None:
    try:
        validation_issues = intent_graph.validate()
    except (AttributeError, TypeError, ValueError):
        validation_issues = None
    if not isinstance(validation_issues, (list, tuple)) or not all(
        isinstance(issue, str) and issue.strip() for issue in validation_issues
    ):
        details.append("malformed intent graph validation result")
    else:
        details.extend(validation_issues)

    unresolved = getattr(intent_graph, "unresolved_dependencies", ())
    if not isinstance(unresolved, (tuple, list)) or not all(
        isinstance(dependency, str) and dependency.strip()
        for dependency in unresolved
    ):
        details.append(
            "unresolved_dependencies must be a list or tuple of nonempty strings"
        )
    else:
        details.extend(
            f"unresolved dependency: {dependency}"
            for dependency in unresolved
        )

    raw_intents = getattr(intent_graph, "intents", ())
    if isinstance(raw_intents, (tuple, list)):
        for intent in raw_intents:
            intent_id = getattr(intent, "id", None)
            if not isinstance(intent_id, str) or not _INTENT_ID_RE.fullmatch(intent_id):
                details.append(f"invalid intent id: {intent_id}")

    if details:
        _add_reason(reason_codes, "invalid_intent_graph")


def _validated_intents(
    intent_graph: IntentGraph,
    reason_codes: list[str],
    details: list[str],
) -> dict[str, Any]:
    raw_intents = getattr(intent_graph, "intents", ())
    if not isinstance(raw_intents, (tuple, list)) or not raw_intents:
        _add_reason(reason_codes, "malformed_intent_graph")
        return {}
    intents: dict[str, Any] = {}
    for intent in raw_intents:
        intent_id = getattr(intent, "id", None)
        if not isinstance(intent_id, str) or not intent_id:
            _add_reason(reason_codes, "invalid_intent_graph")
            details.append(f"invalid intent id: {intent_id}")
            continue
        if intent_id in intents:
            _add_reason(reason_codes, "duplicate_intent_id")
            continue
        dependencies = getattr(intent, "depends_on", None)
        if not isinstance(dependencies, (tuple, list)) or not all(
            isinstance(dependency, str) and dependency for dependency in dependencies
        ):
            _add_reason(reason_codes, "malformed_intent_dependency")
            continue
        intents[intent_id] = intent
    for intent in intents.values():
        if any(dependency not in intents for dependency in intent.depends_on):
            _add_reason(reason_codes, "unknown_intent_dependency")
    return intents


def _validated_selections(
    composition: ScenarioComposition,
    intents: dict[str, Any],
    reason_codes: list[str],
) -> tuple[Any, ...]:
    if getattr(composition, "status", None) != "complete" or getattr(
        composition, "uncovered_intents", ()
    ):
        _add_reason(reason_codes, "incomplete_composition")
    raw_selections = getattr(composition, "selections", ())
    if not isinstance(raw_selections, (tuple, list)):
        _add_reason(reason_codes, "malformed_composition")
        return ()
    validated = []
    for selection in raw_selections:
        scenario_id = getattr(selection, "scenario_id", None)
        intent_ids = getattr(selection, "intent_ids", None)
        if not isinstance(scenario_id, str) or not scenario_id:
            _add_reason(reason_codes, "malformed_scenario_id")
            continue
        if not isinstance(intent_ids, (tuple, list)) or not intent_ids:
            _add_reason(reason_codes, "malformed_selection_intents")
            continue
        if any(not isinstance(intent_id, str) or not intent_id for intent_id in intent_ids):
            _add_reason(reason_codes, "malformed_selection_intents")
            continue
        if any(intent_id not in intents for intent_id in intent_ids):
            _add_reason(reason_codes, "unknown_intent_id")
            continue
        validated.append(selection)
    return tuple(validated)


def _validated_bundles(bundles_index: dict, reason_codes: list[str]) -> dict[str, dict]:
    try:
        bundles = validate_bundles_index(bundles_index)
    except (TypeError, ValueError, KeyError):
        _add_reason(reason_codes, "malformed_bundles_index")
        return {}
    return {bundle["id"]: bundle for bundle in bundles}


def _is_acyclic(nodes: list[dict[str, Any]], edges: list[dict[str, str]]) -> bool:
    node_ids = [node["id"] for node in nodes]
    indegree = {node_id: 0 for node_id in node_ids}
    outgoing: dict[str, list[str]] = defaultdict(list)
    for edge in edges:
        outgoing[edge["from"]].append(edge["to"])
        indegree[edge["to"]] += 1
    ready = deque(sorted(node_id for node_id, degree in indegree.items() if degree == 0))
    visited = 0
    while ready:
        node_id = ready.popleft()
        visited += 1
        for target_id in sorted(outgoing[node_id]):
            indegree[target_id] -= 1
            if indegree[target_id] == 0:
                ready.append(target_id)
    return visited == len(node_ids)


def _intent_dependencies_are_acyclic(intents: dict[str, Any]) -> bool:
    indegree = {intent_id: 0 for intent_id in intents}
    outgoing: dict[str, list[str]] = defaultdict(list)
    for intent_id, intent in intents.items():
        for dependency_id in set(intent.depends_on):
            if dependency_id not in intents:
                return False
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
    return visited == len(intents)


def _terminal_verification_nodes(
    node_ids: list[str], nodes: list[dict[str, Any]]
) -> tuple[str, ...]:
    stage_by_id = {node["id"]: node["stage"] for node in nodes}
    rank_by_id = {node_id: rank for rank, node_id in enumerate(node_ids)}
    verification_ids = [
        node_id for node_id in node_ids if stage_by_id[node_id] == "verification"
    ]
    if not verification_ids:
        return ()
    last_position = max(rank_by_id[node_id] for node_id in verification_ids)
    return tuple(
        node_id for node_id in verification_ids if rank_by_id[node_id] == last_position
    )


def _deduplicate_and_sort_edges(edges: list[dict[str, str]]) -> list[dict[str, str]]:
    unique = {(edge["from"], edge["to"], edge["type"]) for edge in edges}
    return [
        {"from": source, "to": target, "type": edge_type}
        for source, target, edge_type in sorted(unique)
    ]


def _node_sort_key(
    node: dict[str, Any], scenario_ranks: dict[str, dict[str, int]]
) -> tuple[Any, ...]:
    scenario_id = node["scenario_ids"][0]
    return (
        _intent_sort_key(node["intent_ids"][0]),
        scenario_ranks[scenario_id][node["skill"]],
        node["id"],
    )


def _intent_sort_key(intent_id: str) -> tuple[int, int | str]:
    if intent_id.startswith("i") and intent_id[1:].isdigit():
        return (0, int(intent_id[1:]))
    return (1, intent_id)


def _result(
    acyclic: bool,
    nodes: list[dict[str, Any]],
    edges: list[dict[str, str]],
    reason_codes: list[str],
    details: list[str],
) -> dict[str, Any]:
    result = {
        "schema_version": 2,
        "status": "ready" if acyclic and not reason_codes else "blocked",
        "acyclic": acyclic and not reason_codes,
        "nodes": nodes,
        "edges": edges,
        "reason_codes": sorted(set(reason_codes)),
    }
    if details:
        result["details"] = sorted(set(details))
    return result


def _add_reason(reason_codes: list[str], reason_code: str) -> None:
    if reason_code not in reason_codes:
        reason_codes.append(reason_code)


def _has_fatal_precompile_reason(reason_codes: list[str]) -> bool:
    return any(reason_code != "invalid_intent_graph" for reason_code in reason_codes)
