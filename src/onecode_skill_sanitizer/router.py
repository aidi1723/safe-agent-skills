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
        if skill["name"] not in ordered_names:
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
        if skill["name"] not in ordered_names:
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
