from __future__ import annotations

import json
import re
from pathlib import Path

from .validation import UnsafeAuxiliaryContentError, auxiliary_file_counts


DEPTH_CLASSES = {"routing_card", "playbook", "specialist"}
REQUIRED_SECTIONS = {
    "When To Use",
    "Safe Workflow",
    "Expected Output",
    "Verifier Expectations",
}


def _section_names(text: str) -> set[str]:
    return {
        match.group(1).strip()
        for match in re.finditer(r"^##\s+(.+?)\s*$", text, flags=re.MULTILINE)
    }


def analyze_skill(skill_dir: Path, policy: dict) -> dict:
    body_path = skill_dir / "SKILL.md"
    errors = []
    warnings = []
    depth_class = policy.get("depth_class", "routing_card")
    if depth_class not in DEPTH_CLASSES:
        errors.append({"id": "invalid-depth-class", "value": depth_class})
        depth_class = "routing_card"
    if not body_path.is_file():
        return {
            "name": skill_dir.name,
            "depth_class": depth_class,
            "errors": [{"id": "missing-skill-body"}],
            "warnings": warnings,
        }
    text = body_path.read_text(encoding="utf-8")
    sections = _section_names(text)
    missing_sections = sorted(REQUIRED_SECTIONS - sections)
    if missing_sections:
        errors.append({"id": "missing-required-sections", "sections": missing_sections})
    try:
        auxiliary_counts = auxiliary_file_counts(skill_dir)
    except UnsafeAuxiliaryContentError:
        errors.append({"id": "unsafe-auxiliary-content"})
        auxiliary_counts = {}
    reference_count = auxiliary_counts.get("references", 0)
    script_count = auxiliary_counts.get("scripts", 0)
    word_count = len(re.findall(r"[\w-]+", text, flags=re.UNICODE))
    workflow_step_count = len(re.findall(r"^\d+\.\s+", text, flags=re.MULTILINE))
    has_examples = any("example" in section.lower() for section in sections)
    has_decision_guidance = any("decision" in section.lower() for section in sections)
    has_failure_handling = "Failure Handling" in sections
    if depth_class == "specialist" and reference_count + script_count == 0:
        warnings.append({"id": "specialist-missing-reference"})
    if depth_class in {"playbook", "specialist"} and not has_decision_guidance:
        warnings.append({"id": "deep-skill-missing-decision-guidance"})
    if depth_class != "routing_card" and word_count < 300:
        warnings.append({"id": "deep-skill-low-word-count", "actual": word_count, "recommended": 300})
    return {
        "name": skill_dir.name,
        "depth_class": depth_class,
        "word_count": word_count,
        "workflow_step_count": workflow_step_count,
        "sections": sorted(sections),
        "has_examples": has_examples,
        "has_decision_guidance": has_decision_guidance,
        "has_failure_handling": has_failure_handling,
        "reference_count": reference_count,
        "script_count": script_count,
        "errors": errors,
        "warnings": warnings,
    }


def audit_catalog_depth(catalog_dir: Path, policy_path: Path) -> dict:
    policy = json.loads(policy_path.read_text(encoding="utf-8"))
    default_class = policy.get("default_depth_class", "routing_card")
    overrides = policy.get("skills", {})
    reports = []
    for body_path in sorted(catalog_dir.glob("*/*/SKILL.md")):
        name = body_path.parent.name
        skill_policy = {"depth_class": overrides.get(name, default_class)}
        reports.append(analyze_skill(body_path.parent, skill_policy))
    error_count = sum(len(report["errors"]) for report in reports)
    warning_count = sum(len(report["warnings"]) for report in reports)
    depth_counts = {
        depth_class: sum(report["depth_class"] == depth_class for report in reports)
        for depth_class in sorted(DEPTH_CLASSES)
        if any(report["depth_class"] == depth_class for report in reports)
    }
    return {
        "schema_version": 1,
        "status": "failed" if error_count else "ok",
        "skill_count": len(reports),
        "depth_counts": depth_counts,
        "error_count": error_count,
        "warning_count": warning_count,
        "skills": reports,
    }
