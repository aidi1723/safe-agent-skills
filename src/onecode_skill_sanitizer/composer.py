"""Compose trusted scenario candidates across ordered intents."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from .candidates import ScenarioCandidate, trusted_scenario_map
from .intent import IntentGraph
from .router import build_profile_for_task_type, score_bundle_for_profile


@dataclass(frozen=True)
class ScenarioSelection:
    scenario_id: str
    intent_ids: tuple[str, ...]
    score: float
    deterministic_score: int

    def to_json(self) -> dict[str, Any]:
        return _json_compatible(asdict(self))


@dataclass(frozen=True)
class ScenarioComposition:
    selections: tuple[ScenarioSelection, ...]
    uncovered_intents: tuple[str, ...]
    status: str

    def to_json(self) -> dict[str, Any]:
        return _json_compatible(asdict(self))


def compose_scenarios(
    intent_graph: IntentGraph,
    candidates: tuple[ScenarioCandidate, ...] | list[ScenarioCandidate],
    bundles_index: dict,
    trusted_skill_names: set[str],
) -> ScenarioComposition:
    valid_scenarios = trusted_scenario_map(bundles_index, trusted_skill_names)
    selected_by_intent: list[ScenarioCandidate] = []
    uncovered_intents: list[str] = []
    for intent in intent_graph.intents:
        profile = build_profile_for_task_type(intent.summary, intent.task_type)
        authoritative = [
            (
                score_bundle_for_profile(valid_scenarios[candidate.scenario_id], profile),
                candidate.scenario_id,
            )
            for candidate in candidates
            if candidate.intent_id == intent.id
            and candidate.scenario_id in valid_scenarios
        ]
        available = [item for item in authoritative if item[0] > 0]
        if not available:
            uncovered_intents.append(intent.id)
            continue
        deterministic_score, scenario_id = min(
            available, key=lambda item: (-item[0], item[1])
        )
        maximum_score = max(item[0] for item in available)
        selected_by_intent.append(
            ScenarioCandidate(
                intent_id=intent.id,
                scenario_id=scenario_id,
                score=deterministic_score / maximum_score,
                deterministic_score=deterministic_score,
            )
        )

    merged: dict[str, dict[str, Any]] = {}
    for selected in selected_by_intent:
        aggregate = merged.setdefault(
            selected.scenario_id,
            {
                "intent_ids": [],
                "score": selected.score,
                "deterministic_score": 0,
            },
        )
        aggregate["intent_ids"].append(selected.intent_id)
        aggregate["score"] = max(aggregate["score"], selected.score)
        aggregate["deterministic_score"] += selected.deterministic_score

    selections = tuple(
        ScenarioSelection(
            scenario_id=scenario_id,
            intent_ids=tuple(aggregate["intent_ids"]),
            score=aggregate["score"],
            deterministic_score=aggregate["deterministic_score"],
        )
        for scenario_id, aggregate in merged.items()
    )
    uncovered = tuple(uncovered_intents)
    return ScenarioComposition(
        selections=selections,
        uncovered_intents=uncovered,
        status="complete" if not uncovered else "incomplete",
    )


def _json_compatible(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _json_compatible(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_compatible(item) for item in value]
    return value
