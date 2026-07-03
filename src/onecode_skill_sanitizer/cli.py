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
FILESYSTEM_SCOPE_VALUES = {"workspace_only", "read_only_workspace", "none"}
NETWORK_SCOPE_VALUES = {"none", "approved_hosts", "onecode_api_only"}
CONTRACT_STAGE_VALUES = {"preflight", "source", "planning", "review", "execution", "verification"}
CONTRACT_CAPABILITY_PATTERN = re.compile(r"^[a-z][a-z0-9_]*(\.[a-z][a-z0-9_]*)+$")
CONTRACT_ARTIFACT_PATTERN = re.compile(r"^[a-z][a-z0-9_]{1,80}$")
DISALLOWED_TOOL_VALUES = {
    "account",
    "browser",
    "connector",
    "filesystem",
    "network",
    "production",
    "shell",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def text_sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def canonical_json_sha256(payload: dict) -> str:
    return text_sha256(json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False))


def manifest_payload_for_hash(manifest: dict) -> dict:
    payload = json.loads(json.dumps(manifest, sort_keys=True))
    hashes = payload.get("hashes")
    if isinstance(hashes, dict):
        hashes.pop("manifest_sha256", None)
    return payload


def manifest_sha256(manifest: dict) -> str:
    return canonical_json_sha256(manifest_payload_for_hash(manifest))


def seal_manifest(manifest: dict) -> dict:
    manifest.setdefault("hashes", {})["manifest_sha256"] = manifest_sha256(manifest)
    return manifest


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
            "pipeline_plan": routed["pipeline_plan"],
            "invariant_capabilities": routed["invariant_capabilities"],
            "pruned_skills": routed["pruned_skills"],
            "selection_quality": routed["selection_quality"],
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
            "pipeline_plan": routed["pipeline_plan"],
            "selection_explanations": routed["selection_explanations"],
            "selection_quality": routed["selection_quality"],
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
        if task_pack.get("pipeline_plan"):
            plan = task_pack["pipeline_plan"]
            lines.extend(
                [
                    "",
                    "## Pipeline Plan",
                    "",
                    f"- id: `{plan.get('id', 'general')}`",
                    f"- mode: `{str(plan.get('mode', 'method_only')).replace('_', '-')}`",
                    f"- source: `{plan.get('source', '')}`",
                    f"- boundary: {plan.get('runtime_boundary', 'Skills provide method only; host runtime controls permissions.')}",
                ]
            )
            for stage in plan.get("stages", []):
                gate = stage.get("gate", {})
                lines.extend(
                    [
                        "",
                        f"### {stage.get('name', stage.get('id', ''))}",
                        "",
                        f"- id: `{stage.get('id', '')}`",
                        f"- purpose: {stage.get('purpose', 'Not specified.')}",
                        f"- skills: {', '.join(f'`{skill}`' for skill in stage.get('skills', [])) or 'none'}",
                        f"- gate: {gate.get('condition', 'Not specified.')}",
                        f"- failure action: `{gate.get('failure_action', 'not_specified')}`",
                    ]
                )
                evidence_template = gate.get("evidence_template", {})
                evidence_fields = evidence_template.get("required_fields", [])
                if evidence_fields:
                    lines.append("- evidence fields: " + ", ".join(f"`{field}`" for field in evidence_fields))
            if plan.get("approval_gates"):
                lines.extend(["", "### Approval Gates", ""])
                for gate in plan["approval_gates"]:
                    required_for = ", ".join(gate.get("required_for", [])) or "not specified"
                    lines.append(
                        f"- stage `{gate.get('stage', '')}` requires approval for {required_for} "
                        f"by `{gate.get('owner', 'host_runtime_or_operator')}`"
                    )
        lines.extend(["", "## Selection Explanations", ""])
        for item in task_pack.get("selection_explanations", []):
            lines.append(f"- `{item['name']}` ({item['type']}, {item['role']}): {item['selection_reason']}")
    if task_pack.get("selection_quality"):
        quality = task_pack["selection_quality"]
        lines.extend(
            [
                "",
                "## Selection Quality",
                "",
                f"- confidence: `{quality.get('confidence', 'low')}`",
                f"- score: `{quality.get('score', 0)}`",
                f"- coverage ratio: `{quality.get('coverage_ratio', 0)}`",
                f"- low confidence: `{quality.get('low_confidence', False)}`",
            ]
        )
        for warning in quality.get("warnings", []):
            lines.append(f"- warning: {warning}")
    if task_pack.get("acceptance_criteria"):
        lines.extend(["", "## Acceptance Criteria", ""])
        for criterion in task_pack["acceptance_criteria"]:
            lines.append(f"- {criterion}")
    if task_pack.get("completion_contract"):
        contract = task_pack["completion_contract"]
        lines.extend(["", "## Completion Contract", ""])
        lines.append("- final response must include: " + ", ".join(contract.get("final_response_must_include", [])))
        lines.append("- stop conditions: " + ", ".join(contract.get("stop_conditions", [])))
        lines.append("- evidence requirements: " + ", ".join(contract.get("evidence_requirements", [])))
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
    manifest_hash = hashes.get("manifest_sha256")
    if manifest_hash is None:
        add_issue(issues, "schema-missing-manifest-hash", path, "hashes.manifest_sha256 is required")
    elif not isinstance(manifest_hash, str) or not HASH_PATTERN.fullmatch(manifest_hash):
        add_issue(issues, "schema-invalid-hash", path, "manifest_sha256 must be a 64 character lowercase sha256 hex string")


def validate_manifest_integrity(payload: dict, path: Path, issues: list[dict]) -> None:
    hashes = payload.get("hashes")
    if not isinstance(hashes, dict):
        return
    expected = hashes.get("manifest_sha256")
    if not isinstance(expected, str) or not HASH_PATTERN.fullmatch(expected):
        return
    actual = manifest_sha256(payload)
    if actual != expected:
        add_issue(issues, "schema-manifest-hash-mismatch", path, "hashes.manifest_sha256 does not match manifest content", "critical")


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


def validate_policy(payload: dict, path: Path, issues: list[dict]) -> None:
    policy = payload.get("policy")
    if not isinstance(policy, dict):
        add_issue(issues, "schema-invalid-policy", path, "policy must be an object")
        return
    filesystem = policy.get("filesystem")
    if not isinstance(filesystem, dict):
        add_issue(issues, "schema-invalid-policy-filesystem", path, "policy.filesystem must be an object")
    else:
        scope = filesystem.get("scope")
        if scope not in FILESYSTEM_SCOPE_VALUES:
            add_issue(issues, "schema-invalid-policy-filesystem-scope", path, "policy.filesystem.scope is not supported")
    network = policy.get("network")
    if not isinstance(network, dict):
        add_issue(issues, "schema-invalid-policy-network", path, "policy.network must be an object")
    else:
        scope = network.get("scope")
        if scope not in NETWORK_SCOPE_VALUES:
            add_issue(issues, "schema-invalid-policy-network-scope", path, "policy.network.scope is not supported")
        approved_hosts = network.get("approved_hosts")
        if approved_hosts is not None and (
            not isinstance(approved_hosts, list) or not all(isinstance(item, str) and item for item in approved_hosts)
        ):
            add_issue(issues, "schema-invalid-policy-approved-hosts", path, "policy.network.approved_hosts must be a string array")
    approval = policy.get("approval")
    if not isinstance(approval, dict):
        add_issue(issues, "schema-invalid-policy-approval", path, "policy.approval must be an object")
    else:
        required_for = approval.get("required_for")
        if not isinstance(required_for, list) or not all(isinstance(item, str) and item for item in required_for):
            add_issue(issues, "schema-invalid-policy-approval-required-for", path, "policy.approval.required_for must be a string array")


def validate_allowed_tools(payload: dict, path: Path, issues: list[dict]) -> None:
    allowed_tools = payload.get("allowed_tools")
    if not isinstance(allowed_tools, list):
        add_issue(issues, "schema-invalid-allowed-tools", path, "allowed_tools must be an array")
        return
    seen = set()
    for tool in allowed_tools:
        if not isinstance(tool, str) or not tool:
            add_issue(issues, "schema-invalid-allowed-tool", path, "allowed_tools entries must be non-empty strings")
            continue
        normalized = tool.lower()
        if normalized in seen:
            add_issue(issues, "schema-duplicate-allowed-tool", path, f"allowed_tools contains duplicate value {tool!r}", "medium")
        seen.add(normalized)
        if normalized in DISALLOWED_TOOL_VALUES:
            add_issue(issues, "schema-disallowed-tool", path, f"allowed_tools cannot grant runtime permission {tool!r}", "critical")


def validate_string_list(
    value: object,
    path: Path,
    issues: list[dict],
    field: str,
    issue_id: str,
    pattern: re.Pattern[str] | None = None,
) -> list[str]:
    if value is None:
        return []
    if not isinstance(value, list):
        add_issue(issues, issue_id, path, f"contract.{field} must be an array")
        return []
    values = []
    seen = set()
    for item in value:
        if not isinstance(item, str) or not item:
            add_issue(issues, issue_id, path, f"contract.{field} entries must be non-empty strings")
            continue
        if pattern is not None and not pattern.fullmatch(item):
            add_issue(issues, issue_id, path, f"contract.{field} entry {item!r} is not supported")
        if item in seen:
            add_issue(issues, issue_id, path, f"contract.{field} contains duplicate entry {item!r}", "medium")
        seen.add(item)
        values.append(item)
    return values


def validate_contract(payload: dict, path: Path, issues: list[dict]) -> None:
    contract = payload.get("contract")
    if contract is None:
        return
    if not isinstance(contract, dict):
        add_issue(issues, "schema-invalid-contract", path, "contract must be an object")
        return
    allowed_fields = {
        "requires_context",
        "produces_artifacts",
        "produces_evidence",
        "capability_vector",
        "stage_hint",
        "conflicts_with",
        "cost_weight",
    }
    for field in contract:
        if field not in allowed_fields:
            add_issue(issues, "schema-invalid-contract-field", path, f"contract.{field} is not supported")
    validate_string_list(contract.get("requires_context"), path, issues, "requires_context", "schema-invalid-contract-artifact", CONTRACT_ARTIFACT_PATTERN)
    validate_string_list(contract.get("produces_artifacts"), path, issues, "produces_artifacts", "schema-invalid-contract-artifact", CONTRACT_ARTIFACT_PATTERN)
    validate_string_list(contract.get("produces_evidence"), path, issues, "produces_evidence", "schema-invalid-contract-artifact", CONTRACT_ARTIFACT_PATTERN)
    capabilities = validate_string_list(
        contract.get("capability_vector"),
        path,
        issues,
        "capability_vector",
        "schema-invalid-contract-capability",
        CONTRACT_CAPABILITY_PATTERN,
    )
    if contract.get("capability_vector") is not None and not capabilities:
        add_issue(issues, "schema-invalid-contract-capability", path, "contract.capability_vector cannot be empty")
    stage_hint = contract.get("stage_hint")
    if stage_hint is not None and stage_hint not in CONTRACT_STAGE_VALUES:
        add_issue(issues, "schema-invalid-contract-stage", path, "contract.stage_hint is not supported")
    conflicts = validate_string_list(contract.get("conflicts_with"), path, issues, "conflicts_with", "schema-invalid-contract-conflict")
    if payload.get("name") in conflicts:
        add_issue(issues, "schema-invalid-contract-conflict", path, "contract.conflicts_with cannot include the skill itself")
    cost_weight = contract.get("cost_weight")
    if cost_weight is not None and (not isinstance(cost_weight, int) or cost_weight < 1 or cost_weight > 10):
        add_issue(issues, "schema-invalid-contract-cost", path, "contract.cost_weight must be an integer from 1 to 10")


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
    if not isinstance(payload.get("required_verifiers"), list):
        add_issue(issues, "schema-invalid-required-verifiers", path, "required_verifiers must be an array")
    validate_allowed_tools(payload, path, issues)
    validate_policy(payload, path, issues)
    validate_contract(payload, path, issues)
    validate_taxonomy(payload, path, issues)
    validate_source(payload, path, issues)
    validate_hashes(payload, path, issues)
    validate_manifest_integrity(payload, path, issues)


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


ROUTER_EVAL_STRING_LIST_FIELDS = (
    "expected_skills",
    "forbidden_skills",
    "forbidden_skill_prefixes",
    "forbidden_skill_subcategories",
)


def validate_router_eval_case(case: dict) -> list[dict]:
    issues = []
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
        case_issues.extend(validate_router_eval_case(case))
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
        actual_skill_subcategories = {
            skill["name"]: skill.get("taxonomy", {}).get("subcategory", "") for skill in task_pack.get("skills", [])
        }
        expected_scenario = case.get("expected_scenario")
        expected_task_type = case.get("expected_task_type")
        expected_skills = case.get("expected_skills", [])
        forbidden_skills = case.get("forbidden_skills", [])
        forbidden_skill_prefixes = case.get("forbidden_skill_prefixes", [])
        forbidden_skill_subcategories = case.get("forbidden_skill_subcategories", [])
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
                "max_skill_count": max_skill_count,
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


def build_claude_skills_bulk_drafts(candidate_map_path: Path, out_dir: Path, batch_size: int, batch_index: int) -> dict:
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
        write_json(
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
        Path(args.registry),
        Path(args.bundles) if args.bundles else None,
        Path(args.overlap_groups) if args.overlap_groups else None,
        Path(args.references) if getattr(args, "references", None) else None,
        Path(args.claude_skills_candidate_map) if getattr(args, "claude_skills_candidate_map", None) else None,
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
    maintain_check_parser.add_argument("--claude-skills-candidate-map")
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
