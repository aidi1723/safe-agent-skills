"""Deterministic trusted scenario retrieval for decomposed intents."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import math
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

    def __post_init__(self) -> None:
        if not math.isfinite(self.score):
            raise ValueError("score must be finite")
        if not 0 <= self.score <= 1:
            raise ValueError("score must be between 0 and 1")
        if isinstance(self.deterministic_score, bool) or not isinstance(
            self.deterministic_score, int
        ):
            raise ValueError("deterministic_score must be an integer")
        if self.deterministic_score < 0:
            raise ValueError("deterministic_score must be nonnegative")

    def to_json(self) -> dict[str, Any]:
        return asdict(self)


def retrieve_scenario_candidates(
    intent_graph: IntentGraph,
    bundles_index: dict,
    trusted_skill_names: set[str],
    top_n: int = DEFAULT_TOP_N,
) -> tuple[ScenarioCandidate, ...]:
    if isinstance(top_n, bool) or not isinstance(top_n, int) or not 0 <= top_n <= MAX_TOP_N:
        raise ValueError("top_n must be an integer between 0 and 10")

    bundles = validate_bundles_index(bundles_index)
    trusted_bundles = [
        bundle
        for bundle in bundles
        if bundle["status"] == "trusted"
        and referenced_skill_names(bundle).issubset(trusted_skill_names)
    ]
    if top_n == 0:
        return ()

    candidates: list[ScenarioCandidate] = []
    for intent in intent_graph.intents:
        if intent.task_type == "general":
            continue
        profile = build_profile_for_task_type(intent.summary, intent.task_type)
        scored = [
            (score_bundle_for_profile(bundle, profile), bundle)
            for bundle in trusted_bundles
        ]
        positive = [item for item in scored if item[0] > 0]
        positive.sort(key=lambda item: (-item[0], item[1]["id"]))
        selected = positive[:top_n]
        maximum = selected[0][0] if selected else 0
        for deterministic_score, bundle in selected:
            normalized_score = deterministic_score / maximum
            if not math.isfinite(normalized_score):
                raise ValueError("normalized candidate score must be finite")
            candidates.append(
                ScenarioCandidate(
                    intent_id=intent.id,
                    scenario_id=bundle["id"],
                    score=normalized_score,
                    deterministic_score=deterministic_score,
                )
            )
    return tuple(candidates)


def validate_bundles_index(bundles_index: dict) -> tuple[dict, ...]:
    if not isinstance(bundles_index, dict):
        raise ValueError("bundles index must be an object")
    bundles = bundles_index.get("bundles")
    if not isinstance(bundles, list):
        raise ValueError("bundles must be a list")

    validated: list[dict] = []
    seen_ids: set[str] = set()
    for bundle_index, bundle in enumerate(bundles):
        prefix = f"bundle[{bundle_index}]"
        if not isinstance(bundle, dict):
            raise ValueError(f"{prefix} must be an object")
        bundle_id = bundle.get("id")
        if not isinstance(bundle_id, str) or not bundle_id.strip():
            raise ValueError(f"{prefix}.id must be a nonempty string")
        if bundle_id in seen_ids:
            raise ValueError(f"duplicate bundle id: {bundle_id}")
        seen_ids.add(bundle_id)
        if not isinstance(bundle.get("status"), str):
            raise ValueError(f"{prefix}.status must be a string")
        _validate_string_list(bundle, "skills", prefix, nonempty=True)
        _validate_string_list(bundle, "execution_order", prefix, nonempty=True)
        _validate_string_list(bundle, "task_signals", prefix, nonempty=False)
        capabilities = bundle.get("required_capabilities")
        if not isinstance(capabilities, list):
            raise ValueError(f"{prefix}.required_capabilities must be a list")
        for capability_index, capability in enumerate(capabilities):
            capability_prefix = f"{prefix}.required_capabilities[{capability_index}]"
            if not isinstance(capability, dict):
                raise ValueError(f"{capability_prefix} must be an object")
            capability_id = capability.get("id")
            if not isinstance(capability_id, str) or not capability_id.strip():
                raise ValueError(f"{capability_prefix}.id must be a nonempty string")
            preferred_skills = capability.get("preferred_skills")
            if not isinstance(preferred_skills, list) or not all(
                isinstance(skill_name, str) for skill_name in preferred_skills
            ):
                raise ValueError(
                    f"{capability_prefix}.preferred_skills must be a list of strings"
                )
        validated.append(bundle)
    return tuple(validated)


def referenced_skill_names(bundle: dict) -> set[str]:
    names = set(bundle["skills"]) | set(bundle["execution_order"])
    for capability in bundle["required_capabilities"]:
        names.update(capability["preferred_skills"])
    return names


def trusted_scenario_map(
    bundles_index: dict,
    trusted_skill_names: set[str],
) -> dict[str, dict]:
    return {
        bundle["id"]: bundle
        for bundle in validate_bundles_index(bundles_index)
        if bundle["status"] == "trusted"
        and referenced_skill_names(bundle).issubset(trusted_skill_names)
    }


def _validate_string_list(
    bundle: dict,
    field: str,
    prefix: str,
    *,
    nonempty: bool,
) -> None:
    values = bundle.get(field)
    valid = isinstance(values, list) and all(
        isinstance(value, str) and (bool(value.strip()) if nonempty else True)
        for value in values
    )
    if not valid:
        qualifier = "nonempty strings" if nonempty else "strings"
        raise ValueError(f"{prefix}.{field} must be a list of {qualifier}")
