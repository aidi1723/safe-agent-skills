"""Deterministic trusted scenario retrieval for decomposed intents."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from .intent import IntentGraph
from .router import build_profile_for_task_type, score_bundle_for_profile


DEFAULT_TOP_N = 3
MAX_TOP_N = 10


@dataclass(frozen=True)
class ScenarioCandidate:
    intent_id: str
    scenario_id: str
    score: float
    deterministic_score: int

    def to_json(self) -> dict[str, Any]:
        return asdict(self)


def retrieve_scenario_candidates(
    intent_graph: IntentGraph,
    bundles_index: dict,
    top_n: int = DEFAULT_TOP_N,
) -> tuple[ScenarioCandidate, ...]:
    limit = min(MAX_TOP_N, max(0, int(top_n)))
    if limit == 0:
        return ()

    trusted_bundles = [
        bundle
        for bundle in bundles_index.get("bundles", [])
        if bundle.get("status") == "trusted"
    ]
    candidates: list[ScenarioCandidate] = []
    for intent in intent_graph.intents:
        if intent.task_type == "general":
            continue
        profile = build_profile_for_task_type(intent.summary, intent.task_type)
        scored = [
            (score_bundle_for_profile(bundle, profile), index, bundle)
            for index, bundle in enumerate(trusted_bundles)
        ]
        positive = [item for item in scored if item[0] > 0]
        positive.sort(key=lambda item: (-item[0], item[1]))
        selected = positive[:limit]
        maximum = selected[0][0] if selected else 0
        for deterministic_score, _, bundle in selected:
            candidates.append(
                ScenarioCandidate(
                    intent_id=intent.id,
                    scenario_id=bundle["id"],
                    score=deterministic_score / maximum,
                    deterministic_score=deterministic_score,
                )
            )
    return tuple(candidates)
