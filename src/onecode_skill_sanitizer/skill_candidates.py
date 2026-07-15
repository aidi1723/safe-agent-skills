from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date
import json
import math
from pathlib import Path
import re
from typing import Any

from .intent import NormalizedTask
from .task_packs import extract_frontmatter_description


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


@dataclass(frozen=True)
class SkillCandidate:
    skill: str
    registry_path: str
    status: str
    description: str
    deterministic_score: float
    semantic_score: float | None
    final_score: float
    matched_intents: tuple[str, ...]
    matched_capabilities: tuple[str, ...]
    matched_examples: tuple[str, ...]
    positive_evidence: tuple[dict[str, Any], ...]
    penalties: tuple[dict[str, Any], ...]
    exclusions: tuple[str, ...]
    excluded: bool
    selected: bool
    reason_codes: tuple[str, ...]

    def to_json(self) -> dict[str, Any]:
        return asdict(self)


def load_cohort_profiles(registry_dir: Path) -> dict[str, dict[str, Any]]:
    index = json.loads((registry_dir / "index.json").read_text(encoding="utf-8"))
    indexed = {item["name"]: item for item in index["skills"] if isinstance(item, dict)}
    profiles: dict[str, dict[str, Any]] = {}
    for name in HIGH_FREQUENCY_SKILL_NAMES:
        item = indexed.get(name)
        if not isinstance(item, dict) or item.get("status") != "trusted":
            raise RoutingExampleError(f"cohort skill is not trusted: {name}")
        skill_dir = registry_dir / item["registry_path"]
        manifest = json.loads((skill_dir / "skill.json").read_text(encoding="utf-8"))
        skill_text = (skill_dir / "SKILL.md").read_text(encoding="utf-8")
        contract = manifest.get("contract") if isinstance(manifest.get("contract"), dict) else {}
        profiles[name] = {
            "name": name,
            "status": "trusted",
            "registry_path": item["registry_path"],
            "description": extract_frontmatter_description(skill_text),
            "task_intent": manifest["taxonomy"]["task_intent"],
            "subcategory": manifest["taxonomy"]["subcategory"],
            "capabilities": list(contract.get("capability_vector", [])),
            "requires_context": list(contract.get("requires_context", [])),
            "produces_artifacts": list(contract.get("produces_artifacts", [])),
            "produces_evidence": list(contract.get("produces_evidence", [])),
            "requires_after": list(contract.get("requires_after", [])),
            "conflicts_with": list(contract.get("conflicts_with", [])),
            "excludes": list(contract.get("excludes", [])),
        }
    return profiles


def retrieve_skill_candidates(
    normalized: NormalizedTask,
    need: dict[str, Any],
    profiles: dict[str, dict[str, Any]],
    examples: list[dict[str, Any]],
    *,
    top_k: int = 3,
) -> list[dict[str, Any]]:
    if isinstance(top_k, bool) or not isinstance(top_k, int) or not 1 <= top_k <= 7:
        raise ValueError("top_k must be an integer from 1 to 7")
    query_tokens = _tokens(normalized.current)
    records: list[dict[str, Any]] = []
    for name in HIGH_FREQUENCY_SKILL_NAMES:
        profile = profiles[name]
        matched_capabilities = sorted(set(profile["capabilities"]) & set(need["required_capabilities"]))
        explicit = name in need["explicit_skills"]
        excluded = name in need["excluded_skills"]
        description_tokens = _tokens(f"{profile['description']} {profile['task_intent']}")
        description_similarity = _jaccard(query_tokens, description_tokens)
        positive_examples = _matching_examples(query_tokens, examples, name, "required_skills")
        negative_examples = _matching_examples(query_tokens, examples, name, "forbidden_skills")
        positive_similarity = max((score for score, _ in positive_examples), default=0.0)
        negative_similarity = max((score for score, _ in negative_examples), default=0.0)
        evidence = []
        if matched_capabilities:
            evidence.append({"type": "capability", "value": matched_capabilities, "weight": 0.55})
        if explicit:
            evidence.append({"type": "explicit_skill", "value": name, "weight": 1.0})
        if description_similarity:
            evidence.append({"type": "description", "value": round(description_similarity, 6), "weight": 0.15})
        if positive_similarity:
            evidence.append({"type": "reviewed_example", "value": positive_examples[0][1], "weight": 0.30})
        penalties = []
        if negative_similarity:
            penalties.append({"type": "near_miss", "value": negative_examples[0][1], "weight": -0.65})
        score = 1.0 if explicit else min(
            1.0,
            0.55 * bool(matched_capabilities) + 0.15 * description_similarity + 0.30 * positive_similarity,
        )
        score = max(0.0, score - 0.65 * negative_similarity)
        reasons = []
        exclusions = []
        if excluded:
            score = 0.0
            exclusions.append("explicit_exclusion")
            reasons.append("explicit_exclusion")
        if not math.isfinite(score):
            raise ValueError("deterministic score must be finite")
        records.append(
            SkillCandidate(
                skill=name,
                registry_path=profile["registry_path"],
                status="trusted",
                description=profile["description"],
                deterministic_score=round(score, 6),
                semantic_score=None,
                final_score=round(score, 6),
                matched_intents=tuple(need["required_capabilities"]),
                matched_capabilities=tuple(matched_capabilities),
                matched_examples=tuple(item[1] for item in positive_examples[:3]),
                positive_evidence=tuple(evidence),
                penalties=tuple(penalties),
                exclusions=tuple(exclusions),
                excluded=excluded,
                selected=False,
                reason_codes=tuple(reasons or (["deterministic_candidate"] if score > 0 else ["no_positive_evidence"])),
            ).to_json()
        )
    records.sort(key=lambda item: (-item["deterministic_score"], item["skill"]))
    admitted_names = {item["skill"] for item in records[:top_k]}
    admitted_names.update(
        item["skill"]
        for item in records
        if item["matched_capabilities"]
        or item["skill"] in need["explicit_skills"]
        or item["skill"] in need["excluded_skills"]
    )
    admitted = [item for item in records if item["skill"] in admitted_names]
    return admitted


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


def _tokens(text: str) -> set[str]:
    latin = re.findall(r"[a-z0-9][a-z0-9_-]+", text.casefold())
    han = re.findall(r"[\u4e00-\u9fff]{2,}", text)
    han_bigrams = [token[index:index + 2] for token in han for index in range(len(token) - 1)]
    return set(latin + han_bigrams)


def _jaccard(left: set[str], right: set[str]) -> float:
    return len(left & right) / len(left | right) if left or right else 0.0


def _matching_examples(
    query_tokens: set[str],
    examples: list[dict[str, Any]],
    skill: str,
    label: str,
) -> list[tuple[float, str]]:
    matches = [(_jaccard(query_tokens, _tokens(item["query"])), item["id"]) for item in examples if skill in item[label]]
    return sorted((item for item in matches if item[0] > 0), key=lambda item: (-item[0], item[1]))
