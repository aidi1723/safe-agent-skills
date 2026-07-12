"""Bounded clause-level propositions for software release readiness."""

from __future__ import annotations

from dataclasses import dataclass
import re

from .intent_source import bound_task_text


MAX_READINESS_OCCURRENCES = 128


@dataclass(frozen=True)
class ReleaseReadinessProposition:
    start: int
    end: int
    action: str
    object_text: str
    polarity: str
    discourse_role: str


_OBJECT_RE = re.compile(
    r"(?<![a-z0-9])release[\s-]+(?:checklist|packet|readiness)(?![a-z0-9])|"
    r"发布清单",
    re.IGNORECASE,
)
_ACTION_RE = re.compile(
    r"(?<![a-z0-9])(?:prepare|review|check|verify|audit|assess|assemble|"
    r"create|build|draft|produce|document|approve)(?![a-z0-9])|"
    r"(?:准备|审查|检查|验证|审计|评估|组装|生成|创建|起草|记录|批准)",
    re.IGNORECASE,
)
_SOFTWARE_ANCHOR_RE = re.compile(
    r"(?<![a-z0-9])(?:repository|repo|package|cli|codebase|software|"
    r"open[ -]source|code[ -]artifact|maintainer|npm|docker(?:\s+image)?|"
    r"v?\d+\.\d+(?:\.\d+)?)(?![a-z0-9])|"
    r"(?:代码库|仓库|软件包|维护者|开源|软件|版本)",
    re.IGNORECASE,
)
_COORDINATOR_RE = re.compile(
    r"\s*(?:,\s*)?(?:\b(?:and|but|then)\b|然后|但是|但要|不过|再)\s*|"
    r"[;；\n。]|\s*[+＋]\s*",
    re.IGNORECASE,
)
_NEGATED_ACTION_PREFIX_RE = re.compile(
    r"(?:\b(?:can(?:not|'t)|do\s+not|don't|must\s+not|mustn't|"
    r"should\s+not|shouldn't|never|no\s+need\s+to|not\s+authorized\s+to)\s*$)|"
    r"(?:不能|不可|不需要|无需|不得|不要|暂不|先不|别|未授权)\s*$",
    re.IGNORECASE,
)
_NEGATED_ACTION_SUFFIX_RE = re.compile(r"^\s*(?:not|不|未)", re.IGNORECASE)
_STRUCTURAL_PREFIX_RE = re.compile(
    r"^\s*(?:#{1,6}\s+|>\s+|<h[1-6]\b[^>]*>|"
    r"(?:[-*+]\s+)?\[[ xX]\]\s+|"
    r"(?:example|label|terms?|navigation|headings?|menu|title|readme|"
    r"description)\s*[:：]|"
    r"[-*+]\s+)",
    re.IGNORECASE,
)
_REFERENCE_CLAUSE_RE = re.compile(
    r"^\s*(?:hypothetical(?:ly)?|suppose\b|if\b)|"
    r"\b(?:text|description|document)\s+(?:mentions|contains|lists)\b",
    re.IGNORECASE,
)
_FILENAME_SUFFIX_RE = re.compile(
    r"^\s*\.(?:md|markdown|json|ya?ml|toml|txt|html?|xml|csv)\b",
    re.IGNORECASE,
)
_LEGACY_CHECKLIST_RE = re.compile(
    r"^\s*(?:(?:a|the)\s+)?(?:draft\s+)?release\s+checklist"
    r"(?:\s+draft)?[.!]?\s*$|^\s*(?:一份)?发布清单(?:\s*草案)?[。！]?$",
    re.IGNORECASE,
)
_EVIDENCE_STATEMENT_RE = re.compile(
    r"^\s*release\s+readiness\s+has\b[\s\S]*\bevidence\b",
    re.IGNORECASE,
)
_QUOTES = (('"', '"'), ("'", "'"), ("“", "”"), ("‘", "’"), ("\u0060", "\u0060"))


def parse_release_readiness_propositions(
    source: str,
) -> tuple[ReleaseReadinessProposition, ...]:
    """Extract bounded action-object readiness propositions without raising."""
    source = bound_task_text(source)
    propositions: list[ReleaseReadinessProposition] = []
    for occurrence_index, match in enumerate(_OBJECT_RE.finditer(source)):
        if occurrence_index >= MAX_READINESS_OCCURRENCES:
            break
        object_start, object_end = match.span()
        object_text = match.group()
        line_start, line_end = _line_bounds(source, object_start, object_end)
        line = source[line_start:line_end]
        local_start = object_start - line_start
        local_end = object_end - line_start

        if (
            _is_quoted(line, local_start, local_end)
            or _STRUCTURAL_PREFIX_RE.search(line)
            or _FILENAME_SUFFIX_RE.match(line[local_end:])
        ):
            propositions.append(
                ReleaseReadinessProposition(
                    object_start,
                    object_end,
                    "reference",
                    object_text,
                    "positive",
                    "reference",
                )
            )
            continue

        if _LEGACY_CHECKLIST_RE.fullmatch(line):
            propositions.append(
                ReleaseReadinessProposition(
                    object_start,
                    object_end,
                    "prepare",
                    object_text,
                    "positive",
                    "request",
                )
            )
            continue

        proposition_start, proposition_end = _proposition_bounds(
            source, object_start, object_end
        )
        proposition = source[proposition_start:proposition_end]
        local_object_start = object_start - proposition_start
        local_object_end = object_end - proposition_start
        if _REFERENCE_CLAUSE_RE.search(proposition):
            propositions.append(
                ReleaseReadinessProposition(
                    object_start,
                    object_end,
                    "reference",
                    object_text,
                    "positive",
                    "reference",
                )
            )
            continue
        if _LEGACY_CHECKLIST_RE.fullmatch(proposition):
            propositions.append(
                ReleaseReadinessProposition(
                    object_start,
                    object_end,
                    "prepare",
                    object_text,
                    "positive",
                    "request",
                )
            )
            continue
        actions = tuple(_ACTION_RE.finditer(proposition))
        action = min(
            actions,
            key=lambda item: (
                max(
                    local_object_start - item.end(),
                    item.start() - local_object_end,
                    0,
                ),
                0 if item.end() <= local_object_start else 1,
                item.start(),
            ),
            default=None,
        )
        has_anchor = bool(_SOFTWARE_ANCHOR_RE.search(proposition))

        if (
            action is None
            and _EVIDENCE_STATEMENT_RE.search(line)
            and _SOFTWARE_ANCHOR_RE.search(line)
        ):
            propositions.append(
                ReleaseReadinessProposition(
                    object_start,
                    object_end,
                    "document",
                    object_text,
                    "positive",
                    "request",
                )
            )
            continue
        if action is None or not has_anchor:
            propositions.append(
                ReleaseReadinessProposition(
                    object_start,
                    object_end,
                    action.group().casefold() if action else "reference",
                    object_text,
                    "positive",
                    "reference",
                )
            )
            continue

        prefix = proposition[: action.start()]
        suffix = proposition[action.end() : local_object_start]
        polarity = (
            "negative"
            if _NEGATED_ACTION_PREFIX_RE.search(prefix)
            or _NEGATED_ACTION_SUFFIX_RE.search(suffix)
            else "positive"
        )
        action_start = proposition_start + action.start()
        action_end = proposition_start + action.end()
        propositions.append(
            ReleaseReadinessProposition(
                min(action_start, object_start),
                max(action_end, object_end),
                action.group().casefold(),
                object_text,
                polarity,
                "request",
            )
        )
    return tuple(propositions)


def _line_bounds(source: str, start: int, end: int) -> tuple[int, int]:
    line_start = source.rfind("\n", 0, start) + 1
    next_line = source.find("\n", end)
    return line_start, len(source) if next_line < 0 else next_line


def _proposition_bounds(source: str, start: int, end: int) -> tuple[int, int]:
    proposition_start = 0
    proposition_end = len(source)
    for boundary in _COORDINATOR_RE.finditer(source):
        if boundary.end() <= start:
            proposition_start = boundary.end()
        elif boundary.start() >= end:
            proposition_end = boundary.start()
            break
    return proposition_start, proposition_end


def _is_quoted(line: str, start: int, end: int) -> bool:
    for opener, closer in _QUOTES:
        search_start = 0
        while True:
            quote_start = line.find(opener, search_start)
            if quote_start < 0:
                break
            quote_end = line.find(closer, quote_start + len(opener))
            if quote_end < 0:
                break
            if quote_start <= start and end <= quote_end + len(closer):
                return True
            search_start = quote_end + len(closer)
    return False
