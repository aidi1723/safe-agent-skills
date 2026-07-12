from __future__ import annotations

import json
import re
from pathlib import Path
from types import MappingProxyType

from . import __version__
from .candidates import retrieve_scenario_candidates
from .compatibility import build_canonical_content_hash
from .compatibility import build_route_id
from .compatibility import build_route_identity_payload
from .compatibility import to_legacy_v1
from .compiler import compile_execution_graph
from .compiler import _is_acyclic as _compiler_graph_is_acyclic
from .composer import compose_scenarios
from .contracts import usable_contract
from .intent import DecompositionDiagnostics
from .intent import IntentGraph
from .intent import TaskDecomposition
from .intent import decompose_task_detailed, normalize_task
from .registry import load_registry_index
from .registry import manifest_index_entry
from .registry import utc_now
from .registry import verify_registry
from .registry import VerifiedRegistrySnapshot
from .registry import build_verified_registry_snapshot
from .rendering import project_legacy_contracts
from .router import CAPABILITY_SKILL_PREFERENCES
from .router import PIPELINE_STAGE_ORDER
from .router import build_task_profile, capability_skill_names, parse_invariant_capabilities
from .router import pipeline_stage_for_skill
from .router import route_mesh_task, route_scenario_task
from .taxonomy import classify_skill
from .validation import validate_contract


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
    manifest = json.loads((skill_dir / "skill.json").read_text(encoding="utf-8"))
    return _build_skill_pack_item(entry, manifest, skill_text)


def _build_skill_pack_item(entry: dict, manifest: dict, skill_text: str) -> dict:
    sections = extract_markdown_sections(skill_text)
    item = {
        "name": entry["name"],
        "status": entry["status"],
        "risk_level": entry["risk_level"],
        "match_score": entry.get("match_score", 0),
        "taxonomy": entry["taxonomy"],
        "source": entry["source"],
        "hashes": {
            key: entry["hashes"][key]
            for key in ["source_sha256", "sanitized_sha256", "manifest_sha256"]
            if key in entry["hashes"]
        },
        "registry_path": entry["registry_path"],
        "description": extract_frontmatter_description(skill_text),
        "when_to_use": sections.get("When To Use", ""),
        "safe_workflow": sections.get("Safe Workflow", ""),
        "expected_output": sections.get("Expected Output", ""),
        "verifier_expectations": sections.get("Verifier Expectations", ""),
        "failure_handling": sections.get("Failure Handling", ""),
        "policy": manifest.get("policy", {}),
    }
    if "contract" in manifest:
        item["contract"] = manifest["contract"]
    return item

def load_trusted_skill_pack_items(
    registry_dir: Path,
    *,
    snapshot: VerifiedRegistrySnapshot | None = None,
) -> list[dict]:
    if snapshot is not None:
        skills = []
        for bound_skill in snapshot.skills:
            entry = bound_skill.entry()
            if entry.get("status") != "trusted":
                continue
            item = _build_skill_pack_item(
                entry,
                bound_skill.manifest(),
                bound_skill.skill_text,
            )
            item["match_score"] = item.get("match_score", 0)
            skills.append(item)
        return skills

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
    *,
    snapshot: VerifiedRegistrySnapshot | None = None,
) -> dict:
    if not task.strip():
        raise ValueError("task must not be empty")
    snapshot = snapshot or build_verified_registry_snapshot(registry_dir)
    verification = snapshot.verification()

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
    trusted_names = set(snapshot.trusted_skill_names())
    normalized_task = normalize_task(task)
    decomposition = decompose_task_detailed(task)
    intent_graph, decomposition_diagnostics = _validated_decomposition(decomposition)
    candidates = retrieve_scenario_candidates(intent_graph, bundles_index, trusted_names)
    composition = compose_scenarios(intent_graph, candidates, bundles_index, trusted_names)
    trusted_items = {
        item["name"]: item
        for item in load_trusted_skill_pack_items(registry_dir, snapshot=snapshot)
        if item["name"] in trusted_names
    }
    stage_by_skill = MappingProxyType(
        {name: _v2_skill_stage(item) for name, item in trusted_items.items()}
    )
    host_action_by_skill = {
        name: _v2_skill_host_action(item)
        for name, item in trusted_items.items()
    }
    execution_graph = compile_execution_graph(
        intent_graph,
        composition,
        bundles_index,
        trusted_names,
        stage_by_skill,
    )
    execution_graph = _apply_v2_graph_host_actions(execution_graph, host_action_by_skill)
    invariant_capabilities = parse_invariant_capabilities(invariants)
    invariant_skill_names = capability_skill_names(invariant_capabilities, trusted_names)
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
    routing_status = _routing_status(
        composition.status,
        capability_resolution,
        execution_graph,
        decomposition.diagnostics.status,
    )
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
        catalog_content_hash=build_canonical_content_hash(snapshot.index()),
        bundle_content_hash=_json_asset_content_hash(bundles_path),
        overlap_content_hash=(
            build_canonical_content_hash(overlap_groups) if overlap_groups is not None else "none"
        ),
        router_version="hybrid-router-v2-quality-remediation",
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
            "decomposition": decomposition_diagnostics,
        },
        "registry_verification": verification,
        "compatibility": {},
    }
    payload["compatibility"] = {
        "legacy_schema_version": 1,
        "compatibility_loss": to_legacy_v1(payload)["compatibility_loss"],
    }
    validate_task_pack_v2_semantics(payload)
    return payload


def validate_task_pack_v2_semantics(payload: object) -> None:
    """Validate Task Pack relationships that JSON Schema cannot express."""

    root = _semantic_object(payload, "payload")
    intent_graph = _semantic_object(root.get("intent_graph"), "intent_graph")
    intents = _semantic_object_list(intent_graph.get("intents"), "intent_graph.intents")
    intent_ids = _unique_semantic_values(
        [_semantic_text(item.get("id"), "intent.id") for item in intents],
        "intent ids",
    )
    if not intent_ids or len(intent_ids) > 12:
        _semantic_error("intent ids")
    intent_id_set = set(intent_ids)
    intent_edges = []
    for intent in intents:
        intent_id = _semantic_text(intent.get("id"), "intent.id")
        dependencies = _semantic_text_list(intent.get("depends_on"), "intent.depends_on")
        if (
            len(dependencies) != len(set(dependencies))
            or intent_id in dependencies
            or not set(dependencies) <= intent_id_set
        ):
            _semantic_error("intent dependencies")
        intent_edges.extend(
            {"from": dependency_id, "to": intent_id, "type": "intent_dependency"}
            for dependency_id in dependencies
        )
    if not _compiler_graph_is_acyclic(
        [{"id": intent_id} for intent_id in intent_ids], intent_edges
    ):
        _semantic_error("intent dependency cycle")
    unresolved_dependencies = _semantic_text_list(
        intent_graph.get("unresolved_dependencies"), "unresolved dependencies"
    )
    if len(unresolved_dependencies) != len(set(unresolved_dependencies)):
        _semantic_error("unresolved dependencies")
    if unresolved_dependencies and root.get("routing_status") != "blocked":
        _semantic_error("unresolved dependency routing status")

    candidates = _semantic_object_list(root.get("scenario_candidates"), "scenario_candidates")
    candidate_keys = []
    for candidate in candidates:
        intent_id = _semantic_text(candidate.get("intent_id"), "candidate.intent_id")
        scenario_id = _semantic_text(candidate.get("scenario_id"), "candidate.scenario_id")
        if intent_id not in intent_id_set:
            _semantic_error("candidate intent reference")
        candidate_keys.append((intent_id, scenario_id))
    _require_unique_semantic_keys(candidate_keys, "candidate identities")

    selections = _semantic_object_list(root.get("selected_scenarios"), "selected_scenarios")
    scenario_ids = _unique_semantic_values(
        [_semantic_text(item.get("scenario_id"), "selection.scenario_id") for item in selections],
        "selected scenario ids",
    )
    scenario_id_set = set(scenario_ids)
    selected_intent_ids: list[str] = []
    selected_scenario_by_intent: dict[str, str] = {}
    candidate_key_set = set(candidate_keys)
    for selection in selections:
        scenario_id = _semantic_text(selection.get("scenario_id"), "selection.scenario_id")
        selection_intents = _semantic_text_list(selection.get("intent_ids"), "selection.intent_ids")
        if (
            not selection_intents
            or len(selection_intents) != len(set(selection_intents))
            or not set(selection_intents) <= intent_id_set
        ):
            _semantic_error("selected scenario intent references")
        if any((intent_id, scenario_id) not in candidate_key_set for intent_id in selection_intents):
            _semantic_error("selected scenario candidate references")
        selected_intent_ids.extend(selection_intents)
        selected_scenario_by_intent.update(
            {intent_id: scenario_id for intent_id in selection_intents}
        )
    _require_unique_semantic_keys(selected_intent_ids, "selected intent ids")

    uncovered_intents = _semantic_text_list(root.get("uncovered_intents"), "uncovered_intents")
    if (
        len(uncovered_intents) != len(set(uncovered_intents))
        or not set(uncovered_intents) <= intent_id_set
        or set(selected_intent_ids) & set(uncovered_intents)
        or set(selected_intent_ids) | set(uncovered_intents) != intent_id_set
    ):
        _semantic_error("intent coverage")

    selected_skills = _semantic_object_list(root.get("selected_skills"), "selected_skills")
    selected_skill_names = _unique_semantic_values(
        [_semantic_text(item.get("name"), "selected skill name") for item in selected_skills],
        "selected skill names",
    )
    selected_skill_name_set = set(selected_skill_names)
    selected_skill_host_actions = {}
    for skill in selected_skills:
        if "contract" in skill:
            contract = _semantic_object(skill.get("contract"), "selected skill contract")
            if "approval_classes" in contract:
                approval_classes = _semantic_text_list(
                    contract.get("approval_classes"), "selected skill approval classes"
                )
                if len(approval_classes) != len(set(approval_classes)):
                    _semantic_error("selected skill approval classes")
        selected_skill_host_actions[skill["name"]] = _v2_skill_host_action(skill)
    routing_metrics = _semantic_object(root.get("routing_metrics"), "routing_metrics")
    declared_omitted_skills = _semantic_text_list(
        routing_metrics.get("required_skills_omitted"), "required skills omitted"
    )
    if len(declared_omitted_skills) != len(set(declared_omitted_skills)):
        _semantic_error("required skills omitted")
    capability_resolution = _semantic_object(
        root.get("capability_resolution"), "capability_resolution"
    )
    capabilities = _semantic_object_list(
        capability_resolution.get("capabilities"), "capability_resolution.capabilities"
    )
    capability_keys = []
    expected_invariant_nodes: list[tuple[str, str, str, str]] = []
    missing_required_count = 0
    for capability in capabilities:
        scenario_id = capability.get("scenario_id")
        capability_id = capability.get("capability")
        source = capability.get("source", "scenario")
        if type(scenario_id) is not str or type(capability_id) is not str or type(source) is not str:
            _semantic_error("capability identity")
        if scenario_id and scenario_id not in scenario_id_set:
            _semantic_error("capability scenario reference")
        if source == "invariant" and scenario_id:
            _semantic_error("invariant capability scenario")
        skills = _semantic_text_list(capability.get("skills"), "capability.skills")
        if len(skills) != len(set(skills)) or not set(skills) <= selected_skill_name_set:
            _semantic_error("capability skill references")
        required = capability.get("required")
        status = capability.get("status")
        if type(required) is not bool or status not in {"covered", "missing"}:
            _semantic_error("capability status")
        if (status == "covered") != bool(skills):
            _semantic_error("capability coverage")
        if source == "invariant" and status == "covered":
            stage = _semantic_text(capability.get("stage"), "invariant capability stage")
            expected_invariant_nodes.extend(
                (
                    f"invariant:{capability_id}:{skill_name}",
                    capability_id,
                    skill_name,
                    stage,
                )
                for skill_name in skills
            )
        if required and status == "missing":
            missing_required_count += 1
        capability_keys.append((scenario_id, capability_id, source))
    _require_unique_semantic_keys(capability_keys, "capability identities")
    _require_semantic_count(
        capability_resolution.get("missing_required_count"),
        missing_required_count,
        "missing required capability count",
    )
    expected_capability_status = "complete" if missing_required_count == 0 else "incomplete"
    if capability_resolution.get("status") != expected_capability_status:
        _semantic_error("capability resolution status")

    execution_graph = _semantic_object(root.get("execution_graph"), "execution_graph")
    reason_codes = _semantic_text_list(execution_graph.get("reason_codes"), "reason_codes")
    invariant_only_fallback = (
        root.get("routing_status") == "incomplete"
        and execution_graph.get("status") == "blocked"
        and execution_graph.get("acyclic") is False
        and reason_codes == ["incomplete_composition"]
        and not selected_intent_ids
    )
    nodes = _semantic_object_list(execution_graph.get("nodes"), "execution_graph.nodes")
    maximum_node_count = (len(intent_ids) + 1) * len(selected_skill_name_set)
    if len(nodes) > maximum_node_count:
        _semantic_error("execution node count")
    node_ids = _unique_semantic_values(
        [_semantic_text(item.get("id"), "execution node id") for item in nodes],
        "execution node ids",
    )
    node_id_set = set(node_ids)
    required_skill_names: list[str] = []
    standard_node_intents: set[str] = set()
    actual_invariant_nodes: list[tuple[str, str, str, str]] = []
    selected_intent_id_set = set(selected_intent_ids)
    for node in nodes:
        node_intents = _semantic_text_list(node.get("intent_ids"), "execution node intent ids")
        node_scenarios = _semantic_text_list(
            node.get("scenario_ids"), "execution node scenario ids"
        )
        skill_name = _semantic_text(node.get("skill"), "execution node skill")
        host_action = node.get("host_action")
        is_invariant_node = "invariant_capability" in node
        empty_invariant_fallback = (
            is_invariant_node and invariant_only_fallback and not node_intents
        )
        if (
            (not node_intents and not empty_invariant_fallback)
            or len(node_intents) != len(set(node_intents))
            or not set(node_intents) <= selected_intent_id_set
            or len(node_scenarios) != len(set(node_scenarios))
            or not set(node_scenarios) <= scenario_id_set
            or skill_name not in selected_skill_name_set
        ):
            _semantic_error("execution node references")
        if (
            type(host_action) is not bool
            or host_action != selected_skill_host_actions[skill_name]
        ):
            _semantic_error("execution node host action")
        if is_invariant_node:
            invariant_capability = _semantic_text(
                node.get("invariant_capability"), "invariant node capability"
            )
            node_stage = _semantic_text(node.get("stage"), "invariant node stage")
            if (
                (not empty_invariant_fallback and set(node_intents) != selected_intent_id_set)
                or node_scenarios
            ):
                _semantic_error("invariant node mapping")
            actual_invariant_nodes.append(
                (node["id"], invariant_capability, skill_name, node_stage)
            )
        else:
            if (
                len(node_intents) != 1
                or len(node_scenarios) != 1
                or selected_scenario_by_intent.get(node_intents[0]) != node_scenarios[0]
            ):
                _semantic_error("execution node mapping")
            standard_node_intents.add(node_intents[0])
        if skill_name not in required_skill_names:
            required_skill_names.append(skill_name)
    if nodes and standard_node_intents != selected_intent_id_set:
        _semantic_error("execution intent coverage")
    if (
        len(actual_invariant_nodes) != len(expected_invariant_nodes)
        or set(actual_invariant_nodes) != set(expected_invariant_nodes)
    ):
        _semantic_error("invariant capability node projection")

    edges = _semantic_object_list(execution_graph.get("edges"), "execution_graph.edges")
    if len(edges) > 4 * len(nodes) * len(nodes):
        _semantic_error("execution edge count")
    edge_keys = []
    for edge in edges:
        source = _semantic_text(edge.get("from"), "execution edge source")
        target = _semantic_text(edge.get("to"), "execution edge target")
        edge_type = _semantic_text(edge.get("type"), "execution edge type")
        if source not in node_id_set or target not in node_id_set:
            _semantic_error("execution edge endpoint")
        edge_keys.append((source, target, edge_type))
    _require_unique_semantic_keys(edge_keys, "execution edges")
    topology_acyclic = _compiler_graph_is_acyclic(nodes, edges)

    if len(reason_codes) != len(set(reason_codes)):
        _semantic_error("execution graph reason codes")
    graph_status = execution_graph.get("status")
    acyclic = execution_graph.get("acyclic")
    if type(acyclic) is not bool or graph_status not in {"ready", "blocked"}:
        _semantic_error("execution graph status")
    expected_acyclic = bool(nodes) and topology_acyclic and not reason_codes
    if acyclic != expected_acyclic:
        _semantic_error("execution graph acyclic flag")
    if nodes and not topology_acyclic and "dependency_cycle" not in reason_codes:
        _semantic_error("execution graph cycle reason")
    expected_graph_status = "ready" if expected_acyclic else "blocked"
    if graph_status != expected_graph_status or (graph_status == "blocked" and not reason_codes):
        _semantic_error("execution graph coherence")
    if unresolved_dependencies and "invalid_intent_graph" not in reason_codes:
        _semantic_error("unresolved dependency graph reason")

    _require_semantic_count(routing_metrics.get("intent_count"), len(intents), "intent count")
    _require_semantic_count(routing_metrics.get("candidate_count"), len(candidates), "candidate count")
    _require_semantic_count(
        routing_metrics.get("selected_scenario_count"), len(selections), "selected scenario count"
    )
    _require_semantic_count(
        routing_metrics.get("required_skill_count"), len(required_skill_names), "required skill count"
    )
    _require_semantic_count(
        routing_metrics.get("selected_skill_count"), len(selected_skills), "selected skill count"
    )
    _require_semantic_count(
        routing_metrics.get("optional_skills_selected"), 0, "optional skills selected"
    )
    optional_skill_limit = routing_metrics.get("optional_skill_limit")
    if type(optional_skill_limit) is not int or optional_skill_limit < 0:
        _semantic_error("optional skill limit")
    expected_omitted = [name for name in required_skill_names if name not in selected_skill_name_set]
    if declared_omitted_skills != expected_omitted:
        _semantic_error("required skills omitted")
    expected_selected = [name for name in required_skill_names if name not in set(expected_omitted)]
    if selected_skill_names != expected_selected:
        _semantic_error("selected skill order")

    decomposition = _semantic_object(routing_metrics.get("decomposition"), "decomposition")
    _require_semantic_count(
        decomposition.get("emitted_intent_count"), len(intents), "emitted intent count"
    )
    observed_candidates = decomposition.get("observed_candidate_count")
    # Signal scans have no corresponding candidate-record array in the pack.
    if type(observed_candidates) is not int or not 0 <= observed_candidates <= 129:
        _semantic_error("observed candidate count")
    decomposition_reasons = _semantic_text_list(
        decomposition.get("reason_codes"), "decomposition reason codes"
    )
    if len(decomposition_reasons) != len(set(decomposition_reasons)):
        _semantic_error("decomposition reason codes")
    for flag, reason in (
        ("candidate_signal_limit_exceeded", "candidate_signal_limit_exceeded"),
        ("intent_limit_exceeded", "intent_limit_exceeded"),
    ):
        flag_value = decomposition.get(flag)
        if type(flag_value) is not bool or flag_value != (reason in decomposition_reasons):
            _semantic_error("decomposition status")

    registry_verification = _semantic_object(
        root.get("registry_verification"), "registry_verification"
    )
    issues = _semantic_object_list(registry_verification.get("issues"), "registry issues")
    issue_keys = []
    unknown_provenance_count = 0
    tampered_count = 0
    for issue in issues:
        issue_id = _semantic_text(issue.get("id"), "registry issue id")
        skill = _semantic_text(issue.get("skill"), "registry issue skill")
        path = _semantic_text(issue.get("path"), "registry issue path")
        issue_keys.append((issue_id, skill, path))
        if issue_id == "unknown-provenance":
            unknown_provenance_count += 1
        else:
            tampered_count += 1
    _require_unique_semantic_keys(issue_keys, "registry issues")
    # Registry totals have no corresponding Skill-record array in the pack.
    skill_count = _semantic_nonnegative_int(registry_verification.get("skill_count"), "skill count")
    trusted_count = _semantic_nonnegative_int(
        registry_verification.get("trusted_count"), "trusted count"
    )
    if trusted_count > skill_count:
        _semantic_error("trusted count")
    if tampered_count > skill_count or unknown_provenance_count > skill_count:
        _semantic_error("registry issue counts")
    _require_semantic_count(
        registry_verification.get("tampered_count"), tampered_count, "tampered count"
    )
    _require_semantic_count(
        registry_verification.get("unknown_provenance_count"),
        unknown_provenance_count,
        "unknown provenance count",
    )
    expected_registry_status = "failed" if issues else "ok"
    if registry_verification.get("status") != expected_registry_status:
        _semantic_error("registry status")

    compatibility = _semantic_object(root.get("compatibility"), "compatibility")
    if compatibility.get("legacy_schema_version") != 1:
        _semantic_error("compatibility schema version")
    compatibility_loss = _semantic_object(
        compatibility.get("compatibility_loss"), "compatibility loss"
    )
    expected_compatibility_loss = to_legacy_v1(root).get("compatibility_loss")
    if compatibility_loss != expected_compatibility_loss:
        _semantic_error("compatibility loss")

    composition_status = "complete" if not uncovered_intents else "incomplete"
    decomposition_status = "incomplete" if decomposition_reasons else "complete"
    expected_routing_status = _routing_status(
        composition_status,
        capability_resolution,
        execution_graph,
        decomposition_status,
    )
    if root.get("routing_status") != expected_routing_status:
        _semantic_error("routing status")


def _semantic_error(field: str) -> None:
    raise ValueError(f"task pack v2 semantic validation failed: {field}")


def _semantic_object(value: object, field: str) -> dict:
    if type(value) is not dict:
        _semantic_error(field)
    return value


def _semantic_object_list(value: object, field: str) -> list[dict]:
    if type(value) is not list or any(type(item) is not dict for item in value):
        _semantic_error(field)
    return value


def _semantic_text(value: object, field: str) -> str:
    if type(value) is not str or not value:
        _semantic_error(field)
    return value


def _semantic_text_list(value: object, field: str) -> list[str]:
    if type(value) is not list or any(type(item) is not str or not item for item in value):
        _semantic_error(field)
    return value


def _semantic_nonnegative_int(value: object, field: str) -> int:
    if type(value) is not int or value < 0:
        _semantic_error(field)
    return value


def _require_semantic_count(value: object, expected: int, field: str) -> None:
    if _semantic_nonnegative_int(value, field) != expected:
        _semantic_error(field)


def _unique_semantic_values(values: list[str], field: str) -> list[str]:
    _require_unique_semantic_keys(values, field)
    return values


def _require_unique_semantic_keys(values: list, field: str) -> None:
    if len(values) != len(set(values)):
        _semantic_error(field)


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
    if "contract" not in skill:
        return pipeline_stage_for_skill(skill.get("name", ""))
    contract = skill["contract"]
    skill_name = skill.get("name", "")
    issues: list[dict] = []
    validate_contract(
        {"name": skill_name, "contract": contract},
        Path("skill.json"),
        issues,
    )
    if issues or not isinstance(contract, dict):
        raise ValueError(f"invalid Contract v2 or legacy contract: {skill_name}")
    if contract.get("schema_version") == 2 and not usable_contract(
        contract, skill_name=skill_name
    ):
        raise ValueError(f"invalid Contract v2 for trusted skill: {skill_name}")
    stage_hint = contract.get("stage_hint")
    if stage_hint == "execution":
        return "production"
    if stage_hint in PIPELINE_STAGE_ORDER:
        return stage_hint
    raise ValueError(f"invalid Contract v2 or legacy contract stage: {skill_name}")

def _v2_skill_host_action(skill: dict) -> bool:
    contract = skill.get("contract")
    return bool(contract.get("approval_classes")) if isinstance(contract, dict) else False

def _apply_v2_graph_host_actions(
    execution_graph: dict,
    host_action_by_skill: dict[str, bool],
) -> dict:
    graph = dict(execution_graph)
    graph["nodes"] = [
        {
            **node,
            "host_action": host_action_by_skill.get(node.get("skill", ""), False),
        }
        for node in execution_graph.get("nodes", [])
    ]
    return graph

def _routing_status(
    composition_status: str,
    capability_resolution: dict,
    execution_graph: dict,
    decomposition_status: str = "complete",
) -> str:
    reason_codes = set(execution_graph.get("reason_codes", []))
    composition_only_block = reason_codes == {"incomplete_composition"} and composition_status != "complete"
    if execution_graph.get("status") == "blocked" and not composition_only_block:
        return "blocked"
    if (
        composition_status != "complete"
        or decomposition_status != "complete"
        or capability_resolution.get("status") != "complete"
        or capability_resolution.get("missing_required_count", 0) > 0
    ):
        return "incomplete"
    return "complete" if execution_graph.get("status") == "ready" else "blocked"


def _validated_decomposition(
    decomposition: TaskDecomposition,
) -> tuple[IntentGraph, dict]:
    if type(decomposition) is not TaskDecomposition:
        raise ValueError("detailed decomposition must use the TaskDecomposition contract")
    if type(decomposition.intent_graph) is not IntentGraph:
        raise ValueError("detailed decomposition must contain an IntentGraph")
    diagnostics = decomposition.diagnostics
    if type(diagnostics) is not DecompositionDiagnostics:
        raise ValueError("detailed decomposition must contain decomposition diagnostics")

    payload = diagnostics.to_json()
    expected_keys = {
        "mode",
        "observed_candidate_count",
        "emitted_intent_count",
        "candidate_signal_limit_exceeded",
        "intent_limit_exceeded",
        "reason_codes",
    }
    if set(payload) != expected_keys:
        raise ValueError("decomposition diagnostics shape is invalid")
    if payload["mode"] not in {"single_clause", "strong_clauses", "profile_spans"}:
        raise ValueError("decomposition diagnostics mode is invalid")
    for key in ("observed_candidate_count", "emitted_intent_count"):
        maximum = 129 if key == "observed_candidate_count" else 12
        if type(payload[key]) is not int or not 0 <= payload[key] <= maximum:
            raise ValueError("decomposition diagnostics count is invalid")
    if payload["emitted_intent_count"] != len(decomposition.intent_graph.intents):
        raise ValueError("decomposition diagnostics intent count is inconsistent")
    if payload["emitted_intent_count"] > 12:
        raise ValueError("decomposition diagnostics intent count exceeds the limit")
    for key in ("candidate_signal_limit_exceeded", "intent_limit_exceeded"):
        if type(payload[key]) is not bool:
            raise ValueError("decomposition diagnostics limit flag is invalid")

    reason_codes = payload["reason_codes"]
    reason_order = (
        "task_scan_limit_exceeded",
        "candidate_signal_limit_exceeded",
        "intent_limit_exceeded",
        "ambiguous_profile_enumeration",
    )
    if (
        not isinstance(reason_codes, list)
        or reason_codes != [code for code in reason_order if code in reason_codes]
    ):
        raise ValueError("decomposition diagnostics reason codes are invalid")
    if payload["candidate_signal_limit_exceeded"] != (
        "candidate_signal_limit_exceeded" in reason_codes
    ):
        raise ValueError("decomposition diagnostics candidate limit is inconsistent")
    if payload["intent_limit_exceeded"] != ("intent_limit_exceeded" in reason_codes):
        raise ValueError("decomposition diagnostics intent limit is inconsistent")
    return decomposition.intent_graph, payload

def _json_asset_content_hash(path: Path) -> str:
    return build_canonical_content_hash(json.loads(path.read_text(encoding="utf-8")))

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

def resolve_overlap_groups_path(registry_dir: Path, overlap_path: Path | None) -> Path | None:
    if overlap_path is not None:
        if not overlap_path.is_file():
            raise SystemExit(f"overlap groups file not found: {overlap_path}")
        return overlap_path
    default_path = registry_dir / "overlap-groups.json"
    return default_path if default_path.exists() else None
