from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from .validation import SOURCE_PROVENANCE_FIELDS
from .validation import manifest_sha256
from .validation import seal_manifest
from .validation import text_sha256
from .validation import validate_manifest_schema


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")

def write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")

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

def reseal_skill_content(skill_dir: Path) -> dict:
    manifest = load_manifest(skill_dir)
    skill_path = skill_dir / "SKILL.md"
    if not skill_path.is_file():
        raise ValueError(f"missing skill body: {skill_path}")
    manifest["hashes"]["sanitized_sha256"] = text_sha256(skill_path.read_text(encoding="utf-8"))
    seal_manifest(manifest)
    write_json(skill_dir / "skill.json", manifest)
    report_path = skill_dir / "SANITIZATION_REPORT.json"
    if report_path.is_file():
        report = json.loads(report_path.read_text(encoding="utf-8"))
        report.setdefault("hashes", {})["sanitized_sha256"] = manifest["hashes"]["sanitized_sha256"]
        report["hashes"]["manifest_sha256"] = manifest["hashes"]["manifest_sha256"]
        write_json(report_path, report)
    return manifest

