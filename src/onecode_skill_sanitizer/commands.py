from __future__ import annotations

import argparse
import json
import tempfile
from pathlib import Path

from .batch_lifecycle import build_batch_index
from .batch_lifecycle import compact_promoted_bodies
from .batch_lifecycle import validate_batch_index
from .bulk import claude_skills_candidate_action as claude_skills_candidate_action
from .bulk import claude_skills_candidate_sort_key as claude_skills_candidate_sort_key
from .bulk import compact_claude_skills_candidate as compact_claude_skills_candidate
from .bulk import most_common as most_common
from .bulk import build_claude_skills_bulk_plan as build_claude_skills_bulk_plan
from .bulk import claude_skills_bulk_plan_command as claude_skills_bulk_plan_command
from .bulk import slugify_skill_part as slugify_skill_part
from .bulk import humanize_candidate_name as humanize_candidate_name
from .bulk import local_draft_skill_name as local_draft_skill_name
from .bulk import build_claude_skills_draft_skill_text as build_claude_skills_draft_skill_text
from .bulk import build_claude_skills_draft_manifest as build_claude_skills_draft_manifest
from .bulk import claude_skills_bulk_draft_command as claude_skills_bulk_draft_command
from .bulk import STOPWORD_SKILL_TOKENS as STOPWORD_SKILL_TOKENS
from .bulk import skill_name_tokens as skill_name_tokens
from .bulk import load_draft_skill_names as load_draft_skill_names
from .bulk import trusted_registry_skill_names as trusted_registry_skill_names
from .bulk import registry_skill_statuses as registry_skill_statuses
from .bulk import find_claude_skills_overlap as find_claude_skills_overlap
from .bulk import assess_claude_skills_candidate as assess_claude_skills_candidate
from .bulk import build_claude_skills_bulk_assessment as build_claude_skills_bulk_assessment
from .bulk import claude_skills_bulk_assess_command as claude_skills_bulk_assess_command
from .contracts import contract_coverage
from .paths import resolve_project_asset_path
from .references import validate_external_references
from .registry import build_registry_index as build_registry_index
from .registry import comparable_registry_index as comparable_registry_index
from .registry import load_manifest as load_manifest
from .registry import load_registry_index as load_registry_index
from .registry import manifest_index_entry as manifest_index_entry
from .registry import registry_index_staleness as registry_index_staleness
from .registry import registry_root_for_skill_dir as registry_root_for_skill_dir
from .registry import seal_manifest_file as seal_manifest_file
from .registry import seal_registry_manifests as seal_registry_manifests
from .registry import set_status_command as set_status_command
from .registry import utc_now as utc_now
from .registry import verify_registry as verify_registry
from .registry import write_json as write_json
from .registry import write_registry_index as write_registry_index
from .rendering import markdown_safe_line as markdown_safe_line
from .rendering import project_legacy_contracts
from .rendering import render_task_pack_markdown
from .rendering import render_task_pack_v2_markdown
from .router_evaluation import ROUTER_EVAL_OPTIONAL_STRING_FIELDS as ROUTER_EVAL_OPTIONAL_STRING_FIELDS
from .router_evaluation import ROUTER_EVAL_ROUTER_VALUES as ROUTER_EVAL_ROUTER_VALUES
from .router_evaluation import ROUTER_EVAL_STRATEGY_VALUES as ROUTER_EVAL_STRATEGY_VALUES
from .router_evaluation import ROUTER_EVAL_STRING_LIST_FIELDS as ROUTER_EVAL_STRING_LIST_FIELDS
from .router_evaluation import annotate_router_eval_issues as annotate_router_eval_issues
from .router_evaluation import build_router_eval_quality_summary as build_router_eval_quality_summary
from .router_evaluation import classify_router_eval_issue as classify_router_eval_issue
from .router_evaluation import load_router_eval as load_router_eval
from .router_evaluation import router_eval_empty_bucket as router_eval_empty_bucket
from .router_evaluation import router_eval_summary_key as router_eval_summary_key
from .router_evaluation import router_eval_trace_summary as router_eval_trace_summary
from .router_evaluation import run_router_eval as run_router_eval
from .router_evaluation import validate_router_eval_case as validate_router_eval_case
from .router_eval_v2 import DatasetValidationError
from .router_eval_v2 import EvaluatorError
from .router_eval_v2 import evaluate_router_v2
from .router_eval_v2 import load_eval_dataset_v2
from .scanner import highest_risk, line_findings, read_text_files, scan_text, source_hash
from .taxonomy import classify_skill, taxonomy_from_manifest
from .task_packs import TASK_PROFILE_CATEGORY_VALUES as TASK_PROFILE_CATEGORY_VALUES
from .task_packs import _build_v2_capability_resolution as _build_v2_capability_resolution
from .task_packs import _extend_v2_graph_with_invariants as _extend_v2_graph_with_invariants
from .task_packs import _json_asset_content_hash as _json_asset_content_hash
from .task_packs import _normalize_v2_graph_stages as _normalize_v2_graph_stages
from .task_packs import _routing_status as _routing_status
from .task_packs import _safe_v2_error as _safe_v2_error
from .task_packs import _v2_skill_host_action as _v2_skill_host_action
from .task_packs import _v2_skill_stage as _v2_skill_stage
from .task_packs import build_acceptance_criteria as build_acceptance_criteria
from .task_packs import build_agent_instructions as build_agent_instructions
from .task_packs import build_completion_contract as build_completion_contract
from .task_packs import build_task_pack as build_task_pack
from .task_packs import build_task_pack_v2 as build_task_pack_v2
from .task_packs import bundle_matches_task as bundle_matches_task
from .task_packs import extract_frontmatter_description as extract_frontmatter_description
from .task_packs import extract_markdown_sections as extract_markdown_sections
from .task_packs import load_bundles_index as load_bundles_index
from .task_packs import load_overlap_groups as load_overlap_groups
from .task_packs import load_skill_pack_item as load_skill_pack_item
from .task_packs import load_trusted_skill_pack_items as load_trusted_skill_pack_items
from .task_packs import resolve_overlap_groups_path as resolve_overlap_groups_path
from .task_packs import select_bundles_for_task as select_bundles_for_task
from .task_packs import select_skills_for_task as select_skills_for_task
from .task_packs import skill_matches_task as skill_matches_task
from .task_packs import task_taxonomy_from_profile as task_taxonomy_from_profile
from .task_packs import trusted_skill_names as trusted_skill_names
from .task_packs import validate_overlap_groups as validate_overlap_groups
from .task_packs import validate_overlap_skill_reference as validate_overlap_skill_reference
from .validation import SOURCE_DEFAULT_USAGE_BY_TYPE
from .validation import add_issue
from .validation import seal_manifest
from .validation import text_sha256
from .validation import validate_manifest_schema
from .validation import validate_registry_index_schema
from .validation import validate_sanitization_report_schema
from .validation import validate_verify_report_schema


def batch_check_command(args: argparse.Namespace) -> int:
    batch_root = Path(args.batches)
    catalog_root = Path(args.catalog)
    index_path = Path(args.index)
    index = json.loads(index_path.read_text(encoding="utf-8"))
    issues = validate_batch_index(index, batch_root, catalog_root)
    result = {
        "schema_version": 1,
        "status": "failed" if issues else "ok",
        "item_count": index.get("item_count", 0),
        "compacted_count": sum(bool(item.get("compacted")) for item in index.get("items", [])),
        "issues": issues,
    }
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if not issues else 2


def batch_compact_command(args: argparse.Namespace) -> int:
    batch_root = Path(args.batches)
    catalog_root = Path(args.catalog)
    index_path = Path(args.index)
    previous_index = None
    if index_path.is_file():
        previous_index = json.loads(index_path.read_text(encoding="utf-8"))
    index = build_batch_index(batch_root, catalog_root, args.source_commit, previous_index=previous_index)
    result = compact_promoted_bodies(index, batch_root, catalog_root)
    write_json(index_path, index)
    output = {
        "schema_version": 1,
        "status": "ok",
        "item_count": index["item_count"],
        "lifecycle_counts": index["lifecycle_counts"],
        "compacted_count": len(result["compacted"]),
        "skipped_count": len(result["skipped"]),
        "compacted": result["compacted"],
        "skipped": result["skipped"],
    }
    print(json.dumps(output, indent=2, sort_keys=True))
    return 0


def load_optional_skill_json(source_dir: Path) -> dict:
    manifest_path = source_dir / "skill.json"
    if not manifest_path.exists():
        return {}
    try:
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    return payload if isinstance(payload, dict) else {}

def build_source_record(source_dir: Path, args: argparse.Namespace | None = None) -> dict:
    payload = load_optional_skill_json(source_dir)
    manifest_source = payload.get("source")
    if not isinstance(manifest_source, dict):
        manifest_source = {}

    def value(key: str, arg_name: str | None = None) -> str:
        if args is not None and arg_name is not None:
            arg_value = getattr(args, arg_name, None)
            if arg_value:
                return str(arg_value)
        manifest_value = manifest_source.get(key)
        if manifest_value:
            return str(manifest_value)
        return "unknown"

    source_type = str(manifest_source.get("type", "local_folder"))
    source_usage = value("usage", "source_usage")
    if source_usage == "unknown":
        source_usage = SOURCE_DEFAULT_USAGE_BY_TYPE.get(source_type, "local_authoring")

    return {
        "type": source_type,
        "usage": source_usage,
        "path": str(source_dir),
        "url": value("url", "source_url"),
        "author": value("author", "author"),
        "license": value("license", "license"),
        "reference": value("reference", "reference"),
        "collected_by": value("collected_by", "collected_by"),
        "captured_at": utc_now(),
    }

def build_scan_report(source_dir: Path, args: argparse.Namespace | None = None) -> dict:
    files = read_text_files(source_dir)
    combined_text = "\n".join(text for _, text in files)
    findings = scan_text(combined_text)
    risk_level = highest_risk(findings)
    taxonomy = taxonomy_from_manifest(source_dir) or classify_skill(source_dir.name, combined_text)
    status = "review_required" if findings or not taxonomy.classified else "quarantined"

    return {
        "schema_version": 1,
        "skill_name": source_dir.name,
        "taxonomy": taxonomy.to_json(),
        "source": build_source_record(source_dir, args),
        "files": [relative_path for relative_path, _ in files],
        "hashes": {
            "source_sha256": source_hash(files),
            "sanitized_sha256": None,
        },
        "summary": {
            "status": status,
            "risk_level": risk_level,
            "preserved_sections": [],
            "removed_fragment_count": 0,
            "rewritten_fragment_count": 0,
            "unresolved_finding_count": len(findings),
        },
        "findings": [finding.to_json() for finding in findings],
        "required_verifiers": [],
        "recommendation": "Keep quarantined until sanitization and verifier binding are complete.",
}

def sanitize_skill_text(text: str) -> tuple[str, list[dict[str, str]]]:
    kept_lines = []
    removed = []
    for line_number, line in enumerate(text.splitlines(), start=1):
        findings = line_findings(line)
        if findings:
            for finding in findings:
                item = finding.to_json()
                item["line"] = str(line_number)
                removed.append(item)
            continue
        kept_lines.append(line)
    return "\n".join(kept_lines).strip() + "\n", removed

def build_manifest(scan_report: dict, sanitized_text: str) -> dict:
    return seal_manifest(
        {
            "schema_version": 1,
            "name": scan_report["skill_name"],
            "version": "0.1.0",
            "status": scan_report["summary"]["status"],
            "risk_level": scan_report["summary"]["risk_level"],
            "taxonomy": scan_report["taxonomy"],
            "source": scan_report["source"],
            "hashes": {
                "source_sha256": scan_report["hashes"]["source_sha256"],
                "sanitized_sha256": text_sha256(sanitized_text),
            },
            "allowed_tools": [],
            "required_verifiers": scan_report["required_verifiers"],
            "policy": {
                "filesystem": {"scope": "workspace_only"},
                "network": {"scope": "none"},
                "approval": {"required_for": ["trust", "execution"]},
            },
            "findings": scan_report["findings"],
        }
    )

def sanitize_to_dir(source_dir: Path, out_dir: Path, args: argparse.Namespace) -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)

    source_skill = source_dir / "SKILL.md"
    if source_skill.exists():
        source_text = source_skill.read_text(encoding="utf-8")
    else:
        source_text = "\n".join(text for _, text in read_text_files(source_dir))

    scan_report = build_scan_report(source_dir, args)
    sanitized_text, removed = sanitize_skill_text(source_text)
    manifest = build_manifest(scan_report, sanitized_text)
    report = dict(scan_report)
    report["hashes"] = dict(scan_report["hashes"])
    report["hashes"]["sanitized_sha256"] = manifest["hashes"]["sanitized_sha256"]
    report["hashes"]["manifest_sha256"] = manifest["hashes"]["manifest_sha256"]
    report["summary"] = dict(scan_report["summary"])
    report["summary"]["removed_fragment_count"] = len(removed)
    report["removed_fragments"] = removed

    (out_dir / "SKILL.md").write_text(sanitized_text, encoding="utf-8")
    write_json(out_dir / "skill.json", manifest)
    write_json(out_dir / "SANITIZATION_REPORT.json", report)
    return manifest

def sanitize_command(args: argparse.Namespace) -> int:
    source_dir = Path(args.source)
    if not source_dir.exists() or not source_dir.is_dir():
        raise SystemExit(f"source must be an existing directory: {source_dir}")
    sanitize_to_dir(source_dir, Path(args.out), args)
    return 0

def import_command(args: argparse.Namespace) -> int:
    incoming_dir = Path(args.incoming)
    registry_dir = Path(args.registry)
    if not incoming_dir.exists() or not incoming_dir.is_dir():
        raise SystemExit(f"incoming must be an existing directory: {incoming_dir}")
    registry_dir.mkdir(parents=True, exist_ok=True)
    for source_dir in sorted(path for path in incoming_dir.iterdir() if path.is_dir()):
        scan_report = build_scan_report(source_dir, args)
        category = scan_report["taxonomy"]["category"]
        out_dir = registry_dir / category / source_dir.name
        sanitize_to_dir(source_dir, out_dir, args)
    write_registry_index(registry_dir)
    return 0

def list_command(args: argparse.Namespace) -> int:
    index = load_registry_index(resolve_project_asset_path(args.registry))
    print(json.dumps(index, indent=2, sort_keys=True))
    return 0

def inspect_command(args: argparse.Namespace) -> int:
    registry_dir = resolve_project_asset_path(args.registry)
    index = load_registry_index(registry_dir)
    matches = [entry for entry in index["skills"] if entry["name"] == args.name]
    if not matches:
        return 2
    manifest_path = registry_dir / matches[0]["registry_path"] / "skill.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    print(json.dumps(manifest, indent=2, sort_keys=True))
    return 0

def select_command(args: argparse.Namespace) -> int:
    registry_dir = resolve_project_asset_path(args.registry)
    task_taxonomy = classify_skill("task", args.task).to_json()
    selected = select_skills_for_task(registry_dir, task_taxonomy, args.task, args.include_review_required)
    result = {
        "schema_version": 1,
        "task": args.task,
        "task_taxonomy": task_taxonomy,
        "skill_count": len(selected),
        "skills": selected,
    }
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0

def task_pack_command(args: argparse.Namespace) -> int:
    if args.schema_version == 2:
        return _run_v2_task_pack_command(args)
    else:
        task_pack = build_task_pack(
            resolve_project_asset_path(args.registry),
            args.task,
            args.top,
            args.include_review_required,
            args.include_bundles,
            resolve_project_asset_path(args.bundles) if args.bundles else None,
            args.router,
            args.max_skills,
            args.invariants if getattr(args, "invariants", None) else None,
            getattr(args, "strategy", "balanced"),
            resolve_project_asset_path(args.overlap_groups) if getattr(args, "overlap_groups", None) else None,
        )
        task_pack = project_legacy_contracts(task_pack)
    if args.format == "markdown":
        print(render_task_pack_v2_markdown(task_pack) if args.schema_version == 2 else render_task_pack_markdown(task_pack))
    else:
        print(json.dumps(task_pack, indent=2, sort_keys=True))
    return 0

def smart_command(args: argparse.Namespace) -> int:
    if args.schema_version == 2:
        return _run_v2_task_pack_command(args)
    else:
        task_pack = build_task_pack(
            resolve_project_asset_path(args.registry),
            args.task,
            args.max_skills,
            False,
            True,
            resolve_project_asset_path(args.bundles) if args.bundles else None,
            "mesh",
            args.max_skills,
            args.invariants,
            args.strategy,
            resolve_project_asset_path(args.overlap_groups) if args.overlap_groups else None,
        )
        task_pack = project_legacy_contracts(task_pack)
    if args.format == "markdown":
        print(render_task_pack_markdown(task_pack))
    else:
        print(json.dumps(task_pack, indent=2, sort_keys=True))
    return 0

def _run_v2_task_pack_command(args: argparse.Namespace) -> int:
    try:
        overlap_groups_path = resolve_overlap_groups_path(
            resolve_project_asset_path(args.registry),
            resolve_project_asset_path(args.overlap_groups)
            if getattr(args, "overlap_groups", None)
            else None,
        )
        task_pack = build_task_pack_v2(
            resolve_project_asset_path(args.registry),
            args.task,
            resolve_project_asset_path(args.bundles),
            args.max_skills,
            args.invariants if getattr(args, "invariants", None) else None,
            getattr(args, "strategy", "balanced"),
            overlap_groups_path,
        )
    except (json.JSONDecodeError, OSError, ValueError, SystemExit) as exc:
        error = _safe_v2_error(exc)
        if args.format == "markdown":
            print(
                "\n".join(
                    [
                        "# OneCode Task Pack v2 Error",
                        "",
                        f"- code: `{error['code']}`",
                        f"- message: {error['message']}",
                    ]
                )
            )
        else:
            print(
                json.dumps(
                    {"schema_version": 2, "status": "error", "error": error},
                    indent=2,
                    sort_keys=True,
                )
            )
        return 2
    if args.format == "markdown":
        print(render_task_pack_v2_markdown(task_pack))
    else:
        print(json.dumps(task_pack, indent=2, sort_keys=True))
    return 0

def verify_command(args: argparse.Namespace) -> int:
    result = verify_registry(resolve_project_asset_path(args.registry))
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["status"] == "ok" else 2

def schema_check(registry_dir: Path) -> dict:
    issues: list[dict] = []
    skill_manifest_count = 0
    for manifest_path in sorted(registry_dir.glob("*/*/skill.json")):
        skill_manifest_count += 1
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            add_issue(issues, "schema-invalid-json", manifest_path, str(exc), "critical")
            continue
        validate_manifest_schema(manifest, manifest_path, issues)
        report_path = manifest_path.parent / "SANITIZATION_REPORT.json"
        try:
            report = json.loads(report_path.read_text(encoding="utf-8"))
        except FileNotFoundError:
            add_issue(issues, "schema-report-missing", report_path, "sanitization report is missing", "critical")
            continue
        except json.JSONDecodeError as exc:
            add_issue(issues, "schema-invalid-json", report_path, str(exc), "critical")
            continue
        validate_sanitization_report_schema(report, report_path, manifest, issues)

    index_path = registry_dir / "index.json"
    try:
        registry_index = json.loads(index_path.read_text(encoding="utf-8"))
        validate_registry_index_schema(registry_index, index_path, issues)
    except FileNotFoundError:
        add_issue(issues, "schema-index-missing", index_path, "registry index is missing", "critical")
    except json.JSONDecodeError as exc:
        add_issue(issues, "schema-invalid-json", index_path, str(exc), "critical")

    with tempfile.TemporaryDirectory() as tmp:
        verify_path = Path(tmp) / "verify-report.json"
        verify_report = verify_registry(registry_dir)
        verify_path.write_text(json.dumps(verify_report), encoding="utf-8")
        validate_verify_report_schema(verify_report, verify_path, issues)

    return {
        "schema_version": 1,
        "generated_at": utc_now(),
        "status": "failed" if issues else "ok",
        "skill_manifest_count": skill_manifest_count,
        "issues": issues,
    }

def schema_check_command(args: argparse.Namespace) -> int:
    result = schema_check(resolve_project_asset_path(args.registry))
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["status"] == "ok" else 2

def contract_check_command(args: argparse.Namespace) -> int:
    registry_dir = resolve_project_asset_path(args.registry)
    bundles_path = resolve_project_asset_path(args.bundles)
    try:
        registry_index_path = registry_dir / "index.json"
        try:
            registry = json.loads(registry_index_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            raise ValueError(f"invalid registry index JSON: {registry_index_path}")
        try:
            bundles_index = json.loads(bundles_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            raise ValueError(f"invalid bundles index JSON: {bundles_path}")
        result = contract_coverage(
            registry,
            bundles_index,
            args.scenario,
            registry_root=registry_dir,
        )
    except ValueError as exc:
        print(json.dumps({"status": "error", "error": str(exc)}, indent=2, sort_keys=True, allow_nan=False))
        return 2
    result["minimum_ratio"] = args.minimum_ratio
    result["status"] = "ok" if result["coverage_ratio"] >= args.minimum_ratio else "failed"
    print(json.dumps(result, indent=2, sort_keys=True, allow_nan=False))
    return 0 if result["status"] == "ok" else 2

def reference_check_command(args: argparse.Namespace) -> int:
    result = validate_external_references(resolve_project_asset_path(args.references))
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["status"] == "ok" else 2

def router_eval_command(args: argparse.Namespace) -> int:
    result = run_router_eval(
        eval_path=resolve_project_asset_path(args.eval),
        registry_dir=resolve_project_asset_path(args.registry),
        bundles_path=resolve_project_asset_path(args.bundles),
        overlap_groups_path=resolve_project_asset_path(args.overlap_groups) if args.overlap_groups else None,
        max_skills=args.max_skills,
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["status"] == "ok" else 2

def router_eval_v2_command(args: argparse.Namespace) -> int:
    eval_path = resolve_project_asset_path(args.eval)
    registry_dir = resolve_project_asset_path(args.registry)
    bundles_path = resolve_project_asset_path(args.bundles)
    try:
        bundles_index = load_bundles_index(bundles_path)
        known_scenarios = {
            bundle["id"]
            for bundle in bundles_index.get("bundles", [])
            if isinstance(bundle, dict) and isinstance(bundle.get("id"), str)
        }
        cases = load_eval_dataset_v2(eval_path, known_scenarios)
        result = evaluate_router_v2(
            cases,
            route_builder=lambda case: build_task_pack_v2(
                registry_dir,
                case["task"],
                bundles_path,
            ),
            known_scenarios=known_scenarios,
        )
    except (DatasetValidationError, EvaluatorError, ValueError, OSError, SystemExit) as exc:
        print(
            json.dumps(
                {"status": "error", "error": str(exc)},
                indent=2,
                sort_keys=True,
                allow_nan=False,
            )
        )
        return 2
    print(json.dumps(result, indent=2, sort_keys=True, allow_nan=False))
    return 0

def validate_bundles(registry_dir: Path, bundles_path: Path) -> dict:
    issues = []
    bundles_index = load_bundles_index(bundles_path)
    index = load_registry_index(registry_dir)
    statuses = {entry["name"]: entry.get("status") for entry in index["skills"]}
    bundles = bundles_index["bundles"]
    declared_count = bundles_index.get("bundle_count")
    if declared_count is not None and declared_count != len(bundles):
        issues.append(
            {
                "id": "bundle-count-mismatch",
                "severity": "medium",
                "path": bundles_path.as_posix(),
                "expected": len(bundles),
                "actual": declared_count,
            }
        )
    for bundle in bundles:
        bundle_id = bundle.get("id", "unknown")
        if bundle.get("status") != "trusted":
            continue
        for skill_name in bundle.get("skills", []):
            status = statuses.get(skill_name)
            if status is None:
                issues.append(
                    {
                        "id": "bundle-missing-skill",
                        "severity": "high",
                        "bundle": bundle_id,
                        "skill": skill_name,
                    }
                )
            elif status != "trusted":
                issues.append(
                    {
                        "id": "bundle-non-trusted-skill",
                        "severity": "high",
                        "bundle": bundle_id,
                        "skill": skill_name,
                        "status": status,
                    }
                )
    return {
        "schema_version": 1,
        "bundle_count": len(bundles),
        "trusted_bundle_count": sum(1 for bundle in bundles if bundle.get("status") == "trusted"),
        "issues": issues,
    }

def validate_claude_skills_candidate_map(registry_dir: Path, candidate_map_path: Path) -> dict:
    issues = []
    candidate_map = json.loads(candidate_map_path.read_text(encoding="utf-8"))
    candidates = candidate_map.get("candidates", [])
    if not isinstance(candidates, list):
        issues.append(
            {
                "id": "claude-skills-invalid-candidates",
                "severity": "high",
                "path": candidate_map_path.as_posix(),
            }
        )
        candidates = []

    declared_candidate_count = candidate_map.get("candidate_count")
    if declared_candidate_count is not None and declared_candidate_count != len(candidates):
        issues.append(
            {
                "id": "claude-skills-candidate-count-mismatch",
                "severity": "medium",
                "path": candidate_map_path.as_posix(),
                "expected": len(candidates),
                "actual": declared_candidate_count,
            }
        )

    index = load_registry_index(registry_dir)
    statuses = {entry["name"]: entry.get("status") for entry in index["skills"]}
    converted_candidates = [candidate for candidate in candidates if candidate.get("adoption") == "converted"]
    declared_converted_count = candidate_map.get("converted_skill_count")
    if declared_converted_count is not None and declared_converted_count != len(converted_candidates):
        issues.append(
            {
                "id": "claude-skills-converted-count-mismatch",
                "severity": "medium",
                "path": candidate_map_path.as_posix(),
                "expected": len(converted_candidates),
                "actual": declared_converted_count,
            }
        )

    actual_pairs = set()
    for candidate_index, candidate in enumerate(candidates):
        if candidate.get("adoption") != "converted":
            continue
        candidate_name = str(candidate.get("name", ""))
        candidate_path = f"{candidate_map_path.as_posix()}#/candidates/{candidate_index}"
        local_skill = candidate.get("local_skill")
        if not isinstance(local_skill, str) or not local_skill:
            issues.append(
                {
                    "id": "claude-skills-missing-local-skill",
                    "severity": "high",
                    "path": candidate_path,
                    "candidate": candidate_name,
                }
            )
            continue
        actual_pairs.add((candidate_name, local_skill))
        status = statuses.get(local_skill)
        if status is None:
            issues.append(
                {
                    "id": "claude-skills-missing-registry-skill",
                    "severity": "high",
                    "path": candidate_path,
                    "candidate": candidate_name,
                    "skill": local_skill,
                }
            )
        elif status != "trusted":
            issues.append(
                {
                    "id": "claude-skills-non-trusted-local-skill",
                    "severity": "high",
                    "path": candidate_path,
                    "candidate": candidate_name,
                    "skill": local_skill,
                    "status": status,
                }
            )

    declared_converted_skills = candidate_map.get("converted_skills", [])
    if not isinstance(declared_converted_skills, list):
        declared_converted_skills = []
        issues.append(
            {
                "id": "claude-skills-invalid-converted-skills",
                "severity": "high",
                "path": candidate_map_path.as_posix(),
            }
        )
    declared_pairs = {
        (str(item.get("source_candidate", "")), str(item.get("local_skill", "")))
        for item in declared_converted_skills
        if isinstance(item, dict) and item.get("source_candidate") and item.get("local_skill")
    }
    if declared_pairs != actual_pairs:
        issues.append(
            {
                "id": "claude-skills-converted-skills-mismatch",
                "severity": "medium",
                "path": candidate_map_path.as_posix(),
                "expected": len(actual_pairs),
                "actual": len(declared_pairs),
            }
        )

    return {
        "schema_version": 1,
        "status": "failed" if issues else "ok",
        "path": candidate_map_path.as_posix(),
        "candidate_count": len(candidates),
        "converted_count": len(converted_candidates),
        "converted_skill_mapping_count": len(actual_pairs),
        "issues": issues,
    }

def maintain_check(
    registry_dir: Path,
    bundles_path: Path | None = None,
    overlap_groups_path: Path | None = None,
    references_path: Path | None = None,
    claude_skills_candidate_map_path: Path | None = None,
) -> dict:
    registry_verification = verify_registry(registry_dir)
    issues = list(registry_verification["issues"])
    issues.extend(registry_index_staleness(registry_dir))
    bundle_validation = None
    if bundles_path is not None:
        bundle_validation = validate_bundles(registry_dir, bundles_path)
        issues.extend(bundle_validation["issues"])
    overlap_validation = None
    resolved_overlap_path = resolve_overlap_groups_path(registry_dir, overlap_groups_path)
    if resolved_overlap_path is not None:
        overlap_validation = validate_overlap_groups(registry_dir, resolved_overlap_path)
        issues.extend(overlap_validation["issues"])
    reference_validation = None
    if references_path is not None:
        reference_validation = validate_external_references(references_path)
        issues.extend(reference_validation["issues"])
    claude_skills_candidate_map_validation = None
    if claude_skills_candidate_map_path is not None:
        claude_skills_candidate_map_validation = validate_claude_skills_candidate_map(
            registry_dir,
            claude_skills_candidate_map_path,
        )
        issues.extend(claude_skills_candidate_map_validation["issues"])
    return {
        "schema_version": 1,
        "generated_at": utc_now(),
        "status": "failed" if issues else "ok",
        "registry_verification": registry_verification,
        "bundle_validation": bundle_validation,
        "overlap_validation": overlap_validation,
        "reference_validation": reference_validation,
        "claude_skills_candidate_map_validation": claude_skills_candidate_map_validation,
        "issues": issues,
    }

def maintain_check_command(args: argparse.Namespace) -> int:
    result = maintain_check(
        resolve_project_asset_path(args.registry),
        resolve_project_asset_path(args.bundles) if args.bundles else None,
        resolve_project_asset_path(args.overlap_groups) if args.overlap_groups else None,
        resolve_project_asset_path(args.references) if getattr(args, "references", None) else None,
        resolve_project_asset_path(args.claude_skills_candidate_map)
        if getattr(args, "claude_skills_candidate_map", None)
        else None,
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["status"] == "ok" else 2

def reindex_command(args: argparse.Namespace) -> int:
    write_registry_index(Path(args.registry), seal_manifests=True)
    return 0

def audit_command(args: argparse.Namespace) -> int:
    skill_dir = Path(args.skill_dir)
    manifest = load_manifest(skill_dir)
    skill_path = skill_dir / "SKILL.md"
    if not skill_path.exists():
        return 2
    actual_hash = text_sha256(skill_path.read_text(encoding="utf-8"))
    expected_hash = manifest.get("hashes", {}).get("sanitized_sha256")
    if actual_hash != expected_hash:
        return 2
    return 0 if manifest.get("status") == "trusted" else 2

def approve_command(args: argparse.Namespace) -> int:
    return set_status_command(args, "trusted")

def reject_command(args: argparse.Namespace) -> int:
    return set_status_command(args, "rejected")

def disable_command(args: argparse.Namespace) -> int:
    return set_status_command(args, "disabled")

def scan_command(args: argparse.Namespace) -> int:
    source_dir = Path(args.source)
    if not source_dir.exists() or not source_dir.is_dir():
        raise SystemExit(f"source must be an existing directory: {source_dir}")
    report = build_scan_report(source_dir, args)
    output = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out:
        out_path = Path(args.out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(output, encoding="utf-8")
    else:
        print(output, end="")
    return 0
