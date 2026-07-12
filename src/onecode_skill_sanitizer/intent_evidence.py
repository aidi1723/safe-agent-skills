"""Internal, nonserialized evidence produced by bounded intent span analysis."""

from __future__ import annotations

from dataclasses import dataclass, replace
import hashlib
import json
import re
from typing import Any

from .intent_source import (
    bound_task_text,
    is_release_action_text,
    parse_approval_release,
    source_contains_release_action,
)


EVIDENCE_CONTEXTS = frozenset({"action", "descriptive", "how_to", "ambiguous"})
EVIDENCE_POLARITIES = frozenset({"positive", "negative", "mixed"})
RELEASE_MODES = frozenset({"none", "readiness", "action"})
RELATION_MODES = frozenset(
    {"single", "enumeration", "parallel", "explicit_sequence"}
)
GATE_MODES = frozenset({"none", "completion", "verification"})
MAX_MATCHED_SCORE = 512
RELEASE_READINESS_PATTERNS = (
    ("发布清单", re.compile(r"发布清单")),
    (
        "release checklist",
        re.compile(r"(?<![a-z0-9])release[\s-]+checklist(?![a-z0-9])", re.I),
    ),
    (
        "release packet",
        re.compile(r"(?<![a-z0-9])release[\s-]+packet(?![a-z0-9])", re.I),
    ),
    (
        "release readiness",
        re.compile(r"(?<![a-z0-9])release[\s-]+readiness(?![a-z0-9])", re.I),
    ),
)
RELEASE_READINESS_SIGNALS = frozenset(
    signal for signal, _ in RELEASE_READINESS_PATTERNS
)
RELEASE_READINESS_EVIDENCE_SIGNALS = RELEASE_READINESS_SIGNALS | {"release"}
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
_READINESS_SEGMENT_BOUNDARY_RE = re.compile(
    r"[;；\n。]|(?<=[.!?])\s+|"
    r",\s*(?:then|but)\s+|，\s*(?:然后|再|但(?:是|要)?|不过)\s*",
    re.IGNORECASE,
)
_NON_REQUEST_RELEASE_READINESS_RE = re.compile(
    r"\b(?:hypothetical(?:ly)?|mentions?|stale|unauthorized)\b|"
    r"\bnot\s+(?:authorized|a\s+work\s+order)\b|"
    r"\bwithout\s+(?:publishing|releasing)\b|"
    r"(?:过期|未授权|未经授权|不是(?:工作|任务)指令)",
    re.IGNORECASE,
)
_NEGATED_RELEASE_READINESS_RE = re.compile(
    r"\b(?:must\s+not|do\s+not|don't|never)\b[\s\S]{0,80}"
    r"\b(?:prepare|release|claim|publish|create|assemble|draft|produce)\b|"
    r"\brelease[\s-]+(?:readiness|checklist|packet)\b[\s\S]{0,40}"
    r"\b(?:is\s+not|isn't|was\s+not|wasn't)\s+"
    r"(?:approved|authorized|ready|valid)\b|"
    r"(?:不要|不得|禁止|不可|无需)[\s\S]{0,80}(?:准备|发布|声称|生成|创建)",
    re.IGNORECASE,
)
_READINESS_LABEL_RE = re.compile(
    r"^\s*(?:(?:example|label|terms?|navigation|headings?|menu)\s*[:：]|"
    r"(?:[-*+]|\d+[.)、])\s+)",
    re.IGNORECASE,
)
_MARKUP_HEADING_RE = re.compile(
    r"^\s*(?:#{1,6}\s+|<h[1-6]\b[^>]*>)", re.IGNORECASE
)
_READINESS_FILENAME_SUFFIX_RE = re.compile(
    r"\.(?:md|markdown|json|ya?ml|toml|txt|html?|xml|csv)\b", re.IGNORECASE
)
_QUOTED_TEXT_PATTERNS = (
    re.compile(r'"[^"\n]*"'),
    re.compile(r"“[^”\n]*”"),
    re.compile(r"‘[^’\n]*’"),
    re.compile(r"`[^`\n]*`"),
)
_NON_SOFTWARE_RELEASE_RE = re.compile(
    r"\b(?:talent|model|content)\s+release[\s-]+packet\b|"
    r"\b(?:photo(?:graphy)?|photo\s+shoot|photographer|campaign|performer|actor)\b",
    re.IGNORECASE,
)
_SOFTWARE_RELEASE_ANCHOR_RE = re.compile(
    r"\b(?:repository|repo|package|cli|codebase|software|project|maintainer)\b|"
    r"(?:代码库|仓库|软件包|维护者|项目)",
    re.IGNORECASE,
)
_RELEASE_PACKET_REQUEST_RE = re.compile(
    r"\b(?:prepare|assemble|create|build|draft|produce)\b[\s\S]{0,120}"
    r"\brelease\s+packet\b|"
    r"\b(?:maintainer[- ]ready|repository|repo)\s+release\s+packet\b|"
    r"\brelease\s+packet\b[\s\S]{0,60}"
    r"\b(?:preparation|readiness|go/no-go)\b",
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
    provenance: str = ""
    gate_mode: str = "none"


def bind_intent_evidence(
    evidence: tuple[IntentEvidence, ...], source: str
) -> tuple[IntentEvidence, ...]:
    """Bind generated evidence to the exact bounded source and field values."""
    source = bound_task_text(source)
    return tuple(
        replace(item, provenance=_evidence_provenance(item, source))
        for item in evidence
    )


def validate_intent_evidence(
    evidence: Any,
    expected_task_types: tuple[str, ...],
    evidence_source: str = "",
) -> list[str]:
    """Validate internal evidence without accepting lookalike records."""
    if not isinstance(evidence, tuple):
        return ["intent evidence must be a tuple of IntentEvidence records"]
    if not evidence:
        return []
    if len(evidence) != len(expected_task_types):
        return ["intent evidence count must match intent count"]
    errors: list[str] = []
    source_valid = (
        type(evidence_source) is str and bool(evidence_source.strip())
    )
    if source_valid:
        evidence_source = bound_task_text(evidence_source)
    else:
        errors.append(
            "intent evidence source must be an exact nonblank string"
        )
        evidence_source = ""
    for index, (item, task_type) in enumerate(
        zip(evidence, expected_task_types, strict=True), start=1
    ):
        if type(item) is not IntentEvidence:
            errors.append(f"intent evidence {index} must be an IntentEvidence")
            continue
        if item.task_type != task_type:
            errors.append(f"intent evidence {index} task type does not match intent")
        context_valid = isinstance(item.context, str) and item.context in EVIDENCE_CONTEXTS
        polarity_valid = (
            isinstance(item.polarity, str)
            and item.polarity in EVIDENCE_POLARITIES
        )
        release_mode_valid = (
            isinstance(item.release_mode, str)
            and item.release_mode in RELEASE_MODES
        )
        relation_mode_valid = (
            isinstance(item.relation_mode, str)
            and item.relation_mode in RELATION_MODES
        )
        gate_mode_valid = (
            isinstance(item.gate_mode, str) and item.gate_mode in GATE_MODES
        )
        provenance_valid = (
            type(item.provenance) is str and bool(item.provenance.strip())
        )
        signals_valid = isinstance(item.matched_signals, tuple) and all(
            isinstance(signal, str) and bool(signal)
            for signal in item.matched_signals
        )
        score_valid = (
            not isinstance(item.matched_score, bool)
            and isinstance(item.matched_score, int)
            and 0 <= item.matched_score <= MAX_MATCHED_SCORE
        )
        if not context_valid:
            errors.append(f"intent evidence {index} has invalid context")
        if not polarity_valid:
            errors.append(f"intent evidence {index} has invalid polarity")
        if not release_mode_valid:
            errors.append(f"intent evidence {index} has invalid release mode")
        if not relation_mode_valid:
            errors.append(f"intent evidence {index} has invalid relation mode")
        if not gate_mode_valid:
            errors.append(f"intent evidence {index} has invalid gate mode")
        if not provenance_valid:
            errors.append(f"intent evidence {index} has invalid provenance")
        if not signals_valid:
            errors.append(f"intent evidence {index} has invalid matched signals")
        if not score_valid:
            errors.append(f"intent evidence {index} has invalid matched score")
        fields_valid = all(
            (
                isinstance(item.task_type, str),
                context_valid,
                polarity_valid,
                release_mode_valid,
                relation_mode_valid,
                gate_mode_valid,
                signals_valid,
                score_valid,
            )
        )
        if fields_valid:
            if (
                source_valid
                and provenance_valid
                and item.provenance != _evidence_provenance(item, evidence_source)
            ):
                errors.append(
                    f"intent evidence {index} does not match its source binding"
                )
            errors.extend(_semantic_errors(item, evidence_source, index))
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
    source = bound_task_text(source)
    normalized = {signal.casefold() for signal in matched_signals}
    if not normalized & RELEASE_READINESS_EVIDENCE_SIGNALS:
        return False
    return any(
        _readiness_occurrence_is_request(source, signal, match.start(), match.end())
        for signal, pattern in RELEASE_READINESS_PATTERNS
        for match in pattern.finditer(source)
    )


def _readiness_occurrence_is_request(
    source: str, signal: str, start: int, end: int
) -> bool:
    segment, local_start, local_end = _local_readiness_segment(
        source, start, end
    )
    if (
        _occurrence_is_quoted(segment, local_start, local_end)
        or _MARKUP_HEADING_RE.search(segment)
        or _READINESS_LABEL_RE.search(segment)
        or _READINESS_FILENAME_SUFFIX_RE.match(segment[local_end:])
        or _NON_REQUEST_RELEASE_READINESS_RE.search(segment)
        or _NEGATED_RELEASE_READINESS_RE.search(segment)
    ):
        return False
    if (
        _NON_SOFTWARE_RELEASE_RE.search(segment)
        and not _SOFTWARE_RELEASE_ANCHOR_RE.search(segment)
    ):
        return False
    if signal == "release packet":
        return _RELEASE_PACKET_REQUEST_RE.search(segment) is not None
    return True


def _local_readiness_segment(
    source: str, start: int, end: int
) -> tuple[str, int, int]:
    segment_start = 0
    segment_end = len(source)
    for boundary in _READINESS_SEGMENT_BOUNDARY_RE.finditer(source):
        if boundary.end() <= start:
            segment_start = boundary.end()
        elif boundary.start() >= end:
            segment_end = boundary.start()
            break
    return (
        source[segment_start:segment_end],
        start - segment_start,
        end - segment_start,
    )


def _occurrence_is_quoted(segment: str, start: int, end: int) -> bool:
    return any(
        match.start() <= start and end <= match.end()
        for pattern in _QUOTED_TEXT_PATTERNS
        for match in pattern.finditer(segment)
    )


def source_supports_release_action(
    source: str, matched_signals: tuple[str, ...] = ()
) -> bool:
    source = bound_task_text(source)
    if parse_approval_release(source) is not None or is_release_action_text(
        source, allow_bare=True
    ):
        return True
    normalized = {signal.casefold() for signal in matched_signals}
    return bool(
        source_contains_release_action(source)
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
    source = bound_task_text(source)
    if signal.isascii():
        return re.search(
            rf"(?<![a-z0-9]){re.escape(signal)}(?![a-z0-9])",
            source.casefold(),
        ) is not None
    return signal in source.casefold()


def _evidence_provenance(item: IntentEvidence, source: str) -> str:
    source = bound_task_text(source)
    payload = {
        "source": source,
        "task_type": item.task_type,
        "context": item.context,
        "polarity": item.polarity,
        "release_mode": item.release_mode,
        "relation_mode": item.relation_mode,
        "matched_signals": item.matched_signals,
        "matched_score": item.matched_score,
        "gate_mode": item.gate_mode,
    }
    encoded = json.dumps(
        payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()
