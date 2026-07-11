"""Immutable contracts for bounded intent span decomposition."""

from dataclasses import dataclass
import re

from .routing_profiles import (
    SCENARIO_PROFILES,
    is_design_governance_composite,
    iter_profile_signal_matches,
)


MAX_CANDIDATE_SIGNALS = 128
MAX_EMITTED_INTENTS = 12


@dataclass(frozen=True)
class ProfileSignalSpan:
    start: int
    end: int
    task_type: str
    signal: str
    score: int


@dataclass(frozen=True)
class SpanDecomposition:
    clauses: tuple[str, ...]
    observed_candidate_count: int
    candidate_signal_limit_exceeded: bool
    intent_limit_exceeded: bool
    classification_suppressed: bool = False


_PROFILE_ORDER = {
    profile["task_type"]: index for index, profile in enumerate(SCENARIO_PROFILES)
}
_CONNECTOR_RE = re.compile(
    r"\s*(?:,|，|、|/|\+|＋|\band\b|\bor\b|\bbut\b|但是|但要|和|或)\s*",
    re.IGNORECASE,
)
_PLUS_CONNECTOR_RE = re.compile(r"\+|＋")
_NEGATION_MARKER_RE = re.compile(
    r"\b(?:do\s+not|don't|never)\b|(?:不需要|不要|不得|禁止|无需|暂不|先不|不做|别)",
    re.IGNORECASE,
)
_PUNCTUATION_BOUNDARY_RE = re.compile(r"[,，;；]")
_COORDINATING_CONTINUATION_RE = re.compile(r"\s*(?:\b(?:or|and)\b|或|和)", re.IGNORECASE)
_ADVERSATIVE_BOUNDARY_RE = re.compile(r"\bbut\b|但是|但要", re.IGNORECASE)
_DESCRIPTIVE_ENUMERATION_RE = re.compile(
    r"\b(?:contains?|mentions?)\b|包含", re.IGNORECASE
)
_DESCRIPTIVE_LIST_PREFIX_RE = re.compile(
    r"^\s*(?:(?:artifacts?|objects?|terms?|file\s+lists?|supported\s+files?|"
    r"file\s+types?|files?)|(?:产物|对象|术语|文件列表|支持的文件|"
    r"支持文件|文件类型|文件))\s*[:：]",
    re.IGNORECASE,
)
_DESCRIPTIVE_RELEASE_ACTION_RE = re.compile(
    r"(?:\bresearch\s+how\s+to\b|\bwrite\s+(?:a\s+)?guide\s+(?:about|to)\b|"
    r"\bhow[-\s]+to\s+guide\b|\bguide\s+(?:about|to)\b)"
    r"[\s\S]{0,80}\b(?:push|publish|release)\b|"
    r"(?:研究|指南|教程)[\s\S]{0,80}(?:推送|发布|上线)",
    re.IGNORECASE,
)


def find_profile_signal_spans(
    clause: str,
    candidate_limit: int = MAX_CANDIDATE_SIGNALS,
) -> tuple[tuple[ProfileSignalSpan, ...], int, bool]:
    """Find distinctive, unambiguous spans using bounded deterministic work."""
    if (
        _is_negated_enumeration(clause)
        or _DESCRIPTIVE_ENUMERATION_RE.search(clause)
        or _DESCRIPTIVE_LIST_PREFIX_RE.search(clause)
    ):
        return (), 0, False

    candidates: list[ProfileSignalSpan] = []
    negation_ranges = _coordinated_negation_ranges(clause)
    observed = 0
    limit_exceeded = False
    for item in iter_profile_signal_matches(clause):
        observed += 1
        if observed > candidate_limit:
            limit_exceeded = True
            break
        span = ProfileSignalSpan(
            start=int(item["start"]),
            end=int(item["end"]),
            task_type=str(item["task_type"]),
            signal=str(item["signal"]),
            score=int(item["score"]),
        )
        if not _offset_is_negated(span.start, negation_ranges):
            candidates.append(span)

    resolved: list[ProfileSignalSpan] = []
    cursor = 0
    while cursor < len(candidates):
        cluster = [candidates[cursor]]
        cluster_end = candidates[cursor].end
        cursor += 1
        while cursor < len(candidates) and candidates[cursor].start < cluster_end:
            cluster.append(candidates[cursor])
            cluster_end = max(cluster_end, candidates[cursor].end)
            cursor += 1
        winner = _resolve_overlap_cluster(cluster)
        if winner is not None:
            resolved.append(winner)
    return tuple(resolved), observed, limit_exceeded


def merge_same_profile_spans(
    spans: tuple[ProfileSignalSpan, ...] | list[ProfileSignalSpan],
) -> tuple[ProfileSignalSpan, ...]:
    """Merge adjacent or overlapping spans when they name the same profile."""
    merged: list[ProfileSignalSpan] = []
    for span in sorted(spans, key=lambda item: (item.start, item.end)):
        if (
            merged
            and merged[-1].task_type == span.task_type
            and span.start <= merged[-1].end
        ):
            previous = merged[-1]
            signals = previous.signal.split(" / ")
            if span.signal not in signals:
                signals.append(span.signal)
            merged[-1] = ProfileSignalSpan(
                start=previous.start,
                end=max(previous.end, span.end),
                task_type=previous.task_type,
                signal=" / ".join(signals),
                score=previous.score + span.score,
            )
        else:
            merged.append(span)
    return tuple(merged)


def split_profile_enumeration(
    clause: str,
    candidate_limit: int = MAX_CANDIDATE_SIGNALS,
) -> SpanDecomposition:
    """Split a profile-backed enumeration while preserving readable source text."""
    if _classification_should_be_suppressed(clause):
        return SpanDecomposition((clause,), 0, False, False, True)

    spans, observed, candidate_limit_exceeded = find_profile_signal_spans(
        clause, candidate_limit
    )
    spans = merge_same_profile_spans(spans)
    if is_design_governance_composite(clause):
        spans = tuple(
            span
            for span in spans
            if not (
                span.task_type == "website_build"
                and span.signal == "design system"
            )
        )
    if _PLUS_CONNECTOR_RE.search(clause) and not _plus_segments_have_profile_evidence(
        clause, spans
    ):
        return SpanDecomposition(
            (clause,), observed, candidate_limit_exceeded, False, True
        )
    if len({span.task_type for span in spans}) < 2:
        positive_prefix = _positive_prefix_before_coordinated_negation(clause)
        return SpanDecomposition(
            (positive_prefix or clause,),
            observed,
            candidate_limit_exceeded,
            False,
        )

    boundaries = list(_CONNECTOR_RE.finditer(clause))
    pieces: list[tuple[int, int, str]] = []
    start = 0
    for connector in boundaries:
        if connector.start() > start:
            pieces.append((start, connector.start(), clause[start : connector.start()].strip()))
        start = connector.end()
    if start < len(clause):
        pieces.append((start, len(clause), clause[start:].strip()))

    negation_ranges = _coordinated_negation_ranges(clause)
    piece_assignments: list[str] = []
    for piece_start, piece_end, text in pieces:
        if not text:
            piece_assignments.append("")
            continue
        piece_spans = [
            span
            for span in spans
            if span.start < piece_end and span.end > piece_start
        ]
        piece_assignments.append(_unique_piece_winner(piece_spans))

    if _PLUS_CONNECTOR_RE.search(clause) and any(
        text
        and not piece_assignments[piece_index]
        and not _range_is_negated(piece_start, piece_end, negation_ranges)
        for piece_index, (piece_start, piece_end, text) in enumerate(pieces)
    ):
        return SpanDecomposition(
            (clause,), observed, candidate_limit_exceeded, False, True
        )

    for piece_index, (piece_start, piece_end, _) in enumerate(pieces):
        if piece_assignments[piece_index] or _range_is_negated(
            piece_start, piece_end, negation_ranges
        ):
            continue
        preceding = next(
            (
                piece_assignments[index]
                for index in range(piece_index - 1, -1, -1)
                if piece_assignments[index]
            ),
            "",
        )
        following = next(
            (
                piece_assignments[index]
                for index in range(piece_index + 1, len(pieces))
                if piece_assignments[index]
            ),
            "",
        )
        piece_assignments[piece_index] = preceding or following

    assigned = [
        (piece_index, piece_start, piece_end, text, piece_assignments[piece_index])
        for piece_index, (piece_start, piece_end, text) in enumerate(pieces)
        if piece_assignments[piece_index]
    ]

    if len({item[4] for item in assigned}) < 2:
        return SpanDecomposition((clause,), observed, candidate_limit_exceeded, False)

    local_groups: list[tuple[int, int, int, str, str]] = []
    for piece_index, piece_start, piece_end, text, task_type in assigned:
        if (
            local_groups
            and local_groups[-1][4] == task_type
            and local_groups[-1][0] == piece_index - 1
        ):
            _, group_start, _, _, _ = local_groups[-1]
            local_groups[-1] = (
                piece_index,
                group_start,
                piece_end,
                clause[group_start:piece_end].strip(),
                task_type,
            )
        else:
            local_groups.append((piece_index, piece_start, piece_end, text, task_type))

    task_order: list[str] = []
    summaries: dict[str, list[str]] = {}
    for _, _, _, text, task_type in local_groups:
        if task_type not in summaries:
            task_order.append(task_type)
            summaries[task_type] = []
        summaries[task_type].append(text)

    clauses = tuple("; ".join(summaries[task_type]) for task_type in task_order)
    intent_limit = len(clauses) > MAX_EMITTED_INTENTS
    return SpanDecomposition(
        clauses=clauses[:MAX_EMITTED_INTENTS],
        observed_candidate_count=observed,
        candidate_signal_limit_exceeded=candidate_limit_exceeded,
        intent_limit_exceeded=intent_limit,
    )


def _classification_should_be_suppressed(clause: str) -> bool:
    return bool(
        _DESCRIPTIVE_ENUMERATION_RE.search(clause)
        or _DESCRIPTIVE_LIST_PREFIX_RE.search(clause)
        or _DESCRIPTIVE_RELEASE_ACTION_RE.search(clause)
    )


def _plus_segments_have_profile_evidence(
    clause: str, spans: tuple[ProfileSignalSpan, ...]
) -> bool:
    start = 0
    pieces: list[tuple[int, int]] = []
    for connector in _PLUS_CONNECTOR_RE.finditer(clause):
        pieces.append((start, connector.start()))
        start = connector.end()
    pieces.append((start, len(clause)))
    return all(
        not clause[piece_start:piece_end].strip()
        or any(
            span.start < piece_end and span.end > piece_start
            for span in spans
        )
        for piece_start, piece_end in pieces
    )


def _resolve_overlap_cluster(cluster: list[ProfileSignalSpan]) -> ProfileSignalSpan | None:
    best_score = max(span.score for span in cluster)
    scored = [span for span in cluster if span.score == best_score]
    best_length = max(span.end - span.start for span in scored)
    finalists = [span for span in scored if span.end - span.start == best_length]
    if len({span.task_type for span in finalists}) != 1:
        return None
    return min(
        finalists,
        key=lambda span: (_PROFILE_ORDER.get(span.task_type, len(_PROFILE_ORDER)), span.start),
    )


def _unique_piece_winner(spans: list[ProfileSignalSpan]) -> str:
    if not spans:
        return ""
    scores: dict[str, int] = {}
    longest: dict[str, int] = {}
    for span in spans:
        scores[span.task_type] = scores.get(span.task_type, 0) + span.score
        longest[span.task_type] = max(
            longest.get(span.task_type, 0), span.end - span.start
        )
    ranked = sorted(
        scores,
        key=lambda task_type: (
            -scores[task_type],
            -longest[task_type],
            _PROFILE_ORDER.get(task_type, len(_PROFILE_ORDER)),
        ),
    )
    if len(ranked) > 1 and (
        scores[ranked[0]], longest[ranked[0]]
    ) == (scores[ranked[1]], longest[ranked[1]]):
        return ""
    return ranked[0]


def _is_negated_enumeration(clause: str) -> bool:
    stripped = clause.lstrip()
    return bool(
        re.match(r"(?:do\s+not|don't|never)\b", stripped, re.IGNORECASE)
        or re.match(r"(?:不需要|不要|不得|禁止|无需|暂不|先不|不做|别)", stripped)
    )


def _coordinated_negation_ranges(clause: str) -> tuple[tuple[int, int], ...]:
    ranges: list[tuple[int, int]] = []
    for negation in _NEGATION_MARKER_RE.finditer(clause):
        end = len(clause)
        adversative = _ADVERSATIVE_BOUNDARY_RE.search(clause, negation.end())
        if adversative is not None:
            end = adversative.start()
        for boundary in _PUNCTUATION_BOUNDARY_RE.finditer(
            clause, negation.end(), end
        ):
            if boundary.group() in {";", "；"}:
                end = boundary.start()
                break
            following = clause[boundary.end() : end]
            if _COORDINATING_CONTINUATION_RE.match(following):
                continue
            end = boundary.start()
            break
        ranges.append((negation.start(), end))
    return tuple(ranges)


def _offset_is_negated(start: int, ranges: tuple[tuple[int, int], ...]) -> bool:
    return any(range_start <= start < range_end for range_start, range_end in ranges)


def _range_is_negated(
    start: int, end: int, ranges: tuple[tuple[int, int], ...]
) -> bool:
    return any(start < range_end and end > range_start for range_start, range_end in ranges)


def _positive_prefix_before_coordinated_negation(clause: str) -> str:
    negation = _NEGATION_MARKER_RE.search(clause)
    if negation is None or negation.start() == 0:
        return ""
    boundaries = [
        boundary
        for boundary in _PUNCTUATION_BOUNDARY_RE.finditer(
            clause[: negation.start()]
        )
    ]
    if not boundaries:
        return ""
    return clause[: boundaries[-1].start()].strip(" \t\n,，。")
