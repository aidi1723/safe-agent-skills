from __future__ import annotations

from .routing_profiles import AMBIGUOUS_PROFILE_SIGNALS as AMBIGUOUS_PROFILE_SIGNALS
from .routing_profiles import CAPABILITY_SKILL_PREFERENCES as CAPABILITY_SKILL_PREFERENCES
from .routing_profiles import CURRENT_CONTEXT_LABELS as CURRENT_CONTEXT_LABELS
from .routing_profiles import CURRENT_INTENT_MARKER_RE as CURRENT_INTENT_MARKER_RE
from .routing_profiles import CURRENT_INTENT_WEIGHT as CURRENT_INTENT_WEIGHT
from .routing_profiles import HISTORY_CONTEXT_LABELS as HISTORY_CONTEXT_LABELS
from .routing_profiles import HISTORY_CONTEXT_MARKER_RE as HISTORY_CONTEXT_MARKER_RE
from .routing_profiles import HISTORY_CONTEXT_WEIGHT as HISTORY_CONTEXT_WEIGHT
from .routing_profiles import INVARIANT_CAPABILITY_SIGNALS as INVARIANT_CAPABILITY_SIGNALS
from .routing_profiles import NORMALIZATION_ALIASES as NORMALIZATION_ALIASES
from .routing_profiles import SCENARIO_PROFILES as SCENARIO_PROFILES
from .routing_profiles import STALE_CONTEXT_LABELS as STALE_CONTEXT_LABELS
from .routing_profiles import _signal_score as _signal_score
from .routing_profiles import build_capability_coverage as build_capability_coverage
from .routing_profiles import build_profile_for_task_type as build_profile_for_task_type
from .routing_profiles import build_task_profile as build_task_profile
from .routing_profiles import capability_skill_names as capability_skill_names
from .routing_profiles import empty_current_intent_metadata as empty_current_intent_metadata
from .routing_profiles import normalize_task_text as normalize_task_text
from .routing_profiles import parse_invariant_capabilities as parse_invariant_capabilities
from .routing_profiles import parse_structured_context_text as parse_structured_context_text
from .routing_profiles import prune_overlap_skill_names as prune_overlap_skill_names
from .routing_profiles import score_bundle_for_profile as score_bundle_for_profile
from .routing_profiles import select_trusted_bundle_for_profile as select_trusted_bundle_for_profile
from .routing_profiles import selected_bundle_required_skill_names as selected_bundle_required_skill_names
from .routing_profiles import signal_matches_text as signal_matches_text
from .routing_profiles import split_current_intent_text as split_current_intent_text
from .routing_profiles import structured_context_label_key as structured_context_label_key
from .routing_execution import EXECUTION_ROLE_BY_STAGE as EXECUTION_ROLE_BY_STAGE
from .routing_execution import EXTERNAL_CONTEXT_ARTIFACTS as EXTERNAL_CONTEXT_ARTIFACTS
from .routing_execution import LOW_CONFIDENCE_EXPLANATIONS as LOW_CONFIDENCE_EXPLANATIONS
from .routing_execution import LOW_CONFIDENCE_GENERAL_FALLBACK_SKILLS as LOW_CONFIDENCE_GENERAL_FALLBACK_SKILLS
from .routing_execution import LOW_CONFIDENCE_GENERAL_NOISE_SKILLS as LOW_CONFIDENCE_GENERAL_NOISE_SKILLS
from .routing_execution import LOW_CONFIDENCE_RECOMMENDED_ACTIONS as LOW_CONFIDENCE_RECOMMENDED_ACTIONS
from .routing_execution import PIPELINE_STAGE_INFO as PIPELINE_STAGE_INFO
from .routing_execution import PIPELINE_STAGE_ORDER as PIPELINE_STAGE_ORDER
from .routing_execution import RUNTIME_APPROVAL_RULES as RUNTIME_APPROVAL_RULES
from .routing_execution import SCENARIO_STAGE_SKILLS as SCENARIO_STAGE_SKILLS
from .routing_execution import SKILL_APPROVAL_REQUIREMENTS as SKILL_APPROVAL_REQUIREMENTS
from .routing_execution import SKILL_STAGE_HINTS as SKILL_STAGE_HINTS
from .routing_execution import STAGE_GATE_BY_STAGE as STAGE_GATE_BY_STAGE
from .routing_execution import approval_gate_text as approval_gate_text
from .routing_execution import build_approval_gates as build_approval_gates
from .routing_execution import build_contract_diagnostics as build_contract_diagnostics
from .routing_execution import build_contract_edges as build_contract_edges
from .routing_execution import build_contract_graph as build_contract_graph
from .routing_execution import build_execution_graph as build_execution_graph
from .routing_execution import build_execution_plan as build_execution_plan
from .routing_execution import build_pipeline_plan as build_pipeline_plan
from .routing_execution import build_pipeline_stage as build_pipeline_stage
from .routing_execution import build_selection_explanations as build_selection_explanations
from .routing_execution import build_selection_quality as build_selection_quality
from .routing_execution import build_selection_trace as build_selection_trace
from .routing_execution import contract_artifacts as contract_artifacts
from .routing_execution import contract_required_context as contract_required_context
from .routing_execution import contract_requires_after as contract_requires_after
from .routing_execution import contract_sorted_skill_names as contract_sorted_skill_names
from .routing_execution import execution_role_for_skill as execution_role_for_skill
from .routing_execution import execution_role_for_stage as execution_role_for_stage
from .routing_execution import lightweight_general_fallback_skill_names as lightweight_general_fallback_skill_names
from .routing_execution import low_confidence_reason_codes as low_confidence_reason_codes
from .routing_execution import pipeline_stage_for_skill as pipeline_stage_for_skill
from .routing_execution import scenario_stage_skill_map as scenario_stage_skill_map
from .routing_execution import selected_skill_names as selected_skill_names
from .routing_execution import should_use_lightweight_general_fallback as should_use_lightweight_general_fallback
from .routing_execution import signal_matches_approval_text as signal_matches_approval_text
from .routing_execution import skill_contract as skill_contract
from .routing_execution import skill_stage as skill_stage
from .routing_execution import skill_stage_for_item as skill_stage_for_item
from .routing_execution import sort_mesh_skill_names as sort_mesh_skill_names
from .routing_execution import strategy_optional_skill_names as strategy_optional_skill_names
from .routing_execution import topology_layers as topology_layers


ROUTER_VERSION = 1

def route_scenario_task(
    task: str,
    selected_skills: list[dict],
    bundles_index: dict,
    trusted_skill_names: set[str],
    max_skills: int,
) -> dict:
    profile = build_task_profile(task)
    trusted_bundles = [
        bundle
        for bundle in bundles_index.get("bundles", [])
        if bundle.get("status") == "trusted" and set(bundle.get("skills", [])).issubset(trusted_skill_names)
    ]
    selected_bundle = max(
        trusted_bundles,
        key=lambda bundle: (score_bundle_for_profile(bundle, profile), bundle.get("id", "")),
        default={},
    )
    if selected_bundle and score_bundle_for_profile(selected_bundle, profile) <= 0:
        selected_bundle = {}

    selected_by_name = {skill["name"]: skill for skill in selected_skills}
    ordered_names: list[str] = []
    if should_use_lightweight_general_fallback(profile, selected_bundle):
        ordered_names.extend(lightweight_general_fallback_skill_names(selected_skills, selected_by_name))
    elif selected_bundle:
        for name in selected_bundle.get("execution_order", selected_bundle.get("skills", [])):
            if name in selected_by_name and name not in ordered_names:
                ordered_names.append(name)
        for capability in selected_bundle.get("required_capabilities", []):
            for name in capability.get("preferred_skills", []):
                if name in selected_by_name and name not in ordered_names:
                    ordered_names.append(name)
        for skill in selected_skills:
            if skill.get("match_score", 0) > 0 and skill["name"] not in ordered_names:
                ordered_names.append(skill["name"])
    else:
        for skill in selected_skills:
            if skill.get("match_score", 0) > 0 and skill["name"] not in ordered_names:
                ordered_names.append(skill["name"])
    required_skill_names: list[str] = []
    if selected_bundle:
        task_required_capabilities = set(profile.get("required_capabilities", []))
        for capability in selected_bundle.get("required_capabilities", []):
            capability_id = capability.get("id", "")
            if not capability.get("required", True) and capability_id not in task_required_capabilities:
                continue
            selected_name = next(
                (name for name in capability.get("preferred_skills", []) if name in selected_by_name),
                "",
            )
            if selected_name and selected_name not in required_skill_names:
                required_skill_names.append(selected_name)
    routed_names = ordered_names[:max_skills]
    for name in required_skill_names:
        if name not in routed_names:
            routed_names.append(name)
    routed_skills = [selected_by_name[name] for name in routed_names]
    coverage = (
        build_capability_coverage(
            selected_bundle,
            {skill["name"] for skill in routed_skills},
            set(selected_by_name),
            set(profile.get("required_capabilities", [])),
        )
        if selected_bundle
        else []
    )
    selected_scenario = {
        "id": selected_bundle.get("id", ""),
        "name": selected_bundle.get("name", selected_bundle.get("id", "")),
        "match_score": score_bundle_for_profile(selected_bundle, profile) if selected_bundle else 0,
    }
    selection_quality = build_selection_quality(
        task_profile=profile,
        selected_bundle=selected_bundle,
        selected_scenario=selected_scenario,
        coverage=coverage,
        pruned_skills=[],
    )
    selection_trace = build_selection_trace(
        router_mode="deterministic_scenario_router",
        strategy="balanced",
        task_profile=profile,
        selected_bundle=selected_bundle,
        selected_scenario=selected_scenario,
        candidate_skills=selected_skills,
        routed_skills=routed_skills,
        coverage=coverage,
        required_skill_names=set(required_skill_names),
        pruned_skill_names=[],
        invariant_capabilities=[],
        selection_quality=selection_quality,
    )
    execution_plan = build_execution_plan(selected_bundle, routed_skills) if selected_bundle else build_execution_plan({}, routed_skills)
    explanations = build_selection_explanations(selected_bundle, routed_skills, coverage) if selected_bundle else []
    contract_graph = build_contract_graph(routed_skills)
    contract_diagnostics = build_contract_diagnostics(routed_skills, contract_graph)
    pipeline_plan = build_pipeline_plan(
        task=task,
        task_profile=profile,
        selected_bundle=selected_bundle,
        selected_skills=routed_skills,
        coverage=coverage,
        execution_graph=None,
        invariants=None,
    )
    return {
        "router": {"mode": "deterministic_scenario_router", "version": ROUTER_VERSION},
        "task_profile": profile,
        "selected_scenario": selected_scenario,
        "skills": routed_skills,
        "bundles": [selected_bundle] if selected_bundle else [],
        "coverage": coverage,
        "selection_quality": selection_quality,
        "selection_trace": selection_trace,
        "execution_plan": execution_plan,
        "selection_explanations": explanations,
        "pipeline_plan": pipeline_plan,
        "contract_diagnostics": contract_diagnostics,
    }


def route_mesh_task(
    task: str,
    invariants: list[str] | str | None,
    selected_skills: list[dict],
    bundles_index: dict,
    trusted_skill_names: set[str],
    overlap_groups: dict | None,
    max_skills: int,
    strategy: str = "balanced",
) -> dict:
    profile = build_task_profile(task)
    invariant_capabilities = parse_invariant_capabilities(invariants)
    selected_bundle = select_trusted_bundle_for_profile(bundles_index, profile, trusted_skill_names)
    selected_by_name = {skill["name"]: skill for skill in selected_skills}
    use_lightweight_general_fallback = should_use_lightweight_general_fallback(
        profile,
        selected_bundle,
        invariant_capabilities,
    )

    ordered_names: list[str] = []
    if use_lightweight_general_fallback:
        ordered_names.extend(lightweight_general_fallback_skill_names(selected_skills, selected_by_name))
    elif selected_bundle:
        for name in selected_bundle.get("execution_order", selected_bundle.get("skills", [])):
            if name in selected_by_name and name not in ordered_names:
                ordered_names.append(name)
        for capability in selected_bundle.get("required_capabilities", []):
            for name in capability.get("preferred_skills", []):
                if name in selected_by_name and name not in ordered_names:
                    ordered_names.append(name)

    if not use_lightweight_general_fallback:
        for name in capability_skill_names(invariant_capabilities, trusted_skill_names):
            if name in selected_by_name and name not in ordered_names:
                ordered_names.append(name)

        for skill in selected_skills:
            if skill.get("match_score", 0) > 0 and skill["name"] not in ordered_names:
                ordered_names.append(skill["name"])

    required_names = set(capability_skill_names(invariant_capabilities, trusted_skill_names))
    task_required_capabilities = set(profile.get("required_capabilities", []))
    required_names.update(selected_bundle_required_skill_names(selected_bundle, selected_by_name, task_required_capabilities))
    ordered_names, pruned_names = prune_overlap_skill_names(ordered_names, overlap_groups, required_names)
    if not use_lightweight_general_fallback:
        for skill in selected_skills:
            if skill.get("match_score", 0) > 0 and skill["name"] not in ordered_names:
                ordered_names.append(skill["name"])
    sorted_names, prelimit_graph = contract_sorted_skill_names(selected_by_name, ordered_names)
    strategy_limits = {"fast": min(max_skills, 5), "balanced": max_skills, "deep": max(max_skills, 10)}
    required_sorted_names = [name for name in sorted_names if name in required_names]
    optional_sorted_names = strategy_optional_skill_names([name for name in sorted_names if name not in required_names], strategy)
    limit = max(strategy_limits.get(strategy, max_skills), len(required_sorted_names))
    final_names = required_sorted_names + optional_sorted_names[: max(0, limit - len(required_sorted_names))]
    final_names, _final_graph = contract_sorted_skill_names(selected_by_name, final_names)
    routed_skills = [selected_by_name[name] for name in final_names]
    use_stage_ordered_output = bool(selected_bundle and selected_bundle.get("id") == "skill-router-quality-review")
    if use_stage_ordered_output:
        stage_map = scenario_stage_skill_map(selected_bundle.get("id", ""), selected_skill_names(routed_skills))
        ordered_names = [name for stage in PIPELINE_STAGE_ORDER for name in stage_map.get(stage, [])]
        ordered_names.extend(skill["name"] for skill in routed_skills if skill["name"] not in ordered_names)
        routed_skills = [selected_by_name[name] for name in ordered_names]
    selected_names = {skill["name"] for skill in routed_skills}
    coverage = (
        build_capability_coverage(selected_bundle, selected_names, set(selected_by_name), task_required_capabilities)
        if selected_bundle
        else []
    )
    for capability in invariant_capabilities:
        preferred = CAPABILITY_SKILL_PREFERENCES.get(capability, [])
        selected = next((name for name in preferred if name in selected_names), "")
        coverage.append(
            {
                "capability": capability,
                "required": True,
                "status": "covered" if selected else "missing",
                "skill": selected,
                "preferred_skills": preferred,
            }
        )
    selected_scenario = {
        "id": selected_bundle.get("id", ""),
        "name": selected_bundle.get("name", selected_bundle.get("id", "")),
        "match_score": score_bundle_for_profile(selected_bundle, profile) if selected_bundle else 0,
    }
    selection_quality = build_selection_quality(
        task_profile=profile,
        selected_bundle=selected_bundle,
        selected_scenario=selected_scenario,
        coverage=coverage,
        pruned_skills=pruned_names,
    )
    selection_trace = build_selection_trace(
        router_mode="deterministic_mesh_router",
        strategy=strategy,
        task_profile=profile,
        selected_bundle=selected_bundle,
        selected_scenario=selected_scenario,
        candidate_skills=selected_skills,
        routed_skills=routed_skills,
        coverage=coverage,
        required_skill_names=required_names,
        pruned_skill_names=pruned_names,
        invariant_capabilities=invariant_capabilities,
        selection_quality=selection_quality,
    )
    stage_map = (
        scenario_stage_skill_map(selected_bundle.get("id", ""), selected_skill_names(routed_skills))
        if use_stage_ordered_output
        else {}
    )
    stage_by_name = {name: stage for stage, names in stage_map.items() for name in names}
    ordered_names = [name for stage in PIPELINE_STAGE_ORDER for name in stage_map.get(stage, [])] if use_stage_ordered_output else []
    for skill in routed_skills:
        name = skill["name"]
        if name not in ordered_names:
            ordered_names.append(name)
            stage_by_name[name] = skill_stage_for_item(skill)
    execution_plan = [
        {
            "order": index,
            "skill": name,
            "instruction": f"Apply `{name}` during the `{stage_by_name.get(name, 'production')}` stage, then record evidence and unresolved assumptions.",
        }
        for index, name in enumerate(ordered_names, start=1)
    ]
    explanations = build_selection_explanations(selected_bundle, routed_skills, coverage) if selected_bundle else []
    explanations.append(
        {
            "type": "router",
            "name": "smart",
            "role": "mesh",
            "confidence": 0.8,
            "matched_capabilities": invariant_capabilities,
            "selection_reason": "Selected skills from task profile, trusted scenario bundle, invariants, and overlap-group pruning.",
        }
    )
    contract_graph = build_contract_graph(routed_skills)
    contract_diagnostics = build_contract_diagnostics(routed_skills, contract_graph)
    execution_graph = (
        contract_graph
        if contract_graph.get("mode") == "contract" and contract_graph.get("acyclic", True)
        else build_execution_graph(routed_skills)
    )
    pipeline_plan = build_pipeline_plan(
        task=task,
        task_profile=profile,
        selected_bundle=selected_bundle,
        selected_skills=routed_skills,
        coverage=coverage,
        execution_graph=execution_graph,
        invariants=invariants,
    )
    return {
        "router": {
            "mode": "deterministic_mesh_router",
            "version": ROUTER_VERSION,
            "strategy": strategy,
            "strategy_profile": {
                "fast": "minimum required gates plus non-verification task matches",
                "balanced": "required gates plus task-matched skills up to max_skills",
                "deep": "required gates plus verification and review depth before other optional skills",
            }.get(strategy, "required gates plus task-matched skills"),
        },
        "task_profile": profile,
        "selected_scenario": selected_scenario,
        "skills": routed_skills,
        "bundles": [selected_bundle] if selected_bundle else [],
        "coverage": coverage,
        "selection_quality": selection_quality,
        "selection_trace": selection_trace,
        "execution_plan": execution_plan,
        "selection_explanations": explanations,
        "execution_graph": execution_graph,
        "contract_diagnostics": contract_diagnostics,
        "pipeline_plan": pipeline_plan,
        "invariant_capabilities": invariant_capabilities,
        "pruned_skills": pruned_names,
    }
