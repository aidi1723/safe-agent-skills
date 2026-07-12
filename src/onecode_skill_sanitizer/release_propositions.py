"""Bounded clause-level propositions for software release readiness."""

from __future__ import annotations

from dataclasses import dataclass
import re

from .intent_source import bound_task_text


MAX_READINESS_OCCURRENCES = 128
MAX_STRUCTURAL_REFERENCE_SPANS = 256
MAX_NARRATIVE_GOVERNOR_GAP = 256
MAX_NARRATIVE_TRANSITIONS = 128
MAX_RELEASE_OBJECT_PREFIX_CHARS = 96
MAX_RELEASE_OBJECT_COMPLEMENT_CHARS = 96
_HARD_SENTENCE_PUNCTUATION = ".!?！？。"
_DASH_CHARACTER = r"[-\u2010-\u2015\u2212\uff0d]"
_COMPOUND_SEPARATOR = rf"(?:\s+|{_DASH_CHARACTER})"


@dataclass(frozen=True)
class ReleaseReadinessProposition:
    start: int
    end: int
    action: str
    object_text: str
    polarity: str
    discourse_role: str


@dataclass(frozen=True)
class _BoundReadinessAction:
    match: re.Match[str]
    start: int
    end: int
    text: str
    polarity: str


@dataclass(frozen=True)
class _ReadinessCandidate:
    object_start: int
    object_end: int
    object_text: str
    proposition_start: int
    proposition_end: int
    actions: tuple[_BoundReadinessAction, ...]
    software_object: bool
    software_anchor_spans: tuple[tuple[int, int], ...]
    structurally_contained: bool
    sentence_reference: bool
    proposition_reference: bool
    filename_reference: bool
    legacy_line_request: bool
    legacy_proposition_request: bool
    evidence_statement_request: bool
    skip: bool


_OBJECT_RE = re.compile(
    r"(?<!\w)release[\s-]+(?:checklist|packet|readiness)(?!\w)|"
    r"发布清单",
    re.IGNORECASE,
)
_NON_SOFTWARE_RELEASE_DOMAIN_RE = re.compile(
    rf"(?<!\w)(?:talent|model(?!{_COMPOUND_SEPARATOR}serving\b)|"
    rf"content(?!{_COMPOUND_SEPARATOR}management\b))(?!\w)",
    re.IGNORECASE,
)
_SOFTWARE_RELEASE_DOMAIN_RE = re.compile(
    rf"(?<!\w)(?:content{_COMPOUND_SEPARATOR}management|"
    rf"model{_COMPOUND_SEPARATOR}serving)(?!\w)",
    re.IGNORECASE,
)
_STRONG_SOFTWARE_RELEASE_OBJECT_PATTERN = (
    r"(?<!\w)(?:repository|repo|software|code(?:base)?|"
    r"open[ -]source|maintainers?|npm|docker(?:\s+image)?|cli|version|"
    r"v?\d+\.\d+(?:\.\d+)?)(?!\w)|"
    r"(?:代码库|仓库|软件包|维护者|开源|软件|版本)"
)
_STRONG_SOFTWARE_RELEASE_OBJECT_RE = re.compile(
    _STRONG_SOFTWARE_RELEASE_OBJECT_PATTERN,
    re.IGNORECASE,
)
_STRONG_SOFTWARE_RELEASE_COMPLEMENT_RE = re.compile(
    rf"^\s*(?:for|of)\s+(?:(?:the|an?|this|that)\s+)?"
    rf"(?:{_STRONG_SOFTWARE_RELEASE_OBJECT_PATTERN})",
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
    rf"\s*(?:,\s*)?(?:(?<!{_DASH_CHARACTER})\b(?:and|but|then)\b"
    rf"(?!{_DASH_CHARACTER})|然后|但是|但要|不过|同时|再)\s*|"
    r"[;；\n。]|\s*[+＋]\s*",
    re.IGNORECASE,
)
_ACTION_MODIFIER = (
    r"(?:[^\W\d_]+ly|never|ever|yet|now|soon|still|just|already)"
)
_ENGLISH_ACTION_NEGATION_RE = re.compile(
    r"(?:\basked\s+(?:you|us|me|them)\s+not\s+to|"
    r"\b(?:refuse|refused|decline|declined)\s+to|"
    r"\bnot\s+(?:permitted|allowed)\s+to|"
    r"\bno\s+(?:requirement|need|plan)\s+to|"
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
_ENGLISH_REQUEST_PREFIX_RE = re.compile(
    r"^\s*[.,;:!?\"'”’\)\]}-]*\s*(?:"
    r"(?:[^\W\d_]+ly\s+){0,2}|"
    r"(?:please|kindly)(?:\s+[^\W\d_]+ly){0,2}\s+|"
    r"please\s+help(?:\s+to)?\s+|"
    r"however\s*,\s*|"
    r"(?:so|therefore)(?:\s*,)?\s+|"
    r"(?:first|next|now)(?:\s*,)?\s+|"
    r"let(?:['’]s|\s+us)\s+|"
    r"make\s+sure\s+to\s+|"
    r"(?:could|would|can)\s+you(?:\s+(?:please|kindly))?\s+|"
    r"(?:(?:the\s+)?(?:team|maintainers?)|we|i|you)\s+"
    r"(?:(?:needs?|wants?|plans?|intends?)\s+to|"
    r"would\s+like\s+to|should|must)\s+|"
    r"use\b[^,;!?\n]{0,80}\bto\s+|"
    r"(?:for|before|after|once|when|while|during|at|in|as\s+part\s+of)\b"
    r"[^,;!?\n]{0,80},\s*(?:(?:please|kindly)\s+)?"
    r")$",
    re.IGNORECASE,
)
_NARRATIVE_REFERENCE_PREFIX_RE = re.compile(
    r"^\s*(?:"
    r"according\s+to\s+(?:the\s+)?"
    r"(?:report|documentation|docs|guide|instruction)\b[^,;!?\n]{0,48},\s*|"
    r"(?:(?:the|an?)\s+)?"
    r"(?:report|documentation|docs|guide|instruction)\s+"
    r"(?:states?|recommends?|says?|instructs?|requires?)\b[^,;!?\n]{0,96}"
    r")$",
    re.IGNORECASE,
)
_CHINESE_REQUEST_PREFIX_RE = re.compile(
    r"^\s*[，。！？；：”’）】]*\s*(?:(?:请(?:你)?|请帮忙|麻烦|我们需要|"
    r"我们计划|维护者应|团队要|接下来[，,]?)"
    r"(?:立即|马上|仔细|认真|谨慎|再|先)?\s*)?$"
)
_CHINESE_ACTION_OBJECT_GAP_RE = re.compile(
    r"^(?:\s|该|本|这个|一个|一份|完整|详细的|好|一下|仓库|代码库|软件包|"
    r"维护者|开源|软件|版本|许可证|供应链|的|、|与|和|及|以及)*$"
)
_CHINESE_ACTION_NEGATION_RE = re.compile(
    r"(?:请勿|不能|不会|不可|不需要|无需|不得|不要|不打算|禁止|"
    r"暂不|先不|别|未授权)"
    r"(?:立即|马上|暂时|仔细|认真|谨慎|再|先)?\s*$"
)
_OBJECT_EXCLUSION_RE = re.compile(
    r"(?:\b(?:rather\s+than|instead\s+of|excluding|except)\s+"
    r"(?:(?:the|an?)\s+)?|"
    r"\bother\s+than\s+(?:(?:the|an?)\s+)?(?:repository\s+)?|"
    r"[\s,，]*(?:not\s+(?:(?:the|an?)\s+)?|而不是(?:这个|该)?))$",
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
_NARRATIVE_WORD_TOKEN = r"(?!(?:and|but|then)\b)[^\W\d_]+"
_NARRATIVE_NOUN_PHRASE = (
    rf"{_NARRATIVE_WORD_TOKEN}(?:\s+{_NARRATIVE_WORD_TOKEN}){{0,3}}"
)
_NARRATIVE_INSTRUCTION_START_RE = re.compile(
    r"^\s*(?:"
    r"(?:(?:the|an?)\s+)?(?:report|example|documentation|docs|guide|"
    r"(?:quoted\s+)?instruction)\s+"
    r"(?:"
    r"(?:says?|tells?|asks?)(?:"
    rf"(?:\s+{_NARRATIVE_NOUN_PHRASE})?\s+to\s+|"
    rf"\s+that\s+(?:{_NARRATIVE_NOUN_PHRASE}\s+)?"
    r"(?:should|must|needs?\s+to|is\s+to|are\s+to)\s+"
    r")|"
    r"says?\s+|"
    rf"(?:tells?|asks?)(?:\s+{_NARRATIVE_NOUN_PHRASE})?\s+"
    r")|"
    r"(?:(?:the|an?)\s+)?report\s+(?:states?|recommends?)\s+that\s+"
    rf"(?:{_NARRATIVE_NOUN_PHRASE}\s+)?(?:(?:should|must)\s+)?|"
    r"according\s+to\s+(?:the\s+)?(?:report|documentation|docs|guide)"
    rf"\s*,\s*(?:{_NARRATIVE_NOUN_PHRASE}\s+)?"
    r"(?:(?:should|must|needs?\s+to)\s+)?|"
    r"(?:(?:the|an?)\s+)?(?:documentation|docs|guide)\s+"
    rf"(?:instructs?|requires?)(?:\s+{_NARRATIVE_NOUN_PHRASE})?"
    r"\s+(?:to\s+)?"
    r")"
    r"(?:[^\W\d_]+ly\s+){0,2}"
    r"(?=(?:prepare|review|check|verify|audit|assess|assemble|create|build|"
    r"draft|produce|document|approve)\b)",
    re.IGNORECASE,
)
_NARRATIVE_GOVERNOR_START_RE = re.compile(
    r"^\s*(?:"
    r"(?:(?:the|an?)\s+)?(?:report|example|documentation|docs|guide|"
    r"(?:quoted\s+)?instruction)\s+(?:says?|tells?|asks?)\b|"
    r"(?:(?:the|an?)\s+)?report\s+(?:states?|recommends?)\s+that\b|"
    r"according\s+to\s+(?:the\s+)?(?:report|documentation|docs|guide)\s*,|"
    r"(?:(?:the|an?)\s+)?(?:documentation|docs|guide)\s+"
    r"(?:instructs?|requires?)\b"
    r")",
    re.IGNORECASE,
)
_NARRATIVE_INSTRUCTION_STOP_RE = re.compile(
    r"\s*(?:,\s*)?(?:\bbut\b|\bhowever\b|但是|但)",
    re.IGNORECASE,
)
_NARRATIVE_REQUEST_TRANSITION_RE = re.compile(
    r"\s*(?:,\s*)?(?:\bso\b|\btherefore\b|\band\s+now\b)",
    re.IGNORECASE,
)
_SENTENCE_REFERENCE_RE = re.compile(
    r"^\s*(?:#{1,6}\s+|>\s+|"
    r"(?:example|for\s+example|reference|quoted|hypothetical(?:ly)?|"
    r"suppose|if\b|label|terms?|navigation|headings?|menu|title|readme|"
    r"description)\s*[:：,，]?|"
    r"(?:[-*+]\s+)?\[[ xX]\]\s+|(?:e\.g\.|i\.e\.)\s*[,，:]?)|"
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
    candidates = _collect_readiness_candidates(
        source,
        sentence_boundaries,
        proposition_boundaries,
        structural_spans,
    )
    reported_reference_spans = _narrative_instruction_reference_spans(
        source, sentence_boundaries, candidates
    )
    propositions: list[ReleaseReadinessProposition] = []
    for candidate in candidates:
        reported_instruction = _range_is_contained(
            candidate.object_start,
            candidate.object_end,
            reported_reference_spans,
        )
        if (
            candidate.structurally_contained
            or reported_instruction
            or candidate.filename_reference
        ):
            propositions.append(
                ReleaseReadinessProposition(
                    candidate.object_start,
                    candidate.object_end,
                    "reference",
                    candidate.object_text,
                    "positive",
                    "reference",
                )
            )
            continue
        if candidate.legacy_line_request:
            propositions.append(
                ReleaseReadinessProposition(
                    candidate.object_start,
                    candidate.object_end,
                    "prepare",
                    candidate.object_text,
                    "positive",
                    "request",
                )
            )
            continue
        if candidate.sentence_reference or candidate.proposition_reference:
            propositions.append(
                ReleaseReadinessProposition(
                    candidate.object_start,
                    candidate.object_end,
                    "reference",
                    candidate.object_text,
                    "positive",
                    "reference",
                )
            )
            continue
        if candidate.legacy_proposition_request:
            propositions.append(
                ReleaseReadinessProposition(
                    candidate.object_start,
                    candidate.object_end,
                    "prepare",
                    candidate.object_text,
                    "positive",
                    "request",
                )
            )
            continue
        if candidate.skip:
            continue
        proposition = source[
            candidate.proposition_start : candidate.proposition_end
        ]
        request_actions = tuple(
            action
            for action in candidate.actions
            if _action_has_request_prefix(
                action.match,
                proposition,
                candidates,
                candidate.proposition_start,
            )
        )
        action = (request_actions or candidate.actions or (None,))[0]
        if action is None and candidate.evidence_statement_request:
            propositions.append(
                ReleaseReadinessProposition(
                    candidate.object_start,
                    candidate.object_end,
                    "document",
                    candidate.object_text,
                    "positive",
                    "request",
                )
            )
            continue
        if (
            action is None
            or not candidate.software_object
            or not candidate.software_anchor_spans
        ):
            propositions.append(
                ReleaseReadinessProposition(
                    candidate.object_start,
                    candidate.object_end,
                    action.text if action else "reference",
                    candidate.object_text,
                    "positive",
                    "reference",
                )
            )
            continue
        propositions.append(
            ReleaseReadinessProposition(
                min(action.start, candidate.object_start),
                max(action.end, candidate.object_end),
                action.text,
                candidate.object_text,
                action.polarity,
                "request" if action in request_actions else "reference",
            )
        )
    return tuple(propositions)


def _collect_readiness_candidates(
    source: str,
    sentence_boundaries: tuple[tuple[int, int], ...],
    proposition_boundaries: tuple[tuple[int, int], ...],
    structural_spans: tuple[tuple[int, int], ...],
) -> tuple[_ReadinessCandidate, ...]:
    candidates: list[_ReadinessCandidate] = []
    for occurrence_index, match in enumerate(_OBJECT_RE.finditer(source)):
        if occurrence_index >= MAX_READINESS_OCCURRENCES:
            break
        object_start, object_end = match.span()
        object_text = match.group()
        chinese_object = object_text == "发布清单"
        if chinese_object:
            object_prefix = source[max(0, object_start - 1) : object_start]
            object_suffix = source[object_end:]
            if object_prefix in {"已", "未", "不"} or object_suffix.startswith(
                ("项", "条目", "字段", "记录", "化")
            ):
                continue
        line_start, line_end = _line_bounds(source, object_start, object_end)
        line = source[line_start:line_end]
        proposition_start, proposition_end = _proposition_bounds(
            source, object_start, object_end, proposition_boundaries
        )
        proposition = source[proposition_start:proposition_end]
        local_object_start = object_start - proposition_start
        local_object_end = object_end - proposition_start
        raw_actions = tuple(_ACTION_RE.finditer(proposition))
        invalid_actions = tuple(
            item
            for item in raw_actions
            if _chinese_action_is_nominalized(item, proposition)
        )
        actions = tuple(
            item
            for item in raw_actions
            if item not in invalid_actions
            and (
                not chinese_object
                or _chinese_action_governs_object(
                    item, proposition, local_object_start
                )
            )
        )
        ranked_actions = tuple(
            sorted(
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
            )
        )
        bound_actions: list[_BoundReadinessAction] = []
        for action in ranked_actions:
            prefix = proposition[: action.start()]
            between_action_and_object = proposition[
                action.end() : local_object_start
            ]
            bound_actions.append(
                _BoundReadinessAction(
                    action,
                    proposition_start + action.start(),
                    proposition_start + action.end(),
                    action.group().casefold(),
                    (
                        "negative"
                        if _action_is_negated(prefix, between_action_and_object)
                        else "positive"
                    ),
                )
            )
        sentence_start, sentence_end = _bounds_from_boundaries(
            source, object_start, object_end, sentence_boundaries
        )
        sentence = source[sentence_start:sentence_end]
        candidates.append(
            _ReadinessCandidate(
                object_start,
                object_end,
                object_text,
                proposition_start,
                proposition_end,
                tuple(bound_actions),
                _release_object_is_software(
                    proposition, local_object_start, local_object_end
                ),
                tuple(
                    (
                        proposition_start + anchor.start(),
                        proposition_start + anchor.end(),
                    )
                    for anchor in _SOFTWARE_ANCHOR_RE.finditer(proposition)
                ),
                _range_is_contained(object_start, object_end, structural_spans),
                bool(_SENTENCE_REFERENCE_RE.search(sentence)),
                bool(
                    _STRUCTURAL_PREFIX_RE.search(proposition)
                    or _REFERENCE_CLAUSE_RE.search(proposition)
                ),
                _FILENAME_SUFFIX_RE.match(line[object_end - line_start :])
                is not None,
                _LEGACY_CHECKLIST_RE.fullmatch(line) is not None,
                _LEGACY_CHECKLIST_RE.fullmatch(proposition) is not None,
                bool(
                    _EVIDENCE_STATEMENT_RE.search(line)
                    and _SOFTWARE_ANCHOR_RE.search(line)
                ),
                bool(raw_actions and not actions and chinese_object),
            )
        )
    return tuple(candidates)


def _release_object_is_software(
    proposition: str, object_start: int, object_end: int
) -> bool:
    prefix_start = max(0, object_start - MAX_RELEASE_OBJECT_PREFIX_CHARS)
    prefix = proposition[prefix_start:object_start]
    boundary = max(
        (prefix.rfind(character) for character in ",;:.!?()[]{}。！？；\n"),
        default=-1,
    )
    coordinator_end = max(
        (match.end() for match in _COORDINATOR_RE.finditer(prefix)),
        default=0,
    )
    noun_phrase = prefix[max(boundary + 1, coordinator_end) :]
    non_software = tuple(_NON_SOFTWARE_RELEASE_DOMAIN_RE.finditer(noun_phrase))
    if non_software:
        return False
    if _SOFTWARE_RELEASE_DOMAIN_RE.search(noun_phrase):
        if _STRONG_SOFTWARE_RELEASE_OBJECT_RE.search(noun_phrase):
            return True
        complement = proposition[
            object_end : object_end + MAX_RELEASE_OBJECT_COMPLEMENT_CHARS
        ]
        return (
            _STRONG_SOFTWARE_RELEASE_COMPLEMENT_RE.match(complement)
            is not None
        )
    return True


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
        if character not in _HARD_SENTENCE_PUNCTUATION:
            index += 1
            continue
        if character == "." and _dot_is_internal(source, index):
            index += 1
            continue
        boundary_start = index
        while (
            index < len(source)
            and source[index] in _HARD_SENTENCE_PUNCTUATION
        ):
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


def _action_has_request_prefix(
    action: re.Match[str],
    proposition: str,
    readiness_candidates: tuple[_ReadinessCandidate, ...] = (),
    proposition_start: int = 0,
) -> bool:
    prefix = _without_structural_reference_spans(
        proposition[: action.start()]
    )
    if _is_chinese_action(action.group()):
        return _CHINESE_REQUEST_PREFIX_RE.fullmatch(prefix) is not None
    if _POSITIVE_OBLIGATION_RE.search(prefix) or _NOT_ONLY_RE.search(prefix):
        return True
    governor = _NARRATIVE_GOVERNOR_START_RE.match(prefix)
    if governor is not None and _independent_narrative_request_transition(
        prefix,
        governor.end(),
        len(prefix),
        readiness_candidates,
        proposition_start,
    ) is not None:
        return True
    if _NARRATIVE_REFERENCE_PREFIX_RE.fullmatch(prefix):
        return False
    return _ENGLISH_REQUEST_PREFIX_RE.fullmatch(prefix) is not None


def _without_structural_reference_spans(source: str) -> str:
    spans = _structural_reference_spans(source)
    if not spans:
        return source
    pieces: list[str] = []
    cursor = 0
    for start, end in spans:
        if start > cursor:
            pieces.append(source[cursor:start])
        cursor = max(cursor, end)
    pieces.append(source[cursor:])
    return "".join(pieces)


def _chinese_action_governs_object(
    action: re.Match[str], proposition: str, object_start: int
) -> bool:
    if action.end() > object_start:
        return False
    gap = proposition[action.end() : object_start]
    return len(gap) <= 32 and _CHINESE_ACTION_OBJECT_GAP_RE.fullmatch(gap) is not None


def _structural_reference_spans(
    source: str,
) -> tuple[tuple[int, int], ...]:
    spans: list[tuple[int, int]] = []
    scanned_spans = (
        *_delimited_spans(source, "```", "```"),
        *_delimited_spans(source, "~~~", "~~~"),
        *_inline_code_spans(source),
        *_quote_spans(source, '"', '"'),
        *_quote_spans(source, "“", "”"),
        *_quote_spans(source, "‘", "’"),
        *_quote_spans(source, "'", "'", require_word_boundary=True),
        *_html_pre_spans(source),
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


def _html_pre_spans(source: str) -> tuple[tuple[int, int], ...]:
    opening = re.compile(r"<pre\b[^>]*>", re.IGNORECASE)
    closing = re.compile(r"</pre\s*>", re.IGNORECASE)
    spans: list[tuple[int, int]] = []
    cursor = 0
    while cursor < len(source):
        start_match = opening.search(source, cursor)
        if start_match is None:
            break
        close_match = closing.search(source, start_match.end())
        if close_match is None:
            spans.append((start_match.start(), len(source)))
            break
        spans.append((start_match.start(), close_match.end()))
        if len(spans) >= MAX_STRUCTURAL_REFERENCE_SPANS:
            return ((0, len(source)),)
        cursor = close_match.end()
    return tuple(spans)


def _narrative_instruction_reference_spans(
    source: str,
    sentence_boundaries: tuple[tuple[int, int], ...],
    readiness_candidates: tuple[_ReadinessCandidate, ...] | None = None,
) -> tuple[tuple[int, int], ...]:
    if readiness_candidates is None:
        proposition_boundaries = tuple(
            sorted(
                set(
                    [match.span() for match in _COORDINATOR_RE.finditer(source)]
                    + list(sentence_boundaries)
                )
            )
        )
        readiness_candidates = _collect_readiness_candidates(
            source,
            sentence_boundaries,
            proposition_boundaries,
            _structural_reference_spans(source),
        )
    candidate_starts = {0}
    candidate_starts.update(
        match.end() for match in re.finditer(r"[;；\n]", source)
    )
    candidate_starts.update(
        match.end() for match in _COORDINATOR_RE.finditer(source)
    )
    candidate_starts.update(end for _, end in sentence_boundaries)
    spans: list[tuple[int, int]] = []
    for candidate_start in sorted(candidate_starts):
        candidate = source[candidate_start:]
        governor = _NARRATIVE_GOVERNOR_START_RE.match(candidate)
        match = _NARRATIVE_INSTRUCTION_START_RE.match(candidate)
        if match is None:
            if governor is None:
                continue
            match = governor
        span_start = candidate_start + match.start()
        instruction_start = candidate_start + match.end()
        stops = [len(source)]
        semicolon = re.search(r"[;；]", source[instruction_start:])
        if semicolon is not None:
            stops.append(instruction_start + semicolon.start())
        adversative = _NARRATIVE_INSTRUCTION_STOP_RE.search(
            source, instruction_start
        )
        if adversative is not None:
            stops.append(adversative.start())
        stops.extend(
            boundary_start
            for boundary_start, _ in sentence_boundaries
            if boundary_start >= instruction_start
        )
        if governor is not None:
            transition = _independent_narrative_request_transition(
                source,
                candidate_start + governor.end(),
                min(stops),
                readiness_candidates,
            )
            if transition is not None:
                stops.append(transition)
        spans.append((span_start, min(stops)))
        if len(spans) >= MAX_STRUCTURAL_REFERENCE_SPANS:
            return ((0, len(source)),)
    return tuple(spans)


def _independent_narrative_request_transition(
    source: str,
    governor_end: int,
    search_end: int,
    readiness_candidates: tuple[_ReadinessCandidate, ...] = (),
    source_offset: int = 0,
) -> int | None:
    bounded_end = min(search_end, governor_end + MAX_NARRATIVE_GOVERNOR_GAP)
    segment_start = governor_end
    for transition_index, transition in enumerate(
        _NARRATIVE_REQUEST_TRANSITION_RE.finditer(
            source, governor_end, bounded_end
        )
    ):
        if transition_index >= MAX_NARRATIVE_TRANSITIONS:
            return None
        if _governed_readiness_chain_started(
            readiness_candidates,
            source_offset + segment_start,
            source_offset + transition.start(),
        ):
            segment_start = transition.end()
            continue
        return transition.start()
    return None


def _governed_readiness_chain_started(
    readiness_candidates: tuple[_ReadinessCandidate, ...],
    segment_start: int,
    transition_start: int,
) -> bool:
    for candidate in readiness_candidates:
        if (
            candidate.object_start < segment_start
            or candidate.object_end > transition_start
            or candidate.structurally_contained
            or candidate.sentence_reference
            or candidate.proposition_reference
            or candidate.filename_reference
            or candidate.skip
            or not candidate.software_object
            or not any(
                segment_start <= anchor_start
                and anchor_end <= transition_start
                for anchor_start, anchor_end in candidate.software_anchor_spans
            )
        ):
            continue
        if candidate.actions:
            action = candidate.actions[0]
            if (
                action.polarity == "positive"
                and segment_start <= action.start
                and action.end <= candidate.object_start
            ):
                return True
    return False


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


def _chinese_action_is_nominalized(match: re.Match[str], source: str) -> bool:
    action = match.group()
    if not _is_chinese_action(action):
        return False
    suffix = source[match.end() :]
    return suffix.startswith(("度", "工作", "流程", "阶段", "事项", "报告", "中")) or (
        action == "准备" and suffix.startswith(("性", "项"))
    )


def _range_is_contained(
    start: int, end: int, spans: tuple[tuple[int, int], ...]
) -> bool:
    return any(
        span_start <= start and end <= span_end
        for span_start, span_end in spans
    )
