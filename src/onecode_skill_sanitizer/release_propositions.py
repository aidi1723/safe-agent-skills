"""Bounded clause-level propositions for software release readiness."""

from __future__ import annotations

from dataclasses import dataclass
import re

from .intent_source import bound_task_text


MAX_READINESS_OCCURRENCES = 128
MAX_STRUCTURAL_REFERENCE_SPANS = 256


@dataclass(frozen=True)
class ReleaseReadinessProposition:
    start: int
    end: int
    action: str
    object_text: str
    polarity: str
    discourse_role: str


_OBJECT_RE = re.compile(
    r"(?<!\w)release[\s-]+(?:checklist|packet|readiness)(?!\w)|"
    r"发布清单",
    re.IGNORECASE,
)
_ACTION_RE = re.compile(
    r"(?<!\w)(?:prepare|review|check|verify|audit|assess|assemble|"
    r"create|build|draft|produce|document|approve)(?!\w)|"
    r"(?:准备|审查|检查|验证|审计|评估|组装|生成|创建|起草|记录|批准)",
    re.IGNORECASE,
)
_SOFTWARE_ANCHOR_RE = re.compile(
    r"(?<!\w)(?:repository|repo|package|cli|codebase|software|"
    r"open[ -]source|code[ -]artifact|maintainer|npm|docker(?:\s+image)?|"
    r"v?\d+\.\d+(?:\.\d+)?)(?!\w)|"
    r"(?:代码库|仓库|软件包|维护者|开源|软件|版本)",
    re.IGNORECASE,
)
_COORDINATOR_RE = re.compile(
    r"\s*(?:,\s*)?(?:\b(?:and|but|then)\b|然后|但是|但要|不过|再)\s*|"
    r"[;；\n。]|\s*[+＋]\s*",
    re.IGNORECASE,
)
_ACTION_MODIFIER = (
    r"(?:[^\W\d_]+ly|never|ever|yet|now|soon|still|just|already)"
)
_ENGLISH_ACTION_NEGATION_RE = re.compile(
    r"(?:\basked\s+(?:you|us|me|them)\s+not\s+to|"
    r"\b(?:am|is|are)\s+not\s+going\s+to|"
    r"\b(?:have|has)\s+no\s+plans?\s+to|"
    r"\b(?:am|is|are)\s+not\s+to|"
    r"\b(?:do|will|can|must|should)\s+not|"
    r"\b(?:do|ca|wo|must|should)n['’]t|"
    r"\bcannot|\bnever|\bno\s+need\s+to|"
    r"\bnot\s+authorized\s+to|\bnot\s+to|\bnot)"
    rf"(?:\s+{_ACTION_MODIFIER}){{0,3}}\s*$",
    re.IGNORECASE,
)
_NEGATIVE_INTENT_RE = re.compile(
    r"(?:\b(?:do|will|can)\s+not|"
    r"\b(?:do|ca|wo)n['’]t|\bcannot)"
    rf"(?:\s+{_ACTION_MODIFIER}){{0,2}}\s+"
    r"(?:want|plan|intend)\s+to"
    rf"(?:\s+{_ACTION_MODIFIER}){{0,2}}\s*$",
    re.IGNORECASE,
)
_POSITIVE_OBLIGATION_RE = re.compile(
    r"(?:\bdo\s+not|\bdon['’]t)"
    rf"(?:\s+{_ACTION_MODIFIER}){{0,2}}\s+"
    r"(?:forget|fail|neglect|hesitate)\s+to"
    rf"(?:\s+{_ACTION_MODIFIER}){{0,2}}\s*$",
    re.IGNORECASE,
)
_NOT_ONLY_RE = re.compile(r"\bnot\s+only\s*$", re.IGNORECASE)
_CHINESE_ACTION_NEGATION_RE = re.compile(
    r"(?:请勿|不能|不会|不可|不需要|无需|不得|不要|不打算|禁止|"
    r"暂不|先不|别|未授权)"
    r"(?:立即|马上|暂时|仔细|认真|谨慎|再|先)?\s*$"
)
_OBJECT_EXCLUSION_RE = re.compile(
    r"[\s,，]*(?:not\s+(?:(?:the|an?)\s+)?|而不是(?:这个|该)?)$",
    re.IGNORECASE,
)
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
_SENTENCE_REFERENCE_RE = re.compile(
    r"^\s*(?:#{1,6}\s+|>\s+|"
    r"(?:example|for\s+example|reference|quoted|hypothetical(?:ly)?|"
    r"suppose|if\b|label|terms?|navigation|headings?|menu|title|readme|"
    r"description)\s*[:：,，]?|"
    r"(?:[-*+]\s+)?\[[ xX]\]\s+)|"
    r"\bdiscussed\s+whether\b|"
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
_FILENAME_EXTENSION_RE = re.compile(
    r"\.(?:md|markdown|json|ya?ml|toml|txt|html?|xml|csv|py|js|ts|"
    r"tsx|jsx|css|scss|rs|go|java)(?!\w)",
    re.IGNORECASE,
)
_STRUCTURAL_REFERENCE_PATTERNS = (
    re.compile(r"\[[^\]\n]*\](?:\([^\)\n]*\))?"),
    re.compile(r"<h[1-6]\b[^>]*>[\s\S]*?</h[1-6]\s*>", re.IGNORECASE),
    re.compile(r"<code\b[^>]*>[\s\S]*?</code\s*>", re.IGNORECASE),
    re.compile(r"(?m)^(?: {4,}|\t).*(?:\n|$)"),
)


def parse_release_readiness_propositions(
    source: str,
) -> tuple[ReleaseReadinessProposition, ...]:
    """Extract bounded action-object readiness propositions without raising."""
    source = bound_task_text(source)
    sentence_boundaries = _sentence_boundaries(source)
    proposition_boundaries = tuple(
        sorted(
            set(
                [match.span() for match in _COORDINATOR_RE.finditer(source)]
                + list(sentence_boundaries)
            )
        )
    )
    structural_spans = _structural_reference_spans(source)
    propositions: list[ReleaseReadinessProposition] = []
    for occurrence_index, match in enumerate(_OBJECT_RE.finditer(source)):
        if occurrence_index >= MAX_READINESS_OCCURRENCES:
            break
        object_start, object_end = match.span()
        object_text = match.group()
        if object_text == "发布清单" and source[object_end : object_end + 1] == "化":
            continue
        line_start, line_end = _line_bounds(source, object_start, object_end)
        line = source[line_start:line_end]
        local_end = object_end - line_start

        sentence_start, sentence_end = _bounds_from_boundaries(
            source, object_start, object_end, sentence_boundaries
        )
        sentence = source[sentence_start:sentence_end]
        sentence_is_reference = bool(_SENTENCE_REFERENCE_RE.search(sentence))
        structurally_contained = _range_is_contained(
            object_start, object_end, structural_spans
        )

        if structurally_contained or _FILENAME_SUFFIX_RE.match(line[local_end:]):
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
            source, object_start, object_end, proposition_boundaries
        )
        proposition = source[proposition_start:proposition_end]
        local_object_start = object_start - proposition_start
        local_object_end = object_end - proposition_start
        if (
            sentence_is_reference
            or _STRUCTURAL_PREFIX_RE.search(proposition)
            or _REFERENCE_CLAUSE_RE.search(proposition)
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
        raw_actions = tuple(_ACTION_RE.finditer(proposition))
        invalid_actions = tuple(
            item
            for item in raw_actions
            if _is_chinese_action(item.group())
            and proposition[item.end() : item.end() + 1] == "度"
        )
        actions = tuple(item for item in raw_actions if item not in invalid_actions)
        if invalid_actions and not actions:
            continue
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
        between_action_and_object = proposition[
            action.end() : local_object_start
        ]
        polarity = (
            "negative"
            if _action_is_negated(prefix, between_action_and_object)
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


def _proposition_bounds(
    source: str,
    start: int,
    end: int,
    boundaries: tuple[tuple[int, int], ...],
) -> tuple[int, int]:
    return _bounds_from_boundaries(source, start, end, boundaries)


def _bounds_from_boundaries(
    source: str,
    start: int,
    end: int,
    boundaries: tuple[tuple[int, int], ...],
) -> tuple[int, int]:
    region_start = 0
    region_end = len(source)
    for boundary_start, boundary_end in boundaries:
        if boundary_end <= start:
            region_start = boundary_end
        elif boundary_start >= end:
            region_end = boundary_start
            break
    return region_start, region_end


def _sentence_boundaries(source: str) -> tuple[tuple[int, int], ...]:
    boundaries: list[tuple[int, int]] = []
    index = 0
    while index < len(source):
        character = source[index]
        if character == "\n":
            boundaries.append((index, index + 1))
            index += 1
            continue
        if character not in ".!?！？":
            index += 1
            continue
        if character == "." and _dot_is_internal(source, index):
            index += 1
            continue
        boundary_start = index
        while index < len(source) and source[index] in ".!?！？":
            index += 1
        while index < len(source) and source[index].isspace():
            index += 1
        boundaries.append((boundary_start, index))
    return tuple(boundaries)


def _dot_is_internal(source: str, index: int) -> bool:
    previous = source[index - 1] if index else ""
    following = source[index + 1] if index + 1 < len(source) else ""
    if previous.isdigit() and following.isdigit():
        return True
    around = source[max(0, index - 3) : index + 3].casefold()
    if "e.g." in around or "i.e." in around:
        return True
    return _FILENAME_EXTENSION_RE.match(source, index) is not None


def _action_is_negated(prefix: str, between_action_and_object: str) -> bool:
    if _POSITIVE_OBLIGATION_RE.search(prefix) or _NOT_ONLY_RE.search(prefix):
        return False
    return bool(
        _NEGATIVE_INTENT_RE.search(prefix)
        or _ENGLISH_ACTION_NEGATION_RE.search(prefix)
        or _CHINESE_ACTION_NEGATION_RE.search(prefix)
        or _OBJECT_EXCLUSION_RE.search(between_action_and_object)
    )


def _structural_reference_spans(
    source: str,
) -> tuple[tuple[int, int], ...]:
    spans: list[tuple[int, int]] = []
    scanned_spans = (
        *_delimited_spans(source, "```", "```"),
        *_inline_code_spans(source),
        *_quote_spans(source, '"', '"'),
        *_quote_spans(source, "“", "”"),
        *_quote_spans(source, "‘", "’"),
        *_quote_spans(source, "'", "'", require_word_boundary=True),
    )
    for span in scanned_spans:
        spans.append(span)
        if len(spans) >= MAX_STRUCTURAL_REFERENCE_SPANS:
            return ((0, len(source)),)
    for pattern in _STRUCTURAL_REFERENCE_PATTERNS:
        for match in pattern.finditer(source):
            spans.append(match.span())
            if len(spans) >= MAX_STRUCTURAL_REFERENCE_SPANS:
                return ((0, len(source)),)
    return tuple(sorted(spans))


def _delimited_spans(
    source: str, opening: str, closing: str
) -> tuple[tuple[int, int], ...]:
    spans: list[tuple[int, int]] = []
    cursor = 0
    while cursor < len(source):
        start = source.find(opening, cursor)
        if start < 0:
            break
        close_start = source.find(closing, start + len(opening))
        while close_start >= 0 and _is_escaped(source, close_start):
            close_start = source.find(closing, close_start + len(closing))
        if close_start < 0:
            spans.append((start, len(source)))
            break
        end = close_start + len(closing)
        spans.append((start, end))
        cursor = end
    return tuple(spans)


def _inline_code_spans(source: str) -> tuple[tuple[int, int], ...]:
    fence_spans = _delimited_spans(source, "```", "```")
    spans: list[tuple[int, int]] = []
    cursor = 0
    while cursor < len(source):
        start = source.find("`", cursor)
        if start < 0:
            break
        if source.startswith("```", start) or _range_is_contained(
            start, start + 1, fence_spans
        ):
            cursor = start + 1
            continue
        close_start = source.find("`", start + 1)
        while close_start >= 0 and (
            source.startswith("```", close_start)
            or _is_escaped(source, close_start)
        ):
            close_start = source.find("`", close_start + 1)
        if close_start < 0:
            spans.append((start, len(source)))
            break
        spans.append((start, close_start + 1))
        cursor = close_start + 1
    return tuple(spans)


def _quote_spans(
    source: str,
    opening: str,
    closing: str,
    *,
    require_word_boundary: bool = False,
) -> tuple[tuple[int, int], ...]:
    spans: list[tuple[int, int]] = []
    cursor = 0
    while cursor < len(source):
        start = source.find(opening, cursor)
        while start >= 0 and (
            _is_escaped(source, start)
            or (
                require_word_boundary
                and start > 0
                and (source[start - 1].isalnum() or source[start - 1] == "_")
            )
        ):
            start = source.find(opening, start + len(opening))
        if start < 0:
            break
        close_start = source.find(closing, start + len(opening))
        while close_start >= 0 and (
            _is_escaped(source, close_start)
            or (
                require_word_boundary
                and close_start + len(closing) < len(source)
                and (
                    source[close_start + len(closing)].isalnum()
                    or source[close_start + len(closing)] == "_"
                )
            )
        ):
            close_start = source.find(closing, close_start + len(closing))
        if close_start < 0:
            spans.append((start, len(source)))
            break
        end = close_start + len(closing)
        spans.append((start, end))
        cursor = end
    return tuple(spans)


def _is_escaped(source: str, index: int) -> bool:
    backslashes = 0
    index -= 1
    while index >= 0 and source[index] == "\\":
        backslashes += 1
        index -= 1
    return backslashes % 2 == 1


def _is_chinese_action(action: str) -> bool:
    return any("\u4e00" <= character <= "\u9fff" for character in action)


def _range_is_contained(
    start: int, end: int, spans: tuple[tuple[int, int], ...]
) -> bool:
    return any(
        span_start <= start and end <= span_end
        for span_start, span_end in spans
    )
