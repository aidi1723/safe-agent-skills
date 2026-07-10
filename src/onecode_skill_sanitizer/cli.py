from __future__ import annotations

import argparse
import json
import math
import re
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from . import __version__
from .bulk import claude_skills_candidate_action as claude_skills_candidate_action
from .bulk import claude_skills_candidate_sort_key as claude_skills_candidate_sort_key
from .bulk import compact_claude_skills_candidate as compact_claude_skills_candidate
from .bulk import most_common as most_common
from .bulk import build_claude_skills_bulk_plan as build_claude_skills_bulk_plan
from .bulk import claude_skills_bulk_plan_command as claude_skills_bulk_plan_command
from .bulk import slugify_skill_part as slugify_skill_part
from .bulk import humanize_candidate_name as humanize_candidate_name
from .bulk import local_draft_skill_name as local_draft_skill_name
from .bulk import build_claude_skills_draft_skill_text as build_claude_skills_draft_skill_text
from .bulk import build_claude_skills_draft_manifest as build_claude_skills_draft_manifest
from .bulk import build_claude_skills_bulk_drafts as _bulk_build_claude_skills_bulk_drafts
from .bulk import claude_skills_bulk_draft_command as claude_skills_bulk_draft_command
from .bulk import STOPWORD_SKILL_TOKENS as STOPWORD_SKILL_TOKENS
from .bulk import skill_name_tokens as skill_name_tokens
from .bulk import load_draft_skill_names as load_draft_skill_names
from .bulk import trusted_registry_skill_names as trusted_registry_skill_names
from .bulk import registry_skill_statuses as registry_skill_statuses
from .bulk import find_claude_skills_overlap as find_claude_skills_overlap
from .bulk import assess_claude_skills_candidate as assess_claude_skills_candidate
from .bulk import build_claude_skills_bulk_assessment as build_claude_skills_bulk_assessment
from .bulk import claude_skills_bulk_assess_command as claude_skills_bulk_assess_command
from .candidates import retrieve_scenario_candidates
from .compatibility import build_canonical_content_hash
from .compatibility import build_route_id
from .compatibility import build_route_identity_payload
from .compatibility import to_legacy_v1
from .compiler import compile_execution_graph
from .composer import compose_scenarios
from .contracts import contract_coverage
from .intent import decompose_task, normalize_task
from .paths import resolve_project_asset_path
from .references import validate_external_references
from .rendering import markdown_safe_line as markdown_safe_line
from .rendering import project_legacy_contracts
from .rendering import render_task_pack_markdown
from .rendering import render_task_pack_v2_markdown
from .router_eval_v2 import DatasetValidationError
from .router_eval_v2 import EvaluatorError
from .router_eval_v2 import evaluate_router_v2
from .router_eval_v2 import load_eval_dataset_v2
from .router import CAPABILITY_SKILL_PREFERENCES
from .router import PIPELINE_STAGE_ORDER
from .router import build_task_profile, capability_skill_names, parse_invariant_capabilities
from .router import pipeline_stage_for_skill
from .router import route_mesh_task, route_scenario_task
from .scanner import highest_risk, line_findings, read_text_files, scan_text, source_hash
from .taxonomy import classify_skill, taxonomy_from_manifest
from .validation import SOURCE_DEFAULT_USAGE_BY_TYPE
from .validation import SOURCE_PROVENANCE_FIELDS
from .validation import SOURCE_USAGE_VALUES
from .validation import add_issue
from .validation import manifest_sha256
from .validation import seal_manifest
from .validation import text_sha256
from .validation import validate_manifest_schema
from .validation import validate_registry_index_schema
from .validation import validate_sanitization_report_schema
from .validation import validate_verify_report_schema



def build_claude_skills_bulk_drafts(
    candidate_map_path: Path,
    out_dir: Path,
    batch_size: int,
    batch_index: int,
) -> dict:
    return _bulk_build_claude_skills_bulk_drafts(
        candidate_map_path,
        out_dir,
        batch_size,
        batch_index,
        write_json,
    )

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
    return seal_manifest(
        {
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
    )


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
    report["hashes"]["manifest_sha256"] = manifest["hashes"]["manifest_sha256"]
    report["summary"] = dict(scan_report["summary"])
    report["summary"]["removed_fragment_count"] = len(removed)
    report["removed_fragments"] = removed

    (out_dir / "SKILL.md").write_text(sanitized_text, encoding="utf-8")
    write_json(out_dir / "skill.json", manifest)
    write_json(out_dir / "SANITIZATION_REPORT.json", report)
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
    entry = {
        "name": manifest["name"],
        "status": manifest["status"],
        "risk_level": manifest["risk_level"],
        "taxonomy": manifest["taxonomy"],
        "source": manifest["source"],
        "hashes": manifest["hashes"],
        "registry_path": registry_path.as_posix(),
    }
    if isinstance(manifest.get("contract"), dict):
        entry["contract"] = manifest["contract"]
    return entry


def seal_manifest_file(manifest_path: Path) -> dict:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    seal_manifest(manifest)
    write_json(manifest_path, manifest)
    return manifest


def seal_registry_manifests(registry_dir: Path) -> None:
    for manifest_path in sorted(registry_dir.glob("*/*/skill.json")):
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        issues: list[dict] = []
        validate_manifest_schema(manifest, manifest_path, issues)
        sealable_issue_ids = {"schema-missing-manifest-hash", "schema-manifest-hash-mismatch"}
        if all(issue["id"] in sealable_issue_ids for issue in issues):
            seal_manifest(manifest)
            write_json(manifest_path, manifest)
            report_path = manifest_path.parent / "SANITIZATION_REPORT.json"
            if report_path.exists():
                report = json.loads(report_path.read_text(encoding="utf-8"))
                report.setdefault("hashes", {})["manifest_sha256"] = manifest["hashes"]["manifest_sha256"]
                write_json(report_path, report)


def write_registry_index(registry_dir: Path, seal_manifests: bool = False) -> dict:
    if seal_manifests:
        seal_registry_manifests(registry_dir)
    index = build_registry_index(registry_dir)
    registry_dir.mkdir(parents=True, exist_ok=True)
    write_json(registry_dir / "index.json", index)
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
    payload = json.loads(index_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("registry index must be an object")
    skills = payload.get("skills")
    if not isinstance(skills, list):
        raise ValueError("registry index skills must be an array")
    if any(not isinstance(entry, dict) for entry in skills):
        raise ValueError("registry index skill entries must be objects")
    return payload


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
    index = load_registry_index(resolve_project_asset_path(args.registry))
    print(json.dumps(index, indent=2, sort_keys=True))
    return 0


def inspect_command(args: argparse.Namespace) -> int:
    registry_dir = resolve_project_asset_path(args.registry)
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
    registry_dir = resolve_project_asset_path(args.registry)
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


TASK_PROFILE_CATEGORY_VALUES = {
    "design",
    "code",
    "engineering",
    "security",
    "office",
    "execution",
    "research",
    "data",
    "business",
    "content",
    "commerce",
    "media",
    "compliance",
    "ai",
    "vertical",
}


def task_taxonomy_from_profile(task: str, fallback_taxonomy: dict) -> dict:
    profile = build_task_profile(task)
    primary_domain = profile.get("primary_domain", "")
    if primary_domain not in TASK_PROFILE_CATEGORY_VALUES:
        return fallback_taxonomy
    task_type = str(profile.get("task_type", "")).replace("-", "_")
    artifact_types = profile.get("artifact_types", [])
    return {
        "category": primary_domain,
        "subcategory": f"{primary_domain}.{task_type}",
        "task_intent": f"route {task_type} tasks with verified skill selection",
        "artifact_type": artifact_types[0] if artifact_types else "workflow",
        "collection_priority": "P0",
    }


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
    item = {
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
    if isinstance(manifest.get("contract"), dict):
        item["contract"] = manifest["contract"]
    return item


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
    if not isinstance(payload, dict):
        raise ValueError("bundles index must be an object")
    bundles = payload.get("bundles")
    if not isinstance(bundles, list):
        raise ValueError("bundles index bundles must be an array")
    if any(not isinstance(bundle, dict) for bundle in bundles):
        raise ValueError("bundles index entries must be objects")
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
    if router_context and router_context.get("contract_diagnostics"):
        diagnostics = router_context["contract_diagnostics"]
        lines.extend(
            [
                "Contract diagnostics:",
                f"- status: {diagnostics.get('status', 'unknown')}",
                f"- graph mode: {diagnostics.get('graph_mode', 'unknown')}",
                f"- missing preconditions: {diagnostics.get('missing_precondition_count', 0)}",
                f"- missing ordering: {diagnostics.get('missing_ordering_count', 0)}",
                f"- collisions: {diagnostics.get('collision_count', 0)}",
            ]
        )
        for item in diagnostics.get("missing_preconditions", []):
            lines.append(f"- missing: {item.get('skill', '')} requires {item.get('artifact', '')}")
        for item in diagnostics.get("missing_ordering", []):
            lines.append(f"- ordering: {item.get('skill', '')} requires after {item.get('requires_after', '')}")
        for item in diagnostics.get("collisions", []):
            lines.append(f"- collision: {item.get('skill', '')} conflicts with {item.get('conflicts_with', '')}")
        lines.append("")
    if router_context and router_context.get("pipeline_plan"):
        plan = router_context["pipeline_plan"]
        mode = str(plan.get("mode", "method_only")).replace("_", "-")
        lines.extend(
            [
                "Pipeline plan:",
                f"- id: {plan.get('id', 'general')}",
                f"- mode: {mode}",
                f"- boundary: {plan.get('runtime_boundary', 'Skills provide method only; host runtime controls permissions.')}",
            ]
        )
        for stage in plan.get("stages", []):
            gate = stage.get("gate", {})
            evidence_template = gate.get("evidence_template", {})
            evidence_fields = ", ".join(evidence_template.get("required_fields", []))
            skills_text = ", ".join(stage.get("skills", [])) or "none"
            lines.extend(
                [
                    f"- stage {stage.get('name', stage.get('id', ''))}:",
                    f"  purpose: {stage.get('purpose', 'Not specified.')}",
                    f"  skills: {skills_text}",
                    f"  gate: {gate.get('condition', 'Not specified.')} "
                    f"(failure action: {gate.get('failure_action', 'not_specified')})",
                ]
            )
            if evidence_fields:
                lines.append(f"  evidence fields: {evidence_fields}")
        lines.append("")
    if router_context and router_context.get("acceptance_criteria"):
        lines.extend(["Acceptance criteria:"])
        for criterion in router_context["acceptance_criteria"]:
            lines.append(f"- {criterion}")
        lines.append("")
    if router_context and router_context.get("completion_contract"):
        contract = router_context["completion_contract"]
        lines.extend(["Completion contract:"])
        lines.append("- final response must include: " + ", ".join(contract.get("final_response_must_include", [])))
        lines.append("- stop conditions: " + ", ".join(contract.get("stop_conditions", [])))
        lines.append("- evidence requirements: " + ", ".join(contract.get("evidence_requirements", [])))
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


def build_acceptance_criteria(task_pack_context: dict) -> list[str]:
    criteria = [
        "Record selected trusted skills before execution.",
        "Preserve the method-only safety boundary for all runtime actions.",
    ]
    if task_pack_context.get("selected_scenario", {}).get("id"):
        criteria.append("Record selected scenario and why it matched the task.")
    if task_pack_context.get("pipeline_plan"):
        criteria.append("Complete every pipeline stage gate or record the failed gate.")
    if task_pack_context.get("coverage"):
        criteria.append("Record required capability coverage and missing required capabilities.")
    if task_pack_context.get("invariant_capabilities"):
        criteria.append("Preserve invariant capabilities throughout execution.")
    if task_pack_context.get("pipeline_plan", {}).get("approval_gates"):
        criteria.append("Stop before approval-required runtime actions until the host runtime or operator approves them.")
    criteria.append("Record verification evidence before claiming completion.")
    criteria.append("List unresolved assumptions and residual risks in the handoff.")
    return list(dict.fromkeys(criteria))


def build_completion_contract(task_pack_context: dict) -> dict:
    stop_conditions = [
        "required input missing",
        "registry verification failed",
        "approval-required runtime action blocked",
        "required capability missing and no fallback exists",
    ]
    quality = task_pack_context.get("selection_quality", {})
    if quality.get("low_confidence"):
        stop_conditions.append("low-confidence route requires explicit residual-risk handoff")
    if quality.get("missing_required_count", 0):
        stop_conditions.append("missing required capabilities must be reported before completion")
    return {
        "final_response_must_include": [
            "selected_scenario",
            "selected_skills",
            "verification_performed",
            "unresolved_assumptions",
            "residual_risks",
        ],
        "stop_conditions": list(dict.fromkeys(stop_conditions)),
        "evidence_requirements": [
            "commands or checks run",
            "schema or format checks",
            "source or provenance checks when relevant",
            "failed or unavailable checks",
        ],
    }


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
    skills = [project_legacy_contracts(load_skill_pack_item(registry_dir, entry)) for entry in selected]
    bundles = []
    if include_bundles:
        bundle_index_path = bundles_path or Path("bundles/index.json")
        bundles = select_bundles_for_task(registry_dir, bundle_index_path, task, skills)
    if router_mode == "mesh":
        bundle_index_path = bundles_path or Path("bundles/index.json")
        bundles_index = load_bundles_index(bundle_index_path)
        selected_by_name = {skill["name"]: skill for skill in skills}
        for skill in project_legacy_contracts(load_trusted_skill_pack_items(registry_dir)):
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
        routed_task_taxonomy = task_taxonomy_from_profile(task, task_taxonomy)
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
            "task_taxonomy": routed_task_taxonomy,
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
            "contract_diagnostics": routed["contract_diagnostics"],
            "pipeline_plan": routed["pipeline_plan"],
            "invariant_capabilities": routed["invariant_capabilities"],
            "pruned_skills": routed["pruned_skills"],
            "selection_quality": routed["selection_quality"],
            "selection_trace": routed["selection_trace"],
        }
        task_pack["acceptance_criteria"] = build_acceptance_criteria(task_pack)
        task_pack["completion_contract"] = build_completion_contract(task_pack)
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
        routed_task_taxonomy = task_taxonomy_from_profile(task, task_taxonomy)
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
            "task_taxonomy": routed_task_taxonomy,
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
            "pipeline_plan": routed["pipeline_plan"],
            "contract_diagnostics": routed["contract_diagnostics"],
            "selection_explanations": routed["selection_explanations"],
            "selection_quality": routed["selection_quality"],
            "selection_trace": routed["selection_trace"],
        }
        task_pack["acceptance_criteria"] = build_acceptance_criteria(task_pack)
        task_pack["completion_contract"] = build_completion_contract(task_pack)
        task_pack["agent_instructions"] = build_agent_instructions(task, skills, bundles, task_pack)
        return task_pack
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
    }
    task_pack["acceptance_criteria"] = build_acceptance_criteria(task_pack)
    task_pack["completion_contract"] = build_completion_contract(task_pack)
    task_pack["agent_instructions"] = build_agent_instructions(task, skills, bundles, task_pack)
    return task_pack


def build_task_pack_v2(
    registry_dir: Path,
    task: str,
    bundles_path: Path,
    max_skills: int | None = None,
    invariants: list[str] | None = None,
    strategy: str = "balanced",
    overlap_groups_path: Path | None = None,
) -> dict:
    if not task.strip():
        raise ValueError("task must not be empty")
    verification = verify_registry(registry_dir)
    if verification["status"] != "ok":
        raise SystemExit("registry verification failed; refusing to build task pack")

    bundles_index = load_bundles_index(bundles_path)
    overlap_groups = None
    overlap_policy = "not_configured"
    if overlap_groups_path is not None:
        overlap_groups = load_overlap_groups(overlap_groups_path)
        overlap_validation = validate_overlap_groups(
            registry_dir,
            overlap_groups_path,
            overlap_groups,
        )
        if overlap_validation["issues"]:
            raise ValueError("overlap groups validation failed")
        overlap_policy = "validated_not_applied"
    trusted_names = trusted_skill_names(registry_dir)
    normalized_task = normalize_task(task)
    intent_graph = decompose_task(task)
    candidates = retrieve_scenario_candidates(intent_graph, bundles_index, trusted_names)
    composition = compose_scenarios(intent_graph, candidates, bundles_index, trusted_names)
    execution_graph = compile_execution_graph(intent_graph, composition, bundles_index, trusted_names)
    invariant_capabilities = parse_invariant_capabilities(invariants)
    invariant_skill_names = capability_skill_names(invariant_capabilities, trusted_names)

    trusted_items = {
        item["name"]: item
        for item in load_trusted_skill_pack_items(registry_dir)
        if item["name"] in trusted_names
    }
    stage_by_skill = {
        name: _v2_skill_stage(item)
        for name, item in trusted_items.items()
    }
    host_action_by_skill = {
        name: _v2_skill_host_action(item)
        for name, item in trusted_items.items()
    }
    execution_graph = _normalize_v2_graph_stages(
        execution_graph,
        stage_by_skill,
        host_action_by_skill,
    )
    execution_graph = _extend_v2_graph_with_invariants(
        execution_graph,
        invariant_capabilities,
        invariant_skill_names,
        stage_by_skill,
        host_action_by_skill,
    )
    required_skill_names = []
    for node in execution_graph["nodes"]:
        skill_name = node["skill"]
        if skill_name not in required_skill_names:
            required_skill_names.append(skill_name)
    selected_skills = [trusted_items[name] for name in required_skill_names if name in trusted_items]
    missing_graph_skills = [name for name in required_skill_names if name not in trusted_items]
    if missing_graph_skills:
        execution_graph = dict(execution_graph)
        execution_graph["status"] = "blocked"
        execution_graph["acyclic"] = False
        execution_graph["reason_codes"] = sorted(
            set(execution_graph.get("reason_codes", [])) | {"missing_trusted_skill_pack_item"}
        )
        execution_graph["details"] = [
            f"missing trusted skill pack item: {name}" for name in missing_graph_skills
        ]

    selected_scenarios = [
        {
            "scenario_id": selection.scenario_id,
            "intent_ids": list(selection.intent_ids),
            "score": selection.score,
            "score_breakdown": {
                "deterministic_signal": selection.score,
                "deterministic_score": selection.deterministic_score,
            },
        }
        for selection in composition.selections
    ]
    capability_resolution = _build_v2_capability_resolution(
        bundles_index,
        selected_scenarios,
        set(required_skill_names),
        invariant_capabilities,
        stage_by_skill,
    )
    routing_status = _routing_status(composition.status, capability_resolution, execution_graph)
    provider = {
        "requested": "none",
        "used": "none",
        "fallback_reason": "semantic_provider_not_enabled_in_first_milestone",
    }
    host_protocol = {
        "mode": "method_only",
        "runtime_boundary": "The host runtime controls permissions and execution.",
        "node_statuses": [
            "pending",
            "ready",
            "running",
            "waiting_approval",
            "completed",
            "failed",
            "blocked",
            "skipped",
        ],
    }
    route_inputs = build_route_identity_payload(
        current=normalized_task.current,
        history=normalized_task.history,
        stale=normalized_task.stale,
        stale_policy=normalized_task.stale_policy,
        invariants=invariants or [],
        capabilities=sorted(
            {
                artifact
                for intent in intent_graph.intents
                for artifact in intent.required_artifacts
            }
        ),
        strategy=strategy,
        provider_identifier=provider["used"],
        catalog_content_hash=_json_asset_content_hash(registry_dir / "index.json"),
        bundle_content_hash=_json_asset_content_hash(bundles_path),
        overlap_content_hash=(
            build_canonical_content_hash(overlap_groups) if overlap_groups is not None else "none"
        ),
        router_version="hybrid-router-v2-first-milestone",
        package_version=__version__,
    )
    payload = {
        "schema_version": 2,
        "generated_at": utc_now(),
        "route_id": build_route_id(route_inputs),
        "routing_mode": "hybrid",
        "routing_status": routing_status,
        "provider": provider,
        "normalized_task": normalized_task.to_json(),
        "intent_graph": intent_graph.to_json(),
        "scenario_candidates": [candidate.to_json() for candidate in candidates],
        "selected_scenarios": selected_scenarios,
        "uncovered_intents": list(composition.uncovered_intents),
        "selected_skills": selected_skills,
        "capability_resolution": capability_resolution,
        "execution_graph": execution_graph,
        "host_execution_protocol": host_protocol,
        "routing_metrics": {
            "intent_count": len(intent_graph.intents),
            "candidate_count": len(candidates),
            "selected_scenario_count": len(selected_scenarios),
            "required_skill_count": len(required_skill_names),
            "selected_skill_count": len(selected_skills),
            "optional_skill_limit": max(0, max_skills or 0),
            "optional_skills_selected": 0,
            "required_skills_omitted": missing_graph_skills,
            "overlap_policy": overlap_policy,
        },
        "registry_verification": verification,
        "compatibility": {},
    }
    payload["compatibility"] = {
        "legacy_schema_version": 1,
        "compatibility_loss": to_legacy_v1(payload)["compatibility_loss"],
    }
    return payload


def _build_v2_capability_resolution(
    bundles_index: dict,
    selected_scenarios: list[dict],
    selected_skill_names: set[str],
    invariant_capabilities: list[str] | None = None,
    stage_by_skill: dict[str, str] | None = None,
) -> dict:
    bundles = {bundle["id"]: bundle for bundle in bundles_index.get("bundles", []) if isinstance(bundle, dict)}
    capabilities = []
    for selection in selected_scenarios:
        scenario_id = selection["scenario_id"]
        bundle = bundles.get(scenario_id, {})
        for capability in bundle.get("required_capabilities", []):
            preferred = capability.get("preferred_skills", [])
            matched = [name for name in preferred if name in selected_skill_names]
            capabilities.append(
                {
                    "scenario_id": scenario_id,
                    "capability": capability.get("id", ""),
                    "required": bool(capability.get("required")),
                    "status": "covered" if matched else "missing",
                    "skills": matched,
                }
            )
    for capability in invariant_capabilities or []:
        matched = [
            name
            for name in CAPABILITY_SKILL_PREFERENCES.get(capability, [])
            if name in selected_skill_names
        ][:1]
        capabilities.append(
            {
                "scenario_id": "",
                "capability": capability,
                "required": True,
                "status": "covered" if matched else "missing",
                "skills": matched,
                "source": "invariant",
                "stage": stage_by_skill.get(matched[0], "") if matched and stage_by_skill else "",
            }
        )
    missing_required = [
        item for item in capabilities if item["required"] and item["status"] == "missing"
    ]
    return {
        "status": "complete" if not missing_required else "incomplete",
        "capabilities": capabilities,
        "missing_required_count": len(missing_required),
    }


def _extend_v2_graph_with_invariants(
    execution_graph: dict,
    invariant_capabilities: list[str],
    invariant_skill_names: list[str],
    stage_by_skill: dict[str, str],
    host_action_by_skill: dict[str, bool],
) -> dict:
    graph = dict(execution_graph)
    nodes = [dict(node) for node in execution_graph.get("nodes", [])]
    edges = [dict(edge) for edge in execution_graph.get("edges", [])]
    capability_by_skill = {
        skill_name: capability
        for capability in invariant_capabilities
        for skill_name in CAPABILITY_SKILL_PREFERENCES.get(capability, [])
        if skill_name in invariant_skill_names
    }
    if not capability_by_skill:
        return graph

    original_node_ids = {node["id"] for node in nodes}
    intent_ids = sorted(
        {
            intent_id
            for node in nodes
            for intent_id in node.get("intent_ids", [])
            if isinstance(intent_id, str)
        }
    )
    rank_by_stage = {stage: rank for rank, stage in enumerate(PIPELINE_STAGE_ORDER)}
    invariant_specs = sorted(
        [
            (
                stage_by_skill.get(skill_name, pipeline_stage_for_skill(skill_name)),
                skill_name,
                capability_by_skill[skill_name],
            )
            for skill_name in invariant_skill_names
        ],
        key=lambda item: (rank_by_stage.get(item[0], len(rank_by_stage)), item[1]),
    )
    invariant_ids_by_stage: dict[str, list[str]] = {}
    for stage, skill_name, capability in invariant_specs:
        node_id = f"invariant:{capability}:{skill_name}"
        nodes.append(
            {
                "id": node_id,
                "intent_ids": intent_ids,
                "scenario_ids": [],
                "skill": skill_name,
                "stage": stage,
                "host_action": host_action_by_skill.get(skill_name, False),
                "invariant_capability": capability,
            }
        )
        invariant_ids_by_stage.setdefault(stage, []).append(node_id)

    original_nodes = {node["id"]: node for node in nodes if node["id"] in original_node_ids}
    graph_roots = sorted(original_node_ids - {edge["to"] for edge in edges})
    graph_terminals = sorted(original_node_ids - {edge["from"] for edge in edges})
    previous_last = ""
    for stage in PIPELINE_STAGE_ORDER:
        stage_ids = invariant_ids_by_stage.get(stage, [])
        if not stage_ids:
            continue
        for source, target in zip(stage_ids, stage_ids[1:]):
            edges.append({"from": source, "to": target, "type": "invariant_safeguard"})
        if previous_last:
            edges.append({"from": previous_last, "to": stage_ids[0], "type": "invariant_safeguard"})
        stage_rank = rank_by_stage[stage]
        crossing_edges = [
            edge
            for edge in edges
            if edge["from"] in original_nodes
            and edge["to"] in original_nodes
            and rank_by_stage[original_nodes[edge["from"]]["stage"]] < stage_rank
            <= rank_by_stage[original_nodes[edge["to"]]["stage"]]
        ]
        if crossing_edges:
            for edge in crossing_edges:
                edges.append({"from": edge["from"], "to": stage_ids[0], "type": "invariant_safeguard"})
                edges.append({"from": stage_ids[-1], "to": edge["to"], "type": "invariant_safeguard"})
        elif stage_rank == 0:
            edges.extend(
                {"from": stage_ids[-1], "to": root, "type": "invariant_safeguard"}
                for root in graph_roots
            )
        elif all(
            rank_by_stage[original_nodes[node_id]["stage"]] < stage_rank
            for node_id in original_node_ids
        ):
            edges.extend(
                {"from": terminal, "to": stage_ids[0], "type": "invariant_safeguard"}
                for terminal in graph_terminals
            )
        previous_last = stage_ids[-1]

    graph["nodes"] = nodes
    graph["edges"] = sorted(
        {
            (edge["from"], edge["to"], edge["type"])
            for edge in edges
        }
    )
    graph["edges"] = [
        {"from": source, "to": target, "type": edge_type}
        for source, target, edge_type in graph["edges"]
    ]
    return graph


def _v2_skill_stage(skill: dict) -> str:
    contract = skill.get("contract")
    if isinstance(contract, dict) and contract.get("stage_hint") in PIPELINE_STAGE_ORDER:
        return contract["stage_hint"]
    return pipeline_stage_for_skill(skill.get("name", ""))


def _v2_skill_host_action(skill: dict) -> bool:
    contract = skill.get("contract")
    return bool(contract.get("approval_classes")) if isinstance(contract, dict) else False


def _normalize_v2_graph_stages(
    execution_graph: dict,
    stage_by_skill: dict[str, str],
    host_action_by_skill: dict[str, bool],
) -> dict:
    graph = dict(execution_graph)
    nodes = [
        {
            **node,
            "stage": stage_by_skill.get(node.get("skill", ""), node.get("stage", "production")),
            "host_action": host_action_by_skill.get(node.get("skill", ""), False),
        }
        for node in execution_graph.get("nodes", [])
    ]
    rank_by_stage = {stage: rank for rank, stage in enumerate(PIPELINE_STAGE_ORDER)}
    original_rank = {node["id"]: rank for rank, node in enumerate(nodes)}
    nodes_by_intent: dict[str, list[dict]] = {}
    for node in nodes:
        intent_ids = node.get("intent_ids", [])
        if len(intent_ids) == 1:
            nodes_by_intent.setdefault(intent_ids[0], []).append(node)
    edges = [
        dict(edge)
        for edge in execution_graph.get("edges", [])
        if edge.get("type") != "scenario_order"
    ]
    for intent_id in sorted(nodes_by_intent):
        ordered = sorted(
            nodes_by_intent[intent_id],
            key=lambda node: (
                rank_by_stage.get(node["stage"], len(rank_by_stage)),
                original_rank[node["id"]],
                node["id"],
            ),
        )
        edges.extend(
            {"from": source["id"], "to": target["id"], "type": "scenario_order"}
            for source, target in zip(ordered, ordered[1:])
        )
    graph["nodes"] = nodes
    graph["edges"] = sorted(
        (
            {"from": source, "to": target, "type": edge_type}
            for source, target, edge_type in {
                (edge["from"], edge["to"], edge["type"])
                for edge in edges
            }
        ),
        key=lambda edge: (edge["from"], edge["to"], edge["type"]),
    )
    return graph


def _routing_status(
    composition_status: str,
    capability_resolution: dict,
    execution_graph: dict,
) -> str:
    reason_codes = set(execution_graph.get("reason_codes", []))
    composition_only_block = reason_codes == {"incomplete_composition"} and composition_status != "complete"
    if execution_graph.get("status") == "blocked" and not composition_only_block:
        return "blocked"
    if (
        composition_status != "complete"
        or capability_resolution.get("status") != "complete"
        or capability_resolution.get("missing_required_count", 0) > 0
    ):
        return "incomplete"
    return "complete" if execution_graph.get("status") == "ready" else "blocked"


def _json_asset_content_hash(path: Path) -> str:
    return build_canonical_content_hash(json.loads(path.read_text(encoding="utf-8")))


def task_pack_command(args: argparse.Namespace) -> int:
    if args.schema_version == 2:
        return _run_v2_task_pack_command(args)
    else:
        task_pack = build_task_pack(
            resolve_project_asset_path(args.registry),
            args.task,
            args.top,
            args.include_review_required,
            args.include_bundles,
            resolve_project_asset_path(args.bundles) if args.bundles else None,
            args.router,
            args.max_skills,
            args.invariants if getattr(args, "invariants", None) else None,
            getattr(args, "strategy", "balanced"),
            resolve_project_asset_path(args.overlap_groups) if getattr(args, "overlap_groups", None) else None,
        )
        task_pack = project_legacy_contracts(task_pack)
    if args.format == "markdown":
        print(render_task_pack_v2_markdown(task_pack) if args.schema_version == 2 else render_task_pack_markdown(task_pack))
    else:
        print(json.dumps(task_pack, indent=2, sort_keys=True))
    return 0


def smart_command(args: argparse.Namespace) -> int:
    if args.schema_version == 2:
        return _run_v2_task_pack_command(args)
    else:
        task_pack = build_task_pack(
            resolve_project_asset_path(args.registry),
            args.task,
            args.max_skills,
            False,
            True,
            resolve_project_asset_path(args.bundles) if args.bundles else None,
            "mesh",
            args.max_skills,
            args.invariants,
            args.strategy,
            resolve_project_asset_path(args.overlap_groups) if args.overlap_groups else None,
        )
        task_pack = project_legacy_contracts(task_pack)
    if args.format == "markdown":
        print(render_task_pack_markdown(task_pack))
    else:
        print(json.dumps(task_pack, indent=2, sort_keys=True))
    return 0


def _run_v2_task_pack_command(args: argparse.Namespace) -> int:
    try:
        overlap_groups_path = resolve_overlap_groups_path(
            resolve_project_asset_path(args.registry),
            resolve_project_asset_path(args.overlap_groups)
            if getattr(args, "overlap_groups", None)
            else None,
        )
        task_pack = build_task_pack_v2(
            resolve_project_asset_path(args.registry),
            args.task,
            resolve_project_asset_path(args.bundles),
            args.max_skills,
            args.invariants if getattr(args, "invariants", None) else None,
            getattr(args, "strategy", "balanced"),
            overlap_groups_path,
        )
    except (json.JSONDecodeError, OSError, ValueError, SystemExit) as exc:
        error = _safe_v2_error(exc)
        if args.format == "markdown":
            print(
                "\n".join(
                    [
                        "# OneCode Task Pack v2 Error",
                        "",
                        f"- code: `{error['code']}`",
                        f"- message: {error['message']}",
                    ]
                )
            )
        else:
            print(
                json.dumps(
                    {"schema_version": 2, "status": "error", "error": error},
                    indent=2,
                    sort_keys=True,
                )
            )
        return 2
    if args.format == "markdown":
        print(render_task_pack_v2_markdown(task_pack))
    else:
        print(json.dumps(task_pack, indent=2, sort_keys=True))
    return 0


def _safe_v2_error(exc: BaseException) -> dict[str, str]:
    if isinstance(exc, json.JSONDecodeError):
        return {"code": "invalid_json", "message": "A routing asset contains invalid JSON."}
    if isinstance(exc, FileNotFoundError):
        return {"code": "asset_not_found", "message": "A required routing asset was not found."}
    if isinstance(exc, OSError):
        return {"code": "asset_read_error", "message": "A required routing asset could not be read."}
    message = str(exc)
    if "registry verification failed" in message:
        return {
            "code": "registry_verification_failed",
            "message": "Registry verification failed; task pack generation was refused.",
        }
    if isinstance(exc, SystemExit):
        return {"code": "invalid_asset", "message": "A required routing asset is missing or invalid."}
    return {"code": "invalid_input", "message": "Routing input or assets are invalid."}


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

        expected_manifest_hash = manifest.get("hashes", {}).get("manifest_sha256")
        actual_manifest_hash = manifest_sha256(manifest)
        if expected_manifest_hash != actual_manifest_hash:
            tampered_count += 1
            issues.append(
                {
                    "id": "manifest-hash-mismatch",
                    "severity": "critical",
                    "skill": name,
                    "path": manifest_path.as_posix(),
                }
            )

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
    result = verify_registry(resolve_project_asset_path(args.registry))
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
    result = schema_check(resolve_project_asset_path(args.registry))
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["status"] == "ok" else 2


def contract_check_command(args: argparse.Namespace) -> int:
    registry_dir = resolve_project_asset_path(args.registry)
    bundles_path = resolve_project_asset_path(args.bundles)
    try:
        registry_index_path = registry_dir / "index.json"
        try:
            registry = json.loads(registry_index_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            raise ValueError(f"invalid registry index JSON: {registry_index_path}")
        try:
            bundles_index = json.loads(bundles_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            raise ValueError(f"invalid bundles index JSON: {bundles_path}")
        result = contract_coverage(
            registry,
            bundles_index,
            args.scenario,
            registry_root=registry_dir,
        )
    except ValueError as exc:
        print(json.dumps({"status": "error", "error": str(exc)}, indent=2, sort_keys=True, allow_nan=False))
        return 2
    result["minimum_ratio"] = args.minimum_ratio
    result["status"] = "ok" if result["coverage_ratio"] >= args.minimum_ratio else "failed"
    print(json.dumps(result, indent=2, sort_keys=True, allow_nan=False))
    return 0 if result["status"] == "ok" else 2


def reference_check_command(args: argparse.Namespace) -> int:
    result = validate_external_references(resolve_project_asset_path(args.references))
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["status"] == "ok" else 2


def load_router_eval(eval_path: Path) -> dict:
    if not eval_path.exists():
        raise SystemExit(f"missing router eval file: {eval_path}")
    payload = json.loads(eval_path.read_text(encoding="utf-8"))
    schema_version = payload.get("schema_version")
    if schema_version not in {1, 2}:
        raise SystemExit(f"invalid router eval schema_version: {eval_path}")
    if not isinstance(payload.get("cases"), list):
        raise SystemExit(f"invalid router eval cases: {eval_path}")
    if schema_version == 2:
        dataset = payload.get("dataset")
        if not isinstance(dataset, str) or not dataset:
            raise SystemExit(f"invalid router eval dataset: {eval_path}")
        split = payload.get("split")
        if split != "regression":
            raise SystemExit(f"invalid router eval split: {eval_path}")
        case_count = payload.get("case_count")
        if (
            not isinstance(case_count, int)
            or isinstance(case_count, bool)
            or case_count != len(payload["cases"])
        ):
            raise SystemExit(f"invalid router eval case_count: {eval_path}")
        case_ids = [case.get("id") if isinstance(case, dict) else None for case in payload["cases"]]
        invalid_case_id = any(not isinstance(case_id, str) or not case_id for case_id in case_ids)
        if invalid_case_id or len(case_ids) != len(set(case_ids)):
            raise SystemExit(f"invalid router eval unique case id: {eval_path}")
    return payload


ROUTER_EVAL_STRING_LIST_FIELDS = (
    "expected_skills",
    "forbidden_skills",
    "forbidden_skill_prefixes",
    "forbidden_skill_subcategories",
    "expected_trace_selected",
    "expected_trace_pruned",
    "expected_trace_required",
    "expected_trace_reason_codes",
)
ROUTER_EVAL_OPTIONAL_STRING_FIELDS = (
    "expected_scenario",
    "expected_task_type",
)
ROUTER_EVAL_ROUTER_VALUES = {"scenario", "mesh"}
ROUTER_EVAL_STRATEGY_VALUES = {"fast", "balanced", "deep"}


def validate_router_eval_case(case: dict) -> list[dict]:
    issues = []
    router_mode = case.get("router", "scenario")
    if not isinstance(router_mode, str):
        issues.append(
            {
                "id": "router-eval-invalid-case-field",
                "field": "router",
                "expected": "scenario or mesh",
                "actual": type(router_mode).__name__,
            }
        )
    strategy = case.get("strategy", "balanced")
    if not isinstance(strategy, str) or strategy not in ROUTER_EVAL_STRATEGY_VALUES:
        issues.append(
            {
                "id": "router-eval-invalid-case-field",
                "field": "strategy",
                "expected": "fast, balanced, or deep",
                "actual": type(strategy).__name__,
            }
        )
    invariants = case.get("invariants")
    if invariants is not None:
        invalid_invariants = not isinstance(invariants, (str, list)) or (
            isinstance(invariants, list) and any(not isinstance(item, str) for item in invariants)
        )
        if invalid_invariants:
            issues.append(
                {
                    "id": "router-eval-invalid-case-field",
                    "field": "invariants",
                    "expected": "string or array of strings",
                    "actual": type(invariants).__name__,
                }
            )
    for field in ROUTER_EVAL_OPTIONAL_STRING_FIELDS:
        value = case.get(field)
        if value is not None and not isinstance(value, str):
            issues.append(
                {
                    "id": "router-eval-invalid-case-field",
                    "field": field,
                    "expected": "string",
                    "actual": type(value).__name__,
                }
            )
    for field in ROUTER_EVAL_STRING_LIST_FIELDS:
        value = case.get(field, [])
        if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
            issues.append(
                {
                    "id": "router-eval-invalid-case-field",
                    "field": field,
                    "expected": "array of strings",
                    "actual": type(value).__name__,
                }
            )
    max_skill_count = case.get("max_skill_count")
    if max_skill_count is not None and (
        not isinstance(max_skill_count, int) or isinstance(max_skill_count, bool) or max_skill_count < 0
    ):
        issues.append(
            {
                "id": "router-eval-invalid-case-field",
                "field": "max_skill_count",
                "expected": "non-negative integer",
                "actual": type(max_skill_count).__name__,
            }
        )
    return issues


def router_eval_summary_key(value: object, empty_label: str) -> str:
    if isinstance(value, str) and value:
        return value
    return empty_label


def router_eval_empty_bucket() -> dict:
    return {"case_count": 0, "passed_count": 0, "failed_count": 0}


def classify_router_eval_issue(issue: dict, result_context: dict | None = None) -> str:
    issue_id = router_eval_summary_key(issue.get("id"), "unknown-issue")
    context = result_context or {}
    if issue_id == "router-eval-scenario-mismatch":
        expected = issue.get("expected", context.get("expected_scenario"))
        actual = issue.get("actual", context.get("actual_scenario"))
        if not expected and actual:
            return "false_positive"
        if expected and not actual:
            return "false_negative"
        return "route_mismatch"
    if issue_id == "router-eval-missing-skill":
        return "false_negative"
    if issue_id in {
        "router-eval-trace-missing-selected",
        "router-eval-trace-missing-required",
    }:
        return "false_negative"
    if issue_id in {
        "router-eval-forbidden-skill",
        "router-eval-forbidden-skill-prefix",
        "router-eval-forbidden-skill-subcategory",
        "router-eval-max-skill-count-exceeded",
        "router-eval-trace-missing-pruned",
    }:
        return "false_positive"
    if issue_id == "router-eval-trace-missing-reason-code":
        return "route_mismatch"
    if issue_id == "router-eval-task-type-mismatch":
        return "task_type_mismatch"
    if issue_id in {
        "router-eval-count-mismatch",
        "router-eval-invalid-case-field",
        "router-eval-invalid-router",
        "router-eval-missing-task",
    }:
        return "eval_contract"
    return "unclassified"


def annotate_router_eval_issues(issues: list[dict], result_context: dict | None = None) -> list[dict]:
    annotated = []
    for issue in issues:
        item = dict(issue)
        item["classification"] = classify_router_eval_issue(item, result_context)
        annotated.append(item)
    return annotated


def build_router_eval_quality_summary(results: list[dict], top_level_issues: list[dict] | None = None) -> dict:
    by_expected_scenario: dict[str, dict] = {}
    by_actual_scenario: dict[str, dict] = {}
    by_expected_task_type: dict[str, dict] = {}
    by_confidence: dict[str, dict] = {}
    by_issue: dict[str, int] = {}
    by_issue_class: dict[str, int] = {}

    def bump_bucket(target: dict[str, dict], key: str, status: str) -> None:
        bucket = target.setdefault(key, router_eval_empty_bucket())
        bucket["case_count"] += 1
        if status == "ok":
            bucket["passed_count"] += 1
        else:
            bucket["failed_count"] += 1

    def bump_issue(issue: dict) -> None:
        issue_id = router_eval_summary_key(issue.get("id"), "unknown-issue")
        by_issue[issue_id] = by_issue.get(issue_id, 0) + 1
        issue_class = router_eval_summary_key(issue.get("classification"), "unclassified")
        by_issue_class[issue_class] = by_issue_class.get(issue_class, 0) + 1

    for result in results:
        status = result.get("status", "failed")
        bump_bucket(
            by_expected_scenario,
            router_eval_summary_key(result.get("expected_scenario"), "(none)"),
            status,
        )
        bump_bucket(
            by_actual_scenario,
            router_eval_summary_key(result.get("actual_scenario"), "(none)"),
            status,
        )
        bump_bucket(
            by_expected_task_type,
            router_eval_summary_key(result.get("expected_task_type"), "(unspecified)"),
            status,
        )
        bump_bucket(
            by_confidence,
            router_eval_summary_key(result.get("actual_confidence"), "(unknown)"),
            status,
        )
        for issue in result.get("issues", []):
            bump_issue(issue)
    for issue in annotate_router_eval_issues(top_level_issues or []):
        bump_issue(issue)

    failed_count = sum(1 for item in results if item.get("status") != "ok")
    low_confidence_results = [item for item in results if item.get("actual_low_confidence") is True]
    low_confidence_failed_count = sum(1 for item in low_confidence_results if item.get("status") != "ok")
    return {
        "case_count": len(results),
        "passed_count": len(results) - failed_count,
        "failed_count": failed_count,
        "low_confidence_case_count": len(low_confidence_results),
        "low_confidence_passed_count": len(low_confidence_results) - low_confidence_failed_count,
        "low_confidence_failed_count": low_confidence_failed_count,
        "by_expected_scenario": dict(sorted(by_expected_scenario.items())),
        "by_actual_scenario": dict(sorted(by_actual_scenario.items())),
        "by_expected_task_type": dict(sorted(by_expected_task_type.items())),
        "by_confidence": dict(sorted(by_confidence.items())),
        "by_issue": dict(sorted(by_issue.items())),
        "by_issue_class": dict(sorted(by_issue_class.items())),
    }


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
        if isinstance(router_mode, str) and router_mode not in ROUTER_EVAL_ROUTER_VALUES:
            case_issues.append({"id": "router-eval-invalid-router", "router": router_mode})
        case_issues.extend(validate_router_eval_case(case))
        if case_issues:
            results.append(
                {
                    "id": case_id,
                    "status": "failed",
                    "actual_confidence": "",
                    "actual_low_confidence": False,
                    "issues": annotate_router_eval_issues(case_issues),
                }
            )
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
        actual_selection_quality = task_pack.get("selection_quality", {})
        actual_confidence = actual_selection_quality.get("confidence", "")
        actual_low_confidence = actual_selection_quality.get("low_confidence") is True
        actual_skills = [skill["name"] for skill in task_pack.get("skills", [])]
        actual_skill_subcategories = {
            skill["name"]: skill.get("taxonomy", {}).get("subcategory", "") for skill in task_pack.get("skills", [])
        }
        actual_selection_trace = router_eval_trace_summary(task_pack.get("selection_trace", {}))
        expected_scenario = case.get("expected_scenario")
        expected_task_type = case.get("expected_task_type")
        expected_skills = case.get("expected_skills", [])
        forbidden_skills = case.get("forbidden_skills", [])
        forbidden_skill_prefixes = case.get("forbidden_skill_prefixes", [])
        forbidden_skill_subcategories = case.get("forbidden_skill_subcategories", [])
        expected_trace_selected = case.get("expected_trace_selected", [])
        expected_trace_pruned = case.get("expected_trace_pruned", [])
        expected_trace_required = case.get("expected_trace_required", [])
        expected_trace_reason_codes = case.get("expected_trace_reason_codes", [])
        max_skill_count = case.get("max_skill_count")

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
        for skill_name in forbidden_skills:
            if skill_name in actual_skills:
                case_issues.append(
                    {
                        "id": "router-eval-forbidden-skill",
                        "skill": skill_name,
                    }
                )
        for prefix in forbidden_skill_prefixes:
            for skill_name in actual_skills:
                if skill_name.startswith(prefix):
                    case_issues.append(
                        {
                            "id": "router-eval-forbidden-skill-prefix",
                            "prefix": prefix,
                            "skill": skill_name,
                        }
                    )
        for subcategory in forbidden_skill_subcategories:
            for skill_name, actual_subcategory in actual_skill_subcategories.items():
                if actual_subcategory == subcategory:
                    case_issues.append(
                        {
                            "id": "router-eval-forbidden-skill-subcategory",
                            "subcategory": subcategory,
                            "skill": skill_name,
                        }
                    )
        if isinstance(max_skill_count, int) and len(actual_skills) > max_skill_count:
            case_issues.append(
                {
                    "id": "router-eval-max-skill-count-exceeded",
                    "expected_max": max_skill_count,
                    "actual": len(actual_skills),
                }
            )
        for skill_name in expected_trace_selected:
            if skill_name not in actual_selection_trace["selected"]:
                case_issues.append(
                    {
                        "id": "router-eval-trace-missing-selected",
                        "skill": skill_name,
                    }
                )
        for skill_name in expected_trace_required:
            if skill_name not in actual_selection_trace["required"]:
                case_issues.append(
                    {
                        "id": "router-eval-trace-missing-required",
                        "skill": skill_name,
                    }
                )
        for skill_name in expected_trace_pruned:
            if skill_name not in actual_selection_trace["pruned"]:
                case_issues.append(
                    {
                        "id": "router-eval-trace-missing-pruned",
                        "skill": skill_name,
                    }
                )
        for reason_code in expected_trace_reason_codes:
            if reason_code not in actual_selection_trace["reason_codes"]:
                case_issues.append(
                    {
                        "id": "router-eval-trace-missing-reason-code",
                        "reason_code": reason_code,
                    }
                )

        result_context = {
            "expected_scenario": expected_scenario,
            "actual_scenario": actual_scenario,
            "expected_task_type": expected_task_type,
            "actual_task_type": actual_task_type,
        }
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
                "actual_confidence": actual_confidence,
                "actual_low_confidence": actual_low_confidence,
                "max_skill_count": max_skill_count,
                "actual_skills": actual_skills,
                "actual_selection_trace": actual_selection_trace,
                "issues": annotate_router_eval_issues(case_issues, result_context),
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
        "quality_summary": build_router_eval_quality_summary(results, issues),
        "cases": results,
    }


def router_eval_trace_summary(selection_trace: dict) -> dict:
    candidates = selection_trace.get("candidates", [])
    selected = [
        item.get("name", "")
        for item in candidates
        if item.get("selected") is True and item.get("name")
    ]
    required = [
        item.get("name", "")
        for item in candidates
        if item.get("required") is True and item.get("name")
    ]
    pruned = [
        item.get("name", "")
        for item in selection_trace.get("pruned", [])
        if item.get("name")
    ]
    quality = selection_trace.get("quality", {})
    return {
        "selected_count": selection_trace.get("selected_count", len(selected)),
        "candidate_count": selection_trace.get("candidate_count", len(candidates)),
        "required_skill_count": selection_trace.get("required_skill_count", len(required)),
        "selected": selected,
        "required": required,
        "pruned": pruned,
        "reason_codes": list(quality.get("reason_codes", [])),
    }


def router_eval_command(args: argparse.Namespace) -> int:
    result = run_router_eval(
        eval_path=resolve_project_asset_path(args.eval),
        registry_dir=resolve_project_asset_path(args.registry),
        bundles_path=resolve_project_asset_path(args.bundles),
        overlap_groups_path=resolve_project_asset_path(args.overlap_groups) if args.overlap_groups else None,
        max_skills=args.max_skills,
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["status"] == "ok" else 2


def router_eval_v2_command(args: argparse.Namespace) -> int:
    eval_path = resolve_project_asset_path(args.eval)
    registry_dir = resolve_project_asset_path(args.registry)
    bundles_path = resolve_project_asset_path(args.bundles)
    try:
        bundles_index = load_bundles_index(bundles_path)
        known_scenarios = {
            bundle["id"]
            for bundle in bundles_index.get("bundles", [])
            if isinstance(bundle, dict) and isinstance(bundle.get("id"), str)
        }
        cases = load_eval_dataset_v2(eval_path, known_scenarios)
        result = evaluate_router_v2(
            cases,
            route_builder=lambda case: build_task_pack_v2(
                registry_dir,
                case["task"],
                bundles_path,
            ),
            known_scenarios=known_scenarios,
        )
    except (DatasetValidationError, EvaluatorError, ValueError, OSError, SystemExit) as exc:
        print(
            json.dumps(
                {"status": "error", "error": str(exc)},
                indent=2,
                sort_keys=True,
                allow_nan=False,
            )
        )
        return 2
    print(json.dumps(result, indent=2, sort_keys=True, allow_nan=False))
    return 0


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
    if not isinstance(payload, dict):
        raise ValueError("overlap groups index must be an object")
    groups = payload.get("groups")
    if not isinstance(groups, list):
        raise ValueError("overlap groups must be an array")
    if any(not isinstance(group, dict) for group in groups):
        raise ValueError("overlap group entries must be objects")
    return payload


def validate_overlap_groups(
    registry_dir: Path,
    overlap_path: Path,
    overlap_index: dict | None = None,
) -> dict:
    issues = []
    overlap_index = overlap_index if overlap_index is not None else load_overlap_groups(overlap_path)
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
        if not isinstance(group_id, str) or not group_id.strip():
            issues.append(
                {
                    "id": "overlap-invalid-group-id",
                    "severity": "high",
                    "path": group_path,
                }
            )
            continue
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


def validate_claude_skills_candidate_map(registry_dir: Path, candidate_map_path: Path) -> dict:
    issues = []
    candidate_map = json.loads(candidate_map_path.read_text(encoding="utf-8"))
    candidates = candidate_map.get("candidates", [])
    if not isinstance(candidates, list):
        issues.append(
            {
                "id": "claude-skills-invalid-candidates",
                "severity": "high",
                "path": candidate_map_path.as_posix(),
            }
        )
        candidates = []

    declared_candidate_count = candidate_map.get("candidate_count")
    if declared_candidate_count is not None and declared_candidate_count != len(candidates):
        issues.append(
            {
                "id": "claude-skills-candidate-count-mismatch",
                "severity": "medium",
                "path": candidate_map_path.as_posix(),
                "expected": len(candidates),
                "actual": declared_candidate_count,
            }
        )

    index = load_registry_index(registry_dir)
    statuses = {entry["name"]: entry.get("status") for entry in index["skills"]}
    converted_candidates = [candidate for candidate in candidates if candidate.get("adoption") == "converted"]
    declared_converted_count = candidate_map.get("converted_skill_count")
    if declared_converted_count is not None and declared_converted_count != len(converted_candidates):
        issues.append(
            {
                "id": "claude-skills-converted-count-mismatch",
                "severity": "medium",
                "path": candidate_map_path.as_posix(),
                "expected": len(converted_candidates),
                "actual": declared_converted_count,
            }
        )

    actual_pairs = set()
    for candidate_index, candidate in enumerate(candidates):
        if candidate.get("adoption") != "converted":
            continue
        candidate_name = str(candidate.get("name", ""))
        candidate_path = f"{candidate_map_path.as_posix()}#/candidates/{candidate_index}"
        local_skill = candidate.get("local_skill")
        if not isinstance(local_skill, str) or not local_skill:
            issues.append(
                {
                    "id": "claude-skills-missing-local-skill",
                    "severity": "high",
                    "path": candidate_path,
                    "candidate": candidate_name,
                }
            )
            continue
        actual_pairs.add((candidate_name, local_skill))
        status = statuses.get(local_skill)
        if status is None:
            issues.append(
                {
                    "id": "claude-skills-missing-registry-skill",
                    "severity": "high",
                    "path": candidate_path,
                    "candidate": candidate_name,
                    "skill": local_skill,
                }
            )
        elif status != "trusted":
            issues.append(
                {
                    "id": "claude-skills-non-trusted-local-skill",
                    "severity": "high",
                    "path": candidate_path,
                    "candidate": candidate_name,
                    "skill": local_skill,
                    "status": status,
                }
            )

    declared_converted_skills = candidate_map.get("converted_skills", [])
    if not isinstance(declared_converted_skills, list):
        declared_converted_skills = []
        issues.append(
            {
                "id": "claude-skills-invalid-converted-skills",
                "severity": "high",
                "path": candidate_map_path.as_posix(),
            }
        )
    declared_pairs = {
        (str(item.get("source_candidate", "")), str(item.get("local_skill", "")))
        for item in declared_converted_skills
        if isinstance(item, dict) and item.get("source_candidate") and item.get("local_skill")
    }
    if declared_pairs != actual_pairs:
        issues.append(
            {
                "id": "claude-skills-converted-skills-mismatch",
                "severity": "medium",
                "path": candidate_map_path.as_posix(),
                "expected": len(actual_pairs),
                "actual": len(declared_pairs),
            }
        )

    return {
        "schema_version": 1,
        "status": "failed" if issues else "ok",
        "path": candidate_map_path.as_posix(),
        "candidate_count": len(candidates),
        "converted_count": len(converted_candidates),
        "converted_skill_mapping_count": len(actual_pairs),
        "issues": issues,
    }


def resolve_overlap_groups_path(registry_dir: Path, overlap_path: Path | None) -> Path | None:
    if overlap_path is not None:
        if not overlap_path.is_file():
            raise SystemExit(f"overlap groups file not found: {overlap_path}")
        return overlap_path
    default_path = registry_dir / "overlap-groups.json"
    return default_path if default_path.exists() else None


def maintain_check(
    registry_dir: Path,
    bundles_path: Path | None = None,
    overlap_groups_path: Path | None = None,
    references_path: Path | None = None,
    claude_skills_candidate_map_path: Path | None = None,
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
    claude_skills_candidate_map_validation = None
    if claude_skills_candidate_map_path is not None:
        claude_skills_candidate_map_validation = validate_claude_skills_candidate_map(
            registry_dir,
            claude_skills_candidate_map_path,
        )
        issues.extend(claude_skills_candidate_map_validation["issues"])
    return {
        "schema_version": 1,
        "generated_at": utc_now(),
        "status": "failed" if issues else "ok",
        "registry_verification": registry_verification,
        "bundle_validation": bundle_validation,
        "overlap_validation": overlap_validation,
        "reference_validation": reference_validation,
        "claude_skills_candidate_map_validation": claude_skills_candidate_map_validation,
        "issues": issues,
    }


def maintain_check_command(args: argparse.Namespace) -> int:
    result = maintain_check(
        resolve_project_asset_path(args.registry),
        resolve_project_asset_path(args.bundles) if args.bundles else None,
        resolve_project_asset_path(args.overlap_groups) if args.overlap_groups else None,
        resolve_project_asset_path(args.references) if getattr(args, "references", None) else None,
        resolve_project_asset_path(args.claude_skills_candidate_map)
        if getattr(args, "claude_skills_candidate_map", None)
        else None,
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["status"] == "ok" else 2


def reindex_command(args: argparse.Namespace) -> int:
    write_registry_index(Path(args.registry), seal_manifests=True)
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
    seal_manifest(manifest)
    write_json(skill_dir / "skill.json", manifest)
    report_path = skill_dir / "SANITIZATION_REPORT.json"
    if report_path.exists():
        report = json.loads(report_path.read_text(encoding="utf-8"))
        report["summary"]["status"] = status
        report.setdefault("hashes", {})["manifest_sha256"] = manifest["hashes"]["manifest_sha256"]
        if status == "trusted":
            report["approved_at"] = manifest["approved_at"]
        elif status == "rejected":
            report["rejected_at"] = manifest["rejected_at"]
        elif status == "disabled":
            report["disabled_at"] = manifest["disabled_at"]
        write_json(report_path, report)
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
    task_pack_parser.add_argument("--top", type=positive_int, default=3)
    task_pack_parser.add_argument("--format", choices=["json", "markdown"], default="json")
    task_pack_parser.add_argument("--include-review-required", action="store_true")
    task_pack_parser.add_argument("--include-bundles", action="store_true")
    task_pack_parser.add_argument("--bundles", default="bundles/index.json")
    task_pack_parser.add_argument("--router", choices=["simple", "scenario", "mesh"], default="simple")
    task_pack_parser.add_argument("--max-skills", type=positive_int)
    task_pack_parser.add_argument("--invariants", action="append")
    task_pack_parser.add_argument("--strategy", choices=["fast", "balanced", "deep"], default="balanced")
    task_pack_parser.add_argument("--overlap-groups")
    task_pack_parser.add_argument("--schema-version", type=int, choices=[1, 2], default=2)
    task_pack_parser.set_defaults(func=task_pack_command)

    smart_parser = subparsers.add_parser("smart")
    smart_parser.add_argument("task")
    smart_parser.add_argument("--registry", default="catalog")
    smart_parser.add_argument("--bundles", default="bundles/index.json")
    smart_parser.add_argument("--overlap-groups")
    smart_parser.add_argument("--invariants", action="append")
    smart_parser.add_argument("--strategy", choices=["fast", "balanced", "deep"], default="balanced")
    smart_parser.add_argument("--max-skills", type=positive_int, default=8)
    smart_parser.add_argument("--format", choices=["json", "markdown"], default="json")
    smart_parser.add_argument("--schema-version", type=int, choices=[1, 2], default=2)
    smart_parser.set_defaults(func=smart_command)

    verify_parser = subparsers.add_parser("verify")
    verify_parser.add_argument("--registry", required=True)
    verify_parser.set_defaults(func=verify_command)

    maintain_check_parser = subparsers.add_parser("maintain-check")
    maintain_check_parser.add_argument("--registry", required=True)
    maintain_check_parser.add_argument("--bundles")
    maintain_check_parser.add_argument("--overlap-groups")
    maintain_check_parser.add_argument("--references")
    maintain_check_parser.add_argument("--claude-skills-candidate-map")
    maintain_check_parser.set_defaults(func=maintain_check_command)

    schema_check_parser = subparsers.add_parser("schema-check")
    schema_check_parser.add_argument("--registry", required=True)
    schema_check_parser.set_defaults(func=schema_check_command)

    contract_check_parser = subparsers.add_parser("contract-check")
    contract_check_parser.add_argument("--registry", required=True)
    contract_check_parser.add_argument("--bundles", required=True)
    contract_check_parser.add_argument("--scenario", action="append")
    contract_check_parser.add_argument("--minimum-ratio", type=ratio, default=0.0)
    contract_check_parser.set_defaults(func=contract_check_command)

    reference_check_parser = subparsers.add_parser("reference-check")
    reference_check_parser.add_argument("--references", required=True)
    reference_check_parser.set_defaults(func=reference_check_command)

    router_eval_parser = subparsers.add_parser("router-eval")
    router_eval_parser.add_argument("--eval", required=True)
    router_eval_parser.add_argument("--registry", required=True)
    router_eval_parser.add_argument("--bundles", default="bundles/index.json")
    router_eval_parser.add_argument("--overlap-groups")
    router_eval_parser.add_argument("--max-skills", type=positive_int, default=8)
    router_eval_parser.set_defaults(func=router_eval_command)

    router_eval_v2_parser = subparsers.add_parser("router-eval-v2")
    router_eval_v2_parser.add_argument("--eval", required=True)
    router_eval_v2_parser.add_argument("--registry", default="catalog")
    router_eval_v2_parser.add_argument("--bundles", default="bundles/index.json")
    router_eval_v2_parser.set_defaults(func=router_eval_v2_command)

    claude_skills_bulk_plan_parser = subparsers.add_parser("claude-skills-bulk-plan")
    claude_skills_bulk_plan_parser.add_argument("--candidate-map", required=True)
    claude_skills_bulk_plan_parser.add_argument("--batch-size", type=int, default=50)
    claude_skills_bulk_plan_parser.set_defaults(func=claude_skills_bulk_plan_command)

    claude_skills_bulk_draft_parser = subparsers.add_parser("claude-skills-bulk-draft")
    claude_skills_bulk_draft_parser.add_argument("--candidate-map", required=True)
    claude_skills_bulk_draft_parser.add_argument("--out", required=True)
    claude_skills_bulk_draft_parser.add_argument("--batch-size", type=int, default=50)
    claude_skills_bulk_draft_parser.add_argument("--batch-index", type=int, default=1)
    claude_skills_bulk_draft_parser.set_defaults(func=claude_skills_bulk_draft_command)

    claude_skills_bulk_assess_parser = subparsers.add_parser("claude-skills-bulk-assess")
    claude_skills_bulk_assess_parser.add_argument("--candidate-map", required=True)
    claude_skills_bulk_assess_parser.add_argument("--draft-root", required=True)
    claude_skills_bulk_assess_parser.add_argument("--registry", required=True)
    claude_skills_bulk_assess_parser.set_defaults(func=claude_skills_bulk_assess_command)

    reindex_parser = subparsers.add_parser("reindex")
    reindex_parser.add_argument("--registry", required=True)
    reindex_parser.set_defaults(func=reindex_command)

    return parser


def positive_int(value: str) -> int:
    try:
        parsed = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("must be an integer greater than or equal to 1") from exc
    if parsed < 1:
        raise argparse.ArgumentTypeError("must be greater than or equal to 1")
    return parsed


def ratio(value: str) -> float:
    try:
        parsed = float(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("must be a number from 0 to 1") from exc
    if not math.isfinite(parsed) or parsed < 0 or parsed > 1:
        raise argparse.ArgumentTypeError("must be from 0 to 1")
    return parsed


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
