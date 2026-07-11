"""Internal, nonserialized evidence produced by bounded intent span analysis."""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any


EVIDENCE_CONTEXTS = frozenset({"action", "descriptive", "how_to", "ambiguous"})
EVIDENCE_POLARITIES = frozenset({"positive", "negative", "mixed"})
RELEASE_MODES = frozenset({"none", "readiness", "action"})
RELATION_MODES = frozenset(
    {"single", "enumeration", "parallel", "explicit_sequence"}
)
RELEASE_READINESS_SIGNALS = frozenset({"发布清单", "release checklist"})
RELEASE_ACTION_SIGNALS = frozenset(
    {
        "open source",
        "publish repo",
        "public repository",
        "开源",
        "发布仓库",
        "公开仓库",
        "推送 github",
        "推送到 github",
        "推送代码到 github",
        "push to github",
        "push changes to github",
        "push the repository to github",
        "发布更新",
        "publish update",
    }
)
_RELEASE_ACTION_CONTEXT_RE = re.compile(
    r"(?:验证(?:通过)?|测试通过|完成|批准|审批通过|审核通过)后(?:再)?"
    r"(?:发布|上线|推送)|"
    r"(?:发布|上线|推送)(?:更新|结果|版本|新版本|软件包|包|项目|网站|应用|代码|变更|到\S+)|"
    r"推送(?:代码)?(?:到)?\s*github|"
    r"\b(?:publish|release)\b\s+(?:the\s+|an?\s+)?"
    r"(?:(?:verified|approved)\s+)?"
    r"(?:update|results?|package|version|project|website|app|code|changes?)\b|"
    r"\bpush\s+(?:changes\s+to\s+github|the\s+repository(?:\s+to\s+github)?|"
    r"to\s+github)\b|\bopen[-\s]+source\s+release\b|^\s*release\s*$",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class IntentEvidence:
    """Profile and relation evidence aligned by index with an internal intent."""

    task_type: str
    context: str
    polarity: str
    release_mode: str
    relation_mode: str
    matched_signals: tuple[str, ...]
    matched_score: int


def validate_intent_evidence(
    evidence: Any,
    expected_task_types: tuple[str, ...],
    source_summaries: tuple[str, ...] = (),
) -> list[str]:
    """Validate internal evidence without accepting lookalike records."""
    if not isinstance(evidence, tuple):
        return ["intent evidence must be a tuple of IntentEvidence records"]
    if not evidence:
        return []
    if len(evidence) != len(expected_task_types):
        return ["intent evidence count must match intent count"]
    if source_summaries and len(source_summaries) != len(expected_task_types):
        return ["intent evidence source count must match intent count"]

    errors: list[str] = []
    for index, (item, task_type) in enumerate(
        zip(evidence, expected_task_types, strict=True), start=1
    ):
        if type(item) is not IntentEvidence:
            errors.append(f"intent evidence {index} must be an IntentEvidence")
            continue
        if item.task_type != task_type:
            errors.append(f"intent evidence {index} task type does not match intent")
        if item.context not in EVIDENCE_CONTEXTS:
            errors.append(f"intent evidence {index} has invalid context")
        if item.polarity not in EVIDENCE_POLARITIES:
            errors.append(f"intent evidence {index} has invalid polarity")
        if item.release_mode not in RELEASE_MODES:
            errors.append(f"intent evidence {index} has invalid release mode")
        if item.relation_mode not in RELATION_MODES:
            errors.append(f"intent evidence {index} has invalid relation mode")
        if not isinstance(item.matched_signals, tuple) or any(
            not isinstance(signal, str) or not signal
            for signal in item.matched_signals
        ):
            errors.append(f"intent evidence {index} has invalid matched signals")
        if (
            isinstance(item.matched_score, bool)
            or not isinstance(item.matched_score, int)
            or item.matched_score < 0
        ):
            errors.append(f"intent evidence {index} has invalid matched score")
        if type(item) is IntentEvidence:
            summary = source_summaries[index - 1] if source_summaries else ""
            errors.extend(_semantic_errors(item, summary, index))
    return errors


def release_signals(evidence: IntentEvidence) -> tuple[str, ...]:
    """Expand merged span labels into normalized source signals."""
    return tuple(
        signal.strip().casefold()
        for combined in evidence.matched_signals
        for signal in combined.split(" / ")
        if signal.strip()
    )


def source_supports_release_readiness(
    source: str, matched_signals: tuple[str, ...]
) -> bool:
    normalized = tuple(signal.casefold() for signal in matched_signals)
    return bool(
        set(normalized) & RELEASE_READINESS_SIGNALS
        and any(
            signal in RELEASE_READINESS_SIGNALS
            and _signal_in_source(source, signal)
            for signal in normalized
        )
    )


def source_supports_release_action(
    source: str, matched_signals: tuple[str, ...] = ()
) -> bool:
    normalized = {signal.casefold() for signal in matched_signals}
    return bool(
        _RELEASE_ACTION_CONTEXT_RE.search(source)
        or any(
            signal in RELEASE_ACTION_SIGNALS
            and _signal_in_source(source, signal)
            for signal in normalized
        )
    )


def _semantic_errors(
    item: IntentEvidence, source: str, index: int
) -> list[str]:
    errors: list[str] = []
    is_release = item.task_type == "open_source_release"
    if not is_release and item.release_mode != "none":
        errors.append(
            f"intent evidence {index} non-release intent cannot carry release mode"
        )
    if is_release and item.release_mode == "none":
        errors.append(
            f"intent evidence {index} release intent must declare release mode"
        )

    suppressed = item.context in {"descriptive", "how_to", "ambiguous"}
    if suppressed and (
        item.task_type != "general"
        or item.release_mode != "none"
        or item.matched_signals
        or item.matched_score != 0
    ):
        errors.append(
            f"intent evidence {index} suppressed general evidence must have empty matches"
        )

    signals = release_signals(item)
    if item.release_mode == "readiness" and not source_supports_release_readiness(
        source, signals
    ):
        errors.append(
            f"intent evidence {index} readiness evidence is not supported by source"
        )
    if item.release_mode == "readiness" and item.polarity not in {
        "positive",
        "mixed",
    }:
        errors.append(
            f"intent evidence {index} readiness evidence requires positive context"
        )
    if item.release_mode == "action" and (
        item.context != "action"
        or item.polarity not in {"positive", "mixed"}
        or not source_supports_release_action(source, signals)
    ):
        errors.append(
            f"intent evidence {index} release action evidence requires action context"
        )
    return errors


def _signal_in_source(source: str, signal: str) -> bool:
    if signal.isascii():
        return re.search(
            rf"(?<![a-z0-9]){re.escape(signal)}(?![a-z0-9])",
            source.casefold(),
        ) is not None
    return signal in source.casefold()
