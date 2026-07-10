"""Stable route identity and bounded Schema v1 compatibility helpers."""

from __future__ import annotations

import hashlib
import json
import re
from typing import Any


_DYNAMIC_KEYS = {
    "generated_at",
    "created_at",
    "updated_at",
    "timestamp",
    "request_id",
    "trace_id",
}
_SECRET_KEY_RE = re.compile(
    r"(?:api[_ -]?key|access[_ -]?key|private[_ -]?key|secret|token|password|bearer|"
    r"authorization|auth|session|credentials?|访问令牌|授权|会话|私钥|凭证|密钥|密码|令牌)",
    re.IGNORECASE,
)
_SECRET_ASSIGNMENT_RE = re.compile(
    r"(?P<label>\b(?:api[_ -]?key|access[_ -]?key|private[_ -]?key|secret|token|password|"
    r"authorization|auth|session|credentials?)\b|访问令牌|授权|会话|私钥|凭证|密钥|密码|令牌)"
    r"(?P<separator>\s*[=:：＝]\s*)"
    r"(?P<value>\"[^\"\r\n]*\"|'[^'\r\n]*'|[^\s,;，；]+)",
    re.IGNORECASE,
)
_BEARER_RE = re.compile(r"\bBearer\s+[A-Za-z0-9._~+/=-]+", re.IGNORECASE)
_URI_CREDENTIAL_RE = re.compile(
    r"(?P<scheme>\b[a-z][a-z0-9+.-]*://)(?P<user>[^\s/@:]+):(?P<password>[^\s/@]+)@",
    re.IGNORECASE,
)
_OPENAI_KEY_RE = re.compile(r"\bsk-(?:proj-)?[A-Za-z0-9_-]{20,}\b")
_GITHUB_TOKEN_RE = re.compile(r"\b(?:ghp_|gho_|ghu_|ghs_|ghr_|github_pat_)[A-Za-z0-9_]{20,}\b")
_AWS_ACCESS_KEY_RE = re.compile(r"(?<![A-Z0-9])(?:AKIA|ASIA)[A-Z0-9]{16}(?![A-Z0-9])")
_JWT_RE = re.compile(r"\beyJ[A-Za-z0-9_-]{7,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\b")


def build_route_id(inputs: dict) -> str:
    canonical = json.dumps(
        inputs if isinstance(inputs, dict) else {},
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return f"sha256:{hashlib.sha256(canonical).hexdigest()}"


def build_route_identity_payload(
    *,
    current: str,
    history: str,
    stale: str,
    stale_policy: str,
    invariants: list[str] | tuple[str, ...],
    strategy: str,
    provider_identifier: str,
    catalog_content_hash: str,
    bundle_content_hash: str,
    overlap_content_hash: str,
    router_version: str,
    package_version: str,
    capabilities: list[str] | tuple[str, ...] = (),
) -> dict[str, Any]:
    return {
        "current": redact_route_identity_text(current),
        "history": redact_route_identity_text(history),
        "stale": redact_route_identity_text(stale),
        "stale_policy": redact_route_identity_text(stale_policy),
        "invariants": [redact_route_identity_text(value) for value in invariants],
        "capabilities": [redact_route_identity_text(value) for value in capabilities],
        "strategy": strategy,
        "provider_identifier": provider_identifier,
        "catalog_content_hash": catalog_content_hash,
        "bundle_content_hash": bundle_content_hash,
        "overlap_content_hash": overlap_content_hash,
        "router_version": router_version,
        "package_version": package_version,
    }


def redact_route_identity_text(value: Any) -> str:
    text = value if isinstance(value, str) else ""
    text = _URI_CREDENTIAL_RE.sub(
        lambda match: f"{match.group('scheme')}{match.group('user')}:[REDACTED]@",
        text,
    )
    text = _BEARER_RE.sub("Bearer [REDACTED]", text)
    text = _SECRET_ASSIGNMENT_RE.sub(
        lambda match: f"{match.group('label')}{match.group('separator')}[REDACTED]",
        text,
    )
    for pattern in (_OPENAI_KEY_RE, _GITHUB_TOKEN_RE, _AWS_ACCESS_KEY_RE, _JWT_RE):
        text = pattern.sub("[REDACTED]", text)
    return text


def build_canonical_content_hash(value: Any) -> str:
    canonical = json.dumps(
        _canonical_asset_value(value),
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


def _canonical_asset_value(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            key: "[REDACTED]" if _SECRET_KEY_RE.search(key) else _canonical_asset_value(item)
            for key, item in value.items()
            if isinstance(key, str) and key.lower() not in _DYNAMIC_KEYS
        }
    if isinstance(value, (list, tuple)):
        return [_canonical_asset_value(item) for item in value]
    if isinstance(value, str):
        return redact_route_identity_text(value)
    return value


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
