from __future__ import annotations

import json
from pathlib import Path

from .validation import validate_contract


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
) -> dict:
    bundles = bundles_index.get("bundles")
    if not isinstance(bundles, list):
        raise ValueError("bundles index must contain a bundles array")
    available_ids = {
        bundle.get("id") for bundle in bundles if isinstance(bundle, dict) and isinstance(bundle.get("id"), str)
    }
    selected_ids = list(dict.fromkeys(scenario_ids or sorted(available_ids)))
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
    entries = {
        entry.get("name"): entry
        for entry in registry.get("skills", [])
        if isinstance(entry, dict) and entry.get("status") == "trusted" and isinstance(entry.get("name"), str)
    }
    covered_names = []
    missing_names = []
    for name in sorted(selected_names):
        entry = entries.get(name)
        if not entry or not isinstance(entry.get("registry_path"), str):
            missing_names.append(name)
            continue
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
