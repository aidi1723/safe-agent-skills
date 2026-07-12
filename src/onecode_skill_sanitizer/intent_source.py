"""Shared hard boundary and source predicates for intent parsing."""

from dataclasses import dataclass
import re


MAX_TASK_SCAN_CHARS = 20_000

_RELEASE_ACTION_PHRASE = (
    r"(?:验证(?:通过)?|测试通过|完成|批准|审批通过|审核通过)后(?:再)?"
    r"(?:发布|上线|推送)|"
    r"(?:发布|上线|推送)(?:更新|结果|版本|新版本|软件包|包|项目|网站|应用|代码|变更|到\S+)|"
    r"推送(?:代码)?(?:到)?\s*github|"
    r"\b(?:publish|release)\b\s+(?:the\s+|an?\s+)?"
    r"(?:(?:verified|approved)\s+)?"
    r"(?:update|results?|package|version|project|website|app|code|changes?|release\s+notes)\b|"
    r"\bpush\s+(?:changes\s+to\s+github|the\s+repository(?:\s+to\s+github)?|"
    r"to\s+github)\b|\bopen[-\s]+source\s+release\b"
    r"|\bopen[-\s]+source\s+"
    r"(?:the|this|that|our|your|their|a|an)\s+"
    r"(?:project|repository|repo|package|codebase|software|code)\b"
)
_RELEASE_ACTION_RE = re.compile(_RELEASE_ACTION_PHRASE, re.IGNORECASE)
_RELEASE_ACTION_CLAUSE_BOUNDARY_RE = re.compile(
    r"[;；\n。！？!?]|(?<=[,.，])\s*(?:and\s+)?(?:then|but|so|therefore)\b",
    re.IGNORECASE,
)
_RELEASE_ACTION_DOT_ABBREVIATIONS = ("e.g.", "i.e.")
_RELEASE_ACTION_TITLE_ABBREVIATIONS = frozenset(
    {
        "capt",
        "cmdr",
        "col",
        "dr",
        "gen",
        "hon",
        "jr",
        "lt",
        "mr",
        "mrs",
        "ms",
        "prof",
        "rev",
        "sgt",
        "sr",
    }
)
_RELEASE_ACTION_NEGATED_PREFIX_RE = re.compile(
    r"(?:\b(?:do|must|should|will|can)\s+not|"
    r"\b(?:do|ca|wo|must|should)n['’]t|\bnever|"
    r"\bno\s+need\s+to|\bnot\s+authorized\s+to)\b"
    r"(?:(?:\s*,\s*|\s+)[^\s,;.!?。！？；，]+){0,4}"
    r"\s*,?\s*$",
    re.IGNORECASE,
)
_RELEASE_ACTION_REPORTED_PREFIX_RE = re.compile(
    r"\b(?:says?|said|asks?|asked|tells?|told|claims?|claimed|"
    r"reports?|reported|recommends?|recommended|instructs?|instructed|"
    r"requires?|required)\b[\s\S]{0,128}$",
    re.IGNORECASE,
)
_BARE_RELEASE_ACTION_RE = re.compile(
    r"(?:publish|release|push)(?:\s+now)?|"
    r"(?:发布|上线|推送)(?:现在|立即)?",
    re.IGNORECASE,
)
_APPROVAL_RELEASE_RE = re.compile(
    r"^\s*(?:"
    r"(?:在\s*)?(?P<cn_source>(?:PR|拉取请求)\s*"
    r"(?:审批通过|批准|审核通过)后)\s*[,，]?\s*"
    r"(?P<cn_target>.+?)|"
    r"(?P<en_source>after\s+(?:(?:the\s+)?(?:pr|pull\s+request)\s+"
    r"is\s+approved|(?:pr|pull\s+request)\s+approval))\s*[,，]?\s*"
    r"(?P<en_target>.+?)"
    r")\s*$",
    re.IGNORECASE,
)
_RELEASE_PRECONDITION_RE = re.compile(
    r"^\s*(?:"
    r"before\s+(?:the\s+)?(?P<en_source>(?:pr|pull\s+request)\s+approval)"
    r"\s*[,\uff0c]?\s*(?P<en_target>.+?)|"
    r"(?:在\s*)?(?P<cn_source>(?:PR|拉取请求)\s*"
    r"(?:审批|批准|审核)前)\s*[,\uff0c]?\s*(?P<cn_target>.+?)"
    r")\s*$",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class SourceActionSpan:
    source: str
    target: str
    source_start: int
    target_start: int


def bound_task_text(text: str) -> str:
    """Return the only source region intent parsers may inspect."""
    return text[:MAX_TASK_SCAN_CHARS]


def is_release_action_text(text: str, *, allow_bare: bool = False) -> bool:
    """Validate a complete release action using the central action taxonomy."""
    text = bound_task_text(text).strip()
    return bool(
        _RELEASE_ACTION_RE.fullmatch(text)
        or (allow_bare and _BARE_RELEASE_ACTION_RE.fullmatch(text))
    )


def source_contains_release_action(text: str) -> bool:
    """Find a positive host release action inside a bounded task source."""
    text = bound_task_text(text)
    boundaries = iter(_release_action_clause_boundary_ends(text))
    boundary = next(boundaries, None)
    clause_start = 0
    for action in _RELEASE_ACTION_RE.finditer(text):
        while boundary is not None and boundary <= action.start():
            clause_start = boundary
            boundary = next(boundaries, None)
        prefix = text[clause_start : action.start()]
        if (
            _RELEASE_ACTION_NEGATED_PREFIX_RE.search(prefix) is None
            and _RELEASE_ACTION_REPORTED_PREFIX_RE.search(prefix) is None
        ):
            return True
    return False


def _release_action_clause_boundary_ends(text: str) -> tuple[int, ...]:
    boundaries = [
        match.end() for match in _RELEASE_ACTION_CLAUSE_BOUNDARY_RE.finditer(text)
    ]
    boundaries.extend(
        index + 1
        for index, character in enumerate(text)
        if character == "." and _is_release_sentence_dot(text, index)
    )
    return tuple(sorted(boundaries))


def _is_release_sentence_dot(text: str, index: int) -> bool:
    if (
        index > 0
        and index + 1 < len(text)
        and text[index - 1].isdigit()
        and text[index + 1].isdigit()
    ):
        return False
    if (
        index > 0
        and text[index - 1].isalpha()
        and (
            (
                index >= 3
                and text[index - 2] == "."
                and text[index - 3].isalpha()
            )
            or (
                index + 2 < len(text)
                and text[index + 1].isalpha()
                and text[index + 2] == "."
            )
        )
    ):
        return False
    if (
        index > 0
        and text[index - 1].isalpha()
        and (index < 2 or not text[index - 2].isalpha())
    ):
        name_start = index + 1
        while (
            name_start < len(text)
            and name_start <= index + 4
            and text[name_start] in " \t"
        ):
            name_start += 1
        if (
            name_start > index + 1
            and name_start < len(text)
            and text[name_start].isupper()
        ):
            return False
    token_start = index
    while token_start > 0 and text[token_start - 1].isalpha():
        token_start -= 1
    if text[token_start:index].casefold() in _RELEASE_ACTION_TITLE_ABBREVIATIONS:
        return False
    for abbreviation in _RELEASE_ACTION_DOT_ABBREVIATIONS:
        first_start = max(0, index - len(abbreviation) + 1)
        last_start = min(index, len(text) - len(abbreviation))
        if any(
            text[start : start + len(abbreviation)].casefold() == abbreviation
            for start in range(first_start, last_start + 1)
        ):
            return False
    return True


def parse_approval_release(text: str) -> tuple[str, str] | None:
    """Return canonical approval source and validated release target."""
    span = parse_approval_release_span(text)
    return (span.source, span.target) if span else None


def parse_approval_release_span(text: str) -> SourceActionSpan | None:
    """Return the exact source offsets for a whole approval-release task."""
    match = _APPROVAL_RELEASE_RE.fullmatch(bound_task_text(text))
    return _action_span_from_match(match, 0)


def parse_release_precondition(text: str) -> tuple[str, str] | None:
    """Return approval prerequisite and validated release target."""
    match = _RELEASE_PRECONDITION_RE.fullmatch(bound_task_text(text))
    span = _action_span_from_match(match, 0)
    return (span.source, span.target) if span else None


def find_release_precondition_span(text: str) -> SourceActionSpan | None:
    """Return exact offsets for a strict precondition segment."""
    for segment in re.finditer(r"[^;；]+", bound_task_text(text)):
        match = _RELEASE_PRECONDITION_RE.fullmatch(segment.group())
        if span := _action_span_from_match(match, segment.start()):
            return span
    return None


def _action_span_from_match(
    match: re.Match[str] | None, offset: int
) -> SourceActionSpan | None:
    if not match:
        return None
    source_group = "cn_source" if match.group("cn_source") else "en_source"
    target_group = "cn_target" if match.group("cn_target") else "en_target"
    target = match.group(target_group)
    if not is_release_action_text(target, allow_bare=True):
        return None
    return SourceActionSpan(
        source=match.group(source_group),
        target=target,
        source_start=offset + match.start(source_group),
        target_start=offset + match.start(target_group),
    )
