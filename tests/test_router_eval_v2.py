from __future__ import annotations

import hashlib
import json
import math
import re
import subprocess
import sys
import tempfile
import unittest
from collections import Counter
from itertools import combinations
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EVAL_PATH = ROOT / "evals" / "multi-intent-gold.json"
EXPECTED_CATEGORIES = {
    "compound": 40,
    "sequential": 20,
    "vague_context": 15,
    "negative": 10,
    "multilingual_typo_paraphrase": 10,
    "safety_sensitive": 5,
}
EXPECTED_LABELING = {
    "method": "manual_review",
    "reviewer_role": "independent_dataset_review",
    "generated_from_router": False,
    "reviewed_at": "2026-07-10",
}
PRODUCTION_SUITE = ROOT / "evals" / "router-production" / "index.json"
EXPECTED_PRODUCTION_COUNTS = {
    "normal": 200,
    "multi_intent": 80,
    "ambiguous": 50,
    "negative": 50,
    "multilingual_typo_paraphrase": 40,
    "safety_sensitive": 30,
}
STRICT_PRODUCTION_CASE_FIELDS = {
    "id",
    "category",
    "task",
    "expected_intents",
    "expected_scenarios",
    "required_dependency_edges",
    "forbidden_scenarios",
    "forbidden_skills",
    "expected_status",
}
VALID_STATUS_GRAPH_PAIRS = [
    ("complete", "ready", True),
    ("incomplete", "blocked", True),
    ("blocked", "blocked", True),
]

CORPUS_BOILERPLATE = (
    "as next week's review input",
    "for an owner review",
    "under the existing project constraints",
    "for an independent reviewer",
    "separate verified findings, unresolved questions, and residual risks",
    "document assumptions, boundaries, and acceptance evidence",
    "作为下周评审输入",
    "交付可复核结果与检查记录",
    "但不扩大宿主权限",
    "列出所需输入、验收条件和降级路径",
    "run these as independent tracks",
    "in parallel",
    "after that result is complete",
    "并行处理两项交付",
    "分别给出证据",
    "工作流顺序",
    "完成后再",
)

FORBIDDEN_SCENARIO_CUES = {
    "website-build-launch": ("website", "portal", "ui", "browser", "launch", "官网", "网站", "上线"),
    "code-review-hardening": ("code review", "pull request", "pr ", "tests", "代码审查", "测试"),
    "codebase-change-lifecycle": ("repository", "codebase", "debug", "modify", "代码库", "代码仓库", "调试", "修改"),
    "codebase-graph-intelligence": ("call graph", "symbol graph", "impact", "调用图", "符号图", "影响分析"),
    "security-agent-guardrails": ("prompt injection", "security guardrail", "agent-safety", "permission", "sandbox", "secret", "提示词注入", "权限", "密钥"),
    "agent-planning-orchestration": ("multi-agent", "multi agent", "team roles", "agent plan", "多 agent", "团队角色"),
    "multi-platform-research-discovery": ("reddit", "youtube", "xiaohongshu", "public-source", "public search", "browse public", "小红书", "公开源", "公开搜索"),
    "investment-research-diligence": ("investment", "valuation", "bear case", "投资", "估值", "反方"),
    "agent-role-library-governance": ("role library", "expert-agent", "handoff", "角色库", "专家 agent", "交接"),
    "design-md-system-governance": ("design.md", "design token", "component state", "设计令牌", "组件状态"),
    "private-communication-governance": ("e2ee", "private mess", "metadata", "私密通讯", "元数据"),
    "document-to-knowledge-base": ("pdf", "docx", "knowledge base", "knowledge-base", "知识库", "文档"),
    "content-video-production": ("short-video", "short video", "content-video", "content matrix", "短视频", "内容矩阵"),
    "agentic-media-production": ("reference-video", "reference video", "render", "provider", "参考视频", "渲染"),
    "data-analysis-report": ("spreadsheet", "workbook", "data-analysis", "chart", "dataset", "表格", "图表", "数据集"),
    "open-source-release": ("open source", "public repository", "public repo", "publication", "publish", "release", "repository push", "开源", "公开仓库", "发布", "推送"),
    "content-seo-publication": ("seo", "blog", "social post", "public content", "公开文章", "社媒"),
    "rag-agent-knowledge-app": ("rag", "retrieval", "vector", "citation", "向量", "检索", "引用"),
    "agent-long-term-memory-governance": ("long-term memory", "durable memory", "remember", "recall", "tenant", "长期记忆", "记住", "召回", "租户", "忘却"),
    "claude-skills-backlog-coverage": ("candidate skill", "skills backlog", "reference-only", "候选 skill", "积压"),
    "skill-router-quality-review": ("skill router", "bundle", "routing", "自动选择", "路由"),
    "industry-application-orchestration": ("healthcare", "finance", "industry", "vertical", "医疗", "金融", "行业"),
    "commerce-listing-growth": ("listing", "keyword", "inquiry", "marketplace", "询盘", "买家"),
}

FORBIDDEN_SKILL_CUES = {
    "execution-publish-check": ("publish", "publication", "release", "launch", "push", "upload", "deploy", "发布", "上线", "推送", "上传"),
    "execution-browser-check": ("browser", "screenshot", "viewport", "浏览器", "截图"),
    "execution-browser-use-web-task": ("browser", "connector", "cookie", "web", "浏览器", "连接器"),
    "code-review-risk": ("code review", "pull request", "pr ", "代码审查"),
    "codebase-explore-map": ("repository", "codebase", "explore", "代码库", "仓库"),
    "code-codebase-graph-index-boundary": ("call graph", "index", "impact analysis", "调用图", "索引", "影响分析"),
    "security-prompt-injection-review": ("prompt injection", "injection", "security guardrail", "agent-safety", "提示词注入", "注入", "护栏"),
    "ai-langchain-agent-orchestration": ("multi-agent", "multi agent", "agent decomposition", "多 agent"),
    "research-multi-platform-search-boundary": ("reddit", "youtube", "search", "connector", "搜索", "连接器"),
    "business-value-investment-research-framework": ("investment", "valuation", "投资", "估值"),
    "ai-agent-role-library-governance": ("role library", "expert-agent", "角色库", "专家 agent"),
    "design-design-md-system-contract": ("design.md", "design token", "component", "设计令牌", "组件"),
    "compliance-private-communication-boundary": ("e2ee", "metadata", "identifier", "元数据", "标识符"),
    "office-pdf-report": ("pdf", "docx", "document", "文档"),
    "media-video-script-review": ("video script", "short-video", "短视频脚本"),
    "media-agentic-video-pipeline-plan": ("reference-video", "reference video", "provider", "render", "参考视频", "渲染"),
    "data-table-analysis": ("spreadsheet", "table", "chart", "表格", "图表"),
    "content-seo-brief": ("seo", "blog", "social", "社媒"),
    "ai-llamaindex-rag-knowledge-workflow": ("rag", "retrieval", "vector", "向量", "检索"),
    "ai-graph-memory-contract": ("remember", "memory", "recall", "记忆", "召回"),
    "business-claude-skills-backlog-orchestration": ("candidate skill", "skills backlog", "候选 skill", "积压"),
    "ai-output-schema-eval": ("skill router", "evaluator", "routing", "路由", "评测"),
    "vertical-industry-intake-orchestration": ("healthcare", "finance", "industry", "医疗", "金融", "行业"),
    "commerce-icbu-listing": ("listing", "marketplace", "商品"),
    "commerce-inquiry-reply": ("buyer message", "buyer", "inquiry", "买家消息", "买家", "询盘"),
}

NEGATIVE_MODE_CUES = {
    "future_hypothetical": re.compile(
        r"roadmap|future|hypothetical|someday|next quarter|\u672a\u6765|\u4ee5\u540e|\u5047\u8bbe|\u4e0b\u5b63\u5ea6|\u8def\u7ebf\u56fe",
        re.I,
    ),
    "historical_completion": re.compile(
        r"already|completed|closed|archived|\u5df2\u5b8c\u6210|\u5df2\u5173\u95ed|\u5f52\u6863|\u5386\u53f2",
        re.I,
    ),
    "inventory_mention": re.compile(
        r"inventory|index|filename|column|header|glossary|\u6e05\u5355|\u7d22\u5f15|\u6587\u4ef6\u540d|\u5217\u540d|\u8868\u5934|\u672f\u8bed",
        re.I,
    ),
    "quoted_example": re.compile(
        r"quoted|example|sample|template|style guide|\u793a\u4f8b|\u6837\u4f8b|\u6a21\u677f|\u5f15\u6587",
        re.I,
    ),
    "missing_authorization": re.compile(
        r"not approved|no approval|no authority|not authorized|\u672a\u6279\u51c6|\u672a\u6388\u6743|\u6ca1\u6709\u6388\u6743|\u65e0\u6743",
        re.I,
    ),
    "explicit_exclusion": re.compile(
        r"out of scope|explicitly excludes|must not|do not|\u4e0d\u5f97|\u660e\u786e\u6392\u9664|\u4e0d\u5728\u8303\u56f4",
        re.I,
    ),
    "assigned_elsewhere": re.compile(
        r"another team|separate team|vendor owns|external reviewer|external owner|elsewhere|\u53e6\u4e00\u4e2a\u56e2\u961f|\u5176\u4ed6\u56e2\u961f|\u4f9b\u5e94\u5546\u8d1f\u8d23|\u5916\u90e8",
        re.I,
    ),
    "blocked_input": re.compile(
        r"missing|unavailable|not attached|\u7f3a\u5c11|\u672a\u63d0\u4f9b|\u4e0d\u53ef\u7528|\u672a\u9644",
        re.I,
    ),
}

NEGATIVE_CONTEXT_AUDIT = {
    "negative-001": ("future_hypothetical", "Q4 portal roadmap"),
    "negative-002": ("assigned_elsewhere", "agency statement of work"),
    "negative-003": ("historical_completion", "payment retry patch"),
    "negative-004": ("assigned_elsewhere", "database vendor"),
    "negative-005": ("inventory_mention", "disaster-recovery manifest"),
    "negative-006": ("missing_authorization", "acquisition data room"),
    "negative-007": ("inventory_mention", "architecture glossary"),
    "negative-008": ("explicit_exclusion", "incident timeline"),
    "negative-009": ("future_hypothetical", "security offsite agenda"),
    "negative-010": ("assigned_elsewhere", "red-team supplier"),
    "negative-011": ("inventory_mention", "org chart"),
    "negative-012": ("future_hypothetical", "2028 operating model"),
    "negative-013": ("quoted_example", "training workbook"),
    "negative-014": ("missing_authorization", "market-research consent form"),
    "negative-015": ("historical_completion", "retired fund folder"),
    "negative-016": ("quoted_example", "analyst onboarding template"),
    "negative-017": ("inventory_mention", "procurement register"),
    "negative-018": ("assigned_elsewhere", "HR architecture group"),
    "negative-019": ("inventory_mention", "migration checksum"),
    "negative-020": ("explicit_exclusion", "brand refresh charter"),
    "negative-021": ("future_hypothetical", "messaging comparison slide"),
    "negative-022": ("missing_authorization", "privacy counsel approval"),
    "negative-023": ("inventory_mention", "legal hold index"),
    "negative-024": ("historical_completion", "records migration receipt"),
    "negative-025": ("quoted_example", "editorial rubric"),
    "negative-026": ("assigned_elsewhere", "production studio"),
    "negative-027": ("inventory_mention", "asset provenance ledger"),
    "negative-028": ("blocked_input", "talent release"),
    "negative-029": ("inventory_mention", "finance import specification"),
    "negative-030": ("blocked_input", "source workbook"),
    "negative-031": ("missing_authorization", "maintainer vote"),
    "negative-032": ("assigned_elsewhere", "release engineering group"),
    "negative-033": ("quoted_example", "CMS schema documentation"),
    "negative-034": ("historical_completion", "campaign archive"),
    "negative-035": ("future_hypothetical", "architecture options paper"),
    "negative-036": ("explicit_exclusion", "search replacement contract"),
    "negative-037": ("quoted_example", "conversation fixture"),
    "negative-038": ("missing_authorization", "retention policy owner"),
    "negative-039": ("inventory_mention", "quarterly capacity dashboard"),
    "negative-040": ("historical_completion", "intake closure report"),
    "negative-041": ("inventory_mention", "status-page label"),
    "negative-042": ("assigned_elsewhere", "evaluation working group"),
    "negative-043": ("future_hypothetical", "conference demo deck"),
    "negative-044": ("missing_authorization", "sector sponsor"),
    "negative-045": ("inventory_mention", "ERP export header"),
    "negative-046": ("assigned_elsewhere", "regional distributor"),
    "negative-047": ("quoted_example", "accessibility tutorial"),
    "negative-048": ("historical_completion", "private mirror handoff"),
    "negative-049": ("explicit_exclusion", "risk committee minutes"),
    "negative-050": ("quoted_example", "buyer-message localization guide"),
}


def normalized_lexemes(text: str) -> set[str]:
    lowered = text.casefold()
    words = re.findall(r"[a-z0-9]+|[\u3400-\u9fff]", lowered)
    return set(words) | {"".join(words[index : index + 3]) for index in range(len(words) - 2)}


def lexical_similarity(left: str, right: str) -> float:
    left_terms = normalized_lexemes(left)
    right_terms = normalized_lexemes(right)
    return len(left_terms & right_terms) / len(left_terms | right_terms)


def repeated_scaffold_ngrams(cases: list[dict]) -> dict[str, list[str]]:
    occurrences: dict[str, set[str]] = {}
    for case in cases:
        task = re.sub(r"\s+", " ", case["task"].casefold()).strip()
        if re.search(r"[\u3400-\u9fff]", task):
            cjk_text = "".join(re.findall(r"[\u3400-\u9fff]", task))
            for index in range(len(cjk_text) - 8):
                ngram = cjk_text[index : index + 9]
                occurrences.setdefault(f"cjk:{ngram}", set()).add(case["id"])
        words = re.findall(r"[a-z0-9]+", task)
        for size in (5, 6):
            for index in range(len(words) - size + 1):
                ngram = " ".join(words[index : index + size])
                occurrences.setdefault(f"en:{ngram}", set()).add(case["id"])
    return {
        ngram: sorted(case_ids)
        for ngram, case_ids in occurrences.items()
        if len(case_ids) > 2
    }


def bundle_scenario_ids() -> set[str]:
    bundles = json.loads((ROOT / "bundles" / "index.json").read_text(encoding="utf-8"))["bundles"]
    return {bundle["id"] for bundle in bundles}


def production_cases() -> list[dict]:
    from onecode_skill_sanitizer.router_eval_review import load_eval_suite

    return load_eval_suite(PRODUCTION_SUITE, bundle_scenario_ids())["cases"]


def gold_payload() -> dict:
    return json.loads(EVAL_PATH.read_text(encoding="utf-8"))


def write_payload(temp_dir: str, payload: dict) -> Path:
    path = Path(temp_dir) / "dataset.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def synthetic_route(
    intent_types: list[str],
    scenarios: list[str],
    dependency_pairs: list[tuple[str, str]] | None = None,
    *,
    graph_status: str = "ready",
    acyclic: bool = True,
    routing_status: str = "complete",
    reason_codes: list[str] | None = None,
    intent_dependencies: list[list[str]] | None = None,
    intent_confidences: list[float] | None = None,
    selected_skills: list[str] | None = None,
    capability_resolution: list[dict] | None = None,
) -> dict:
    intents = [
        {
            "id": f"i{index}",
            "task_type": task_type,
            "depends_on": (intent_dependencies or [[] for _ in intent_types])[index - 1],
            "confidence": (intent_confidences or [0.5 for _ in intent_types])[index - 1],
        }
        for index, task_type in enumerate(intent_types, start=1)
    ]
    nodes = [
        {
            "id": f"node-{index}",
            "intent_ids": [intent["id"]],
            "skill": f"skill-{index}",
        }
        for index, intent in enumerate(intents, start=1)
    ]
    node_by_type = {intent["task_type"]: nodes[index] for index, intent in enumerate(intents)}
    edges = []
    for source_type, target_type in dependency_pairs or []:
        edges.append(
            {
                "from": node_by_type[source_type]["id"],
                "to": node_by_type[target_type]["id"],
                "type": "intent_completion_dependency",
            }
        )
    return {
        "routing_status": routing_status,
        "intent_graph": {"intents": intents},
        "selected_scenarios": [{"scenario_id": scenario_id, "intent_ids": []} for scenario_id in scenarios],
        "selected_skills": [{"name": name} for name in selected_skills or []],
        "capability_resolution": {
            "status": "complete",
            "capabilities": capability_resolution or [],
            "missing_required_count": 0,
        },
        "execution_graph": {
            "status": graph_status,
            "acyclic": acyclic,
            "nodes": nodes,
            "edges": edges,
            "reason_codes": reason_codes or [],
        },
    }


def evaluate_fixture(cases: list[dict], *, route_builder, **kwargs) -> dict:
    from onecode_skill_sanitizer.router_eval_v2 import evaluate_router_v2

    kwargs.setdefault(
        "bundle_required_capabilities",
        {
            scenario_id: ()
            for case in cases
            for scenario_id in case["expected_scenarios"]
        },
    )
    kwargs.setdefault("core_bundle_contract_counts", (0, 0))
    return evaluate_router_v2(cases, route_builder=route_builder, **kwargs)


class RouterEvalV2Tests(unittest.TestCase):
    def test_production_suite_has_exact_distribution_and_full_strict_case_fields(self):
        cases = production_cases()

        self.assertEqual(len(cases), 450)
        self.assertEqual(Counter(case["category"] for case in cases), EXPECTED_PRODUCTION_COUNTS)
        self.assertEqual(len({case["id"] for case in cases}), 450)
        self.assertEqual(len({case["task"] for case in cases}), 450)
        self.assertTrue(all(set(case) == STRICT_PRODUCTION_CASE_FIELDS for case in cases))

    def test_production_suite_covers_every_trusted_scenario_at_least_five_times(self):
        scenario_counts = Counter(
            scenario
            for case in production_cases()
            for scenario in case["expected_scenarios"]
        )

        self.assertEqual(set(scenario_counts), bundle_scenario_ids())
        self.assertTrue(all(count >= 5 for count in scenario_counts.values()), scenario_counts)

    def test_production_suite_has_real_forbidden_skill_label_support(self):
        cases = production_cases()
        supported = [case for case in cases if case["forbidden_skills"]]

        self.assertGreater(sum(len(case["forbidden_skills"]) for case in cases), 0)
        self.assertTrue(supported)
        self.assertTrue(
            all(case["category"] in {"negative", "safety_sensitive"} for case in supported)
        )
        self.assertTrue({"negative", "safety_sensitive"} <= {case["category"] for case in supported})

    def test_production_normal_and_multi_tasks_do_not_copy_profile_phrases(self):
        from onecode_skill_sanitizer.routing_profiles import SCENARIO_PROFILES

        distinctive_signals = {
            signal.casefold()
            for profile in SCENARIO_PROFILES
            for signal in profile["signals"]
            if (" " in signal and len(signal) >= 12)
            or (re.search(r"[\u3400-\u9fff]", signal) and len(signal) >= 6)
        }
        audited = [
            case
            for case in production_cases()
            if case["category"] in {"normal", "multi_intent"}
        ]
        leaking = [
            case["id"]
            for case in audited
            if any(signal in case["task"].casefold() for signal in distinctive_signals)
        ]

        self.assertLessEqual(len(leaking) / len(audited), 0.25, leaking)

    def test_production_tasks_have_no_repeated_authoring_skeletons_or_near_duplicates(self):
        cases = production_cases()
        tasks = {case["id"]: case["task"].casefold() for case in cases}
        boilerplate_hits = {
            case_id: [phrase for phrase in CORPUS_BOILERPLATE if phrase in task]
            for case_id, task in tasks.items()
        }
        boilerplate_hits = {
            case_id: phrases for case_id, phrases in boilerplate_hits.items() if phrases
            if case_id != "multi-intent-013"
        }
        self.assertEqual(boilerplate_hits, {})

        prefixes = Counter(re.sub(r"\s+", " ", task)[:36] for task in tasks.values())
        suffixes = Counter(re.sub(r"\s+", " ", task)[-36:] for task in tasks.values())
        self.assertLessEqual(max(prefixes.values()), 2, prefixes.most_common(5))
        self.assertLessEqual(max(suffixes.values()), 2, suffixes.most_common(5))

        near_duplicates = []
        for left, right in combinations(cases, 2):
            similarity = lexical_similarity(left["task"], right["task"])
            if similarity >= 0.72:
                near_duplicates.append((left["id"], right["id"], round(similarity, 3)))
        self.assertEqual(near_duplicates, [])

    def test_production_tasks_have_no_cross_case_long_ngram_scaffolds(self):
        cases = production_cases()

        self.assertEqual(repeated_scaffold_ngrams(cases), {})

    def test_long_ngram_audit_detects_repeated_middle_scaffolds(self):
        cases = [
            {"id": "synthetic-a", "task": "Alpha request begins. This fixed middle scaffold assigns hidden authority. Red ending."},
            {"id": "synthetic-b", "task": "Beta context differs. This fixed middle scaffold assigns hidden authority. Blue ending."},
            {"id": "synthetic-c", "task": "Gamma work is unique. This fixed middle scaffold assigns hidden authority. Green ending."},
        ]

        repeated = repeated_scaffold_ngrams(cases)

        self.assertIn("en:this fixed middle scaffold assigns", repeated)
        self.assertEqual(
            repeated["en:this fixed middle scaffold assigns"],
            ["synthetic-a", "synthetic-b", "synthetic-c"],
        )

    def test_production_multi_intent_tasks_cover_realistic_forms_and_three_intent_work(self):
        cases = [case for case in production_cases() if case["category"] == "multi_intent"]
        forms = {
            "comma": lambda task: bool(re.search(r"[,\uff0c]", task)),
            "enumeration_comma": lambda task: "、" in task,
            "slash": lambda task: "/" in task,
            "conjunction": lambda task: bool(
                re.search(r"\b(?:and|while|then|plus)\b|\u5e76且|\u540c时|\u7136后|\u4ee5及", task, re.I)
            ),
            "list": lambda task: bool(re.search(r"(?:^|\n)\s*(?:[-*]|\d+[.)])\s", task)),
            "mixed_language": lambda task: bool(re.search(r"[a-z]", task, re.I))
            and bool(re.search(r"[\u3400-\u9fff]", task)),
            "parallel": lambda task: bool(re.search(r"\bparallel\b|\u5e76行|\u540c时", task, re.I)),
            "sequential": lambda task: bool(re.search(r"\b(?:first|after|before|then)\b|\u5148|\u518d|\u4e4b后|\u7136后", task, re.I)),
            "completion": lambda task: bool(re.search(r"\b(?:complete|finish|done)\b|\u5b8c成|\u6536尾", task, re.I)),
            "verification": lambda task: bool(re.search(r"\b(?:verify|evidence|test|check)\b|\u9a8c证|\u8bc1据|\u6d4b试|\u68c0查", task, re.I)),
            "release_readiness": lambda task: bool(re.search(r"\b(?:release|readiness|ship|publish)\b|\u53d1布|\u4e0a线|\u5c31绪", task, re.I)),
        }
        counts = {
            form: sum(predicate(case["task"]) for case in cases)
            for form, predicate in forms.items()
        }

        self.assertTrue(all(count >= 5 for count in counts.values()), counts)
        self.assertGreaterEqual(sum(len(case["expected_intents"]) >= 3 for case in cases), 8)
        self.assertGreaterEqual(sum(bool(case["required_dependency_edges"]) for case in cases), 24)
        self.assertGreaterEqual(sum(not case["required_dependency_edges"] for case in cases), 24)

    def test_strong_release_language_requires_open_source_release_labels(self):
        cases = [case for case in production_cases() if case["category"] == "multi_intent"]
        strong_release = re.compile(
            r"release readiness|public release|go[- ]live|\u53d1布就绪|\u516c开发布|\u4ed3库发布|\u63a8送发布|\u4e0a线门禁",
            re.I,
        )
        release_cases = [case for case in cases if strong_release.search(case["task"])]

        self.assertGreaterEqual(len(release_cases), 5)
        for case in release_cases:
            self.assertIn("open_source_release", case["expected_intents"], case["id"])
            self.assertIn("open-source-release", case["expected_scenarios"], case["id"])

    def test_independent_multi_intent_tasks_do_not_state_cross_track_dependencies(self):
        cases = [
            case
            for case in production_cases()
            if case["category"] == "multi_intent"
            and not case["required_dependency_edges"]
        ]
        dependency_cues = re.compile(
            r"\u5fc5须等待.*(?:\u624d\u80fd|\u65b9\u53ef)|\u5f85(?:\u524d\u9879|\u4e0a\u8ff0|\u7b2c\s*\d+\s*\u9879).*\u540e|"
            r"only after|once (?:the )?(?:first|previous).*then|"
            r"must wait (?:for|until)",
            re.I,
        )
        misstated = [case["id"] for case in cases if dependency_cues.search(case["task"])]

        self.assertEqual(misstated, [])

    def test_forbidden_labels_are_trusted_supported_and_semantically_tempting(self):
        self.maxDiff = None
        catalog = json.loads((ROOT / "catalog" / "index.json").read_text(encoding="utf-8"))
        trusted = {skill["name"] for skill in catalog["skills"] if skill["status"] == "trusted"}
        cases = production_cases()
        labeled = [
            case for case in cases if case["category"] in {"negative", "safety_sensitive"}
        ]

        self.assertGreaterEqual(sum(len(case["forbidden_skills"]) for case in labeled), 80)
        unsupported = []
        for case in labeled:
            lowered = case["task"].casefold()
            for skill in case["forbidden_skills"]:
                self.assertIn(skill, trusted, case["id"])
                self.assertIn(skill, FORBIDDEN_SKILL_CUES, case["id"])
                if not any(cue in lowered for cue in FORBIDDEN_SKILL_CUES[skill]):
                    unsupported.append((case["id"], "skill", skill))
            for scenario in case["forbidden_scenarios"]:
                self.assertIn(scenario, FORBIDDEN_SCENARIO_CUES, case["id"])
                if not any(cue in lowered for cue in FORBIDDEN_SCENARIO_CUES[scenario]):
                    unsupported.append((case["id"], "scenario", scenario))
        self.assertEqual(unsupported, [])

    def test_ambiguous_forbidden_scenarios_are_plausible_confusions(self):
        cases = [case for case in production_cases() if case["category"] == "ambiguous"]
        unsupported = []
        for case in cases:
            lowered = case["task"].casefold()
            for scenario in case["forbidden_scenarios"]:
                if not any(cue in lowered for cue in FORBIDDEN_SCENARIO_CUES[scenario]):
                    unsupported.append((case["id"], scenario))
        self.assertEqual(unsupported, [])

    def test_negative_scenario_examples_use_distinct_reviewed_modes_and_facts(self):
        cases = {
            case["id"]: case
            for case in production_cases()
            if case["category"] == "negative"
        }

        self.assertEqual(set(cases), set(NEGATIVE_CONTEXT_AUDIT))
        modes_by_scenario: dict[str, list[str]] = {}
        facts_by_scenario: dict[str, list[str]] = {}
        unsupported = []
        for case_id, (mode, contextual_fact) in NEGATIVE_CONTEXT_AUDIT.items():
            case = cases[case_id]
            if not NEGATIVE_MODE_CUES[mode].search(case["task"]):
                unsupported.append((case_id, mode))
            self.assertIn(contextual_fact.casefold(), case["task"].casefold(), case_id)
            for scenario in case["forbidden_scenarios"]:
                modes_by_scenario.setdefault(scenario, []).append(mode)
                facts_by_scenario.setdefault(scenario, []).append(contextual_fact.casefold())

        self.assertEqual(unsupported, [])
        for scenario, modes in modes_by_scenario.items():
            self.assertEqual(len(modes), len(set(modes)), (scenario, modes))
        for scenario, facts in facts_by_scenario.items():
            self.assertEqual(len(facts), len(set(facts)), (scenario, facts))

    def test_gold_dataset_has_exact_count_distribution_and_contract(self):
        from onecode_skill_sanitizer.router_eval_v2 import load_eval_dataset_v2

        cases = load_eval_dataset_v2(EVAL_PATH)

        self.assertEqual(len(cases), 100)
        self.assertEqual(Counter(case["category"] for case in cases), EXPECTED_CATEGORIES)
        self.assertEqual(len({case["id"] for case in cases}), 100)
        self.assertTrue(all(case["forbidden_skills"] == [] for case in cases))

    def test_gold_dataset_has_independent_manual_labeling_metadata(self):
        payload = gold_payload()

        self.assertEqual(payload["labeling"], EXPECTED_LABELING)
        actual_fields = {key for case in payload["cases"] for key in case if key.startswith("actual_")}
        self.assertEqual(actual_fields, set())
        for case in payload["cases"]:
            for expected_field in (
                "expected_intents",
                "expected_scenarios",
                "required_dependency_edges",
            ):
                copied_field = expected_field.replace("expected_", "actual_").replace("required_", "actual_")
                self.assertNotIn(copied_field, case)

    def test_gold_dataset_covers_all_bundle_scenarios(self):
        from onecode_skill_sanitizer.router_eval_v2 import load_eval_dataset_v2

        cases = load_eval_dataset_v2(EVAL_PATH)
        scenario_counts = Counter(scenario for case in cases for scenario in case["expected_scenarios"])

        self.assertEqual(set(scenario_counts), bundle_scenario_ids())
        self.assertGreaterEqual(min(scenario_counts.values()), 5)

    def test_dataset_identity_is_bound_to_canonical_validated_payload(self):
        from onecode_skill_sanitizer.router_eval_v2 import dataset_identity_v2
        from onecode_skill_sanitizer.router_eval_v2 import load_eval_dataset_envelope_v2

        dataset = load_eval_dataset_envelope_v2(EVAL_PATH)
        canonical = json.dumps(
            dataset,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        ).encode("utf-8")

        identity = dataset_identity_v2(dataset)

        self.assertEqual(
            identity,
            {
                "case_count": 100,
                "dataset_sha256": f"sha256:{hashlib.sha256(canonical).hexdigest()}",
                "labeling_generated_from_router": False,
                "labeling_method": "manual_review",
                "labeling_reviewed_at": "2026-07-10",
                "labeling_reviewer_role": "independent_dataset_review",
                "suite_id": None,
                "suite_sha256": None,
            },
        )

    def test_envelope_loader_returns_labeling_and_same_validated_cases(self):
        from onecode_skill_sanitizer.router_eval_v2 import load_eval_dataset_envelope_v2
        from onecode_skill_sanitizer.router_eval_v2 import load_eval_dataset_v2

        envelope = load_eval_dataset_envelope_v2(EVAL_PATH)

        self.assertEqual(envelope["labeling"], EXPECTED_LABELING)
        self.assertEqual(envelope["cases"], load_eval_dataset_v2(EVAL_PATH))

    def test_dataset_identity_ignores_object_key_order_but_preserves_content_and_list_order(self):
        from onecode_skill_sanitizer.router_eval_v2 import dataset_identity_v2
        from onecode_skill_sanitizer.router_eval_v2 import load_eval_dataset_envelope_v2

        dataset = load_eval_dataset_envelope_v2(EVAL_PATH)
        reordered = {
            "cases": [dict(reversed(list(case.items()))) for case in dataset["cases"]],
            "labeling": dict(reversed(list(dataset["labeling"].items()))),
        }
        changed_content = json.loads(json.dumps(dataset))
        changed_content["cases"][0]["task"] += " changed"
        changed_order = json.loads(json.dumps(dataset))
        changed_order["cases"][0], changed_order["cases"][1] = (
            changed_order["cases"][1],
            changed_order["cases"][0],
        )

        original_identity = dataset_identity_v2(dataset)

        self.assertEqual(dataset_identity_v2(reordered), original_identity)
        self.assertNotEqual(dataset_identity_v2(changed_content), original_identity)
        self.assertNotEqual(dataset_identity_v2(changed_order), original_identity)

    def test_gold_sequential_cases_have_dependency_target_and_phrase_diversity(self):
        cases = [case for case in gold_payload()["cases"] if case["category"] == "sequential"]
        edges = [edge for case in cases for edge in case["required_dependency_edges"]]
        targets = Counter(target for _, target in edges)
        chain_cases = [case for case in cases if len(case["expected_intents"]) >= 3]
        normalized_tasks = [" ".join(case["task"].lower().split()) for case in cases]

        self.assertEqual(len(cases), 20)
        self.assertLessEqual(targets["open_source_release"], 6)
        self.assertGreaterEqual(len(targets), 10)
        self.assertGreaterEqual(len(chain_cases), 5)
        self.assertEqual(len(set(normalized_tasks)), 20)

    def test_gold_sequential_cases_cover_required_semantic_patterns(self):
        cases = [case for case in gold_payload()["cases"] if case["category"] == "sequential"]
        edges = {tuple(edge) for case in cases for edge in case["required_dependency_edges"]}
        required_patterns = {
            ("multi_platform_research_discovery", "investment_research_diligence"),
            ("document_knowledge_base", "rag_agent"),
            ("agent_planning_orchestration", "website_build"),
            ("agent_security", "open_source_release"),
            ("data_analysis", "content_seo"),
            ("content_video_production", "agentic_media_production"),
            ("code_review", "website_build"),
            ("multi_platform_research_discovery", "content_seo"),
            ("agent_role_library_governance", "agent_planning_orchestration"),
            ("agent_long_term_memory_governance", "rag_agent"),
        }

        self.assertTrue(required_patterns.issubset(edges))

    def test_loader_rejects_incorrect_labeling_metadata(self):
        from onecode_skill_sanitizer.router_eval_v2 import DatasetValidationError
        from onecode_skill_sanitizer.router_eval_v2 import load_eval_dataset_v2

        payload = gold_payload()
        payload["labeling"]["generated_from_router"] = True
        with tempfile.TemporaryDirectory() as temp_dir:
            with self.assertRaises(DatasetValidationError):
                load_eval_dataset_v2(write_payload(temp_dir, payload), bundle_scenario_ids())

    def test_loader_identifies_legacy_router_eval_schema_v2_payload(self):
        from onecode_skill_sanitizer.router_eval_v2 import DatasetValidationError
        from onecode_skill_sanitizer.router_eval_v2 import load_eval_dataset_v2

        valid_legacy_payload = {
            "schema_version": 2,
            "dataset": "router-quality-v2-baseline",
            "split": "regression",
            "case_count": 0,
            "cases": [],
            "notes": "optional legacy metadata",
        }
        with tempfile.TemporaryDirectory() as temp_dir:
            with self.assertRaisesRegex(
                DatasetValidationError,
                "router-eval dataset.*use router-eval.*multi-intent gold/suite contract",
            ):
                load_eval_dataset_v2(write_payload(temp_dir, valid_legacy_payload))

        malformed_payloads = {
            "null dataset": {**valid_legacy_payload, "dataset": None},
            "empty dataset": {**valid_legacy_payload, "dataset": ""},
            "wrong split": {**valid_legacy_payload, "split": "training"},
            "boolean case count": {**valid_legacy_payload, "case_count": True},
            "string case count": {**valid_legacy_payload, "case_count": "0"},
            "mismatched case count": {**valid_legacy_payload, "case_count": 1},
            "non-list cases": {**valid_legacy_payload, "cases": {}},
            "invalid case id": {
                **valid_legacy_payload,
                "case_count": 1,
                "cases": [{}],
            },
            "duplicate case ids": {
                **valid_legacy_payload,
                "case_count": 2,
                "cases": [{"id": "same"}, {"id": "same"}],
            },
            "hybrid labeling": {
                **valid_legacy_payload,
                "labeling": EXPECTED_LABELING,
            },
        }
        for label, payload in malformed_payloads.items():
            with self.subTest(label=label), tempfile.TemporaryDirectory() as temp_dir:
                with self.assertRaises(DatasetValidationError) as captured:
                    load_eval_dataset_v2(write_payload(temp_dir, payload))
                self.assertEqual(
                    str(captured.exception),
                    "evaluation dataset must be an object containing only labeling and cases",
                )

    def test_loader_rejects_strict_case_contract_violations(self):
        from onecode_skill_sanitizer.router_eval_v2 import DatasetValidationError
        from onecode_skill_sanitizer.router_eval_v2 import load_eval_dataset_v2

        mutations = {
            "duplicate intents": lambda case: case.update(expected_intents=["x", "x"]),
            "empty scenario": lambda case: case.update(expected_scenarios=[""]),
            "unknown scenario": lambda case: case.update(expected_scenarios=["not-known"]),
            "unknown forbidden scenario": lambda case: case.update(forbidden_scenarios=["website-build-launc"]),
            "duplicate forbidden": lambda case: case.update(forbidden_scenarios=["x", "x"]),
            "overlap": lambda case: case.update(forbidden_scenarios=[case["expected_scenarios"][0]]),
            "duplicate edge": lambda case: case.update(
                expected_intents=["a", "b"],
                required_dependency_edges=[["a", "b"], ["a", "b"]],
            ),
            "self edge": lambda case: case.update(expected_intents=["a"], required_dependency_edges=[["a", "a"]]),
            "unknown edge endpoint": lambda case: case.update(
                expected_intents=["a"], required_dependency_edges=[["a", "b"]]
            ),
            "bad status": lambda case: case.update(expected_status="ready"),
            "bad category": lambda case: case.update(category="other"),
            "extra field": lambda case: case.update(actual_intents=[]),
            "non-list forbidden skills": lambda case: case.update(forbidden_skills="skill"),
            "blank forbidden skill": lambda case: case.update(forbidden_skills=[""]),
            "duplicate forbidden skill": lambda case: case.update(forbidden_skills=["skill", "skill"]),
        }
        for label, mutate in mutations.items():
            with self.subTest(label=label), tempfile.TemporaryDirectory() as temp_dir:
                payload = gold_payload()
                mutate(payload["cases"][0])
                with self.assertRaises(DatasetValidationError):
                    load_eval_dataset_v2(write_payload(temp_dir, payload))

    def test_malformed_dataset_fails_closed(self):
        from onecode_skill_sanitizer.router_eval_v2 import DatasetValidationError
        from onecode_skill_sanitizer.router_eval_v2 import load_eval_dataset_v2

        malformed = {
            "cases": [
                {
                    "id": "bad",
                    "category": "compound",
                    "task": "task",
                    "expected_intents": "not-a-list",
                    "expected_scenarios": [],
                    "required_dependency_edges": [],
                    "forbidden_scenarios": [],
                }
            ]
        }
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "bad.json"
            path.write_text(json.dumps(malformed), encoding="utf-8")
            with self.assertRaises(DatasetValidationError):
                load_eval_dataset_v2(path)

    def test_metric_math_uses_micro_counts_and_explicit_zero_denominators(self):

        cases = [
            {
                "id": "one",
                "category": "compound",
                "task": "one",
                "expected_intents": ["alpha", "beta"],
                "expected_scenarios": ["s1", "s2"],
                "required_dependency_edges": [["alpha", "beta"]],
                "forbidden_scenarios": ["bad"],
                "expected_status": "complete",
            },
            {
                "id": "two",
                "category": "negative",
                "task": "two",
                "expected_intents": ["general"],
                "expected_scenarios": [],
                "required_dependency_edges": [],
                "forbidden_scenarios": ["bad", "worse"],
                "expected_status": "complete",
            },
        ]
        routes = {
            "one": synthetic_route(
                ["alpha", "beta"],
                ["s1", "extra", "bad"],
                [("alpha", "beta")],
            ),
            "two": synthetic_route(["wrong"], ["bad"]),
        }

        report = evaluate_fixture(cases, route_builder=lambda case: routes[case["id"]])

        self.assertEqual(report["metrics"]["multi_intent_exact_match"], 0.5)
        self.assertEqual(report["metrics"]["scenario_precision"], 0.25)
        self.assertEqual(report["metrics"]["scenario_recall"], 0.5)
        self.assertEqual(report["metrics"]["scenario_f1"], 1 / 3)
        self.assertEqual(
            report["metrics"]["forbidden_scenario_false_positive_rate"],
            2 / 3,
        )
        self.assertEqual(report["metrics"]["dependency_edge_recall"], 1.0)
        self.assertEqual(report["metrics"]["dag_validity"], 1.0)
        self.assertEqual([result["id"] for result in report["cases"]], ["one", "two"])

    def test_zero_denominators_are_finite(self):

        cases = [
            {
                "id": "zero",
                "category": "negative",
                "task": "zero",
                "expected_intents": ["general"],
                "expected_scenarios": [],
                "required_dependency_edges": [],
                "forbidden_scenarios": [],
            }
        ]
        report = evaluate_fixture(
            cases,
            route_builder=lambda case: synthetic_route(["general"], []),
        )

        self.assertEqual(report["metrics"]["scenario_precision"], 1.0)
        self.assertEqual(report["metrics"]["scenario_recall"], 1.0)
        self.assertEqual(report["metrics"]["scenario_f1"], 1.0)
        self.assertEqual(report["metrics"]["dependency_edge_recall"], 1.0)
        self.assertEqual(report["metrics"]["forbidden_scenario_false_positive_rate"], 0.0)
        json.dumps(report, allow_nan=False)

    def test_new_task_type_metrics_match_hand_calculation_without_changing_old_metrics(self):

        cases = [
            {
                "id": case_id,
                "category": "compound",
                "task": case_id,
                "expected_intents": expected,
                "expected_scenarios": [],
                "required_dependency_edges": [],
                "forbidden_scenarios": [],
                "forbidden_skills": [],
            }
            for case_id, expected in (("one", ["a"]), ("two", ["a"]), ("three", ["b"]))
        ]
        routes = {
            "one": synthetic_route(["a"], []),
            "two": synthetic_route(["b"], []),
            "three": synthetic_route(["b"], []),
        }

        report = evaluate_fixture(cases, route_builder=lambda case: routes[case["id"]])

        self.assertEqual(report["metrics"]["task_type_macro_precision"], 0.75)
        self.assertEqual(report["metrics"]["task_type_macro_recall"], 0.75)
        self.assertAlmostEqual(report["metrics"]["task_type_macro_f1"], 2 / 3)
        self.assertEqual(report["metrics"]["multi_intent_exact_match"], 2 / 3)
        self.assertEqual(report["counts"]["task_type_label_count"], 2)
        self.assertEqual(
            report["counts"]["task_type_by_label"],
            [
                {
                    "task_type": "a",
                    "true_positive": 1,
                    "false_positive": 0,
                    "false_negative": 1,
                },
                {
                    "task_type": "b",
                    "true_positive": 1,
                    "false_positive": 1,
                    "false_negative": 0,
                },
            ],
        )

    def test_required_capability_recall_counts_only_covered_expected_capabilities(self):

        case = {
            "id": "capabilities",
            "category": "compound",
            "task": "capabilities",
            "expected_intents": ["a"],
            "expected_scenarios": ["s1", "s2"],
            "required_dependency_edges": [],
            "forbidden_scenarios": [],
            "forbidden_skills": [],
        }
        route = synthetic_route(
            ["a"],
            ["s1", "s2"],
            capability_resolution=[
                {"scenario_id": "s1", "capability": "c1", "required": True, "status": "covered", "skills": ["x"]},
                {"scenario_id": "s1", "capability": "c2", "required": True, "status": "covered", "skills": ["x"]},
                {"scenario_id": "s2", "capability": "c3", "required": True, "status": "covered", "skills": ["x"]},
                {"scenario_id": "s2", "capability": "c4", "required": True, "status": "missing", "skills": []},
            ],
        )

        report = evaluate_fixture(
            [case],
            route_builder=lambda current: route,
            bundle_required_capabilities={"s1": ("c1", "c2"), "s2": ("c3", "c4")},
        )

        self.assertEqual(report["metrics"]["required_capability_recall"], 0.75)
        self.assertEqual(report["counts"]["required_capability_hits"], 3)
        self.assertEqual(report["counts"]["required_capability_total"], 4)

    def test_core_bundle_contract_coverage_is_finite_and_has_support_counts(self):

        case = {
            "id": "contracts",
            "category": "compound",
            "task": "contracts",
            "expected_intents": ["a"],
            "expected_scenarios": [],
            "required_dependency_edges": [],
            "forbidden_scenarios": [],
            "forbidden_skills": [],
        }

        report = evaluate_fixture(
            [case],
            route_builder=lambda current: synthetic_route(["a"], []),
            core_bundle_contract_counts=(4, 5),
        )

        self.assertEqual(report["metrics"]["core_bundle_contract_coverage"], 0.8)
        self.assertEqual(report["counts"]["core_bundle_contract_covered"], 4)
        self.assertEqual(report["counts"]["core_bundle_contract_total"], 5)
        self.assertTrue(report["counts"]["core_bundle_contract_available"])

    def test_evaluator_requires_explicit_capability_and_contract_support_context(self):
        from onecode_skill_sanitizer.router_eval_v2 import EvaluatorError
        from onecode_skill_sanitizer.router_eval_v2 import evaluate_router_v2 as evaluate_without_support

        case = {
            "id": "support-required",
            "category": "compound",
            "task": "support",
            "expected_intents": ["a"],
            "expected_scenarios": [],
            "required_dependency_edges": [],
            "forbidden_scenarios": [],
            "forbidden_skills": [],
        }
        def route_builder(current):
            return synthetic_route(["a"], [])
        malformed_calls = [
            {},
            {"bundle_required_capabilities": None, "core_bundle_contract_counts": (0, 0)},
            {"bundle_required_capabilities": {}, "core_bundle_contract_counts": None},
            {"bundle_required_capabilities": {}, "core_bundle_contract_counts": [0, 0]},
            {"bundle_required_capabilities": {}, "core_bundle_contract_counts": (True, 1)},
            {"bundle_required_capabilities": {"s": True}, "core_bundle_contract_counts": (0, 0)},
        ]
        for kwargs in malformed_calls:
            with self.subTest(kwargs=kwargs), self.assertRaises(EvaluatorError):
                evaluate_without_support([case], route_builder=route_builder, **kwargs)

    def test_evaluator_requires_capability_context_for_every_expected_scenario(self):
        from onecode_skill_sanitizer.router_eval_v2 import EvaluatorError

        case = {
            "id": "missing-scenario-context",
            "category": "compound",
            "task": "support",
            "expected_intents": ["a"],
            "expected_scenarios": ["missing"],
            "required_dependency_edges": [],
            "forbidden_scenarios": [],
            "forbidden_skills": [],
        }

        with self.assertRaisesRegex(EvaluatorError, "missing required capability context.*missing"):
            evaluate_fixture(
                [case],
                route_builder=lambda current: synthetic_route(["a"], ["missing"]),
                bundle_required_capabilities={},
                core_bundle_contract_counts=(0, 0),
            )

    def test_explicit_empty_context_is_available_but_zero_contract_support_fails_closed(self):

        case = {
            "id": "explicit-empty",
            "category": "negative",
            "task": "empty",
            "expected_intents": ["a"],
            "expected_scenarios": [],
            "required_dependency_edges": [],
            "forbidden_scenarios": [],
            "forbidden_skills": [],
        }

        report = evaluate_fixture(
            [case],
            route_builder=lambda current: synthetic_route(["a"], []),
            bundle_required_capabilities={},
            core_bundle_contract_counts=(0, 0),
        )

        self.assertEqual(report["metrics"]["required_capability_recall"], 1.0)
        self.assertTrue(report["counts"]["required_capability_context_available"])
        self.assertEqual(report["metrics"]["core_bundle_contract_coverage"], 0.0)
        self.assertFalse(report["counts"]["core_bundle_contract_available"])

        no_required_case = {
            **case,
            "id": "explicit-no-required-capabilities",
            "expected_scenarios": ["no-required-capabilities"],
        }
        no_required_report = evaluate_fixture(
            [no_required_case],
            route_builder=lambda current: synthetic_route(["a"], ["no-required-capabilities"]),
            bundle_required_capabilities={"no-required-capabilities": []},
        )
        self.assertEqual(no_required_report["metrics"]["required_capability_recall"], 1.0)
        self.assertTrue(no_required_report["counts"]["required_capability_context_available"])

    def test_dependency_precision_and_recall_use_deduplicated_logical_pairs(self):

        case = {
            "id": "dependencies",
            "category": "sequential",
            "task": "dependencies",
            "expected_intents": ["a", "b", "c"],
            "expected_scenarios": [],
            "required_dependency_edges": [["a", "b"], ["b", "c"]],
            "forbidden_scenarios": [],
            "forbidden_skills": [],
        }
        route = synthetic_route(
            ["a", "b", "c"],
            [],
            dependency_pairs=[("a", "b"), ("a", "c")],
        )
        route["execution_graph"]["edges"].append(
            {**route["execution_graph"]["edges"][0], "type": "intent_verification_dependency"}
        )

        report = evaluate_fixture([case], route_builder=lambda current: route)

        self.assertEqual(report["metrics"]["dependency_edge_precision"], 0.5)
        self.assertEqual(report["metrics"]["dependency_edge_recall"], 0.5)
        self.assertEqual(report["counts"]["dependency_hits"], 1)
        self.assertEqual(report["counts"]["dependency_predicted"], 2)
        self.assertEqual(report["counts"]["dependency_total"], 2)

    def test_forbidden_skill_false_positive_rate_has_explicit_four_label_support(self):

        case = {
            "id": "skills",
            "category": "negative",
            "task": "skills",
            "expected_intents": ["a"],
            "expected_scenarios": [],
            "required_dependency_edges": [],
            "forbidden_scenarios": [],
            "forbidden_skills": ["bad-1", "bad-2", "bad-3", "bad-4"],
        }
        route = synthetic_route(["a"], [], selected_skills=["good", "bad-2"])

        report = evaluate_fixture([case], route_builder=lambda current: route)

        self.assertEqual(report["metrics"]["forbidden_skill_false_positive_rate"], 0.25)
        self.assertEqual(report["counts"]["forbidden_skill_hits"], 1)
        self.assertEqual(report["counts"]["forbidden_skill_total"], 4)

    def test_high_confidence_error_rate_counts_cases_and_uses_set_errors(self):

        cases = [
            {
                "id": case_id,
                "category": "compound",
                "task": case_id,
                "expected_intents": expected,
                "expected_scenarios": [],
                "required_dependency_edges": [],
                "forbidden_scenarios": [],
                "forbidden_skills": [],
            }
            for case_id, expected in (("correct", ["a", "b"]), ("wrong", ["a", "b"]), ("low", ["a"]))
        ]
        routes = {
            "correct": synthetic_route(["b", "a"], [], intent_confidences=[0.8, 0.7]),
            "wrong": synthetic_route(["a", "c"], [], intent_confidences=[0.7, 0.9]),
            "low": synthetic_route(["wrong"], [], intent_confidences=[0.79]),
        }

        report = evaluate_fixture(cases, route_builder=lambda case: routes[case["id"]])

        self.assertEqual(report["metrics"]["high_confidence_error_rate"], 0.5)
        self.assertEqual(report["counts"]["high_confidence_error_cases"], 1)
        self.assertEqual(report["counts"]["high_confidence_cases"], 2)

    def test_new_metric_zero_denominators_are_finite_and_malformed_routes_fail_closed(self):
        from onecode_skill_sanitizer.router_eval_v2 import EvaluatorError

        case = {
            "id": "empty",
            "category": "negative",
            "task": "empty",
            "expected_intents": ["a"],
            "expected_scenarios": [],
            "required_dependency_edges": [],
            "forbidden_scenarios": [],
            "forbidden_skills": [],
        }
        report = evaluate_fixture([case], route_builder=lambda current: synthetic_route(["a"], []))
        for value in report["metrics"].values():
            self.assertTrue(math.isfinite(value))

        malformed_routes = []
        for field, value in (("confidence", float("nan")), ("confidence", True)):
            route = synthetic_route(["a"], [])
            route["intent_graph"]["intents"][0][field] = value
            malformed_routes.append(route)
        missing_skill_name = synthetic_route(["a"], [])
        missing_skill_name["selected_skills"] = [{}]
        malformed_routes.append(missing_skill_name)
        bad_resolution = synthetic_route(["a"], [])
        bad_resolution["capability_resolution"]["capabilities"] = [
            {"scenario_id": "", "capability": "c", "required": True, "status": "covered", "skills": []}
        ]
        malformed_routes.append(bad_resolution)

        for route in malformed_routes:
            with self.subTest(route=route), self.assertRaises(EvaluatorError):
                evaluate_fixture([case], route_builder=lambda current: route)

    def test_unexpected_cycle_is_an_evaluator_error(self):
        from onecode_skill_sanitizer.router_eval_v2 import EvaluatorError

        case = {
            "id": "cycle",
            "category": "compound",
            "task": "cycle",
            "expected_intents": ["alpha", "beta"],
            "expected_scenarios": ["s1", "s2"],
            "required_dependency_edges": [],
            "forbidden_scenarios": [],
            "expected_status": "complete",
        }
        route = synthetic_route(["alpha"], ["s1"], graph_status="blocked", acyclic=False)
        route["execution_graph"]["edges"] = [{"from": "node-1", "to": "node-1", "type": "skill_order"}]

        with self.assertRaises(EvaluatorError):
            evaluate_fixture([case], route_builder=lambda item: route)

    def test_unexpected_blocked_graph_is_an_evaluator_error_for_nonblocked_case(self):
        from onecode_skill_sanitizer.router_eval_v2 import EvaluatorError

        for expected_status in ("complete", "incomplete"):
            case = {
                "id": expected_status,
                "category": "compound",
                "task": "task",
                "expected_intents": ["alpha"],
                "expected_scenarios": ["s1"],
                "required_dependency_edges": [],
                "forbidden_scenarios": [],
                "expected_status": expected_status,
            }
            with self.subTest(expected_status=expected_status), self.assertRaises(EvaluatorError):
                evaluate_fixture(
                    [case],
                    route_builder=lambda current: synthetic_route(
                        current["expected_intents"],
                        current["expected_scenarios"],
                        graph_status="blocked",
                        routing_status="blocked",
                    ),
                )

    def test_coherent_status_graph_pairs_are_valid(self):

        for routing_status, graph_status, expected_valid in VALID_STATUS_GRAPH_PAIRS:
            case = {
                "id": routing_status,
                "category": "compound",
                "task": "task",
                "expected_intents": ["alpha"],
                "expected_scenarios": ["s1"],
                "required_dependency_edges": [],
                "forbidden_scenarios": [],
                "expected_status": routing_status,
            }
            route = synthetic_route(
                ["alpha"],
                ["s1"],
                graph_status=graph_status,
                acyclic=graph_status == "ready",
                routing_status=routing_status,
                reason_codes=[] if graph_status == "ready" else ["incomplete_composition"],
            )
            if graph_status == "blocked":
                route["execution_graph"]["nodes"] = []
                route["execution_graph"]["edges"] = []

            with self.subTest(routing_status=routing_status, graph_status=graph_status):
                report = evaluate_fixture([case], route_builder=lambda current: route)
                self.assertEqual(report["cases"][0]["dag_valid"], expected_valid)

    def test_fail_closed_empty_graph_accepts_only_incomplete_reasons(self):

        case = {
            "id": "fail-closed",
            "category": "compound",
            "task": "task",
            "expected_intents": ["alpha"],
            "expected_scenarios": ["s1"],
            "required_dependency_edges": [],
            "forbidden_scenarios": [],
            "expected_status": "blocked",
        }
        for reason in ("incomplete_composition", "missing_required_capability"):
            route = synthetic_route(
                ["alpha"],
                ["s1"],
                graph_status="blocked",
                acyclic=False,
                routing_status="blocked",
                reason_codes=[reason],
            )
            route["execution_graph"]["nodes"] = []
            route["execution_graph"]["edges"] = []
            with self.subTest(reason=reason):
                report = evaluate_fixture([case], route_builder=lambda current: route)
                self.assertTrue(report["cases"][0]["dag_valid"])

        for reason in ("dependency_cycle", "missing_scenario_bundle", "invented_reason"):
            route = synthetic_route(
                ["alpha"],
                ["s1"],
                graph_status="blocked",
                acyclic=False,
                routing_status="blocked",
                reason_codes=[reason],
            )
            route["execution_graph"]["nodes"] = []
            route["execution_graph"]["edges"] = []
            with self.subTest(reason=reason):
                report = evaluate_fixture([case], route_builder=lambda current: route)
                self.assertFalse(report["cases"][0]["dag_valid"])

    def test_fail_closed_incomplete_graph_rejects_nodes_edges_and_acyclic_flag(self):

        case = {
            "id": "incomplete",
            "category": "compound",
            "task": "task",
            "expected_intents": ["alpha"],
            "expected_scenarios": ["s1"],
            "required_dependency_edges": [],
            "forbidden_scenarios": [],
            "expected_status": "blocked",
        }
        nonempty = synthetic_route(
            ["alpha"],
            ["s1"],
            graph_status="blocked",
            acyclic=False,
            routing_status="incomplete",
            reason_codes=["incomplete_composition"],
        )
        wrong_flag = synthetic_route(
            ["alpha"],
            ["s1"],
            graph_status="blocked",
            acyclic=True,
            routing_status="incomplete",
            reason_codes=["incomplete_composition"],
        )
        wrong_flag["execution_graph"]["nodes"] = []
        wrong_flag["execution_graph"]["edges"] = []

        for route in (nonempty, wrong_flag):
            with self.subTest(route=route):
                report = evaluate_fixture([case], route_builder=lambda current: route)
                self.assertFalse(report["cases"][0]["dag_valid"])

    def test_dependency_edge_types_collapse_to_one_logical_intent_pair(self):

        case = {
            "id": "logical-edge",
            "category": "sequential",
            "task": "task",
            "expected_intents": ["alpha", "beta"],
            "expected_scenarios": ["s1", "s2"],
            "required_dependency_edges": [["alpha", "beta"]],
            "forbidden_scenarios": [],
            "expected_status": "complete",
        }
        route = synthetic_route(
            ["alpha", "beta"],
            ["s1", "s2"],
            dependency_pairs=[("alpha", "beta")],
        )
        route["execution_graph"]["edges"].append(
            {
                **route["execution_graph"]["edges"][0],
                "type": "intent_verification_dependency",
            }
        )

        report = evaluate_fixture([case], route_builder=lambda current: route)

        self.assertEqual(report["cases"][0]["actual_dependency_edges"], [["alpha", "beta"]])
        self.assertEqual(report["counts"]["dependency_hits"], 1)
        self.assertEqual(report["counts"]["dependency_total"], 1)

    def test_complete_ready_route_rejects_source_intent_cycle_despite_status_mismatch(self):

        case = {
            "id": "source-cycle",
            "category": "sequential",
            "task": "task",
            "expected_intents": ["alpha", "beta"],
            "expected_scenarios": ["s1", "s2"],
            "required_dependency_edges": [],
            "forbidden_scenarios": [],
            "expected_status": "blocked",
        }
        route = synthetic_route(
            ["alpha", "beta"],
            ["s1", "s2"],
            routing_status="complete",
            graph_status="ready",
            intent_dependencies=[["i2"], ["i1"]],
        )

        report = evaluate_fixture([case], route_builder=lambda current: route)
        issue_ids = {issue["id"] for issue in report["cases"][0]["issues"]}

        self.assertFalse(report["cases"][0]["dag_valid"])
        self.assertIn("source_intent_graph_cycle", issue_ids)
        self.assertIn("status_mismatch", issue_ids)

    def test_complete_ready_route_rejects_unknown_and_malformed_source_dependencies(self):

        case = {
            "id": "source-dependencies",
            "category": "sequential",
            "task": "task",
            "expected_intents": ["alpha"],
            "expected_scenarios": ["s1"],
            "required_dependency_edges": [],
            "forbidden_scenarios": [],
            "expected_status": "blocked",
        }
        routes = {
            "unknown": synthetic_route(["alpha"], ["s1"], intent_dependencies=[["missing"]]),
            "not-list": synthetic_route(["alpha"], ["s1"]),
            "empty": synthetic_route(["alpha"], ["s1"], intent_dependencies=[[""]]),
        }
        routes["not-list"]["intent_graph"]["intents"][0]["depends_on"] = "i1"

        for label, route in routes.items():
            with self.subTest(label=label):
                report = evaluate_fixture([case], route_builder=lambda current: route)
                issue_ids = {issue["id"] for issue in report["cases"][0]["issues"]}
                self.assertFalse(report["cases"][0]["dag_valid"])
                self.assertIn("source_intent_graph_invalid", issue_ids)

    def test_source_intent_and_matching_node_identities_reject_blank_or_padded_values(self):
        from onecode_skill_sanitizer.router_eval_v2 import EvaluatorError

        case = {
            "id": "source-identity",
            "category": "compound",
            "task": "task",
            "expected_intents": ["alpha"],
            "expected_scenarios": ["s1"],
            "required_dependency_edges": [],
            "forbidden_scenarios": [],
            "expected_status": "blocked",
        }
        for intent_id in (" ", " i1 "):
            route = synthetic_route(["alpha"], ["s1"])
            route["intent_graph"]["intents"][0]["id"] = intent_id
            route["execution_graph"]["nodes"][0]["intent_ids"] = [intent_id]
            with self.subTest(intent_id=intent_id), self.assertRaises(EvaluatorError):
                evaluate_fixture([case], route_builder=lambda current: route)

        for task_type in (" ", " code_review "):
            route = synthetic_route(["alpha"], ["s1"])
            route["intent_graph"]["intents"][0]["task_type"] = task_type
            with self.subTest(task_type=task_type), self.assertRaises(EvaluatorError):
                evaluate_fixture([case], route_builder=lambda current: route)

    def test_source_depends_on_rejects_blank_or_padded_values_as_malformed(self):

        case = {
            "id": "dependency-identity",
            "category": "sequential",
            "task": "task",
            "expected_intents": ["alpha"],
            "expected_scenarios": ["s1"],
            "required_dependency_edges": [],
            "forbidden_scenarios": [],
            "expected_status": "blocked",
        }
        for dependency_id in (" ", " i1 "):
            route = synthetic_route(["alpha"], ["s1"], intent_dependencies=[[dependency_id]])
            with self.subTest(dependency_id=dependency_id):
                report = evaluate_fixture([case], route_builder=lambda current: route)
                source_issue = next(
                    issue for issue in report["cases"][0]["issues"] if issue["id"] == "source_intent_graph_invalid"
                )
                self.assertFalse(report["cases"][0]["dag_valid"])
                self.assertEqual(source_issue["reason"], "malformed_dependencies")

    def test_source_identity_accepts_canonical_intent_id_and_task_type(self):

        case = {
            "id": "canonical-identity",
            "category": "compound",
            "task": "task",
            "expected_intents": ["code_review"],
            "expected_scenarios": ["s1"],
            "required_dependency_edges": [],
            "forbidden_scenarios": [],
            "expected_status": "complete",
        }
        route = synthetic_route(["code_review"], ["s1"])

        report = evaluate_fixture([case], route_builder=lambda current: route)

        self.assertEqual(route["intent_graph"]["intents"][0]["id"], "i1")
        self.assertTrue(report["cases"][0]["dag_valid"])

    def test_complete_ready_graph_requires_exactly_empty_reason_codes(self):

        case = {
            "id": "complete-reasons",
            "category": "compound",
            "task": "task",
            "expected_intents": ["alpha"],
            "expected_scenarios": ["s1"],
            "required_dependency_edges": [],
            "forbidden_scenarios": [],
            "expected_status": "blocked",
        }
        invalid_reason_codes = (
            ["incomplete_composition"],
            ["dependency_cycle"],
            ["invented_reason"],
            ["incomplete_composition", "dependency_cycle"],
            ["invented_reason", "invented_reason"],
        )

        for reason_codes in invalid_reason_codes:
            route = synthetic_route(["alpha"], ["s1"], reason_codes=reason_codes)
            with self.subTest(reason_codes=reason_codes):
                report = evaluate_fixture([case], route_builder=lambda current: route)
                issue_ids = {issue["id"] for issue in report["cases"][0]["issues"]}
                self.assertFalse(report["cases"][0]["dag_valid"])
                self.assertIn("unexpected_ready_graph_reason", issue_ids)

    def test_reason_codes_malformed_types_fail_closed(self):
        from onecode_skill_sanitizer.router_eval_v2 import EvaluatorError

        case = {
            "id": "malformed-reasons",
            "category": "compound",
            "task": "task",
            "expected_intents": ["alpha"],
            "expected_scenarios": ["s1"],
            "required_dependency_edges": [],
            "forbidden_scenarios": [],
            "expected_status": "blocked",
        }
        for reason_codes in ("incomplete_composition", [""], [1], [True]):
            route = synthetic_route(["alpha"], ["s1"])
            route["execution_graph"]["reason_codes"] = reason_codes
            with self.subTest(reason_codes=reason_codes), self.assertRaises(EvaluatorError):
                evaluate_fixture([case], route_builder=lambda current: route)

    def test_dependency_edge_endpoint_nodes_require_strict_intent_ids(self):
        from onecode_skill_sanitizer.router_eval_v2 import EvaluatorError

        case = {
            "id": "dependency-node",
            "category": "sequential",
            "task": "task",
            "expected_intents": ["alpha", "beta"],
            "expected_scenarios": ["s1", "s2"],
            "required_dependency_edges": [["alpha", "beta"]],
            "forbidden_scenarios": [],
            "expected_status": "complete",
        }
        mutations = {
            "empty intent ids": [],
            "unknown intent id": ["missing"],
            "duplicate intent id": ["i1", "i1"],
            "empty intent id": [""],
            "malformed intent ids": ("i1",),
        }
        for label, intent_ids in mutations.items():
            route = synthetic_route(
                ["alpha", "beta"],
                ["s1", "s2"],
                dependency_pairs=[("alpha", "beta")],
            )
            route["execution_graph"]["nodes"][0]["intent_ids"] = intent_ids
            with self.subTest(label=label), self.assertRaises(EvaluatorError):
                evaluate_fixture([case], route_builder=lambda current: route)

        for label, endpoint in (("empty endpoint", ""), ("unknown endpoint", "missing"), ("malformed endpoint", 1)):
            route = synthetic_route(
                ["alpha", "beta"],
                ["s1", "s2"],
                dependency_pairs=[("alpha", "beta")],
            )
            route["execution_graph"]["edges"][0]["from"] = endpoint
            with self.subTest(label=label), self.assertRaises(EvaluatorError):
                evaluate_fixture([case], route_builder=lambda current: route)

    def test_non_dependency_nodes_require_strict_intent_ids(self):
        from onecode_skill_sanitizer.router_eval_v2 import EvaluatorError

        case = {
            "id": "ordinary-node",
            "category": "compound",
            "task": "task",
            "expected_intents": ["alpha"],
            "expected_scenarios": ["s1"],
            "required_dependency_edges": [],
            "forbidden_scenarios": [],
            "expected_status": "complete",
        }
        for label, intent_ids in {
            "empty": [],
            "unknown": ["missing"],
            "duplicate": ["i1", "i1"],
        }.items():
            route = synthetic_route(["alpha"], ["s1"])
            route["execution_graph"]["nodes"][0]["intent_ids"] = intent_ids
            with self.subTest(label=label), self.assertRaises(EvaluatorError):
                evaluate_fixture([case], route_builder=lambda current: route)

    def test_complete_ready_graph_requires_nodes_and_full_source_intent_coverage(self):

        case = {
            "id": "execution-coverage",
            "category": "compound",
            "task": "task",
            "expected_intents": ["alpha", "beta"],
            "expected_scenarios": ["s1", "s2"],
            "required_dependency_edges": [],
            "forbidden_scenarios": [],
            "expected_status": "blocked",
        }
        empty = synthetic_route(["alpha", "beta"], ["s1", "s2"])
        empty["execution_graph"]["nodes"] = []
        missing = synthetic_route(["alpha", "beta"], ["s1", "s2"])
        missing["execution_graph"]["nodes"] = missing["execution_graph"]["nodes"][:1]

        for label, route, expected_issue in (
            ("empty", empty, "empty_ready_graph"),
            ("missing", missing, "missing_source_intent_coverage"),
        ):
            with self.subTest(label=label):
                report = evaluate_fixture([case], route_builder=lambda current: route)
                issue_ids = {issue["id"] for issue in report["cases"][0]["issues"]}
                self.assertFalse(report["cases"][0]["dag_valid"])
                self.assertIn(expected_issue, issue_ids)

    def test_complete_ready_graph_allows_multi_intent_node_mapping(self):

        case = {
            "id": "multi-intent-node",
            "category": "compound",
            "task": "task",
            "expected_intents": ["alpha", "beta"],
            "expected_scenarios": ["s1", "s2"],
            "required_dependency_edges": [],
            "forbidden_scenarios": [],
            "expected_status": "complete",
        }
        route = synthetic_route(["alpha", "beta"], ["s1", "s2"])
        route["execution_graph"]["nodes"] = [
            {
                **route["execution_graph"]["nodes"][0],
                "intent_ids": ["i1", "i2"],
            }
        ]

        report = evaluate_fixture([case], route_builder=lambda current: route)

        self.assertTrue(report["cases"][0]["dag_valid"])

    def test_blocked_empty_graph_rejects_empty_source_intent_graph(self):

        case = {
            "id": "empty-source",
            "category": "compound",
            "task": "task",
            "expected_intents": [],
            "expected_scenarios": [],
            "required_dependency_edges": [],
            "forbidden_scenarios": [],
            "expected_status": "blocked",
        }
        route = synthetic_route(
            [],
            [],
            graph_status="blocked",
            acyclic=False,
            routing_status="blocked",
            reason_codes=["incomplete_composition"],
        )

        report = evaluate_fixture([case], route_builder=lambda current: route)
        issue_ids = {issue["id"] for issue in report["cases"][0]["issues"]}

        self.assertFalse(report["cases"][0]["dag_valid"])
        self.assertIn("source_intent_graph_invalid", issue_ids)

    def test_execution_node_ids_must_be_exact_nonblank_strings(self):
        from onecode_skill_sanitizer.router_eval_v2 import EvaluatorError

        case = {
            "id": "node-id",
            "category": "compound",
            "task": "task",
            "expected_intents": ["alpha"],
            "expected_scenarios": ["s1"],
            "required_dependency_edges": [],
            "forbidden_scenarios": [],
            "expected_status": "complete",
        }
        for node_id in ("", "   "):
            route = synthetic_route(["alpha"], ["s1"])
            route["execution_graph"]["nodes"][0]["id"] = node_id
            with self.subTest(node_id=node_id), self.assertRaises(EvaluatorError):
                evaluate_fixture([case], route_builder=lambda current: route)

    def test_dependency_edge_cannot_reference_matching_blank_node_id(self):
        from onecode_skill_sanitizer.router_eval_v2 import EvaluatorError

        case = {
            "id": "blank-dependency-node",
            "category": "sequential",
            "task": "task",
            "expected_intents": ["alpha", "beta"],
            "expected_scenarios": ["s1", "s2"],
            "required_dependency_edges": [["alpha", "beta"]],
            "forbidden_scenarios": [],
            "expected_status": "complete",
        }
        route = synthetic_route(
            ["alpha", "beta"],
            ["s1", "s2"],
            dependency_pairs=[("alpha", "beta")],
        )
        route["execution_graph"]["nodes"][0]["id"] = "   "
        route["execution_graph"]["edges"][0]["from"] = "   "

        with self.assertRaises(EvaluatorError):
            evaluate_fixture([case], route_builder=lambda current: route)

    def test_expected_blocked_case_accepts_allowed_empty_graph_and_scores_ready_as_mismatch(self):

        case = {
            "id": "blocked",
            "category": "sequential",
            "task": "impossible dependency",
            "expected_intents": ["alpha", "beta"],
            "expected_scenarios": ["s1", "s2"],
            "required_dependency_edges": [],
            "forbidden_scenarios": [],
            "expected_status": "blocked",
        }
        blocked = evaluate_fixture(
            [case],
            route_builder=lambda current: {
                **synthetic_route(
                    current["expected_intents"],
                    current["expected_scenarios"],
                    graph_status="blocked",
                    acyclic=False,
                    routing_status="blocked",
                    reason_codes=["incomplete_composition"],
                ),
                "execution_graph": {
                    "status": "blocked",
                    "acyclic": False,
                    "nodes": [],
                    "edges": [],
                    "reason_codes": ["incomplete_composition"],
                },
            },
        )
        ready = evaluate_fixture(
            [case],
            route_builder=lambda current: synthetic_route(
                current["expected_intents"],
                current["expected_scenarios"],
                graph_status="ready",
                routing_status="complete",
            ),
        )

        self.assertTrue(blocked["cases"][0]["dag_valid"])
        self.assertTrue(ready["cases"][0]["dag_valid"])
        self.assertIn("status_mismatch", {issue["id"] for issue in ready["cases"][0]["issues"]})

    def test_blocked_source_cycle_is_invalid_even_with_empty_execution_graph(self):

        case = {
            "id": "blocked-cycle",
            "category": "sequential",
            "task": "cyclic dependency",
            "expected_intents": ["alpha", "beta"],
            "expected_scenarios": ["s1", "s2"],
            "required_dependency_edges": [],
            "forbidden_scenarios": [],
            "expected_status": "blocked",
        }
        route = synthetic_route(
            ["alpha", "beta"],
            ["s1", "s2"],
            graph_status="blocked",
            acyclic=False,
            routing_status="blocked",
            reason_codes=["dependency_cycle"],
            intent_dependencies=[["i2"], ["i1"]],
        )
        route["execution_graph"]["nodes"] = []
        route["execution_graph"]["edges"] = []

        report = evaluate_fixture([case], route_builder=lambda current: route)

        self.assertFalse(report["cases"][0]["dag_valid"])
        self.assertTrue(report["cases"][0]["topology_acyclic"])
        issue_ids = {issue["id"] for issue in report["cases"][0]["issues"]}
        self.assertIn("source_intent_graph_cycle", issue_ids)
        self.assertIn("invalid_incomplete_graph_reason", issue_ids)

    def test_incoherent_blocked_self_cycle_is_invalid_with_flag_issue(self):

        case = {
            "id": "blocked-cycle",
            "category": "sequential",
            "task": "cyclic dependency",
            "expected_intents": ["alpha"],
            "expected_scenarios": ["s1"],
            "required_dependency_edges": [],
            "forbidden_scenarios": [],
            "expected_status": "blocked",
        }
        route = synthetic_route(
            ["alpha", "beta"],
            ["s1", "s2"],
            graph_status="blocked",
            acyclic=True,
            routing_status="blocked",
            reason_codes=["dependency_cycle"],
            intent_dependencies=[["i2"], ["i1"]],
        )
        route["execution_graph"]["nodes"] = []
        route["execution_graph"]["edges"] = []

        report = evaluate_fixture([case], route_builder=lambda current: route)
        issue_ids = {issue["id"] for issue in report["cases"][0]["issues"]}

        self.assertFalse(report["cases"][0]["dag_valid"])
        self.assertIn("acyclic_flag_mismatch", issue_ids)

    def test_dependency_cycle_reason_with_acyclic_source_intents_is_invalid(self):

        case = {
            "id": "blocked-cycle",
            "category": "sequential",
            "task": "cyclic dependency",
            "expected_intents": ["alpha", "beta"],
            "expected_scenarios": ["s1", "s2"],
            "required_dependency_edges": [],
            "forbidden_scenarios": [],
            "expected_status": "blocked",
        }
        route = synthetic_route(
            ["alpha", "beta"],
            ["s1", "s2"],
            graph_status="blocked",
            acyclic=False,
            routing_status="blocked",
            reason_codes=["dependency_cycle"],
            intent_dependencies=[[], ["i1"]],
        )
        route["execution_graph"]["nodes"] = []
        route["execution_graph"]["edges"] = []

        report = evaluate_fixture([case], route_builder=lambda current: route)
        issue_ids = {issue["id"] for issue in report["cases"][0]["issues"]}

        self.assertFalse(report["cases"][0]["dag_valid"])
        self.assertIn("invalid_incomplete_graph_reason", issue_ids)

    def test_cyclic_source_with_noncycle_blocking_reason_is_invalid(self):

        case = {
            "id": "blocked-cycle",
            "category": "sequential",
            "task": "cyclic dependency",
            "expected_intents": ["alpha", "beta"],
            "expected_scenarios": ["s1", "s2"],
            "required_dependency_edges": [],
            "forbidden_scenarios": [],
            "expected_status": "blocked",
        }
        route = synthetic_route(
            ["alpha", "beta"],
            ["s1", "s2"],
            graph_status="blocked",
            acyclic=False,
            routing_status="blocked",
            reason_codes=["invalid_intent_graph"],
            intent_dependencies=[["i2"], ["i1"]],
        )
        route["execution_graph"]["nodes"] = []
        route["execution_graph"]["edges"] = []

        report = evaluate_fixture([case], route_builder=lambda current: route)
        issue_ids = {issue["id"] for issue in report["cases"][0]["issues"]}

        self.assertFalse(report["cases"][0]["dag_valid"])
        self.assertIn("source_intent_graph_cycle", issue_ids)
        self.assertIn("invalid_incomplete_graph_reason", issue_ids)

    def test_real_compiler_cyclic_intent_graph_is_invalid_blocked(self):
        from onecode_skill_sanitizer.compiler import compile_execution_graph
        from onecode_skill_sanitizer.composer import ScenarioComposition, ScenarioSelection
        from onecode_skill_sanitizer.intent import Intent, IntentGraph

        def intent(intent_id: str, depends_on: tuple[str, ...]) -> Intent:
            return Intent(
                id=intent_id,
                summary=intent_id,
                task_type=intent_id,
                required_artifacts=(),
                risk_flags=(),
                depends_on=depends_on,
                source="deterministic",
                confidence=1.0,
            )

        graph = IntentGraph(
            intents=(intent("i1", ("i2",)), intent("i2", ("i1",))),
            unresolved_dependencies=(),
        )
        composition = ScenarioComposition(
            selections=(
                ScenarioSelection("first", ("i1",), 1.0, 1),
                ScenarioSelection("second", ("i2",), 1.0, 1),
            ),
            uncovered_intents=(),
            status="complete",
        )
        compiled = compile_execution_graph(
            graph,
            composition,
            {"bundles": []},
            set(),
        )
        route = {
            "routing_status": "blocked",
            "intent_graph": {
                "intents": [
                    {
                        "id": intent.id,
                        "task_type": intent.task_type,
                        "depends_on": list(intent.depends_on),
                        "confidence": intent.confidence,
                    }
                    for intent in graph.intents
                ]
            },
            "selected_scenarios": [],
            "selected_skills": [],
            "capability_resolution": {"status": "complete", "capabilities": [], "missing_required_count": 0},
            "execution_graph": compiled,
        }
        case = {
            "id": "real-cycle",
            "category": "sequential",
            "task": "cycle",
            "expected_intents": ["i1", "i2"],
            "expected_scenarios": [],
            "required_dependency_edges": [],
            "forbidden_scenarios": [],
            "expected_status": "blocked",
        }

        report = evaluate_fixture([case], route_builder=lambda current: route)

        self.assertIn("dependency_cycle", compiled["reason_codes"])
        self.assertEqual(compiled["nodes"], [])
        self.assertEqual(compiled["edges"], [])
        self.assertFalse(report["cases"][0]["dag_valid"])
        issue_ids = {issue["id"] for issue in report["cases"][0]["issues"]}
        self.assertIn("source_intent_graph_cycle", issue_ids)
        self.assertIn("invalid_incomplete_graph_reason", issue_ids)

    def test_noncycle_blocked_boundary_rejects_disallowed_reason(self):

        case = {
            "id": "blocked-boundary",
            "category": "sequential",
            "task": "missing scenario",
            "expected_intents": ["alpha"],
            "expected_scenarios": ["s1"],
            "required_dependency_edges": [],
            "forbidden_scenarios": [],
            "expected_status": "blocked",
        }
        route = synthetic_route(
            ["alpha"],
            ["s1"],
            graph_status="blocked",
            acyclic=False,
            routing_status="blocked",
            reason_codes=["missing_scenario_bundle"],
        )
        route["execution_graph"]["nodes"] = []
        route["execution_graph"]["edges"] = []

        report = evaluate_fixture([case], route_builder=lambda current: route)

        self.assertFalse(report["cases"][0]["dag_valid"])
        self.assertTrue(report["cases"][0]["topology_acyclic"])
        issue_ids = {issue["id"] for issue in report["cases"][0]["issues"]}
        self.assertIn("invalid_incomplete_graph_reason", issue_ids)

    def test_noncycle_blocked_payload_with_emitted_graph_is_invalid(self):

        case = {
            "id": "blocked-boundary",
            "category": "sequential",
            "task": "missing scenario",
            "expected_intents": ["alpha"],
            "expected_scenarios": ["s1"],
            "required_dependency_edges": [],
            "forbidden_scenarios": [],
            "expected_status": "blocked",
        }
        route = synthetic_route(
            ["alpha"],
            ["s1"],
            graph_status="blocked",
            acyclic=False,
            routing_status="blocked",
            reason_codes=["missing_scenario_bundle"],
        )

        report = evaluate_fixture([case], route_builder=lambda current: route)
        issue_ids = {issue["id"] for issue in report["cases"][0]["issues"]}

        self.assertFalse(report["cases"][0]["dag_valid"])
        self.assertIn("blocked_graph_not_empty", issue_ids)

    def test_cycle_blocked_payload_with_emitted_graph_is_invalid(self):

        case = {
            "id": "blocked-cycle",
            "category": "sequential",
            "task": "cyclic dependency",
            "expected_intents": ["alpha", "beta"],
            "expected_scenarios": ["s1", "s2"],
            "required_dependency_edges": [],
            "forbidden_scenarios": [],
            "expected_status": "blocked",
        }
        route = synthetic_route(
            ["alpha", "beta"],
            ["s1", "s2"],
            graph_status="blocked",
            acyclic=False,
            routing_status="blocked",
            reason_codes=["dependency_cycle", "invalid_intent_graph"],
            intent_dependencies=[["i2"], ["i1"]],
        )

        report = evaluate_fixture([case], route_builder=lambda current: route)
        issue_ids = {issue["id"] for issue in report["cases"][0]["issues"]}

        self.assertFalse(report["cases"][0]["dag_valid"])
        self.assertIn("blocked_graph_not_empty", issue_ids)

    def test_real_compiler_missing_scenario_payload_is_invalid_blocked_boundary(self):
        from onecode_skill_sanitizer.compiler import compile_execution_graph
        from onecode_skill_sanitizer.composer import ScenarioComposition, ScenarioSelection
        from onecode_skill_sanitizer.intent import Intent, IntentGraph

        graph = IntentGraph(
            intents=(
                Intent(
                    id="i1",
                    summary="missing scenario",
                    task_type="alpha",
                    required_artifacts=(),
                    risk_flags=(),
                    depends_on=(),
                    source="deterministic",
                    confidence=1.0,
                ),
            ),
            unresolved_dependencies=(),
        )
        composition = ScenarioComposition(
            selections=(ScenarioSelection("missing", ("i1",), 1.0, 1),),
            uncovered_intents=(),
            status="complete",
        )
        compiled = compile_execution_graph(graph, composition, {"bundles": []}, set())
        route = {
            "routing_status": "blocked",
            "intent_graph": {
                "intents": [
                    {"id": "i1", "task_type": "alpha", "depends_on": [], "confidence": 1.0},
                ]
            },
            "selected_scenarios": [{"scenario_id": "missing", "intent_ids": ["i1"]}],
            "selected_skills": [],
            "capability_resolution": {"status": "complete", "capabilities": [], "missing_required_count": 0},
            "execution_graph": compiled,
        }
        case = {
            "id": "real-blocked-boundary",
            "category": "sequential",
            "task": "missing scenario",
            "expected_intents": ["alpha"],
            "expected_scenarios": ["missing"],
            "required_dependency_edges": [],
            "forbidden_scenarios": [],
            "expected_status": "blocked",
        }

        report = evaluate_fixture([case], route_builder=lambda current: route)

        self.assertEqual(compiled["reason_codes"], ["missing_scenario_bundle"])
        self.assertEqual(compiled["nodes"], [])
        self.assertEqual(compiled["edges"], [])
        self.assertFalse(report["cases"][0]["dag_valid"])
        issue_ids = {issue["id"] for issue in report["cases"][0]["issues"]}
        self.assertIn("invalid_incomplete_graph_reason", issue_ids)

    def test_real_compiler_missing_verification_diagnostic_graph_is_invalid_blocked(self):
        from onecode_skill_sanitizer.compiler import compile_execution_graph
        from onecode_skill_sanitizer.composer import ScenarioComposition, ScenarioSelection
        from onecode_skill_sanitizer.intent import Intent, IntentGraph

        def intent(intent_id: str, depends_on: tuple[str, ...] = ()) -> Intent:
            return Intent(
                id=intent_id,
                summary=intent_id,
                task_type=intent_id,
                required_artifacts=(),
                risk_flags=(),
                depends_on=depends_on,
                source="deterministic",
                confidence=1.0,
            )

        graph = IntentGraph(
            intents=(intent("i1"), intent("i2", ("i1",))),
            unresolved_dependencies=(),
        )
        composition = ScenarioComposition(
            selections=(
                ScenarioSelection("first", ("i1",), 1.0, 1),
                ScenarioSelection("second", ("i2",), 1.0, 1),
            ),
            uncovered_intents=(),
            status="complete",
        )
        bundles = {
            "bundles": [
                {
                    "id": "first",
                    "name": "first",
                    "scenario": "first",
                    "status": "trusted",
                    "task_signals": [],
                    "required_capabilities": [],
                    "execution_order": ["skill-a", "skill-b"],
                    "skills": ["skill-a", "skill-b"],
                    "expected_output": [],
                    "safety_boundary": "method only",
                },
                {
                    "id": "second",
                    "name": "second",
                    "scenario": "second",
                    "status": "trusted",
                    "task_signals": [],
                    "required_capabilities": [],
                    "execution_order": ["execution-publish-check"],
                    "skills": ["execution-publish-check"],
                    "expected_output": [],
                    "safety_boundary": "method only",
                },
            ]
        }
        compiled = compile_execution_graph(
            graph,
            composition,
            bundles,
            {"skill-a", "skill-b", "execution-publish-check"},
        )
        route = {
            "routing_status": "blocked",
            "intent_graph": {
                "intents": [
                    {
                        "id": intent.id,
                        "task_type": intent.task_type,
                        "depends_on": list(intent.depends_on),
                        "confidence": intent.confidence,
                    }
                    for intent in graph.intents
                ]
            },
            "selected_scenarios": [
                {"scenario_id": "first", "intent_ids": ["i1"]},
                {"scenario_id": "second", "intent_ids": ["i2"]},
            ],
            "selected_skills": [],
            "capability_resolution": {"status": "complete", "capabilities": [], "missing_required_count": 0},
            "execution_graph": compiled,
        }
        case = {
            "id": "missing-verification",
            "category": "sequential",
            "task": "missing verification",
            "expected_intents": ["i1", "i2"],
            "expected_scenarios": ["first", "second"],
            "required_dependency_edges": [],
            "forbidden_scenarios": [],
            "expected_status": "blocked",
        }

        report = evaluate_fixture([case], route_builder=lambda current: route)

        self.assertEqual(compiled["reason_codes"], ["missing_intent_verification"])
        self.assertTrue(compiled["nodes"])
        self.assertTrue(compiled["edges"])
        self.assertEqual({edge["type"] for edge in compiled["edges"]}, {"scenario_order"})
        self.assertFalse(report["cases"][0]["dag_valid"])
        issue_ids = {issue["id"] for issue in report["cases"][0]["issues"]}
        self.assertIn("invalid_incomplete_graph_reason", issue_ids)
        self.assertIn("blocked_graph_not_empty", issue_ids)

    def test_missing_verification_rejects_dependent_intent_edges(self):

        case = {
            "id": "missing-verification",
            "category": "sequential",
            "task": "missing verification",
            "expected_intents": ["alpha", "beta"],
            "expected_scenarios": ["s1", "s2"],
            "required_dependency_edges": [],
            "forbidden_scenarios": [],
            "expected_status": "blocked",
        }
        route = synthetic_route(
            ["alpha", "beta"],
            ["s1", "s2"],
            dependency_pairs=[("alpha", "beta")],
            graph_status="blocked",
            acyclic=False,
            routing_status="blocked",
            reason_codes=["missing_intent_verification"],
            intent_dependencies=[[], ["i1"]],
        )

        report = evaluate_fixture([case], route_builder=lambda current: route)
        issue_ids = {issue["id"] for issue in report["cases"][0]["issues"]}

        self.assertFalse(report["cases"][0]["dag_valid"])
        self.assertIn("invalid_incomplete_graph_reason", issue_ids)
        self.assertIn("blocked_graph_not_empty", issue_ids)

    def test_ready_graph_requires_true_flag_and_acyclic_topology(self):
        from onecode_skill_sanitizer.router_eval_v2 import EvaluatorError

        case = {
            "id": "ready",
            "category": "compound",
            "task": "ready",
            "expected_intents": ["alpha"],
            "expected_scenarios": ["s1"],
            "required_dependency_edges": [],
            "forbidden_scenarios": [],
            "expected_status": "complete",
        }
        coherent = synthetic_route(["alpha"], ["s1"])
        contradictory = synthetic_route(["alpha"], ["s1"], acyclic=False)

        report = evaluate_fixture([case], route_builder=lambda current: coherent)
        self.assertTrue(report["cases"][0]["dag_valid"])
        with self.assertRaises(EvaluatorError):
            evaluate_fixture([case], route_builder=lambda current: contradictory)

    def test_blocked_graph_requires_blocked_route_and_recognized_reason(self):

        case = {
            "id": "blocked",
            "category": "sequential",
            "task": "blocked",
            "expected_intents": ["alpha"],
            "expected_scenarios": ["s1"],
            "required_dependency_edges": [],
            "forbidden_scenarios": [],
            "expected_status": "blocked",
        }
        routes = [
            synthetic_route(
                ["alpha"],
                ["s1"],
                graph_status="blocked",
                routing_status="complete",
                reason_codes=["missing_intent_verification"],
            ),
            synthetic_route(
                ["alpha"],
                ["s1"],
                graph_status="blocked",
                routing_status="blocked",
                reason_codes=[],
            ),
            synthetic_route(
                ["alpha"],
                ["s1"],
                graph_status="blocked",
                routing_status="blocked",
                reason_codes=["invented_reason"],
            ),
        ]

        for route in routes:
            with self.subTest(route=route):
                report = evaluate_fixture([case], route_builder=lambda current: route)
                self.assertFalse(report["cases"][0]["dag_valid"])

    def test_real_command_prints_json_without_failing_on_low_metrics(self):
        completed = subprocess.run(
            [
                sys.executable,
                "-m",
                "onecode_skill_sanitizer",
                "router-eval-v2",
                "--eval",
                str(EVAL_PATH),
                "--registry",
                str(ROOT / "catalog"),
                "--bundles",
                str(ROOT / "bundles" / "index.json"),
            ],
            cwd=ROOT,
            env={"PYTHONPATH": str(ROOT / "src")},
            capture_output=True,
            text=True,
            check=False,
        )

        self.assertEqual(completed.returncode, 0, completed.stderr)
        report = json.loads(completed.stdout)
        self.assertEqual(report["case_count"], 100)
        self.assertFalse(report["quality_gate"]["production_ready"])
        self.assertEqual(
            report["quality_gate"]["failed_gates"],
            ["forbidden_scenario_false_positive_rate", "high_confidence_error_rate"],
        )
        self.assertEqual(
            report["quality_gate"]["missing_gates"],
            ["forbidden_skill_false_positive_rate", "independent_label_review"],
        )
        self.assertEqual(
            report["quality_gate"]["dataset_identity"],
            {
                "case_count": 100,
                "dataset_sha256": report["quality_gate"]["dataset_identity"]["dataset_sha256"],
                "labeling_generated_from_router": False,
                "labeling_method": "manual_review",
                "labeling_reviewed_at": "2026-07-10",
                "labeling_reviewer_role": "independent_dataset_review",
                "suite_id": None,
                "suite_sha256": None,
            },
        )
        self.assertRegex(
            report["quality_gate"]["dataset_identity"]["dataset_sha256"],
            r"^sha256:[0-9a-f]{64}$",
        )
        self.assertIsNone(report["quality_gate"]["review_identity"])
        self.assertEqual(report["metrics"]["dag_validity"], 1.0)
        self.assertGreaterEqual(report["metrics"]["dependency_edge_recall"], 0.90)
        self.assertEqual(
            set(report["metrics"]),
            {
                "multi_intent_exact_match",
                "scenario_precision",
                "scenario_recall",
                "scenario_f1",
                "forbidden_scenario_false_positive_rate",
                "dependency_edge_recall",
                "dag_validity",
                "task_type_macro_precision",
                "task_type_macro_recall",
                "task_type_macro_f1",
                "required_capability_recall",
                "forbidden_skill_false_positive_rate",
                "dependency_edge_precision",
                "high_confidence_error_rate",
                "core_bundle_contract_coverage",
            },
        )
        task_type_support = report["counts"]["task_type_by_label"]
        self.assertEqual(
            [item["task_type"] for item in task_type_support],
            sorted(item["task_type"] for item in task_type_support),
        )
        for item in task_type_support:
            for field in ("true_positive", "false_positive", "false_negative"):
                self.assertIs(type(item[field]), int)
                self.assertGreaterEqual(item[field], 0)
        per_label = []
        for item in task_type_support:
            true_positive = item["true_positive"]
            precision_denominator = true_positive + item["false_positive"]
            recall_denominator = true_positive + item["false_negative"]
            precision = true_positive / precision_denominator if precision_denominator else 0.0
            recall = true_positive / recall_denominator if recall_denominator else 0.0
            f1 = 0.0 if precision + recall == 0 else 2 * precision * recall / (precision + recall)
            per_label.append((precision, recall, f1))
        self.assertTrue(per_label)
        self.assertAlmostEqual(
            report["metrics"]["task_type_macro_precision"],
            sum(item[0] for item in per_label) / len(per_label),
        )
        self.assertAlmostEqual(
            report["metrics"]["task_type_macro_recall"],
            sum(item[1] for item in per_label) / len(per_label),
        )
        self.assertAlmostEqual(
            report["metrics"]["task_type_macro_f1"],
            sum(item[2] for item in per_label) / len(per_label),
        )

    def test_real_command_requires_production_ready_only_when_requested(self):
        base_command = [
            sys.executable,
            "-m",
            "onecode_skill_sanitizer",
            "router-eval-v2",
            "--eval",
            str(EVAL_PATH),
            "--registry",
            str(ROOT / "catalog"),
            "--bundles",
            str(ROOT / "bundles" / "index.json"),
        ]
        normal = subprocess.run(
            base_command,
            cwd=ROOT,
            env={"PYTHONPATH": str(ROOT / "src")},
            capture_output=True,
            text=True,
            check=False,
        )
        completed = subprocess.run(
            [*base_command, "--require-production-ready"],
            cwd=ROOT,
            env={"PYTHONPATH": str(ROOT / "src")},
            capture_output=True,
            text=True,
            check=False,
        )

        self.assertEqual(normal.returncode, 0, normal.stderr)
        self.assertEqual(completed.returncode, 2, completed.stderr)
        self.assertEqual(completed.stdout, normal.stdout)
        report = json.loads(completed.stdout)
        self.assertFalse(report["quality_gate"]["production_ready"])
        self.assertEqual(
            report["quality_gate"]["failed_gates"],
            ["forbidden_scenario_false_positive_rate", "high_confidence_error_rate"],
        )
        self.assertEqual(
            report["quality_gate"]["missing_gates"],
            ["forbidden_skill_false_positive_rate", "independent_label_review"],
        )

    def test_bundle_capability_context_is_deterministic_and_required_only(self):
        from onecode_skill_sanitizer.commands import _bundle_required_capability_context

        bundles = {
            "bundles": [
                {
                    "id": "zeta",
                    "required_capabilities": [
                        {"id": "optional", "required": False, "preferred_skills": ["x"]},
                        {"id": "required-b", "required": True, "preferred_skills": ["x"]},
                    ],
                },
                {
                    "id": "alpha",
                    "required_capabilities": [
                        {"id": "required-a", "required": True, "preferred_skills": ["x"]},
                    ],
                },
            ]
        }

        self.assertEqual(
            _bundle_required_capability_context(bundles),
            {"alpha": ("required-a",), "zeta": ("required-b",)},
        )

    def test_bundle_capability_context_rejects_malformed_or_duplicate_required_capabilities(self):
        from onecode_skill_sanitizer.commands import _bundle_required_capability_context

        malformed = [
            {"bundles": [{"id": "s", "required_capabilities": "bad"}]},
            {"bundles": [{"id": "s", "required_capabilities": [{"id": "c", "required": 1}]}]},
            {
                "bundles": [
                    {
                        "id": "s",
                        "required_capabilities": [
                            {"id": "c", "required": True},
                            {"id": "c", "required": True},
                        ],
                    }
                ]
            },
        ]
        for bundles in malformed:
            with self.subTest(bundles=bundles), self.assertRaises(ValueError):
                _bundle_required_capability_context(bundles)

    def test_command_returns_two_for_schema_errors(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "bad.json"
            path.write_text('{"cases": []}', encoding="utf-8")
            completed = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "onecode_skill_sanitizer",
                    "router-eval-v2",
                    "--eval",
                    str(path),
                    "--registry",
                    str(ROOT / "catalog"),
                    "--bundles",
                    str(ROOT / "bundles" / "index.json"),
                ],
                cwd=ROOT,
                env={"PYTHONPATH": str(ROOT / "src")},
                capture_output=True,
                text=True,
                check=False,
            )

        self.assertEqual(completed.returncode, 2)
        json.loads(completed.stdout)

    def test_command_returns_two_for_missing_bundle_catalog(self):
        completed = subprocess.run(
            [
                sys.executable,
                "-m",
                "onecode_skill_sanitizer",
                "router-eval-v2",
                "--eval",
                str(EVAL_PATH),
                "--registry",
                str(ROOT / "catalog"),
                "--bundles",
                str(ROOT / "bundles" / "missing.json"),
            ],
            cwd=ROOT,
            env={"PYTHONPATH": str(ROOT / "src")},
            capture_output=True,
            text=True,
            check=False,
        )

        self.assertEqual(completed.returncode, 2)
        json.loads(completed.stdout)

    def test_command_uses_catalog_and_bundle_defaults(self):
        completed = subprocess.run(
            [
                sys.executable,
                "-m",
                "onecode_skill_sanitizer",
                "router-eval-v2",
                "--eval",
                str(EVAL_PATH),
            ],
            cwd=ROOT,
            env={"PYTHONPATH": str(ROOT / "src")},
            capture_output=True,
            text=True,
            check=False,
        )

        self.assertNotEqual(completed.returncode, 2, completed.stdout + completed.stderr)

    def test_evaluator_has_no_label_generation_helper(self):
        import onecode_skill_sanitizer.router_eval_v2 as evaluator

        prohibited = {
            "generate_labels",
            "generate_expected_labels",
            "label_cases_from_router",
        }
        self.assertTrue(prohibited.isdisjoint(dir(evaluator)))


if __name__ == "__main__":
    unittest.main()
