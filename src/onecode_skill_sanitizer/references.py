from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from .validation import REFERENCE_ADOPTION_STATUSES
from .validation import REFERENCE_REQUIRED_FIELDS
from .validation import SOURCE_TYPE_VALUES
from .validation import add_issue


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def validate_external_references(references_path: Path) -> dict:
    issues: list[dict] = []
    try:
        payload = json.loads(references_path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {
            "schema_version": 1,
            "generated_at": utc_now(),
            "status": "failed",
            "reference_count": 0,
            "issues": [
                {
                    "id": "reference-index-missing",
                    "severity": "high",
                    "path": references_path.as_posix(),
                }
            ],
        }
    except json.JSONDecodeError as exc:
        return {
            "schema_version": 1,
            "generated_at": utc_now(),
            "status": "failed",
            "reference_count": 0,
            "issues": [
                {
                    "id": "reference-invalid-json",
                    "severity": "critical",
                    "path": references_path.as_posix(),
                    "summary": str(exc),
                }
            ],
        }

    if payload.get("schema_version") != 1:
        add_issue(issues, "reference-invalid-version", references_path, "schema_version must be 1")
    references = payload.get("references")
    if not isinstance(references, list):
        add_issue(issues, "reference-invalid-list", references_path, "references must be an array")
        references = []
    declared_count = payload.get("reference_count")
    if declared_count is not None and declared_count != len(references):
        issues.append(
            {
                "id": "reference-count-mismatch",
                "severity": "medium",
                "path": references_path.as_posix(),
                "expected": len(references),
                "actual": declared_count,
            }
        )

    seen_names = set()
    for index, reference in enumerate(references):
        reference_path = f"{references_path.as_posix()}#/references/{index}"
        if not isinstance(reference, dict):
            add_issue(issues, "reference-invalid-entry", reference_path, "reference entry must be an object")
            continue
        for field in REFERENCE_REQUIRED_FIELDS:
            value = reference.get(field)
            if value in (None, ""):
                issues.append(
                    {
                        "id": "reference-missing-field",
                        "severity": "high",
                        "path": reference_path,
                        "field": field,
                    }
                )
        name = reference.get("name")
        if isinstance(name, str):
            if name in seen_names:
                issues.append(
                    {
                        "id": "reference-duplicate-name",
                        "severity": "medium",
                        "path": reference_path,
                        "name": name,
                    }
                )
            seen_names.add(name)
        source_url = reference.get("source_url")
        if isinstance(source_url, str) and not source_url.startswith(("https://", "http://")):
            issues.append(
                {
                    "id": "reference-invalid-source-url",
                    "severity": "high",
                    "path": reference_path,
                    "source_url": source_url,
                }
            )
        source_type = reference.get("source_type")
        if isinstance(source_type, str) and source_type not in SOURCE_TYPE_VALUES:
            issues.append(
                {
                    "id": "reference-invalid-source-type",
                    "severity": "high",
                    "path": reference_path,
                    "source_type": source_type,
                }
            )
        adoption_status = reference.get("adoption_status")
        if isinstance(adoption_status, str) and adoption_status not in REFERENCE_ADOPTION_STATUSES:
            issues.append(
                {
                    "id": "reference-invalid-adoption-status",
                    "severity": "high",
                    "path": reference_path,
                    "adoption_status": adoption_status,
                }
            )
        for field in ["claimed_capabilities", "taxonomy_categories"]:
            value = reference.get(field)
            if not isinstance(value, list) or not value or not all(isinstance(item, str) and item for item in value):
                issues.append(
                    {
                        "id": "reference-invalid-list-field",
                        "severity": "high",
                        "path": reference_path,
                        "field": field,
                    }
                )
        if reference.get("metadata_only") is not True:
            issues.append(
                {
                    "id": "reference-not-metadata-only",
                    "severity": "critical",
                    "path": reference_path,
                    "name": name or "",
                }
            )

    return {
        "schema_version": 1,
        "generated_at": utc_now(),
        "status": "failed" if issues else "ok",
        "reference_count": len(references),
        "issues": issues,
    }
