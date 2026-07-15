"""Bounded semantic reranking over the fixed trusted candidate cohort."""

from __future__ import annotations

import copy
import json
import math
from typing import Any, Protocol

from .compatibility import build_canonical_content_hash, redact_route_identity_text
from .skill_candidates import HIGH_FREQUENCY_SKILL_NAMES


_MODES = frozenset({"none", "shadow", "influence"})
_NEED_DECISIONS = frozenset({"none", "single", "composite", "clarify"})
_CANONICAL_CAPABILITIES = {
    "codebase-explore-map": "code.explore",
    "code-review-risk": "code.review",
    "code-test-regression": "code.test",
    "execution-browser-check": "execution.browser_check",
    "research-source-check": "research.source",
    "design-ui-review": "design.ui_review",
    "security-supply-chain-review": "security.supply_chain",
}
_CONSTRAINT_KEYS = frozenset({
    "decision",
    "specialized_need",
    "required_capabilities",
    "explicit_skills",
    "excluded_skills",
    "explanation_only",
    "inventory_only",
    "missing_inputs",
    "mandatory_capabilities",
    "policy_block_reasons",
    "reason_codes",
})
_CONSTRAINT_BOOL_FIELDS = frozenset({
    "specialized_need",
    "explanation_only",
    "inventory_only",
})
_CONSTRAINT_LIST_FIELDS = _CONSTRAINT_KEYS - _CONSTRAINT_BOOL_FIELDS - {"decision"}
_CANDIDATE_REQUIRED_FIELDS = frozenset({
    "skill",
    "status",
    "excluded",
    "description",
    "deterministic_score",
    "matched_capabilities",
})
_CANDIDATE_FIELDS = frozenset({
    "skill",
    "registry_path",
    "status",
    "description",
    "deterministic_score",
    "semantic_score",
    "final_score",
    "matched_intents",
    "matched_capabilities",
    "matched_examples",
    "positive_evidence",
    "penalties",
    "exclusions",
    "excluded",
    "selected",
    "reason_codes",
})
_MAX_INTENT_CHARS = 16 * 1024
_MAX_DESCRIPTION_CHARS = 4 * 1024
_MAX_IDENTIFIER_CHARS = 128
_MAX_CONSTRAINT_ITEMS = 64
_MAX_CONSTRAINT_STRING_CHARS = 4 * 1024
_MAX_REQUEST_BYTES = 64 * 1024
_MAX_CANDIDATE_BYTES = 64 * 1024


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
    _validate_mode(mode)
    sanitized_intent = _sanitize_current_intent(current_intent)
    sanitized_constraints = _sanitize_constraints(constraints)
    baseline = _deterministic_baseline(candidates)
    eligible = [item for item in baseline if not item["excluded"]]
    eligible_names = tuple(item["skill"] for item in eligible)
    request = {
        "current_intent": sanitized_intent,
        "constraints": sanitized_constraints,
        "candidates": [
            {
                "skill": item["skill"],
                "description": redact_route_identity_text(item["description"]),
                "deterministic_score": item["deterministic_score"],
                "matched_capabilities": list(item["matched_capabilities"]),
            }
            for item in eligible
        ],
    }
    _validate_request_envelope(request)
    scope_hash = build_canonical_content_hash(request)
    if provider is None or mode == "none" or len(eligible) < 2:
        return baseline, _record(
            "none", "none", "none", "not_requested", scope_hash, [], "not_requested"
        )

    requested = "invalid_provider"
    adapter = "none"
    try:
        provider_name = _sanitize_provider_identifier(provider.name)
        provider_adapter = _sanitize_provider_identifier(provider.model_or_adapter)
        requested = provider_name
        adapter = provider_adapter
        rerank = provider.rerank
        if not callable(rerank):
            raise TypeError("provider rerank must be callable")
        response = rerank(request)
        reasons = _validate_response(response, eligible_names)
    except Exception as exc:
        return baseline, _record(
            requested,
            "none",
            adapter,
            "provider_failure",
            scope_hash,
            [f"provider_exception:{_safe_exception_type(exc)}"],
        )

    if reasons:
        return baseline, _record(
            requested,
            "none",
            adapter,
            "invalid_provider_response",
            scope_hash,
            reasons,
        )
    if mode == "influence" and min(item["confidence"] for item in response["scores"]) < 0.60:
        return baseline, _record(
            requested,
            "none",
            adapter,
            "low_semantic_confidence",
            scope_hash,
            ["low_semantic_confidence"],
        )

    semantic = {item["skill"]: item["score"] for item in response["scores"]}
    for item in baseline:
        if item["excluded"]:
            continue
        item["semantic_score"] = semantic[item["skill"]]
        if mode == "influence":
            item["final_score"] = round(
                0.75 * item["deterministic_score"] + 0.25 * semantic[item["skill"]],
                6,
            )
    if mode == "influence":
        baseline.sort(
            key=lambda item: (
                item["excluded"],
                -item["final_score"],
                -item["deterministic_score"],
                item["skill"],
            )
        )
    status = "accepted_shadow" if mode == "shadow" else "accepted_influence"
    return baseline, _record(requested, requested, adapter, "none", scope_hash, [], status)


def _validate_mode(mode: Any) -> None:
    if type(mode) is not str or mode not in _MODES:
        raise ValueError("mode must be one of none, shadow, influence")


def _sanitize_current_intent(value: Any) -> str:
    if type(value) is not str or len(value) > _MAX_INTENT_CHARS:
        raise ValueError("current_intent must be a string of at most 16384 characters")
    return redact_route_identity_text(value)


def _sanitize_constraints(value: Any) -> dict[str, Any]:
    if type(value) is not dict:
        raise ValueError("constraints must be an object")
    keys = tuple(value.keys())
    if any(type(key) is not str for key in keys) or not set(keys).issubset(_CONSTRAINT_KEYS):
        raise ValueError("constraints contain an unknown field")
    sanitized: dict[str, Any] = {}
    for key in keys:
        item = value[key]
        if key == "decision":
            if type(item) is not str or item not in _NEED_DECISIONS:
                raise ValueError("constraints.decision is invalid")
            sanitized[key] = redact_route_identity_text(item)
        elif key in _CONSTRAINT_BOOL_FIELDS:
            if type(item) is not bool:
                raise ValueError(f"constraints.{key} must be a boolean")
            sanitized[key] = item
        elif key in _CONSTRAINT_LIST_FIELDS:
            sanitized[key] = _sanitize_constraint_list(item, key)
    return sanitized


def _sanitize_constraint_list(value: Any, field: str) -> list[str]:
    if type(value) not in (list, tuple) or len(value) > _MAX_CONSTRAINT_ITEMS:
        raise ValueError(f"constraints.{field} must be a bounded string list")
    result: list[str] = []
    seen: set[str] = set()
    for item in value:
        if (
            type(item) is not str
            or not item.strip()
            or len(item) > _MAX_CONSTRAINT_STRING_CHARS
            or item in seen
        ):
            raise ValueError(f"constraints.{field} must contain unique bounded strings")
        seen.add(item)
        result.append(redact_route_identity_text(item))
    return result


def _deterministic_baseline(value: Any) -> list[dict[str, Any]]:
    if type(value) is not list or len(value) > len(HIGH_FREQUENCY_SKILL_NAMES):
        raise ValueError("candidates must be a list with at most 7 items")
    baseline: list[dict[str, Any]] = []
    names: set[str] = set()
    for index, item in enumerate(value):
        context = f"candidate[{index}]"
        if type(item) is not dict:
            raise ValueError(f"{context} must be an object")
        keys = tuple(item.keys())
        if any(type(key) is not str for key in keys):
            raise ValueError(f"{context} contains an invalid field")
        if not set(keys).issubset(_CANDIDATE_FIELDS):
            raise ValueError(f"{context} contains an unknown field")
        if not _CANDIDATE_REQUIRED_FIELDS.issubset(keys):
            raise ValueError(f"{context} is missing required fields")
        name = item["skill"]
        if type(name) is not str or not name or name not in HIGH_FREQUENCY_SKILL_NAMES:
            raise ValueError(f"{context}.skill must belong to the fixed cohort")
        if name in names:
            raise ValueError(f"{context}.skill must be unique")
        if type(item["status"]) is not str or item["status"] != "trusted":
            raise ValueError(f"{context}.status must be trusted")
        if type(item["excluded"]) is not bool:
            raise ValueError(f"{context}.excluded must be a boolean")
        score = item["deterministic_score"]
        if type(score) not in (int, float) or not math.isfinite(score) or not 0 <= score <= 1:
            raise ValueError(f"{context}.deterministic_score must be finite from 0 to 1")
        if item["excluded"] and score != 0:
            raise ValueError(f"{context}.deterministic_score must be zero when excluded")
        description = item["description"]
        if type(description) is not str or len(description) > _MAX_DESCRIPTION_CHARS:
            raise ValueError(f"{context}.description must be a bounded string")
        _validate_matched_capabilities(item["matched_capabilities"], name, context)
        try:
            cloned = copy.deepcopy(item)
        except Exception as exc:
            raise ValueError(f"{context} could not be cloned") from exc
        cloned["semantic_score"] = None
        cloned["final_score"] = score
        _validate_candidate_envelope(cloned, context)
        baseline.append(cloned)
        names.add(name)
    return baseline


def _validate_matched_capabilities(value: Any, name: str, context: str) -> None:
    if type(value) not in (list, tuple) or len(value) > 1:
        raise ValueError(f"{context}.matched_capabilities must be a bounded list")
    if value and (
        type(value[0]) is not str
        or value[0] != _CANONICAL_CAPABILITIES[name]
    ):
        raise ValueError(f"{context}.matched_capabilities contains an invalid value")


def _validate_candidate_envelope(value: dict[str, Any], context: str) -> None:
    try:
        encoded = json.dumps(
            value,
            allow_nan=False,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{context} must be strict JSON") from exc
    if len(encoded) > _MAX_CANDIDATE_BYTES:
        raise ValueError(f"{context} exceeds 65536 bytes")


def _validate_request_envelope(request: dict[str, Any]) -> None:
    try:
        encoded = json.dumps(
            request,
            allow_nan=False,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise ValueError("semantic request must be strict JSON") from exc
    if len(encoded) > _MAX_REQUEST_BYTES:
        raise ValueError("semantic request exceeds 65536 bytes")


def _sanitize_provider_identifier(value: Any) -> str:
    if (
        type(value) is not str
        or not value.strip()
        or len(value) > _MAX_IDENTIFIER_CHARS
    ):
        raise ValueError("provider metadata is invalid")
    sanitized = redact_route_identity_text(value).strip()
    if not sanitized or len(sanitized) > _MAX_IDENTIFIER_CHARS:
        raise ValueError("provider metadata is invalid")
    return sanitized


def _safe_exception_type(exc: Exception) -> str:
    try:
        value = type(exc).__name__
    except Exception:
        return "Exception"
    if type(value) is not str or not value:
        return "Exception"
    sanitized = redact_route_identity_text(value)
    return sanitized[:_MAX_IDENTIFIER_CHARS] or "Exception"


def _validate_response(response: Any, names: tuple[str, ...]) -> list[str]:
    if type(response) is not dict:
        return ["schema_mismatch"]
    response_keys = tuple(response.keys())
    if (
        any(type(key) is not str for key in response_keys)
        or set(response_keys) != {"status", "scores"}
        or type(response.get("status")) is not str
        or response.get("status") != "ok"
    ):
        return ["schema_mismatch"]
    scores = response.get("scores")
    if type(scores) is not list:
        return ["schema_mismatch"]
    if len(scores) < 1 or len(scores) != len(names):
        return ["candidate_scope_mismatch"]

    response_names: list[str] = []
    for item in scores:
        if type(item) is not dict:
            return ["schema_mismatch"]
        item_keys = tuple(item.keys())
        if (
            any(type(key) is not str for key in item_keys)
            or set(item_keys) != {"skill", "score", "confidence"}
        ):
            return ["schema_mismatch"]
        skill = item["skill"]
        if (
            type(skill) is not str
            or not skill
            or skill not in HIGH_FREQUENCY_SKILL_NAMES
        ):
            return ["candidate_scope_mismatch"]
        response_names.append(skill)
        for field in ("score", "confidence"):
            number = item[field]
            if type(number) not in (int, float) or not math.isfinite(number):
                return [f"invalid_{field}"]
            if not 0 <= number <= 1:
                return [f"out_of_range_{field}"]
    if len(response_names) != len(set(response_names)):
        return ["duplicate_candidate"]
    if set(response_names) != set(names):
        return ["candidate_scope_mismatch"]
    return []


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
