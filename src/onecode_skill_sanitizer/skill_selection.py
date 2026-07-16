from __future__ import annotations

from collections import defaultdict, deque
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any


SELECTION_THRESHOLD = 0.35
CLARIFY_MARGIN = 0.08


@dataclass(frozen=True)
class _ConflictEvent:
    kind: str
    winner: str
    rejected: str
    members: tuple[str, ...]
    margin: float


@dataclass
class _ConflictState:
    hard_losers: set[str] = field(default_factory=set)
    deferred: set[str] = field(default_factory=set)
    resolutions: list[dict[str, Any]] = field(default_factory=list)

    def unavailable(self, name: str) -> bool:
        return name in self.hard_losers or name in self.deferred

    def apply(self, event: _ConflictEvent) -> None:
        if event.kind == "deferred":
            self.deferred.update(event.members)
            winner = ""
            reason = "insufficient_margin"
        else:
            self.hard_losers.add(event.rejected)
            winner = event.winner
            reason = "higher_final_score"
        self.resolutions.append(
            {
                "winner": winner,
                "rejected": event.rejected,
                "reason": reason,
                "margin": event.margin,
            }
        )


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
    eligible = [
        item
        for item in candidates
        if not item.get("excluded")
        and float(item["final_score"]) >= SELECTION_THRESHOLD
    ]
    selected, contributions, conflicts = _stabilize_selection(
        eligible,
        profiles,
        set(required),
        set(need.get("explicit_skills", ())),
        set(need.get("mandatory_capabilities", ())),
    )

    selected_capabilities = {
        capability
        for name in selected
        for capability in _profile_values(profiles[name], "capabilities")
    }
    deferred_capabilities = {
        capability
        for name in conflicts.deferred
        for capability in _profile_values(profiles[name], "capabilities")
    }
    missing = sorted(set(required) - selected_capabilities - deferred_capabilities)
    missing_inputs = list(
        dict.fromkeys(
            (
                *need.get("missing_inputs", ()),
                *_unresolved_declared_contexts(selected, profiles),
            )
        )
    )
    mandatory_capabilities = set(need.get("mandatory_capabilities", ()))
    mandatory_skills = {
        name
        for name in selected
        if set(_profile_values(profiles[name], "capabilities"))
        & mandatory_capabilities
    }
    graph = _compile_graph(selected, profiles, explicit_order, mandatory_skills)
    status = _routing_status(
        graph,
        missing,
        missing_inputs,
        unresolved=bool(conflicts.deferred),
    )
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
        "conflicting_candidates_low_margin" if conflicts.deferred else "",
        graph,
        _confidence(candidates, status),
        missing_inputs=missing_inputs,
        failure_reason=failure_reason,
    )
    result["selection"]["marginal_contributions"] = contributions
    result["selection"]["conflict_resolutions"] = conflicts.resolutions
    return result


def _stabilize_selection(
    eligible: list[dict[str, Any]],
    profiles: Mapping[str, Mapping[str, Any]],
    required: set[str],
    explicit_skills: set[str],
    mandatory_capabilities: set[str],
) -> tuple[list[str], list[dict[str, Any]], _ConflictState]:
    state = _ConflictState()
    candidates_by_name = {item["skill"]: item for item in eligible}
    candidate_order = {
        item["skill"]: index for index, item in enumerate(eligible)
    }
    root_names = [
        item["skill"]
        for item in eligible
        if item["skill"] in explicit_skills
        or required & set(_profile_values(profiles[item["skill"]], "capabilities"))
    ]

    for _ in range(2 * len(eligible) + 2):
        event = _next_root_conflict(
            root_names,
            state,
            candidates_by_name,
            candidate_order,
            profiles,
        )
        if event is not None:
            state.apply(event)
            continue
        roots, contributions = _select_roots(
            eligible,
            state,
            profiles,
            required,
            explicit_skills,
            mandatory_capabilities,
        )
        selected, contributions, event = _expand_artifact_closure(
            roots,
            contributions,
            eligible,
            state,
            candidates_by_name,
            candidate_order,
            profiles,
        )
        if event is not None:
            state.apply(event)
            continue
        return selected, contributions, state
    raise RuntimeError("skill selection conflict fixed point did not converge")


def _next_root_conflict(
    root_names: Sequence[str],
    state: _ConflictState,
    candidates: Mapping[str, Mapping[str, Any]],
    candidate_order: Mapping[str, int],
    profiles: Mapping[str, Mapping[str, Any]],
) -> _ConflictEvent | None:
    active = [name for name in root_names if not state.unavailable(name)]
    ranked = sorted(
        active,
        key=lambda name: (-float(candidates[name]["final_score"]), candidate_order[name]),
    )
    survivors: list[str] = []
    for name in ranked:
        winner = next(
            (other for other in survivors if _conflicts(name, other, profiles)),
            "",
        )
        if not winner:
            survivors.append(name)
            continue
        margin = _score_margin(candidates[name], candidates[winner])
        if margin < CLARIFY_MARGIN:
            return _ConflictEvent(
                "deferred", "", name, (winner, name), margin
            )
        return _ConflictEvent("hard", winner, name, (name,), margin)
    return None


def _select_roots(
    eligible: Sequence[dict[str, Any]],
    state: _ConflictState,
    profiles: Mapping[str, Mapping[str, Any]],
    required: set[str],
    explicit_skills: set[str],
    mandatory_capabilities: set[str],
) -> tuple[list[str], list[dict[str, Any]]]:
    uncovered = set(required)
    selected: list[str] = []
    contributions: list[dict[str, Any]] = []
    for item in eligible:
        name = item["skill"]
        if state.unavailable(name):
            continue
        marginal = sorted(
            uncovered & set(_profile_values(profiles[name], "capabilities"))
        )
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
    return selected, contributions


def _expand_artifact_closure(
    roots: list[str],
    root_contributions: list[dict[str, Any]],
    eligible: Sequence[dict[str, Any]],
    state: _ConflictState,
    candidates: Mapping[str, Mapping[str, Any]],
    candidate_order: Mapping[str, int],
    profiles: Mapping[str, Mapping[str, Any]],
) -> tuple[list[str], list[dict[str, Any]], _ConflictEvent | None]:
    selected = list(roots)
    contributions = list(root_contributions)
    produced_by: dict[str, list[str]] = defaultdict(list)
    for item in eligible:
        name = item["skill"]
        if state.unavailable(name):
            continue
        for artifact in _produced_values(profiles[name]):
            if name not in produced_by[artifact]:
                produced_by[artifact].append(name)

    ready = deque(selected)
    while ready:
        target = ready.popleft()
        for artifact in _profile_values(profiles[target], "requires_context"):
            if _has_selected_producer(target, artifact, selected, profiles):
                continue
            producers = [
                name
                for name in produced_by.get(artifact, ())
                if name != target
            ]
            if len(producers) != 1:
                continue
            producer = producers[0]
            event = _producer_conflict(
                producer,
                selected,
                candidates,
                candidate_order,
                profiles,
            )
            if event is not None:
                return selected, contributions, event
            selected.append(producer)
            ready.append(producer)
            contributions.append(
                {
                    "skill": producer,
                    "capabilities": [],
                    "reason": f"required_artifact:{artifact}",
                }
            )
    return selected, contributions, None


def _producer_conflict(
    producer: str,
    selected: Sequence[str],
    candidates: Mapping[str, Mapping[str, Any]],
    candidate_order: Mapping[str, int],
    profiles: Mapping[str, Mapping[str, Any]],
) -> _ConflictEvent | None:
    conflicting = [
        name for name in selected if _conflicts(producer, name, profiles)
    ]
    if not conflicting:
        return None
    ranked = sorted(
        [producer, *conflicting],
        key=lambda name: (-float(candidates[name]["final_score"]), candidate_order[name]),
    )
    winner = ranked[0]
    rejected = producer if winner != producer else ranked[1]
    margin = _score_margin(candidates[winner], candidates[rejected])
    if margin < CLARIFY_MARGIN:
        return _ConflictEvent(
            "deferred", "", rejected, (winner, rejected), margin
        )
    return _ConflictEvent("hard", winner, rejected, (rejected,), margin)


def _has_selected_producer(
    target: str,
    artifact: str,
    selected: Sequence[str],
    profiles: Mapping[str, Mapping[str, Any]],
) -> bool:
    return any(
        source != target and artifact in _produced_values(profiles[source])
        for source in selected
    )


def _unresolved_declared_contexts(
    selected: Sequence[str],
    profiles: Mapping[str, Mapping[str, Any]],
) -> list[str]:
    produced_by: dict[Any, set[str]] = defaultdict(set)
    for source, profile in profiles.items():
        for artifact in _produced_values(profile):
            produced_by[artifact].add(source)

    missing: list[str] = []
    for target in selected:
        for artifact in _profile_values(profiles[target], "requires_context"):
            if _has_selected_producer(target, artifact, selected, profiles):
                continue
            if (
                any(source != target for source in produced_by[artifact])
                and artifact not in missing
            ):
                missing.append(artifact)
    return missing


def _routing_status(
    graph: Mapping[str, Any],
    missing: Sequence[str],
    missing_inputs: Sequence[str],
    *,
    unresolved: bool,
) -> str:
    if graph["status"] == "blocked":
        return "blocked"
    if missing or missing_inputs:
        return "incomplete"
    if unresolved:
        return "clarify"
    return "complete"


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

    if not _is_acyclic([node["id"] for node in nodes], edges):
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


def _is_acyclic(node_ids: Sequence[str], edges: Sequence[Mapping[str, str]]) -> bool:
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


def _score_margin(left: Mapping[str, Any], right: Mapping[str, Any]) -> float:
    return round(
        abs(float(left["final_score"]) - float(right["final_score"])),
        6,
    )


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


def _has_edge(edges: Sequence[Mapping[str, str]], source: str, target: str) -> bool:
    return any(
        edge["from"] == source and edge["to"] == target for edge in edges
    )
