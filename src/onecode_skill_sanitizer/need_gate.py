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
    "code.explore": re.compile(
        r"unfamiliar (?:repo|repository|monorepo|codebase)|"
        r"map (?:the )?(?:repo|repository|monorepo|codebase)|"
        r"map (?:the |its |this )?local (?:integration|wiring|callers?)|"
        r"(?:repo|repository|monorepo|codebase) map|"
        r"repository orientation|source ownership|data flow|entry points?|"
        r"where does|where is .*(?:implemented|defined|owned|handled)|"
        r"architecture|陌生代码库|"
        r"梳理.*(?:代码库|仓库|repo|入口|模块)|"
        r"(?:代码库|仓库|repo).*(?:映射|梳理)|调用链",
        re.I,
    ),
    "code.review": re.compile(
        r"review (?:this |the )?(?:diff|patch|pr|code)\b|"
        r"(?:review|inspect) (?:only )?(?:this |the )?"
        r"(?:(?!not\b)[A-Za-z0-9_-]+\s+){0,4}(?:diff|patch|pr)\b|"
        r"code review|\bpr\b.*review|risk[- ]review|code delta|find (?:bugs|defects)|"
        r"check this change.*(?:concurrency|cleanup|regression)|"
        r"审查.*(?:diff|PR|补丁|代码)|评审.*(?:缺陷|代码|补丁|变更)|"
        r"代码变更.*(?:问题|风险)|回归风险",
        re.I,
    ),
    "code.test": re.compile(r"regression test|regression coverage|test coverage|failing test|test boundary|contract test|old behavior.*fail|red[- ]green|回归测试|补.*测试|失败用例", re.I),
    "execution.browser_check": re.compile(
        r"real browser|"
        r"(?:run|check|verify|test|exercise) (?:the )?(?:existing )?UI flow"
        r"(?!\s+(?:(?:unit|integration|regression|contract|end-to-end|e2e)\s+)?tests?\b)"
        r"(?![^.;\n]*\bwithout\b[^.;\n]*\bbrowser\b)"
        r"(?: (?:in )?(?:a )?(?:real )?browser)?|"
        r"(?:smoke[- ]test|check|verify).*browser[- ]visible|"
        r"browser[- ](?:check|flow|test)|playwright|screenshot|DOM state|canvas|"
        r"console error|浏览器.*(?:验证|检查|跑|截图|复现)|打开.*页面",
        re.I,
    ),
    "research.source": re.compile(
        r"primary sources?|official (?:sources?|documentation|records?)|citations?|"
        r"(?:current|up[- ]to[- ]date|latest|fresh).{0,80}(?:cite|citation)\b|"
        r"fact[- ]check|verify (?:the |these )?.{0,30}?\bclaims?|"
        r"research (?:the )?(?:claims|sources|package|community skill)|"
        r"standards?.*evidence|web research|全网搜索|一手资料|官方资料|"
        r"权威来源|查证|核实|引用|事实核查",
        re.I,
    ),
    "design.ui_review": re.compile(
        r"polish (?:the )?(?:UI|dashboard)|"
        r"review (?:the )?(?:UI|dashboard|layout)|(?:UI|layout|interface) critique|"
        r"critique (?:the )?(?:UI|layout|interface)|"
        r"(?:review|critique)"
        r"(?=[^.;\n]{0,80}\b(?:UI|dashboard|interface|design)\b)"
        r"[^.;\n]{0,80}\b(?:density|surfaces?|empty states?|colors?|layout|hierarchy)\b|"
        r"visual hierarchy|spacing|responsive layout|accessibility|"
        r"优化.*(?:UI|页面|界面)|"
        r"评审.*(?:UI|页面|界面|配色|布局|视觉|密度|空状态)|"
        r"视觉一致|响应式布局|可访问性",
        re.I,
    ),
    "security.supply_chain": re.compile(
        r"supply[- ]chain|package (?:provenance|trust|before adoption)|"
        r"(?:npm|package|dependency|library|plugin)\s+audit.*(?:source|license|provenance|release)|"
        r"install scripts?|plugin maintainer|community skill|"
        r"dependency (?:risk|provenance|trust)|connector.*permissions?|"
        r"供应链|包.*(?:来源|信任)|社区 Skill|插件.*风险|connector.*权限|"
        r"许可证.*权限",
        re.I,
    ),
}
EXPLANATION_RE = re.compile(r"\b(?:explain|what is|describe)\b|解释|是什么|什么是|介绍", re.I)
INVENTORY_RE = re.compile(r"\b(?:list|show)\b.*\bskills?\b|列出.*Skill|有哪些.*Skill", re.I)
NEGATION_PREFIX = r"(?:do not|don't|never|no need to|不要|别|不需要|无需|先不)"
GENERIC_SKILL_EXCLUSION_RE = re.compile(
    rf"{NEGATION_PREFIX}\s*(?:(?:use|invoke|使用|调用)\s*)?"
    rf"(?:(?:any|all|任何|所有)\s*)?(?:skills?\b|技能)",
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
NON_ACTION_CODE_REVIEW_RE = re.compile(
    r"code review (?:findings|report|results) (?:are|is) "
    r"(?:ready|complete|attached|available)",
    re.I,
)
AMBIGUOUS_SPECIALIZED_RE = re.compile(
    r"(?:check|review|看看|检查)(?: the| this)? ui[\s.!?。！？]*|"
    r"(?:check|review) (?:this |the )?(?:change|package)[\s.!?]*|"
    r"看一下这个变更|检查这个包",
    re.I,
)
CLAUSE_BOUNDARY_RE = re.compile(r"[.;\n。；！？!?]+|(?:,\s*)?\bthen\b", re.I)
HISTORICAL_CONTEXT_RE = re.compile(
    r"\b(?:earlier|previously)\s+we\s+(?:planned|discussed)\b", re.I
)
REFERENCE_REPORT_RE = re.compile(
    r"\b(?:the\s+)?(?:documentation|docs?|history|inventory)\s+"
    r"(?:mentions?|lists?|records?|shows?)\b",
    re.I,
)
SKILL_DIRECTIVE_RE = re.compile(
    rf"(?P<negative>{NEGATION_PREFIX}\s*(?:(?:use|invoke|使用|调用)\s*)?)|"
    r"(?P<bare_negative>(?:\bbut\s+)?\bnot\s+(?!only\b)(?:use\s+)?)|"
    r"(?P<positive>\b(?:use|invoke)\b|使用|调用)",
    re.I,
)
CAPABILITY_NEGATION_PATTERNS = {
    "code.explore": re.compile(
        rf"{NEGATION_PREFIX}\s*(?:map|explore|梳理|映射)", re.I
    ),
    "code.review": re.compile(
        rf"{NEGATION_PREFIX}\s*(?:(?:perform|do)\s+)?(?:a\s+)?(?:general\s+)?"
        r"(?:code review|review\s+(?:this\s+|the\s+)?(?:patch|diff|pr|code|change))\b|"
        r"\b(?:not|no)\s+(?:a\s+)?(?:general\s+)?code review\b",
        re.I,
    ),
    "code.test": re.compile(
        rf"{NEGATION_PREFIX}\s*(?:(?:create|add|run|write|perform|创建|添加|运行|编写)\s*)?"
        r"(?:(?:regression coverage|regression tests?|tests?|testing)(?![A-Za-z0-9_])|"
        r"回归覆盖|回归测试|测试)",
        re.I,
    ),
    "execution.browser_check": re.compile(
        rf"{NEGATION_PREFIX}\s*(?:"
        r"(?:smoke[- ]test|check|verify).*browser[- ]visible|"
        r"(?:run|check|verify|test|exercise)\s+(?:the\s+)?(?:existing\s+)?"
        r"UI flow(?:\s+(?:in\s+)?(?:a\s+)?(?:real\s+)?browser)?|"
        r"(?:(?:open|run|use|check|verify|打开|使用|运行|检查|验证)\s*)?"
        r"(?:(?:a\s+|the\s+)?(?:real\s+)?(?:browser|playwright)(?![A-Za-z0-9_])|"
        r"浏览器))",
        re.I,
    ),
    "research.source": re.compile(
        rf"{NEGATION_PREFIX}\s*(?:research|cite|verify|fact[- ]check|搜索|引用|查证|核实)",
        re.I,
    ),
    "design.ui_review": re.compile(
        rf"{NEGATION_PREFIX}\s*(?:(?:review|polish|check|critique|审查|评审|检查|优化)\s*)?"
        r"(?:(?:the\s+)?(?:ui|dashboard|layout|design|interface)(?![A-Za-z0-9_])|"
        r"页面|界面|设计|视觉)",
        re.I,
    ),
    "security.supply_chain": re.compile(
        rf"{NEGATION_PREFIX}\s*(?:supply[- ]chain|provenance|install scripts?|package trust|"
        r"供应链|来源审计|包信任)",
        re.I,
    ),
}


def _canonical_skill_pattern(name: str) -> re.Pattern[str]:
    separator = r"(?:-|\s+)"
    body = separator.join(re.escape(part) for part in name.split("-"))
    return re.compile(rf"(?<![A-Za-z0-9_-]){body}(?![A-Za-z0-9_-])", re.I)


SKILL_NAME_PATTERNS = {
    name: _canonical_skill_pattern(name) for name in HIGH_FREQUENCY_SKILL_NAMES
}


def decide_skill_need(normalized: NormalizedTask) -> dict[str, Any]:
    current = normalized.current.strip()
    clauses = _request_clauses(current)
    capability_indexes = {
        capability: index for index, capability in enumerate(CAPABILITY_SKILL)
    }
    evidence: dict[str, tuple[int, int]] = {}
    positive_occurrences = _positive_explicit_skill_occurrences(current)
    positive_skills = {name for name, _, _ in positive_occurrences}
    excluded_skills: set[str] = set()
    derived_mandatory: set[str] = set()
    explanation_seen = False
    inventory_seen = False

    for name, start, _ in positive_occurrences:
        capability = _capability_for_skill(name)
        _record_evidence(
            evidence,
            capability,
            start,
            capability_indexes[capability],
        )

    for clause, offset in clauses:
        explanation_match = EXPLANATION_RE.search(clause)
        inventory_match = INVENTORY_RE.search(clause)
        explanation_seen = explanation_seen or bool(explanation_match)
        inventory_seen = inventory_seen or bool(inventory_match)
        information_position = _information_position(clause)

        if GENERIC_SKILL_EXCLUSION_RE.search(clause):
            excluded_skills.update(HIGH_FREQUENCY_SKILL_NAMES)

        for name, pattern in SKILL_NAME_PATTERNS.items():
            for match in pattern.finditer(clause):
                directive, _ = _skill_directive_before(clause, match.start())
                if directive == "negative":
                    excluded_skills.add(name)

        masked_clause = _mask_canonical_skill_names(clause)
        negated_capabilities = {
            capability
            for capability, pattern in CAPABILITY_NEGATION_PATTERNS.items()
            if pattern.search(masked_clause)
        }
        excluded_skills.update(
            CAPABILITY_SKILL[capability] for capability in negated_capabilities
        )

        for capability, pattern in CAPABILITY_PATTERNS.items():
            if capability in negated_capabilities:
                continue
            for match in pattern.finditer(masked_clause):
                if not _before_information(match.start(), information_position):
                    continue
                if (
                    capability == "execution.browser_check"
                    and _is_non_action_browser_match(masked_clause, match)
                ):
                    continue
                if (
                    capability == "code.review"
                    and _is_non_action_code_review_match(masked_clause, match)
                ):
                    continue
                _record_evidence(
                    evidence,
                    capability,
                    offset + match.start(),
                    capability_indexes[capability],
                )

        for match in MANDATORY_TEST_RE.finditer(masked_clause):
            if not _before_information(match.start(), information_position):
                continue
            if _match_has_negation_prefix(masked_clause, match.start()):
                continue
            derived_mandatory.add("code.test")
            _record_evidence(
                evidence,
                "code.test",
                offset + match.start(),
                capability_indexes["code.test"],
            )

    explicit = [
        name for name in HIGH_FREQUENCY_SKILL_NAMES if name in positive_skills
    ]
    excluded = [
        name for name in HIGH_FREQUENCY_SKILL_NAMES if name in excluded_skills
    ]
    conflicting_capabilities = [
        capability
        for capability in evidence
        if CAPABILITY_SKILL[capability] in excluded_skills
    ]
    if conflicting_capabilities:
        return _decision(
            "clarify", [], explicit, excluded, ["conflicting_explicit_constraint"],
            False, False, [], [], [],
        )

    capabilities = sorted(evidence, key=evidence.__getitem__)
    mandatory_capabilities = [
        capability
        for capability in CAPABILITY_SKILL
        if capability in derived_mandatory
        and CAPABILITY_SKILL[capability] not in excluded_skills
    ]
    has_positive_action = bool(evidence)
    inventory_only = bool(inventory_seen and not has_positive_action)
    explanation_only = bool(
        explanation_seen and not has_positive_action and not inventory_only
    )
    if not current or current.casefold() in {"hi", "hello", "thanks", "thank you", "你好", "谢谢"}:
        reason_codes = ["no_specialized_need"]
    elif inventory_only:
        reason_codes = ["inventory_only"]
    elif explanation_only:
        reason_codes = ["explanation_only"]
    elif not has_positive_action and set(excluded) == set(HIGH_FREQUENCY_SKILL_NAMES):
        reason_codes = ["all_candidates_excluded"]
    elif not has_positive_action and _has_ambiguous_specialized_request(clauses):
        return _decision(
            "clarify", [], explicit, excluded, ["adjacent_capability_ambiguous"],
            False, False, [], [], [],
        )
    elif not has_positive_action:
        reason_codes = ["no_specialized_need"]
    else:
        reason_codes = []
    if not has_positive_action:
        return _decision(
            "none", [], explicit, excluded, reason_codes,
            explanation_only, inventory_only, [], [], [],
        )
    missing_inputs = [
        field for field, pattern in MISSING_INPUT_PATTERNS.items() if pattern.search(current)
    ]
    decision = "single" if len(capabilities) == 1 else "composite"
    return _decision(
        decision, capabilities, explicit, excluded, ["specialized_need_detected"],
        False, False, missing_inputs, mandatory_capabilities, [],
    )


def _request_clauses(text: str) -> list[tuple[str, int]]:
    clauses: list[tuple[str, int]] = []
    start = 0
    for boundary in CLAUSE_BOUNDARY_RE.finditer(text):
        _append_clause(clauses, text, start, boundary.start())
        start = boundary.end()
    _append_clause(clauses, text, start, len(text))
    return clauses


def _append_clause(
    clauses: list[tuple[str, int]], text: str, start: int, end: int
) -> None:
    raw = text[start:end]
    clause = raw.strip()
    if clause:
        clauses.append((clause, start + len(raw) - len(raw.lstrip())))


def _positive_explicit_skill_occurrences(
    text: str,
) -> list[tuple[str, int, int]]:
    clauses = _request_clauses(text)
    occurrences: list[tuple[str, int, int]] = []
    previous_clause_confirmed_action = False

    for clause_index, (clause, offset) in enumerate(clauses):
        action_active = False
        clause_confirmed_action = False
        inherit_action = (
            previous_clause_confirmed_action
            and _follows_then_boundary(text, clauses, clause_index)
        )

        for start, end, event, name in _canonical_action_events(clause):
            if event == "positive":
                action_active = True
                inherit_action = False
                continue
            if event in {"information", "negative"}:
                action_active = False
                inherit_action = False
                continue
            if inherit_action and start == 0:
                action_active = True
                inherit_action = False
            if action_active:
                occurrences.append((name, offset + start, offset + end))
                clause_confirmed_action = True

        previous_clause_confirmed_action = (
            clause_confirmed_action and action_active
        )

    return occurrences


def _canonical_action_events(
    text: str,
) -> list[tuple[int, int, str, str]]:
    events: list[tuple[int, int, str, str]] = []
    for directive in SKILL_DIRECTIVE_RE.finditer(text):
        if directive.lastgroup == "positive":
            if _is_embedded_positive_directive(text, directive):
                continue
            event = "positive"
        else:
            event = "negative"
        events.append((directive.start(), directive.end(), event, ""))
    for pattern in (
        EXPLANATION_RE,
        INVENTORY_RE,
        HISTORICAL_CONTEXT_RE,
        REFERENCE_REPORT_RE,
    ):
        events.extend(
            (match.start(), match.end(), "information", "")
            for match in pattern.finditer(text)
        )
    for name, pattern in SKILL_NAME_PATTERNS.items():
        events.extend(
            (match.start(), match.end(), "skill", name)
            for match in pattern.finditer(text)
        )
    event_priority = {"negative": 0, "information": 0, "positive": 1, "skill": 2}
    return sorted(
        events,
        key=lambda item: (item[0], event_priority[item[2]], item[1], item[3]),
    )


def _is_embedded_positive_directive(
    text: str,
    directive: re.Match[str],
) -> bool:
    prefix = text[: directive.start()]
    return bool(re.search(r"(?:\b(?:how\s+)?to|\u5982\u4f55)\s*$", prefix, re.I))


def _information_position(text: str) -> int | None:
    positions = [
        match.start()
        for pattern in (
            EXPLANATION_RE,
            INVENTORY_RE,
            HISTORICAL_CONTEXT_RE,
            REFERENCE_REPORT_RE,
        )
        if (match := pattern.search(text)) is not None
    ]
    return min(positions, default=None)


def _follows_then_boundary(
    text: str,
    clauses: list[tuple[str, int]],
    clause_index: int,
) -> bool:
    if clause_index == 0:
        return False
    previous_clause, previous_offset = clauses[clause_index - 1]
    previous_end = previous_offset + len(previous_clause)
    current_offset = clauses[clause_index][1]
    boundary = text[previous_end:current_offset]
    return bool(re.fullmatch(r"\s*,?\s*\bthen\b\s*", boundary, re.I))


def _skill_directive_before(text: str, position: int) -> tuple[str, int]:
    directive_kind = ""
    directive_position = -1
    for directive in SKILL_DIRECTIVE_RE.finditer(text, 0, position):
        if directive.lastgroup == "bare_negative" and directive.end() != position:
            continue
        directive_kind = (
            "negative"
            if directive.lastgroup in {"negative", "bare_negative"}
            else "positive"
        )
        directive_position = directive.start()
    return directive_kind, directive_position


def _before_information(position: int, information_position: int | None) -> bool:
    return information_position is None or position < information_position


def _capability_for_skill(skill: str) -> str:
    return next(
        capability
        for capability, candidate in CAPABILITY_SKILL.items()
        if candidate == skill
    )


def _mask_canonical_skill_names(text: str) -> str:
    masked = list(text)
    for pattern in SKILL_NAME_PATTERNS.values():
        for match in pattern.finditer(text):
            masked[match.start() : match.end()] = " " * (match.end() - match.start())
    return "".join(masked)


def _record_evidence(
    evidence: dict[str, tuple[int, int]],
    capability: str,
    position: int,
    capability_index: int,
) -> None:
    candidate = (position, capability_index)
    if capability not in evidence or candidate < evidence[capability]:
        evidence[capability] = candidate


def _match_has_negation_prefix(text: str, position: int) -> bool:
    return bool(re.search(rf"{NEGATION_PREFIX}\s*$", text[:position], re.I))


def _is_non_action_browser_match(text: str, match: re.Match[str]) -> bool:
    return any(
        non_action.start() < match.end() and match.start() < non_action.end()
        for non_action in NON_ACTION_BROWSER_RE.finditer(text)
    )


def _is_non_action_code_review_match(text: str, match: re.Match[str]) -> bool:
    return any(
        non_action.start() < match.end() and match.start() < non_action.end()
        for non_action in NON_ACTION_CODE_REVIEW_RE.finditer(text)
    )


def _has_ambiguous_specialized_request(clauses: list[tuple[str, int]]) -> bool:
    for clause, _ in clauses:
        information_position = _information_position(clause)
        masked_clause = _mask_canonical_skill_names(clause)
        for match in AMBIGUOUS_SPECIALIZED_RE.finditer(masked_clause):
            if (
                _before_information(match.start(), information_position)
                and not _match_has_negation_prefix(masked_clause, match.start())
            ):
                return True
    return False


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
