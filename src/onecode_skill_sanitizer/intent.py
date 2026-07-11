"""Deterministic task normalization and multi-intent decomposition."""

from __future__ import annotations

from dataclasses import asdict, dataclass, replace
import re
from typing import Any

from .intent_evidence import IntentEvidence, validate_intent_evidence
from .intent_spans import (
    MAX_CANDIDATE_SIGNALS,
    MAX_EMITTED_INTENTS,
    SpanDecomposition,
    relation_mode_for_text,
    split_profile_enumeration,
)
from .router import build_profile_for_task_type, build_task_profile, split_current_intent_text
from .routing_profiles import MAX_SCAN_CHARACTERS


_LIST_MARKER_RE = re.compile(
    r"^\s*(?:\d+[.)、]|[-*+]\s*\[[ xX]\]|[-*+])\s+(.+?)\s*$"
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
            errors.extend(validate_intent_evidence(self.intent_evidence, ()))
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
        errors.extend(
            validate_intent_evidence(
                self.intent_evidence,
                tuple(intent.task_type for intent in self.intents),
                tuple(intent.summary for intent in self.intents),
            )
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


def normalize_task(task: str) -> NormalizedTask:
    context = split_current_intent_text(task)
    current = context["current_intent_text"] if context["current_intent_detected"] else task.strip()
    return NormalizedTask(
        raw=task,
        current=current,
        history=context["history_context_text"],
        stale=context["stale_context_text"],
        stale_policy=context["stale_context_policy"],
    )


def split_task_clauses(task: str) -> list[str]:
    normalized = normalize_task(task)
    text = normalized.current.strip()
    if not text:
        return []

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
    scanned_clause = clause[:MAX_SCAN_CHARACTERS]
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


def decompose_task_detailed(task: str) -> TaskDecomposition:
    from .intent_dependencies import (
        apply_intent_relations,
        infer_intent_relations,
        infer_unresolved_dependencies,
    )

    current = normalize_task(task).current
    task_scan_limit_exceeded = len(current) > MAX_SCAN_CHARACTERS
    broad_clauses = split_task_clauses(current[:MAX_SCAN_CHARACTERS])
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
            decomposition = split_profile_enumeration(broad_clause, candidate_budget)
        observed_candidate_count = min(
            129,
            observed_candidate_count + decomposition.observed_candidate_count,
        )
        candidate_signal_limit_exceeded = (
            candidate_signal_limit_exceeded
            or decomposition.candidate_signal_limit_exceeded
        )
        intent_limit_exceeded = intent_limit_exceeded or decomposition.intent_limit_exceeded
        used_profile_spans = used_profile_spans or len(decomposition.clauses) > 1
        remaining = MAX_EMITTED_INTENTS - len(clauses)
        if len(decomposition.clauses) > remaining:
            intent_limit_exceeded = True
        if remaining > 0:
            emitted = decomposition.clauses[:remaining]
            clauses.extend(emitted)
            clause_evidence.extend(decomposition.intent_evidence[: len(emitted)])
        if (
            len(clauses) >= MAX_EMITTED_INTENTS
            and clause_index < len(broad_clauses) - 1
        ):
            intent_limit_exceeded = True
            break

    intents: list[Intent] = []
    if (
        relation_mode_for_text(current) == "explicit_sequence"
        or len(_split_list_items(current)) > 1
    ):
        clause_evidence = [
            replace(evidence, relation_mode="explicit_sequence")
            for evidence in clause_evidence
        ]
    for index, clause in enumerate(clauses, start=1):
        evidence = clause_evidence[index - 1]
        intents.append(classify_intent(clause, index, evidence))
    relations = infer_intent_relations(current, intents, tuple(clause_evidence))
    final_intents = apply_intent_relations(intents, relations)
    intent_graph = IntentGraph(
        intents=final_intents,
        unresolved_dependencies=infer_unresolved_dependencies(current, final_intents),
        dependency_relations=relations,
        intent_evidence=tuple(clause_evidence),
    )
    reason_codes: list[str] = []
    if task_scan_limit_exceeded:
        reason_codes.append("task_scan_limit_exceeded")
    if candidate_signal_limit_exceeded:
        reason_codes.append("candidate_signal_limit_exceeded")
    if intent_limit_exceeded:
        reason_codes.append("intent_limit_exceeded")
    if any(
        evidence.task_type == "general"
        and evidence.context in {"descriptive", "how_to", "ambiguous"}
        for evidence in clause_evidence
    ):
        reason_codes.append("ambiguous_profile_enumeration")
    diagnostics = DecompositionDiagnostics(
        mode=(
            "profile_spans"
            if used_profile_spans
            else "strong_clauses"
            if len(broad_clauses) > 1
            else "single_clause"
        ),
        observed_candidate_count=observed_candidate_count,
        emitted_intent_count=len(intents),
        candidate_signal_limit_exceeded=candidate_signal_limit_exceeded,
        intent_limit_exceeded=intent_limit_exceeded,
        reason_codes=tuple(reason_codes),
    )
    return TaskDecomposition(intent_graph=intent_graph, diagnostics=diagnostics)


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
