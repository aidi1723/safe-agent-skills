from __future__ import annotations

import argparse
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path

from .router import route_scenario_task
from .scanner import highest_risk, line_findings, read_text_files, scan_text, source_hash
from .taxonomy import classify_skill, taxonomy_from_manifest


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

    return {
        "type": str(manifest_source.get("type", "local_folder")),
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
            "sanitized_sha256": "0" * 64,
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
    skills = []
    for manifest_path in sorted(registry_dir.glob("*/*/skill.json")):
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        skills.append(manifest_index_entry(manifest, manifest_path.parent.relative_to(registry_dir)))
    index = {
        "schema_version": 1,
        "generated_at": utc_now(),
        "skill_count": len(skills),
        "skills": skills,
    }
    registry_dir.mkdir(parents=True, exist_ok=True)
    (registry_dir / "index.json").write_text(json.dumps(index, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return index


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
) -> dict:
    verification = verify_registry(registry_dir)
    if verification["status"] != "ok":
        raise SystemExit("registry verification failed; refusing to build task pack")
    task_taxonomy = classify_skill("task", task).to_json()
    candidate_limit = max(top, max_skills or top) if router_mode == "scenario" else top
    selected = select_skills_for_task(registry_dir, task_taxonomy, task, include_review_required)[:candidate_limit]
    skills = [load_skill_pack_item(registry_dir, entry) for entry in selected]
    bundles = []
    if include_bundles:
        bundle_index_path = bundles_path or Path("bundles/index.json")
        bundles = select_bundles_for_task(registry_dir, bundle_index_path, task, skills)
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
        bundles = select_bundles_for_task(registry_dir, bundle_index_path, task, skills) if include_bundles else []
        if include_bundles and routed["selected_scenario"].get("id"):
            scenario_id = routed["selected_scenario"]["id"]
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
        lines.extend(["", "## Execution Plan", ""])
        for step in task_pack.get("execution_plan", []):
            lines.append(f"{step['order']}. `{step['skill']}` - {step['instruction']}")
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
    required_source_fields = ["url", "author", "license", "reference", "collected_by"]

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
        if any(source.get(field, "unknown") == "unknown" for field in required_source_fields):
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


def maintain_check(registry_dir: Path, bundles_path: Path | None = None) -> dict:
    registry_verification = verify_registry(registry_dir)
    issues = list(registry_verification["issues"])
    bundle_validation = None
    if bundles_path is not None:
        bundle_validation = validate_bundles(registry_dir, bundles_path)
        issues.extend(bundle_validation["issues"])
    return {
        "schema_version": 1,
        "generated_at": utc_now(),
        "status": "failed" if issues else "ok",
        "registry_verification": registry_verification,
        "bundle_validation": bundle_validation,
        "issues": issues,
    }


def maintain_check_command(args: argparse.Namespace) -> int:
    result = maintain_check(Path(args.registry), Path(args.bundles) if args.bundles else None)
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
    task_pack_parser.add_argument("--router", choices=["simple", "scenario"], default="simple")
    task_pack_parser.add_argument("--max-skills", type=int)
    task_pack_parser.set_defaults(func=task_pack_command)

    verify_parser = subparsers.add_parser("verify")
    verify_parser.add_argument("--registry", required=True)
    verify_parser.set_defaults(func=verify_command)

    maintain_check_parser = subparsers.add_parser("maintain-check")
    maintain_check_parser.add_argument("--registry", required=True)
    maintain_check_parser.add_argument("--bundles")
    maintain_check_parser.set_defaults(func=maintain_check_command)

    reindex_parser = subparsers.add_parser("reindex")
    reindex_parser.add_argument("--registry", required=True)
    reindex_parser.set_defaults(func=reindex_command)

    return parser


def add_provenance_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--source-url")
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
