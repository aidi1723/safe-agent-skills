"""Shared hard boundary for every intent text parsing entry point."""

import re


MAX_TASK_SCAN_CHARS = 20_000

_APPROVAL_RELEASE_RE = re.compile(
    r"^\s*(?:"
    r"(?:\u5728\s*)?(?P<cn_source>(?:PR|\u62c9\u53d6\u8bf7\u6c42)\s*"
    r"(?:\u5ba1\u6279\u901a\u8fc7|\u6279\u51c6|\u5ba1\u6838\u901a\u8fc7)\u540e)\s*[,\uff0c]?\s*"
    r"(?P<cn_target>(?:\u53d1\u5e03|\u4e0a\u7ebf|\u63a8\u9001)"
    r"(?:\u66f4\u65b0|\u7248\u672c|\u8f6f\u4ef6\u5305|\u5305|\u4ee3\u7801|\u53d8\u66f4|\u9879\u76ee|\u73b0\u5728|\u7acb\u5373)?)|"
    r"(?P<en_source>after\s+(?:(?:the\s+)?(?:pr|pull\s+request)\s+"
    r"is\s+approved|(?:pr|pull\s+request)\s+approval))\s*[,\uff0c]?\s*"
    r"(?P<en_target>(?:publish|release|push)"
    r"(?:\s+(?:now|update|(?:the\s+)?package|changes?|code|repository))?)"
    r")\s*$",
    re.IGNORECASE,
)


def bound_task_text(text: str) -> str:
    """Return the only source region intent parsers may inspect."""
    return text[:MAX_TASK_SCAN_CHARS]


def parse_approval_release(text: str) -> tuple[str, str] | None:
    """Return canonical approval source and release target for a whole task."""
    match = _APPROVAL_RELEASE_RE.fullmatch(bound_task_text(text))
    if not match:
        return None
    return (
        match.group("cn_source") or match.group("en_source"),
        match.group("cn_target") or match.group("en_target"),
    )
