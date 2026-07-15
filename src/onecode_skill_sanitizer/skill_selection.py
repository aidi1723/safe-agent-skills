from __future__ import annotations

from collections import defaultdict, deque
from collections.abc import Mapping, Sequence
from typing import Any


SELECTION_THRESHOLD = 0.35
CLARIFY_MARGIN = 0.08


def compose_skill_selection(
    need: dict[str, Any],
    candidates: list[dict[str, Any]],
    profiles: Mapping[str, Mapping[str, Any]],
    *,
    explicit_order: list[tuple[str, str]],
) -> dict[str, Any]:
    block_reasons = list(need.get("policy_block_reasons", ()))
    if block_reasons:
        required = list(need["required_capabilities"])
        graph = _empty_graph("blocked")
        graph["reason_codes"] = block_reasons
        graph["details"] = ["routing policy rejected the explicit request"]
        return _result(
            "blocked",
            [],
            candidates,
            required,
            required,
            "",
            graph,
            _confidence(candidates, "blocked"),
            failure_reason=block_reasons[0],
        )

    decision = need["decision"]
    if decision == "none":
        result = _result(
            "none",
            [],
            candidates,
            [],
            [],
            "",
            _empty_graph("ready"),
            _confidence(candidates, "none"),
        )
        result["selection"]["abstention_reason"] = need["reason_codes"][0]
        return result
    if decision == "clarify":
        return _result(
            "clarify",
            [],
            candidates,
            [],
            [],
            need["reason_codes"][0],
            _empty_graph("ready"),
            _confidence(candidates, "clarify"),
        )

    required = list(dict.fromkeys(need["required_capabilities"]))
    required_set = set(required)
    explicit_skills = set(need.get("explicit_skills", ()))
    mandatory_capabilities = set(need.get("mandatory_capabilities", ()))
    eligible = [
        item
        for item in candidates
        if not item.get("excluded")
        and float(item["final_score"]) >= SELECTION_THRESHOLD
    ]
    conflict_losers, conflict_resolutions, clarification = _resolve_conflicts(
        eligible,
        profiles,
        required_set,
        explicit_skills,
    )
    if clarification:
        missing = sorted(
            required_set
            - _available_required(
                eligible, profiles, required_set, conflict_losers
            )
        )
        return _clarification_result(
            candidates,
            required,
            missing,
            list(need.get("missing_inputs", ())),
            [*conflict_resolutions, clarification],
        )

    uncovered = set(required)
    selected: list[str] = []
    contributions: list[dict[str, Any]] = []
    selectable = [
        item for item in eligible if item["skill"] not in conflict_losers
    ]
    for item in selectable:
        name = item["skill"]
        profile = profiles[name]
        marginal = sorted(uncovered & set(_profile_values(profile, "capabilities")))
        explicitly_requested = name in explicit_skills
        if not marginal and not explicitly_requested:
            continue
        selected.append(name)
        uncovered.difference_update(marginal)
        reason = "marginal_capability_coverage"
        if set(marginal) & mandatory_capabilities:
            reason = "mandatory_verification"
        elif explicitly_requested and not marginal:
            reason = "explicit_user_request"
        contributions.append(
            {"skill": name, "capabilities": marginal, "reason": reason}
        )

    selected, dependency_clarification = _include_required_producers(
        selected,
        profiles,
        contributions,
        eligible,
        conflict_losers,
        conflict_resolutions,
    )
    missing = sorted(
        required_set
        - {
            capability
            for name in selected
            for capability in _profile_values(profiles[name], "capabilities")
        }
    )
    conflict_missing_contexts = _conflict_missing_contexts(
        selected,
        eligible,
        conflict_losers,
        profiles,
    )
    missing_inputs = _append_missing_inputs(
        list(need.get("missing_inputs", ())),
        conflict_missing_contexts,
    )
    if dependency_clarification:
        unresolved_missing = sorted(
            required_set
            - _available_required(
                eligible, profiles, required_set, conflict_losers
            )
        )
        return _clarification_result(
            candidates,
            required,
            unresolved_missing,
            missing_inputs,
            [*conflict_resolutions, dependency_clarification],
        )

    mandatory_skills = {
        name
        for name in selected
        if set(_profile_values(profiles[name], "capabilities"))
        & mandatory_capabilities
    }
    graph = _compile_graph(selected, profiles, explicit_order, mandatory_skills)
    if graph["status"] == "blocked":
        status = "blocked"
    elif missing or missing_inputs:
        status = "incomplete"
    else:
        status = "complete"
    failure_reason = (
        "dependency_cycle"
        if status == "blocked"
        else "missing_required_input"
        if missing_inputs
        else "missing_capability"
        if missing
        else ""
    )
    result = _result(
        status,
        selected,
        candidates,
        required,
        missing,
        "",
        graph,
        _confidence(candidates, status),
        missing_inputs=missing_inputs,
        failure_reason=failure_reason,
    )
    result["selection"]["marginal_contributions"] = contributions
    result["selection"]["conflict_resolutions"] = conflict_resolutions
    return result


def _resolve_conflicts(
    eligible: list[dict[str, Any]],
    profiles: Mapping[str, Mapping[str, Any]],
    required: set[str],
    explicit_skills: set[str],
) -> tuple[set[str], list[dict[str, Any]], dict[str, Any] | None]:
    indexed = list(enumerate(eligible))
    potential = [
        (index, item)
        for index, item in indexed
        if item["skill"] in explicit_skills
        or required & set(_profile_values(profiles[item["skill"]], "capabilities"))
    ]
    potential.sort(key=lambda pair: (-float(pair[1]["final_score"]), pair[0]))
    survivors: list[dict[str, Any]] = []
    losers: set[str] = set()
    resolutions: list[dict[str, Any]] = []
    for _, item in potential:
        name = item["skill"]
        conflicting = next(
            (
                survivor
                for survivor in survivors
                if _conflicts(name, survivor["skill"], profiles)
            ),
            None,
        )
        if conflicting is None:
            survivors.append(item)
            continue
        margin = round(
            abs(float(item["final_score"]) - float(conflicting["final_score"])),
            6,
        )
        if margin < CLARIFY_MARGIN:
            return (
                losers,
                resolutions,
                {
                    "winner": "",
                    "rejected": name,
                    "reason": "insufficient_margin",
                    "margin": margin,
                },
            )
        losers.add(name)
        resolutions.append(
            {
                "winner": conflicting["skill"],
                "rejected": name,
                "reason": "higher_deterministic_score",
                "margin": margin,
            }
        )
    return losers, resolutions, None


def _include_required_producers(
    selected: list[str],
    profiles: Mapping[str, Mapping[str, Any]],
    contributions: list[dict[str, Any]],
    admitted: Sequence[dict[str, Any]],
    rejected_conflicts: set[str],
    conflict_resolutions: list[dict[str, Any]],
) -> tuple[list[str], dict[str, Any] | None]:
    expanded = list(selected)
    admitted_names = [item["skill"] for item in admitted]
    candidates_by_name = {item["skill"]: item for item in admitted}
    candidate_order = {name: index for index, name in enumerate(admitted_names)}
    produced_by: dict[str, list[str]] = defaultdict(list)
    for name in admitted_names:
        profile = profiles[name]
        for artifact in _produced_values(profile):
            if name not in produced_by[artifact]:
                produced_by[artifact].append(name)

    ready = deque(expanded)
    deferred_conflicts: set[str] = set()
    clarification: dict[str, Any] | None = None
    while ready:
        target = ready.popleft()
        if target not in expanded:
            continue
        for artifact in _profile_values(profiles[target], "requires_context"):
            if any(
                producer != target and producer in expanded
                for producer in produced_by.get(artifact, ())
            ):
                continue
            producers = [
                producer
                for producer in produced_by.get(artifact, ())
                if producer != target
            ]
            if len(producers) != 1 or producers[0] in expanded:
                continue
            producer = producers[0]
            if producer in rejected_conflicts or producer in deferred_conflicts:
                continue
            conflicting = [
                name
                for name in expanded
                if _conflicts(producer, name, profiles)
            ]
            close_conflict = next(
                (
                    name
                    for name in conflicting
                    if _score_margin(
                        candidates_by_name[producer], candidates_by_name[name]
                    )
                    < CLARIFY_MARGIN
                ),
                "",
            )
            if close_conflict:
                deferred_conflicts.add(producer)
                if clarification is None:
                    clarification = {
                        "winner": "",
                        "rejected": producer,
                        "reason": "insufficient_margin",
                        "margin": _score_margin(
                            candidates_by_name[producer],
                            candidates_by_name[close_conflict],
                        ),
                    }
                continue
            if conflicting:
                winner = min(
                    [producer, *conflicting],
                    key=lambda name: (
                        -float(candidates_by_name[name]["final_score"]),
                        candidate_order[name],
                    ),
                )
                if winner != producer:
                    rejected_conflicts.add(producer)
                    conflict_resolutions.append(
                        _higher_score_resolution(
                            winner,
                            producer,
                            candidates_by_name,
                        )
                    )
                    continue
                for loser in conflicting:
                    expanded.remove(loser)
                    rejected_conflicts.add(loser)
                    conflict_resolutions.append(
                        _higher_score_resolution(
                            producer,
                            loser,
                            candidates_by_name,
                        )
                    )
                contributions[:] = [
                    item
                    for item in contributions
                    if item["skill"] not in rejected_conflicts
                ]
            expanded.append(producer)
            ready.append(producer)
            contributions.append(
                {
                    "skill": producer,
                    "capabilities": [],
                    "reason": f"required_artifact:{artifact}",
                }
            )
            if target not in expanded:
                break
    return expanded, clarification


def _available_required(
    candidates: Sequence[dict[str, Any]],
    profiles: Mapping[str, Mapping[str, Any]],
    required: set[str],
    rejected_conflicts: set[str],
) -> set[str]:
    return required & {
        capability
        for item in candidates
        if item["skill"] not in rejected_conflicts
        for capability in _profile_values(
            profiles[item["skill"]], "capabilities"
        )
    }


def _clarification_result(
    candidates: list[dict[str, Any]],
    required: list[str],
    missing: list[str],
    missing_inputs: list[str],
    conflict_resolutions: list[dict[str, Any]],
) -> dict[str, Any]:
    status = "incomplete" if missing or missing_inputs else "clarify"
    failure_reason = (
        "missing_required_input"
        if missing_inputs
        else "missing_capability"
        if missing
        else ""
    )
    result = _result(
        status,
        [],
        candidates,
        required,
        missing,
        "conflicting_candidates_low_margin",
        _empty_graph("ready"),
        _confidence(candidates, status),
        missing_inputs=missing_inputs,
        failure_reason=failure_reason,
    )
    result["selection"]["conflict_resolutions"] = conflict_resolutions
    return result


def _conflict_missing_contexts(
    selected: list[str],
    admitted: Sequence[dict[str, Any]],
    rejected_conflicts: set[str],
    profiles: Mapping[str, Mapping[str, Any]],
) -> list[str]:
    produced_by: dict[str, list[str]] = defaultdict(list)
    for item in admitted:
        name = item["skill"]
        for artifact in _produced_values(profiles[name]):
            if name not in produced_by[artifact]:
                produced_by[artifact].append(name)

    missing: list[str] = []
    for target in selected:
        for artifact in _profile_values(profiles[target], "requires_context"):
            if any(
                producer != target and producer in selected
                for producer in produced_by.get(artifact, ())
            ):
                continue
            producers = [
                producer
                for producer in produced_by.get(artifact, ())
                if producer != target
            ]
            if (
                len(producers) == 1
                and producers[0] in rejected_conflicts
                and artifact not in missing
            ):
                missing.append(artifact)
    return missing


def _append_missing_inputs(
    caller_inputs: list[str], additional_inputs: Sequence[str]
) -> list[str]:
    combined = list(caller_inputs)
    seen = set(caller_inputs)
    for item in additional_inputs:
        if item not in seen:
            combined.append(item)
            seen.add(item)
    return combined


def _score_margin(left: Mapping[str, Any], right: Mapping[str, Any]) -> float:
    return round(
        abs(float(left["final_score"]) - float(right["final_score"])),
        6,
    )


def _higher_score_resolution(
    winner: str,
    rejected: str,
    candidates: Mapping[str, Mapping[str, Any]],
) -> dict[str, Any]:
    return {
        "winner": winner,
        "rejected": rejected,
        "reason": "higher_deterministic_score",
        "margin": _score_margin(candidates[winner], candidates[rejected]),
    }


def _compile_graph(
    selected: list[str],
    profiles: Mapping[str, Mapping[str, Any]],
    explicit_order: list[tuple[str, str]],
    mandatory_skills: set[str],
) -> dict[str, Any]:
    nodes = [
        {"id": f"skill:{name}", "skill": name, "parallel": True}
        for name in selected
    ]
    edges: list[dict[str, str]] = []
    selected_set = set(selected)
    for target in selected:
        requirements = set(_profile_values(profiles[target], "requires_context"))
        for source in selected:
            if source == target:
                continue
            for artifact in sorted(requirements & set(_produced_values(profiles[source]))):
                edges.append(
                    {
                        "from": f"skill:{source}",
                        "to": f"skill:{target}",
                        "type": "artifact_dependency",
                        "evidence": artifact,
                    }
                )
        for source in _profile_values(profiles[target], "requires_after"):
            if source in selected_set:
                edges.append(
                    {
                        "from": f"skill:{source}",
                        "to": f"skill:{target}",
                        "type": "requires_after",
                        "evidence": source,
                    }
                )

    for source, target in explicit_order:
        source_id = f"skill:{source}"
        target_id = f"skill:{target}"
        if (
            source in selected_set
            and target in selected_set
            and not _has_edge(edges, source_id, target_id)
        ):
            edges.append(
                {
                    "from": source_id,
                    "to": target_id,
                    "type": "explicit_user_order",
                    "evidence": "current_request",
                }
            )

    for verifier in sorted(mandatory_skills):
        verifier_id = f"skill:{verifier}"
        for source in selected:
            source_id = f"skill:{source}"
            if source != verifier and not _has_edge(edges, source_id, verifier_id):
                edges.append(
                    {
                        "from": source_id,
                        "to": verifier_id,
                        "type": "mandatory_verification_precondition",
                        "evidence": "risk_derived_verification",
                    }
                )

    unique_edges = {
        (edge["from"], edge["to"], edge["type"], edge["evidence"]): edge
        for edge in edges
    }
    edges = sorted(
        unique_edges.values(),
        key=lambda edge: (
            edge["from"],
            edge["to"],
            edge["type"],
            edge["evidence"],
        ),
    )
    edge_nodes = {edge["from"] for edge in edges} | {
        edge["to"] for edge in edges
    }
    for node in nodes:
        node["parallel"] = node["id"] not in edge_nodes

    acyclic = _is_acyclic([node["id"] for node in nodes], edges)
    if not acyclic:
        return {
            "status": "blocked",
            "acyclic": False,
            "nodes": [],
            "edges": [],
            "reason_codes": ["dependency_cycle"],
            "details": ["selected skill dependency graph contains a cycle"],
        }
    return {
        "status": "ready",
        "acyclic": True,
        "nodes": nodes,
        "edges": edges,
        "reason_codes": [],
        "details": [],
    }


def _is_acyclic(node_ids: list[str], edges: list[dict[str, str]]) -> bool:
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
        for target in sorted(outgoing[node_id]):
            indegree[target] -= 1
            if indegree[target] == 0:
                ready.append(target)
    return visited == len(node_ids)


def _conflicts(
    left: str,
    right: str,
    profiles: Mapping[str, Mapping[str, Any]],
) -> bool:
    left_conflicts = set(_profile_values(profiles[left], "conflicts_with")) | set(
        _profile_values(profiles[left], "excludes")
    )
    right_conflicts = set(
        _profile_values(profiles[right], "conflicts_with")
    ) | set(_profile_values(profiles[right], "excludes"))
    return right in left_conflicts or left in right_conflicts


def _empty_graph(status: str) -> dict[str, Any]:
    return {
        "status": status,
        "acyclic": status != "blocked",
        "nodes": [],
        "edges": [],
        "reason_codes": [],
        "details": [],
    }


def _confidence(candidates: list[dict[str, Any]], status: str) -> dict[str, Any]:
    scores = sorted(
        (
            float(item["final_score"])
            for item in candidates
            if not item.get("excluded")
        ),
        reverse=True,
    )
    top = scores[0] if scores else 0.0
    runner_up = scores[1] if len(scores) > 1 else 0.0
    margin = max(0.0, top - runner_up)
    if status in {"blocked", "clarify", "incomplete", "none"}:
        level = "low"
    elif top >= 0.75 and (len(scores) == 1 or margin >= CLARIFY_MARGIN):
        level = "high"
    else:
        level = "medium"
    reason_codes = [f"routing_status:{status}"]
    if len(scores) > 1 and margin < CLARIFY_MARGIN:
        reason_codes.append("low_score_margin")
    return {
        "overall": round(top, 6),
        "level": level,
        "top_score": round(top, 6),
        "runner_up_score": round(runner_up, 6),
        "margin": round(margin, 6),
        "selection_threshold": SELECTION_THRESHOLD,
        "clarify_margin": CLARIFY_MARGIN,
        "reason_codes": reason_codes,
    }


def _result(
    status: str,
    selected: list[str],
    candidates: list[dict[str, Any]],
    required: list[str],
    missing: list[str],
    clarification_reason: str,
    graph: dict[str, Any],
    confidence: dict[str, Any],
    *,
    missing_inputs: list[str] | None = None,
    failure_reason: str = "",
) -> dict[str, Any]:
    missing_inputs = list(missing_inputs or ())
    missing_set = set(missing)
    covered = [capability for capability in required if capability not in missing_set]
    rejected = [
        item["skill"]
        for item in candidates
        if item["skill"] not in selected and not item.get("excluded")
    ]
    return {
        "routing_status": status,
        "selected_skill_names": list(selected),
        "missing_capabilities": list(missing),
        "rejected_adjacent_candidates": rejected,
        "selection": {
            "selected_skill_names": list(selected),
            "selected_skills": [],
            "marginal_contributions": [],
            "rejected_adjacent_candidates": rejected,
            "conflict_resolutions": [],
            "clarification_reason": clarification_reason,
            "abstention_reason": "",
            "failure_reason": failure_reason,
        },
        "capability_resolution": {
            "required_capabilities": list(required),
            "covered_capabilities": covered,
            "missing_capabilities": list(missing),
            "missing_inputs": missing_inputs,
            "covered_count": len(covered),
            "missing_count": len(missing),
            "status": (
                "incomplete" if missing or missing_inputs else "complete"
            ),
        },
        "execution_graph": graph,
        "confidence": confidence,
    }


def _profile_values(
    profile: Mapping[str, Any], key: str
) -> tuple[Any, ...]:
    return tuple(profile.get(key, ()))


def _produced_values(profile: Mapping[str, Any]) -> tuple[Any, ...]:
    return _profile_values(profile, "produces_artifacts") + _profile_values(
        profile, "produces_evidence"
    )


def _has_edge(edges: list[dict[str, str]], source: str, target: str) -> bool:
    return any(
        edge["from"] == source and edge["to"] == target for edge in edges
    )
