"""Deterministic task normalization and multi-intent decomposition."""

from __future__ import annotations

from dataclasses import asdict, dataclass, replace
import re
from typing import Any

from .intent_evidence import (
    IntentEvidence,
    bind_intent_evidence,
    validate_intent_evidence,
)
from .intent_spans import (
    MAX_CANDIDATE_SIGNALS,
    MAX_EMITTED_INTENTS,
    SpanDecomposition,
    relation_mode_for_text,
    split_profile_enumeration,
)
from .intent_source import MAX_TASK_SCAN_CHARS, bound_task_text
from .router import build_profile_for_task_type, build_task_profile, split_current_intent_text


_LIST_MARKER_RE = re.compile(
    r"^\s*(?:\d+[.)、]|[-*+]\s*\[[ xX]\]|[-*+])\s+(.+?)\s*$"
)
_ORDERED_LIST_MARKER_RE = re.compile(r"^\s*\d+[.)、]\s+")
_UNORDERED_LIST_MARKER_RE = re.compile(r"^\s*[-*+](?:\s*\[[ xX]\])?\s+")
_PARALLEL_MARKER_RE = re.compile(
    r"\bin\s+parallel\b|\bparallel\b|同时|并行", re.IGNORECASE
)
_CLAUSE_SEPARATOR_RE = re.compile(
    r"\s*(?:[；;]|，?同时|，?以及|，\s*再|\bthen\b)\s*",
    re.IGNORECASE,
)
_ORDERED_BEFORE_RE = re.compile(
    r"\s+\bbefore\b\s+(?!(?:publishing|releasing|pushing|publish|release|push)\b)",
    re.IGNORECASE,
)
_ORDERED_AFTER_RE = re.compile(
    r"\s+\bafter\b\s+(?="
    r"(?:complet(?:e|ing)|verif(?:y|ying|ication)|review(?:ing)?)\b|"
    r"approval\s+of\s+(?:the\s+)?(?:pr|pull\s+request)\b|"
    r"(?:the\s+)?(?:pr|pull\s+request)\s+is\s+approved\b)",
    re.IGNORECASE,
)
_CHINESE_TARGET_FIRST_APPROVAL_RE = re.compile(
    r"\s*在\s*(?=(?:PR|拉取请求)\s*(?:审批通过|批准|审核通过)后\s*$)",
    re.IGNORECASE,
)
_PUBLISHING_SITE_TARGET = (
    r"publishing\s+"
    r"(?:(?:the|a|an|our|my|your|their|its)\s+)?"
    r"(?:(?:official|product|company)\s+)?(?:website|site)"
)
_BEFORE_PUBLISHING_WEBSITE_RE = re.compile(
    r"^(?P<source>.+?)\s+\bbefore\b\s+"
    rf"(?P<target>{_PUBLISHING_SITE_TARGET})\s*$",
    re.IGNORECASE,
)
_CHINESE_PRECEDES_RE = re.compile(r"\s*先于\s*")
_RELEASE_BOUNDARY_RE = re.compile(
    r"(?:验证(?:通过)?|测试通过|完成|批准|审批通过|审核通过)后(?:再)?(?:发布|上线|推送)"
)
_PREFIX_GATE_RE = re.compile(
    r"^\s*(?:after|once)\b|^\u5f85.+(?:\u5b8c\u6210|\u9a8c\u8bc1\u901a\u8fc7)\u540e|^\u5728.+(?:\u5b8c\u6210|\u9a8c\u8bc1\u901a\u8fc7)\u540e",
    re.IGNORECASE,
)
_INFIX_GATE_RE = re.compile(
    r"\bafter\s+(?:"
    r"(?:complet(?:e|ing)|verif(?:y|ying|ication)|review(?:ing)?)\b|"
    r"approval\s+of\s+(?:the\s+)?(?:pr|pull\s+request)\b|"
    r"(?:the\s+)?(?:pr|pull\s+request)\s+is\s+approved\b)",
    re.IGNORECASE,
)
_CHINESE_GATE_RE = re.compile(
    r"(?:\u5b8c\u6210|\u9a8c\u8bc1\u901a\u8fc7|\u6d4b\u8bd5\u901a\u8fc7|\u6279\u51c6|\u5ba1\u6279\u901a\u8fc7|\u5ba1\u6838\u901a\u8fc7)\u540e(?:\u518d)?"
)
_GATE_VERIFICATION_RE = re.compile(
    r"\b(?:verif(?:y|ied|ying|ication)|approv(?:ed|al))\b|"
    r"(?:\u9a8c\u8bc1\u901a\u8fc7|\u6d4b\u8bd5\u901a\u8fc7|\u6279\u51c6|\u5ba1\u6279\u901a\u8fc7|\u5ba1\u6838\u901a\u8fc7)",
    re.IGNORECASE,
)
_APPROVAL_RELEASE_RE = re.compile(
    r"^\s*(?:"
    r"(?:\u5728\s*)?(?P<cn_source>(?:PR|\u62c9\u53d6\u8bf7\u6c42)\s*"
    r"(?:\u5ba1\u6279\u901a\u8fc7|\u6279\u51c6|\u5ba1\u6838\u901a\u8fc7)\u540e)\s*[,\uff0c]?\s*"
    r"(?P<cn_target>(?:\u53d1\u5e03|\u4e0a\u7ebf|\u63a8\u9001).+)|"
    r"(?P<en_source>after\s+(?:(?:the\s+)?(?:pr|pull\s+request)\s+"
    r"is\s+approved|(?:pr|pull\s+request)\s+approval))\s*[,\uff0c]?\s*"
    r"(?P<en_target>(?:publish|release|push)\b.+)"
    r")\s*$",
    re.IGNORECASE,
)
_CANONICAL_PREFIX_BEFORE_RE = re.compile(
    r"^\s*before\b|^\s*.+\u524d\s*[,\uff0c]", re.IGNORECASE
)
_CANONICAL_FIRST_THEN_RE = re.compile(
    r"\bthen\b|\u5148[\s\S]*\u518d", re.IGNORECASE
)
_CANONICAL_BEFORE_RE = re.compile(r"\bbefore\b|\u5148\u4e8e", re.IGNORECASE)
_CANONICAL_ORDER_LEAD_IN_RE = re.compile(
    r"\b(?:workstream|workflow|execution)\s+order\b|"
    r"\bin\s+(?:this\s+)?order\b|"
    r"\b(?:ordered\s+)?(?:workflow\s+)?steps?\s*:|"
    r"(?:\u5de5\u4f5c\u6d41|\u6d41\u7a0b|\u6267\u884c)\u987a\u5e8f|\u6b65\u9aa4\s*[:\uff1a]",
    re.IGNORECASE,
)
_CANONICAL_UNKNOWN_PREFIX_GATE_RE = re.compile(
    r"^\s*(?:after|once)\s+(.+?)"
    r"(?:\s+is\s+(?:complete|completed|verified|approved))?\s*[,;]",
    re.IGNORECASE,
)
SEMICOLON_WORKFLOW_TRANSITIONS = frozenset(
    {
        ("multi_platform_research_discovery", "investment_research_diligence"),
        ("investment_research_diligence", "data_analysis"),
        ("document_knowledge_base", "rag_agent"),
        ("rag_agent", "agent_security"),
        ("agent_planning_orchestration", "website_build"),
        ("website_build", "code_review"),
        ("data_analysis", "content_seo"),
        ("content_seo", "content_video_production"),
        ("code_review", "codebase_change_lifecycle"),
        ("multi_platform_research_discovery", "content_seo"),
        ("design_md_system_governance", "website_build"),
        ("private_communication_governance", "document_knowledge_base"),
        ("claude_skills_backlog_coverage", "skill_router_review"),
        ("skill_router_review", "code_review"),
        ("data_analysis", "commerce_growth"),
        ("commerce_growth", "content_seo"),
        ("industry_application_orchestration", "agent_planning_orchestration"),
        ("agent_planning_orchestration", "data_analysis"),
        ("codebase_graph_intelligence", "codebase_change_lifecycle"),
        ("codebase_change_lifecycle", "code_review"),
        ("investment_research_diligence", "agent_security"),
        ("content_video_production", "agentic_media_production"),
        ("private_communication_governance", "agent_role_library_governance"),
        ("agent_role_library_governance", "agent_planning_orchestration"),
        ("code_review", "website_build"),
    }
)
_INTENT_ID_RE = re.compile(r"^i[1-9][0-9]*$")
_INTENT_SOURCES = {"deterministic", "semantic", "hybrid"}
_INTENT_RELATION_REASON_REQUIREMENTS = {
    "before": False,
    "completion_gate": False,
    "explicit_sequence": False,
    "first_then": False,
    "release_gate": True,
    "semicolon_sequence": False,
    "semicolon_workflow": False,
    "verification_gate": True,
}


@dataclass(frozen=True)
class NormalizedTask:
    raw: str
    current: str
    history: str
    stale: str
    stale_policy: str

    def to_json(self) -> dict[str, Any]:
        return _json_compatible(asdict(self))


@dataclass(frozen=True)
class Intent:
    id: str
    summary: str
    task_type: str
    required_artifacts: tuple[str, ...]
    risk_flags: tuple[str, ...]
    depends_on: tuple[str, ...]
    source: str
    confidence: float

    def to_json(self) -> dict[str, Any]:
        return _json_compatible(asdict(self))


@dataclass(frozen=True)
class IntentRelation:
    source_id: str
    target_id: str
    reason: str
    requires_verification: bool = False


@dataclass(frozen=True)
class IntentGraph:
    intents: tuple[Intent, ...]
    unresolved_dependencies: tuple[str, ...]
    dependency_relations: tuple[IntentRelation, ...] = ()
    intent_evidence: tuple[IntentEvidence, ...] = ()
    evidence_source: str = ""

    def to_json(self) -> dict[str, Any]:
        return {
            "intents": [intent.to_json() for intent in self.intents],
            "unresolved_dependencies": _json_compatible(
                self.unresolved_dependencies
            ),
        }

    def validate(self) -> list[str]:
        errors: list[str] = []
        if not self.intents:
            errors.append("intent graph is empty")
            errors.extend(
                _validate_dependency_relations(
                    self.dependency_relations, {}, set()
                )
            )
            errors.extend(
                validate_intent_evidence(
                    self.intent_evidence, (), self.evidence_source
                )
            )
            return errors

        duplicate_ids = _duplicate_intent_ids(self.intents)
        if duplicate_ids:
            return [f"duplicate intent id: {intent_id}" for intent_id in duplicate_ids]

        intent_ids = {intent.id for intent in self.intents}
        dependencies = {
            intent.id: intent.depends_on
            if isinstance(intent.depends_on, (tuple, list))
            else ()
            for intent in self.intents
        }

        for intent in self.intents:
            if not isinstance(intent.id, str) or not _INTENT_ID_RE.fullmatch(intent.id):
                errors.append(f"invalid intent id: {intent.id}")
            if not isinstance(intent.summary, str) or not intent.summary.strip():
                errors.append(f"intent {intent.id} summary must be nonempty")
            if not isinstance(intent.task_type, str) or not intent.task_type.strip():
                errors.append(f"intent {intent.id} task_type must be nonempty")
            if not _contains_only_nonempty_strings(intent.required_artifacts):
                errors.append(
                    f"intent {intent.id} required_artifacts must contain nonempty strings"
                )
            if not _contains_only_nonempty_strings(intent.risk_flags):
                errors.append(f"intent {intent.id} risk_flags must contain nonempty strings")
            if not isinstance(intent.depends_on, (tuple, list)):
                errors.append(f"intent {intent.id} depends_on must contain valid intent IDs")
            else:
                for dependency in intent.depends_on:
                    if not isinstance(dependency, str) or not _INTENT_ID_RE.fullmatch(dependency):
                        errors.append(f"intent {intent.id} has invalid dependency id: {dependency}")
                    if dependency not in intent_ids:
                        errors.append(f"intent {intent.id} depends on unknown intent {dependency}")
            if intent.source not in _INTENT_SOURCES:
                errors.append(f"intent {intent.id} has invalid source: {intent.source}")
            if (
                isinstance(intent.confidence, bool)
                or not isinstance(intent.confidence, (int, float))
                or not 0 <= intent.confidence <= 1
            ):
                errors.append(f"intent {intent.id} confidence must be between 0 and 1")

        if not _contains_only_nonempty_strings(self.unresolved_dependencies):
            errors.append("unresolved_dependencies must contain nonempty strings")

        errors.extend(
            _validate_dependency_relations(
                self.dependency_relations, dependencies, intent_ids
            )
        )
        bounded_evidence_source = (
            bound_task_text(self.evidence_source)
            if isinstance(self.evidence_source, str)
            else self.evidence_source
        )
        errors.extend(
            validate_intent_evidence(
                self.intent_evidence,
                tuple(intent.task_type for intent in self.intents),
                bounded_evidence_source,
            )
        )
        if (
            self.intent_evidence
            and isinstance(self.evidence_source, str)
            and self.evidence_source
        ):
            if len(self.evidence_source) > MAX_TASK_SCAN_CHARS:
                errors.append("intent evidence source exceeds scan boundary")
            canonical = _parse_bounded_intent_source(
                bound_task_text(self.evidence_source)
            )
            if self.intent_evidence != canonical.intent_evidence:
                errors.append(
                    "intent evidence does not match canonical source analysis"
                )
            canonical_summaries = canonical.clauses
            actual_summaries = tuple(intent.summary for intent in self.intents)
            if actual_summaries != canonical_summaries:
                errors.append(
                    "intent summaries do not match canonical source analysis"
                )
            actual_dependencies = tuple(
                tuple(intent.depends_on)
                if isinstance(intent.depends_on, (tuple, list))
                else ()
                for intent in self.intents
            )
            if actual_dependencies != canonical.intent_dependencies:
                errors.append(
                    "intent dependencies do not match canonical source analysis"
                )
            if self.dependency_relations != canonical.dependency_relations:
                errors.append(
                    "dependency relations do not match canonical source analysis"
                )
            if self.unresolved_dependencies != canonical.unresolved_dependencies:
                errors.append(
                    "unresolved dependencies do not match canonical source analysis"
                )

        cycle = _find_dependency_cycle(dependencies, intent_ids)
        if cycle:
            errors.append(f"intent dependency cycle detected: {' -> '.join(cycle)}")
        return errors


@dataclass(frozen=True)
class DecompositionDiagnostics:
    mode: str
    observed_candidate_count: int
    emitted_intent_count: int
    candidate_signal_limit_exceeded: bool
    intent_limit_exceeded: bool
    reason_codes: tuple[str, ...]

    @property
    def status(self) -> str:
        return "incomplete" if self.reason_codes else "complete"

    def to_json(self) -> dict[str, Any]:
        return _json_compatible(asdict(self))


@dataclass(frozen=True)
class TaskDecomposition:
    intent_graph: IntentGraph
    diagnostics: DecompositionDiagnostics


@dataclass(frozen=True)
class _ParsedIntentSource:
    clauses: tuple[str, ...]
    intent_evidence: tuple[IntentEvidence, ...]
    dependency_relations: tuple[IntentRelation, ...]
    intent_dependencies: tuple[tuple[str, ...], ...]
    unresolved_dependencies: tuple[str, ...]
    observed_candidate_count: int
    candidate_signal_limit_exceeded: bool
    intent_limit_exceeded: bool
    used_profile_spans: bool


def normalize_task(task: str) -> NormalizedTask:
    bounded_task = bound_task_text(task)
    context = split_current_intent_text(bounded_task)
    current = (
        context["current_intent_text"]
        if context["current_intent_detected"]
        else bounded_task.strip()
    )
    return NormalizedTask(
        raw=task,
        current=current,
        history=context["history_context_text"],
        stale=context["stale_context_text"],
        stale_policy=context["stale_context_policy"],
    )


def split_task_clauses(task: str) -> list[str]:
    task = bound_task_text(task)
    normalized = normalize_task(task)
    text = normalized.current.strip()
    if not text:
        return []

    approval_release = _APPROVAL_RELEASE_RE.fullmatch(text)
    if approval_release:
        return [
            approval_release.group("cn_source")
            or approval_release.group("en_source"),
            approval_release.group("cn_target")
            or approval_release.group("en_target"),
        ]

    list_items = _split_list_items(text)
    if len(list_items) > 1:
        return list_items

    clauses: list[str] = []
    for candidate in _CLAUSE_SEPARATOR_RE.split(text):
        candidate = candidate.strip(" \t\n,，。")
        if not candidate:
            continue
        before_publishing = _BEFORE_PUBLISHING_WEBSITE_RE.match(candidate)
        if before_publishing:
            clauses.extend(
                [
                    before_publishing.group("source"),
                    f"before {before_publishing.group('target')}",
                ]
            )
            continue
        ordered_parts = [
            part.strip(" \t\n,，。")
            for part in _ORDERED_BEFORE_RE.split(candidate)
            if part.strip(" \t\n,，。")
        ]
        if len(ordered_parts) > 1:
            clauses.extend(ordered_parts)
            continue
        completion_parts = [
            part.strip(" \t\n,，。")
            for part in _ORDERED_AFTER_RE.split(candidate)
            if part.strip(" \t\n,，。")
        ]
        if len(completion_parts) > 1:
            clauses.extend(completion_parts)
            continue
        target_first_approval_parts = [
            part.strip(" \t\n,，。")
            for part in _CHINESE_TARGET_FIRST_APPROVAL_RE.split(candidate)
            if part.strip(" \t\n,，。")
        ]
        if len(target_first_approval_parts) > 1:
            clauses.extend(target_first_approval_parts)
            continue
        preceding_parts = [
            part.strip(" \t\n,，。")
            for part in _CHINESE_PRECEDES_RE.split(candidate)
            if part.strip(" \t\n,，。")
        ]
        if len(preceding_parts) > 1:
            clauses.extend(preceding_parts)
            continue
        release_match = _RELEASE_BOUNDARY_RE.search(candidate)
        if release_match and release_match.start() > 0:
            clauses.extend([candidate[: release_match.start()], candidate[release_match.start() :]])
        else:
            clauses.append(candidate)
    return [clause.strip(" \t\n,，。") for clause in clauses if clause.strip(" \t\n,，。")]


def _split_list_items(text: str) -> list[str]:
    items: list[str] = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        marker = _LIST_MARKER_RE.match(raw_line)
        if marker:
            items.append(marker.group(1).strip())
        elif items:
            items[-1] = f"{items[-1]} {line}"
        else:
            return []
    return items


def classify_intent(
    clause: str,
    index: int,
    evidence: IntentEvidence,
) -> Intent:
    scanned_clause = bound_task_text(clause)
    if evidence.task_type == "general":
        profile = build_task_profile("")
    else:
        profile = build_profile_for_task_type(
            scanned_clause, evidence.task_type
        )
    task_type = evidence.task_type
    required_artifacts = tuple(profile["artifact_types"])
    risk_flags = tuple(profile["risk_flags"])
    if evidence.release_mode == "action":
        required_artifacts = ("release_record",)
        risk_flags = ("public_release",)
    return Intent(
        id=f"i{index}",
        summary=clause.strip(),
        task_type=task_type,
        required_artifacts=required_artifacts,
        risk_flags=risk_flags,
        depends_on=(),
        source="deterministic",
        confidence=_deterministic_confidence(evidence.matched_score, task_type),
    )


def _parse_bounded_intent_source(source: str) -> _ParsedIntentSource:
    """Build canonical clauses and evidence from an already bounded source."""
    current = bound_task_text(source)
    broad_clauses = split_task_clauses(current)
    clauses: list[str] = []
    observed_candidate_count = 0
    candidate_signal_limit_exceeded = False
    intent_limit_exceeded = False
    used_profile_spans = False
    clause_evidence: list[IntentEvidence] = []
    for clause_index, broad_clause in enumerate(broad_clauses):
        if candidate_signal_limit_exceeded:
            decomposition = SpanDecomposition(
                clauses=(broad_clause,),
                observed_candidate_count=0,
                candidate_signal_limit_exceeded=True,
                intent_limit_exceeded=False,
                intent_evidence=(
                    IntentEvidence(
                        task_type="general",
                        context="ambiguous",
                        polarity="positive",
                        release_mode="none",
                        relation_mode="single",
                        matched_signals=(),
                        matched_score=0,
                    ),
                ),
            )
        else:
            candidate_budget = max(
                0, MAX_CANDIDATE_SIGNALS - observed_candidate_count
            )
            decomposition = split_profile_enumeration(
                broad_clause, candidate_budget
            )
        observed_candidate_count = min(
            129,
            observed_candidate_count + decomposition.observed_candidate_count,
        )
        candidate_signal_limit_exceeded = (
            candidate_signal_limit_exceeded
            or decomposition.candidate_signal_limit_exceeded
        )
        intent_limit_exceeded = (
            intent_limit_exceeded or decomposition.intent_limit_exceeded
        )
        used_profile_spans = (
            used_profile_spans or len(decomposition.clauses) > 1
        )
        remaining = MAX_EMITTED_INTENTS - len(clauses)
        if len(decomposition.clauses) > remaining:
            intent_limit_exceeded = True
        if remaining > 0:
            emitted = decomposition.clauses[:remaining]
            clauses.extend(emitted)
            clause_evidence.extend(
                decomposition.intent_evidence[: len(emitted)]
            )
        if (
            len(clauses) >= MAX_EMITTED_INTENTS
            and clause_index < len(broad_clauses) - 1
        ):
            intent_limit_exceeded = True
            break

    clause_evidence = _apply_source_relation_modes(
        current, clauses, clause_evidence
    )
    clause_evidence = _apply_source_gate_modes(
        current, clauses, clause_evidence
    )
    bound_evidence = bind_intent_evidence(tuple(clause_evidence), current)
    dependency_relations = _canonical_relations(current, bound_evidence)
    intent_dependencies = _canonical_dependencies(
        len(bound_evidence), dependency_relations
    )
    unresolved_dependencies = _canonical_unresolved_dependencies(
        current, len(bound_evidence)
    )
    return _ParsedIntentSource(
        clauses=tuple(clauses),
        intent_evidence=bound_evidence,
        dependency_relations=dependency_relations,
        intent_dependencies=intent_dependencies,
        unresolved_dependencies=unresolved_dependencies,
        observed_candidate_count=observed_candidate_count,
        candidate_signal_limit_exceeded=candidate_signal_limit_exceeded,
        intent_limit_exceeded=intent_limit_exceeded,
        used_profile_spans=used_profile_spans,
    )


def _canonical_intent_evidence(source: str) -> tuple[IntentEvidence, ...]:
    return _parse_bounded_intent_source(bound_task_text(source)).intent_evidence


def decompose_task_detailed(task: str) -> TaskDecomposition:
    from .intent_dependencies import (
        apply_intent_relations,
    )

    task_scan_limit_exceeded = len(task) > MAX_TASK_SCAN_CHARS
    current = normalize_task(task).current
    parsed = _parse_bounded_intent_source(current)
    clauses = parsed.clauses
    bound_evidence = parsed.intent_evidence

    intents: list[Intent] = []
    for index, clause in enumerate(clauses, start=1):
        evidence = bound_evidence[index - 1]
        intents.append(classify_intent(clause, index, evidence))
    relations = parsed.dependency_relations
    final_intents = apply_intent_relations(intents, relations)
    intent_graph = IntentGraph(
        intents=final_intents,
        unresolved_dependencies=parsed.unresolved_dependencies,
        dependency_relations=relations,
        intent_evidence=bound_evidence,
        evidence_source=current,
    )
    reason_codes: list[str] = []
    if task_scan_limit_exceeded:
        reason_codes.append("task_scan_limit_exceeded")
    if parsed.candidate_signal_limit_exceeded:
        reason_codes.append("candidate_signal_limit_exceeded")
    if parsed.intent_limit_exceeded:
        reason_codes.append("intent_limit_exceeded")
    if any(
        evidence.task_type == "general"
        and evidence.context in {"descriptive", "how_to", "ambiguous"}
        for evidence in bound_evidence
    ):
        reason_codes.append("ambiguous_profile_enumeration")
    diagnostics = DecompositionDiagnostics(
        mode=(
            "profile_spans"
            if parsed.used_profile_spans
            else "strong_clauses"
            if len(split_task_clauses(current)) > 1
            else "single_clause"
        ),
        observed_candidate_count=parsed.observed_candidate_count,
        emitted_intent_count=len(intents),
        candidate_signal_limit_exceeded=parsed.candidate_signal_limit_exceeded,
        intent_limit_exceeded=parsed.intent_limit_exceeded,
        reason_codes=tuple(reason_codes),
    )
    return TaskDecomposition(intent_graph=intent_graph, diagnostics=diagnostics)


def _apply_source_relation_modes(
    source: str,
    clauses: list[str],
    evidence: list[IntentEvidence],
) -> list[IntentEvidence]:
    list_mode = _list_relation_mode(source)
    if list_mode is not None:
        return [replace(item, relation_mode=list_mode) for item in evidence]
    if relation_mode_for_text(source) != "explicit_sequence":
        return evidence

    parallel = _PARALLEL_MARKER_RE.search(source)
    if parallel is None:
        return [
            replace(item, relation_mode="explicit_sequence") for item in evidence
        ]

    source_folded = source.casefold()
    search_start = 0
    result: list[IntentEvidence] = []
    for clause, item in zip(clauses, evidence, strict=True):
        position = source_folded.find(clause.casefold(), search_start)
        if position < 0:
            position = search_start
        search_start = position + len(clause)
        mode = "parallel" if position >= parallel.start() else "explicit_sequence"
        result.append(replace(item, relation_mode=mode))
    return result


def _list_relation_mode(source: str) -> str | None:
    lines = [line for line in source.splitlines() if line.strip()]
    if len(lines) < 2:
        return None
    if all(_ORDERED_LIST_MARKER_RE.match(line) for line in lines):
        return "explicit_sequence"
    if all(_UNORDERED_LIST_MARKER_RE.match(line) for line in lines):
        return "parallel"
    return None


def _apply_source_gate_modes(
    source: str,
    clauses: list[str],
    evidence: list[IntentEvidence],
) -> list[IntentEvidence]:
    if not evidence:
        return evidence

    result = list(evidence)
    if _CHINESE_TARGET_FIRST_APPROVAL_RE.search(source) or (
        _INFIX_GATE_RE.search(source) and not _PREFIX_GATE_RE.search(source)
    ):
        index = len(result) - 1
        result[index] = replace(
            result[index], gate_mode=_gate_mode_for_clause(source)
        )
        return result
    if _PREFIX_GATE_RE.search(source) or _CHINESE_GATE_RE.search(source):
        for index in range(len(result) - 1):
            result[index] = replace(
                result[index],
                gate_mode=_gate_mode_for_clause(clauses[index]),
            )
    return result


def _gate_mode_for_clause(clause: str) -> str:
    return (
        "verification"
        if _GATE_VERIFICATION_RE.search(bound_task_text(clause))
        else "completion"
    )


def _canonical_relations(
    source: str, evidence: tuple[IntentEvidence, ...]
) -> tuple[IntentRelation, ...]:
    source = bound_task_text(source)
    if len(evidence) < 2:
        return ()

    relations: list[IntentRelation] = []
    parallel_start = next(
        (
            index
            for index, item in enumerate(evidence)
            if item.relation_mode == "parallel"
        ),
        len(evidence),
    )
    ordered = evidence[:parallel_start]
    gate_indexes = [
        index for index, item in enumerate(ordered) if item.gate_mode != "none"
    ]

    if gate_indexes:
        if (
            len(ordered) == 2
            and gate_indexes == [1]
            and ordered[0].task_type != "open_source_release"
        ):
            _append_canonical_gate(relations, 1, 0, ordered[1])
        else:
            for index in gate_indexes:
                if (
                    index + 1 < len(ordered)
                    and ordered[index + 1].task_type != "open_source_release"
                ):
                    _append_canonical_gate(
                        relations, index, index + 1, ordered[index]
                    )
    elif _CANONICAL_PREFIX_BEFORE_RE.search(source) and len(ordered) == 2:
        relations.append(IntentRelation("i2", "i1", "before"))
    elif _CANONICAL_FIRST_THEN_RE.search(source):
        _append_canonical_chain(relations, ordered, "first_then")
    elif _CANONICAL_BEFORE_RE.search(source):
        _append_canonical_chain(relations, ordered, "before")
    elif any(item.relation_mode == "explicit_sequence" for item in ordered):
        _append_canonical_chain(relations, ordered, "explicit_sequence")
    elif ";" in source or "；" in source:
        explicit_order = bool(
            _CANONICAL_ORDER_LEAD_IN_RE.search(source)
            or _CANONICAL_FIRST_THEN_RE.search(source)
        )
        for index, (left, right) in enumerate(zip(ordered, ordered[1:])):
            if right.task_type != "open_source_release" and (
                explicit_order
                or (left.task_type, right.task_type)
                in SEMICOLON_WORKFLOW_TRANSITIONS
            ):
                relations.append(
                    IntentRelation(
                        f"i{index + 1}", f"i{index + 2}", "semicolon_sequence"
                    )
                )

    for target_index, target in enumerate(evidence):
        if target.task_type != "open_source_release":
            continue
        if target.release_mode == "readiness" and target.relation_mode in {
            "single",
            "enumeration",
            "parallel",
        }:
            continue
        for source_index in range(target_index):
            relations.append(
                IntentRelation(
                    f"i{source_index + 1}",
                    f"i{target_index + 1}",
                    "release_gate",
                    True,
                )
            )
    return _deduplicate_canonical_relations(relations)


def _append_canonical_gate(
    relations: list[IntentRelation],
    source_index: int,
    target_index: int,
    source_evidence: IntentEvidence,
) -> None:
    verification = source_evidence.gate_mode == "verification"
    relations.append(
        IntentRelation(
            f"i{source_index + 1}",
            f"i{target_index + 1}",
            "verification_gate" if verification else "completion_gate",
            verification,
        )
    )


def _append_canonical_chain(
    relations: list[IntentRelation],
    evidence: tuple[IntentEvidence, ...],
    reason: str,
) -> None:
    for index, target in enumerate(evidence[1:]):
        if target.task_type != "open_source_release":
            relations.append(
                IntentRelation(f"i{index + 1}", f"i{index + 2}", reason)
            )


def _deduplicate_canonical_relations(
    relations: list[IntentRelation],
) -> tuple[IntentRelation, ...]:
    seen: set[tuple[str, str]] = set()
    result: list[IntentRelation] = []
    for relation in relations:
        edge = (relation.source_id, relation.target_id)
        if edge not in seen and relation.source_id != relation.target_id:
            seen.add(edge)
            result.append(relation)
    return tuple(result)


def _canonical_dependencies(
    intent_count: int, relations: tuple[IntentRelation, ...]
) -> tuple[tuple[str, ...], ...]:
    dependencies = [[] for _ in range(intent_count)]
    for relation in relations:
        target_index = int(relation.target_id[1:]) - 1
        dependencies[target_index].append(relation.source_id)
    return tuple(tuple(items) for items in dependencies)


def _canonical_unresolved_dependencies(
    source: str, intent_count: int
) -> tuple[str, ...]:
    if intent_count != 1:
        return ()
    match = _CANONICAL_UNKNOWN_PREFIX_GATE_RE.search(bound_task_text(source))
    if not match:
        return ()
    reference = match.group(1).strip()
    return (f"unresolved dependency: {reference}",) if reference else ()


def decompose_task(task: str) -> IntentGraph:
    return decompose_task_detailed(task).intent_graph


def _deterministic_confidence(matched_signal_score: int, task_type: str) -> float:
    if task_type == "open_source_release":
        return 0.9
    if matched_signal_score <= 0:
        return 0.5
    return min(1.0, 0.6 + matched_signal_score / 20)


def _json_compatible(value: Any) -> Any:
    if isinstance(value, tuple):
        return [_json_compatible(item) for item in value]
    if isinstance(value, list):
        return [_json_compatible(item) for item in value]
    if isinstance(value, dict):
        return {key: _json_compatible(item) for key, item in value.items()}
    return value


def _duplicate_intent_ids(intents: tuple[Intent, ...]) -> list[str]:
    seen: set[str] = set()
    duplicates: list[str] = []
    for intent in intents:
        if intent.id in seen and intent.id not in duplicates:
            duplicates.append(intent.id)
        seen.add(intent.id)
    return duplicates


def _contains_only_nonempty_strings(values: Any) -> bool:
    return isinstance(values, (tuple, list)) and all(
        isinstance(value, str) and bool(value) for value in values
    )


def _validate_dependency_relations(
    relations: Any,
    dependencies: dict[str, tuple[str, ...]],
    intent_ids: set[str],
) -> list[str]:
    if not isinstance(relations, tuple):
        return ["dependency_relations must be a tuple of IntentRelation records"]

    errors: list[str] = []
    seen_pairs: set[tuple[str, str]] = set()
    represented_pairs: set[tuple[str, str]] = set()
    for relation in relations:
        if type(relation) is not IntentRelation:
            errors.append("dependency relation must be an IntentRelation")
            continue

        source_valid = bool(
            isinstance(relation.source_id, str)
            and _INTENT_ID_RE.fullmatch(relation.source_id)
        )
        target_valid = bool(
            isinstance(relation.target_id, str)
            and _INTENT_ID_RE.fullmatch(relation.target_id)
        )
        if not source_valid:
            errors.append(
                f"dependency relation has invalid source id: {relation.source_id}"
            )
        elif relation.source_id not in intent_ids:
            errors.append(
                f"dependency relation has unknown source id: {relation.source_id}"
            )
        if not target_valid:
            errors.append(
                f"dependency relation has invalid target id: {relation.target_id}"
            )
        elif relation.target_id not in intent_ids:
            errors.append(
                f"dependency relation has unknown target id: {relation.target_id}"
            )
        if source_valid and target_valid and relation.source_id == relation.target_id:
            errors.append(
                f"dependency relation cannot be self-referential: {relation.source_id}"
            )
        if (
            not isinstance(relation.reason, str)
            or relation.reason not in _INTENT_RELATION_REASON_REQUIREMENTS
        ):
            errors.append(
                f"dependency relation has unsupported reason: {relation.reason}"
            )
        if type(relation.requires_verification) is not bool:
            errors.append("dependency relation requires_verification must be bool")
        elif (
            isinstance(relation.reason, str)
            and relation.reason in _INTENT_RELATION_REASON_REQUIREMENTS
            and relation.requires_verification
            is not _INTENT_RELATION_REASON_REQUIREMENTS[relation.reason]
        ):
            errors.append(
                "dependency relation verification requirement mismatches "
                f"reason: {relation.reason}"
            )

        pair = (
            (relation.source_id, relation.target_id)
            if isinstance(relation.source_id, str)
            and isinstance(relation.target_id, str)
            else None
        )
        if pair is not None:
            if pair in seen_pairs:
                errors.append(
                    "duplicate dependency relation metadata: "
                    f"{relation.source_id} -> {relation.target_id}"
                )
            seen_pairs.add(pair)
        if (
            source_valid
            and target_valid
            and relation.source_id in intent_ids
            and relation.target_id in intent_ids
        ):
            if relation.source_id not in dependencies.get(relation.target_id, ()):
                errors.append(
                    f"dependency relation {relation.source_id} -> "
                    f"{relation.target_id} is not represented by depends_on"
                )
            else:
                if pair is not None:
                    represented_pairs.add(pair)

    if relations:
        dependency_pairs = {
            (dependency_id, target_id)
            for target_id, dependency_ids in dependencies.items()
            for dependency_id in dependency_ids
            if isinstance(dependency_id, str)
        }
        for source_id, target_id in sorted(dependency_pairs - represented_pairs):
            errors.append(
                f"dependency relation metadata missing for edge: "
                f"{source_id} -> {target_id}"
            )
    return errors


def _find_dependency_cycle(
    dependencies: dict[str, tuple[str, ...]],
    intent_ids: set[str],
) -> tuple[str, ...]:
    visited: set[str] = set()
    active: list[str] = []
    active_ids: set[str] = set()

    def visit(intent_id: str) -> tuple[str, ...]:
        if intent_id in active_ids:
            start = active.index(intent_id)
            return tuple(active[start:] + [intent_id])
        if intent_id in visited:
            return ()

        active.append(intent_id)
        active_ids.add(intent_id)
        for dependency in dependencies.get(intent_id, ()):
            if dependency not in intent_ids:
                continue
            cycle = visit(dependency)
            if cycle:
                return cycle
        active.pop()
        active_ids.remove(intent_id)
        visited.add(intent_id)
        return ()

    for intent_id in dependencies:
        cycle = visit(intent_id)
        if cycle:
            return cycle
    return ()
