from __future__ import annotations

import re
from collections.abc import Iterable


ROUTER_VERSION = 1

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
    normalized = normalize_task_text(label)
    if normalized in CURRENT_CONTEXT_LABELS:
        return "current"
    if normalized in HISTORY_CONTEXT_LABELS:
        return "history"
    if normalized in STALE_CONTEXT_LABELS:
        return "stale"
    return ""


def parse_structured_context_text(task: str) -> dict:
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


def _signal_score(text: str, signals: Iterable[str]) -> int:
    score = 0
    distinctive_score = 0
    for signal in signals:
        normalized_signal = normalize_task_text(signal)
        if normalized_signal and normalized_signal in text:
            signal_score = 4 if " " in normalized_signal else 2
            score += signal_score
            if normalized_signal not in AMBIGUOUS_PROFILE_SIGNALS:
                distinctive_score += signal_score
    if score and not distinctive_score:
        return 0
    return score


def build_task_profile(task: str) -> dict:
    intent = split_current_intent_text(task)
    full_text = normalize_task_text(task)
    text = intent["current_intent_text"] if intent["current_intent_detected"] else full_text
    history_text = intent["history_context_text"]

    def profile_score(profile: dict) -> int:
        current_score = _signal_score(text, profile["signals"])
        if not intent["current_intent_detected"]:
            return current_score
        if current_score <= 0:
            return 0
        history_score = _signal_score(history_text, profile["signals"])
        return current_score + int(history_score * HISTORY_CONTEXT_WEIGHT)

    best = max(SCENARIO_PROFILES, key=lambda profile: (profile_score(profile), profile["task_type"]))
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
        "execution_plan": execution_plan,
        "selection_explanations": explanations,
        "pipeline_plan": pipeline_plan,
        "contract_diagnostics": contract_diagnostics,
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
    ("preflight", ["security-", "compliance-", "content-claims-compliance-filter"]),
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
        "execution_plan": execution_plan,
        "selection_explanations": explanations,
        "execution_graph": execution_graph,
        "contract_diagnostics": contract_diagnostics,
        "pipeline_plan": pipeline_plan,
        "invariant_capabilities": invariant_capabilities,
        "pruned_skills": pruned_names,
    }
