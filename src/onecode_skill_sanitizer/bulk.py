from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def load_optional_skill_json(source_dir: Path) -> dict:
    manifest_path = source_dir / "skill.json"
    if not manifest_path.exists():
        return {}
    try:
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    return payload if isinstance(payload, dict) else {}


def load_registry_index(registry_dir: Path) -> dict:
    from .cli import load_registry_index as load_cli_registry_index

    return load_cli_registry_index(registry_dir)


def claude_skills_candidate_action(candidate: dict) -> str:
    adoption = candidate.get("adoption", "reference_only")
    if adoption == "converted":
        return "already_converted"
    if adoption == "candidate":
        return "draft_local_sanitized_skill"
    if adoption == "reference_only":
        return "mine_reference_cluster_or_merge_existing"
    return "review_before_action"


def claude_skills_candidate_sort_key(candidate: dict) -> tuple[int, int, int, str]:
    adoption_rank = {"converted": 0, "candidate": 1, "reference_only": 2, "rejected": 3}
    priority_rank = {"P0": 0, "P1": 1, "P2": 2, "P3": 3}
    return (
        adoption_rank.get(str(candidate.get("adoption", "reference_only")), 9),
        -int(candidate.get("score", 0) or 0),
        priority_rank.get(str(candidate.get("priority", "P3")), 9),
        str(candidate.get("name", "")),
    )


def compact_claude_skills_candidate(candidate: dict) -> dict:
    item = {
        "name": candidate.get("name", ""),
        "adoption": candidate.get("adoption", "reference_only"),
        "priority": candidate.get("priority", ""),
        "score": candidate.get("score", 0),
        "mapped_category": candidate.get("mapped_category", ""),
        "source_domain": candidate.get("source_domain", ""),
        "source_path": candidate.get("source_path", ""),
        "recommended_action": claude_skills_candidate_action(candidate),
    }
    if candidate.get("local_skill"):
        item["local_skill"] = candidate["local_skill"]
    return item


def most_common(values: list[str]) -> str:
    counts: dict[str, int] = {}
    for value in values:
        if not value:
            continue
        counts[value] = counts.get(value, 0) + 1
    if not counts:
        return ""
    return sorted(counts.items(), key=lambda item: (-item[1], item[0]))[0][0]


def build_claude_skills_bulk_plan(candidate_map_path: Path, batch_size: int) -> dict:
    if batch_size <= 0:
        raise SystemExit("batch-size must be greater than 0")
    candidate_map = json.loads(candidate_map_path.read_text(encoding="utf-8"))
    candidates = candidate_map.get("candidates", [])
    if not isinstance(candidates, list):
        raise SystemExit(f"invalid candidate map: {candidate_map_path}")

    adoption_counts: dict[str, int] = {}
    for candidate in candidates:
        adoption = str(candidate.get("adoption", "reference_only"))
        adoption_counts[adoption] = adoption_counts.get(adoption, 0) + 1
    adoption_counts = dict(sorted(adoption_counts.items()))

    actionable = [
        candidate
        for candidate in candidates
        if candidate.get("adoption") != "converted"
    ]
    actionable.sort(key=claude_skills_candidate_sort_key)

    batches = []
    for index in range(0, len(actionable), batch_size):
        batch_candidates = actionable[index : index + batch_size]
        items = [compact_claude_skills_candidate(candidate) for candidate in batch_candidates]
        batches.append(
            {
                "id": f"claude-skills-bulk-{len(batches) + 1:03d}",
                "item_count": len(items),
                "dominant_category": most_common([item["mapped_category"] for item in items]),
                "dominant_source_domain": most_common([item["source_domain"] for item in items]),
                "items": items,
            }
        )

    return {
        "schema_version": 1,
        "generated_at": utc_now(),
        "mode": "metadata_only_bulk_review",
        "source": candidate_map.get("source", ""),
        "candidate_count": len(candidates),
        "declared_candidate_count": candidate_map.get("candidate_count"),
        "converted_count": adoption_counts.get("converted", 0),
        "actionable_count": len(actionable),
        "adoption_counts": adoption_counts,
        "batch_size": batch_size,
        "batch_count": len(batches),
        "safety_boundary": "Do not copy, install, execute, or trust upstream skill bodies. Use metadata-only planning, local authoring, sanitization, serial approval, and verification.",
        "recommended_next_action": "Generate local sanitized batch drafts from the highest-priority batch, then import, approve serially, and verify.",
        "batches": batches,
    }


def claude_skills_bulk_plan_command(args: argparse.Namespace) -> int:
    result = build_claude_skills_bulk_plan(Path(args.candidate_map), args.batch_size)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


def slugify_skill_part(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "skill"


def humanize_candidate_name(value: str) -> str:
    return " ".join(part for part in re.split(r"[-_\s]+", value.strip()) if part) or "skill"


def local_draft_skill_name(candidate: dict) -> str:
    category = slugify_skill_part(str(candidate.get("mapped_category") or "general"))
    name = slugify_skill_part(str(candidate.get("name") or "skill"))
    if name.startswith(f"{category}-"):
        return f"{name}-review"
    return f"{category}-{name}-review"


def build_claude_skills_draft_skill_text(candidate: dict, skill_name: str) -> str:
    label = humanize_candidate_name(str(candidate.get("name", skill_name)))
    category = str(candidate.get("mapped_category") or "general")
    source_domain = str(candidate.get("source_domain") or "unknown")
    return f"""---
name: {skill_name}
description: Use when reviewing {label} workflows, metadata-only skill candidates, upstream reference clusters, or local adoption drafts before catalog inclusion.
---

# {label.title()} Review

## When To Use

Use this draft when reviewing the `{candidate.get("name", "")}` metadata-only
candidate from `claude-skills` before deciding whether to author a local
OneCode skill, merge it into an existing skill, or keep it reference-only.

## Safe Workflow

1. Identify the task, audience, owner, source domain, target catalog category,
   and expected artifact.
2. Compare the candidate with existing trusted Safe-Agent-Skills to avoid
   duplicate or overlapping guidance.
3. Draft local OneCode guidance from project requirements and operator review;
   do not copy upstream skill bodies.
4. Check provenance, license notes, runtime permissions, and connector
   assumptions before import.
5. Produce an adoption recommendation only; Do not execute upstream content or
   mark this draft trusted.

## Expected Output

- metadata-only candidate summary
- overlap and merge recommendation
- local authoring notes
- required verifier checklist
- adoption decision: convert, merge, keep reference-only, or reject

## Verifier Expectations

- metadata-only boundary check
- duplicate skill check
- provenance and license check
- import, serial approval, schema-check, maintain-check, and verify before trust

## Draft Metadata

- upstream candidate: `{candidate.get("name", "")}`
- source domain: `{source_domain}`
- source path: `{candidate.get("source_path", "")}`
- mapped category: `{category}`
- score: `{candidate.get("score", 0)}`
- priority: `{candidate.get("priority", "")}`
- adoption before draft: `{candidate.get("adoption", "reference_only")}`
"""


def build_claude_skills_draft_manifest(candidate: dict, skill_name: str, candidate_map_source: str) -> dict:
    category = str(candidate.get("mapped_category") or "general")
    return {
        "schema_version": 1,
        "name": skill_name,
        "version": "0.1.0",
        "status": "draft",
        "taxonomy": {
            "category": category,
            "subcategory": f"{slugify_skill_part(category)}.{slugify_skill_part(str(candidate.get('name') or 'skill')).replace('-', '_')}",
            "artifact_type": "review",
            "task_intent": f"review {humanize_candidate_name(str(candidate.get('name', skill_name)))} metadata-only candidate before local skill adoption",
            "collection_priority": str(candidate.get("priority") or "P3"),
        },
        "source": {
            "type": "local_folder",
            "usage": "local_authoring",
            "path": "",
            "url": "https://github.com/aidi1723/safe-agent-skills",
            "author": "OneCode Project",
            "license": "Apache-2.0",
            "reference": f"{candidate_map_source}; metadata-only claude-skills candidate {candidate.get('name', '')}",
            "collected_by": "onecode-claude-skills-bulk-draft",
        },
        "draft": {
            "upstream_source": "https://github.com/alirezarezvani/claude-skills",
            "upstream_candidate": candidate.get("name", ""),
            "source_domain": candidate.get("source_domain", ""),
            "source_path": candidate.get("source_path", ""),
            "score": candidate.get("score", 0),
            "adoption": candidate.get("adoption", "reference_only"),
            "metadata_only": True,
        },
    }


def build_claude_skills_bulk_drafts(
    candidate_map_path: Path,
    out_dir: Path,
    batch_size: int,
    batch_index: int,
    write_json_file,
) -> dict:
    if batch_index <= 0:
        raise SystemExit("batch-index must be greater than 0")
    plan = build_claude_skills_bulk_plan(candidate_map_path, batch_size)
    batches = plan["batches"]
    if batch_index > len(batches):
        raise SystemExit(f"batch-index out of range: {batch_index}")

    batch = batches[batch_index - 1]
    out_dir.mkdir(parents=True, exist_ok=True)
    draft_names = []
    for item in batch["items"]:
        skill_name = local_draft_skill_name(item)
        draft_names.append(skill_name)
        skill_dir = out_dir / skill_name
        skill_dir.mkdir(parents=True, exist_ok=True)
        (skill_dir / "SKILL.md").write_text(
            build_claude_skills_draft_skill_text(item, skill_name),
            encoding="utf-8",
        )
        write_json_file(
            skill_dir / "skill.json",
            build_claude_skills_draft_manifest(item, skill_name, candidate_map_path.as_posix()),
        )

    return {
        "schema_version": 1,
        "generated_at": utc_now(),
        "mode": "metadata_only_local_draft",
        "batch_id": batch["id"],
        "batch_index": batch_index,
        "batch_size": batch_size,
        "draft_count": len(draft_names),
        "out": out_dir.as_posix(),
        "draft_names": draft_names,
        "safety_boundary": plan["safety_boundary"],
        "next_steps": [
            "Drafts are not trusted and are not in the catalog.",
            "Review and edit local guidance before import.",
            "Run import, approve serially, schema-check, maintain-check, and verify before trust.",
        ],
    }


def claude_skills_bulk_draft_command(args: argparse.Namespace) -> int:
    result = build_claude_skills_bulk_drafts(
        candidate_map_path=Path(args.candidate_map),
        out_dir=Path(args.out),
        batch_size=args.batch_size,
        batch_index=args.batch_index,
        write_json_file=write_json,
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


STOPWORD_SKILL_TOKENS = {
    "advisor",
    "builder",
    "candidate",
    "candidates",
    "expert",
    "manager",
    "review",
    "skill",
    "skills",
    "toolkit",
    "workflow",
    "workflows",
}


def skill_name_tokens(value: str) -> set[str]:
    return {
        part
        for part in re.split(r"[^a-z0-9]+", value.lower())
        if len(part) > 2 and part not in STOPWORD_SKILL_TOKENS
    }


def load_draft_skill_names(draft_root: Path) -> set[str]:
    names: set[str] = set()
    if not draft_root.exists():
        return names
    for manifest_path in sorted(draft_root.glob("**/skill.json")):
        manifest = load_optional_skill_json(manifest_path.parent)
        if manifest.get("status") != "draft":
            continue
        name = manifest.get("name") or manifest_path.parent.name
        if isinstance(name, str) and name:
            names.add(name)
    return names


def trusted_registry_skill_names(registry_dir: Path) -> list[str]:
    if not registry_dir.exists():
        return []
    index = load_registry_index(registry_dir)
    return [
        str(entry.get("name", ""))
        for entry in index.get("skills", [])
        if entry.get("status") == "trusted" and entry.get("name")
    ]


def registry_skill_statuses(registry_dir: Path) -> dict[str, str]:
    if not registry_dir.exists():
        return {}
    index = load_registry_index(registry_dir)
    return {
        str(entry.get("name", "")): str(entry.get("status", ""))
        for entry in index.get("skills", [])
        if entry.get("name")
    }


def find_claude_skills_overlap(candidate: dict, trusted_names: list[str]) -> str:
    candidate_name = str(candidate.get("name", ""))
    candidate_slug = slugify_skill_part(candidate_name)
    candidate_tokens = skill_name_tokens(candidate_name)
    for trusted_name in trusted_names:
        trusted_slug = slugify_skill_part(trusted_name)
        trusted_tokens = skill_name_tokens(trusted_name)
        if candidate_slug and candidate_slug in trusted_slug:
            return trusted_name
        if len(candidate_tokens & trusted_tokens) >= 2:
            return trusted_name
    return ""


def assess_claude_skills_candidate(
    candidate: dict,
    draft_names: set[str],
    trusted_names: list[str],
    skill_statuses: dict[str, str],
) -> dict:
    name = str(candidate.get("name", ""))
    draft_name = local_draft_skill_name(candidate)
    adoption = str(candidate.get("adoption", "reference_only"))
    score = int(candidate.get("score", 0) or 0)
    priority = str(candidate.get("priority", "P3"))
    item = {
        "candidate": name,
        "draft_name": draft_name,
        "draft_present": draft_name in draft_names,
        "priority": priority,
        "score": score,
        "mapped_category": candidate.get("mapped_category", ""),
        "source_domain": candidate.get("source_domain", ""),
        "source_path": candidate.get("source_path", ""),
    }
    if adoption == "converted":
        local_skill = candidate.get("local_skill", "")
        if not isinstance(local_skill, str) or not local_skill:
            item.update(
                {
                    "recommendation": "invalid_converted_mapping",
                    "next_gate": "candidate-map-fix",
                    "reason": "converted candidate is missing a local_skill mapping",
                    "mapping_status": "missing_local_skill",
                    "local_skill": "",
                }
            )
            return item
        local_skill_status = skill_statuses.get(local_skill)
        if local_skill_status is None:
            item.update(
                {
                    "recommendation": "invalid_converted_mapping",
                    "next_gate": "candidate-map-fix",
                    "reason": "converted candidate points to a local skill that is missing from the registry",
                    "mapping_status": "missing_registry_skill",
                    "local_skill": local_skill,
                }
            )
            return item
        if local_skill_status != "trusted":
            item.update(
                {
                    "recommendation": "invalid_converted_mapping",
                    "next_gate": "candidate-map-fix",
                    "reason": "converted candidate points to a local skill that is not trusted",
                    "mapping_status": "non_trusted_local_skill",
                    "local_skill": local_skill,
                    "local_skill_status": local_skill_status,
                }
            )
            return item
        item.update(
            {
                "recommendation": "already_converted",
                "next_gate": "none",
                "reason": "candidate map records a converted trusted local skill",
                "mapping_status": "trusted_local_skill",
                "local_skill": local_skill,
                "local_skill_status": local_skill_status,
            }
        )
        return item
    if not item["draft_present"]:
        item.update(
            {
                "recommendation": "missing_draft",
                "next_gate": "draft-generation",
                "reason": "candidate has no matching local metadata-only draft folder",
            }
        )
        return item

    overlap_skill = find_claude_skills_overlap(candidate, trusted_names)
    if overlap_skill:
        item.update(
            {
                "recommendation": "merge_existing",
                "next_gate": "overlap-merge-review",
                "reason": "candidate overlaps an existing trusted catalog skill",
                "overlap_skill": overlap_skill,
            }
        )
        return item

    if priority in {"P0", "P1"} or score >= 75:
        item.update(
            {
                "recommendation": "author_local_skill",
                "next_gate": "local-authoring-review",
                "reason": "high-priority or high-score candidate with no trusted overlap",
            }
        )
        return item

    item.update(
        {
            "recommendation": "keep_reference_only",
            "next_gate": "defer-or-cluster-review",
            "reason": "lower-priority metadata-only candidate should remain reference-only until a concrete local need appears",
        }
    )
    return item


def build_claude_skills_bulk_assessment(candidate_map_path: Path, draft_root: Path, registry_dir: Path) -> dict:
    candidate_map = json.loads(candidate_map_path.read_text(encoding="utf-8"))
    candidates = candidate_map.get("candidates", [])
    if not isinstance(candidates, list):
        raise SystemExit(f"invalid candidate map: {candidate_map_path}")

    draft_names = load_draft_skill_names(draft_root)
    trusted_names = trusted_registry_skill_names(registry_dir)
    skill_statuses = registry_skill_statuses(registry_dir)
    items = [
        assess_claude_skills_candidate(candidate, draft_names, trusted_names, skill_statuses)
        for candidate in sorted(candidates, key=claude_skills_candidate_sort_key)
    ]
    recommendation_counts: dict[str, int] = {}
    for item in items:
        recommendation = str(item["recommendation"])
        recommendation_counts[recommendation] = recommendation_counts.get(recommendation, 0) + 1

    return {
        "schema_version": 1,
        "generated_at": utc_now(),
        "mode": "metadata_only_bulk_assessment",
        "source": candidate_map.get("source", ""),
        "candidate_count": len(candidates),
        "draft_root": draft_root.as_posix(),
        "draft_count": len(draft_names),
        "trusted_skill_count": len(trusted_names),
        "recommendation_counts": dict(sorted(recommendation_counts.items())),
        "safety_boundary": "This command reviews metadata-only drafts only; it does not approve or trust drafts, execute upstream content, or bypass import, serial approval, schema-check, maintain-check, and verify.",
        "items": items,
    }


def claude_skills_bulk_assess_command(args: argparse.Namespace) -> int:
    result = build_claude_skills_bulk_assessment(
        Path(args.candidate_map),
        Path(args.draft_root),
        Path(args.registry),
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0
