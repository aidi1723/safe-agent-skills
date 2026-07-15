from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date
import json
import math
from pathlib import Path
from pathlib import PurePosixPath
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
_HIGH_FREQUENCY_CAPABILITIES = frozenset(
    {
        "code.explore",
        "code.review",
        "code.test",
        "execution.browser_check",
        "research.source",
        "design.ui_review",
        "security.supply_chain",
    }
)
EXAMPLE_CLASSES = {"positive", "near_miss", "negation", "explanation_only", "composition"}
NEED_DECISIONS = {"none", "single", "composite", "clarify"}
EXAMPLE_KEYS = {
    "id", "query", "expected_need", "required_skills", "forbidden_skills",
    "intent_labels", "capability_labels", "example_class", "review",
}
_REVIEW_KEYS = {
    "status", "reviewed_at", "reviewer_role", "source_classification", "generated_from_router",
}
_PROFILE_LIST_FIELDS = (
    "requires_context",
    "produces_artifacts",
    "produces_evidence",
    "requires_after",
    "conflicts_with",
    "excludes",
)


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
    registry_root = _resolved_registry_root(registry_dir)
    index_path = _confined_source_path(
        registry_root,
        registry_root / "index.json",
        "catalog index path",
    )
    index = _read_json(index_path, "catalog index")
    indexed = _cohort_index_entries(index)
    profiles: dict[str, dict[str, Any]] = {}
    for name in HIGH_FREQUENCY_SKILL_NAMES:
        item = indexed[name]
        if item.get("status") != "trusted":
            raise RoutingExampleError(f"cohort {name} index status must be trusted")
        registry_path = _normalized_registry_path(item.get("registry_path"), name)
        skill_dir = _confined_source_path(
            registry_root,
            registry_root.joinpath(*registry_path.parts),
            f"cohort {name} registry_path",
        )
        if not skill_dir.is_dir():
            raise RoutingExampleError(f"cohort {name} registry_path must resolve to a directory")
        manifest_path = _confined_source_path(
            registry_root,
            skill_dir / "skill.json",
            f"cohort {name} manifest source path",
        )
        skill_path = _confined_source_path(
            registry_root,
            skill_dir / "SKILL.md",
            f"cohort {name} SKILL.md source path",
        )
        manifest = _validated_profile_manifest(_read_json(manifest_path, f"cohort {name} manifest"), name)
        skill_text = _read_text(skill_path, f"cohort {name} SKILL.md")
        frontmatter_name, description = _profile_frontmatter(skill_text, name)
        if frontmatter_name != name:
            raise RoutingExampleError(f"cohort {name} frontmatter name must match the cohort name")
        contract = manifest["contract"]
        taxonomy = manifest["taxonomy"]
        profiles[name] = {
            "name": name,
            "status": "trusted",
            "registry_path": registry_path.as_posix(),
            "description": description,
            "task_intent": taxonomy["task_intent"],
            "subcategory": taxonomy["subcategory"],
            "capabilities": contract["capability_vector"],
            **{field: contract.get(field, []) for field in _PROFILE_LIST_FIELDS},
        }
    return profiles


def _resolved_registry_root(registry_dir: Path) -> Path:
    try:
        root = registry_dir.resolve()
    except (OSError, RuntimeError) as error:
        raise RoutingExampleError("catalog registry root cannot be resolved") from error
    if not root.is_dir():
        raise RoutingExampleError("catalog registry root must be a directory")
    return root


def _confined_source_path(root: Path, path: Path, context: str) -> Path:
    try:
        resolved = path.resolve()
        resolved.relative_to(root)
    except (OSError, RuntimeError, ValueError) as error:
        raise RoutingExampleError(f"{context} must remain inside the catalog registry root") from error
    return resolved


def _read_text(path: Path, context: str) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as error:
        raise RoutingExampleError(f"{context} cannot be read as UTF-8") from error


def _read_json(path: Path, context: str) -> Any:
    try:
        return json.loads(_read_text(path, context))
    except json.JSONDecodeError as error:
        raise RoutingExampleError(f"{context} must contain valid JSON") from error


def _cohort_index_entries(index: Any) -> dict[str, dict[str, Any]]:
    if not isinstance(index, dict):
        raise RoutingExampleError("catalog index must be an object")
    skills = index.get("skills")
    if not isinstance(skills, list):
        raise RoutingExampleError("catalog index skills must be a list")
    indexed: dict[str, dict[str, Any]] = {}
    for position, item in enumerate(skills):
        if not isinstance(item, dict):
            raise RoutingExampleError(f"catalog index skill[{position}] must be an object")
        name = item.get("name")
        if not isinstance(name, str) or not name.strip():
            raise RoutingExampleError(f"catalog index skill[{position}] name must be a nonempty string")
        if name in indexed:
            raise RoutingExampleError(f"catalog index contains duplicate cohort name: {name}")
        indexed[name] = item
    missing = [name for name in HIGH_FREQUENCY_SKILL_NAMES if name not in indexed]
    if missing:
        raise RoutingExampleError(f"catalog index is missing cohort skill: {missing[0]}")
    return {name: indexed[name] for name in HIGH_FREQUENCY_SKILL_NAMES}


def _normalized_registry_path(
    value: Any,
    name: str,
    *,
    context: str | None = None,
) -> PurePosixPath:
    field = f"{context or f'cohort {name}'} registry_path"
    if (
        not isinstance(value, str)
        or not value
        or value != value.strip()
        or "\\" in value
    ):
        raise RoutingExampleError(f"{field} must be a normalized relative POSIX path")
    path = PurePosixPath(value)
    if (
        path.is_absolute()
        or path.as_posix() != value
        or any(part in {"", ".", ".."} for part in path.parts)
        or path.name != name
    ):
        raise RoutingExampleError(
            f"{field} must be a normalized relative POSIX path ending in {name}"
        )
    return path


def _validated_profile_manifest(manifest: Any, name: str) -> dict[str, Any]:
    if not isinstance(manifest, dict):
        raise RoutingExampleError(f"cohort {name} manifest must be an object")
    if manifest.get("name") != name:
        raise RoutingExampleError(f"cohort {name} manifest name must match the cohort name")
    if manifest.get("status") != "trusted":
        raise RoutingExampleError(f"cohort {name} manifest status must be trusted")
    taxonomy = manifest.get("taxonomy")
    if not isinstance(taxonomy, dict):
        raise RoutingExampleError(f"cohort {name} manifest taxonomy must be an object")
    for field in ("task_intent", "subcategory"):
        value = taxonomy.get(field)
        if not isinstance(value, str) or not value.strip():
            raise RoutingExampleError(
                f"cohort {name} manifest taxonomy.{field} must be a nonempty string"
            )
    contract = manifest.get("contract")
    if not isinstance(contract, dict):
        raise RoutingExampleError(f"cohort {name} manifest contract must be an object")
    schema_version = contract.get("schema_version")
    if (
        isinstance(schema_version, bool)
        or not isinstance(schema_version, int)
        or schema_version != 2
    ):
        raise RoutingExampleError(
            f"cohort {name} manifest contract.schema_version must be the integer 2"
        )
    capabilities = _strict_string_list(
        contract.get("capability_vector"),
        f"cohort {name} manifest contract.capability_vector",
    )
    if not capabilities:
        raise RoutingExampleError(
            f"cohort {name} manifest contract.capability_vector must not be empty"
        )
    for field in _PROFILE_LIST_FIELDS:
        if field in contract:
            _strict_string_list(contract[field], f"cohort {name} manifest contract.{field}")
    return manifest


def _profile_frontmatter(skill_text: str, name: str) -> tuple[str, str]:
    frontmatter_match = re.match(r"^---\r?\n(?P<body>.*?)\r?\n---(?:\r?\n|$)", skill_text, re.DOTALL)
    if not frontmatter_match:
        raise RoutingExampleError(f"cohort {name} SKILL.md frontmatter is missing")
    frontmatter = frontmatter_match.group("body")
    names = re.findall(r"^name:\s*(.*?)\s*$", frontmatter, re.MULTILINE)
    if len(names) != 1 or not names[0]:
        raise RoutingExampleError(f"cohort {name} frontmatter name must be a nonempty string")
    description = extract_frontmatter_description(frontmatter)
    if not description:
        raise RoutingExampleError(f"cohort {name} frontmatter description must be a nonempty string")
    return names[0], description


def _validate_retrieval_profiles(profiles: Any) -> None:
    if not isinstance(profiles, dict) or set(profiles) != set(HIGH_FREQUENCY_SKILL_NAMES):
        raise RoutingExampleError("profiles must be an exact mapping of the fixed cohort")
    for name in HIGH_FREQUENCY_SKILL_NAMES:
        profile = profiles[name]
        context = f"profile {name}"
        if not isinstance(profile, dict):
            raise RoutingExampleError(f"{context} must be an object")
        if profile.get("name") != name:
            raise RoutingExampleError(f"{context} name must match its fixed cohort key")
        if profile.get("status") != "trusted":
            raise RoutingExampleError(f"{context} status must be trusted")
        _normalized_registry_path(profile.get("registry_path"), name, context=context)
        for field in ("description", "task_intent"):
            value = profile.get(field)
            if not isinstance(value, str) or not value.strip():
                raise RoutingExampleError(f"{context} {field} must be a nonempty string")
        capabilities = _strict_string_list(profile.get("capabilities"), f"{context} capabilities")
        if not capabilities:
            raise RoutingExampleError(f"{context} capabilities must not be empty")
        unknown = set(capabilities) - _HIGH_FREQUENCY_CAPABILITIES
        if unknown:
            raise RoutingExampleError(f"{context} capabilities contain an unknown capability")


def _validate_retrieval_need(need: Any) -> None:
    if not isinstance(need, dict):
        raise RoutingExampleError("need must be an object")
    capabilities = _strict_string_list(
        need.get("required_capabilities"),
        "need.required_capabilities",
    )
    explicit = _strict_string_list(need.get("explicit_skills"), "need.explicit_skills")
    excluded = _strict_string_list(need.get("excluded_skills"), "need.excluded_skills")
    if not set(capabilities).issubset(_HIGH_FREQUENCY_CAPABILITIES):
        raise RoutingExampleError("need.required_capabilities contains an unknown capability")
    if not set(explicit).issubset(HIGH_FREQUENCY_SKILL_NAMES):
        raise RoutingExampleError("need.explicit_skills contains an out-of-cohort skill")
    if not set(excluded).issubset(HIGH_FREQUENCY_SKILL_NAMES):
        raise RoutingExampleError("need.excluded_skills contains an out-of-cohort skill")


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
    current = getattr(normalized, "current", None)
    if not isinstance(current, str):
        raise RoutingExampleError("normalized.current must be a string")
    _validate_retrieval_profiles(profiles)
    _validate_retrieval_need(need)
    examples = _validate_routing_examples(examples)
    query_tokens = _tokens(current)
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
            evidence.append(
                {
                    "type": "reviewed_example",
                    "value": positive_examples[0][1],
                    "similarity": round(positive_similarity, 6),
                    "weight": 0.30,
                    "contribution": round(0.30 * positive_similarity, 6),
                }
            )
        penalties = []
        if negative_similarity:
            penalties.append(
                {
                    "type": "near_miss",
                    "value": negative_examples[0][1],
                    "similarity": round(negative_similarity, 6),
                    "weight": -0.65,
                    "contribution": round(-0.65 * negative_similarity, 6),
                }
            )
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
                matched_intents=tuple(matched_capabilities),
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
    records.sort(
        key=lambda item: (-item["deterministic_score"], item["excluded"], item["skill"])
    )
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
    return _validate_routing_examples(payload["examples"])


def _validate_routing_examples(examples: Any) -> list[dict[str, Any]]:
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
