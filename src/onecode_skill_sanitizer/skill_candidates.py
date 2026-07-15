from __future__ import annotations

import json
from datetime import date
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
_REVIEW_KEYS = {
    "status", "reviewed_at", "reviewer_role", "source_classification", "generated_from_router",
}


class RoutingExampleError(ValueError):
    pass


def load_routing_examples(path: Path) -> list[dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or set(payload) != {"schema_version", "scope", "examples"}:
        raise RoutingExampleError("routing examples must use the strict top-level contract")
    schema_version = payload["schema_version"]
    if not isinstance(schema_version, int) or isinstance(schema_version, bool) or schema_version != 1:
        raise RoutingExampleError("routing examples schema_version must be the integer 1")
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
        if not isinstance(item["id"], str) or not item["id"].strip():
            raise RoutingExampleError(f"example[{index}] id must be a nonempty string")
        if item["id"] in seen_ids:
            raise RoutingExampleError(f"example[{index}] id must be unique")
        query = item["query"]
        normalized_query = " ".join(query.casefold().split()) if isinstance(query, str) else ""
        if not normalized_query:
            raise RoutingExampleError(f"example[{index}] query must be a nonempty string")
        if normalized_query in seen_queries:
            raise RoutingExampleError(f"example[{index}] query must be unique")
        if not isinstance(item["expected_need"], str) or item["expected_need"] not in NEED_DECISIONS:
            raise RoutingExampleError(f"example[{index}] expected_need is invalid")
        if not isinstance(item["example_class"], str) or item["example_class"] not in EXAMPLE_CLASSES:
            raise RoutingExampleError(f"example[{index}] example_class is invalid")
        required = _strict_string_list(item["required_skills"], f"example[{index}].required_skills")
        forbidden = _strict_string_list(item["forbidden_skills"], f"example[{index}].forbidden_skills")
        if not set(required + forbidden).issubset(HIGH_FREQUENCY_SKILL_NAMES):
            raise RoutingExampleError(f"example[{index}] references an out-of-cohort skill")
        if set(required) & set(forbidden):
            raise RoutingExampleError(f"example[{index}] labels overlap")
        _strict_string_list(item["intent_labels"], f"example[{index}].intent_labels")
        _strict_string_list(item["capability_labels"], f"example[{index}].capability_labels")
        review = item["review"]
        if not isinstance(review, dict) or set(review) != _REVIEW_KEYS:
            raise RoutingExampleError(f"example[{index}] review has an invalid field set")
        if review["status"] != "approved":
            raise RoutingExampleError(f"example[{index}] is not approved")
        if review["reviewer_role"] != "operator_review":
            raise RoutingExampleError(f"example[{index}] review must be operator reviewed")
        if review["source_classification"] != "local_curated":
            raise RoutingExampleError(f"example[{index}] review must be locally curated")
        if review["generated_from_router"] is not False:
            raise RoutingExampleError(f"example[{index}] must not be generated from router output")
        reviewed_at = review["reviewed_at"]
        if not isinstance(reviewed_at, str) or not reviewed_at.strip():
            raise RoutingExampleError(f"example[{index}] reviewed_at must be an ISO date")
        try:
            reviewed_date = date.fromisoformat(reviewed_at)
        except ValueError as error:
            raise RoutingExampleError(f"example[{index}] reviewed_at must be an ISO date") from error
        if reviewed_date.isoformat() != reviewed_at:
            raise RoutingExampleError(f"example[{index}] reviewed_at must use YYYY-MM-DD")
        seen_ids.add(item["id"])
        seen_queries.add(normalized_query)
    return examples


def _strict_string_list(value: Any, field: str) -> list[str]:
    if not isinstance(value, list) or any(not isinstance(item, str) or not item.strip() for item in value):
        raise RoutingExampleError(f"{field} must contain nonempty strings")
    if len(value) != len(set(value)):
        raise RoutingExampleError(f"{field} must not contain duplicates")
    return value
