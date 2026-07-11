"""Deterministic task normalization and multi-intent decomposition."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import re
from typing import Any

from .intent_spans import (
    MAX_CANDIDATE_SIGNALS,
    MAX_EMITTED_INTENTS,
    SpanDecomposition,
    split_profile_enumeration,
)
from .router import build_profile_for_task_type, build_task_profile, split_current_intent_text


_LIST_MARKER_RE = re.compile(
    r"^\s*(?:\d+[.)、]|[-*+]\s*\[[ xX]\]|[-*+])\s+(.+?)\s*$"
)
_CLAUSE_SEPARATOR_RE = re.compile(r"\s*(?:[；;]|，?同时|，?以及|\bthen\b)\s*", re.IGNORECASE)
_RELEASE_BOUNDARY_RE = re.compile(
    r"(?:验证(?:通过)?|测试通过|完成|批准|审批通过|审核通过)后(?:再)?(?:发布|上线|推送)"
)
_CHINESE_RELEASE_ACTION_RE = re.compile(
    r"(?:发布|上线|推送)(?:更新|结果|版本|新版本|软件包|包|项目|网站|应用|代码|变更|到\S+)"
)
_ENGLISH_RELEASE_ACTION_RE = re.compile(
    r"\b(?:publish|release)\b\s+(?:the\s+|an?\s+)?(?:update|results?|package|version|project|website|app|code|changes?)\b",
    re.IGNORECASE,
)
_EXPLICIT_PUSH_ACTION_RE = re.compile(
    r"推送\s*github|\bpush\s+(?:to\s+github|the\s+repository)\b",
    re.IGNORECASE,
)
_RELEASE_NEGATION_RE = re.compile(
    r"(?:不要|不得|禁止|无需|暂不|先不|别|不)\s*(?:发布|上线|推送)|\b(?:do\s+not|don't|never)\s+(?:publish|release|push)\b",
    re.IGNORECASE,
)
_RELEASE_PRECONDITION_RE = re.compile(
    r"(?:发布|上线|推送)前|推送\s*github\s*前|"
    r"\bbefore\s+(?:publishing|releasing|pushing|publish|release|push)\b",
    re.IGNORECASE,
)
_NON_ACTION_RELEASE_TERM_RE = re.compile(
    r"(?:不要|不得|禁止|无需|暂不|先不|别|不)\s*"
    r"(?:发布|上线|推送)(?:\s*github)?|"
    r"推送\s*github\s*前|"
    r"(?:发布|上线|推送)前|"
    r"\brelease\s+notes\b|\bpublishable\b|"
    r"\b(?:do\s+not|don't|never)\s+(?:publish|release|push)"
    r"(?:\s+to\s+github|\s+the\s+repository)?\b|"
    r"\bbefore\s+(?:publishing|releasing|pushing|publish|release|push)"
    r"(?:\s+to\s+github|\s+the\s+repository)?\b",
    re.IGNORECASE,
)
_INTENT_ID_RE = re.compile(r"^i[1-9][0-9]*$")
_INTENT_SOURCES = {"deterministic", "semantic", "hybrid"}


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
class IntentGraph:
    intents: tuple[Intent, ...]
    unresolved_dependencies: tuple[str, ...]

    def to_json(self) -> dict[str, Any]:
        return _json_compatible(asdict(self))

    def validate(self) -> list[str]:
        errors: list[str] = []
        if not self.intents:
            return ["intent graph is empty"]

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


def classify_intent(clause: str, index: int) -> Intent:
    release_action = _is_release_action(clause)
    routing_clause = clause if release_action else _routing_clause_without_non_action_release_terms(clause)
    profile = build_task_profile(routing_clause)
    lowered_clause = routing_clause.lower()
    if "design system" in lowered_clause and "component states" in lowered_clause:
        profile = build_profile_for_task_type(
            routing_clause, "design_md_system_governance"
        )
    task_type = profile["task_type"]
    required_artifacts = tuple(profile["artifact_types"])
    risk_flags = tuple(profile["risk_flags"])
    if release_action:
        task_type = "open_source_release"
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
        confidence=_deterministic_confidence(profile["matched_signal_score"], task_type),
    )


def decompose_task_detailed(task: str) -> TaskDecomposition:
    broad_clauses = split_task_clauses(task)
    clauses: list[str] = []
    observed_candidate_count = 0
    candidate_signal_limit_exceeded = False
    intent_limit_exceeded = False
    used_profile_spans = False
    for clause_index, broad_clause in enumerate(broad_clauses):
        if candidate_signal_limit_exceeded:
            decomposition = SpanDecomposition(
                clauses=(broad_clause,),
                observed_candidate_count=0,
                candidate_signal_limit_exceeded=True,
                intent_limit_exceeded=False,
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
            clauses.extend(decomposition.clauses[:remaining])
        if (
            len(clauses) >= MAX_EMITTED_INTENTS
            and clause_index < len(broad_clauses) - 1
        ):
            intent_limit_exceeded = True
            break

    intents: list[Intent] = []
    for index, clause in enumerate(clauses, start=1):
        intent = classify_intent(clause, index)
        if intent.task_type == "open_source_release" and intents:
            intent = Intent(
                id=intent.id,
                summary=intent.summary,
                task_type=intent.task_type,
                required_artifacts=intent.required_artifacts,
                risk_flags=intent.risk_flags,
                depends_on=tuple(previous.id for previous in intents),
                source=intent.source,
                confidence=intent.confidence,
            )
        intents.append(intent)
    intent_graph = IntentGraph(intents=tuple(intents), unresolved_dependencies=())
    reason_codes: list[str] = []
    if candidate_signal_limit_exceeded:
        reason_codes.append("candidate_signal_limit_exceeded")
    if intent_limit_exceeded:
        reason_codes.append("intent_limit_exceeded")
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


def _is_release_action(clause: str) -> bool:
    if _RELEASE_NEGATION_RE.search(clause) or _RELEASE_PRECONDITION_RE.search(clause):
        return False
    return bool(
        _RELEASE_BOUNDARY_RE.search(clause)
        or _CHINESE_RELEASE_ACTION_RE.search(clause)
        or _ENGLISH_RELEASE_ACTION_RE.search(clause)
        or _EXPLICIT_PUSH_ACTION_RE.search(clause)
    )


def _routing_clause_without_non_action_release_terms(clause: str) -> str:
    return _NON_ACTION_RELEASE_TERM_RE.sub(" ", clause).strip(" \t\n,，。")


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
