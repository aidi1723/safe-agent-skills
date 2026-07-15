from __future__ import annotations

import json
from pathlib import Path
from typing import Any


HIGH_FREQUENCY_ENTRY_NAMES = (
    "safe-agent-router",
    "codebase-explore-map",
    "code-review-risk",
    "code-test-regression",
    "execution-browser-check",
    "research-source-check",
    "design-ui-review",
    "security-supply-chain-review",
)
HIGH_FREQUENCY_SKILL_NAMES = HIGH_FREQUENCY_ENTRY_NAMES[1:]
EXAMPLE_CLASSES = {"positive", "near_miss", "negation", "explanation_only", "composition"}
NEED_DECISIONS = {"none", "single", "composite", "clarify"}
EXAMPLE_KEYS = {
    "id", "query", "expected_need", "required_skills", "forbidden_skills",
    "intent_labels", "capability_labels", "example_class", "review",
}


class RoutingExampleError(ValueError):
    pass


def load_routing_examples(path: Path) -> list[dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or set(payload) != {"schema_version", "scope", "examples"}:
        raise RoutingExampleError("routing examples must use the strict top-level contract")
    if payload["schema_version"] != 1:
        raise RoutingExampleError("routing examples schema_version must be 1")
    scope = payload["scope"]
    if scope != {
        "entry_names": list(HIGH_FREQUENCY_ENTRY_NAMES),
        "candidate_names": list(HIGH_FREQUENCY_SKILL_NAMES),
    }:
        raise RoutingExampleError("routing example scope does not match the fixed cohort")
    examples = payload["examples"]
    if not isinstance(examples, list):
        raise RoutingExampleError("routing examples must be a list")
    seen_ids: set[str] = set()
    seen_queries: set[str] = set()
    for index, item in enumerate(examples):
        if not isinstance(item, dict) or set(item) != EXAMPLE_KEYS:
            raise RoutingExampleError(f"example[{index}] has an invalid field set")
        if not isinstance(item["id"], str) or not item["id"] or item["id"] in seen_ids:
            raise RoutingExampleError(f"example[{index}] id must be unique")
        query = item["query"]
        normalized_query = " ".join(query.casefold().split()) if isinstance(query, str) else ""
        if not normalized_query or normalized_query in seen_queries:
            raise RoutingExampleError(f"example[{index}] query must be unique")
        if item["expected_need"] not in NEED_DECISIONS or item["example_class"] not in EXAMPLE_CLASSES:
            raise RoutingExampleError(f"example[{index}] enum value is invalid")
        required = _strict_string_list(item["required_skills"], f"example[{index}].required_skills")
        forbidden = _strict_string_list(item["forbidden_skills"], f"example[{index}].forbidden_skills")
        if not set(required + forbidden).issubset(HIGH_FREQUENCY_SKILL_NAMES):
            raise RoutingExampleError(f"example[{index}] references an out-of-cohort skill")
        if set(required) & set(forbidden):
            raise RoutingExampleError(f"example[{index}] labels overlap")
        _strict_string_list(item["intent_labels"], f"example[{index}].intent_labels")
        _strict_string_list(item["capability_labels"], f"example[{index}].capability_labels")
        review = item["review"]
        if not isinstance(review, dict) or review.get("status") != "approved":
            raise RoutingExampleError(f"example[{index}] is not approved")
        if review.get("generated_from_router") is not False:
            raise RoutingExampleError(f"example[{index}] must not be generated from router output")
        if not all(isinstance(review.get(key), str) and review[key] for key in (
            "reviewed_at", "reviewer_role", "source_classification"
        )):
            raise RoutingExampleError(f"example[{index}] review metadata is incomplete")
        seen_ids.add(item["id"])
        seen_queries.add(normalized_query)
    return examples


def _strict_string_list(value: Any, field: str) -> list[str]:
    if not isinstance(value, list) or any(not isinstance(item, str) or not item for item in value):
        raise RoutingExampleError(f"{field} must contain nonempty strings")
    if len(value) != len(set(value)):
        raise RoutingExampleError(f"{field} must not contain duplicates")
    return value
