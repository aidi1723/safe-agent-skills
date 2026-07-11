"""Pure inference and application of explicit intent dependencies."""

from __future__ import annotations

import dataclasses
import re
from typing import TYPE_CHECKING, Iterable, Sequence

from .intent import IntentRelation, SEMICOLON_WORKFLOW_TRANSITIONS
from .intent_evidence import IntentEvidence, validate_intent_evidence
from .intent_source import bound_task_text

if TYPE_CHECKING:
    from .intent import Intent


_LEGACY_PARALLEL_RE = re.compile(r"\bin\s+parallel\b|\bparallel\b|同时|并行", re.IGNORECASE)
_LEGACY_FIRST_THEN_RE = re.compile(
    r"(?:\bthen\b|先[\s\S]*再)", re.IGNORECASE
)
_LEGACY_BEFORE_RE = re.compile(r"\bbefore\b", re.IGNORECASE)
_LEGACY_PREFIX_BEFORE_RE = re.compile(r"^\s*before\b|^\s*.+前\s*[,，]", re.IGNORECASE)
_LEGACY_CHINESE_PRECEDES_RE = re.compile(r"先于")
_LEGACY_ORDER_LEAD_IN_RE = re.compile(
    r"\b(?:workstream|workflow|execution)\s+order\b|"
    r"\bin\s+(?:this\s+)?order\b|"
    r"\b(?:ordered\s+)?(?:workflow\s+)?steps?\s*:|"
    r"(?:工作流|流程|执行)顺序|步骤\s*[:：]",
    re.IGNORECASE,
)
_LEGACY_PREFIX_COMPLETION_RE = re.compile(
    r"^\s*(?:after|once)\b|^待.+(?:完成|验证通过)后|^在.+(?:完成|验证通过)后",
    re.IGNORECASE,
)
_LEGACY_INFIX_COMPLETION_RE = re.compile(
    r"\bafter\s+(?:"
    r"(?:complet(?:e|ing)|verif(?:y|ying|ication)|review(?:ing)?)\b|"
    r"approval\s+of\s+(?:the\s+)?(?:pr|pull\s+request)\b|"
    r"(?:the\s+)?(?:pr|pull\s+request)\s+is\s+approved\b)",
    re.IGNORECASE,
)
_LEGACY_CHINESE_TARGET_FIRST_APPROVAL_RE = re.compile(
    r"在\s*(?:PR|拉取请求)\s*(?:审批通过|批准|审核通过)后",
    re.IGNORECASE,
)
_LEGACY_CHINESE_COMPLETION_RE = re.compile(
    r"(?:完成|验证通过|测试通过|批准|审批通过|审核通过)后(?:再)?"
)
_LEGACY_VERIFICATION_GATE_RE = re.compile(
    r"\b(?:verif(?:y|ied|ying|ication)|approv(?:ed|al))\b|"
    r"(?:验证通过|测试通过|批准|审批通过|审核通过)",
    re.IGNORECASE,
)
_LEGACY_UNKNOWN_PREFIX_GATE_RE = re.compile(
    r"^\s*(?:after|once)\s+(.+?)(?:\s+is\s+(?:complete|completed|verified|approved))?\s*[,;]",
    re.IGNORECASE,
)
_LEGACY_CHINESE_SEQUENCE_RE = re.compile(r"然后|先[\s\S]*(?:再|后)")


def infer_intent_relations(
    current_text: str,
    intents: Sequence[Intent],
    intent_evidence: tuple[IntentEvidence, ...] = (),
) -> tuple[IntentRelation, ...]:
    """Infer only dependencies stated by explicit ordering or release markers."""
    current_text = bound_task_text(current_text)
    if intent_evidence:
        from .intent import _parse_bounded_intent_source

        parsed = _parse_bounded_intent_source(current_text)
        structured_evidence = _validated_evidence(
            intent_evidence,
            intents,
            current_text,
            parsed.intent_evidence,
        )
        if structured_evidence is None:
            return ()
        return parsed.dependency_relations
    return _infer_legacy_relations(current_text, intents)


def _infer_legacy_relations(
    current_text: str, intents: Sequence[Intent]
) -> tuple[IntentRelation, ...]:
    """Compatibility inference for manual graphs without canonical evidence."""
    if len(intents) < 2:
        return ()

    structured_evidence: tuple[IntentEvidence, ...] = ()
    relations: list[IntentRelation] = []
    parallel_start = (
        next(
            (
                index
                for index, evidence in enumerate(structured_evidence)
                if evidence.relation_mode == "parallel"
            ),
            len(intents),
        )
        if structured_evidence
        else 0 if _LEGACY_PARALLEL_RE.search(current_text) else len(intents)
    )
    ordered_intents = intents[:parallel_start]

    if _LEGACY_PREFIX_BEFORE_RE.search(current_text) and len(ordered_intents) == 2:
        relations.append(
            IntentRelation(ordered_intents[1].id, ordered_intents[0].id, "before")
        )
    elif _LEGACY_CHINESE_TARGET_FIRST_APPROVAL_RE.search(current_text) and len(
        ordered_intents
    ) == 2:
        source = ordered_intents[1]
        requires_verification = _gate_requires_verification(
            structured_evidence, 1, source
        )
        relations.append(
            IntentRelation(
                source.id,
                ordered_intents[0].id,
                "verification_gate"
                if requires_verification
                else "completion_gate",
                requires_verification,
            )
        )
    elif _LEGACY_PREFIX_COMPLETION_RE.search(current_text) or _LEGACY_CHINESE_COMPLETION_RE.search(
        current_text
    ):
        _append_gate_chain(
            relations, ordered_intents, structured_evidence
        )
    elif _LEGACY_INFIX_COMPLETION_RE.search(current_text) and len(ordered_intents) == 2:
        source = ordered_intents[1]
        requires_verification = _gate_requires_verification(
            structured_evidence, 1, source
        )
        relations.append(
            IntentRelation(
                source.id,
                ordered_intents[0].id,
                "verification_gate"
                if requires_verification
                else "completion_gate",
                requires_verification,
            )
        )
    elif _LEGACY_FIRST_THEN_RE.search(current_text):
        _append_source_chain(relations, ordered_intents, "first_then")
    elif _LEGACY_BEFORE_RE.search(current_text) or _LEGACY_CHINESE_PRECEDES_RE.search(current_text):
        _append_source_chain(relations, ordered_intents, "before")
    elif structured_evidence and any(
        evidence.relation_mode == "explicit_sequence"
        for evidence in structured_evidence
    ):
        _append_source_chain(relations, ordered_intents, "explicit_sequence")
    elif _LEGACY_CHINESE_SEQUENCE_RE.search(current_text) or _LEGACY_ORDER_LEAD_IN_RE.search(
        current_text
    ):
        _append_source_chain(relations, ordered_intents, "explicit_sequence")
    elif ";" in current_text or "；" in current_text:
        _append_semicolon_relations(relations, current_text, ordered_intents)

    for target_index, target in enumerate(intents):
        if target.task_type != "open_source_release":
            continue
        target_evidence = (
            structured_evidence[target_index] if structured_evidence else None
        )
        if (
            target_evidence is not None
            and target_evidence.release_mode == "readiness"
            and target_evidence.relation_mode
            in {"single", "enumeration", "parallel"}
        ):
            continue
        for source in intents[:target_index]:
            relations.append(
                IntentRelation(source.id, target.id, "release_gate", True)
            )

    return _deduplicate_relations(relations)


def _validated_evidence(
    evidence: tuple[IntentEvidence, ...],
    intents: Sequence[Intent],
    current_text: str,
    canonical_evidence: tuple[IntentEvidence, ...],
) -> tuple[IntentEvidence, ...] | None:
    if evidence == ():
        return ()
    errors = validate_intent_evidence(
        evidence,
        tuple(intent.task_type for intent in intents),
        current_text,
    )
    if errors:
        return None
    if evidence != canonical_evidence:
        return None
    return evidence


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
    current_text = bound_task_text(current_text)
    if len(intents) != 1:
        return ()
    match = _LEGACY_UNKNOWN_PREFIX_GATE_RE.search(current_text)
    if not match:
        return ()
    reference = match.group(1).strip()
    if not reference:
        return ()
    return (f"unresolved dependency: {reference}",)


def _append_source_chain(
    relations: list[IntentRelation],
    intents: Sequence[Intent],
    reason: str,
    requires_verification: bool = False,
) -> None:
    for source, target in zip(intents, intents[1:]):
        if target.task_type != "open_source_release":
            relations.append(
                IntentRelation(
                    source.id, target.id, reason, requires_verification
                )
            )


def _append_gate_chain(
    relations: list[IntentRelation],
    intents: Sequence[Intent],
    evidence: tuple[IntentEvidence, ...],
) -> None:
    for index, (source, target) in enumerate(zip(intents, intents[1:])):
        if target.task_type == "open_source_release":
            continue
        requires_verification = _gate_requires_verification(
            evidence, index, source
        )
        relations.append(
            IntentRelation(
                source.id,
                target.id,
                "verification_gate"
                if requires_verification
                else "completion_gate",
                requires_verification,
            )
        )


def _gate_requires_verification(
    evidence: tuple[IntentEvidence, ...], index: int, intent: Intent
) -> bool:
    if evidence:
        return evidence[index].gate_mode == "verification"
    return _legacy_requires_verification(intent.summary)


def _legacy_requires_verification(text: str) -> bool:
    """Compatibility fallback used only by empty-evidence manual calls."""
    return bool(_LEGACY_VERIFICATION_GATE_RE.search(bound_task_text(text)))


def _append_semicolon_relations(
    relations: list[IntentRelation], current_text: str, intents: Sequence[Intent]
) -> None:
    explicit_order = bool(
        _LEGACY_ORDER_LEAD_IN_RE.search(current_text) or _LEGACY_FIRST_THEN_RE.search(current_text)
    )
    for source, target in zip(intents, intents[1:]):
        transition = (source.task_type, target.task_type)
        if target.task_type != "open_source_release" and (
            explicit_order or transition in SEMICOLON_WORKFLOW_TRANSITIONS
        ):
            relations.append(
                IntentRelation(source.id, target.id, "semicolon_sequence")
            )


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
