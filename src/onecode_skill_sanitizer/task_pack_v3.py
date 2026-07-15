from __future__ import annotations

import json
from pathlib import Path
import re
from typing import Any

from . import __version__
from .compatibility import build_canonical_content_hash
from .compatibility import build_route_id
from .compatibility import build_route_identity_payload
from .compatibility import v3_compatibility_report
from .intent import decompose_task, normalize_task
from .need_gate import CAPABILITY_PATTERNS, CAPABILITY_SKILL, decide_skill_need
from .registry import load_registry_index, utc_now, verify_registry
from .semantic_provider import SemanticProvider, rerank_candidates
from .skill_candidates import HIGH_FREQUENCY_ENTRY_NAMES
from .skill_candidates import load_cohort_profiles
from .skill_candidates import load_routing_examples
from .skill_candidates import retrieve_skill_candidates
from .skill_selection import compose_skill_selection
from .task_packs import load_skill_pack_item


def build_task_pack_v3(
    registry_dir: Path,
    task: str,
    bundles_path: Path,
    routing_examples_path: Path,
    *,
    max_candidates: int = 3,
    semantic_provider: SemanticProvider | None = None,
    semantic_mode: str = "shadow",
) -> dict[str, Any]:
    if not task.strip():
        raise ValueError("task must not be empty")
    if semantic_mode not in {"none", "shadow", "influence"}:
        raise ValueError("semantic_mode must be none, shadow, or influence")

    verification = verify_registry(registry_dir)
    if verification["status"] != "ok":
        raise SystemExit("registry verification failed; refusing to build task pack")

    normalized = normalize_task(task)
    intent_graph = decompose_task(task)
    need = decide_skill_need(normalized)
    examples = load_routing_examples(routing_examples_path)
    profiles = load_cohort_profiles(registry_dir)
    candidates = retrieve_skill_candidates(
        normalized,
        need,
        profiles,
        examples,
        top_k=max_candidates,
    )
    active_provider = None if need["decision"] == "none" else semantic_provider
    candidates, provider_record = rerank_candidates(
        normalized.current,
        need,
        candidates,
        active_provider,
        mode="none" if active_provider is None else semantic_mode,
    )
    explicit_order = _extract_explicit_skill_order(normalized.current, need, candidates)
    composed = compose_skill_selection(
        need,
        candidates,
        profiles,
        explicit_order=explicit_order,
    )

    registry_index = load_registry_index(registry_dir)
    entries = {entry["name"]: entry for entry in registry_index["skills"]}
    selected_items = [
        load_skill_pack_item(registry_dir, entries[name])
        for name in composed["selected_skill_names"]
    ]
    selected_names = set(composed["selected_skill_names"])
    traced_candidates = [
        _trace_candidate(candidate, selected_names)
        for candidate in candidates
    ]

    bundles = json.loads(bundles_path.read_text(encoding="utf-8"))
    examples_content_hash = build_canonical_content_hash(examples)
    route_identity = {
        "base": build_route_identity_payload(
            current=normalized.current,
            history=normalized.history,
            stale=normalized.stale,
            stale_policy=normalized.stale_policy,
            invariants=[],
            capabilities=need["required_capabilities"],
            strategy="high_frequency_v3",
            provider_identifier=provider_record["used"],
            catalog_content_hash=build_canonical_content_hash(registry_index),
            bundle_content_hash=build_canonical_content_hash(bundles),
            overlap_content_hash="none",
            router_version="high-frequency-intelligent-router-v3",
            package_version=__version__,
        ),
        "routing_examples_content_hash": examples_content_hash,
        "cohort_names": list(HIGH_FREQUENCY_ENTRY_NAMES),
        "constraints": {
            "excluded_skills": need["excluded_skills"],
            "missing_inputs": need["missing_inputs"],
            "mandatory_capabilities": need["mandatory_capabilities"],
        },
    }
    payload = {
        "schema_version": 3,
        "generated_at": utc_now(),
        "route_id": build_route_id(route_identity),
        "routing_mode": (
            "deterministic"
            if provider_record["used"] == "none"
            else "semantic_shadow"
            if semantic_mode == "shadow"
            else "hybrid"
        ),
        "routing_status": composed["routing_status"],
        "provider": provider_record,
        "normalized_task": normalized.to_json(),
        "need_decision": need,
        "intent_graph": intent_graph.to_json(),
        "candidates": traced_candidates,
        "selection": {
            **composed["selection"],
            "need_decision": need["decision"],
            "selected_skills": selected_items,
        },
        "capability_resolution": composed["capability_resolution"],
        "execution_graph": composed["execution_graph"],
        "confidence": composed["confidence"],
        "host_execution_protocol": {
            "mode": "method_only",
            "runtime_boundary": "The host runtime controls permissions and execution.",
            "node_statuses": [
                "pending",
                "ready",
                "running",
                "waiting_approval",
                "completed",
                "failed",
                "blocked",
                "skipped",
            ],
        },
        "routing_metrics": {
            "candidate_count": len(traced_candidates),
            "selected_skill_count": len(selected_items),
            "required_capability_count": len(need["required_capabilities"]),
            "covered_capability_count": composed["capability_resolution"]["covered_count"],
            "runtime_example_count": len(examples),
            "cohort_candidate_count": len(profiles),
        },
        "registry_verification": {
            "catalog": verification,
            "routing_examples": {
                "status": "ok",
                "count": len(examples),
                "content_hash": examples_content_hash,
            },
        },
        "compatibility": {},
    }
    payload["compatibility"] = v3_compatibility_report(payload)
    return payload


def _trace_candidate(candidate: dict[str, Any], selected_names: set[str]) -> dict[str, Any]:
    traced = json.loads(json.dumps(candidate, ensure_ascii=False))
    selected = traced["skill"] in selected_names
    traced["selected"] = selected
    traced["reason_codes"] = sorted(
        set(traced["reason_codes"]) | ({"selected"} if selected else {"rejected"})
    )
    return traced


def _extract_explicit_skill_order(
    current: str,
    need: dict[str, Any],
    candidates: list[dict[str, Any]],
) -> list[tuple[str, str]]:
    admitted = {item["skill"] for item in candidates}
    required = set(need["required_capabilities"])
    relations: list[tuple[str, str]] = []
    binary_connectors = re.compile(
        r"(?P<after>\bafter\b)|(?P<before>\bbefore\b)|"
        r"(?P<after_zh>之后)|(?P<before_zh>之前)",
        re.IGNORECASE,
    )
    for connector in binary_connectors.finditer(current):
        pair = _skills_around_connector(current, connector, required, admitted)
        if pair is None:
            continue
        left, right = pair
        if connector.lastgroup == "after":
            relations.append((right, left))
        elif connector.lastgroup == "before":
            relations.append((left, right))
        # Chinese temporal connectors are postfixes attached to the left action.
        elif connector.lastgroup == "after_zh":
            relations.append((left, right))
        else:
            relations.append((right, left))

    sequence_connectors = re.compile(r"\bthen\b|然后|再|最后", re.IGNORECASE)
    for connector in sequence_connectors.finditer(current):
        pair = _skills_around_connector(current, connector, required, admitted)
        if pair is not None:
            relations.append(pair)

    return list(dict.fromkeys(relation for relation in relations if relation[0] != relation[1]))


def _skills_around_connector(
    current: str,
    connector: re.Match[str],
    required: set[str],
    admitted: set[str],
) -> tuple[str, str] | None:
    left = _skill_mentions(current[: connector.start()], required, admitted)
    right = _skill_mentions(current[connector.end() :], required, admitted)
    if not left or not right:
        return None
    return left[-1][1], right[0][1]


def _skill_mentions(
    text: str,
    required: set[str],
    admitted: set[str],
) -> list[tuple[int, str]]:
    mentions: list[tuple[int, str]] = []
    for capability, pattern in CAPABILITY_PATTERNS.items():
        skill = CAPABILITY_SKILL[capability]
        if capability in required and skill in admitted:
            mentions.extend((match.start(), skill) for match in pattern.finditer(text))
    return sorted(mentions, key=lambda item: (item[0], item[1]))
