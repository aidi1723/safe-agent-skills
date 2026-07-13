from __future__ import annotations

import re

from collections.abc import Iterable, Iterator

from .intent_source import MAX_TASK_SCAN_CHARS, bound_task_text


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
        "signals": [
            "website",
            "landing page",
            "official site",
            "dashboard",
            "launch",
            "publish",
            "ui ux pro max",
            "visual designer",
            "css animation",
            "ai interface",
            "design system",
            "官网",
            "网站",
            "上线",
            "发布",
            "构建",
            "设计系统",
            "视觉",
            "css 动画",
            "ai 界面",
            "界面质感",
        ],
    },
    {
        "task_type": "codebase_change_lifecycle",
        "primary_domain": "code",
        "secondary_domains": ["engineering", "ai", "security"],
        "artifact_types": ["code", "implementation_plan", "test_plan", "review_report"],
        "risk_flags": ["code_execution", "regression"],
        "required_capabilities": [
            "project_context",
            "debugging",
            "code_review",
            "regression_test",
            "simplification",
            "engineering_release",
            "ci_check",
        ],
        "signals": [
            "explore",
            "debugger",
            "test engineer",
            "simplify",
            "code lifecycle",
            "codebase change",
            "project map",
            "project-wide review",
            "项目地图",
            "项目审查",
            "项目整体审查",
            "审查整个项目",
            "整个项目",
            "优化和完善",
            "需要优化和完善",
            "疑难 bug",
            "工程全流程",
            "摸清项目",
            "把关质量",
        ],
    },
    {
        "task_type": "codebase_graph_intelligence",
        "primary_domain": "code",
        "secondary_domains": ["ai", "engineering", "security"],
        "artifact_types": ["code_graph", "architecture_report", "impact_report"],
        "risk_flags": ["mcp_config_change", "stale_index", "source_scope"],
        "required_capabilities": [
            "graph_index_boundary",
            "project_context",
            "impact_analysis",
            "source_confirmation",
            "mcp_boundary",
        ],
        "signals": [
            "mcp code graph",
            "code graph index",
            "codebase graph",
            "call graph",
            "symbol graph",
            "architecture query",
            "git diff impact",
            "impact analysis",
            "structural code exploration",
            "codebase-memory-mcp",
            "代码图谱",
            "调用图",
            "符号图",
            "影响分析",
        ],
    },
    {
        "task_type": "content_video_production",
        "primary_domain": "content",
        "secondary_domains": ["media", "research", "execution"],
        "artifact_types": ["copy", "content_matrix", "video_script", "media_plan"],
        "risk_flags": ["public_claims", "asset_rights"],
        "required_capabilities": [
            "content_strategy",
            "copywriting",
            "editorial_review",
            "video_script",
            "asset_review",
            "publish_check",
        ],
        "signals": [
            "copywriting",
            "content strategy",
            "remotion",
            "video production",
            "content matrix",
            "copy",
            "short video",
            "写文案",
            "内容矩阵",
            "一句话灵感",
            "成片",
            "短视频",
        ],
    },
    {
        "task_type": "agentic_media_production",
        "primary_domain": "media",
        "secondary_domains": ["content", "research", "execution", "ai"],
        "artifact_types": ["media_pipeline", "video_brief", "render_qa"],
        "risk_flags": ["asset_rights", "runtime_approval", "cost_budget", "public_claims"],
        "required_capabilities": [
            "agentic_video_pipeline",
            "reference_analysis",
            "provider_route",
            "cost_estimate",
            "render_qa",
            "asset_review",
        ],
        "signals": [
            "agentic video",
            "agentic media",
            "reference video",
            "reference-video",
            "paste a video",
            "tiktok video",
            "youtube short",
            "reels",
            "provider routing",
            "provider route",
            "cost estimate",
            "render qa",
            "ffprobe",
            "post-render",
            "openmontage",
            "参考视频",
            "成本估算",
            "渲染质检",
            "媒体管线",
        ],
    },
    {
        "task_type": "agent_planning_orchestration",
        "primary_domain": "ai",
        "secondary_domains": ["business", "code", "execution"],
        "artifact_types": ["requirements", "agent_plan", "workflow", "handoff_protocol"],
        "risk_flags": ["tool_overload", "role_conflict"],
        "required_capabilities": [
            "requirements",
            "workflow_decomposition",
            "agent_orchestration",
            "role_workflow",
            "multi_agent_review",
            "routing_contract",
            "output_schema_eval",
        ],
        "signals": [
            "deep interview",
            "ralplan",
            "multi agent",
            "team",
            "agent team",
            "plan decomposition",
            "fuzzy requirements",
            "模糊需求",
            "方案拆解",
            "多 agent",
            "多agent",
            "厘清",
            "协同",
        ],
    },
    {
        "task_type": "multi_platform_research_discovery",
        "primary_domain": "research",
        "secondary_domains": ["content", "security", "execution"],
        "artifact_types": ["research_brief", "source_map", "citation_plan"],
        "risk_flags": ["public_claims", "platform_terms", "account_session"],
        "required_capabilities": [
            "platform_boundary",
            "source_check",
            "freshness_check",
            "citation_check",
            "connector_boundary",
        ],
        "signals": [
            "agent-reach",
            "agent reach",
            "multi-platform search",
            "multi platform search",
            "platform search",
            "social search",
            "public-source search",
            "zero api fee",
            "reddit",
            "youtube",
            "github",
            "bilibili",
            "xiaohongshu",
            "twitter",
            "全平台搜索",
            "多平台搜索",
            "公开源采集",
            "社媒采集",
            "小红书",
            "零 api",
            "零API",
        ],
    },
    {
        "task_type": "investment_research_diligence",
        "primary_domain": "business",
        "secondary_domains": ["research", "compliance", "data"],
        "artifact_types": ["investment_memo", "risk_register", "valuation_notes"],
        "risk_flags": ["regulated_advice", "financial_claims", "source_quality"],
        "required_capabilities": [
            "investment_framework",
            "source_check",
            "valuation_assumptions",
            "bear_case",
            "regulated_boundary",
        ],
        "signals": [
            "ai-berkshire",
            "ai berkshire",
            "berkshire",
            "value investing",
            "investment research",
            "investment memo",
            "valuation assumptions",
            "bear case",
            "capital allocation",
            "buffett",
            "munger",
            "价值投资",
            "投研",
            "投资研究",
            "估值假设",
            "反方观点",
            "四大师",
            "资本配置",
        ],
    },
    {
        "task_type": "agent_role_library_governance",
        "primary_domain": "ai",
        "secondary_domains": ["business", "engineering", "security"],
        "artifact_types": ["role_catalog", "handoff_protocol", "workflow"],
        "risk_flags": ["role_conflict", "tool_overload", "supply_chain"],
        "required_capabilities": [
            "role_library_governance",
            "agent_orchestration",
            "handoff_contract",
            "role_conflict_check",
            "supply_chain_review",
        ],
        "signals": [
            "agency-agents",
            "agency agents",
            "ai agency",
            "agent role library",
            "role library",
            "expert agent",
            "expert-agent",
            "agent team service",
            "handoff",
            "全栈智能体团队",
            "智能体团队服务",
            "专家角色库",
            "角色库",
            "多 agent 编排",
            "多agent编排",
        ],
    },
    {
        "task_type": "design_md_system_governance",
        "primary_domain": "design",
        "secondary_domains": ["web", "engineering", "compliance"],
        "artifact_types": ["design_system", "design_brief", "component_contract"],
        "risk_flags": ["design_drift", "accessibility"],
        "required_capabilities": [
            "design_md_contract",
            "design_consistency",
            "token_mapping",
            "component_states",
            "accessibility",
        ],
        "signals": [
            "design.md",
            "design md",
            "google design.md",
            "google design md",
            "design system spec",
            "design system source of truth",
            "design tokens",
            "component states",
            "设计系统规范",
            "设计系统 token",
            "组件状态",
            "设计源事实",
        ],
    },
    {
        "task_type": "private_communication_governance",
        "primary_domain": "compliance",
        "secondary_domains": ["security", "ai", "engineering"],
        "artifact_types": ["privacy_threat_model", "risk_report", "data_flow"],
        "risk_flags": ["privacy", "metadata_leakage", "encryption_claims"],
        "required_capabilities": [
            "private_comms_boundary",
            "privacy_check",
            "metadata_minimization",
            "encryption_boundary",
            "abuse_handling",
        ],
        "signals": [
            "simplex chat",
            "simplex",
            "private messaging",
            "secure communication",
            "e2ee",
            "end-to-end encryption",
            "identifier minimization",
            "metadata privacy",
            "no user identifiers",
            "隐私通讯",
            "私密通讯",
            "无用户标识",
            "端到端加密",
            "元数据最小化",
            "元数据隐私",
        ],
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
        "task_type": "industry_application_orchestration",
        "primary_domain": "vertical",
        "secondary_domains": ["business", "compliance", "research", "data", "content", "commerce", "ai"],
        "artifact_types": ["solution_pack", "workflow", "industry_blueprint", "handoff_plan"],
        "risk_flags": ["regulated_advice", "privacy", "public_claims", "domain_evidence"],
        "required_capabilities": [
            "industry_intake",
            "requirements",
            "regulated_boundary",
            "domain_evidence",
            "data_quality",
            "solution_packaging",
            "content_review",
        ],
        "signals": [
            "industry solution",
            "industry application",
            "vertical solution",
            "vertical workflow",
            "solution pack",
            "healthcare",
            "clinical",
            "legal",
            "finance",
            "education",
            "manufacturing",
            "real estate",
            "saas users",
            "public sector",
            "multi industry",
            "行业",
            "垂直行业",
            "行业应用",
            "行业方案",
            "行业 ai",
            "医疗",
            "临床",
            "法务",
            "金融",
            "教育",
            "制造",
            "房地产",
            "多行业",
            "应用方案",
        ],
    },
    {
        "task_type": "claude_skills_backlog_coverage",
        "primary_domain": "ai",
        "secondary_domains": ["business", "engineering", "code", "content", "compliance", "research", "execution", "office"],
        "artifact_types": ["skill_pack", "catalog", "candidate_map", "coverage_plan"],
        "risk_flags": ["supply_chain", "routing_noise", "permission_boundary"],
        "required_capabilities": [
            "business_backlog",
            "engineering_backlog",
            "code_backlog",
            "content_backlog",
            "compliance_backlog",
            "research_backlog",
            "execution_backlog",
            "office_backlog",
            "ai_meta_backlog",
            "supply_chain_review",
        ],
        "signals": [
            "claude-skills",
            "claude skills",
            "reference-only",
            "reference only",
            "backlog",
            "candidate map",
            "candidate skill",
            "remaining skills",
            "skill backlog",
            "技能候选",
            "候选 skill",
            "候选技能",
            "剩余 skill",
            "剩余技能",
            "纳入体系",
            "补充到我们的",
            "skill库",
            "sikll",
        ],
    },
    {
        "task_type": "skill_router_review",
        "primary_domain": "ai",
        "secondary_domains": ["engineering", "code", "security"],
        "artifact_types": ["skill_pack", "catalog", "router_report"],
        "risk_flags": ["tool_overload", "policy_fragmentation", "misrouting"],
        "required_capabilities": [
            "skill_selection_quality",
            "bundle_quality",
            "routing_contract",
            "schema_contract",
            "regression_test",
            "failure_synthesis",
            "ci_check",
            "supply_chain_review",
        ],
        "signals": [
            "safe-agent-skills",
            "safe agent skills",
            "skill router",
            "smart skill",
            "skill selection",
            "skill pack",
            "auto composition",
            "automatic composition",
            "router quality",
            "misrouting",
            "tool overload",
            "policy fragmentation",
            "sikll",
            "skill库",
            "审计报告",
            "项目复查",
            "项目收尾",
            "复查收尾",
            "收尾报告",
            "写好更新记录",
            "更新记录后",
            "更新日志",
            "更新说明",
            "github 更新说明",
            "验证后发布",
            "更智能的解决方法",
            "智能解决方法",
            "智能选择",
            "自动搭配",
            "自动选择",
            "路由质量",
            "工具过载",
            "策略碎片化",
        ],
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
        "task_type": "agent_long_term_memory_governance",
        "primary_domain": "ai",
        "secondary_domains": ["data", "security", "compliance"],
        "artifact_types": ["memory_contract", "retrieval_policy", "tenant_boundary"],
        "risk_flags": ["privacy", "tenant_leakage", "stale_memory", "hidden_context"],
        "required_capabilities": [
            "memory_contract",
            "retrieval_boundary",
            "tenant_isolation",
            "forget_path",
            "source_disclosure",
        ],
        "signals": [
            "long-term memory",
            "long term memory",
            "graph memory",
            "persistent memory",
            "durable memory",
            "remember recall forget improve",
            "remember",
            "recall",
            "forget",
            "tenant isolation",
            "memory correction",
            "cognee",
            "长期记忆",
            "图谱记忆",
            "持久记忆",
            "租户隔离",
            "记忆治理",
        ],
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

NORMALIZATION_ALIASES = [
    ("sikll", "skill"),
    ("技能库", "skill库 skill pack catalog"),
    ("技能选择", "skill selection 智能选择"),
    ("自动推荐", "skill selection 自动选择"),
    ("任务编排", "auto composition automatic composition"),
    ("编排能力", "auto composition"),
    ("技能庫", "skill pack catalog"),
    ("自動推薦", "skill selection 自动选择"),
    ("任務編排", "auto composition automatic composition"),
    ("skill 選擇", "skill selection 智能选择"),
    ("執行編排", "auto composition automatic composition"),
    ("錯誤調用", "misrouting router quality"),
    ("不相關技能", "skill selection"),
    ("更聪明", "smart skill"),
]

def normalize_task_text(task: str) -> str:
    task = bound_task_text(task)
    text = task.lower().replace("-", " ").replace("_", " ")
    expansions = []
    for source, target in NORMALIZATION_ALIASES:
        if source in text:
            text = text.replace(source, target)
            if target not in text:
                expansions.append(target)
    if expansions:
        text = " ".join([text, *expansions])
    return re.sub(r"\s+", " ", text).strip()

CURRENT_INTENT_MARKER_RE = re.compile(
    r"(?:current\s+request|current\s+task|latest\s+request|now|当前请求|当前任务|最新请求|本次请求|现在)\s*[:：]",
    re.IGNORECASE,
)

HISTORY_CONTEXT_MARKER_RE = re.compile(
    r"^\s*(?:history|earlier\s+context|previous\s+context|conversation\s+history|context|历史上下文|历史|之前|先前上下文|前文)\s*[:：]\s*",
    re.IGNORECASE,
)

CURRENT_INTENT_WEIGHT = 1.0

HISTORY_CONTEXT_WEIGHT = 0.25

CURRENT_CONTEXT_LABELS = {
    "current intent",
    "current request",
    "current task",
    "latest request",
    "当前意图",
    "当前请求",
    "当前任务",
    "最新请求",
    "本次请求",
}

HISTORY_CONTEXT_LABELS = {
    "history summary",
    "history",
    "earlier context",
    "previous context",
    "conversation history",
    "context",
    "历史摘要",
    "历史上下文",
    "历史",
    "之前",
    "先前上下文",
    "前文",
}

STALE_CONTEXT_LABELS = {
    "stale context",
    "do not inherit",
    "do_not_inherit",
    "ignore context",
    "过期上下文",
    "不要继承",
    "不继承",
    "忽略上下文",
}

def structured_context_label_key(label: str) -> str:
    label = bound_task_text(label)
    normalized = normalize_task_text(label)
    if normalized in CURRENT_CONTEXT_LABELS:
        return "current"
    if normalized in HISTORY_CONTEXT_LABELS:
        return "history"
    if normalized in STALE_CONTEXT_LABELS:
        return "stale"
    return ""

def parse_structured_context_text(task: str) -> dict:
    task = bound_task_text(task)
    fields = {"current": [], "history": [], "stale": []}
    active_key = ""
    saw_label = False
    for raw_line in task.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        label_match = re.match(r"^([^:：]{1,48})\s*[:：]\s*(.*)$", line)
        if label_match:
            key = structured_context_label_key(label_match.group(1))
            if key:
                saw_label = True
                active_key = key
                value = label_match.group(2).strip()
                if value:
                    fields[key].append(value)
                continue
        if active_key:
            fields[active_key].append(line)

    current_text = normalize_task_text(" ".join(fields["current"]))
    return {
        "structured_context_detected": bool(saw_label and current_text),
        "current_intent_text": current_text,
        "history_context_text": normalize_task_text(" ".join(fields["history"])),
        "stale_context_text": normalize_task_text(" ".join(fields["stale"])),
        "stale_context_policy": "ignore_for_routing" if fields["stale"] else "",
    }

def empty_current_intent_metadata() -> dict:
    return {
        "structured_context_detected": False,
        "current_intent_detected": False,
        "current_intent_text": "",
        "history_context_text": "",
        "stale_context_text": "",
        "stale_context_policy": "",
        "current_intent_weight": CURRENT_INTENT_WEIGHT,
        "history_context_weight": 0.0,
    }

def split_current_intent_text(task: str) -> dict:
    task = bound_task_text(task)
    structured = parse_structured_context_text(task)
    if structured["structured_context_detected"]:
        return {
            "structured_context_detected": True,
            "current_intent_detected": True,
            "current_intent_text": structured["current_intent_text"],
            "history_context_text": structured["history_context_text"],
            "stale_context_text": structured["stale_context_text"],
            "stale_context_policy": structured["stale_context_policy"],
            "current_intent_weight": CURRENT_INTENT_WEIGHT,
            "history_context_weight": HISTORY_CONTEXT_WEIGHT if structured["history_context_text"] else 0.0,
        }

    match = CURRENT_INTENT_MARKER_RE.search(task)
    if not match:
        return empty_current_intent_metadata()

    history_raw = task[: match.start()].strip(" \n\t。；;")
    if not HISTORY_CONTEXT_MARKER_RE.search(history_raw):
        return empty_current_intent_metadata()

    current_raw = task[match.end() :].strip(" \n\t。；;")
    history_without_marker = HISTORY_CONTEXT_MARKER_RE.sub("", history_raw).strip(" \n\t。；;")
    if not current_raw:
        return empty_current_intent_metadata()
    return {
        "structured_context_detected": False,
        "current_intent_detected": True,
        "current_intent_text": normalize_task_text(current_raw),
        "history_context_text": normalize_task_text(history_without_marker),
        "stale_context_text": "",
        "stale_context_policy": "",
        "current_intent_weight": CURRENT_INTENT_WEIGHT,
        "history_context_weight": HISTORY_CONTEXT_WEIGHT,
    }

AMBIGUOUS_PROFILE_SIGNALS = {"report", "报告"}

PROFILE_SIGNAL_ALIASES = {
    "website_build": ("ui design", "UI 设计", "browser verification", "浏览器验证"),
    "code_review": (
        "ci troubleshooting",
        "CI 排障",
        "review code",
        "审查代码",
    ),
    "document_knowledge_base": ("docx", "DOCX", "PDF/DOCX"),
    "data_analysis": ("老板简报", "管理层简报", "executive brief", "management brief"),
    "open_source_release": (
        "发布清单",
        "release checklist",
        "推送 github",
        "推送到 github",
        "推送代码到 github",
        "push to github",
        "push changes to github",
        "push the repository to github",
        "发布更新",
        "publish update",
    ),
    "skill_router_review": ("skill 路由器",),
    "agent_planning_orchestration": ("multi-agent",),
    "multi_platform_research_discovery": ("public platforms",),
    "investment_research_diligence": ("value-investing",),
}

MAX_SCAN_CHARACTERS = MAX_TASK_SCAN_CHARS


def is_design_governance_composite(text: str) -> bool:
    text = bound_task_text(text)
    lowered = text.lower()
    return "design system" in lowered and "component states" in lowered


def _build_profile_signals_by_prefix() -> dict[str, tuple[tuple[str, str, int, int], ...]]:
    by_prefix: dict[str, list[tuple[str, str, int, int]]] = {}
    for profile_order, profile in enumerate(SCENARIO_PROFILES):
        signals = tuple(profile["signals"]) + PROFILE_SIGNAL_ALIASES.get(
            profile["task_type"], ()
        )
        seen_signals: set[str] = set()
        for signal in signals:
            normalized_signal = signal.lower()
            if (
                not normalized_signal
                or normalized_signal in seen_signals
                or normalized_signal in AMBIGUOUS_PROFILE_SIGNALS
            ):
                continue
            seen_signals.add(normalized_signal)
            score = 4 if " " in normalized_signal else 2
            by_prefix.setdefault(normalized_signal[0], []).append(
                (normalized_signal, profile["task_type"], score, profile_order)
            )
    return {
        prefix: tuple(
            sorted(definitions, key=lambda item: (-item[2], item[3], len(item[0])))
        )
        for prefix, definitions in by_prefix.items()
    }


_PROFILE_SIGNALS_BY_PREFIX = _build_profile_signals_by_prefix()


def iter_profile_signal_matches(text: str) -> Iterator[dict[str, object]]:
    """Return deterministic configured-profile matches with source offsets."""
    source = bound_task_text(text)
    for start, source_character in enumerate(source):
        prefix = source_character.lower()
        if len(prefix) != 1:
            continue
        for signal, task_type, score, _ in _PROFILE_SIGNALS_BY_PREFIX.get(prefix, ()):
            end = start + len(signal)
            if end > len(source) or source[start:end].lower() != signal:
                continue
            if not _short_ascii_signal_has_boundaries(source, start, end, signal):
                continue
            yield _profile_signal_match_item(start, end, task_type, signal, score)


def _profile_signal_match_item(
    start: int, end: int, task_type: str, signal: str, score: int
) -> dict[str, object]:
    return {
        "start": start,
        "end": end,
        "task_type": task_type,
        "signal": signal,
        "score": score,
    }


def _short_ascii_signal_has_boundaries(
    text: str, start: int, end: int, signal: str
) -> bool:
    if len(signal) > 3 or re.fullmatch(r"[a-z0-9]+", signal) is None:
        return True
    return (
        (start == 0 or not text[start - 1].isalnum() or not text[start - 1].isascii())
        and (end == len(text) or not text[end].isalnum() or not text[end].isascii())
    )

def _signal_score(text: str, signals: Iterable[str]) -> int:
    text = bound_task_text(text)
    score = 0
    distinctive_score = 0
    for signal in signals:
        normalized_signal = normalize_task_text(signal)
        if signal_matches_text(normalized_signal, text):
            signal_score = 4 if " " in normalized_signal else 2
            score += signal_score
            if normalized_signal not in AMBIGUOUS_PROFILE_SIGNALS:
                distinctive_score += signal_score
    if score and not distinctive_score:
        return 0
    return score


def _longest_matching_signal(text: str, signals: Iterable[str]) -> int:
    text = bound_task_text(text)
    return max(
        (
            len(normalized_signal)
            for signal in signals
            if (normalized_signal := normalize_task_text(signal))
            and signal_matches_text(normalized_signal, text)
        ),
        default=0,
    )

def signal_matches_text(signal: str, text: str) -> bool:
    text = bound_task_text(text)
    if not signal:
        return False
    if " " in signal:
        return signal in text
    if len(signal) <= 3 and re.fullmatch(r"[a-z0-9]+", signal):
        return re.search(rf"(?<![a-z0-9]){re.escape(signal)}(?![a-z0-9])", text) is not None
    return signal in text

def build_task_profile(task: str) -> dict:
    task = bound_task_text(task)
    intent = split_current_intent_text(task)
    full_text = normalize_task_text(task)
    text = intent["current_intent_text"] if intent["current_intent_detected"] else full_text
    history_text = intent["history_context_text"]

    def profile_score(profile: dict) -> int:
        signals = tuple(profile["signals"]) + PROFILE_SIGNAL_ALIASES.get(
            profile["task_type"], ()
        )
        current_score = _signal_score(text, signals)
        if not intent["current_intent_detected"]:
            return current_score
        if current_score <= 0:
            return 0
        history_score = _signal_score(history_text, signals)
        return current_score + int(history_score * HISTORY_CONTEXT_WEIGHT)

    def profile_rank(profile: dict) -> tuple[int, int, str]:
        signals = tuple(profile["signals"]) + PROFILE_SIGNAL_ALIASES.get(
            profile["task_type"], ()
        )
        return (
            profile_score(profile),
            _longest_matching_signal(text, signals),
            profile["task_type"],
        )

    best = max(SCENARIO_PROFILES, key=profile_rank)
    score = profile_score(best)
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
    required_capabilities = list(best["required_capabilities"])
    if best["task_type"] == "skill_router_review" and any(
        signal in text
        for signal in [
            "github",
            "release notes",
            "changelog",
            "publish",
            "更新日志",
            "更新说明",
            "发布",
            "收尾",
        ]
    ):
        if "publish_check" not in required_capabilities:
            required_capabilities.append("publish_check")
    return {
        "task_type": best["task_type"],
        "primary_domain": best["primary_domain"],
        "secondary_domains": list(best["secondary_domains"]),
        "artifact_types": list(best["artifact_types"]),
        "risk_flags": list(best["risk_flags"]),
        "required_capabilities": required_capabilities,
        "matched_signal_score": score,
        "structured_context_detected": intent["structured_context_detected"],
        "current_intent_detected": intent["current_intent_detected"],
        "current_intent_text": intent["current_intent_text"],
        "history_context_text": intent["history_context_text"],
        "stale_context_text": intent["stale_context_text"],
        "stale_context_policy": intent["stale_context_policy"],
        "current_intent_weight": intent["current_intent_weight"],
        "history_context_weight": intent["history_context_weight"],
    }

def build_profile_for_task_type(task: str, task_type: str) -> dict:
    task = bound_task_text(task)
    profile = build_task_profile(task)
    if profile["task_type"] == task_type:
        return profile
    configured = next(
        (item for item in SCENARIO_PROFILES if item["task_type"] == task_type),
        None,
    )
    if configured is None:
        return profile
    return {
        "task_type": configured["task_type"],
        "primary_domain": configured["primary_domain"],
        "secondary_domains": list(configured["secondary_domains"]),
        "artifact_types": list(configured["artifact_types"]),
        "risk_flags": list(configured["risk_flags"]),
        "required_capabilities": list(configured["required_capabilities"]),
        "matched_signal_score": max(1, profile["matched_signal_score"]),
    }

def score_bundle_for_profile(bundle: dict, task_profile: dict) -> int:
    if task_profile.get("task_type") == "general" or task_profile.get("matched_signal_score", 0) <= 0:
        return 0
    text_parts = [
        bundle.get("id", ""),
        bundle.get("name", ""),
        bundle.get("scenario", ""),
        " ".join(bundle.get("task_signals", [])),
        " ".join(capability.get("id", "") for capability in bundle.get("required_capabilities", [])),
        " ".join(
            skill_name
            for capability in bundle.get("required_capabilities", [])
            for skill_name in capability.get("preferred_skills", [])
        ),
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
    return score

def build_capability_coverage(
    bundle: dict,
    selected_skill_names: set[str],
    available_skill_names: set[str] | None = None,
    task_required_capabilities: set[str] | None = None,
) -> list[dict]:
    available_skill_names = available_skill_names or selected_skill_names
    task_required_capabilities = task_required_capabilities or set()
    coverage = []
    for capability in bundle.get("required_capabilities", []):
        capability_id = capability.get("id", "")
        preferred = capability.get("preferred_skills", [])
        selected = next((skill_name for skill_name in preferred if skill_name in selected_skill_names), "")
        available = next((skill_name for skill_name in preferred if skill_name in available_skill_names), "")
        required = bool(capability.get("required", True)) or capability_id in task_required_capabilities
        item = {
            "capability": capability_id,
            "required": required,
            "status": "covered" if selected else "missing",
            "skill": selected,
            "preferred_skills": preferred,
        }
        if not selected and available:
            item["status"] = "omitted_by_limit"
            item["skill"] = available
            item["omission_reason"] = "available_not_selected"
        coverage.append(item)
    return coverage

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

def selected_bundle_required_skill_names(
    bundle: dict,
    selected_by_name: dict[str, dict],
    task_required_capabilities: set[str] | None = None,
) -> set[str]:
    task_required_capabilities = task_required_capabilities or set()
    required = set()
    for capability in bundle.get("required_capabilities", []):
        capability_id = capability.get("id", "")
        if not capability.get("required", True) and capability_id not in task_required_capabilities:
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
