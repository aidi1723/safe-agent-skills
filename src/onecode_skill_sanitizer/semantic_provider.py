from __future__ import annotations

import math
from typing import Any, Protocol

from .compatibility import build_canonical_content_hash, redact_route_identity_text


class SemanticProvider(Protocol):
    name: str
    model_or_adapter: str

    def rerank(self, request: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError


def rerank_candidates(
    current_intent: str,
    constraints: dict[str, Any],
    candidates: list[dict[str, Any]],
    provider: SemanticProvider | None,
    *,
    mode: str,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    names = [item["skill"] for item in candidates]
    request = {
        "current_intent": redact_route_identity_text(current_intent),
        "constraints": constraints,
        "candidates": [
            {
                "skill": item["skill"],
                "description": item.get("description", ""),
                "deterministic_score": item["deterministic_score"],
                "matched_capabilities": item.get("matched_capabilities", []),
            }
            for item in candidates
        ],
    }
    scope_hash = build_canonical_content_hash(request["candidates"])
    if provider is None or mode == "none" or len(candidates) < 2:
        return candidates, _record(
            "none", "none", "none", "not_requested", scope_hash, [], "not_requested"
        )
    requested = provider.name
    try:
        response = provider.rerank(request)
    except Exception as exc:
        return _clear_semantic(candidates), _record(
            requested, "none", provider.model_or_adapter, "provider_failure", scope_hash,
            [f"provider_exception:{type(exc).__name__}"],
        )
    reasons = _validate_response(response, names)
    if reasons:
        return _clear_semantic(candidates), _record(
            requested, "none", provider.model_or_adapter, "invalid_provider_response", scope_hash, reasons,
        )
    if mode == "influence" and min(item["confidence"] for item in response["scores"]) < 0.60:
        return _clear_semantic(candidates), _record(
            requested, "none", provider.model_or_adapter,
            "low_semantic_confidence", scope_hash, ["low_semantic_confidence"],
        )
    semantic = {item["skill"]: item["score"] for item in response["scores"]}
    reranked = []
    for item in candidates:
        updated = dict(item)
        updated["semantic_score"] = semantic[item["skill"]]
        if mode == "influence":
            updated["final_score"] = round(0.75 * item["deterministic_score"] + 0.25 * semantic[item["skill"]], 6)
        reranked.append(updated)
    if mode == "influence":
        reranked.sort(key=lambda item: (-item["final_score"], -item["deterministic_score"], item["skill"]))
    status = "accepted_shadow" if mode == "shadow" else "accepted_influence"
    return reranked, _record(requested, requested, provider.model_or_adapter, "none", scope_hash, [], status)


def _validate_response(response: Any, names: list[str]) -> list[str]:
    if not isinstance(response, dict) or set(response) != {"status", "scores"} or response.get("status") != "ok":
        return ["schema_mismatch"]
    scores = response.get("scores")
    if not isinstance(scores, list):
        return ["schema_mismatch"]
    response_names = [item.get("skill") for item in scores if isinstance(item, dict)]
    if len(response_names) != len(scores):
        return ["schema_mismatch"]
    if len(response_names) != len(set(response_names)):
        return ["duplicate_candidate"]
    if set(response_names) != set(names):
        return ["candidate_scope_mismatch"]
    for item in scores:
        if set(item) != {"skill", "score", "confidence"}:
            return ["schema_mismatch"]
        for field in ("score", "confidence"):
            value = item[field]
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
                return [f"invalid_{field}"]
            if not 0 <= value <= 1:
                return [f"out_of_range_{field}"]
    return []


def _clear_semantic(candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    cleared = []
    for item in candidates:
        updated = dict(item)
        updated["semantic_score"] = None
        updated["final_score"] = updated["deterministic_score"]
        cleared.append(updated)
    return cleared


def _record(
    requested: str,
    used: str,
    adapter: str,
    fallback: str,
    scope_hash: str,
    reasons: list[str],
    status: str = "rejected_fallback",
) -> dict[str, Any]:
    return {
        "requested": requested,
        "used": used,
        "model_or_adapter": adapter,
        "fallback_reason": fallback,
        "candidate_scope_hash": scope_hash,
        "response_status": status,
        "validation_reason_codes": reasons,
    }
