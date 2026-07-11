"""Pure inference and application of explicit intent dependencies."""

from __future__ import annotations

import dataclasses
import re
from typing import TYPE_CHECKING, Iterable, Sequence

from .intent import IntentRelation
from .routing_profiles import is_release_readiness_request

if TYPE_CHECKING:
    from .intent import Intent


_PARALLEL_RE = re.compile(r"\bin\s+parallel\b|\bparallel\b|同时|并行", re.IGNORECASE)
_FIRST_THEN_RE = re.compile(
    r"(?:\bthen\b|先[\s\S]*再)", re.IGNORECASE
)
_BEFORE_RE = re.compile(r"\bbefore\b", re.IGNORECASE)
_PREFIX_BEFORE_RE = re.compile(r"^\s*before\b|^\s*.+前\s*[,，]", re.IGNORECASE)
_CHINESE_PRECEDES_RE = re.compile(r"先于")
_ORDER_LEAD_IN_RE = re.compile(
    r"\b(?:workstream|workflow|execution)\s+order\b|"
    r"\bin\s+(?:this\s+)?order\b|"
    r"\b(?:ordered\s+)?(?:workflow\s+)?steps?\s*:|"
    r"(?:工作流|流程|执行)顺序|步骤\s*[:：]",
    re.IGNORECASE,
)
_PREFIX_COMPLETION_RE = re.compile(
    r"^\s*(?:after|once)\b|^待.+(?:完成|验证通过)后|^在.+(?:完成|验证通过)后",
    re.IGNORECASE,
)
_INFIX_COMPLETION_RE = re.compile(
    r"\bafter\s+(?:"
    r"(?:complet(?:e|ing)|verif(?:y|ying|ication)|review(?:ing)?)\b|"
    r"approval\s+of\s+(?:the\s+)?(?:pr|pull\s+request)\b|"
    r"(?:the\s+)?(?:pr|pull\s+request)\s+is\s+approved\b)",
    re.IGNORECASE,
)
_CHINESE_TARGET_FIRST_APPROVAL_RE = re.compile(
    r"在\s*(?:PR|拉取请求)\s*(?:审批通过|批准|审核通过)后",
    re.IGNORECASE,
)
_CHINESE_COMPLETION_RE = re.compile(
    r"(?:完成|验证通过|测试通过|批准|审批通过|审核通过)后(?:再)?"
)
_VERIFICATION_GATE_RE = re.compile(
    r"\b(?:verif(?:y|ied|ying|ication)|approv(?:ed|al))\b|"
    r"(?:验证通过|测试通过|批准|审批通过|审核通过)",
    re.IGNORECASE,
)
_UNKNOWN_PREFIX_GATE_RE = re.compile(
    r"^\s*(?:after|once)\s+(.+?)(?:\s+is\s+(?:complete|completed|verified|approved))?\s*[,;]",
    re.IGNORECASE,
)
_PLUS_ENUMERATION_RE = re.compile(r"\+|＋")
_CHINESE_SEQUENCE_RE = re.compile(r"然后|先[\s\S]*(?:再|后)")


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
def infer_intent_relations(
    current_text: str, intents: Sequence[Intent]
) -> tuple[IntentRelation, ...]:
    """Infer only dependencies stated by explicit ordering or release markers."""
    if len(intents) < 2:
        return ()

    relations: list[IntentRelation] = []
    parallel_start = _parallel_start_index(current_text, intents)
    ordered_intents = intents[:parallel_start]

    if _PREFIX_BEFORE_RE.search(current_text) and len(ordered_intents) == 2:
        relations.append(
            IntentRelation(ordered_intents[1].id, ordered_intents[0].id, "before")
        )
    elif _CHINESE_TARGET_FIRST_APPROVAL_RE.search(current_text) and len(
        ordered_intents
    ) == 2:
        source = ordered_intents[1]
        requires_verification = _requires_verification(source.summary)
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
    elif _PREFIX_COMPLETION_RE.search(current_text) or _CHINESE_COMPLETION_RE.search(
        current_text
    ):
        _append_gate_chain(relations, ordered_intents)
    elif _INFIX_COMPLETION_RE.search(current_text) and len(ordered_intents) == 2:
        source = ordered_intents[1]
        requires_verification = _requires_verification(source.summary)
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
    elif _FIRST_THEN_RE.search(current_text):
        _append_source_chain(relations, ordered_intents, "first_then")
    elif _BEFORE_RE.search(current_text) or _CHINESE_PRECEDES_RE.search(current_text):
        _append_source_chain(relations, ordered_intents, "before")
    elif _CHINESE_SEQUENCE_RE.search(current_text):
        _append_source_chain(relations, ordered_intents, "explicit_sequence")
    elif _ORDER_LEAD_IN_RE.search(current_text):
        _append_source_chain(relations, ordered_intents, "explicit_sequence")
    elif ";" in current_text or "；" in current_text:
        _append_semicolon_relations(relations, current_text, ordered_intents)

    for target_index, target in enumerate(intents):
        if target.task_type != "open_source_release":
            continue
        if _is_plain_release_readiness_enumeration(current_text, target):
            continue
        for source in intents[:target_index]:
            relations.append(
                IntentRelation(source.id, target.id, "release_gate", True)
            )

    return _deduplicate_relations(relations)


def _is_plain_release_readiness_enumeration(
    current_text: str, target: Intent
) -> bool:
    if not (
        _PLUS_ENUMERATION_RE.search(current_text)
        and is_release_readiness_request(target.summary)
    ):
        return False
    return not any(
        pattern.search(current_text)
        for pattern in (
            _FIRST_THEN_RE,
            _BEFORE_RE,
            _CHINESE_PRECEDES_RE,
            _ORDER_LEAD_IN_RE,
            _PREFIX_COMPLETION_RE,
            _INFIX_COMPLETION_RE,
            _CHINESE_TARGET_FIRST_APPROVAL_RE,
            _CHINESE_COMPLETION_RE,
            _CHINESE_SEQUENCE_RE,
        )
    )


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
    relations: list[IntentRelation], intents: Sequence[Intent]
) -> None:
    for source, target in zip(intents, intents[1:]):
        if target.task_type == "open_source_release":
            continue
        requires_verification = _requires_verification(source.summary)
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


def _requires_verification(text: str) -> bool:
    return bool(_VERIFICATION_GATE_RE.search(text))


def _append_semicolon_relations(
    relations: list[IntentRelation], current_text: str, intents: Sequence[Intent]
) -> None:
    explicit_order = bool(
        _ORDER_LEAD_IN_RE.search(current_text) or _FIRST_THEN_RE.search(current_text)
    )
    for source, target in zip(intents, intents[1:]):
        transition = (source.task_type, target.task_type)
        if target.task_type != "open_source_release" and (
            explicit_order or transition in SEMICOLON_WORKFLOW_TRANSITIONS
        ):
            relations.append(
                IntentRelation(source.id, target.id, "semicolon_sequence")
            )


def _parallel_start_index(current_text: str, intents: Sequence[Intent]) -> int:
    marker = _PARALLEL_RE.search(current_text)
    if marker is None:
        return len(intents)
    if not current_text[: marker.start()].strip(" \t\n,，;；:："):
        return 0

    suffix = current_text[marker.end() :].casefold()
    for index, intent in enumerate(intents):
        anchor = _PARALLEL_RE.sub("", intent.summary).strip(" \t\n,，;；:：")
        if anchor and anchor.casefold() in suffix:
            return index
    return len(intents)


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
