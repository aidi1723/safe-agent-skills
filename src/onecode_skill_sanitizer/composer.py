"""Compose trusted scenario candidates across ordered intents."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from .candidates import ScenarioCandidate
from .intent import IntentGraph


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
) -> ScenarioComposition:
    by_intent: dict[str, list[tuple[int, ScenarioCandidate]]] = {}
    for index, candidate in enumerate(candidates):
        by_intent.setdefault(candidate.intent_id, []).append((index, candidate))

    selected_by_intent: list[ScenarioCandidate] = []
    uncovered_intents: list[str] = []
    for intent in intent_graph.intents:
        available = by_intent.get(intent.id, [])
        if not available:
            uncovered_intents.append(intent.id)
            continue
        _, selected = min(
            available,
            key=lambda item: (-item[1].deterministic_score, item[0]),
        )
        selected_by_intent.append(selected)

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
