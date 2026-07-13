"""Immutable contracts for bounded intent span decomposition."""

from dataclasses import dataclass
import re

from .intent_evidence import (
    IntentEvidence,
    source_supports_release_action,
)
from .intent_source import bound_task_text
from .release_propositions import (
    ReleaseReadinessProposition,
    parse_release_readiness_propositions,
)
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
class NonActionSourceRange:
    start: int
    end: int
    context: str


@dataclass(frozen=True)
class SpanDecomposition:
    clauses: tuple[str, ...]
    observed_candidate_count: int
    candidate_signal_limit_exceeded: bool
    intent_limit_exceeded: bool
    intent_evidence: tuple[IntentEvidence, ...] = ()


_PROFILE_ORDER = {
    profile["task_type"]: index for index, profile in enumerate(SCENARIO_PROFILES)
}
_CONNECTOR_RE = re.compile(
    r"\s*(?:,|，|、|/|\+|＋|\band\b|\bor\b|\bbut\b|但是|但要|和|或)\s*",
    re.IGNORECASE,
)
_PLUS_CONNECTOR_RE = re.compile(r"\+|＋")
_NEGATION_MARKER_RE = re.compile(
    r"\b(?:(?:do|must|should)\s+not|(?:do|must|should)n['’]t|never)\b|"
    r"(?:不需要|不要|不得|禁止|无需|暂不|先不|不做|别)",
    re.IGNORECASE,
)
_PUNCTUATION_BOUNDARY_RE = re.compile(r"[,，;；]")
_COORDINATING_CONTINUATION_RE = re.compile(r"\s*(?:\b(?:or|and)\b|或|和)", re.IGNORECASE)
_ADVERSATIVE_BOUNDARY_RE = re.compile(r"\bbut\b|但是|但要", re.IGNORECASE)
_CURRENT_ACTION_CONTINUATION_RE = re.compile(
    r"[,，]\s*(?:and\s+)?(?:(?:please|kindly)\s+)?"
    r"(?:complete|review|audit|check|verify|analyze|assess|prepare|draft|"
    r"build|design|convert|classify|define|plan|write|create|implement|fix|"
    r"research|investigate|evaluate|publish|release)\b|"
    r"[,，]\s*(?:请(?:你|帮忙)?|帮我|麻烦(?:你)?|)"
    r"(?:审查|审计|检查|验证|分析|评估|准备|起草|构建|设计|转换|分类|定义|"
    r"规划|撰写|创建|实施|修复|调研|定位)",
    re.IGNORECASE,
)
_POSITIVE_AFTER_NEGATION_RE = re.compile(r"[,，]\s*(?:只|仅|改为|而要)")
_DESCRIPTIVE_ENUMERATION_RE = re.compile(
    r"\b(?:contains?|mentions?)\b|包含", re.IGNORECASE
)
_DESCRIPTIVE_LIST_PREFIX_RE = re.compile(
    r"^\s*(?:(?:artifacts?|objects?|terms?|file\s+lists?|supported\s+files?|"
    r"file\s+types?|files?)|(?:产物|对象|术语|文件列表|支持的文件|"
    r"支持文件|文件类型|文件))\s*[:：]",
    re.IGNORECASE,
)
_NON_ACTION_STRUCTURAL_PREFIX_RE = re.compile(
    r"^\s*(?:"
    r"(?:inventory(?:\s+(?:entries|only))?|headings?\s+only|"
    r"quoted\s+(?:text|example)|future\s+(?:roadmap|hypothesis)|"
    r"(?:file|folder|archive)\s+(?:names?|labels?)|navigation\s+labels?)\s*[:：]|"
    r"(?:这些只是|仅是)(?:文件夹名|文件名|术语|目录|标题|引文)\s*[:：]?"
    r")",
    re.IGNORECASE,
)
_NON_ACTION_AUTHORITY_RE = re.compile(
    r"\b(?:does\s+not|do\s+not|did\s+not|not|no|without|neither|nor)\b"
    r"[^\n。！？;；]{0,64}\b(?:authorize|authorise|authorization|authority|"
    r"approval|permission|request(?:ed|ing)?|instruction|implementation|"
    r"work|action|task)\b|"
    r"(?:不|未|无|别|不得|禁止|无需|暂不|先不|不做)"
    r"[^\n。！？;；]{0,24}(?:执行|实施|授权|权限|操作|启动)|"
    r"(?:当前|本轮|本次|这次|今日)(?:[^\n。！？;；]{0,16})"
    r"(?:不|未|无|别|不得|禁止|无需|暂不|先不|不做)"
    r"[^\n。！？;；]{0,24}(?:设计|构建|审计|发布|上线|转换|搜索|分析|"
    r"生成|处理|审查|复核|规划)",
    re.IGNORECASE,
)
_HISTORICAL_NON_ACTION_RE = re.compile(
    r"\b(?:already|previously|retired|stale|expired|closed|archived|"
    r"withdrawn|abandoned)\b[^\n。！？;；]{0,64}\b(?:completed|closed|"
    r"archived|retired|expired|withdrawn|abandoned|context|brief|ticket|"
    r"plan|project|task|scope)\b|"
    r"(?:已完成|已归档|已撤回|已作废|已关闭|过期|归档|撤回|作废)"
    r"[^\n。！？;；]{0,48}(?:任务|项目|工单|计划|内容|指令|工作|范围|简报)?",
    re.IGNORECASE,
)
_OTHER_OWNER_NON_ACTION_RE = re.compile(
    r"\b(?:another|separate|external)\s+(?:team|group|owner|agency|"
    r"vendor|supplier|studio|distributor)\b[^\n。！？;；]{0,64}"
    r"\b(?:owns?|owned|assigned|responsible)\b|"
    r"(?:另一个团队|其他团队|外部团队|运营组|设计组)[^\n。！？;；]{0,32}"
    r"(?:负责|已关闭|不属于)",
    re.IGNORECASE,
)
_DESCRIPTIVE_RELEASE_ACTION_RE = re.compile(
    r"(?:\b(?:research\s+|learn\s+)?how\s+to\b|"
    r"\bwrite\s+(?:a\s+)?guide\s+(?:about|to)\b|"
    r"\bhow[-\s]+to\s+guide\b|\bguide\s+(?:about|to)\b)"
    r"[\s\S]{0,80}\b(?:push|publish|release)\b|"
    r"(?:研究|指南|教程)[\s\S]{0,80}(?:推送|发布|上线)",
    re.IGNORECASE,
)
_ENUMERATION_MARKER_RE = re.compile(r",|，|、|\+|＋|\band\b|和|或", re.IGNORECASE)
_EXPLICIT_SEQUENCE_RE = re.compile(
    r"\b(?:then|after|before)\b|然后|先[\s\S]*再|"
    r"\b(?:workstream|workflow|execution)\s+order\b|"
    r"\bin\s+(?:this\s+)?order\b|"
    r"\b(?:ordered\s+)?(?:workflow\s+)?steps?\s*:|"
    r"(?:工作流|流程|执行)顺序|步骤\s*[:：]",
    re.IGNORECASE,
)
_PARALLEL_CONTEXT_RE = re.compile(r"\bin\s+parallel\b|\bparallel\b|同时|并行", re.IGNORECASE)
_RELEASE_PRECONDITION_RE = re.compile(
    r"(?:发布|上线|推送)前|推送(?:到)?\s*github\s*前|"
    r"\bbefore\s+(?:publishing|releasing|pushing|publish|release|push)\b",
    re.IGNORECASE,
)
_NON_ACTION_RELEASE_TERM_RE = re.compile(
    r"推送(?:到)?\s*github\s*前|(?:发布|上线|推送)前|"
    r"\brelease\s+notes\b|\bpublishable\b|"
    r"\bbefore\s+(?:publishing|releasing|pushing|publish|release|push)\b",
    re.IGNORECASE,
)
_WEBSITE_PUBLISH_PRECONDITION_RE = re.compile(
    r"^\s*before\s+publishing\s+"
    r"(?:(?:the|a|an|our|my|your|their|its)\s+)?"
    r"(?:(?:official|product|company)\s+)?(?:website|site)\s*$",
    re.IGNORECASE,
)


def find_profile_signal_spans(
    clause: str,
    candidate_limit: int = MAX_CANDIDATE_SIGNALS,
    release_propositions: tuple[ReleaseReadinessProposition, ...] | None = None,
    source_offset: int = 0,
) -> tuple[tuple[ProfileSignalSpan, ...], int, bool]:
    """Find distinctive, unambiguous spans using bounded deterministic work."""
    clause = bound_task_text(clause)
    if release_propositions is None:
        release_propositions = parse_release_readiness_propositions(clause)
        source_offset = 0
    candidates: list[ProfileSignalSpan] = []
    non_action_ranges = _non_action_source_ranges(clause)
    negation_ranges = (
        ((0, len(clause)),)
        if _is_negated_enumeration(clause)
        and _ADVERSATIVE_BOUNDARY_RE.search(clause) is None
        and _POSITIVE_AFTER_NEGATION_RE.search(clause) is None
        else _coordinated_negation_ranges(clause)
    )
    positive_readiness_ranges = tuple(
        (item.start - source_offset, item.end - source_offset)
        for item in release_propositions
        if item.polarity == "positive" and item.discourse_role == "request"
    )
    non_action_release_ranges = tuple(
        (match.start(), match.end())
        for match in _NON_ACTION_RELEASE_TERM_RE.finditer(clause)
    )
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
        negated = _offset_is_negated(span.start, negation_ranges) and not (
            span.task_type == "open_source_release"
            and _range_overlaps(
                span.start, span.end, positive_readiness_ranges
            )
        )
        if not negated and not (
            span.task_type in {"website_build", "open_source_release"}
            and _range_overlaps(span.start, span.end, non_action_release_ranges)
        ) and not _range_overlaps(
            span.start,
            span.end,
            tuple((item.start, item.end) for item in non_action_ranges),
        ):
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
    release_propositions: tuple[ReleaseReadinessProposition, ...] | None = None,
    source_offset: int = 0,
) -> SpanDecomposition:
    """Split a profile-backed enumeration while preserving readable source text."""
    clause = bound_task_text(clause)
    if release_propositions is None:
        release_propositions = parse_release_readiness_propositions(clause)
        source_offset = 0
    spans, observed, candidate_limit_exceeded = find_profile_signal_spans(
        clause,
        candidate_limit,
        release_propositions,
        source_offset,
    )
    spans = merge_same_profile_spans(spans)
    non_action_ranges = _non_action_source_ranges(clause)
    descriptive_release_ranges = _descriptive_release_ranges(clause)
    positive_readiness_ranges = tuple(
        (item.start - source_offset, item.end - source_offset)
        for item in release_propositions
        if item.polarity == "positive" and item.discourse_role == "request"
    )
    if descriptive_release_ranges:
        spans = tuple(
            span
            for span in spans
            if not (
                span.task_type == "open_source_release"
                and _range_overlaps(
                    span.start, span.end, descriptive_release_ranges
                )
                and not _range_overlaps(
                    span.start, span.end, positive_readiness_ranges
                )
            )
        )
    relation_mode = relation_mode_for_text(clause)
    polarity = _clause_polarity(clause, spans)
    if is_design_governance_composite(clause):
        spans = tuple(
            span
            for span in spans
            if not (
                span.task_type == "website_build"
                and span.signal == "design system"
            )
        )
    if _is_governance_enumeration(clause, spans):
        return _suppressed_decomposition(
            clause,
            observed,
            candidate_limit_exceeded,
            "descriptive",
            polarity,
            relation_mode,
        )
    if non_action_ranges and not spans:
        return _suppressed_decomposition(
            clause,
            observed,
            candidate_limit_exceeded,
            non_action_ranges[0].context,
            polarity,
            relation_mode,
        )
    if descriptive_release_ranges and not spans:
        return _suppressed_decomposition(
            clause,
            observed,
            candidate_limit_exceeded,
            "how_to",
            polarity,
            relation_mode,
        )
    if _PLUS_CONNECTOR_RE.search(clause) and not _plus_segments_have_profile_evidence(
        clause, spans
    ):
        return _suppressed_decomposition(
            clause,
            observed,
            candidate_limit_exceeded,
            "ambiguous",
            polarity,
            relation_mode,
        )
    if len({span.task_type for span in spans}) < 2:
        positive_prefix = _positive_prefix_before_coordinated_negation(clause)
        summary = positive_prefix or clause
        evidence = _single_clause_evidence(
            summary,
            spans,
            polarity,
            relation_mode,
            release_propositions,
        )
        return SpanDecomposition(
            (summary,),
            observed,
            candidate_limit_exceeded,
            False,
            (evidence,),
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
        return _suppressed_decomposition(
            clause,
            observed,
            candidate_limit_exceeded,
            "ambiguous",
            polarity,
            relation_mode,
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
        return SpanDecomposition(
            (clause,),
            observed,
            candidate_limit_exceeded,
            False,
            (
                _single_clause_evidence(
                    clause,
                    spans,
                    polarity,
                    relation_mode,
                    release_propositions,
                ),
            ),
        )

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
    evidence_spans: dict[str, list[ProfileSignalSpan]] = {}
    for _, group_start, group_end, text, task_type in local_groups:
        if task_type not in summaries:
            task_order.append(task_type)
            summaries[task_type] = []
            evidence_spans[task_type] = []
        summaries[task_type].append(text)
        evidence_spans[task_type].extend(
            span
            for span in spans
            if span.task_type == task_type
            and span.start < group_end
            and span.end > group_start
        )

    clauses = tuple("; ".join(summaries[task_type]) for task_type in task_order)
    evidence = tuple(
        _profile_evidence(
            task_type,
            evidence_spans[task_type],
            clause if task_type == "open_source_release" else clauses[index],
            polarity,
            relation_mode,
            release_propositions,
        )
        for index, task_type in enumerate(task_order)
    )
    intent_limit = len(clauses) > MAX_EMITTED_INTENTS
    return SpanDecomposition(
        clauses=clauses[:MAX_EMITTED_INTENTS],
        observed_candidate_count=observed,
        candidate_signal_limit_exceeded=candidate_limit_exceeded,
        intent_limit_exceeded=intent_limit,
        intent_evidence=evidence[:MAX_EMITTED_INTENTS],
    )


def _suppressed_decomposition(
    clause: str,
    observed: int,
    candidate_limit_exceeded: bool,
    context: str,
    polarity: str,
    relation_mode: str,
) -> SpanDecomposition:
    return SpanDecomposition(
        clauses=(clause,),
        observed_candidate_count=observed,
        candidate_signal_limit_exceeded=candidate_limit_exceeded,
        intent_limit_exceeded=False,
        intent_evidence=(
            IntentEvidence(
                task_type="general",
                context=context,
                polarity=polarity,
                release_mode="none",
                relation_mode=relation_mode,
                matched_signals=(),
                matched_score=0,
            ),
        ),
    )


def _single_clause_evidence(
    clause: str,
    spans: tuple[ProfileSignalSpan, ...],
    polarity: str,
    relation_mode: str,
    release_propositions: tuple[ReleaseReadinessProposition, ...],
) -> IntentEvidence:
    if _WEBSITE_PUBLISH_PRECONDITION_RE.fullmatch(clause):
        return IntentEvidence(
            task_type="website_build",
            context="action",
            polarity=polarity,
            release_mode="none",
            relation_mode=relation_mode,
            matched_signals=("publishing site",),
            matched_score=2,
        )
    release_spans = [
        span for span in spans if span.task_type == "open_source_release"
    ]
    if release_spans and any(
        item.polarity == "positive" and item.discourse_role == "request"
        for item in release_propositions
    ):
        return _profile_evidence(
            "open_source_release",
            release_spans,
            clause,
            polarity,
            relation_mode,
            release_propositions,
        )
    if _has_positive_release_action(clause):
        return _profile_evidence(
            "open_source_release",
            release_spans,
            clause,
            polarity,
            relation_mode,
            release_propositions,
        )
    task_types = {span.task_type for span in spans}
    if len(task_types) != 1:
        return IntentEvidence(
            task_type="general",
            context="action",
            polarity=polarity,
            release_mode="none",
            relation_mode=relation_mode,
            matched_signals=(),
            matched_score=0,
        )
    task_type = next(iter(task_types))
    return _profile_evidence(
        task_type,
        list(spans),
        clause,
        polarity,
        relation_mode,
        release_propositions,
    )


def _profile_evidence(
    task_type: str,
    spans: list[ProfileSignalSpan],
    clause: str,
    polarity: str,
    relation_mode: str,
    release_propositions: tuple[ReleaseReadinessProposition, ...],
) -> IntentEvidence:
    signals = tuple(dict.fromkeys(span.signal for span in spans))
    release_mode = "none"
    if task_type == "open_source_release":
        normalized_signals = {
            signal.lower()
            for combined in signals
            for signal in combined.split(" / ")
        }
        readiness_proposition = next(
            (
                item
                for item in release_propositions
                if item.polarity == "positive"
                and item.discourse_role == "request"
            ),
            None,
        )
        if readiness_proposition and normalized_signals & {
            "release",
            "release checklist",
            "release packet",
            "release readiness",
            "发布清单",
        }:
            release_mode = "readiness"
            polarity = readiness_proposition.polarity
        elif source_supports_release_action(
            clause, tuple(normalized_signals)
        ):
            release_mode = "action"
        if release_mode == "none":
            return IntentEvidence(
                task_type="general",
                context="action",
                polarity=polarity,
                release_mode="none",
                relation_mode=relation_mode,
                matched_signals=(),
                matched_score=0,
            )
    return IntentEvidence(
        task_type=task_type,
        context="action",
        polarity=polarity,
        release_mode=release_mode,
        relation_mode=relation_mode,
        matched_signals=signals,
        matched_score=sum(span.score for span in spans),
    )


def _is_governance_enumeration(
    clause: str, spans: tuple[ProfileSignalSpan, ...]
) -> bool:
    has_descriptive_marker = bool(
        _DESCRIPTIVE_ENUMERATION_RE.search(clause)
        or _DESCRIPTIVE_LIST_PREFIX_RE.search(clause)
    )
    return bool(
        has_descriptive_marker
        and _ENUMERATION_MARKER_RE.search(clause)
        and len({span.task_type for span in spans}) >= 2
    )


def _non_action_source_ranges(clause: str) -> tuple[NonActionSourceRange, ...]:
    """Find local source ranges that explicitly deny routing authority."""
    structural = _NON_ACTION_STRUCTURAL_PREFIX_RE.match(clause)
    if structural is not None:
        context = (
            "ambiguous"
            if "future" in structural.group().lower()
            else "descriptive"
        )
        _, end = _non_action_segment_bounds(clause, 0, structural.end())
        return (NonActionSourceRange(0, end, context),)

    ranges: list[NonActionSourceRange] = []
    for pattern, context in (
        (_NON_ACTION_AUTHORITY_RE, "ambiguous"),
        (_HISTORICAL_NON_ACTION_RE, "descriptive"),
        (_OTHER_OWNER_NON_ACTION_RE, "ambiguous"),
    ):
        for match in pattern.finditer(clause):
            start, end = _non_action_segment_bounds(clause, match.start(), match.end())
            ranges.append(NonActionSourceRange(start, end, context))
    return tuple(sorted(ranges, key=lambda item: (item.start, item.end, item.context)))


def _non_action_segment_bounds(
    clause: str, match_start: int, match_end: int
) -> tuple[int, int]:
    start = 0
    for boundary in re.finditer(r"[.。！？!?;；\n]", clause[:match_start]):
        start = boundary.end()
    end = len(clause)
    boundary = re.search(r"[.。！？!?;；\n]", clause[match_end:])
    if boundary is not None:
        end = match_end + boundary.start()
    adversative = _ADVERSATIVE_BOUNDARY_RE.search(clause, match_end)
    if adversative is not None and adversative.start() < end:
        end = adversative.start()
    continuation = _CURRENT_ACTION_CONTINUATION_RE.search(clause, match_start)
    if continuation is not None and continuation.start() < end:
        end = continuation.start()
    return start, end


def relation_mode_for_text(clause: str) -> str:
    clause = bound_task_text(clause)
    if _EXPLICIT_SEQUENCE_RE.search(clause):
        return "explicit_sequence"
    if _PARALLEL_CONTEXT_RE.search(clause):
        return "parallel"
    if _PLUS_CONNECTOR_RE.search(clause) or _ENUMERATION_MARKER_RE.search(clause):
        return "enumeration"
    return "single"


def _clause_polarity(
    clause: str, spans: tuple[ProfileSignalSpan, ...]
) -> str:
    negation_ranges = _coordinated_negation_ranges(clause)
    if not negation_ranges:
        return "positive"
    if spans and _ADVERSATIVE_BOUNDARY_RE.search(clause):
        if all(
            span.start >= max(range_end for _, range_end in negation_ranges)
            for span in spans
        ):
            return "positive"
        return "mixed"
    return "negative"


def _has_positive_release_action(clause: str) -> bool:
    for segment in _ADVERSATIVE_BOUNDARY_RE.split(clause):
        if _NEGATION_MARKER_RE.search(segment) or _RELEASE_PRECONDITION_RE.search(
            segment
        ):
            continue
        if source_supports_release_action(segment):
            return True
    return False


def _descriptive_release_ranges(clause: str) -> tuple[tuple[int, int], ...]:
    """Return release-description ranges without crossing adversative boundaries."""
    ranges: list[tuple[int, int]] = []
    start = 0
    for boundary in _ADVERSATIVE_BOUNDARY_RE.finditer(clause):
        segment = clause[start : boundary.start()]
        if _DESCRIPTIVE_RELEASE_ACTION_RE.search(segment):
            ranges.append((start, boundary.start()))
        start = boundary.end()
    segment = clause[start:]
    if _DESCRIPTIVE_RELEASE_ACTION_RE.search(segment):
        ranges.append((start, len(clause)))
    return tuple(ranges)


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


def _range_overlaps(
    start: int, end: int, ranges: tuple[tuple[int, int], ...]
) -> bool:
    return any(start < range_end and end > range_start for range_start, range_end in ranges)


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
