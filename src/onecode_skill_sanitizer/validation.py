from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path


STATUS_VALUES = {"quarantined", "review_required", "trusted", "rejected", "disabled"}
RISK_LEVEL_VALUES = {"low", "medium", "high", "critical"}
SOURCE_TYPE_VALUES = {"local_folder", "archive", "git", "community_index", "github_reference", "web_reference"}
SOURCE_USAGE_VALUES = {"source_import", "reference_only", "local_authoring"}
SOURCE_DEFAULT_USAGE_BY_TYPE = {
    "archive": "source_import",
    "community_index": "source_import",
    "git": "source_import",
    "github_reference": "reference_only",
    "local_folder": "local_authoring",
    "web_reference": "reference_only",
}
SOURCE_USAGE_BY_TYPE = {
    "archive": {"source_import"},
    "community_index": {"source_import"},
    "git": {"source_import"},
    "github_reference": {"reference_only"},
    "local_folder": {"local_authoring"},
    "web_reference": {"reference_only"},
}
SOURCE_REQUIRED_FIELDS = ["type", "usage", "path", "url", "author", "license", "reference", "collected_by", "captured_at"]
SOURCE_PROVENANCE_FIELDS = ["url", "author", "license", "reference", "collected_by"]
SOURCE_IMPORT_CAPTURE_FIELDS = [
    "upstream_url",
    "upstream_ref_type",
    "upstream_ref",
    "captured_at",
    "license_snapshot",
    "upstream_sha256",
    "content_path",
    "capture_method",
]
SOURCE_IMPORT_REF_TYPE_VALUES = {"archive", "branch", "commit", "release", "tag"}
HASH_PATTERN = re.compile(r"^[0-9a-f]{64}$")
REFERENCE_REQUIRED_FIELDS = [
    "name",
    "source_url",
    "source_type",
    "author",
    "license",
    "captured_at",
    "project_category",
    "claimed_capabilities",
    "taxonomy_categories",
    "runtime_permission_notes",
    "adoption_status",
    "review_notes",
    "metadata_only",
]
REFERENCE_ADOPTION_STATUSES = {"reference_only", "candidate", "rejected", "converted"}
FILESYSTEM_SCOPE_VALUES = {"workspace_only", "read_only_workspace", "none"}
NETWORK_SCOPE_VALUES = {"none", "approved_hosts", "onecode_api_only"}
CONTRACT_STAGE_VALUES = {"preflight", "source", "planning", "review", "execution", "verification"}
CONTRACT_CAPABILITY_PATTERN = re.compile(r"^[a-z][a-z0-9_]*(\.[a-z][a-z0-9_]*)+$")
CONTRACT_ARTIFACT_PATTERN = re.compile(r"^[a-z][a-z0-9_]{1,80}$")
CONTRACT_APPROVAL_CLASS_VALUES = {
    "browser_automation",
    "network_access",
    "publication",
    "shell_execution",
    "dependency_install",
    "paid_provider",
    "destructive_action",
}
CONTRACT_RETRY_POLICY_VALUES = {"host_decides", "never", "safe_once"}
DISALLOWED_TOOL_VALUES = {
    "account",
    "browser",
    "connector",
    "filesystem",
    "network",
    "production",
    "shell",
}


def _is_exact_string_enum(value: object, allowed: set[str]) -> bool:
    return type(value) is str and value in allowed


def text_sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def auxiliary_content_sha256(skill_dir: Path) -> str | None:
    files = []
    for directory in ["references", "scripts"]:
        root = skill_dir / directory
        if root.is_dir():
            files.extend(path for path in root.rglob("*") if path.is_file())
    if not files:
        return None
    digest = hashlib.sha256()
    for path in sorted(files, key=lambda item: item.relative_to(skill_dir).as_posix()):
        digest.update(path.relative_to(skill_dir).as_posix().encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def canonical_json_sha256(payload: dict) -> str:
    return text_sha256(json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False))


def manifest_payload_for_hash(manifest: dict) -> dict:
    payload = json.loads(json.dumps(manifest, sort_keys=True))
    hashes = payload.get("hashes")
    if isinstance(hashes, dict):
        hashes.pop("manifest_sha256", None)
    return payload


def manifest_sha256(manifest: dict) -> str:
    return canonical_json_sha256(manifest_payload_for_hash(manifest))


def seal_manifest(manifest: dict) -> dict:
    manifest.setdefault("hashes", {})["manifest_sha256"] = manifest_sha256(manifest)
    return manifest


def add_issue(issues: list[dict], issue_id: str, path: Path | str, summary: str, severity: str = "high") -> None:
    issues.append(
        {
            "id": issue_id,
            "severity": severity,
            "path": path.as_posix() if isinstance(path, Path) else str(path),
            "summary": summary,
        }
    )


def validate_hashes(payload: dict, path: Path, issues: list[dict]) -> None:
    if not isinstance(payload, dict):
        add_issue(issues, "schema-invalid-hash-owner", path, "hash owner must be an object")
        return
    hashes = payload.get("hashes")
    if not isinstance(hashes, dict):
        add_issue(issues, "schema-invalid-hashes", path, "hashes must be an object")
        return
    for key in ["source_sha256", "sanitized_sha256"]:
        value = hashes.get(key)
        if not isinstance(value, str) or not HASH_PATTERN.fullmatch(value):
            add_issue(issues, "schema-invalid-hash", path, f"{key} must be a 64 character lowercase sha256 hex string")
    manifest_hash = hashes.get("manifest_sha256")
    if manifest_hash is None:
        add_issue(issues, "schema-missing-manifest-hash", path, "hashes.manifest_sha256 is required")
    elif not isinstance(manifest_hash, str) or not HASH_PATTERN.fullmatch(manifest_hash):
        add_issue(issues, "schema-invalid-hash", path, "manifest_sha256 must be a 64 character lowercase sha256 hex string")


def validate_manifest_integrity(payload: dict, path: Path, issues: list[dict]) -> None:
    if not isinstance(payload, dict):
        add_issue(issues, "schema-invalid-manifest", path, "manifest must be an object")
        return
    hashes = payload.get("hashes")
    if not isinstance(hashes, dict):
        return
    expected = hashes.get("manifest_sha256")
    if not isinstance(expected, str) or not HASH_PATTERN.fullmatch(expected):
        return
    actual = manifest_sha256(payload)
    if actual != expected:
        add_issue(issues, "schema-manifest-hash-mismatch", path, "hashes.manifest_sha256 does not match manifest content", "critical")


def validate_source(payload: dict, path: Path, issues: list[dict]) -> None:
    if not isinstance(payload, dict):
        add_issue(issues, "schema-invalid-source-owner", path, "source owner must be an object")
        return
    source = payload.get("source")
    if not isinstance(source, dict):
        add_issue(issues, "schema-invalid-source", path, "source must be an object")
        return
    for field in SOURCE_REQUIRED_FIELDS:
        value = source.get(field)
        if not isinstance(value, str) or not value:
            add_issue(issues, "schema-missing-source-field", path, f"source.{field} is required")
    source_type = source.get("type")
    if isinstance(source_type, str) and source_type not in SOURCE_TYPE_VALUES:
        add_issue(issues, "schema-invalid-source-type", path, f"source.type {source_type!r} is not supported")
    source_usage = source.get("usage")
    if isinstance(source_usage, str) and source_usage not in SOURCE_USAGE_VALUES:
        add_issue(issues, "schema-invalid-source-usage", path, f"source.usage {source_usage!r} is not supported")
    if isinstance(source_type, str) and isinstance(source_usage, str):
        expected_usages = SOURCE_USAGE_BY_TYPE.get(source_type)
        if expected_usages is not None and source_usage not in expected_usages:
            allowed = ", ".join(sorted(expected_usages))
            add_issue(
                issues,
                "schema-invalid-source-usage-for-type",
                path,
                f"source.type {source_type!r} requires source.usage to be one of: {allowed}",
            )
    if source_usage == "source_import":
        capture = source.get("capture")
        if not isinstance(capture, dict):
            add_issue(
                issues,
                "schema-missing-source-import-capture",
                path,
                "source.capture is required when source.usage is source_import",
            )
            return
        for field in SOURCE_IMPORT_CAPTURE_FIELDS:
            value = capture.get(field)
            if not isinstance(value, str) or not value:
                add_issue(
                    issues,
                    "schema-invalid-source-import-capture",
                    path,
                    f"source.capture.{field} is required for source_import",
                )
        upstream_url = capture.get("upstream_url")
        if isinstance(upstream_url, str) and upstream_url and not upstream_url.startswith(("https://", "http://")):
            add_issue(
                issues,
                "schema-invalid-source-import-capture",
                path,
                "source.capture.upstream_url must be an http or https URL",
            )
        ref_type = capture.get("upstream_ref_type")
        if isinstance(ref_type, str) and ref_type and ref_type not in SOURCE_IMPORT_REF_TYPE_VALUES:
            allowed = ", ".join(sorted(SOURCE_IMPORT_REF_TYPE_VALUES))
            add_issue(
                issues,
                "schema-invalid-source-import-capture",
                path,
                f"source.capture.upstream_ref_type must be one of: {allowed}",
            )
        upstream_sha = capture.get("upstream_sha256")
        if isinstance(upstream_sha, str) and upstream_sha and not HASH_PATTERN.fullmatch(upstream_sha):
            add_issue(
                issues,
                "schema-invalid-source-import-capture",
                path,
                "source.capture.upstream_sha256 must be a 64 character lowercase sha256 hex string",
            )


def validate_taxonomy(payload: dict, path: Path, issues: list[dict]) -> None:
    if not isinstance(payload, dict):
        add_issue(issues, "schema-invalid-taxonomy-owner", path, "taxonomy owner must be an object")
        return
    taxonomy = payload.get("taxonomy")
    if not isinstance(taxonomy, dict):
        add_issue(issues, "schema-invalid-taxonomy", path, "taxonomy must be an object")
        return
    for field in ["category", "subcategory", "collection_priority"]:
        if not isinstance(taxonomy.get(field), str) or not taxonomy.get(field):
            add_issue(issues, "schema-missing-taxonomy-field", path, f"taxonomy.{field} is required")


def validate_policy(payload: dict, path: Path, issues: list[dict]) -> None:
    if not isinstance(payload, dict):
        add_issue(issues, "schema-invalid-policy-owner", path, "policy owner must be an object")
        return
    policy = payload.get("policy")
    if not isinstance(policy, dict):
        add_issue(issues, "schema-invalid-policy", path, "policy must be an object")
        return
    filesystem = policy.get("filesystem")
    if not isinstance(filesystem, dict):
        add_issue(issues, "schema-invalid-policy-filesystem", path, "policy.filesystem must be an object")
    else:
        scope = filesystem.get("scope")
        if not _is_exact_string_enum(scope, FILESYSTEM_SCOPE_VALUES):
            add_issue(issues, "schema-invalid-policy-filesystem-scope", path, "policy.filesystem.scope is not supported")
    network = policy.get("network")
    if not isinstance(network, dict):
        add_issue(issues, "schema-invalid-policy-network", path, "policy.network must be an object")
    else:
        scope = network.get("scope")
        if not _is_exact_string_enum(scope, NETWORK_SCOPE_VALUES):
            add_issue(issues, "schema-invalid-policy-network-scope", path, "policy.network.scope is not supported")
        approved_hosts = network.get("approved_hosts")
        if approved_hosts is not None and (
            not isinstance(approved_hosts, list) or not all(isinstance(item, str) and item for item in approved_hosts)
        ):
            add_issue(issues, "schema-invalid-policy-approved-hosts", path, "policy.network.approved_hosts must be a string array")
    approval = policy.get("approval")
    if not isinstance(approval, dict):
        add_issue(issues, "schema-invalid-policy-approval", path, "policy.approval must be an object")
    else:
        required_for = approval.get("required_for")
        if not isinstance(required_for, list) or not all(isinstance(item, str) and item for item in required_for):
            add_issue(issues, "schema-invalid-policy-approval-required-for", path, "policy.approval.required_for must be a string array")


def validate_allowed_tools(payload: dict, path: Path, issues: list[dict]) -> None:
    if not isinstance(payload, dict):
        add_issue(issues, "schema-invalid-tools-owner", path, "allowed_tools owner must be an object")
        return
    allowed_tools = payload.get("allowed_tools")
    if not isinstance(allowed_tools, list):
        add_issue(issues, "schema-invalid-allowed-tools", path, "allowed_tools must be an array")
        return
    seen = set()
    for tool in allowed_tools:
        if not isinstance(tool, str) or not tool:
            add_issue(issues, "schema-invalid-allowed-tool", path, "allowed_tools entries must be non-empty strings")
            continue
        normalized = tool.lower()
        if normalized in seen:
            add_issue(issues, "schema-duplicate-allowed-tool", path, f"allowed_tools contains duplicate value {tool!r}", "medium")
        seen.add(normalized)
        if normalized in DISALLOWED_TOOL_VALUES:
            add_issue(issues, "schema-disallowed-tool", path, f"allowed_tools cannot grant runtime permission {tool!r}", "critical")


def validate_string_list(
    value: object,
    path: Path,
    issues: list[dict],
    field: str,
    issue_id: str,
    pattern: re.Pattern[str] | None = None,
) -> list[str]:
    if value is None:
        return []
    if not isinstance(value, list):
        add_issue(issues, issue_id, path, f"contract.{field} must be an array")
        return []
    values = []
    seen = set()
    for item in value:
        if not isinstance(item, str) or not item:
            add_issue(issues, issue_id, path, f"contract.{field} entries must be non-empty strings")
            continue
        if pattern is not None and not pattern.fullmatch(item):
            add_issue(issues, issue_id, path, f"contract.{field} entry {item!r} is not supported")
        if item in seen:
            add_issue(issues, issue_id, path, f"contract.{field} contains duplicate entry {item!r}", "medium")
        seen.add(item)
        values.append(item)
    return values


def validate_contract(payload: dict, path: Path, issues: list[dict]) -> None:
    if not isinstance(payload, dict):
        add_issue(issues, "schema-invalid-contract-owner", path, "contract owner must be an object")
        return
    contract = payload.get("contract")
    if contract is None:
        return
    if not isinstance(contract, dict):
        add_issue(issues, "schema-invalid-contract", path, "contract must be an object")
        return
    allowed_fields = {
        "schema_version",
        "requires_context",
        "optional_context",
        "produces_artifacts",
        "produces_evidence",
        "capability_vector",
        "stage_hint",
        "conflicts_with",
        "excludes",
        "requires_after",
        "cost_weight",
        "approval_classes",
        "estimated_cost",
        "idempotent",
        "retry_policy",
    }
    for field in contract:
        if field not in allowed_fields:
            add_issue(issues, "schema-invalid-contract-field", path, f"contract.{field} is not supported")
    contract_version = contract.get("schema_version")
    if contract_version is not None and (
        not isinstance(contract_version, int) or isinstance(contract_version, bool) or contract_version not in {1, 2}
    ):
        add_issue(issues, "schema-invalid-contract-version", path, "contract.schema_version must be 1 or 2")
    validate_string_list(contract.get("requires_context"), path, issues, "requires_context", "schema-invalid-contract-artifact", CONTRACT_ARTIFACT_PATTERN)
    validate_string_list(contract.get("optional_context"), path, issues, "optional_context", "schema-invalid-contract-artifact", CONTRACT_ARTIFACT_PATTERN)
    validate_string_list(contract.get("produces_artifacts"), path, issues, "produces_artifacts", "schema-invalid-contract-artifact", CONTRACT_ARTIFACT_PATTERN)
    validate_string_list(contract.get("produces_evidence"), path, issues, "produces_evidence", "schema-invalid-contract-artifact", CONTRACT_ARTIFACT_PATTERN)
    capabilities = validate_string_list(
        contract.get("capability_vector"),
        path,
        issues,
        "capability_vector",
        "schema-invalid-contract-capability",
        CONTRACT_CAPABILITY_PATTERN,
    )
    if contract.get("capability_vector") is not None and not capabilities:
        add_issue(issues, "schema-invalid-contract-capability", path, "contract.capability_vector cannot be empty")
    if contract_version == 2 and contract.get("capability_vector") is None:
        add_issue(issues, "schema-invalid-contract-capability", path, "contract.capability_vector is required for version 2")
    stage_hint = contract.get("stage_hint")
    if stage_hint is not None and (
        type(stage_hint) is not str or stage_hint not in CONTRACT_STAGE_VALUES
    ):
        add_issue(issues, "schema-invalid-contract-stage", path, "contract.stage_hint is not supported")
    if contract_version == 2 and stage_hint is None:
        add_issue(issues, "schema-invalid-contract-stage", path, "contract.stage_hint is required for version 2")
    conflicts = validate_string_list(contract.get("conflicts_with"), path, issues, "conflicts_with", "schema-invalid-contract-conflict")
    if payload.get("name") in conflicts:
        add_issue(issues, "schema-invalid-contract-conflict", path, "contract.conflicts_with cannot include the skill itself")
    excludes = validate_string_list(contract.get("excludes"), path, issues, "excludes", "schema-invalid-contract-conflict")
    if payload.get("name") in excludes:
        add_issue(issues, "schema-invalid-contract-conflict", path, "contract.excludes cannot include the skill itself")
    requires_after = validate_string_list(contract.get("requires_after"), path, issues, "requires_after", "schema-invalid-contract-conflict")
    if payload.get("name") in requires_after:
        add_issue(issues, "schema-invalid-contract-conflict", path, "contract.requires_after cannot include the skill itself")
    cost_weight = contract.get("cost_weight")
    if cost_weight is not None and (
        not isinstance(cost_weight, int) or isinstance(cost_weight, bool) or cost_weight < 1 or cost_weight > 10
    ):
        add_issue(issues, "schema-invalid-contract-cost", path, "contract.cost_weight must be an integer from 1 to 10")
    approval_classes = validate_string_list(
        contract.get("approval_classes"),
        path,
        issues,
        "approval_classes",
        "schema-invalid-contract-approval-class",
    )
    for approval_class in approval_classes:
        if approval_class not in CONTRACT_APPROVAL_CLASS_VALUES:
            add_issue(
                issues,
                "schema-invalid-contract-approval-class",
                path,
                f"contract.approval_classes entry {approval_class!r} is not supported",
            )
    estimated_cost = contract.get("estimated_cost")
    if estimated_cost is not None:
        if not isinstance(estimated_cost, dict) or set(estimated_cost) != {"time", "tokens", "runtime"}:
            add_issue(
                issues,
                "schema-invalid-contract-cost",
                path,
                "contract.estimated_cost must contain time, tokens, and runtime",
            )
        else:
            for field, value in estimated_cost.items():
                if not isinstance(value, int) or isinstance(value, bool) or value < 0 or value > 5:
                    add_issue(
                        issues,
                        "schema-invalid-contract-cost",
                        path,
                        f"contract.estimated_cost.{field} must be an integer from 0 to 5",
                    )
    idempotent = contract.get("idempotent")
    if idempotent is not None and not isinstance(idempotent, bool):
        add_issue(issues, "schema-invalid-contract-idempotent", path, "contract.idempotent must be a boolean")
    retry_policy = contract.get("retry_policy")
    if retry_policy is not None and (
        type(retry_policy) is not str
        or retry_policy not in CONTRACT_RETRY_POLICY_VALUES
    ):
        add_issue(
            issues,
            "schema-invalid-contract-retry-policy",
            path,
            "contract.retry_policy is not supported",
        )


def validate_manifest_schema(payload: dict, path: Path, issues: list[dict]) -> None:
    if not isinstance(payload, dict):
        add_issue(issues, "schema-invalid-manifest", path, "manifest must be an object")
        return
    required = [
        "schema_version",
        "name",
        "version",
        "status",
        "risk_level",
        "taxonomy",
        "source",
        "hashes",
        "allowed_tools",
        "required_verifiers",
        "policy",
    ]
    for field in required:
        if field not in payload:
            add_issue(issues, "schema-missing-manifest-field", path, f"{field} is required")
    if type(payload.get("schema_version")) is not int or payload.get("schema_version") != 1:
        add_issue(issues, "schema-invalid-version", path, "schema_version must be 1")
    if not _is_exact_string_enum(payload.get("status"), STATUS_VALUES):
        add_issue(issues, "schema-invalid-status", path, "status is not a supported registry state")
    if not _is_exact_string_enum(payload.get("risk_level"), RISK_LEVEL_VALUES):
        add_issue(issues, "schema-invalid-risk-level", path, "risk_level is not supported")
    if not isinstance(payload.get("required_verifiers"), list):
        add_issue(issues, "schema-invalid-required-verifiers", path, "required_verifiers must be an array")
    validate_allowed_tools(payload, path, issues)
    validate_policy(payload, path, issues)
    validate_contract(payload, path, issues)
    validate_taxonomy(payload, path, issues)
    validate_source(payload, path, issues)
    validate_hashes(payload, path, issues)
    validate_manifest_integrity(payload, path, issues)


def validate_registry_index_schema(payload: dict, path: Path, issues: list[dict]) -> None:
    if not isinstance(payload, dict):
        add_issue(issues, "schema-invalid-index", path, "registry index must be an object")
        return
    for field in ["schema_version", "generated_at", "skill_count", "skills"]:
        if field not in payload:
            add_issue(issues, "schema-missing-index-field", path, f"{field} is required")
    if type(payload.get("schema_version")) is not int or payload.get("schema_version") != 1:
        add_issue(issues, "schema-invalid-version", path, "schema_version must be 1")
    skills = payload.get("skills")
    if not isinstance(skills, list):
        add_issue(issues, "schema-invalid-index-skills", path, "skills must be an array")
        return
    if type(payload.get("skill_count")) is not int or payload.get("skill_count") != len(skills):
        add_issue(issues, "schema-index-count-mismatch", path, "skill_count must match skills length")
    for index, entry in enumerate(skills):
        entry_path = f"{path.as_posix()}#/skills/{index}"
        if not isinstance(entry, dict):
            add_issue(issues, "schema-invalid-index-entry", entry_path, "index entry must be an object")
            continue
        for field in ["name", "status", "risk_level", "taxonomy", "source", "hashes", "registry_path"]:
            if field not in entry:
                add_issue(issues, "schema-missing-index-entry-field", entry_path, f"{field} is required")
        if not _is_exact_string_enum(entry.get("status"), STATUS_VALUES):
            add_issue(issues, "schema-invalid-status", entry_path, "status is not a supported registry state")
        if not _is_exact_string_enum(entry.get("risk_level"), RISK_LEVEL_VALUES):
            add_issue(issues, "schema-invalid-risk-level", entry_path, "risk_level is not supported")
        validate_taxonomy(entry, Path(entry_path), issues)
        validate_source(entry, Path(entry_path), issues)
        validate_hashes(entry, Path(entry_path), issues)


def validate_verify_report_schema(payload: dict, path: Path, issues: list[dict]) -> None:
    if not isinstance(payload, dict):
        add_issue(issues, "schema-invalid-verify-report", path, "verify report must be an object")
        return
    for field in ["schema_version", "generated_at", "status", "skill_count", "trusted_count", "tampered_count", "unknown_provenance_count", "issues"]:
        if field not in payload:
            add_issue(issues, "schema-missing-verify-field", path, f"{field} is required")
    if type(payload.get("schema_version")) is not int or payload.get("schema_version") != 1:
        add_issue(issues, "schema-invalid-version", path, "schema_version must be 1")
    if not _is_exact_string_enum(payload.get("status"), {"ok", "failed"}):
        add_issue(issues, "schema-invalid-verify-status", path, "status must be ok or failed")
    for field in ["skill_count", "trusted_count", "tampered_count", "unknown_provenance_count"]:
        value = payload.get(field)
        if type(value) is not int or value < 0:
            add_issue(issues, "schema-invalid-verify-count", path, f"{field} must be a non-negative integer")
    if not isinstance(payload.get("issues"), list):
        add_issue(issues, "schema-invalid-verify-issues", path, "issues must be an array")


def validate_sanitization_report_schema(payload: dict, path: Path, manifest: dict, issues: list[dict]) -> None:
    if not isinstance(payload, dict) or not isinstance(manifest, dict):
        add_issue(issues, "schema-invalid-report", path, "report and manifest must be objects")
        return
    for field in [
        "schema_version",
        "skill_name",
        "taxonomy",
        "source",
        "files",
        "hashes",
        "summary",
        "findings",
        "required_verifiers",
        "recommendation",
    ]:
        if field not in payload:
            add_issue(issues, "schema-missing-report-field", path, f"{field} is required")
    if type(payload.get("schema_version")) is not int or payload.get("schema_version") != 1:
        add_issue(issues, "schema-invalid-version", path, "schema_version must be 1")
    if payload.get("skill_name") != manifest.get("name"):
        add_issue(issues, "schema-report-name-mismatch", path, "report skill_name must match manifest name")
    validate_taxonomy(payload, path, issues)
    validate_source(payload, path, issues)
    validate_hashes(payload, path, issues)
    for field in ["files", "findings", "required_verifiers"]:
        if not isinstance(payload.get(field), list):
            add_issue(issues, "schema-invalid-report-list", path, f"{field} must be an array")
    summary = payload.get("summary")
    if not isinstance(summary, dict):
        add_issue(issues, "schema-invalid-report-summary", path, "summary must be an object")
    else:
        for field in ["status", "risk_level", "removed_fragment_count", "rewritten_fragment_count", "unresolved_finding_count"]:
            if field not in summary:
                add_issue(issues, "schema-missing-report-summary-field", path, f"summary.{field} is required")
        if summary.get("status") != manifest.get("status") or summary.get("risk_level") != manifest.get("risk_level"):
            add_issue(issues, "schema-report-summary-mismatch", path, "report summary status and risk_level must match manifest")

    for field in ["source", "taxonomy"]:
        if payload.get(field) != manifest.get(field):
            add_issue(issues, f"schema-report-{field}-mismatch", path, f"report {field} must match manifest {field}")
    report_hashes = payload.get("hashes") if isinstance(payload.get("hashes"), dict) else {}
    manifest_hashes = manifest.get("hashes") if isinstance(manifest.get("hashes"), dict) else {}
    captured_hash_fields = {"source_sha256", "sanitized_sha256"}
    if {field: report_hashes.get(field) for field in captured_hash_fields} != {
        field: manifest_hashes.get(field) for field in captured_hash_fields
    }:
        add_issue(issues, "schema-report-hashes-mismatch", path, "report source and sanitized hashes must match manifest hashes")
    if payload.get("required_verifiers") != manifest.get("required_verifiers"):
        add_issue(
            issues,
            "schema-report-required-verifiers-mismatch",
            path,
            "report required_verifiers must match manifest required_verifiers",
        )
