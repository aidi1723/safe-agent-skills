from __future__ import annotations

import hashlib
import json
from pathlib import Path


LIFECYCLE_VALUES = {"active_draft", "review_ready", "promoted", "superseded"}


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _catalog_bodies(catalog_root: Path) -> dict[str, Path]:
    return {
        path.parent.name: path
        for path in sorted(catalog_root.glob("*/*/SKILL.md"))
    }


def _batch_summary(items: list[dict]) -> list[dict]:
    grouped: dict[str, list[dict]] = {}
    for item in items:
        grouped.setdefault(item["batch"], []).append(item)
    summaries = []
    for batch, batch_items in sorted(grouped.items()):
        lifecycle_counts = {
            lifecycle: sum(item["lifecycle"] == lifecycle for item in batch_items)
            for lifecycle in sorted(LIFECYCLE_VALUES)
            if any(item["lifecycle"] == lifecycle for item in batch_items)
        }
        summaries.append(
            {
                "id": batch,
                "item_count": len(batch_items),
                "lifecycle_counts": lifecycle_counts,
            }
        )
    return summaries


def build_batch_index(
    batch_root: Path,
    catalog_root: Path,
    source_commit: str,
    previous_index: dict | None = None,
) -> dict:
    if not source_commit.strip():
        raise ValueError("source_commit must not be empty")
    catalog_bodies = _catalog_bodies(catalog_root)
    items = []
    for manifest_path in sorted(batch_root.glob("batch-*/*/skill.json")):
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        name = str(manifest.get("name") or manifest_path.parent.name)
        body_path = manifest_path.parent / "SKILL.md"
        if not body_path.is_file():
            continue
        canonical = catalog_bodies.get(name)
        lifecycle = "promoted" if canonical is not None else (
            "active_draft" if manifest.get("status") == "draft" else "review_ready"
        )
        source_hash = file_sha256(body_path)
        catalog_hash = file_sha256(canonical) if canonical is not None else None
        items.append(
            {
                "name": name,
                "batch": manifest_path.parent.parent.name,
                "lifecycle": lifecycle,
                "body_path": body_path.relative_to(batch_root).as_posix(),
                "canonical_path": canonical.relative_to(catalog_root).as_posix() if canonical else None,
                "source_sha256": source_hash,
                "catalog_sha256": catalog_hash,
                "content_match": canonical is not None and source_hash == catalog_hash,
                "source_commit": source_commit,
                "compacted": False,
            }
        )
    current_paths = {item["body_path"] for item in items}
    previous_items = previous_index.get("items", []) if isinstance(previous_index, dict) else []
    for previous in previous_items:
        if not isinstance(previous, dict) or not previous.get("compacted"):
            continue
        body_value = previous.get("body_path")
        canonical_value = previous.get("canonical_path")
        if not isinstance(body_value, str) or body_value in current_paths:
            continue
        if not isinstance(canonical_value, str):
            continue
        promotion_path = (batch_root / body_value).with_name("PROMOTED.md")
        canonical_path = catalog_root / canonical_value
        if not promotion_path.is_file() or not canonical_path.is_file():
            continue
        restored = dict(previous)
        restored["catalog_sha256"] = file_sha256(canonical_path)
        restored["content_match"] = restored.get("source_sha256") == restored["catalog_sha256"]
        items.append(restored)
    items.sort(key=lambda item: (item["batch"], item["name"]))
    lifecycle_counts = {
        lifecycle: sum(item["lifecycle"] == lifecycle for item in items)
        for lifecycle in sorted(LIFECYCLE_VALUES)
        if any(item["lifecycle"] == lifecycle for item in items)
    }
    return {
        "schema_version": 1,
        "item_count": len(items),
        "batch_count": len({item["batch"] for item in items}),
        "lifecycle_counts": lifecycle_counts,
        "batches": _batch_summary(items),
        "items": items,
    }


def _promotion_record(item: dict) -> str:
    return "\n".join(
        [
            f"# Promoted: {item['name']}",
            "",
            "This batch body was byte-identical to its canonical catalog body and has been compacted.",
            "",
            f"- lifecycle: `{item['lifecycle']}`",
            f"- original path: `{item['body_path']}`",
            f"- canonical path: `catalog/{item['canonical_path']}`",
            f"- source SHA-256: `{item['source_sha256']}`",
            f"- source commit: `{item['source_commit']}`",
            "",
        ]
    )


def compact_promoted_bodies(index: dict, batch_root: Path, catalog_root: Path) -> dict:
    del catalog_root
    compacted = []
    skipped = []
    for item in index.get("items", []):
        if item.get("lifecycle") != "promoted" or not item.get("content_match"):
            if item.get("lifecycle") == "promoted":
                skipped.append(item.get("name", ""))
            continue
        body_path = batch_root / item["body_path"]
        promotion_path = body_path.with_name("PROMOTED.md")
        if body_path.is_file():
            promotion_path.write_text(_promotion_record(item), encoding="utf-8")
            body_path.unlink()
        item["compacted"] = True
        compacted.append(item["name"])
    return {"compacted": sorted(compacted), "skipped": sorted(skipped)}


def validate_batch_index(index: dict, batch_root: Path, catalog_root: Path) -> list[dict]:
    issues = []
    items = index.get("items")
    if not isinstance(items, list):
        return [{"id": "batch-index-invalid-items", "path": "items"}]
    for position, item in enumerate(items):
        path = f"items/{position}"
        lifecycle = item.get("lifecycle")
        if lifecycle not in LIFECYCLE_VALUES:
            issues.append({"id": "batch-index-invalid-lifecycle", "path": path})
            continue
        body_path = batch_root / str(item.get("body_path", ""))
        canonical_value = item.get("canonical_path")
        canonical_path = catalog_root / canonical_value if isinstance(canonical_value, str) else None
        if lifecycle == "promoted":
            if canonical_path is None or not canonical_path.is_file():
                issues.append({"id": "batch-index-missing-canonical", "path": path})
                continue
            if file_sha256(canonical_path) != item.get("catalog_sha256"):
                issues.append({"id": "batch-index-catalog-hash-mismatch", "path": path})
            if item.get("compacted"):
                promotion_path = body_path.with_name("PROMOTED.md")
                if body_path.exists() or not promotion_path.is_file():
                    issues.append({"id": "batch-index-invalid-compaction", "path": path})
                elif promotion_path.read_text(encoding="utf-8") != _promotion_record(item):
                    issues.append({"id": "batch-index-promotion-record-mismatch", "path": path})
            elif not body_path.is_file():
                issues.append({"id": "batch-index-missing-body", "path": path})
        elif not body_path.is_file():
            issues.append({"id": "batch-index-missing-body", "path": path})
        if body_path.is_file() and file_sha256(body_path) != item.get("source_sha256"):
            issues.append({"id": "batch-index-source-hash-mismatch", "path": path})
    if index.get("item_count") != len(items):
        issues.append({"id": "batch-index-item-count-mismatch", "path": "item_count"})
    return issues
