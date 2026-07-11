from __future__ import annotations

import json
from pathlib import Path
from pathlib import PurePosixPath

from .validation import validate_contract
from .registry import VerifiedRegistrySnapshot


REGISTRY_STATUS_VALUES = {"quarantined", "review_required", "trusted", "rejected", "disabled"}


def _nonempty_string(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _validate_registry_index(registry: object) -> dict[str, dict]:
    if not isinstance(registry, dict):
        raise ValueError("registry index must be an object")
    skills = registry.get("skills")
    if not isinstance(skills, list):
        raise ValueError("registry index skills must be an array")
    entries: dict[str, dict] = {}
    for index, entry in enumerate(skills):
        if not isinstance(entry, dict):
            raise ValueError(f"registry skill entry {index} must be an object")
        name = entry.get("name")
        if not _nonempty_string(name):
            raise ValueError(f"registry skill entry {index} name must be a nonempty string")
        if name in entries:
            raise ValueError(f"registry skill names must be unique: {name}")
        status = entry.get("status")
        if not _nonempty_string(status):
            raise ValueError(f"registry skill {name} status must be a nonempty string")
        if status not in REGISTRY_STATUS_VALUES:
            raise ValueError(f"registry skill {name} status is not supported: {status}")
        registry_path = entry.get("registry_path")
        if not _nonempty_string(registry_path):
            raise ValueError(f"registry skill {name} registry_path must be a nonempty string")
        path = PurePosixPath(registry_path)
        if path.is_absolute() or ".." in path.parts or "." in path.parts:
            raise ValueError(f"registry skill {name} registry_path must be a safe relative path")
        entries[name] = entry
    return entries


def _validate_bundles_index(bundles_index: object) -> tuple[list[dict], dict[str, dict]]:
    if not isinstance(bundles_index, dict):
        raise ValueError("bundles index must be an object")
    bundles = bundles_index.get("bundles")
    if not isinstance(bundles, list):
        raise ValueError("bundles index bundles must be an array")
    by_id: dict[str, dict] = {}
    for index, bundle in enumerate(bundles):
        if not isinstance(bundle, dict):
            raise ValueError(f"bundle entry {index} must be an object")
        bundle_id = bundle.get("id")
        if not _nonempty_string(bundle_id):
            raise ValueError(f"bundle entry {index} id must be a nonempty string")
        if bundle_id in by_id:
            raise ValueError(f"bundle ids must be unique: {bundle_id}")
        skills = bundle.get("skills")
        if not isinstance(skills, list) or not skills or not all(_nonempty_string(name) for name in skills):
            raise ValueError(f"bundle {bundle_id} skills must be a nonempty string array")
        if len(skills) != len(set(skills)):
            raise ValueError(f"bundle {bundle_id} skills must be unique")
        by_id[bundle_id] = bundle
    return bundles, by_id


def usable_contract(contract: object, *, skill_name: str = "contract-coverage-skill") -> bool:
    if not isinstance(contract, dict):
        return False
    if contract.get("schema_version") != 2:
        return False
    if not isinstance(contract.get("stage_hint"), str) or not contract["stage_hint"]:
        return False
    capabilities = contract.get("capability_vector")
    has_capabilities = isinstance(capabilities, list) and bool(capabilities) and all(
        isinstance(capability, str) and capability for capability in capabilities
    )
    if not has_capabilities:
        return False
    issues: list[dict] = []
    validate_contract({"name": skill_name, "contract": contract}, Path("skill.json"), issues)
    return not issues


def contract_coverage(
    registry: dict,
    bundles_index: dict,
    scenario_ids: list[str] | None = None,
    *,
    registry_root: Path = Path("catalog"),
    snapshot: VerifiedRegistrySnapshot | None = None,
) -> dict:
    entries = _validate_registry_index(registry)
    snapshot_manifests: dict[str, dict] | None = None
    if snapshot is not None:
        if snapshot.index() != registry:
            raise ValueError("registry snapshot does not match registry index")
        snapshot_manifests = {
            skill.entry()["name"]: skill.manifest()
            for skill in snapshot.skills
        }
    bundles, bundles_by_id = _validate_bundles_index(bundles_index)
    available_ids = set(bundles_by_id)
    if scenario_ids is not None and not scenario_ids:
        raise ValueError("no scenarios were selected for contract coverage")
    if scenario_ids is None and not available_ids:
        raise ValueError("no scenarios are available for contract coverage")
    selected_ids = list(dict.fromkeys(scenario_ids if scenario_ids is not None else sorted(available_ids)))
    unknown_ids = sorted(set(selected_ids) - available_ids)
    if unknown_ids:
        raise ValueError(f"unknown scenario ids: {', '.join(unknown_ids)}")

    selected_names = {
        name
        for bundle in bundles
        if isinstance(bundle, dict) and bundle.get("id") in selected_ids
        for name in bundle.get("skills", [])
        if isinstance(name, str) and name
    }
    if not selected_names:
        raise ValueError("selected scenarios contain no skills for contract coverage")
    covered_names = []
    missing_names = []
    for name in sorted(selected_names):
        entry = entries.get(name)
        if not entry or entry.get("status") != "trusted":
            missing_names.append(name)
            continue
        if snapshot_manifests is not None:
            manifest = snapshot_manifests.get(name)
            if manifest is None:
                missing_names.append(name)
                continue
        else:
            manifest_path = registry_root / entry["registry_path"] / "skill.json"
            try:
                manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                missing_names.append(name)
                continue
        if usable_contract(manifest.get("contract"), skill_name=name):
            covered_names.append(name)
        else:
            missing_names.append(name)

    total = len(selected_names)
    covered = len(covered_names)
    return {
        "scenario_ids": selected_ids,
        "covered_skill_count": covered,
        "total_skill_count": total,
        "coverage_ratio": covered / total if total else 1.0,
        "covered_skill_names": covered_names,
        "missing_skill_names": missing_names,
    }
