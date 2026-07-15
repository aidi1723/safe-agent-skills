from __future__ import annotations

import re
from typing import Any

from .intent import NormalizedTask
from .skill_candidates import HIGH_FREQUENCY_SKILL_NAMES


CAPABILITY_SKILL = {
    "code.explore": "codebase-explore-map",
    "code.review": "code-review-risk",
    "code.test": "code-test-regression",
    "execution.browser_check": "execution-browser-check",
    "research.source": "research-source-check",
    "design.ui_review": "design-ui-review",
    "security.supply_chain": "security-supply-chain-review",
}
CAPABILITY_PATTERNS = {
    "code.explore": re.compile(r"unfamiliar repo|map (?:the )?repo|repository map|repository orientation|source ownership|data flow|entry points?|where does|architecture|陌生代码库|梳理.*(?:代码库|repo|入口|模块)|(?:代码库|repo).*(?:映射|梳理)|调用链", re.I),
    "code.review": re.compile(r"review (?:this |the )?(?:diff|patch|pr|code)|code review|pr.*review|risk[- ]review|code delta|find (?:bugs|defects)|check this change.*(?:concurrency|cleanup|regression)|审查.*(?:diff|PR|补丁|代码)|评审.*(?:缺陷|代码|补丁|变更)|代码变更.*(?:问题|风险)|回归风险", re.I),
    "code.test": re.compile(r"regression test|regression coverage|test coverage|failing test|test boundary|contract test|old behavior.*fail|red[- ]green|回归测试|补.*测试|失败用例", re.I),
    "execution.browser_check": re.compile(r"real browser|browser (?:check|flow|test)|playwright|screenshot|DOM state|canvas|console error|浏览器.*(?:验证|检查|跑|截图|复现)|打开.*页面", re.I),
    "research.source": re.compile(r"primary sources?|official (?:sources?|documentation|records?)|citations?|fact[- ]check|verify (?:the |these )?claims?|research (?:the )?(?:claims|sources|package|community skill)|standards?.*evidence|web research|全网搜索|一手资料|官方资料|权威来源|查证|核实|引用|事实核查", re.I),
    "design.ui_review": re.compile(r"polish (?:the )?(?:UI|dashboard)|review (?:the )?(?:UI|dashboard|layout)|visual hierarchy|spacing|responsive layout|accessibility|优化.*(?:UI|页面|界面)|视觉一致|响应式布局|可访问性", re.I),
    "security.supply_chain": re.compile(r"supply[- ]chain|package (?:provenance|trust|before adoption)|install scripts?|plugin maintainer|community skill|dependency (?:risk|provenance|trust)|connector.*permissions?|供应链|包.*(?:来源|信任)|社区 Skill|插件.*风险|connector.*权限|许可证.*权限", re.I),
}
EXPLANATION_RE = re.compile(r"\b(?:explain|what is|describe)\b|解释|是什么|介绍", re.I)
INVENTORY_RE = re.compile(r"\b(?:list|show)\b.*\bskills?\b|列出.*Skill|有哪些.*Skill", re.I)
NEGATION_PREFIX = r"(?:do not|don't|never|no need to|不要|别|不需要|无需|先不)"
GENERIC_SKILL_EXCLUSION_RE = re.compile(
    rf"{NEGATION_PREFIX}\s+(?:use|invoke|使用|调用)?\s*(?:any|all|任何|所有)?\s*skills?",
    re.I,
)
MISSING_INPUT_PATTERNS = {
    "target_page_or_flow": re.compile(
        r"(?:target|page|url|flow).*(?:missing|unknown)|没有.*(?:页面|URL|地址|流程)|"
        r"(?:页面|URL|地址|流程).*(?:缺失|不知道)",
        re.I,
    ),
    "behavior_or_change_under_test": re.compile(
        r"behavior under test.*(?:missing|unknown)|(?:behavior|change).*(?:not known|unspecified)|"
        r"待测.*(?:行为|变更).*(?:缺失|不明)",
        re.I,
    ),
}
MANDATORY_TEST_RE = re.compile(
    r"\b(?:fix|implement|change)\b.*\b(?:bug|shared contract|parser)\b|"
    r"修复.*(?:bug|共享契约|解析器)",
    re.I,
)
NON_ACTION_BROWSER_RE = re.compile(r"screenshot (?:is )?attached|截图(?:已)?附", re.I)
AMBIGUOUS_SPECIALIZED_RE = re.compile(
    r"(?:check|review|看看|检查)(?: the| this)? ui[\s.!?。！？]*|"
    r"(?:check|review) (?:this |the )?(?:change|package)[\s.!?]*|"
    r"看一下这个变更|检查这个包",
    re.I,
)


def decide_skill_need(normalized: NormalizedTask) -> dict[str, Any]:
    current = normalized.current.strip()
    folded = current.casefold()
    explicit = [name for name in HIGH_FREQUENCY_SKILL_NAMES if name.casefold() in folded]
    exact_excluded = [
        name for name in HIGH_FREQUENCY_SKILL_NAMES
        if re.search(rf"{NEGATION_PREFIX}[^.;\n。；]{{0,24}}{re.escape(name)}", current, re.I)
    ]
    if GENERIC_SKILL_EXCLUSION_RE.search(current):
        excluded = list(HIGH_FREQUENCY_SKILL_NAMES)
    else:
        excluded = list(exact_excluded)
        for capability, skill in CAPABILITY_SKILL.items():
            if _capability_negated(current, capability) and skill not in excluded:
                excluded.append(skill)
    matched_capabilities: list[tuple[int, int, str]] = []
    for index, (capability, pattern) in enumerate(CAPABILITY_PATTERNS.items()):
        match = pattern.search(current)
        if (
            match
            and not _capability_negated(current, capability)
            and CAPABILITY_SKILL[capability] not in excluded
        ):
            matched_capabilities.append((match.start(), index, capability))
    matched_capabilities.sort(key=lambda item: (item[0], item[1]))
    capabilities = [item[2] for item in matched_capabilities]
    if NON_ACTION_BROWSER_RE.search(current) and "execution.browser_check" in capabilities:
        capabilities.remove("execution.browser_check")
    mandatory_capabilities = ["code.test"] if MANDATORY_TEST_RE.search(current) else []
    for capability in mandatory_capabilities:
        if capability not in capabilities:
            capabilities.append(capability)
    reason_codes: list[str] = []
    explanation_only = bool(EXPLANATION_RE.search(current) and explicit and not capabilities)
    inventory_only = bool(INVENTORY_RE.search(current) and not capabilities)
    if not current or current.casefold() in {"hi", "hello", "thanks", "thank you", "你好", "谢谢"}:
        reason_codes.append("no_specialized_need")
    elif inventory_only:
        reason_codes.append("inventory_only")
    elif explanation_only:
        reason_codes.append("explanation_only")
    elif not capabilities and set(excluded) == set(HIGH_FREQUENCY_SKILL_NAMES):
        reason_codes.append("all_candidates_excluded")
    elif explicit and set(explicit).issubset(excluded):
        return _decision(
            "clarify", [], explicit, excluded, ["conflicting_explicit_constraint"],
            False, False, [], [], [],
        )
    elif not capabilities and AMBIGUOUS_SPECIALIZED_RE.search(current):
        return _decision(
            "clarify", [], explicit, excluded, ["adjacent_capability_ambiguous"],
            False, False, [], [], [],
        )
    elif not capabilities and not explicit:
        reason_codes.append("no_specialized_need")
    if reason_codes:
        return _decision(
            "none", [], explicit, excluded, reason_codes,
            explanation_only, inventory_only, [], [], [],
        )
    for name in explicit:
        capability = next((key for key, value in CAPABILITY_SKILL.items() if value == name), "")
        if capability and name not in excluded and capability not in capabilities:
            capabilities.append(capability)
    missing_inputs = [
        field for field, pattern in MISSING_INPUT_PATTERNS.items() if pattern.search(current)
    ]
    decision = "single" if len(capabilities) == 1 else "composite"
    return _decision(
        decision, capabilities, explicit, excluded, ["specialized_need_detected"],
        False, False, missing_inputs, mandatory_capabilities, [],
    )


def _capability_negated(text: str, capability: str) -> bool:
    skill = CAPABILITY_SKILL[capability]
    aliases = {
        "code.explore": r"map|explore|梳理|映射",
        "code.review": r"review|audit|审查|评审",
        "code.test": r"test|测试",
        "execution.browser_check": r"browser|playwright|浏览器",
        "research.source": r"research|citations?|claims?|facts?|搜索|引用|查证|核实|主张|事实",
        "design.ui_review": r"design|ui review|设计|视觉评审",
        "security.supply_chain": r"supply[- ]chain|provenance|package scripts?|install scripts?|供应链|来源审计|包脚本",
    }[capability]
    return bool(re.search(rf"{NEGATION_PREFIX}[^.;\n。；]{{0,18}}(?:{aliases}|{re.escape(skill)})", text, re.I))


def _decision(
    decision: str,
    capabilities: list[str],
    explicit: list[str],
    excluded: list[str],
    reasons: list[str],
    explanation_only: bool,
    inventory_only: bool,
    missing_inputs: list[str],
    mandatory_capabilities: list[str],
    policy_block_reasons: list[str],
) -> dict[str, Any]:
    return {
        "decision": decision,
        "specialized_need": decision != "none",
        "required_capabilities": capabilities,
        "explicit_skills": explicit,
        "excluded_skills": excluded,
        "explanation_only": explanation_only,
        "inventory_only": inventory_only,
        "missing_inputs": missing_inputs,
        "mandatory_capabilities": mandatory_capabilities,
        "policy_block_reasons": policy_block_reasons,
        "reason_codes": reasons,
    }
