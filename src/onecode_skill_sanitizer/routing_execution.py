from __future__ import annotations

import re
from collections.abc import Iterable

from .routing_profiles import normalize_task_text
from .routing_profiles import split_current_intent_text


LOW_CONFIDENCE_GENERAL_FALLBACK_SKILLS = [
    "execution-file-batch",
    "execution-rollback-checkpoint-plan",
]

LOW_CONFIDENCE_GENERAL_NOISE_SKILLS = {
    "execution-browser-check",
    "execution-browser-use-web-task",
    "execution-claude-skills-productivity-review",
    "execution-e2b-sandbox-boundary",
    "execution-file-batch",
    "execution-playwright-browser-automation",
    "execution-publish-check",
    "execution-rollback-checkpoint-plan",
}

def build_execution_plan(bundle: dict, selected_skills: list[dict]) -> list[dict]:
    selected_by_name = {skill["name"]: skill for skill in selected_skills}
    ordered_names = [name for name in bundle.get("execution_order", []) if name in selected_by_name]
    for skill in selected_skills:
        if skill.get("match_score", 0) > 0 and skill["name"] not in ordered_names:
            ordered_names.append(skill["name"])
    return [
        {
            "order": index,
            "skill": name,
            "instruction": f"Apply `{name}` guidance, then record evidence and unresolved assumptions.",
        }
        for index, name in enumerate(ordered_names, start=1)
    ]

def build_selection_explanations(bundle: dict, selected_skills: list[dict], coverage: list[dict]) -> list[dict]:
    bundle_id = bundle.get("id", "")
    skill_names = selected_skill_names(selected_skills)
    explanations = [
        {
            "type": "bundle",
            "name": bundle.get("id", ""),
            "role": "scenario",
            "execution_role": "planner",
            "confidence": 0.9,
            "matched_capabilities": [item["capability"] for item in coverage if item["status"] == "covered"],
            "selection_reason": f"Selected `{bundle.get('name', bundle.get('id', ''))}` as the closest trusted scenario bundle.",
        }
    ]
    coverage_by_skill: dict[str, list[str]] = {}
    for item in coverage:
        if item["skill"]:
            coverage_by_skill.setdefault(item["skill"], []).append(item["capability"])
    for skill in selected_skills:
        matched = coverage_by_skill.get(skill["name"], [])
        execution_role = execution_role_for_skill(skill["name"], bundle_id, skill_names)
        explanations.append(
            {
                "type": "skill",
                "name": skill["name"],
                "role": "core" if matched else "supplemental",
                "execution_role": execution_role,
                "confidence": 0.85 if matched else 0.6,
                "matched_capabilities": matched,
                "selection_reason": (
                    f"Selected `{skill['name']}` as {execution_role} guidance to cover {', '.join(matched)}."
                    if matched
                    else f"Selected `{skill['name']}` as supplemental trusted guidance."
                ),
            }
        )
    return explanations

LOW_CONFIDENCE_EXPLANATIONS = {
    "no_trusted_scenario_match": "No trusted scenario bundle matched the task.",
    "low_signal_task_profile": "The task profile had no distinctive scenario signal.",
    "direct_skill_selection_fallback": "The router used direct skill selection instead of a scenario bundle.",
    "missing_required_capability": "One or more required capabilities were not covered by selected skills.",
}

LOW_CONFIDENCE_RECOMMENDED_ACTIONS = {
    "no_trusted_scenario_match": "Record low-confidence route as a residual risk.",
    "low_signal_task_profile": "Ask for a more specific task if execution depends on scenario certainty.",
    "direct_skill_selection_fallback": "Use only the selected direct skills and avoid inferred scenario steps.",
    "missing_required_capability": "Report missing required capabilities before completion.",
}

def low_confidence_reason_codes(task_profile: dict, selected_bundle: dict, missing_required: list[dict]) -> list[str]:
    reason_codes = []
    if not selected_bundle:
        reason_codes.append("no_trusted_scenario_match")
    if int(task_profile.get("matched_signal_score", 0) or 0) <= 0:
        reason_codes.append("low_signal_task_profile")
    if not selected_bundle:
        reason_codes.append("direct_skill_selection_fallback")
    if missing_required:
        reason_codes.append("missing_required_capability")
    return list(dict.fromkeys(reason_codes))

def build_selection_quality(
    task_profile: dict,
    selected_bundle: dict,
    selected_scenario: dict,
    coverage: list[dict],
    pruned_skills: list[str] | None = None,
) -> dict:
    required_items = [item for item in coverage if item.get("required", True)]
    covered_required = [item for item in required_items if item.get("status") == "covered"]
    missing_required = [item for item in required_items if item.get("status") == "missing"]
    required_count = len(required_items)
    coverage_ratio = round(len(covered_required) / required_count, 2) if required_count else 0
    warnings = []
    if not selected_bundle:
        warnings.append("No trusted scenario matched; using direct selected skills only.")
    for item in missing_required:
        warnings.append(f"Missing required capability: {item.get('capability', '')}")
    reason_codes = low_confidence_reason_codes(task_profile, selected_bundle, missing_required)

    route_score = int(selected_scenario.get("match_score", 0) or 0)
    matched_signal_score = int(task_profile.get("matched_signal_score", 0) or 0)
    low_confidence = not selected_bundle or matched_signal_score <= 0
    if not selected_bundle or matched_signal_score <= 0:
        confidence = "low"
    elif missing_required or coverage_ratio < 0.8 or route_score < 8:
        confidence = "medium"
    else:
        confidence = "high"

    score = round(
        min(
            1.0,
            (coverage_ratio * 0.7)
            + (min(route_score, 20) / 20 * 0.2)
            + (min(matched_signal_score, 20) / 20 * 0.1),
        ),
        2,
    )
    if confidence == "low":
        score = min(score, 0.49)
    elif confidence == "medium":
        score = min(max(score, 0.5), 0.79)
    else:
        score = max(score, 0.8)

    return {
        "confidence": confidence,
        "score": score,
        "required_count": required_count,
        "covered_required_count": len(covered_required),
        "missing_required_count": len(missing_required),
        "coverage_ratio": coverage_ratio,
        "low_confidence": low_confidence,
        "warnings": warnings,
        "reason_codes": reason_codes,
        "explanations": [LOW_CONFIDENCE_EXPLANATIONS[code] for code in reason_codes],
        "recommended_actions": [LOW_CONFIDENCE_RECOMMENDED_ACTIONS[code] for code in reason_codes],
        "pruned_skills": list(pruned_skills or []),
    }

def build_selection_trace(
    router_mode: str,
    strategy: str,
    task_profile: dict,
    selected_bundle: dict,
    selected_scenario: dict,
    candidate_skills: list[dict],
    routed_skills: list[dict],
    coverage: list[dict],
    required_skill_names: set[str] | None,
    pruned_skill_names: list[str] | None,
    invariant_capabilities: list[str] | None,
    selection_quality: dict,
) -> dict:
    selected_names = set(selected_skill_names(routed_skills))
    required_names = set(required_skill_names or set())
    pruned_names = list(pruned_skill_names or [])
    pruned_set = set(pruned_names)
    coverage_by_skill: dict[str, list[str]] = {}
    required_by_skill: dict[str, bool] = {}
    for item in coverage:
        skill_name = item.get("skill", "")
        if not skill_name:
            continue
        coverage_by_skill.setdefault(skill_name, []).append(item.get("capability", ""))
        if item.get("required", True):
            required_by_skill[skill_name] = True

    candidates = []
    seen = set()
    for skill in candidate_skills:
        name = skill.get("name", "")
        if not name or name in seen:
            continue
        seen.add(name)
        selected = name in selected_names
        pruned = name in pruned_set
        required = name in required_names or required_by_skill.get(name, False)
        if selected:
            status = "selected"
        elif pruned:
            status = "pruned"
        else:
            status = "available_not_selected"
        if pruned:
            reason = "overlap_group_non_required"
        elif required and selected:
            reason = "required_capability"
        elif selected and skill.get("match_score", 0) > 0:
            reason = "direct_task_match"
        elif selected_bundle and name in selected_bundle.get("skills", []):
            reason = "scenario_bundle"
        elif selected:
            reason = "router_selected"
        else:
            reason = "not_needed_for_current_route"
        candidates.append(
            {
                "name": name,
                "status": status,
                "selected": selected,
                "required": required,
                "match_score": skill.get("match_score", 0),
                "stage": pipeline_stage_for_skill(name),
                "matched_capabilities": coverage_by_skill.get(name, []),
                "reason": reason,
            }
        )

    coverage_summary = {
        "covered": [item.get("capability", "") for item in coverage if item.get("status") == "covered"],
        "missing": [item.get("capability", "") for item in coverage if item.get("status") == "missing"],
        "omitted_by_limit": [
            item.get("capability", "") for item in coverage if item.get("status") == "omitted_by_limit"
        ],
    }
    return {
        "schema_version": 1,
        "router_mode": router_mode,
        "strategy": strategy,
        "task_profile": {
            "task_type": task_profile.get("task_type", "general"),
            "primary_domain": task_profile.get("primary_domain", "general"),
            "matched_signal_score": task_profile.get("matched_signal_score", 0),
        },
        "scenario": {
            "id": selected_scenario.get("id", ""),
            "name": selected_scenario.get("name", ""),
            "match_score": selected_scenario.get("match_score", 0),
        },
        "candidate_count": len(candidates),
        "selected_count": len(selected_names),
        "required_skill_count": len(required_names),
        "invariant_capabilities": list(invariant_capabilities or []),
        "coverage": coverage_summary,
        "pruned": [{"name": name, "reason": "overlap_group_non_required"} for name in pruned_names],
        "candidates": candidates,
        "quality": {
            "confidence": selection_quality.get("confidence", "low"),
            "score": selection_quality.get("score", 0),
            "low_confidence": selection_quality.get("low_confidence", False),
            "reason_codes": list(selection_quality.get("reason_codes", [])),
            "warnings": list(selection_quality.get("warnings", [])),
        },
        "decision_stages": [
            {
                "stage": "task_profile",
                "decision": task_profile.get("task_type", "general"),
                "score": task_profile.get("matched_signal_score", 0),
            },
            {
                "stage": "scenario_selection",
                "decision": selected_scenario.get("id", "") or "direct_skill_selection",
                "score": selected_scenario.get("match_score", 0),
            },
            {
                "stage": "capability_coverage",
                "covered_count": len(coverage_summary["covered"]),
                "missing_count": len(coverage_summary["missing"]),
                "omitted_by_limit_count": len(coverage_summary["omitted_by_limit"]),
            },
            {
                "stage": "overlap_pruning",
                "pruned_count": len(pruned_names),
            },
            {
                "stage": "final_pack",
                "selected_count": len(selected_names),
                "confidence": selection_quality.get("confidence", "low"),
            },
        ],
    }

def build_pipeline_plan(
    task: str,
    task_profile: dict,
    selected_bundle: dict,
    selected_skills: list[dict],
    coverage: list[dict],
    execution_graph: dict | None = None,
    invariants: list[str] | str | None = None,
) -> dict:
    skill_names = selected_skill_names(selected_skills)
    bundle_id = selected_bundle.get("id", "")
    source = "trusted_scenario_bundle" if bundle_id else "direct_skill_selection"
    plan_id = bundle_id or "general"
    plan_name = selected_bundle.get("name") or (selected_bundle.get("id") if bundle_id else "General")
    runtime_boundary = selected_bundle.get("safety_boundary") or "Skills provide method only; host runtime controls permissions."
    stage_skill_map = scenario_stage_skill_map(bundle_id, skill_names)
    missing_required = [
        item["capability"]
        for item in coverage
        if item.get("required", True) and item.get("status") == "missing"
    ]
    handoff_risks = []
    if missing_required:
        handoff_risks.append("Missing required capabilities: " + ", ".join(missing_required))
    if not bundle_id:
        handoff_risks.append("No trusted scenario matched; use direct selected skills only.")

    stages = [
        build_pipeline_stage(stage, skills)
        for stage, skills in stage_skill_map.items()
        if stage != "handoff" and skills
    ]
    stages.sort(key=lambda stage: PIPELINE_STAGE_ORDER.index(stage["id"]))
    stages.append(build_pipeline_stage("handoff", stage_skill_map.get("handoff", []), handoff_risks or None))

    plan = {
        "schema_version": 1,
        "id": plan_id,
        "name": plan_name,
        "mode": "method_only",
        "source": source,
        "runtime_boundary": runtime_boundary,
        "stages": stages,
        "approval_gates": build_approval_gates(task, selected_bundle, selected_skills),
    }
    if not bundle_id:
        plan["low_confidence_note"] = "No trusted scenario matched; use direct selected skills only."
        reasons = low_confidence_reason_codes(task_profile, selected_bundle, [])
        plan["low_confidence_reasons"] = reasons
        plan["low_confidence_explanations"] = [LOW_CONFIDENCE_EXPLANATIONS[code] for code in reasons]
        plan["low_confidence_recommended_actions"] = [
            LOW_CONFIDENCE_RECOMMENDED_ACTIONS[code] for code in reasons
        ]
    return plan

def should_use_lightweight_general_fallback(
    task_profile: dict,
    selected_bundle: dict,
    invariant_capabilities: Iterable[str] | None = None,
) -> bool:
    return (
        not selected_bundle
        and task_profile.get("task_type") == "general"
        and int(task_profile.get("matched_signal_score", 0) or 0) <= 0
        and not list(invariant_capabilities or [])
    )

def lightweight_general_fallback_skill_names(selected_skills: list[dict], selected_by_name: dict[str, dict]) -> list[str]:
    direct_names = [
        skill["name"]
        for skill in selected_skills
        if skill.get("match_score", 0) > 0 and skill["name"] not in LOW_CONFIDENCE_GENERAL_NOISE_SKILLS
    ]
    if direct_names:
        return direct_names
    return [name for name in LOW_CONFIDENCE_GENERAL_FALLBACK_SKILLS if name in selected_by_name]

SKILL_STAGE_HINTS = [
    ("preflight", ["security-", "compliance-", "content-claims-compliance-filter"]),
    ("source", ["research-", "data-", "office-"]),
    ("planning", ["business-", "ai-", "commerce-"]),
    ("review", ["design-", "content-", "code-"]),
    ("execution", ["execution-", "engineering-"]),
    ("verification", ["test", "check", "verify", "audit", "review"]),
]

STAGE_GATE_BY_STAGE = {
    "preflight": "preflight",
    "source": "source",
    "planning": "planning",
    "review": "review",
    "execution": "execution",
    "verification": "verification",
}

PIPELINE_STAGE_ORDER = ["preflight", "source", "planning", "production", "review", "verification", "handoff"]

PIPELINE_STAGE_INFO = {
    "preflight": {
        "name": "Preflight",
        "purpose": "Confirm task scope, safety boundary, required inputs, and missing information.",
        "inputs": ["user_task", "task_profile", "invariants"],
        "outputs": ["scope_summary", "missing_inputs", "runtime_boundary"],
        "condition": "Required inputs are known or explicitly marked missing.",
        "failure_action": "stop_and_request_missing_inputs",
        "verification": ["trusted skill status checked", "runtime boundary recorded"],
    },
    "source": {
        "name": "Source",
        "purpose": "Inventory source material, provenance, citations, and retrieved context.",
        "inputs": ["user_task", "task_profile"],
        "outputs": ["source_inventory", "provenance_notes", "source_risks"],
        "condition": "Required sources are identified or source gaps are recorded.",
        "failure_action": "record_source_gap_and_stop_if_source_is_required",
        "verification": ["source provenance checked", "citation or evidence gaps recorded"],
    },
    "planning": {
        "name": "Planning",
        "purpose": "Decompose the task, choose the method, and define the output contract.",
        "inputs": ["task_profile", "coverage", "selected_skills"],
        "outputs": ["work_plan", "output_contract", "unresolved_assumptions"],
        "condition": "Plan covers required capabilities or missing capabilities are recorded.",
        "failure_action": "revise_plan_or_mark_missing_capability",
        "verification": ["required capability coverage reviewed", "selected skill rationale recorded"],
    },
    "production": {
        "name": "Production",
        "purpose": "Apply method-only execution guidance under host-controlled permissions.",
        "inputs": ["work_plan", "selected_skills"],
        "outputs": ["draft_artifact_or_method_notes", "execution_boundary_notes"],
        "condition": "Host approval boundaries are respected before any runtime action.",
        "failure_action": "stop_before_runtime_action_and_request_approval",
        "verification": ["runtime boundary checked", "approval-sensitive actions identified"],
    },
    "review": {
        "name": "Review",
        "purpose": "Check safety, quality, compliance, schema, rights, and review risks.",
        "inputs": ["draft_artifact_or_method_notes", "coverage"],
        "outputs": ["review_findings", "risk_notes", "correction_targets"],
        "condition": "Required review risks are recorded with correction targets.",
        "failure_action": "return_to_planning_or_production_with_findings",
        "verification": ["review findings are specific", "safety and compliance boundaries preserved"],
    },
    "verification": {
        "name": "Verification",
        "purpose": "Run or plan tests, checks, schema validation, and evidence capture.",
        "inputs": ["review_findings", "selected_skills"],
        "outputs": ["verification_evidence", "failed_checks", "residual_risks"],
        "condition": "Verification evidence is recorded or unavailable checks are explained.",
        "failure_action": "record_failed_check_and_stop_before_success_claim",
        "verification": ["test or check command recorded when available", "residual risk stated"],
    },
    "handoff": {
        "name": "Handoff",
        "purpose": "Summarize outputs, unresolved risks, and next approval boundary.",
        "inputs": ["verification_evidence", "review_findings", "runtime_boundary"],
        "outputs": ["final_summary", "unresolved_risks", "next_approval_boundary"],
        "condition": "Handoff includes evidence, risks, and method-only boundary.",
        "failure_action": "revise_handoff_until_boundary_and_risks_are_explicit",
        "verification": ["unresolved risks listed", "method-only boundary repeated"],
    },
}

EXECUTION_ROLE_BY_STAGE = {
    "preflight": "preflight",
    "source": "reviewer",
    "planning": "planner",
    "production": "producer",
    "execution": "producer",
    "review": "reviewer",
    "verification": "verifier",
    "handoff": "handoff",
}

def execution_role_for_stage(stage: str) -> str:
    return EXECUTION_ROLE_BY_STAGE.get(stage, "supplemental")

def execution_role_for_skill(skill_name: str, bundle_id: str = "", skill_names: list[str] | None = None) -> str:
    if skill_names is None:
        skill_names = [skill_name]
    stage_map = scenario_stage_skill_map(bundle_id, skill_names)
    for stage, names in stage_map.items():
        if skill_name in names:
            return execution_role_for_stage(stage)
    return execution_role_for_stage(pipeline_stage_for_skill(skill_name))

SCENARIO_STAGE_SKILLS = {
    "content-video-production": {
        "preflight": ["content-strategy-matrix", "content-seo-brief"],
        "planning": ["content-brand-voice-boundary", "media-video-script-review"],
        "production": ["media-remotion-video-production-boundary"],
        "review": ["content-editorial-review", "content-claims-compliance-filter", "media-asset-review"],
        "verification": ["execution-publish-check"],
    },
    "skill-router-quality-review": {
        "preflight": ["ai-opensquilla-metaskill-workflow"],
        "planning": ["ai-opensquilla-token-routing-pattern", "ai-langchain-agent-orchestration"],
        "review": [
            "ai-tool-schema-protocol-check",
            "ai-pydantic-schema-contract",
            "ai-output-schema-eval",
            "security-supply-chain-review",
        ],
        "verification": ["code-test-regression", "engineering-ci-troubleshoot", "execution-publish-check"],
        "handoff": ["ai-rule-failure-log-synthesis"],
    },
}

RUNTIME_APPROVAL_RULES = [
    {
        "required_for": "dependency install",
        "signals": ["install dependency", "install dependencies", "npm install", "pip install", "make setup", "安装依赖"],
    },
    {
        "required_for": "shell command execution",
        "signals": ["shell command", "run command", "execute command", "run script", "bash script", "执行命令", "运行脚本"],
    },
    {
        "required_for": "browser automation",
        "signals": ["browser automation", "run browser", "playwright", "take screenshot", "浏览器自动化", "截图"],
    },
    {
        "required_for": "network access",
        "signals": ["network access", "web search", "crawl web", "download file", "upload file", "call api", "api call", "联网", "下载", "上传"],
    },
    {
        "required_for": "MCP server exposure",
        "signals": ["start mcp", "mcp server", "expose mcp", "运行 mcp"],
    },
    {
        "required_for": "proxy/wrapper startup",
        "signals": ["start proxy", "proxy server", "wrapper startup", "wrap agent", "启动代理"],
    },
    {
        "required_for": "account or API-key use",
        "signals": ["use api key", "api key", "use credential", "oauth token", "use token", "密钥", "账号", "凭证"],
    },
    {
        "required_for": "file upload or publication",
        "signals": ["publish", "upload", "release", "上线", "发布", "上传"],
    },
    {
        "required_for": "media rendering",
        "signals": ["render video", "media rendering", "remotion render", "ffmpeg", "成片", "视频渲染", "渲染"],
    },
    {
        "required_for": "paid model or provider call",
        "signals": ["paid provider", "provider call", "call openai", "openai api", "anthropic api", "elevenlabs", "fal.ai", "付费调用"],
    },
    {
        "required_for": "destructive filesystem or git action",
        "signals": ["delete file", "remove file", "git reset", "rm -rf", "rm file", "删除文件", "重置 git"],
    },
]

SKILL_APPROVAL_REQUIREMENTS = {
    "execution-browser-check": ["browser automation"],
    "execution-browser-use-web-task": ["browser automation", "network access"],
    "execution-playwright-browser-automation": ["browser automation"],
    "execution-publish-check": ["file upload or publication"],
    "media-remotion-video-production-boundary": [
        "dependency install",
        "media rendering",
        "paid model or provider call",
    ],
}

def pipeline_stage_for_skill(skill_name: str) -> str:
    if skill_name.startswith(("research-", "data-", "office-")):
        return "source"
    if any(marker in skill_name for marker in ["test", "check", "verify", "ci-troubleshoot", "publish-check"]):
        return "verification"
    if skill_name.startswith(("business-", "ai-", "commerce-")):
        return "planning"
    if skill_name.startswith(("security-", "compliance-", "content-claims")):
        return "review"
    if skill_name.startswith(("design-", "content-", "code-", "media-asset")):
        return "review"
    if skill_name.startswith(("execution-", "engineering-", "media-remotion")):
        return "production"
    return "production"

def selected_skill_names(selected_skills: list[dict]) -> list[str]:
    names = []
    for skill in selected_skills:
        name = skill.get("name", "")
        if name and name not in names:
            names.append(name)
    return names

def scenario_stage_skill_map(bundle_id: str, skill_names: list[str]) -> dict[str, list[str]]:
    stage_map = {stage: [] for stage in PIPELINE_STAGE_ORDER}
    explicit = SCENARIO_STAGE_SKILLS.get(bundle_id, {})
    assigned = set()
    for stage in PIPELINE_STAGE_ORDER:
        for name in explicit.get(stage, []):
            if name in skill_names and name not in assigned:
                stage_map[stage].append(name)
                assigned.add(name)
    for name in skill_names:
        if name in assigned:
            continue
        stage_map[pipeline_stage_for_skill(name)].append(name)
    return {stage: names for stage, names in stage_map.items() if names}

def approval_gate_text(task: str, bundle: dict, skills: list[dict]) -> str:
    intent = split_current_intent_text(task)
    task_text = intent["current_intent_text"] if intent["current_intent_detected"] else task
    parts = [
        task_text,
        bundle.get("id", ""),
        bundle.get("name", ""),
        bundle.get("scenario", ""),
        bundle.get("safety_boundary", ""),
    ]
    return normalize_task_text(" ".join(parts))

def signal_matches_approval_text(signal: str, text: str) -> bool:
    normalized_signal = normalize_task_text(signal)
    if not normalized_signal:
        return False
    if not normalized_signal.isascii():
        return normalized_signal in text
    if " " in normalized_signal:
        pattern = rf"(?<![a-z0-9]){re.escape(normalized_signal)}(?![a-z0-9])"
        return re.search(pattern, text) is not None
    pattern = rf"(?<![a-z0-9]){re.escape(normalized_signal)}(?![a-z0-9])"
    return re.search(pattern, text) is not None

def build_approval_gates(task: str, bundle: dict, skills: list[dict]) -> list[dict]:
    text = approval_gate_text(task, bundle, skills)
    required_for = []
    for rule in RUNTIME_APPROVAL_RULES:
        if any(signal_matches_approval_text(signal, text) for signal in rule["signals"]):
            required_for.append(rule["required_for"])
    for skill_name in selected_skill_names(skills):
        for approval in SKILL_APPROVAL_REQUIREMENTS.get(skill_name, []):
            if approval not in required_for:
                required_for.append(approval)
    if not required_for:
        return []
    return [
        {
            "stage": "production",
            "required_for": required_for,
            "owner": "host_runtime_or_operator",
        }
    ]

def build_pipeline_stage(stage_id: str, skills: list[str], unresolved_risks: list[str] | None = None) -> dict:
    info = PIPELINE_STAGE_INFO[stage_id]
    stage = {
        "id": stage_id,
        "name": info["name"],
        "purpose": info["purpose"],
        "skills": skills,
        "inputs": list(info["inputs"]),
        "outputs": list(info["outputs"]),
        "gate": {
            "id": f"{stage_id}_complete",
            "condition": info["condition"],
            "failure_action": info["failure_action"],
            "evidence_template": {
                "status_values": ["pending", "passed", "failed", "blocked", "skipped"],
                "required_fields": [
                    "status",
                    "evidence",
                    "failed_checks",
                    "unresolved_assumptions",
                    "residual_risks",
                ],
            },
        },
        "verification": list(info["verification"]),
    }
    if unresolved_risks:
        stage["unresolved_risks"] = unresolved_risks
    return stage

def skill_stage(skill_name: str) -> str:
    if any(marker in skill_name for marker in ["test-regression", "verify", "audit"]):
        return "verification"
    for stage, markers in SKILL_STAGE_HINTS:
        if any(marker in skill_name for marker in markers):
            return stage
    return "review"

def skill_stage_for_item(skill: dict) -> str:
    contract = skill_contract(skill)
    stage_hint = contract.get("stage_hint")
    return stage_hint if isinstance(stage_hint, str) else skill_stage(skill["name"])

def build_execution_graph(skills: list[dict]) -> dict:
    nodes = []
    for index, skill in enumerate(skills, start=1):
        stage = skill_stage_for_item(skill)
        nodes.append(
            {
                "id": f"n{index}",
                "skill": skill["name"],
                "stage": stage,
                "gate": STAGE_GATE_BY_STAGE.get(stage, "review"),
                "parallel_group": stage,
            }
        )

    stage_rank = {"preflight": 0, "source": 1, "planning": 2, "review": 3, "execution": 4, "verification": 5}
    edges = []
    for source in nodes:
        later_nodes = [
            target
            for target in nodes
            if stage_rank.get(target["stage"], 3) > stage_rank.get(source["stage"], 3)
        ]
        if not later_nodes:
            continue
        first_later_rank = min(stage_rank.get(target["stage"], 3) for target in later_nodes)
        for target in later_nodes:
            if stage_rank.get(target["stage"], 3) == first_later_rank:
                edges.append({"from": source["id"], "to": target["id"], "type": "stage_order"})

    parallel_groups: dict[str, list[str]] = {}
    for node in nodes:
        parallel_groups.setdefault(node["parallel_group"], []).append(node["id"])
    return {
        "schema_version": 1,
        "acyclic": True,
        "nodes": nodes,
        "edges": edges,
        "parallel_groups": {group: ids for group, ids in parallel_groups.items() if len(ids) > 1 or group in {"source", "review", "verification"}},
    }

def contract_artifacts(contract: dict) -> set[str]:
    artifacts = set()
    for field in ["produces_artifacts", "produces_evidence"]:
        values = contract.get(field, [])
        if isinstance(values, list):
            artifacts.update(value for value in values if isinstance(value, str) and value)
    return artifacts

def skill_contract(skill: dict) -> dict:
    contract = skill.get("contract")
    return contract if isinstance(contract, dict) else {}

def build_contract_edges(skills: list[dict], node_ids: dict[str, str]) -> list[dict]:
    edges = []
    for source in skills:
        source_contract = skill_contract(source)
        produced = contract_artifacts(source_contract)
        for target in skills:
            if source["name"] == target["name"]:
                continue
            target_contract = skill_contract(target)
            required = {
                value
                for value in target_contract.get("requires_context", [])
                if isinstance(value, str) and value
            }
            artifacts = sorted(produced & required)
            if artifacts:
                edges.append(
                    {
                        "from": node_ids[source["name"]],
                        "to": node_ids[target["name"]],
                        "type": "contract_dependency",
                        "artifacts": artifacts,
                    }
                )
            requires_after = contract_requires_after(target_contract)
            if source["name"] in requires_after:
                edges.append(
                    {
                        "from": node_ids[source["name"]],
                        "to": node_ids[target["name"]],
                        "type": "contract_requires_after",
                        "skills": [source["name"]],
                    }
                )
    return edges

def topology_layers(nodes: list[dict], edges: list[dict]) -> tuple[bool, dict[str, int]]:
    incoming = {node["id"]: set() for node in nodes}
    outgoing = {node["id"]: set() for node in nodes}
    for edge in edges:
        outgoing[edge["from"]].add(edge["to"])
        incoming[edge["to"]].add(edge["from"])

    layers: dict[str, int] = {}
    ready = sorted(node_id for node_id, sources in incoming.items() if not sources)
    layer = 0
    while ready:
        current = ready
        next_ready = []
        for node_id in current:
            layers[node_id] = layer
            for target in sorted(outgoing[node_id]):
                incoming[target].discard(node_id)
                if not incoming[target] and target not in layers and target not in next_ready:
                    next_ready.append(target)
        ready = sorted(next_ready)
        layer += 1
    return len(layers) == len(nodes), layers

def build_contract_graph(skills: list[dict]) -> dict:
    if not skills:
        return {
            "schema_version": 1,
            "mode": "contract",
            "acyclic": True,
            "nodes": [],
            "edges": [],
            "parallel_groups": {},
            "fallback_reason": "",
        }
    if any(not skill_contract(skill) for skill in skills):
        graph = build_execution_graph(skills)
        graph["mode"] = "stage_fallback"
        graph["fallback_reason"] = "missing_contract"
        return graph

    nodes = []
    for index, skill in enumerate(skills, start=1):
        contract = skill_contract(skill)
        stage = contract.get("stage_hint") if isinstance(contract.get("stage_hint"), str) else skill_stage(skill["name"])
        nodes.append(
            {
                "id": f"n{index}",
                "skill": skill["name"],
                "stage": stage,
                "gate": STAGE_GATE_BY_STAGE.get(stage, "review"),
                "parallel_group": "",
                "topology_layer": 0,
            }
        )
    node_ids = {node["skill"]: node["id"] for node in nodes}
    edges = build_contract_edges(skills, node_ids)
    acyclic, layers = topology_layers(nodes, edges)
    if not acyclic:
        return {
            "schema_version": 1,
            "mode": "contract",
            "acyclic": False,
            "nodes": nodes,
            "edges": edges,
            "parallel_groups": {},
            "fallback_reason": "contract_cycle",
        }

    parallel_groups: dict[str, list[str]] = {}
    for node in nodes:
        layer = layers.get(node["id"], 0)
        node["topology_layer"] = layer
        node["parallel_group"] = f"layer_{layer}"
        parallel_groups.setdefault(node["parallel_group"], []).append(node["id"])
    original_position = {node["id"]: index for index, node in enumerate(nodes)}
    nodes = sorted(nodes, key=lambda node: (node.get("topology_layer", 0), original_position[node["id"]]))
    return {
        "schema_version": 1,
        "mode": "contract",
        "acyclic": True,
        "nodes": nodes,
        "edges": edges,
        "parallel_groups": {group: ids for group, ids in parallel_groups.items() if len(ids) > 1},
        "fallback_reason": "",
    }

EXTERNAL_CONTEXT_ARTIFACTS = {
    "task_brief",
    "user_request",
    "workspace_context",
    "operator_input",
}

def contract_required_context(contract: dict) -> set[str]:
    values = contract.get("requires_context", [])
    if not isinstance(values, list):
        return set()
    return {value for value in values if isinstance(value, str) and value}

def contract_requires_after(contract: dict) -> set[str]:
    values = contract.get("requires_after", [])
    if not isinstance(values, list):
        return set()
    return {value for value in values if isinstance(value, str) and value}

def build_contract_diagnostics(skills: list[dict], graph: dict | None = None) -> dict:
    selected_names = {skill["name"] for skill in skills}
    produced_by: dict[str, list[str]] = {}
    for skill in skills:
        for artifact in sorted(contract_artifacts(skill_contract(skill))):
            produced_by.setdefault(artifact, []).append(skill["name"])

    missing_preconditions = []
    missing_ordering = []
    collisions = []
    seen_collisions: set[tuple[str, str]] = set()
    for skill in skills:
        contract = skill_contract(skill)
        for artifact in sorted(contract_required_context(contract)):
            if artifact in EXTERNAL_CONTEXT_ARTIFACTS or artifact in produced_by:
                continue
            missing_preconditions.append(
                {
                    "skill": skill["name"],
                    "artifact": artifact,
                    "source": "contract.requires_context",
                }
            )
        for predecessor in sorted(contract_requires_after(contract)):
            if predecessor in selected_names:
                continue
            missing_ordering.append(
                {
                    "skill": skill["name"],
                    "requires_after": predecessor,
                    "source": "contract.requires_after",
                }
            )
        for field in ["conflicts_with", "excludes"]:
            conflicts = contract.get(field, [])
            if not isinstance(conflicts, list):
                continue
            for conflict_name in conflicts:
                if not isinstance(conflict_name, str) or conflict_name not in selected_names:
                    continue
                pair = tuple(sorted([skill["name"], conflict_name]))
                if pair in seen_collisions:
                    continue
                seen_collisions.add(pair)
                collisions.append(
                    {
                        "skill": skill["name"],
                        "conflicts_with": conflict_name,
                        "source": f"contract.{field}",
                    }
                )

    graph = graph or build_contract_graph(skills)
    graph_issues = []
    if graph.get("mode") != "contract":
        graph_issues.append(
            {
                "id": "contract-graph-fallback",
                "reason": graph.get("fallback_reason", "unknown"),
            }
        )
    elif graph.get("acyclic") is False:
        graph_issues.append(
            {
                "id": "contract-graph-cycle",
                "reason": graph.get("fallback_reason", "contract_cycle"),
            }
        )

    status = "warning" if missing_preconditions or missing_ordering or collisions or graph_issues else "ok"
    return {
        "schema_version": 1,
        "status": status,
        "graph_mode": graph.get("mode", ""),
        "fallback_reason": graph.get("fallback_reason", ""),
        "missing_precondition_count": len(missing_preconditions),
        "missing_preconditions": missing_preconditions,
        "missing_ordering_count": len(missing_ordering),
        "missing_ordering": missing_ordering,
        "collision_count": len(collisions),
        "collisions": collisions,
        "graph_issue_count": len(graph_issues),
        "graph_issues": graph_issues,
    }

def sort_mesh_skill_names(ordered_names: list[str]) -> list[str]:
    stage_rank = {"preflight": 0, "source": 1, "planning": 2, "review": 3, "execution": 4, "verification": 5}
    return [
        name
        for _, name in sorted(
            enumerate(ordered_names),
            key=lambda item: (stage_rank.get(skill_stage(item[1]), 3), item[0]),
        )
    ]

def strategy_optional_skill_names(optional_names: list[str], strategy: str) -> list[str]:
    if strategy == "fast":
        return [name for name in optional_names if skill_stage(name) not in {"verification"}]
    if strategy == "deep":
        priority = {"verification": 0, "review": 1, "source": 2, "execution": 3, "planning": 4, "preflight": 5}
        return [
            name
            for _, name in sorted(
                enumerate(optional_names),
                key=lambda item: (priority.get(skill_stage(item[1]), 3), item[0]),
            )
        ]
    return optional_names

def contract_sorted_skill_names(skills_by_name: dict[str, dict], ordered_names: list[str]) -> tuple[list[str], dict]:
    skills = [skills_by_name[name] for name in ordered_names]
    graph = build_contract_graph(skills)
    if graph.get("mode") != "contract" or not graph.get("acyclic", True):
        return sort_mesh_skill_names(ordered_names), graph
    layer_by_skill = {node["skill"]: node.get("topology_layer", 0) for node in graph["nodes"]}
    position = {name: index for index, name in enumerate(ordered_names)}
    return sorted(ordered_names, key=lambda name: (layer_by_skill.get(name, 0), position[name])), graph
