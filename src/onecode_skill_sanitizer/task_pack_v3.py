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


_STRONG_ORDER_BOUNDARY_RE = re.compile(r"[.;\n。；！？!?]+")
_BINARY_ORDER_CONNECTOR_RE = re.compile(
    r"(?P<after>\bafter\b)|(?P<before>\bbefore\b)|"
    r"(?P<after_zh>之后)|(?P<before_zh>之前)",
    re.IGNORECASE,
)
_SEQUENCE_ORDER_CONNECTOR_RE = re.compile(r"\bthen\b|然后|再|最后", re.IGNORECASE)
_GROUP_CONTINUATION_RE = re.compile(r"(?:\b(?:but|and)\b|但是|但|并且|且)\s*[,，]?\s*$", re.IGNORECASE)
_XIAN_RE = re.compile(r"先(?!不)")


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
    for clause in _STRONG_ORDER_BOUNDARY_RE.split(current):
        if not clause.strip():
            continue
        relations.extend(_binary_order_relations(clause, required, admitted))
        relations.extend(_sequence_order_relations(clause, required, admitted))

    return list(dict.fromkeys(relation for relation in relations if relation[0] != relation[1]))


def _binary_order_relations(
    clause: str,
    required: set[str],
    admitted: set[str],
) -> list[tuple[str, str]]:
    connectors = list(_BINARY_ORDER_CONNECTOR_RE.finditer(clause))
    if not connectors:
        return []

    active_anchor = _last_skill(clause[: connectors[0].start()], required, admitted)
    relations: list[tuple[str, str]] = []
    for index, connector in enumerate(connectors):
        next_start = connectors[index + 1].start() if index + 1 < len(connectors) else len(clause)
        complement = _first_skill(clause[connector.end() : next_start], required, admitted)
        if index:
            previous = connectors[index - 1]
            gap = clause[previous.end() : connector.start()]
            gap_mentions = _skill_mentions(gap, required, admitted)
            gap_actions = _unique_skill_mentions(gap_mentions)
            continues_group = _GROUP_CONTINUATION_RE.search(gap) and len(gap_actions) <= 1
            if not continues_group:
                active_anchor = gap_mentions[-1][2] if gap_mentions else _last_skill(
                    clause[: connector.start()], required, admitted
                )
        if active_anchor is None or complement is None:
            continue
        relations.append(_direct_binary_relation(connector.lastgroup, active_anchor, complement))
    return relations


def _direct_binary_relation(kind: str | None, anchor: str, complement: str) -> tuple[str, str]:
    if kind == "after":
        return complement, anchor
    if kind == "before":
        return anchor, complement
    # Chinese temporal connectors are postfixes attached to the anchor action.
    if kind == "after_zh":
        return anchor, complement
    return complement, anchor


def _sequence_order_relations(
    clause: str,
    required: set[str],
    admitted: set[str],
) -> list[tuple[str, str]]:
    relations: list[tuple[str, str]] = []
    for connector in _SEQUENCE_ORDER_CONNECTOR_RE.finditer(clause):
        left = _last_skill(clause[: connector.start()], required, admitted)
        right = _first_skill(clause[connector.end() :], required, admitted)
        if left is not None and right is not None:
            relations.append((left, right))

    xian = _XIAN_RE.search(clause)
    if xian is not None and not _BINARY_ORDER_CONNECTOR_RE.search(clause[xian.end() :]):
        ordered = [
            item[2]
            for item in _skill_mentions(clause[xian.end() :], required, admitted)
        ]
        relations.extend(zip(ordered, ordered[1:]))
    return relations


def _first_skill(text: str, required: set[str], admitted: set[str]) -> str | None:
    mentions = _skill_mentions(text, required, admitted)
    return mentions[0][2] if mentions else None


def _last_skill(text: str, required: set[str], admitted: set[str]) -> str | None:
    mentions = _skill_mentions(text, required, admitted)
    return mentions[-1][2] if mentions else None


def _skill_mentions(
    text: str,
    required: set[str],
    admitted: set[str],
) -> list[tuple[int, int, str]]:
    mentions: list[tuple[int, int, str]] = []
    for capability, pattern in CAPABILITY_PATTERNS.items():
        skill = CAPABILITY_SKILL[capability]
        if capability in required and skill in admitted:
            mentions.extend(
                (match.start(), match.end(), skill) for match in pattern.finditer(text)
            )
    return sorted(mentions, key=lambda item: (item[0], item[1], item[2]))


def _unique_skill_mentions(
    mentions: list[tuple[int, int, str]],
) -> list[tuple[int, int, str]]:
    unique: list[tuple[int, int, str]] = []
    seen: set[str] = set()
    for mention in mentions:
        if mention[2] not in seen:
            unique.append(mention)
            seen.add(mention[2])
    return unique
