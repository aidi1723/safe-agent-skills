from __future__ import annotations

from collections.abc import Mapping
from dataclasses import asdict, dataclass
from datetime import date
import json
import math
from pathlib import Path
from pathlib import PurePosixPath
import re
from types import MappingProxyType
from typing import Any

from .intent import NormalizedTask
from .validation import validate_contract


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
_COHORT_IDENTITY = MappingProxyType({
    "codebase-explore-map": MappingProxyType({
        "registry_path": "code/codebase-explore-map",
        "capability_vector": ("code.explore",),
        "subcategory": "code.explore",
    }),
    "code-review-risk": MappingProxyType({
        "registry_path": "code/code-review-risk",
        "capability_vector": ("code.review",),
        "subcategory": "code.review",
    }),
    "code-test-regression": MappingProxyType({
        "registry_path": "code/code-test-regression",
        "capability_vector": ("code.test",),
        "subcategory": "code.test",
    }),
    "execution-browser-check": MappingProxyType({
        "registry_path": "execution/execution-browser-check",
        "capability_vector": ("execution.browser_check",),
        "subcategory": "execution.browser",
    }),
    "research-source-check": MappingProxyType({
        "registry_path": "research/research-source-check",
        "capability_vector": ("research.source",),
        "subcategory": "research.source",
    }),
    "design-ui-review": MappingProxyType({
        "registry_path": "design/design-ui-review",
        "capability_vector": ("design.ui_review",),
        "subcategory": "design.review",
    }),
    "security-supply-chain-review": MappingProxyType({
        "registry_path": "security/security-supply-chain-review",
        "capability_vector": ("security.supply_chain",),
        "subcategory": "security.supply_chain",
    }),
})
_HIGH_FREQUENCY_CAPABILITIES = frozenset(
    identity["capability_vector"][0] for identity in _COHORT_IDENTITY.values()
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
_FRONTMATTER_NONSTRING_VALUES = {
    "null", "~", "true", "false", "yes", "no", "on", "off",
    ".nan", ".inf", "+.inf", "-.inf",
}
_FRONTMATTER_NUMBER_RE = re.compile(
    r"[-+]?(?:(?:\d[\d_]*)(?:\.[\d_]*)?|\.\d[\d_]*)(?:[eE][-+]?\d[\d_]*)?|"
    r"[-+]?0[xXoObB][0-9a-fA-F_]+"
)


class RoutingExampleError(ValueError):
    pass


_PROFILE_LOADER_SENTINEL = object()


class _VerifiedCohortProfiles(Mapping[str, Mapping[str, Any]]):
    __slots__ = ("__profiles", "__provenance", "__sealed")

    def __init__(self, profiles: Mapping[str, Mapping[str, Any]], provenance: object):
        if provenance is not _PROFILE_LOADER_SENTINEL:
            raise TypeError("verified cohort profiles can only be created by the cohort loader")
        frozen = {
            name: MappingProxyType(
                {field: _freeze_profile_value(value) for field, value in profile.items()}
            )
            for name, profile in profiles.items()
        }
        object.__setattr__(self, "_VerifiedCohortProfiles__profiles", MappingProxyType(frozen))
        object.__setattr__(self, "_VerifiedCohortProfiles__provenance", provenance)
        object.__setattr__(self, "_VerifiedCohortProfiles__sealed", True)

    def __setattr__(self, name: str, value: Any) -> None:
        if getattr(self, "_VerifiedCohortProfiles__sealed", False):
            raise TypeError("verified cohort profiles are immutable")
        object.__setattr__(self, name, value)

    def __getitem__(self, name: str) -> Mapping[str, Any]:
        return self.__profiles[name]

    def __iter__(self):
        return iter(self.__profiles)

    def __len__(self) -> int:
        return len(self.__profiles)

    def _is_loader_verified(self) -> bool:
        return self.__provenance is _PROFILE_LOADER_SENTINEL


def _freeze_profile_value(value: Any) -> Any:
    if isinstance(value, Mapping):
        return MappingProxyType(
            {key: _freeze_profile_value(item) for key, item in value.items()}
        )
    if isinstance(value, (list, tuple)):
        return tuple(_freeze_profile_value(item) for item in value)
    return value


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


@dataclass(frozen=True)
class _ExampleMatch:
    similarity: float
    example_id: str
    token_overlap: int
    token_union: int


def load_cohort_profiles(registry_dir: Path) -> Mapping[str, Mapping[str, Any]]:
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
        identity = _COHORT_IDENTITY[name]
        if item.get("status") != "trusted":
            raise RoutingExampleError(f"cohort {name} index status must be trusted")
        if item.get("registry_path") != identity["registry_path"]:
            raise RoutingExampleError(
                f"cohort {name} index must use canonical registry_path "
                f"{identity['registry_path']}"
            )
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
        manifest = _validated_profile_manifest(
            _read_json(manifest_path, f"cohort {name} manifest"),
            name,
            manifest_path,
        )
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
    return _VerifiedCohortProfiles(profiles, _PROFILE_LOADER_SENTINEL)


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


def _validated_profile_manifest(
    manifest: Any,
    name: str,
    manifest_path: Path,
) -> dict[str, Any]:
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
    identity = _COHORT_IDENTITY[name]
    if taxonomy["subcategory"] != identity["subcategory"]:
        raise RoutingExampleError(
            f"cohort {name} manifest must use fixed taxonomy subcategory "
            f"{identity['subcategory']}"
        )
    contract = manifest.get("contract")
    if not isinstance(contract, dict):
        raise RoutingExampleError(f"cohort {name} manifest contract must be an object")
    contract_issues: list[dict[str, Any]] = []
    validate_contract(
        {"name": name, "contract": contract},
        manifest_path,
        contract_issues,
    )
    if contract_issues:
        summary = str(contract_issues[0].get("summary", "invalid contract"))
        raise RoutingExampleError(
            f"cohort {name} manifest canonical contract validation failed: {summary}"
        )
    schema_version = contract.get("schema_version")
    if (
        isinstance(schema_version, bool)
        or not isinstance(schema_version, int)
        or schema_version != 2
    ):
        raise RoutingExampleError(
            f"cohort {name} manifest contract.schema_version must be the integer 2"
        )
    expected_capabilities = identity["capability_vector"]
    if tuple(contract.get("capability_vector", ())) != expected_capabilities:
        raise RoutingExampleError(
            f"cohort {name} manifest must use fixed capability vector {expected_capabilities}"
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
    values: dict[str, str] = {}
    for line_number, line in enumerate(frontmatter.splitlines(), start=1):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if line[0].isspace():
            raise RoutingExampleError(
                f"cohort {name} frontmatter line {line_number} must be a top-level string scalar"
            )
        field_match = re.fullmatch(r"([A-Za-z_][A-Za-z0-9_-]*):[ \t]*(.*)", line)
        if not field_match:
            raise RoutingExampleError(
                f"cohort {name} frontmatter line {line_number} must be a top-level string scalar"
            )
        field, raw_value = field_match.groups()
        if field in values:
            raise RoutingExampleError(
                f"cohort {name} frontmatter {field} must appear exactly once"
            )
        values[field] = _parse_frontmatter_string(raw_value, name, field)
    for field in ("name", "description"):
        if field not in values:
            raise RoutingExampleError(
                f"cohort {name} frontmatter {field} must appear exactly once"
            )
    return values["name"], values["description"]


def _parse_frontmatter_string(raw_value: str, name: str, field: str) -> str:
    value = raw_value.strip()
    error_message = f"cohort {name} frontmatter {field} must be a nonempty string scalar"
    if not value:
        raise RoutingExampleError(error_message)
    if value.startswith('"'):
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError as error:
            raise RoutingExampleError(error_message) from error
        if not isinstance(parsed, str) or not parsed.strip():
            raise RoutingExampleError(error_message)
        return parsed
    if value.startswith("'"):
        if len(value) < 2 or not value.endswith("'"):
            raise RoutingExampleError(error_message)
        inner = value[1:-1]
        if "'" in inner.replace("''", ""):
            raise RoutingExampleError(error_message)
        parsed = inner.replace("''", "'")
        if not parsed.strip():
            raise RoutingExampleError(error_message)
        return parsed
    if value.endswith(("'", '"')):
        raise RoutingExampleError(error_message)
    if (
        value.casefold() in _FRONTMATTER_NONSTRING_VALUES
        or value.startswith(("[", "{", "|", ">"))
        or _FRONTMATTER_NUMBER_RE.fullmatch(value)
    ):
        raise RoutingExampleError(error_message)
    return value


def _validate_retrieval_profiles(profiles: Any) -> None:
    if (
        type(profiles) is not _VerifiedCohortProfiles
        or not profiles._is_loader_verified()
    ):
        raise RoutingExampleError("profiles must come from the verified cohort loader")
    if set(profiles) != set(HIGH_FREQUENCY_SKILL_NAMES):
        raise RoutingExampleError("profiles must be an exact mapping of the fixed cohort")
    for name in HIGH_FREQUENCY_SKILL_NAMES:
        profile = profiles[name]
        context = f"profile {name}"
        if not isinstance(profile, Mapping):
            raise RoutingExampleError(f"{context} must be an object")
        if profile.get("name") != name:
            raise RoutingExampleError(f"{context} name must match its fixed cohort key")
        if profile.get("status") != "trusted":
            raise RoutingExampleError(f"{context} status must be trusted")
        identity = _COHORT_IDENTITY[name]
        if profile.get("registry_path") != identity["registry_path"]:
            raise RoutingExampleError(f"{context} registry_path must match fixed cohort identity")
        if profile.get("subcategory") != identity["subcategory"]:
            raise RoutingExampleError(f"{context} subcategory must match fixed cohort identity")
        for field in ("description", "task_intent"):
            value = profile.get(field)
            if not isinstance(value, str) or not value.strip():
                raise RoutingExampleError(f"{context} {field} must be a nonempty string")
        capabilities = profile.get("capabilities")
        if capabilities != _COHORT_IDENTITY[name]["capability_vector"]:
            raise RoutingExampleError(f"{context} capabilities must match fixed cohort identity")


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
    profiles: Mapping[str, Mapping[str, Any]],
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
        positive_match = positive_examples[0] if positive_examples else None
        negative_match = negative_examples[0] if negative_examples else None
        positive_similarity = positive_match.similarity if positive_match else 0.0
        negative_similarity = negative_match.similarity if negative_match else 0.0
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
                    "value": positive_match.example_id,
                    "similarity": round(positive_similarity, 6),
                    "token_overlap": positive_match.token_overlap,
                    "token_union": positive_match.token_union,
                    "weight": 0.30,
                    "contribution": round(0.30 * positive_similarity, 6),
                }
            )
        penalties = []
        if negative_similarity:
            penalties.append(
                {
                    "type": "near_miss",
                    "value": negative_match.example_id,
                    "similarity": round(negative_similarity, 6),
                    "token_overlap": negative_match.token_overlap,
                    "token_union": negative_match.token_union,
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
                matched_examples=tuple(item.example_id for item in positive_examples[:3]),
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
) -> list[_ExampleMatch]:
    matches: list[_ExampleMatch] = []
    for item in examples:
        if skill not in item[label]:
            continue
        example_tokens = _tokens(item["query"])
        token_overlap = len(query_tokens & example_tokens)
        token_union = len(query_tokens | example_tokens)
        similarity = token_overlap / token_union if token_union else 0.0
        if similarity > 0:
            matches.append(
                _ExampleMatch(
                    similarity=similarity,
                    example_id=item["id"],
                    token_overlap=token_overlap,
                    token_union=token_union,
                )
            )
    return sorted(matches, key=lambda item: (-item.similarity, item.example_id))
