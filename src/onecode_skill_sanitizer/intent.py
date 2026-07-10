"""Deterministic task normalization and multi-intent decomposition."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import re
from typing import Any

from .router import build_task_profile, split_current_intent_text


_LIST_ITEM_RE = re.compile(
    r"(?m)^\s*(?:\d+[.)、]|[-*+]\s*\[[ xX]\]\s+|[-*+]\s+)\s*(.+?)\s*$"
)
_CLAUSE_SEPARATOR_RE = re.compile(r"\s*(?:[；;]|，?同时|，?以及|\band\b)\s*", re.IGNORECASE)
_RELEASE_BOUNDARY_RE = re.compile(
    r"(?:验证(?:通过)?|测试通过|完成|批准|审批通过|审核通过)后(?:再)?(?:发布|上线|推送)"
)
_RELEASE_RE = re.compile(
    r"(?:发布|上线|推送|release|publish|开源发布)",
    re.IGNORECASE,
)
_CODE_REVIEW_LIFECYCLE_RE = re.compile(
    r"(?:审查|审核|review).*(?:代码|code).*(?:测试|test).*(?:合并\s*(?:pr|pull request)|merge)",
    re.IGNORECASE,
)


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
        intent_ids = {intent.id for intent in self.intents}
        dependencies = {intent.id: intent.depends_on for intent in self.intents}

        for intent in self.intents:
            for dependency in intent.depends_on:
                if dependency not in intent_ids:
                    errors.append(f"intent {intent.id} depends on unknown intent {dependency}")

        cycle = _find_dependency_cycle(dependencies, intent_ids)
        if cycle:
            errors.append(f"intent dependency cycle detected: {' -> '.join(cycle)}")
        return errors


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
    if _CODE_REVIEW_LIFECYCLE_RE.search(text):
        return [text]

    list_items = [match.group(1).strip() for match in _LIST_ITEM_RE.finditer(text)]
    if len(list_items) > 1:
        return list_items

    release_match = _RELEASE_BOUNDARY_RE.search(text)
    release_split = [text]
    if release_match and release_match.start() > 0:
        release_split = [text[: release_match.start()], text[release_match.start() :]]
    clauses: list[str] = []
    for part in release_split:
        clauses.extend(_CLAUSE_SEPARATOR_RE.split(part))
    return [clause.strip(" \t\n,，。") for clause in clauses if clause.strip(" \t\n,，。")]


def classify_intent(clause: str, index: int) -> Intent:
    profile = build_task_profile(clause)
    task_type = profile["task_type"]
    required_artifacts = tuple(profile["artifact_types"])
    risk_flags = tuple(profile["risk_flags"])
    if _RELEASE_RE.search(clause):
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


def decompose_task(task: str) -> IntentGraph:
    intents: list[Intent] = []
    for index, clause in enumerate(split_task_clauses(task), start=1):
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
    return IntentGraph(intents=tuple(intents), unresolved_dependencies=())


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
