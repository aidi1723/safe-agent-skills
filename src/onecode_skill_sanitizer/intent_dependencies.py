"""Pure inference and application of explicit intent dependencies."""

from __future__ import annotations

import dataclasses
from dataclasses import dataclass
import re
from typing import TYPE_CHECKING, Iterable, Sequence

if TYPE_CHECKING:
    from .intent import Intent


@dataclass(frozen=True)
class IntentRelation:
    source_id: str
    target_id: str
    reason: str


_PARALLEL_RE = re.compile(r"\bin\s+parallel\b|\bparallel\b|同时|并行", re.IGNORECASE)
_FIRST_THEN_RE = re.compile(
    r"(?:\bfirst\b[\s\S]*\bthen\b|先[\s\S]*再)", re.IGNORECASE
)
_BEFORE_RE = re.compile(r"\bbefore\b", re.IGNORECASE)
_PREFIX_COMPLETION_RE = re.compile(
    r"^\s*(?:after|once)\b|^待.+(?:完成|验证通过)后|^在.+(?:完成|验证通过)后",
    re.IGNORECASE,
)
_INFIX_COMPLETION_RE = re.compile(
    r"\bafter\s+(?:complet(?:e|ing)|verif(?:y|ying|ication)|review(?:ing)?)\b",
    re.IGNORECASE,
)
_CHINESE_COMPLETION_RE = re.compile(r"(?:完成|验证通过|测试通过)后(?:再)?")
_UNKNOWN_PREFIX_GATE_RE = re.compile(
    r"^\s*(?:after|once)\s+(.+?)(?:\s+is\s+(?:complete|completed|verified|approved))?\s*[,;]",
    re.IGNORECASE,
)


def infer_intent_relations(
    current_text: str, intents: Sequence[Intent]
) -> tuple[IntentRelation, ...]:
    """Infer only dependencies stated by explicit ordering or release markers."""
    if len(intents) < 2:
        return ()

    relations: list[IntentRelation] = []
    is_parallel = bool(_PARALLEL_RE.search(current_text))
    if not is_parallel:
        if ";" in current_text or "；" in current_text:
            _append_source_chain(relations, intents, "semicolon_sequence")
        elif _FIRST_THEN_RE.search(current_text):
            _append_source_chain(relations, intents, "first_then")
        elif _BEFORE_RE.search(current_text):
            _append_source_chain(relations, intents, "before")
        elif _PREFIX_COMPLETION_RE.search(current_text) or _CHINESE_COMPLETION_RE.search(
            current_text
        ):
            _append_source_chain(relations, intents, "completion_gate")
        elif _INFIX_COMPLETION_RE.search(current_text) and len(intents) == 2:
            relations.append(
                IntentRelation(intents[1].id, intents[0].id, "completion_gate")
            )

    for target_index, target in enumerate(intents):
        if target.task_type != "open_source_release":
            continue
        for source in intents[:target_index]:
            relations.append(IntentRelation(source.id, target.id, "release_gate"))

    return _deduplicate_relations(relations)


def apply_intent_relations(
    intents: Sequence[Intent], relations: Iterable[IntentRelation]
) -> tuple[Intent, ...]:
    """Return intents with valid inferred dependencies appended in relation order."""
    intent_ids = {intent.id for intent in intents}
    dependencies = {intent.id: list(intent.depends_on) for intent in intents}
    seen = {
        (dependency, intent.id)
        for intent in intents
        for dependency in intent.depends_on
    }
    for relation in relations:
        edge = (relation.source_id, relation.target_id)
        if (
            relation.source_id == relation.target_id
            or relation.source_id not in intent_ids
            or relation.target_id not in intent_ids
            or edge in seen
        ):
            continue
        dependencies[relation.target_id].append(relation.source_id)
        seen.add(edge)

    return tuple(
        dataclasses.replace(intent, depends_on=tuple(dependencies[intent.id]))
        for intent in intents
    )


def infer_unresolved_dependencies(
    current_text: str, intents: Sequence[Intent]
) -> tuple[str, ...]:
    """Record an explicit completion reference when no prerequisite intent exists."""
    if len(intents) != 1:
        return ()
    match = _UNKNOWN_PREFIX_GATE_RE.search(current_text)
    if not match:
        return ()
    reference = match.group(1).strip()
    if not reference:
        return ()
    return (f"unresolved dependency: {reference}",)


def _append_source_chain(
    relations: list[IntentRelation], intents: Sequence[Intent], reason: str
) -> None:
    for source, target in zip(intents, intents[1:]):
        if target.task_type != "open_source_release":
            relations.append(IntentRelation(source.id, target.id, reason))


def _deduplicate_relations(
    relations: Iterable[IntentRelation],
) -> tuple[IntentRelation, ...]:
    seen: set[tuple[str, str]] = set()
    result: list[IntentRelation] = []
    for relation in relations:
        edge = (relation.source_id, relation.target_id)
        if relation.source_id == relation.target_id or edge in seen:
            continue
        seen.add(edge)
        result.append(relation)
    return tuple(result)
