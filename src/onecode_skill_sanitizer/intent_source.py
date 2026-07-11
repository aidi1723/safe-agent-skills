"""Shared hard boundary and source predicates for intent parsing."""

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
)
_RELEASE_ACTION_RE = re.compile(_RELEASE_ACTION_PHRASE, re.IGNORECASE)
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
    """Find a release action inside a bounded task source."""
    return _RELEASE_ACTION_RE.search(bound_task_text(text)) is not None


def parse_approval_release(text: str) -> tuple[str, str] | None:
    """Return canonical approval source and validated release target."""
    match = _APPROVAL_RELEASE_RE.fullmatch(bound_task_text(text))
    if not match:
        return None
    result = (
        match.group("cn_source") or match.group("en_source"),
        match.group("cn_target") or match.group("en_target"),
    )
    return result if is_release_action_text(result[1], allow_bare=True) else None
