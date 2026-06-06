from __future__ import annotations

import re
from collections.abc import Iterable


ROUTER_VERSION = 1


SCENARIO_PROFILES = [
    {
        "task_type": "website_build",
        "primary_domain": "web",
        "secondary_domains": ["business", "design", "content", "engineering", "execution"],
        "artifact_types": ["website", "copy", "release_checklist"],
        "risk_flags": ["public_release"],
        "required_capabilities": [
            "requirements",
            "engineering_release",
            "ui_review",
            "design_consistency",
            "seo_copy",
            "browser_verification",
            "publish_check",
        ],
        "signals": ["website", "landing page", "official site", "dashboard", "launch", "publish", "官网", "网站", "上线", "发布", "构建"],
    },
    {
        "task_type": "code_review",
        "primary_domain": "code",
        "secondary_domains": ["security", "engineering", "ai"],
        "artifact_types": ["code", "review_report", "test_plan"],
        "risk_flags": ["code_execution", "supply_chain"],
        "required_capabilities": ["code_review", "regression_test", "schema_contract", "supply_chain_review", "ci_check"],
        "signals": ["code review", "pull request", "pr", "generated code", "bug fix", "refactor", "tests", "代码审查", "拉取请求", "修复", "测试"],
    },
    {
        "task_type": "agent_security",
        "primary_domain": "security",
        "secondary_domains": ["ai", "compliance", "execution"],
        "artifact_types": ["agent_policy", "risk_report"],
        "risk_flags": ["prompt_injection", "tool_permission", "privacy"],
        "required_capabilities": ["prompt_injection_review", "output_guardrail", "io_scanning", "privacy_check"],
        "signals": ["prompt injection", "connector", "tool permission", "agent safety", "guardrail", "sandbox", "提示词注入", "连接器", "工具权限", "沙箱"],
    },
    {
        "task_type": "document_knowledge_base",
        "primary_domain": "data",
        "secondary_domains": ["office", "ai", "research"],
        "artifact_types": ["markdown", "chunks", "knowledge_base"],
        "risk_flags": ["source_quality"],
        "required_capabilities": ["file_conversion", "document_partition", "rag_plan", "retrieval", "source_check"],
        "signals": ["pdf", "document", "markdown", "knowledge base", "docs", "office file", "文档", "知识库"],
    },
    {
        "task_type": "rag_agent",
        "primary_domain": "ai",
        "secondary_domains": ["data", "research", "security"],
        "artifact_types": ["rag_design", "retrieval_plan", "citation_contract"],
        "risk_flags": ["source_grounding", "prompt_injection"],
        "required_capabilities": ["agent_orchestration", "rag_plan", "vector_retrieval", "schema_contract", "citation_check"],
        "signals": ["rag", "retrieval", "vector", "citation", "knowledge agent", "检索", "向量", "引用", "知识代理"],
    },
    {
        "task_type": "data_analysis",
        "primary_domain": "data",
        "secondary_domains": ["office", "research"],
        "artifact_types": ["analysis_report", "chart_plan"],
        "risk_flags": ["data_quality"],
        "required_capabilities": ["data_quality", "table_analysis", "visualization", "spreadsheet_cleanup", "source_check"],
        "signals": ["dataset", "spreadsheet", "chart", "data analysis", "table", "report", "数据集", "表格", "图表", "数据分析", "报告"],
    },
    {
        "task_type": "open_source_release",
        "primary_domain": "execution",
        "secondary_domains": ["security", "compliance", "content", "research"],
        "artifact_types": ["repository", "release_notes", "public_docs"],
        "risk_flags": ["public_release", "license"],
        "required_capabilities": ["publish_check", "supply_chain_review", "license_review", "editorial_review"],
        "signals": ["open source", "release", "github", "publish repo", "public repository", "开源", "发布仓库", "公开仓库"],
    },
    {
        "task_type": "content_seo",
        "primary_domain": "content",
        "secondary_domains": ["research"],
        "artifact_types": ["article", "seo_brief", "social_copy"],
        "risk_flags": ["public_claims"],
        "required_capabilities": ["seo_copy", "editorial_review", "source_check", "social_post"],
        "signals": ["article", "seo", "social", "public content", "blog", "post", "文章", "社媒", "博客"],
    },
    {
        "task_type": "commerce_growth",
        "primary_domain": "commerce",
        "secondary_domains": ["content", "business"],
        "artifact_types": ["listing", "keyword_plan", "buyer_reply"],
        "risk_flags": ["buyer_communication"],
        "required_capabilities": ["listing", "keyword_plan", "inquiry_reply", "editorial_review"],
        "signals": ["listing", "keyword", "inquiry", "trade", "buyer", "marketplace", "商品", "关键词", "询盘", "买家"],
    },
]


def normalize_task_text(task: str) -> str:
    text = task.lower().replace("-", " ").replace("_", " ")
    return re.sub(r"\s+", " ", text).strip()


def _signal_score(text: str, signals: Iterable[str]) -> int:
    score = 0
    for signal in signals:
        normalized_signal = normalize_task_text(signal)
        if normalized_signal and normalized_signal in text:
            score += 4 if " " in normalized_signal else 2
    return score


def build_task_profile(task: str) -> dict:
    text = normalize_task_text(task)
    best = max(SCENARIO_PROFILES, key=lambda profile: (_signal_score(text, profile["signals"]), profile["task_type"]))
    score = _signal_score(text, best["signals"])
    if score <= 0:
        best = {
            "task_type": "general",
            "primary_domain": "general",
            "secondary_domains": [],
            "artifact_types": [],
            "risk_flags": [],
            "required_capabilities": [],
            "signals": [],
        }
    return {
        "task_type": best["task_type"],
        "primary_domain": best["primary_domain"],
        "secondary_domains": list(best["secondary_domains"]),
        "artifact_types": list(best["artifact_types"]),
        "risk_flags": list(best["risk_flags"]),
        "required_capabilities": list(best["required_capabilities"]),
        "matched_signal_score": score,
    }


def score_bundle_for_profile(bundle: dict, task_profile: dict) -> int:
    text_parts = [
        bundle.get("id", ""),
        bundle.get("name", ""),
        bundle.get("scenario", ""),
        " ".join(bundle.get("task_signals", [])),
    ]
    haystack = normalize_task_text(" ".join(text_parts))
    score = 0
    task_type = task_profile.get("task_type", "")
    if task_type != "general" and task_type.replace("_", "-") in bundle.get("id", ""):
        score += 8
    for capability in task_profile.get("required_capabilities", []):
        if capability.replace("_", " ") in haystack or capability in haystack:
            score += 2
    score += _signal_score(haystack, task_profile.get("artifact_types", []))
    score += _signal_score(haystack, task_profile.get("secondary_domains", []))
    for signal in bundle.get("task_signals", []):
        if normalize_task_text(signal) in haystack:
            score += 1
    return score


def build_capability_coverage(bundle: dict, selected_skill_names: set[str]) -> list[dict]:
    coverage = []
    for capability in bundle.get("required_capabilities", []):
        capability_id = capability.get("id", "")
        preferred = capability.get("preferred_skills", [])
        selected = next((skill_name for skill_name in preferred if skill_name in selected_skill_names), "")
        coverage.append(
            {
                "capability": capability_id,
                "required": bool(capability.get("required", True)),
                "status": "covered" if selected else "missing",
                "skill": selected,
                "preferred_skills": preferred,
            }
        )
    return coverage


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
    explanations = [
        {
            "type": "bundle",
            "name": bundle.get("id", ""),
            "role": "scenario",
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
        explanations.append(
            {
                "type": "skill",
                "name": skill["name"],
                "role": "core" if matched else "supplemental",
                "confidence": 0.85 if matched else 0.6,
                "matched_capabilities": matched,
                "selection_reason": (
                    f"Selected `{skill['name']}` to cover {', '.join(matched)}."
                    if matched
                    else f"Selected `{skill['name']}` as supplemental trusted guidance."
                ),
            }
        )
    return explanations


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
    if selected_bundle:
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
    routed_skills = [selected_by_name[name] for name in ordered_names[:max_skills]]
    coverage = build_capability_coverage(selected_bundle, {skill["name"] for skill in routed_skills}) if selected_bundle else []
    execution_plan = build_execution_plan(selected_bundle, routed_skills) if selected_bundle else build_execution_plan({}, routed_skills)
    explanations = build_selection_explanations(selected_bundle, routed_skills, coverage) if selected_bundle else []
    return {
        "router": {"mode": "deterministic_scenario_router", "version": ROUTER_VERSION},
        "task_profile": profile,
        "selected_scenario": {
            "id": selected_bundle.get("id", ""),
            "name": selected_bundle.get("name", selected_bundle.get("id", "")),
            "match_score": score_bundle_for_profile(selected_bundle, profile) if selected_bundle else 0,
        },
        "skills": routed_skills,
        "bundles": [selected_bundle] if selected_bundle else [],
        "coverage": coverage,
        "execution_plan": execution_plan,
        "selection_explanations": explanations,
    }


INVARIANT_CAPABILITY_SIGNALS = [
    {
        "capability": "secret_redaction",
        "signals": ["secret", "api key", "token", "password", "credential", "密钥", "秘钥", "凭证", "密码", "泄露"],
    },
    {
        "capability": "claims_compliance",
        "signals": ["claim", "compliance", "advertising", "ad law", "public copy", "合规", "广告法", "极限词", "公开文案"],
    },
    {
        "capability": "responsive_check",
        "signals": ["responsive", "viewport", "mobile", "8px", "layout", "响应式", "移动端", "视口", "前端", "ui"],
    },
    {
        "capability": "source_check",
        "signals": ["source", "citation", "fact", "evidence", "来源", "引用", "事实", "证据"],
    },
    {
        "capability": "browser_verification",
        "signals": ["browser", "playwright", "screenshot", "render", "浏览器", "截图", "渲染"],
    },
]


CAPABILITY_SKILL_PREFERENCES = {
    "secret_redaction": ["security-secret-context-redaction", "security-llm-guard-io-scanning"],
    "claims_compliance": ["content-claims-compliance-filter", "compliance-public-claim-risk-register"],
    "responsive_check": ["design-responsive-viewport-check", "design-accessibility-check"],
    "source_check": ["research-source-check", "research-citation-evidence-map"],
    "browser_verification": ["execution-playwright-browser-automation", "execution-browser-check"],
}


SKILL_STAGE_HINTS = [
    ("preflight", ["security-", "compliance-", "research-source-check", "content-claims-compliance-filter"]),
    ("source", ["research-", "data-", "office-"]),
    ("planning", ["business-", "ai-", "commerce-"]),
    ("review", ["design-", "content-", "code-"]),
    ("execution", ["execution-", "engineering-"]),
    ("verification", ["test", "check", "verify", "audit", "review"]),
]


def parse_invariant_capabilities(invariants: str | list[str] | None) -> list[str]:
    if invariants is None:
        return []
    text = " ".join(invariants) if isinstance(invariants, list) else str(invariants)
    normalized = normalize_task_text(text)
    capabilities = []
    for rule in INVARIANT_CAPABILITY_SIGNALS:
        if any(normalize_task_text(signal) in normalized for signal in rule["signals"]):
            capabilities.append(rule["capability"])
    return capabilities


def capability_skill_names(capabilities: list[str], trusted_skill_names: set[str]) -> list[str]:
    names = []
    for capability in capabilities:
        for skill_name in CAPABILITY_SKILL_PREFERENCES.get(capability, []):
            if skill_name in trusted_skill_names and skill_name not in names:
                names.append(skill_name)
                break
    return names


def select_trusted_bundle_for_profile(bundles_index: dict, profile: dict, trusted_skill_names: set[str]) -> dict:
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
        return {}
    return selected_bundle


def selected_bundle_required_skill_names(bundle: dict, selected_by_name: dict[str, dict]) -> set[str]:
    required = set()
    for capability in bundle.get("required_capabilities", []):
        if not capability.get("required", True):
            continue
        selected = next((name for name in capability.get("preferred_skills", []) if name in selected_by_name), "")
        if selected:
            required.add(selected)
    return required


def prune_overlap_skill_names(ordered_names: list[str], overlap_groups: dict | None, required_names: set[str]) -> tuple[list[str], list[str]]:
    if not overlap_groups:
        return ordered_names, []
    keep = list(ordered_names)
    pruned = []
    for group in overlap_groups.get("groups", []):
        primary = group.get("primary_skill", "")
        adjacent = set(group.get("adjacent_skills", []))
        present_adjacent = [name for name in keep if name in adjacent]
        if primary not in keep or not present_adjacent:
            continue
        for name in present_adjacent:
            if name in required_names:
                continue
            keep.remove(name)
            pruned.append(name)
    return keep, pruned


def skill_stage(skill_name: str) -> str:
    for stage, markers in SKILL_STAGE_HINTS:
        if any(marker in skill_name for marker in markers):
            return stage
    return "review"


def build_execution_graph(skills: list[dict]) -> dict:
    nodes = [
        {
            "id": f"n{index}",
            "skill": skill["name"],
            "stage": skill_stage(skill["name"]),
        }
        for index, skill in enumerate(skills, start=1)
    ]
    edges = [
        {
            "from": nodes[index]["id"],
            "to": nodes[index + 1]["id"],
        }
        for index in range(len(nodes) - 1)
    ]
    return {"schema_version": 1, "acyclic": True, "nodes": nodes, "edges": edges}


def sort_mesh_skill_names(ordered_names: list[str]) -> list[str]:
    stage_rank = {"preflight": 0, "source": 1, "planning": 2, "review": 3, "execution": 4, "verification": 5}
    return [
        name
        for _, name in sorted(
            enumerate(ordered_names),
            key=lambda item: (stage_rank.get(skill_stage(item[1]), 3), item[0]),
        )
    ]


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

    ordered_names: list[str] = []
    if selected_bundle:
        for name in selected_bundle.get("execution_order", selected_bundle.get("skills", [])):
            if name in selected_by_name and name not in ordered_names:
                ordered_names.append(name)
        for capability in selected_bundle.get("required_capabilities", []):
            for name in capability.get("preferred_skills", []):
                if name in selected_by_name and name not in ordered_names:
                    ordered_names.append(name)

    for name in capability_skill_names(invariant_capabilities, trusted_skill_names):
        if name in selected_by_name and name not in ordered_names:
            ordered_names.append(name)

    for skill in selected_skills:
        if skill.get("match_score", 0) > 0 and skill["name"] not in ordered_names:
            ordered_names.append(skill["name"])

    required_names = set(capability_skill_names(invariant_capabilities, trusted_skill_names))
    required_names.update(selected_bundle_required_skill_names(selected_bundle, selected_by_name))
    ordered_names, pruned_names = prune_overlap_skill_names(ordered_names, overlap_groups, required_names)
    for skill in selected_skills:
        if skill.get("match_score", 0) > 0 and skill["name"] not in ordered_names:
            ordered_names.append(skill["name"])
    sorted_names = sort_mesh_skill_names(ordered_names)
    strategy_limits = {"fast": min(max_skills, 5), "balanced": max_skills, "deep": max(max_skills, 10)}
    required_sorted_names = [name for name in sorted_names if name in required_names]
    optional_sorted_names = [name for name in sorted_names if name not in required_names]
    limit = max(strategy_limits.get(strategy, max_skills), len(required_sorted_names))
    final_names = required_sorted_names + optional_sorted_names[: max(0, limit - len(required_sorted_names))]
    routed_skills = [selected_by_name[name] for name in final_names]
    selected_names = {skill["name"] for skill in routed_skills}
    coverage = build_capability_coverage(selected_bundle, selected_names) if selected_bundle else []
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
    execution_plan = [
        {
            "order": index,
            "skill": skill["name"],
            "instruction": f"Apply `{skill['name']}` during the `{skill_stage(skill['name'])}` stage, then record evidence and unresolved assumptions.",
        }
        for index, skill in enumerate(routed_skills, start=1)
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
    return {
        "router": {"mode": "deterministic_mesh_router", "version": ROUTER_VERSION, "strategy": strategy},
        "task_profile": profile,
        "selected_scenario": {
            "id": selected_bundle.get("id", ""),
            "name": selected_bundle.get("name", selected_bundle.get("id", "")),
            "match_score": score_bundle_for_profile(selected_bundle, profile) if selected_bundle else 0,
        },
        "skills": routed_skills,
        "bundles": [selected_bundle] if selected_bundle else [],
        "coverage": coverage,
        "execution_plan": execution_plan,
        "selection_explanations": explanations,
        "execution_graph": build_execution_graph(routed_skills),
        "invariant_capabilities": invariant_capabilities,
        "pruned_skills": pruned_names,
    }
