"""Stable route identity and bounded Schema v1 compatibility helpers."""

from __future__ import annotations

import hashlib
import json
from typing import Any


_DYNAMIC_KEYS = {
    "generated_at",
    "created_at",
    "updated_at",
    "timestamp",
    "request_id",
    "trace_id",
}
_SECRET_MARKERS = ("api_key", "apikey", "secret", "password", "credential", "token")


def build_route_id(inputs: dict) -> str:
    canonical = json.dumps(
        _routing_relevant(inputs if isinstance(inputs, dict) else {}),
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return f"sha256:{hashlib.sha256(canonical).hexdigest()}"


def to_legacy_v1(payload: dict) -> dict:
    source = payload if isinstance(payload, dict) else {}
    intents = _object_list(_object(source.get("intent_graph")).get("intents"))
    scenarios = _object_list(source.get("selected_scenarios"))[:100]
    ranked = sorted(
        scenarios,
        key=lambda item: (-_bounded_score(item.get("score")), _scenario_id(item)),
    )
    primary = ranked[0] if ranked else {}
    primary_id = _scenario_id(primary)
    dropped = [_scenario_id(item) for item in ranked[1:] if _scenario_id(item)]
    graph = _object(source.get("execution_graph"))
    nodes = {
        node.get("id"): set(_string_list(node.get("scenario_ids")))
        for node in _object_list(graph.get("nodes"))[:1000]
        if isinstance(node.get("id"), str)
    }
    cross_edges = 0
    for edge in _object_list(graph.get("edges"))[:2000]:
        source_scenarios = nodes.get(edge.get("from"), set())
        target_scenarios = nodes.get(edge.get("to"), set())
        if source_scenarios and target_scenarios and source_scenarios.isdisjoint(target_scenarios):
            cross_edges += 1

    return {
        "schema_version": 1,
        "task": _object(source.get("normalized_task")).get("current", ""),
        "selected_scenario": (
            {
                "id": primary_id,
                "match_score": _bounded_score(primary.get("score")),
                "intent_ids": _string_list(primary.get("intent_ids")),
            }
            if primary_id
            else {}
        ),
        "compatibility_loss": {
            "multi_intent_dropped": len(intents) > 1,
            "scenarios_dropped": dropped,
            "cross_scenario_edges_dropped": cross_edges,
        },
    }


def _routing_relevant(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            key: _routing_relevant(item)
            for key, item in value.items()
            if isinstance(key, str) and not _excluded_key(key)
        }
    if isinstance(value, (list, tuple)):
        return [_routing_relevant(item) for item in value]
    return value


def _excluded_key(key: str) -> bool:
    normalized = key.lower()
    return normalized in _DYNAMIC_KEYS or any(marker in normalized for marker in _SECRET_MARKERS)


def _object(value: Any) -> dict:
    return value if isinstance(value, dict) else {}


def _object_list(value: Any) -> list[dict]:
    return [item for item in value if isinstance(item, dict)] if isinstance(value, list) else []


def _string_list(value: Any) -> list[str]:
    return [item for item in value if isinstance(item, str)] if isinstance(value, list) else []


def _scenario_id(item: dict) -> str:
    value = item.get("scenario_id", item.get("scenario", item.get("id", "")))
    return value if isinstance(value, str) else ""


def _bounded_score(value: Any) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return 0.0
    return max(0.0, min(float(value), 1.0))
