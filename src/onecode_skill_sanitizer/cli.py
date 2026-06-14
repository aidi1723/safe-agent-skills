from __future__ import annotations

import argparse
import hashlib
import json
import re
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from .router import route_mesh_task, route_scenario_task
from .scanner import highest_risk, line_findings, read_text_files, scan_text, source_hash
from .taxonomy import classify_skill, taxonomy_from_manifest


STATUS_VALUES = {"quarantined", "review_required", "trusted", "rejected", "disabled"}
RISK_LEVEL_VALUES = {"low", "medium", "high", "critical"}
SOURCE_TYPE_VALUES = {"local_folder", "archive", "git", "community_index", "github_reference", "web_reference"}
SOURCE_USAGE_VALUES = {"source_import", "reference_only", "local_authoring"}
SOURCE_DEFAULT_USAGE_BY_TYPE = {
    "archive": "source_import",
    "community_index": "source_import",
    "git": "source_import",
    "github_reference": "reference_only",
    "local_folder": "local_authoring",
    "web_reference": "reference_only",
}
SOURCE_USAGE_BY_TYPE = {
    "archive": {"source_import"},
    "community_index": {"source_import"},
    "git": {"source_import"},
    "github_reference": {"reference_only"},
    "local_folder": {"local_authoring"},
    "web_reference": {"reference_only"},
}
SOURCE_REQUIRED_FIELDS = ["type", "usage", "path", "url", "author", "license", "reference", "collected_by", "captured_at"]
SOURCE_PROVENANCE_FIELDS = ["url", "author", "license", "reference", "collected_by"]
HASH_PATTERN = re.compile(r"^[0-9a-f]{64}$")
REFERENCE_REQUIRED_FIELDS = [
    "name",
    "source_url",
    "source_type",
    "author",
    "license",
    "captured_at",
    "project_category",
    "claimed_capabilities",
    "taxonomy_categories",
    "runtime_permission_notes",
    "adoption_status",
    "review_notes",
    "metadata_only",
]
REFERENCE_ADOPTION_STATUSES = {"reference_only", "candidate", "rejected", "converted"}


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def text_sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def load_optional_skill_json(source_dir: Path) -> dict:
    manifest_path = source_dir / "skill.json"
    if not manifest_path.exists():
        return {}
    try:
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    return payload if isinstance(payload, dict) else {}


def build_source_record(source_dir: Path, args: argparse.Namespace | None = None) -> dict:
    payload = load_optional_skill_json(source_dir)
    manifest_source = payload.get("source")
    if not isinstance(manifest_source, dict):
        manifest_source = {}

    def value(key: str, arg_name: str | None = None) -> str:
        if args is not None and arg_name is not None:
            arg_value = getattr(args, arg_name, None)
            if arg_value:
                return str(arg_value)
        manifest_value = manifest_source.get(key)
        if manifest_value:
            return str(manifest_value)
        return "unknown"

    source_type = str(manifest_source.get("type", "local_folder"))
    source_usage = value("usage", "source_usage")
    if source_usage == "unknown":
        source_usage = SOURCE_DEFAULT_USAGE_BY_TYPE.get(source_type, "local_authoring")

    return {
        "type": source_type,
        "usage": source_usage,
        "path": str(source_dir),
        "url": value("url", "source_url"),
        "author": value("author", "author"),
        "license": value("license", "license"),
        "reference": value("reference", "reference"),
        "collected_by": value("collected_by", "collected_by"),
        "captured_at": utc_now(),
    }


def build_scan_report(source_dir: Path, args: argparse.Namespace | None = None) -> dict:
    files = read_text_files(source_dir)
    combined_text = "\n".join(text for _, text in files)
    findings = scan_text(combined_text)
    risk_level = highest_risk(findings)
    taxonomy = taxonomy_from_manifest(source_dir) or classify_skill(source_dir.name, combined_text)
    status = "review_required" if findings or not taxonomy.classified else "quarantined"

    return {
        "schema_version": 1,
        "skill_name": source_dir.name,
        "taxonomy": taxonomy.to_json(),
        "source": build_source_record(source_dir, args),
        "files": [relative_path for relative_path, _ in files],
        "hashes": {
            "source_sha256": source_hash(files),
            "sanitized_sha256": None,
        },
        "summary": {
            "status": status,
            "risk_level": risk_level,
            "preserved_sections": [],
            "removed_fragment_count": 0,
            "rewritten_fragment_count": 0,
            "unresolved_finding_count": len(findings),
        },
        "findings": [finding.to_json() for finding in findings],
        "required_verifiers": [],
        "recommendation": "Keep quarantined until sanitization and verifier binding are complete.",
}


def sanitize_skill_text(text: str) -> tuple[str, list[dict[str, str]]]:
    kept_lines = []
    removed = []
    for line_number, line in enumerate(text.splitlines(), start=1):
        findings = line_findings(line)
        if findings:
            for finding in findings:
                item = finding.to_json()
                item["line"] = str(line_number)
                removed.append(item)
            continue
        kept_lines.append(line)
    return "\n".join(kept_lines).strip() + "\n", removed


def build_manifest(scan_report: dict, sanitized_text: str) -> dict:
    return {
        "schema_version": 1,
        "name": scan_report["skill_name"],
        "version": "0.1.0",
        "status": scan_report["summary"]["status"],
        "risk_level": scan_report["summary"]["risk_level"],
        "taxonomy": scan_report["taxonomy"],
        "source": scan_report["source"],
        "hashes": {
            "source_sha256": scan_report["hashes"]["source_sha256"],
            "sanitized_sha256": text_sha256(sanitized_text),
        },
        "allowed_tools": [],
        "required_verifiers": scan_report["required_verifiers"],
        "policy": {
            "filesystem": {"scope": "workspace_only"},
            "network": {"scope": "none"},
            "approval": {"required_for": ["trust", "execution"]},
        },
        "findings": scan_report["findings"],
    }


def sanitize_to_dir(source_dir: Path, out_dir: Path, args: argparse.Namespace) -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)

    source_skill = source_dir / "SKILL.md"
    if source_skill.exists():
        source_text = source_skill.read_text(encoding="utf-8")
    else:
        source_text = "\n".join(text for _, text in read_text_files(source_dir))

    scan_report = build_scan_report(source_dir, args)
    sanitized_text, removed = sanitize_skill_text(source_text)
    manifest = build_manifest(scan_report, sanitized_text)
    report = dict(scan_report)
    report["hashes"] = dict(scan_report["hashes"])
    report["hashes"]["sanitized_sha256"] = manifest["hashes"]["sanitized_sha256"]
    report["summary"] = dict(scan_report["summary"])
    report["summary"]["removed_fragment_count"] = len(removed)
    report["removed_fragments"] = removed

    (out_dir / "SKILL.md").write_text(sanitized_text, encoding="utf-8")
    (out_dir / "skill.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (out_dir / "SANITIZATION_REPORT.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return manifest


def sanitize_command(args: argparse.Namespace) -> int:
    source_dir = Path(args.source)
    if not source_dir.exists() or not source_dir.is_dir():
        raise SystemExit(f"source must be an existing directory: {source_dir}")
    sanitize_to_dir(source_dir, Path(args.out), args)
    return 0


def load_manifest(skill_dir: Path) -> dict:
    manifest_path = skill_dir / "skill.json"
    if not manifest_path.exists():
        raise SystemExit(f"missing skill manifest: {manifest_path}")
    return json.loads(manifest_path.read_text(encoding="utf-8"))


def manifest_index_entry(manifest: dict, registry_path: Path) -> dict:
    return {
        "name": manifest["name"],
        "status": manifest["status"],
        "risk_level": manifest["risk_level"],
        "taxonomy": manifest["taxonomy"],
        "source": manifest["source"],
        "hashes": manifest["hashes"],
        "registry_path": registry_path.as_posix(),
    }


def write_registry_index(registry_dir: Path) -> dict:
    index = build_registry_index(registry_dir)
    registry_dir.mkdir(parents=True, exist_ok=True)
    (registry_dir / "index.json").write_text(json.dumps(index, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return index


def build_registry_index(registry_dir: Path) -> dict:
    skills = []
    for manifest_path in sorted(registry_dir.glob("*/*/skill.json")):
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        skills.append(manifest_index_entry(manifest, manifest_path.parent.relative_to(registry_dir)))
    return {
        "schema_version": 1,
        "generated_at": utc_now(),
        "skill_count": len(skills),
        "skills": skills,
    }


def load_registry_index(registry_dir: Path) -> dict:
    index_path = registry_dir / "index.json"
    if not index_path.exists():
        return write_registry_index(registry_dir)
    return json.loads(index_path.read_text(encoding="utf-8"))


def import_command(args: argparse.Namespace) -> int:
    incoming_dir = Path(args.incoming)
    registry_dir = Path(args.registry)
    if not incoming_dir.exists() or not incoming_dir.is_dir():
        raise SystemExit(f"incoming must be an existing directory: {incoming_dir}")
    registry_dir.mkdir(parents=True, exist_ok=True)
    for source_dir in sorted(path for path in incoming_dir.iterdir() if path.is_dir()):
        scan_report = build_scan_report(source_dir, args)
        category = scan_report["taxonomy"]["category"]
        out_dir = registry_dir / category / source_dir.name
        sanitize_to_dir(source_dir, out_dir, args)
    write_registry_index(registry_dir)
    return 0


def list_command(args: argparse.Namespace) -> int:
    index = load_registry_index(Path(args.registry))
    print(json.dumps(index, indent=2, sort_keys=True))
    return 0


def inspect_command(args: argparse.Namespace) -> int:
    registry_dir = Path(args.registry)
    index = load_registry_index(registry_dir)
    matches = [entry for entry in index["skills"] if entry["name"] == args.name]
    if not matches:
        return 2
    manifest_path = registry_dir / matches[0]["registry_path"] / "skill.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    print(json.dumps(manifest, indent=2, sort_keys=True))
    return 0


def skill_matches_task(entry: dict, task_taxonomy: dict, task_text: str) -> int:
    score = 0
    taxonomy = entry.get("taxonomy", {})
    if taxonomy.get("category") == task_taxonomy.get("category"):
        score += 10
    if taxonomy.get("subcategory") == task_taxonomy.get("subcategory"):
        score += 5
    haystack = " ".join(
        [
            entry.get("name", ""),
            taxonomy.get("subcategory", ""),
            taxonomy.get("task_intent", ""),
            taxonomy.get("artifact_type", ""),
        ]
    ).lower()
    for token in task_text.lower().replace("-", " ").replace("_", " ").split():
        if len(token) >= 3 and token in haystack:
            score += 1
    return score


def select_command(args: argparse.Namespace) -> int:
    registry_dir = Path(args.registry)
    index = load_registry_index(registry_dir)
    task_taxonomy = classify_skill("task", args.task).to_json()
    selected = select_skills_for_task(registry_dir, task_taxonomy, args.task, args.include_review_required)
    result = {
        "schema_version": 1,
        "task": args.task,
        "task_taxonomy": task_taxonomy,
        "skill_count": len(selected),
        "skills": selected,
    }
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


def select_skills_for_task(registry_dir: Path, task_taxonomy: dict, task: str, include_review_required: bool) -> list[dict]:
    index = load_registry_index(registry_dir)
    selected = []
    allowed_statuses = {"trusted"}
    if include_review_required:
        allowed_statuses.add("review_required")
    for entry in index["skills"]:
        manifest_path = registry_dir / entry["registry_path"] / "skill.json"
        if not manifest_path.exists():
            continue
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        if manifest.get("status") not in allowed_statuses:
            continue
        score = skill_matches_task(manifest, task_taxonomy, task)
        if score <= 0:
            continue
        item = manifest_index_entry(manifest, Path(entry["registry_path"]))
        item["match_score"] = score
        selected.append(item)
    selected.sort(key=lambda item: (-item["match_score"], item["name"]))
    return selected


def extract_frontmatter_description(text: str) -> str:
    match = re.search(r"^description:\s*(.+)$", text, re.MULTILINE)
    return match.group(1).strip() if match else ""


def extract_markdown_sections(text: str) -> dict[str, str]:
    sections: dict[str, str] = {}
    matches = list(re.finditer(r"^##\s+(.+?)\s*$", text, re.MULTILINE))
    for index, match in enumerate(matches):
        title = match.group(1).strip()
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        sections[title] = text[start:end].strip()
    return sections


def load_skill_pack_item(registry_dir: Path, entry: dict) -> dict:
    skill_dir = registry_dir / entry["registry_path"]
    skill_text = (skill_dir / "SKILL.md").read_text(encoding="utf-8")
    sections = extract_markdown_sections(skill_text)
    manifest = json.loads((skill_dir / "skill.json").read_text(encoding="utf-8"))
    return {
        "name": entry["name"],
        "status": entry["status"],
        "risk_level": entry["risk_level"],
        "match_score": entry.get("match_score", 0),
        "taxonomy": entry["taxonomy"],
        "source": entry["source"],
        "hashes": entry["hashes"],
        "registry_path": entry["registry_path"],
        "description": extract_frontmatter_description(skill_text),
        "when_to_use": sections.get("When To Use", ""),
        "safe_workflow": sections.get("Safe Workflow", ""),
        "expected_output": sections.get("Expected Output", ""),
        "verifier_expectations": sections.get("Verifier Expectations", ""),
        "failure_handling": sections.get("Failure Handling", ""),
        "policy": manifest.get("policy", {}),
    }


def load_trusted_skill_pack_items(registry_dir: Path) -> list[dict]:
    index = load_registry_index(registry_dir)
    skills = []
    for entry in index["skills"]:
        if entry.get("status") != "trusted":
            continue
        item = load_skill_pack_item(registry_dir, entry)
        item["match_score"] = item.get("match_score", 0)
        skills.append(item)
    return skills


def load_bundles_index(bundles_path: Path) -> dict:
    if not bundles_path.exists():
        raise SystemExit(f"missing bundles index: {bundles_path}")
    payload = json.loads(bundles_path.read_text(encoding="utf-8"))
    if not isinstance(payload.get("bundles"), list):
        raise SystemExit(f"invalid bundles index: {bundles_path}")
    return payload


def trusted_skill_names(registry_dir: Path) -> set[str]:
    index = load_registry_index(registry_dir)
    return {entry["name"] for entry in index["skills"] if entry.get("status") == "trusted"}


def bundle_matches_task(bundle: dict, task: str, selected_skill_names: set[str]) -> int:
    score = 0
    bundle_skills = set(bundle.get("skills", []))
    overlap_count = len(bundle_skills & selected_skill_names)
    if overlap_count == 0:
        return 0
    score += overlap_count * 5
    haystack = " ".join(
        [
            bundle.get("id", ""),
            bundle.get("name", ""),
            bundle.get("scenario", ""),
            " ".join(bundle.get("skills", [])),
            " ".join(bundle.get("expected_output", [])),
        ]
    ).lower()
    for token in task.lower().replace("-", " ").replace("_", " ").split():
        if len(token) >= 3 and token in haystack:
            score += 1
    return score


def select_bundles_for_task(registry_dir: Path, bundles_path: Path, task: str, selected_skills: list[dict]) -> list[dict]:
    bundles_index = load_bundles_index(bundles_path)
    trusted_names = trusted_skill_names(registry_dir)
    selected_skill_names = {skill["name"] for skill in selected_skills}
    selected_bundles = []
    for bundle in bundles_index["bundles"]:
        if bundle.get("status") != "trusted":
            continue
        bundle_skills = set(bundle.get("skills", []))
        if not bundle_skills or not bundle_skills.issubset(trusted_names):
            continue
        score = bundle_matches_task(bundle, task, selected_skill_names)
        if score <= 0:
            continue
        item = {
            "id": bundle.get("id", ""),
            "name": bundle.get("name", bundle.get("id", "")),
            "status": bundle.get("status"),
            "scenario": bundle.get("scenario", ""),
            "skills": bundle.get("skills", []),
            "expected_output": bundle.get("expected_output", []),
            "safety_boundary": bundle.get("safety_boundary", ""),
            "match_score": score,
        }
        selected_bundles.append(item)
    selected_bundles.sort(key=lambda item: (-item["match_score"], item["id"]))
    return selected_bundles


def build_agent_instructions(
    task: str,
    skills: list[dict],
    bundles: list[dict] | None = None,
    router_context: dict | None = None,
) -> str:
    lines = [
        "You are executing a task with a OneCode verified skill pack.",
        f"Task: {task}",
        "",
        "Safety boundary:",
        "- Only use trusted skills unless the operator explicitly enables review-mode use.",
        "- Skills provide method and verification guidance; they do not grant tool, network, filesystem, connector, or production permissions.",
        "- Follow the host runtime approval policy before any action outside the current approved workspace.",
        "- Preserve provenance, verification notes, and unresolved assumptions in the final answer.",
        "",
    ]
    if router_context and router_context.get("execution_plan"):
        lines.extend(["Execution plan:"])
        for step in router_context["execution_plan"]:
            lines.append(f"- {step['order']}. {step['skill']}: {step['instruction']}")
        lines.append("")
    if router_context and router_context.get("coverage"):
        lines.extend(["Capability coverage:"])
        for item in router_context["coverage"]:
            skill = item.get("skill") or "missing"
            lines.append(f"- {item['capability']}: {item['status']} by {skill}")
        lines.append("")
    lines.append("Selected skills:")
    for skill in skills:
        lines.extend(
            [
                "",
                f"## {skill['name']} (score {skill['match_score']})",
                f"Capability: {skill['description']}",
                "",
                "When to use:",
                skill["when_to_use"] or "Not specified.",
                "",
                "Safe workflow:",
                skill["safe_workflow"] or "Not specified.",
                "",
                "Expected output:",
                skill["expected_output"] or "Not specified.",
                "",
                "Verifier expectations:",
                skill["verifier_expectations"] or "Not specified.",
            ]
        )
        if skill["failure_handling"]:
            lines.extend(["", "Failure handling:", skill["failure_handling"]])
    if bundles:
        lines.extend(["", "Selected scenario bundles:"])
        for bundle in bundles:
            lines.extend(
                [
                    "",
                    f"## {bundle['name']} (score {bundle['match_score']})",
                    f"Scenario: {bundle['scenario']}",
                    "",
                    "Bundle skills:",
                    "\n".join(f"- {skill_name}" for skill_name in bundle["skills"]) or "Not specified.",
                    "",
                    "Expected output:",
                    "\n".join(f"- {item}" for item in bundle["expected_output"]) or "Not specified.",
                    "",
                    "Safety boundary:",
                    bundle["safety_boundary"] or "Skills provide method only; host runtime controls permissions.",
                ]
            )
    return "\n".join(lines).strip()


def build_task_pack(
    registry_dir: Path,
    task: str,
    top: int,
    include_review_required: bool,
    include_bundles: bool = False,
    bundles_path: Path | None = None,
    router_mode: str = "simple",
    max_skills: int | None = None,
    invariants: list[str] | str | None = None,
    strategy: str = "balanced",
    overlap_groups_path: Path | None = None,
) -> dict:
    verification = verify_registry(registry_dir)
    if verification["status"] != "ok":
        raise SystemExit("registry verification failed; refusing to build task pack")
    task_taxonomy = classify_skill("task", task).to_json()
    candidate_limit = max(top, max_skills or top) if router_mode in {"scenario", "mesh"} else top
    selected = select_skills_for_task(registry_dir, task_taxonomy, task, include_review_required)[:candidate_limit]
    skills = [load_skill_pack_item(registry_dir, entry) for entry in selected]
    bundles = []
    if include_bundles:
        bundle_index_path = bundles_path or Path("bundles/index.json")
        bundles = select_bundles_for_task(registry_dir, bundle_index_path, task, skills)
    if router_mode == "mesh":
        bundle_index_path = bundles_path or Path("bundles/index.json")
        bundles_index = load_bundles_index(bundle_index_path)
        selected_by_name = {skill["name"]: skill for skill in skills}
        for skill in load_trusted_skill_pack_items(registry_dir):
            selected_by_name.setdefault(skill["name"], skill)
        resolved_overlap_path = resolve_overlap_groups_path(registry_dir, overlap_groups_path)
        overlap_groups = load_overlap_groups(resolved_overlap_path) if resolved_overlap_path is not None else None
        routed = route_mesh_task(
            task=task,
            invariants=invariants,
            selected_skills=list(selected_by_name.values()),
            bundles_index=bundles_index,
            trusted_skill_names=trusted_skill_names(registry_dir),
            overlap_groups=overlap_groups,
            max_skills=max_skills or top,
            strategy=strategy,
        )
        skills = routed["skills"]
        bundles = []
        if include_bundles and routed["selected_scenario"].get("id"):
            scenario_id = routed["selected_scenario"]["id"]
            bundles = select_bundles_for_task(registry_dir, bundle_index_path, task, skills)
            bundles = [bundle for bundle in bundles if bundle["id"] == scenario_id] or bundles
        task_pack = {
            "schema_version": 1,
            "generated_at": utc_now(),
            "task": task,
            "task_taxonomy": task_taxonomy,
            "skill_count": len(skills),
            "bundle_count": len(bundles),
            "safety_boundary": "Only use trusted skills by default. Skills provide method and verification guidance, not runtime permissions.",
            "registry_verification": verification,
            "skills": skills,
            "bundles": bundles,
            "router": routed["router"],
            "task_profile": routed["task_profile"],
            "selected_scenario": routed["selected_scenario"],
            "coverage": routed["coverage"],
            "execution_plan": routed["execution_plan"],
            "selection_explanations": routed["selection_explanations"],
            "execution_graph": routed["execution_graph"],
            "invariant_capabilities": routed["invariant_capabilities"],
            "pruned_skills": routed["pruned_skills"],
        }
        task_pack["agent_instructions"] = build_agent_instructions(task, skills, bundles, task_pack)
        return task_pack
    if router_mode == "scenario":
        bundle_index_path = bundles_path or Path("bundles/index.json")
        bundles_index = load_bundles_index(bundle_index_path)
        selected_by_name = {skill["name"]: skill for skill in skills}
        for skill in load_trusted_skill_pack_items(registry_dir):
            selected_by_name.setdefault(skill["name"], skill)
        routed = route_scenario_task(
            task=task,
            selected_skills=list(selected_by_name.values()),
            bundles_index=bundles_index,
            trusted_skill_names=trusted_skill_names(registry_dir),
            max_skills=max_skills or top,
        )
        skills = routed["skills"]
        bundles = []
        if include_bundles and routed["selected_scenario"].get("id"):
            scenario_id = routed["selected_scenario"]["id"]
            bundles = select_bundles_for_task(registry_dir, bundle_index_path, task, skills)
            bundles = [bundle for bundle in bundles if bundle["id"] == scenario_id] or bundles
        task_pack = {
            "schema_version": 1,
            "generated_at": utc_now(),
            "task": task,
            "task_taxonomy": task_taxonomy,
            "skill_count": len(skills),
            "bundle_count": len(bundles),
            "safety_boundary": "Only use trusted skills by default. Skills provide method and verification guidance, not runtime permissions.",
            "registry_verification": verification,
            "skills": skills,
            "bundles": bundles,
            "router": routed["router"],
            "task_profile": routed["task_profile"],
            "selected_scenario": routed["selected_scenario"],
            "coverage": routed["coverage"],
            "execution_plan": routed["execution_plan"],
            "selection_explanations": routed["selection_explanations"],
        }
        task_pack["agent_instructions"] = build_agent_instructions(task, skills, bundles, task_pack)
        return task_pack
    return {
        "schema_version": 1,
        "generated_at": utc_now(),
        "task": task,
        "task_taxonomy": task_taxonomy,
        "skill_count": len(skills),
        "bundle_count": len(bundles),
        "safety_boundary": "Only use trusted skills by default. Skills provide method and verification guidance, not runtime permissions.",
        "registry_verification": verification,
        "skills": skills,
        "bundles": bundles,
        "agent_instructions": build_agent_instructions(task, skills, bundles),
    }


def render_task_pack_markdown(task_pack: dict) -> str:
    lines = [
        "# OneCode Agent Task Pack",
        "",
        f"Task: {task_pack['task']}",
        f"Generated at: {task_pack['generated_at']}",
        f"Selected skills: {task_pack['skill_count']}",
        "",
        "## Safety Boundary",
        "",
        task_pack["safety_boundary"],
    ]
    if task_pack.get("router"):
        lines.extend(
            [
                "",
                "## Task Profile",
                "",
                f"- router: `{task_pack['router']['mode']}`",
                f"- task type: `{task_pack['task_profile']['task_type']}`",
                f"- primary domain: `{task_pack['task_profile']['primary_domain']}`",
                "",
                "## Selected Scenario",
                "",
                f"- id: `{task_pack['selected_scenario'].get('id', '')}`",
                f"- score: `{task_pack['selected_scenario'].get('match_score', 0)}`",
                "",
                "## Capability Coverage",
                "",
            ]
        )
        for item in task_pack.get("coverage", []):
            lines.append(f"- `{item['capability']}`: {item['status']} by `{item.get('skill') or 'missing'}`")
        if task_pack.get("invariant_capabilities"):
            lines.extend(["", "## Invariant Capabilities", ""])
            for capability in task_pack["invariant_capabilities"]:
                lines.append(f"- `{capability}`")
        if task_pack.get("pruned_skills"):
            lines.extend(["", "## Pruned Overlap Skills", ""])
            for skill_name in task_pack["pruned_skills"]:
                lines.append(f"- `{skill_name}`")
        lines.extend(["", "## Execution Plan", ""])
        for step in task_pack.get("execution_plan", []):
            lines.append(f"{step['order']}. `{step['skill']}` - {step['instruction']}")
        if task_pack.get("execution_graph"):
            lines.extend(["", "## Execution Graph", ""])
            for node in task_pack["execution_graph"].get("nodes", []):
                lines.append(f"- `{node['id']}` `{node['stage']}` -> `{node['skill']}`")
            for edge in task_pack["execution_graph"].get("edges", []):
                lines.append(f"- edge `{edge['from']}` -> `{edge['to']}`")
        lines.extend(["", "## Selection Explanations", ""])
        for item in task_pack.get("selection_explanations", []):
            lines.append(f"- `{item['name']}` ({item['type']}, {item['role']}): {item['selection_reason']}")
    lines.extend(["", "## Selected Skills"])
    for skill in task_pack["skills"]:
        lines.extend(
            [
                "",
                f"### {skill['name']}",
                "",
                f"- status: `{skill['status']}`",
                f"- risk: `{skill['risk_level']}`",
                f"- match score: `{skill['match_score']}`",
                f"- category: `{skill['taxonomy']['category']}`",
                f"- source: {skill['source']['url']}",
                "",
                skill["description"],
                "",
                "#### Safe Workflow",
                "",
                skill["safe_workflow"] or "Not specified.",
                "",
                "#### Expected Output",
                "",
                skill["expected_output"] or "Not specified.",
                "",
                "#### Verifier Expectations",
                "",
                skill["verifier_expectations"] or "Not specified.",
            ]
        )
    if task_pack.get("bundles"):
        lines.extend(["", "## Scenario Bundles"])
        for bundle in task_pack["bundles"]:
            lines.extend(
                [
                    "",
                    f"### {bundle['name']}",
                    "",
                    f"- id: `{bundle['id']}`",
                    f"- status: `{bundle['status']}`",
                    f"- match score: `{bundle['match_score']}`",
                    "",
                    bundle["scenario"],
                    "",
                    "#### Skills",
                    "",
                    "\n".join(f"- `{skill_name}`" for skill_name in bundle["skills"]),
                    "",
                    "#### Expected Output",
                    "",
                    "\n".join(f"- {item}" for item in bundle["expected_output"]) or "Not specified.",
                ]
            )
    lines.extend(["", "## Agent Instructions", "", task_pack["agent_instructions"], ""])
    return "\n".join(lines)


def task_pack_command(args: argparse.Namespace) -> int:
    task_pack = build_task_pack(
        Path(args.registry),
        args.task,
        args.top,
        args.include_review_required,
        args.include_bundles,
        Path(args.bundles) if args.bundles else None,
        args.router,
        args.max_skills,
        args.invariants if getattr(args, "invariants", None) else None,
        getattr(args, "strategy", "balanced"),
        Path(args.overlap_groups) if getattr(args, "overlap_groups", None) else None,
    )
    if args.format == "markdown":
        print(render_task_pack_markdown(task_pack))
    else:
        print(json.dumps(task_pack, indent=2, sort_keys=True))
    return 0


def smart_command(args: argparse.Namespace) -> int:
    task_pack = build_task_pack(
        Path(args.registry),
        args.task,
        args.max_skills,
        False,
        True,
        Path(args.bundles) if args.bundles else None,
        "mesh",
        args.max_skills,
        args.invariants,
        args.strategy,
        Path(args.overlap_groups) if args.overlap_groups else None,
    )
    if args.format == "markdown":
        print(render_task_pack_markdown(task_pack))
    else:
        print(json.dumps(task_pack, indent=2, sort_keys=True))
    return 0


def verify_registry(registry_dir: Path) -> dict:
    issues = []
    trusted_count = 0
    tampered_count = 0
    unknown_provenance_count = 0
    skill_count = 0
    for manifest_path in sorted(registry_dir.glob("*/*/skill.json")):
        skill_count += 1
        skill_dir = manifest_path.parent
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        name = manifest.get("name", skill_dir.name)
        if manifest.get("status") == "trusted":
            trusted_count += 1

        skill_path = skill_dir / "SKILL.md"
        expected_hash = manifest.get("hashes", {}).get("sanitized_sha256")
        if not skill_path.exists():
            tampered_count += 1
            issues.append(
                {
                    "id": "sanitized-skill-missing",
                    "severity": "critical",
                    "skill": name,
                    "path": skill_path.as_posix(),
                }
            )
        else:
            actual_hash = text_sha256(skill_path.read_text(encoding="utf-8"))
            if actual_hash != expected_hash:
                tampered_count += 1
                issues.append(
                    {
                        "id": "sanitized-hash-mismatch",
                        "severity": "critical",
                        "skill": name,
                        "path": skill_path.as_posix(),
                    }
                )

        source = manifest.get("source", {})
        if any(source.get(field, "unknown") == "unknown" for field in SOURCE_PROVENANCE_FIELDS):
            unknown_provenance_count += 1
            issues.append(
                {
                    "id": "unknown-provenance",
                    "severity": "medium",
                    "skill": name,
                    "path": manifest_path.as_posix(),
                }
            )

    return {
        "schema_version": 1,
        "generated_at": utc_now(),
        "status": "failed" if issues else "ok",
        "skill_count": skill_count,
        "trusted_count": trusted_count,
        "tampered_count": tampered_count,
        "unknown_provenance_count": unknown_provenance_count,
        "issues": issues,
    }


def verify_command(args: argparse.Namespace) -> int:
    result = verify_registry(Path(args.registry))
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["status"] == "ok" else 2


def comparable_registry_index(index: dict) -> dict:
    payload = dict(index)
    payload.pop("generated_at", None)
    return payload


def registry_index_staleness(registry_dir: Path) -> list[dict]:
    index_path = registry_dir / "index.json"
    if not index_path.exists():
        return [
            {
                "id": "registry-index-missing",
                "severity": "high",
                "path": index_path.as_posix(),
            }
        ]
    existing = json.loads(index_path.read_text(encoding="utf-8"))
    expected = build_registry_index(registry_dir)
    if comparable_registry_index(existing) == comparable_registry_index(expected):
        return []
    return [
        {
            "id": "registry-index-stale",
            "severity": "high",
            "path": index_path.as_posix(),
            "expected_skill_count": expected["skill_count"],
            "actual_skill_count": existing.get("skill_count"),
        }
    ]


def add_issue(issues: list[dict], issue_id: str, path: Path | str, summary: str, severity: str = "high") -> None:
    issues.append(
        {
            "id": issue_id,
            "severity": severity,
            "path": path.as_posix() if isinstance(path, Path) else str(path),
            "summary": summary,
        }
    )


def validate_hashes(payload: dict, path: Path, issues: list[dict]) -> None:
    hashes = payload.get("hashes")
    if not isinstance(hashes, dict):
        add_issue(issues, "schema-invalid-hashes", path, "hashes must be an object")
        return
    for key in ["source_sha256", "sanitized_sha256"]:
        value = hashes.get(key)
        if not isinstance(value, str) or not HASH_PATTERN.fullmatch(value):
            add_issue(issues, "schema-invalid-hash", path, f"{key} must be a 64 character lowercase sha256 hex string")


def validate_source(payload: dict, path: Path, issues: list[dict]) -> None:
    source = payload.get("source")
    if not isinstance(source, dict):
        add_issue(issues, "schema-invalid-source", path, "source must be an object")
        return
    for field in SOURCE_REQUIRED_FIELDS:
        value = source.get(field)
        if not isinstance(value, str) or not value:
            add_issue(issues, "schema-missing-source-field", path, f"source.{field} is required")
    source_type = source.get("type")
    if isinstance(source_type, str) and source_type not in SOURCE_TYPE_VALUES:
        add_issue(issues, "schema-invalid-source-type", path, f"source.type {source_type!r} is not supported")
    source_usage = source.get("usage")
    if isinstance(source_usage, str) and source_usage not in SOURCE_USAGE_VALUES:
        add_issue(issues, "schema-invalid-source-usage", path, f"source.usage {source_usage!r} is not supported")
    if isinstance(source_type, str) and isinstance(source_usage, str):
        expected_usages = SOURCE_USAGE_BY_TYPE.get(source_type)
        if expected_usages is not None and source_usage not in expected_usages:
            allowed = ", ".join(sorted(expected_usages))
            add_issue(
                issues,
                "schema-invalid-source-usage-for-type",
                path,
                f"source.type {source_type!r} requires source.usage to be one of: {allowed}",
            )


def validate_taxonomy(payload: dict, path: Path, issues: list[dict]) -> None:
    taxonomy = payload.get("taxonomy")
    if not isinstance(taxonomy, dict):
        add_issue(issues, "schema-invalid-taxonomy", path, "taxonomy must be an object")
        return
    for field in ["category", "subcategory", "collection_priority"]:
        if not isinstance(taxonomy.get(field), str) or not taxonomy.get(field):
            add_issue(issues, "schema-missing-taxonomy-field", path, f"taxonomy.{field} is required")


def validate_manifest_schema(payload: dict, path: Path, issues: list[dict]) -> None:
    required = [
        "schema_version",
        "name",
        "version",
        "status",
        "risk_level",
        "taxonomy",
        "source",
        "hashes",
        "allowed_tools",
        "required_verifiers",
        "policy",
    ]
    for field in required:
        if field not in payload:
            add_issue(issues, "schema-missing-manifest-field", path, f"{field} is required")
    if payload.get("schema_version") != 1:
        add_issue(issues, "schema-invalid-version", path, "schema_version must be 1")
    if payload.get("status") not in STATUS_VALUES:
        add_issue(issues, "schema-invalid-status", path, "status is not a supported registry state")
    if payload.get("risk_level") not in RISK_LEVEL_VALUES:
        add_issue(issues, "schema-invalid-risk-level", path, "risk_level is not supported")
    if not isinstance(payload.get("allowed_tools"), list):
        add_issue(issues, "schema-invalid-allowed-tools", path, "allowed_tools must be an array")
    if not isinstance(payload.get("required_verifiers"), list):
        add_issue(issues, "schema-invalid-required-verifiers", path, "required_verifiers must be an array")
    if not isinstance(payload.get("policy"), dict):
        add_issue(issues, "schema-invalid-policy", path, "policy must be an object")
    validate_taxonomy(payload, path, issues)
    validate_source(payload, path, issues)
    validate_hashes(payload, path, issues)


def validate_registry_index_schema(payload: dict, path: Path, issues: list[dict]) -> None:
    for field in ["schema_version", "generated_at", "skill_count", "skills"]:
        if field not in payload:
            add_issue(issues, "schema-missing-index-field", path, f"{field} is required")
    if payload.get("schema_version") != 1:
        add_issue(issues, "schema-invalid-version", path, "schema_version must be 1")
    skills = payload.get("skills")
    if not isinstance(skills, list):
        add_issue(issues, "schema-invalid-index-skills", path, "skills must be an array")
        return
    if payload.get("skill_count") != len(skills):
        add_issue(issues, "schema-index-count-mismatch", path, "skill_count must match skills length")
    for index, entry in enumerate(skills):
        entry_path = f"{path.as_posix()}#/skills/{index}"
        for field in ["name", "status", "risk_level", "taxonomy", "source", "hashes", "registry_path"]:
            if field not in entry:
                add_issue(issues, "schema-missing-index-entry-field", entry_path, f"{field} is required")
        if entry.get("status") not in STATUS_VALUES:
            add_issue(issues, "schema-invalid-status", entry_path, "status is not a supported registry state")
        if entry.get("risk_level") not in RISK_LEVEL_VALUES:
            add_issue(issues, "schema-invalid-risk-level", entry_path, "risk_level is not supported")
        validate_taxonomy(entry, Path(entry_path), issues)
        validate_source(entry, Path(entry_path), issues)
        validate_hashes(entry, Path(entry_path), issues)


def validate_verify_report_schema(payload: dict, path: Path, issues: list[dict]) -> None:
    for field in ["schema_version", "generated_at", "status", "skill_count", "trusted_count", "tampered_count", "unknown_provenance_count", "issues"]:
        if field not in payload:
            add_issue(issues, "schema-missing-verify-field", path, f"{field} is required")
    if payload.get("schema_version") != 1:
        add_issue(issues, "schema-invalid-version", path, "schema_version must be 1")
    if payload.get("status") not in {"ok", "failed"}:
        add_issue(issues, "schema-invalid-verify-status", path, "status must be ok or failed")
    for field in ["skill_count", "trusted_count", "tampered_count", "unknown_provenance_count"]:
        value = payload.get(field)
        if not isinstance(value, int) or value < 0:
            add_issue(issues, "schema-invalid-verify-count", path, f"{field} must be a non-negative integer")
    if not isinstance(payload.get("issues"), list):
        add_issue(issues, "schema-invalid-verify-issues", path, "issues must be an array")


def validate_sanitization_report_schema(payload: dict, path: Path, manifest: dict, issues: list[dict]) -> None:
    for field in [
        "schema_version",
        "skill_name",
        "taxonomy",
        "source",
        "files",
        "hashes",
        "summary",
        "findings",
        "required_verifiers",
        "recommendation",
    ]:
        if field not in payload:
            add_issue(issues, "schema-missing-report-field", path, f"{field} is required")
    if payload.get("schema_version") != 1:
        add_issue(issues, "schema-invalid-version", path, "schema_version must be 1")
    if payload.get("skill_name") != manifest.get("name"):
        add_issue(issues, "schema-report-name-mismatch", path, "report skill_name must match manifest name")
    validate_taxonomy(payload, path, issues)
    validate_source(payload, path, issues)
    validate_hashes(payload, path, issues)
    for field in ["files", "findings", "required_verifiers"]:
        if not isinstance(payload.get(field), list):
            add_issue(issues, "schema-invalid-report-list", path, f"{field} must be an array")
    summary = payload.get("summary")
    if not isinstance(summary, dict):
        add_issue(issues, "schema-invalid-report-summary", path, "summary must be an object")
    else:
        for field in ["status", "risk_level", "removed_fragment_count", "rewritten_fragment_count", "unresolved_finding_count"]:
            if field not in summary:
                add_issue(issues, "schema-missing-report-summary-field", path, f"summary.{field} is required")
        if summary.get("status") != manifest.get("status") or summary.get("risk_level") != manifest.get("risk_level"):
            add_issue(issues, "schema-report-summary-mismatch", path, "report summary status and risk_level must match manifest")

    for field in ["source", "hashes", "taxonomy"]:
        if payload.get(field) != manifest.get(field):
            add_issue(issues, f"schema-report-{field}-mismatch", path, f"report {field} must match manifest {field}")
    if payload.get("required_verifiers") != manifest.get("required_verifiers"):
        add_issue(
            issues,
            "schema-report-required-verifiers-mismatch",
            path,
            "report required_verifiers must match manifest required_verifiers",
        )


def schema_check(registry_dir: Path) -> dict:
    issues: list[dict] = []
    skill_manifest_count = 0
    for manifest_path in sorted(registry_dir.glob("*/*/skill.json")):
        skill_manifest_count += 1
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            add_issue(issues, "schema-invalid-json", manifest_path, str(exc), "critical")
            continue
        validate_manifest_schema(manifest, manifest_path, issues)
        report_path = manifest_path.parent / "SANITIZATION_REPORT.json"
        try:
            report = json.loads(report_path.read_text(encoding="utf-8"))
        except FileNotFoundError:
            add_issue(issues, "schema-report-missing", report_path, "sanitization report is missing", "critical")
            continue
        except json.JSONDecodeError as exc:
            add_issue(issues, "schema-invalid-json", report_path, str(exc), "critical")
            continue
        validate_sanitization_report_schema(report, report_path, manifest, issues)

    index_path = registry_dir / "index.json"
    try:
        registry_index = json.loads(index_path.read_text(encoding="utf-8"))
        validate_registry_index_schema(registry_index, index_path, issues)
    except FileNotFoundError:
        add_issue(issues, "schema-index-missing", index_path, "registry index is missing", "critical")
    except json.JSONDecodeError as exc:
        add_issue(issues, "schema-invalid-json", index_path, str(exc), "critical")

    with tempfile.TemporaryDirectory() as tmp:
        verify_path = Path(tmp) / "verify-report.json"
        verify_report = verify_registry(registry_dir)
        verify_path.write_text(json.dumps(verify_report), encoding="utf-8")
        validate_verify_report_schema(verify_report, verify_path, issues)

    return {
        "schema_version": 1,
        "generated_at": utc_now(),
        "status": "failed" if issues else "ok",
        "skill_manifest_count": skill_manifest_count,
        "issues": issues,
    }


def schema_check_command(args: argparse.Namespace) -> int:
    result = schema_check(Path(args.registry))
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["status"] == "ok" else 2


def validate_external_references(references_path: Path) -> dict:
    issues: list[dict] = []
    try:
        payload = json.loads(references_path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {
            "schema_version": 1,
            "generated_at": utc_now(),
            "status": "failed",
            "reference_count": 0,
            "issues": [
                {
                    "id": "reference-index-missing",
                    "severity": "high",
                    "path": references_path.as_posix(),
                }
            ],
        }
    except json.JSONDecodeError as exc:
        return {
            "schema_version": 1,
            "generated_at": utc_now(),
            "status": "failed",
            "reference_count": 0,
            "issues": [
                {
                    "id": "reference-invalid-json",
                    "severity": "critical",
                    "path": references_path.as_posix(),
                    "summary": str(exc),
                }
            ],
        }

    if payload.get("schema_version") != 1:
        add_issue(issues, "reference-invalid-version", references_path, "schema_version must be 1")
    references = payload.get("references")
    if not isinstance(references, list):
        add_issue(issues, "reference-invalid-list", references_path, "references must be an array")
        references = []
    declared_count = payload.get("reference_count")
    if declared_count is not None and declared_count != len(references):
        issues.append(
            {
                "id": "reference-count-mismatch",
                "severity": "medium",
                "path": references_path.as_posix(),
                "expected": len(references),
                "actual": declared_count,
            }
        )

    seen_names = set()
    for index, reference in enumerate(references):
        reference_path = f"{references_path.as_posix()}#/references/{index}"
        if not isinstance(reference, dict):
            add_issue(issues, "reference-invalid-entry", reference_path, "reference entry must be an object")
            continue
        for field in REFERENCE_REQUIRED_FIELDS:
            value = reference.get(field)
            if value in (None, ""):
                issues.append(
                    {
                        "id": "reference-missing-field",
                        "severity": "high",
                        "path": reference_path,
                        "field": field,
                    }
                )
        name = reference.get("name")
        if isinstance(name, str):
            if name in seen_names:
                issues.append(
                    {
                        "id": "reference-duplicate-name",
                        "severity": "medium",
                        "path": reference_path,
                        "name": name,
                    }
                )
            seen_names.add(name)
        source_url = reference.get("source_url")
        if isinstance(source_url, str) and not source_url.startswith(("https://", "http://")):
            issues.append(
                {
                    "id": "reference-invalid-source-url",
                    "severity": "high",
                    "path": reference_path,
                    "source_url": source_url,
                }
            )
        source_type = reference.get("source_type")
        if isinstance(source_type, str) and source_type not in SOURCE_TYPE_VALUES:
            issues.append(
                {
                    "id": "reference-invalid-source-type",
                    "severity": "high",
                    "path": reference_path,
                    "source_type": source_type,
                }
            )
        adoption_status = reference.get("adoption_status")
        if isinstance(adoption_status, str) and adoption_status not in REFERENCE_ADOPTION_STATUSES:
            issues.append(
                {
                    "id": "reference-invalid-adoption-status",
                    "severity": "high",
                    "path": reference_path,
                    "adoption_status": adoption_status,
                }
            )
        for field in ["claimed_capabilities", "taxonomy_categories"]:
            value = reference.get(field)
            if not isinstance(value, list) or not value or not all(isinstance(item, str) and item for item in value):
                issues.append(
                    {
                        "id": "reference-invalid-list-field",
                        "severity": "high",
                        "path": reference_path,
                        "field": field,
                    }
                )
        if reference.get("metadata_only") is not True:
            issues.append(
                {
                    "id": "reference-not-metadata-only",
                    "severity": "critical",
                    "path": reference_path,
                    "name": name or "",
                }
            )

    return {
        "schema_version": 1,
        "generated_at": utc_now(),
        "status": "failed" if issues else "ok",
        "reference_count": len(references),
        "issues": issues,
    }


def reference_check_command(args: argparse.Namespace) -> int:
    result = validate_external_references(Path(args.references))
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["status"] == "ok" else 2


def load_router_eval(eval_path: Path) -> dict:
    if not eval_path.exists():
        raise SystemExit(f"missing router eval file: {eval_path}")
    payload = json.loads(eval_path.read_text(encoding="utf-8"))
    if payload.get("schema_version") != 1:
        raise SystemExit(f"invalid router eval schema_version: {eval_path}")
    if not isinstance(payload.get("cases"), list):
        raise SystemExit(f"invalid router eval cases: {eval_path}")
    return payload


def run_router_eval(
    eval_path: Path,
    registry_dir: Path,
    bundles_path: Path,
    overlap_groups_path: Path | None = None,
    max_skills: int = 8,
) -> dict:
    payload = load_router_eval(eval_path)
    cases = payload["cases"]
    declared_count = payload.get("case_count")
    results = []
    issues = []
    if declared_count is not None and declared_count != len(cases):
        issues.append(
            {
                "id": "router-eval-count-mismatch",
                "severity": "medium",
                "expected": len(cases),
                "actual": declared_count,
            }
        )
    for index, case in enumerate(cases):
        case_id = case.get("id", f"case-{index + 1}")
        task = case.get("task", "")
        router_mode = case.get("router", "scenario")
        case_issues = []
        if not isinstance(task, str) or not task:
            case_issues.append({"id": "router-eval-missing-task"})
        if router_mode not in {"scenario", "mesh"}:
            case_issues.append({"id": "router-eval-invalid-router", "router": router_mode})
        if case_issues:
            results.append({"id": case_id, "status": "failed", "issues": case_issues})
            continue

        task_pack = build_task_pack(
            registry_dir=registry_dir,
            task=task,
            top=max_skills,
            include_review_required=False,
            include_bundles=True,
            bundles_path=bundles_path,
            router_mode=router_mode,
            max_skills=max_skills,
            invariants=case.get("invariants"),
            strategy=case.get("strategy", "balanced"),
            overlap_groups_path=overlap_groups_path,
        )
        actual_scenario = task_pack.get("selected_scenario", {}).get("id", "")
        actual_task_type = task_pack.get("task_profile", {}).get("task_type", "")
        actual_skills = [skill["name"] for skill in task_pack.get("skills", [])]
        expected_scenario = case.get("expected_scenario")
        expected_task_type = case.get("expected_task_type")
        expected_skills = case.get("expected_skills", [])

        if expected_scenario is not None and actual_scenario != expected_scenario:
            case_issues.append(
                {
                    "id": "router-eval-scenario-mismatch",
                    "expected": expected_scenario,
                    "actual": actual_scenario,
                }
            )
        if expected_task_type is not None and actual_task_type != expected_task_type:
            case_issues.append(
                {
                    "id": "router-eval-task-type-mismatch",
                    "expected": expected_task_type,
                    "actual": actual_task_type,
                }
            )
        for skill_name in expected_skills:
            if skill_name not in actual_skills:
                case_issues.append(
                    {
                        "id": "router-eval-missing-skill",
                        "skill": skill_name,
                    }
                )

        results.append(
            {
                "id": case_id,
                "status": "failed" if case_issues else "ok",
                "router": router_mode,
                "task": task,
                "expected_scenario": expected_scenario,
                "actual_scenario": actual_scenario,
                "expected_task_type": expected_task_type,
                "actual_task_type": actual_task_type,
                "actual_skills": actual_skills,
                "issues": case_issues,
            }
        )

    failed_count = sum(1 for item in results if item["status"] != "ok")
    return {
        "schema_version": 1,
        "generated_at": utc_now(),
        "status": "failed" if failed_count or issues else "ok",
        "case_count": len(cases),
        "passed_count": len(cases) - failed_count,
        "failed_count": failed_count,
        "issues": issues,
        "cases": results,
    }


def router_eval_command(args: argparse.Namespace) -> int:
    result = run_router_eval(
        eval_path=Path(args.eval),
        registry_dir=Path(args.registry),
        bundles_path=Path(args.bundles),
        overlap_groups_path=Path(args.overlap_groups) if args.overlap_groups else None,
        max_skills=args.max_skills,
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["status"] == "ok" else 2


def validate_bundles(registry_dir: Path, bundles_path: Path) -> dict:
    issues = []
    bundles_index = load_bundles_index(bundles_path)
    index = load_registry_index(registry_dir)
    statuses = {entry["name"]: entry.get("status") for entry in index["skills"]}
    bundles = bundles_index["bundles"]
    declared_count = bundles_index.get("bundle_count")
    if declared_count is not None and declared_count != len(bundles):
        issues.append(
            {
                "id": "bundle-count-mismatch",
                "severity": "medium",
                "path": bundles_path.as_posix(),
                "expected": len(bundles),
                "actual": declared_count,
            }
        )
    for bundle in bundles:
        bundle_id = bundle.get("id", "unknown")
        if bundle.get("status") != "trusted":
            continue
        for skill_name in bundle.get("skills", []):
            status = statuses.get(skill_name)
            if status is None:
                issues.append(
                    {
                        "id": "bundle-missing-skill",
                        "severity": "high",
                        "bundle": bundle_id,
                        "skill": skill_name,
                    }
                )
            elif status != "trusted":
                issues.append(
                    {
                        "id": "bundle-non-trusted-skill",
                        "severity": "high",
                        "bundle": bundle_id,
                        "skill": skill_name,
                        "status": status,
                    }
                )
    return {
        "schema_version": 1,
        "bundle_count": len(bundles),
        "trusted_bundle_count": sum(1 for bundle in bundles if bundle.get("status") == "trusted"),
        "issues": issues,
    }


def load_overlap_groups(overlap_path: Path) -> dict:
    if not overlap_path.exists():
        raise SystemExit(f"missing overlap groups: {overlap_path}")
    payload = json.loads(overlap_path.read_text(encoding="utf-8"))
    if not isinstance(payload.get("groups"), list):
        raise SystemExit(f"invalid overlap groups: {overlap_path}")
    return payload


def validate_overlap_groups(registry_dir: Path, overlap_path: Path) -> dict:
    issues = []
    overlap_index = load_overlap_groups(overlap_path)
    index = load_registry_index(registry_dir)
    statuses = {entry["name"]: entry.get("status") for entry in index["skills"]}
    groups = overlap_index["groups"]
    declared_count = overlap_index.get("group_count")
    if overlap_index.get("schema_version") != 1:
        issues.append(
            {
                "id": "overlap-invalid-version",
                "severity": "high",
                "path": overlap_path.as_posix(),
                "expected": 1,
                "actual": overlap_index.get("schema_version"),
            }
        )
    if declared_count is not None and declared_count != len(groups):
        issues.append(
            {
                "id": "overlap-count-mismatch",
                "severity": "medium",
                "path": overlap_path.as_posix(),
                "expected": len(groups),
                "actual": declared_count,
            }
        )

    seen_group_ids = set()
    for group_index, group in enumerate(groups):
        group_id = group.get("id", f"group-{group_index}")
        group_path = f"{overlap_path.as_posix()}#/groups/{group_index}"
        if group_id in seen_group_ids:
            issues.append(
                {
                    "id": "overlap-duplicate-group",
                    "severity": "high",
                    "group": group_id,
                    "path": group_path,
                }
            )
        seen_group_ids.add(group_id)
        if group.get("status") != "trusted":
            issues.append(
                {
                    "id": "overlap-untrusted-group-status",
                    "severity": "high",
                    "group": group_id,
                    "path": group_path,
                    "status": group.get("status", "missing"),
                }
            )

        primary_skill = group.get("primary_skill")
        if not isinstance(primary_skill, str) or not primary_skill:
            issues.append(
                {
                    "id": "overlap-missing-primary-skill",
                    "severity": "high",
                    "group": group_id,
                    "path": group_path,
                }
            )
        else:
            validate_overlap_skill_reference(issues, statuses, group_id, primary_skill, "primary_skill")

        group_skill_refs = []
        for field in ["adjacent_skills", "use_before", "use_after"]:
            values = group.get(field, [])
            if not isinstance(values, list):
                issues.append(
                    {
                        "id": "overlap-invalid-skill-list",
                        "severity": "high",
                        "group": group_id,
                        "field": field,
                        "path": group_path,
                    }
                )
                continue
            for skill_name in values:
                if not isinstance(skill_name, str) or not skill_name:
                    issues.append(
                        {
                            "id": "overlap-invalid-skill-name",
                            "severity": "high",
                            "group": group_id,
                            "field": field,
                            "path": group_path,
                        }
                    )
                    continue
                group_skill_refs.append((field, skill_name))
                validate_overlap_skill_reference(issues, statuses, group_id, skill_name, field)

        seen_refs = set()
        if isinstance(primary_skill, str) and primary_skill:
            seen_refs.add(primary_skill)
        for field, skill_name in group_skill_refs:
            if skill_name in seen_refs:
                issues.append(
                    {
                        "id": "overlap-duplicate-skill",
                        "severity": "medium",
                        "group": group_id,
                        "field": field,
                        "skill": skill_name,
                    }
                )
            seen_refs.add(skill_name)

    return {
        "schema_version": 1,
        "group_count": len(groups),
        "issues": issues,
    }


def validate_overlap_skill_reference(
    issues: list[dict],
    statuses: dict[str, str | None],
    group_id: str,
    skill_name: str,
    field: str,
) -> None:
    status = statuses.get(skill_name)
    if status is None:
        issues.append(
            {
                "id": "overlap-missing-skill",
                "severity": "high",
                "group": group_id,
                "field": field,
                "skill": skill_name,
            }
        )
    elif status != "trusted":
        issues.append(
            {
                "id": "overlap-non-trusted-skill",
                "severity": "high",
                "group": group_id,
                "field": field,
                "skill": skill_name,
                "status": status,
            }
        )


def resolve_overlap_groups_path(registry_dir: Path, overlap_path: Path | None) -> Path | None:
    if overlap_path is not None:
        return overlap_path
    default_path = registry_dir / "overlap-groups.json"
    return default_path if default_path.exists() else None


def maintain_check(
    registry_dir: Path,
    bundles_path: Path | None = None,
    overlap_groups_path: Path | None = None,
    references_path: Path | None = None,
) -> dict:
    registry_verification = verify_registry(registry_dir)
    issues = list(registry_verification["issues"])
    issues.extend(registry_index_staleness(registry_dir))
    bundle_validation = None
    if bundles_path is not None:
        bundle_validation = validate_bundles(registry_dir, bundles_path)
        issues.extend(bundle_validation["issues"])
    overlap_validation = None
    resolved_overlap_path = resolve_overlap_groups_path(registry_dir, overlap_groups_path)
    if resolved_overlap_path is not None:
        overlap_validation = validate_overlap_groups(registry_dir, resolved_overlap_path)
        issues.extend(overlap_validation["issues"])
    reference_validation = None
    if references_path is not None:
        reference_validation = validate_external_references(references_path)
        issues.extend(reference_validation["issues"])
    return {
        "schema_version": 1,
        "generated_at": utc_now(),
        "status": "failed" if issues else "ok",
        "registry_verification": registry_verification,
        "bundle_validation": bundle_validation,
        "overlap_validation": overlap_validation,
        "reference_validation": reference_validation,
        "issues": issues,
    }


def maintain_check_command(args: argparse.Namespace) -> int:
    result = maintain_check(
        Path(args.registry),
        Path(args.bundles) if args.bundles else None,
        Path(args.overlap_groups) if args.overlap_groups else None,
        Path(args.references) if getattr(args, "references", None) else None,
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["status"] == "ok" else 2


def reindex_command(args: argparse.Namespace) -> int:
    write_registry_index(Path(args.registry))
    return 0


def audit_command(args: argparse.Namespace) -> int:
    skill_dir = Path(args.skill_dir)
    manifest = load_manifest(skill_dir)
    skill_path = skill_dir / "SKILL.md"
    if not skill_path.exists():
        return 2
    actual_hash = text_sha256(skill_path.read_text(encoding="utf-8"))
    expected_hash = manifest.get("hashes", {}).get("sanitized_sha256")
    if actual_hash != expected_hash:
        return 2
    return 0 if manifest.get("status") == "trusted" else 2


def approve_command(args: argparse.Namespace) -> int:
    return set_status_command(args, "trusted")


def registry_root_for_skill_dir(skill_dir: Path) -> Path | None:
    if len(skill_dir.parts) < 2:
        return None
    registry_dir = skill_dir.parent.parent
    if (registry_dir / "index.json").exists():
        return registry_dir
    return None


def set_status_command(args: argparse.Namespace, status: str) -> int:
    skill_dir = Path(args.skill_dir)
    manifest = load_manifest(skill_dir)
    now = utc_now()
    manifest["status"] = status
    if status == "trusted":
        manifest["approved_at"] = now
        manifest["approval_note"] = "Approved by local operator."
    elif status == "rejected":
        manifest["rejected_at"] = now
        manifest["rejection_note"] = "Rejected by local operator."
    elif status == "disabled":
        manifest["disabled_at"] = now
        manifest["disable_note"] = "Disabled by local operator."
    (skill_dir / "skill.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    report_path = skill_dir / "SANITIZATION_REPORT.json"
    if report_path.exists():
        report = json.loads(report_path.read_text(encoding="utf-8"))
        report["summary"]["status"] = status
        if status == "trusted":
            report["approved_at"] = manifest["approved_at"]
        elif status == "rejected":
            report["rejected_at"] = manifest["rejected_at"]
        elif status == "disabled":
            report["disabled_at"] = manifest["disabled_at"]
        report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    registry_dir = registry_root_for_skill_dir(skill_dir)
    if registry_dir is not None:
        write_registry_index(registry_dir)
    return 0


def reject_command(args: argparse.Namespace) -> int:
    return set_status_command(args, "rejected")


def disable_command(args: argparse.Namespace) -> int:
    return set_status_command(args, "disabled")


def scan_command(args: argparse.Namespace) -> int:
    source_dir = Path(args.source)
    if not source_dir.exists() or not source_dir.is_dir():
        raise SystemExit(f"source must be an existing directory: {source_dir}")
    report = build_scan_report(source_dir, args)
    output = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out:
        out_path = Path(args.out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(output, encoding="utf-8")
    else:
        print(output, end="")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="onecode-skill-sanitizer")
    subparsers = parser.add_subparsers(dest="command", required=True)

    scan_parser = subparsers.add_parser("scan")
    scan_parser.add_argument("source")
    scan_parser.add_argument("--out")
    add_provenance_args(scan_parser)
    scan_parser.set_defaults(func=scan_command)

    sanitize_parser = subparsers.add_parser("sanitize")
    sanitize_parser.add_argument("source")
    sanitize_parser.add_argument("--out", required=True)
    add_provenance_args(sanitize_parser)
    sanitize_parser.set_defaults(func=sanitize_command)

    audit_parser = subparsers.add_parser("audit")
    audit_parser.add_argument("skill_dir")
    audit_parser.set_defaults(func=audit_command)

    approve_parser = subparsers.add_parser("approve")
    approve_parser.add_argument("skill_dir")
    approve_parser.set_defaults(func=approve_command)

    reject_parser = subparsers.add_parser("reject")
    reject_parser.add_argument("skill_dir")
    reject_parser.set_defaults(func=reject_command)

    disable_parser = subparsers.add_parser("disable")
    disable_parser.add_argument("skill_dir")
    disable_parser.set_defaults(func=disable_command)

    import_parser = subparsers.add_parser("import")
    import_parser.add_argument("incoming")
    import_parser.add_argument("--registry", required=True)
    add_provenance_args(import_parser)
    import_parser.set_defaults(func=import_command)

    list_parser = subparsers.add_parser("list")
    list_parser.add_argument("--registry", required=True)
    list_parser.set_defaults(func=list_command)

    inspect_parser = subparsers.add_parser("inspect")
    inspect_parser.add_argument("name")
    inspect_parser.add_argument("--registry", required=True)
    inspect_parser.set_defaults(func=inspect_command)

    select_parser = subparsers.add_parser("select")
    select_parser.add_argument("task")
    select_parser.add_argument("--registry", required=True)
    select_parser.add_argument("--include-review-required", action="store_true")
    select_parser.set_defaults(func=select_command)

    task_pack_parser = subparsers.add_parser("task-pack")
    task_pack_parser.add_argument("task")
    task_pack_parser.add_argument("--registry", required=True)
    task_pack_parser.add_argument("--top", type=int, default=3)
    task_pack_parser.add_argument("--format", choices=["json", "markdown"], default="json")
    task_pack_parser.add_argument("--include-review-required", action="store_true")
    task_pack_parser.add_argument("--include-bundles", action="store_true")
    task_pack_parser.add_argument("--bundles", default="bundles/index.json")
    task_pack_parser.add_argument("--router", choices=["simple", "scenario", "mesh"], default="simple")
    task_pack_parser.add_argument("--max-skills", type=int)
    task_pack_parser.add_argument("--invariants", action="append")
    task_pack_parser.add_argument("--strategy", choices=["fast", "balanced", "deep"], default="balanced")
    task_pack_parser.add_argument("--overlap-groups")
    task_pack_parser.set_defaults(func=task_pack_command)

    smart_parser = subparsers.add_parser("smart")
    smart_parser.add_argument("task")
    smart_parser.add_argument("--registry", default="catalog")
    smart_parser.add_argument("--bundles", default="bundles/index.json")
    smart_parser.add_argument("--overlap-groups")
    smart_parser.add_argument("--invariants", action="append")
    smart_parser.add_argument("--strategy", choices=["fast", "balanced", "deep"], default="balanced")
    smart_parser.add_argument("--max-skills", type=int, default=8)
    smart_parser.add_argument("--format", choices=["json", "markdown"], default="json")
    smart_parser.set_defaults(func=smart_command)

    verify_parser = subparsers.add_parser("verify")
    verify_parser.add_argument("--registry", required=True)
    verify_parser.set_defaults(func=verify_command)

    maintain_check_parser = subparsers.add_parser("maintain-check")
    maintain_check_parser.add_argument("--registry", required=True)
    maintain_check_parser.add_argument("--bundles")
    maintain_check_parser.add_argument("--overlap-groups")
    maintain_check_parser.add_argument("--references")
    maintain_check_parser.set_defaults(func=maintain_check_command)

    schema_check_parser = subparsers.add_parser("schema-check")
    schema_check_parser.add_argument("--registry", required=True)
    schema_check_parser.set_defaults(func=schema_check_command)

    reference_check_parser = subparsers.add_parser("reference-check")
    reference_check_parser.add_argument("--references", required=True)
    reference_check_parser.set_defaults(func=reference_check_command)

    router_eval_parser = subparsers.add_parser("router-eval")
    router_eval_parser.add_argument("--eval", required=True)
    router_eval_parser.add_argument("--registry", required=True)
    router_eval_parser.add_argument("--bundles", default="bundles/index.json")
    router_eval_parser.add_argument("--overlap-groups")
    router_eval_parser.add_argument("--max-skills", type=int, default=8)
    router_eval_parser.set_defaults(func=router_eval_command)

    reindex_parser = subparsers.add_parser("reindex")
    reindex_parser.add_argument("--registry", required=True)
    reindex_parser.set_defaults(func=reindex_command)

    return parser


def add_provenance_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--source-url")
    parser.add_argument("--source-usage", choices=sorted(SOURCE_USAGE_VALUES))
    parser.add_argument("--author")
    parser.add_argument("--license")
    parser.add_argument("--reference")
    parser.add_argument("--collected-by")


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
