from __future__ import annotations

import argparse
from dataclasses import dataclass
import json
from datetime import datetime, timezone
from pathlib import Path
from pathlib import PurePosixPath

from .validation import SOURCE_PROVENANCE_FIELDS
from .validation import auxiliary_content_sha256
from .validation import manifest_sha256
from .validation import seal_manifest
from .validation import text_sha256
from .validation import validate_registry_index_schema
from .validation import validate_manifest_schema


@dataclass(frozen=True)
class VerifiedRegistrySkill:
    registry_path: str
    entry_json: str
    manifest_json: str
    skill_text: str

    def entry(self) -> dict:
        return json.loads(self.entry_json)

    def manifest(self) -> dict:
        return json.loads(self.manifest_json)


@dataclass(frozen=True)
class VerifiedRegistrySnapshot:
    index_json: str
    skills: tuple[VerifiedRegistrySkill, ...]
    verification_json: str

    def index(self) -> dict:
        return json.loads(self.index_json)

    def verification(self) -> dict:
        return json.loads(self.verification_json)

    def trusted_skill_names(self) -> frozenset[str]:
        return frozenset(
            skill.entry()["name"]
            for skill in self.skills
            if skill.entry().get("status") == "trusted"
        )


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
        if issues and all(issue["id"] in sealable_issue_ids for issue in issues):
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


def build_verified_registry_snapshot(registry_dir: Path) -> VerifiedRegistrySnapshot:
    root = registry_dir.resolve()
    index_path = registry_dir / "index.json"
    if not index_path.is_file() or index_path.is_symlink():
        raise ValueError("registry snapshot requires a regular index")
    index = json.loads(index_path.read_text(encoding="utf-8"))
    if not isinstance(index, dict) or not isinstance(index.get("skills"), list):
        raise ValueError("registry snapshot index is malformed")
    entries = index["skills"]
    if any(type(entry) is not dict for entry in entries):
        raise ValueError("registry snapshot entries are malformed")
    if any(
        type(entry.get(field)) is not str or not entry[field].strip()
        for entry in entries
        for field in ("name", "status", "risk_level", "registry_path")
    ):
        raise ValueError("registry snapshot entry identity is malformed")
    index_issues: list[dict] = []
    validate_registry_index_schema(index, index_path, index_issues)
    if index_issues:
        raise ValueError("registry snapshot index validation failed")

    paths: list[str] = []
    names: list[str] = []
    for entry in entries:
        relative = PurePosixPath(entry["registry_path"])
        if (
            relative.is_absolute()
            or "." in relative.parts
            or ".." in relative.parts
            or len(relative.parts) != 2
        ):
            raise ValueError("registry snapshot path is unsafe")
        paths.append(relative.as_posix())
        names.append(entry["name"])
    if len(paths) != len(set(paths)) or len(names) != len(set(names)):
        raise ValueError("registry snapshot identities must be unique")

    manifest_paths = sorted(registry_dir.glob("*/*/skill.json"))
    actual_paths = {
        path.parent.relative_to(registry_dir).as_posix() for path in manifest_paths
    }
    if actual_paths != set(paths):
        raise ValueError("registry snapshot index is stale")

    snapshot_skills: list[VerifiedRegistrySkill] = []
    trusted_count = 0
    unknown_provenance_count = 0
    for entry in sorted(entries, key=lambda item: item["registry_path"]):
        relative = PurePosixPath(entry["registry_path"])
        skill_dir = registry_dir.joinpath(*relative.parts)
        manifest_path = skill_dir / "skill.json"
        skill_path = skill_dir / "SKILL.md"
        if (
            skill_dir.is_symlink()
            or manifest_path.is_symlink()
            or skill_path.is_symlink()
            or not manifest_path.is_file()
            or not skill_path.is_file()
        ):
            raise ValueError("registry snapshot skill files are unsafe")
        if root not in manifest_path.resolve().parents or root not in skill_path.resolve().parents:
            raise ValueError("registry snapshot path escapes registry root")

        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        if not isinstance(manifest, dict):
            raise ValueError("registry snapshot manifest is malformed")
        manifest_issues: list[dict] = []
        validate_manifest_schema(manifest, manifest_path, manifest_issues)
        if manifest_issues:
            raise ValueError("registry snapshot manifest validation failed")
        expected_entry = manifest_index_entry(manifest, Path(entry["registry_path"]))
        if entry != expected_entry:
            raise ValueError("registry snapshot entry does not match manifest")

        skill_text = skill_path.read_text(encoding="utf-8")
        if text_sha256(skill_text) != manifest["hashes"]["sanitized_sha256"]:
            raise ValueError("registry snapshot skill content hash mismatch")
        expected_auxiliary = manifest["hashes"].get("auxiliary_sha256")
        if auxiliary_content_sha256(skill_dir) != expected_auxiliary:
            raise ValueError("registry snapshot auxiliary content hash mismatch")
        if manifest["status"] == "trusted":
            trusted_count += 1
        source = manifest.get("source", {})
        if any(
            source.get(field, "unknown") == "unknown"
            for field in SOURCE_PROVENANCE_FIELDS
        ):
            unknown_provenance_count += 1
        snapshot_skills.append(
            VerifiedRegistrySkill(
                registry_path=entry["registry_path"],
                entry_json=json.dumps(entry, ensure_ascii=False, sort_keys=True),
                manifest_json=json.dumps(manifest, ensure_ascii=False, sort_keys=True),
                skill_text=skill_text,
            )
        )

    if unknown_provenance_count:
        raise ValueError("registry snapshot contains unknown provenance")
    verification = {
        "schema_version": 1,
        "generated_at": utc_now(),
        "status": "ok",
        "skill_count": len(snapshot_skills),
        "trusted_count": trusted_count,
        "tampered_count": 0,
        "unknown_provenance_count": unknown_provenance_count,
        "issues": [],
    }
    return VerifiedRegistrySnapshot(
        index_json=json.dumps(index, ensure_ascii=False, sort_keys=True),
        skills=tuple(snapshot_skills),
        verification_json=json.dumps(verification, ensure_ascii=False, sort_keys=True),
    )

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

        expected_auxiliary_hash = manifest.get("hashes", {}).get("auxiliary_sha256")
        actual_auxiliary_hash = auxiliary_content_sha256(skill_dir)
        if actual_auxiliary_hash != expected_auxiliary_hash and (
            actual_auxiliary_hash is not None or expected_auxiliary_hash is not None
        ):
            tampered_count += 1
            issues.append(
                {
                    "id": "auxiliary-content-mismatch",
                    "severity": "critical",
                    "skill": name,
                    "path": skill_dir.as_posix(),
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
    auxiliary_hash = auxiliary_content_sha256(skill_dir)
    if auxiliary_hash is None:
        manifest["hashes"].pop("auxiliary_sha256", None)
    else:
        manifest["hashes"]["auxiliary_sha256"] = auxiliary_hash
    seal_manifest(manifest)
    write_json(skill_dir / "skill.json", manifest)
    report_path = skill_dir / "SANITIZATION_REPORT.json"
    if report_path.is_file():
        report = json.loads(report_path.read_text(encoding="utf-8"))
        report.setdefault("hashes", {})["sanitized_sha256"] = manifest["hashes"]["sanitized_sha256"]
        report["hashes"]["manifest_sha256"] = manifest["hashes"]["manifest_sha256"]
        write_json(report_path, report)
    return manifest
