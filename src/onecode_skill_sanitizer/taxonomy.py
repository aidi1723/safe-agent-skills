from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Taxonomy:
    category: str
    subcategory: str
    task_intent: str
    artifact_type: str
    collection_priority: str
    classified: bool = True

    def to_json(self) -> dict[str, str]:
        return {
            "category": self.category,
            "subcategory": self.subcategory,
            "task_intent": self.task_intent,
            "artifact_type": self.artifact_type,
            "collection_priority": self.collection_priority,
        }


CATEGORY_DEFAULTS = {
    "design": ("design.ui", "design or improve user interfaces", "interface", "P0"),
    "code": ("code.edit", "write or change source code", "code", "P0"),
    "engineering": ("engineering.build", "build or operate software systems", "deployment", "P0"),
    "security": ("security.review", "review and harden safety boundaries", "audit", "P0"),
    "office": ("office.report", "process office documents", "document", "P0"),
    "execution": ("execution.pipeline", "run a bounded workflow", "workflow", "P0"),
    "research": ("research.web", "gather and verify information", "report", "P1"),
    "data": ("data.analysis", "analyze structured data", "dataset", "P1"),
    "business": ("business.ops", "support business operations", "workflow", "P2"),
    "content": ("content.write", "create or edit content", "content", "P1"),
    "commerce": ("commerce.listing", "prepare commerce workflows", "listing", "P1"),
    "media": ("media.image", "create or process media", "asset", "P2"),
    "compliance": ("compliance.policy", "support compliance review", "policy", "P2"),
    "ai": ("ai.prompt", "design or evaluate AI workflows", "prompt", "P1"),
    "vertical": ("vertical.education", "support a domain workflow", "workflow", "P3"),
}

TEXT_SIGNALS = [
    ("office", "office.pdf", "process PDF documents safely", "document", "P0", ("pdf", "docx", "spreadsheet", "slides", "report")),
    ("design", "design.ui", "design or improve user interfaces", "interface", "P0", ("ui", "frontend", "dashboard", "landing", "visual")),
    ("code", "code.debug", "debug and improve source code", "code", "P0", ("code", "bug", "test", "refactor", "python", "typescript")),
    ("engineering", "engineering.build", "build or operate software systems", "deployment", "P0", ("deploy", "docker", "ci", "build", "release")),
    ("security", "security.review", "review safety and security risks", "audit", "P0", ("security", "secret", "sandbox", "permission", "injection")),
    ("execution", "execution.pipeline", "run a bounded workflow", "workflow", "P0", ("browser", "form", "automation", "publish", "batch")),
    ("research", "research.source", "gather and verify information", "report", "P1", ("research", "citation", "source", "paper", "news")),
    ("ai", "ai.prompt", "design or evaluate AI workflows", "prompt", "P1", ("prompt", "agent", "model", "eval", "rag")),
]


def _keyword_present(haystack: str, keyword: str) -> bool:
    return re.search(rf"(?<![a-z0-9_]){re.escape(keyword)}(?![a-z0-9_])", haystack) is not None


def taxonomy_from_manifest(source_dir: Path) -> Taxonomy | None:
    manifest_path = source_dir / "skill.json"
    if not manifest_path.exists():
        return None
    try:
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    taxonomy = payload.get("taxonomy")
    if not isinstance(taxonomy, dict):
        return None
    category = taxonomy.get("category")
    subcategory = taxonomy.get("subcategory")
    priority = taxonomy.get("collection_priority")
    if category not in CATEGORY_DEFAULTS or not isinstance(subcategory, str) or priority not in {"P0", "P1", "P2", "P3"}:
        return None
    return Taxonomy(
        category=category,
        subcategory=subcategory,
        task_intent=str(taxonomy.get("task_intent", CATEGORY_DEFAULTS[category][1])),
        artifact_type=str(taxonomy.get("artifact_type", CATEGORY_DEFAULTS[category][2])),
        collection_priority=priority,
    )


def classify_skill(name: str, text: str) -> Taxonomy:
    haystack = f"{name}\n{text}".lower()
    best = None
    best_score = 0
    for category, subcategory, intent, artifact, priority, keywords in TEXT_SIGNALS:
        score = sum(1 for keyword in keywords if _keyword_present(haystack, keyword))
        if score > best_score:
            best = (category, subcategory, intent, artifact, priority)
            best_score = score

    if best is None:
        category = "execution"
        subcategory, intent, artifact, priority = CATEGORY_DEFAULTS[category]
        return Taxonomy(category, subcategory, intent, artifact, priority, classified=False)

    category, subcategory, intent, artifact, priority = best
    return Taxonomy(category, subcategory, intent, artifact, priority)
