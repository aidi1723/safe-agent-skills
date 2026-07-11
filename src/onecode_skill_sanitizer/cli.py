from __future__ import annotations

import argparse
import math
from pathlib import Path

from .commands import _run_v2_task_pack_command as _run_v2_task_pack_command
from .commands import approve_command as approve_command
from .commands import audit_command as audit_command
from .commands import batch_check_command as batch_check_command
from .commands import batch_compact_command as batch_compact_command
from .commands import build_manifest as build_manifest
from .commands import build_scan_report as build_scan_report
from .commands import build_source_record as build_source_record
from .commands import contract_check_command as contract_check_command
from .commands import disable_command as disable_command
from .commands import depth_check_command as depth_check_command
from .commands import import_command as import_command
from .commands import inspect_command as inspect_command
from .commands import list_command as list_command
from .commands import load_optional_skill_json as load_optional_skill_json
from .commands import maintain_check as maintain_check
from .commands import maintain_check_command as maintain_check_command
from .commands import reference_check_command as reference_check_command
from .commands import reindex_command as reindex_command
from .commands import reseal_content_command as reseal_content_command
from .commands import reject_command as reject_command
from .commands import router_eval_command as router_eval_command
from .commands import router_eval_v2_command as router_eval_v2_command
from .commands import sanitize_command as sanitize_command
from .commands import sanitize_skill_text as sanitize_skill_text
from .commands import sanitize_to_dir as sanitize_to_dir
from .commands import scan_command as scan_command
from .commands import schema_check as schema_check
from .commands import schema_check_command as schema_check_command
from .commands import select_command as select_command
from .commands import smart_command as smart_command
from .commands import task_pack_command as task_pack_command
from .commands import validate_bundles as validate_bundles
from .commands import validate_claude_skills_candidate_map as validate_claude_skills_candidate_map
from .commands import verify_command as verify_command
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
from .bulk import build_claude_skills_bulk_drafts as _bulk_build_claude_skills_bulk_drafts
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
from .registry import build_registry_index as build_registry_index
from .registry import comparable_registry_index as comparable_registry_index
from .registry import load_manifest as load_manifest
from .registry import load_registry_index as load_registry_index
from .registry import manifest_index_entry as manifest_index_entry
from .registry import registry_index_staleness as registry_index_staleness
from .registry import registry_root_for_skill_dir as registry_root_for_skill_dir
from .registry import reseal_skill_content as reseal_skill_content
from .registry import seal_manifest_file as seal_manifest_file
from .registry import seal_registry_manifests as seal_registry_manifests
from .registry import set_status_command as set_status_command
from .registry import utc_now as utc_now
from .registry import verify_registry as verify_registry
from .registry import write_json as write_json
from .registry import write_registry_index as write_registry_index
from .rendering import markdown_safe_line as markdown_safe_line
from .rendering import project_legacy_contracts as project_legacy_contracts
from .rendering import render_task_pack_markdown as render_task_pack_markdown
from .rendering import render_task_pack_v2_markdown as render_task_pack_v2_markdown
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
from .task_packs import TASK_PROFILE_CATEGORY_VALUES as TASK_PROFILE_CATEGORY_VALUES
from .task_packs import _build_v2_capability_resolution as _build_v2_capability_resolution
from .task_packs import _extend_v2_graph_with_invariants as _extend_v2_graph_with_invariants
from .task_packs import _json_asset_content_hash as _json_asset_content_hash
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
from .validation import SOURCE_USAGE_VALUES



def build_claude_skills_bulk_drafts(
    candidate_map_path: Path,
    out_dir: Path,
    batch_size: int,
    batch_index: int,
) -> dict:
    return _bulk_build_claude_skills_bulk_drafts(
        candidate_map_path,
        out_dir,
        batch_size,
        batch_index,
        write_json,
    )

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="onecode-skill-sanitizer")
    subparsers = parser.add_subparsers(dest="command", required=True)

    scan_parser = subparsers.add_parser("scan")
    scan_parser.add_argument("source")
    scan_parser.add_argument("--out")
    add_provenance_args(scan_parser)
    scan_parser.set_defaults(func=scan_command)

    sanitize_parser = subparsers.add_parser("sanitize")
    sanitize_parser.add_argument("source")
    sanitize_parser.add_argument("--out", required=True)
    add_provenance_args(sanitize_parser)
    sanitize_parser.set_defaults(func=sanitize_command)

    audit_parser = subparsers.add_parser("audit")
    audit_parser.add_argument("skill_dir")
    audit_parser.set_defaults(func=audit_command)

    approve_parser = subparsers.add_parser("approve")
    approve_parser.add_argument("skill_dir")
    approve_parser.set_defaults(func=approve_command)

    reject_parser = subparsers.add_parser("reject")
    reject_parser.add_argument("skill_dir")
    reject_parser.set_defaults(func=reject_command)

    disable_parser = subparsers.add_parser("disable")
    disable_parser.add_argument("skill_dir")
    disable_parser.set_defaults(func=disable_command)

    import_parser = subparsers.add_parser("import")
    import_parser.add_argument("incoming")
    import_parser.add_argument("--registry", required=True)
    add_provenance_args(import_parser)
    import_parser.set_defaults(func=import_command)

    list_parser = subparsers.add_parser("list")
    list_parser.add_argument("--registry", required=True)
    list_parser.set_defaults(func=list_command)

    inspect_parser = subparsers.add_parser("inspect")
    inspect_parser.add_argument("name")
    inspect_parser.add_argument("--registry", required=True)
    inspect_parser.set_defaults(func=inspect_command)

    select_parser = subparsers.add_parser("select")
    select_parser.add_argument("task")
    select_parser.add_argument("--registry", required=True)
    select_parser.add_argument("--include-review-required", action="store_true")
    select_parser.set_defaults(func=select_command)

    task_pack_parser = subparsers.add_parser("task-pack")
    task_pack_parser.add_argument("task")
    task_pack_parser.add_argument("--registry", required=True)
    task_pack_parser.add_argument("--top", type=positive_int, default=3)
    task_pack_parser.add_argument("--format", choices=["json", "markdown"], default="json")
    task_pack_parser.add_argument("--include-review-required", action="store_true")
    task_pack_parser.add_argument("--include-bundles", action="store_true")
    task_pack_parser.add_argument("--bundles", default="bundles/index.json")
    task_pack_parser.add_argument("--router", choices=["simple", "scenario", "mesh"], default="simple")
    task_pack_parser.add_argument("--max-skills", type=positive_int)
    task_pack_parser.add_argument("--invariants", action="append")
    task_pack_parser.add_argument("--strategy", choices=["fast", "balanced", "deep"], default="balanced")
    task_pack_parser.add_argument("--overlap-groups")
    task_pack_parser.add_argument("--schema-version", type=int, choices=[1, 2], default=2)
    task_pack_parser.set_defaults(func=task_pack_command)

    smart_parser = subparsers.add_parser("smart")
    smart_parser.add_argument("task")
    smart_parser.add_argument("--registry", default="catalog")
    smart_parser.add_argument("--bundles", default="bundles/index.json")
    smart_parser.add_argument("--overlap-groups")
    smart_parser.add_argument("--invariants", action="append")
    smart_parser.add_argument("--strategy", choices=["fast", "balanced", "deep"], default="balanced")
    smart_parser.add_argument("--max-skills", type=positive_int, default=8)
    smart_parser.add_argument("--format", choices=["json", "markdown"], default="json")
    smart_parser.add_argument("--schema-version", type=int, choices=[1, 2], default=2)
    smart_parser.set_defaults(func=smart_command)

    verify_parser = subparsers.add_parser("verify")
    verify_parser.add_argument("--registry", required=True)
    verify_parser.set_defaults(func=verify_command)

    maintain_check_parser = subparsers.add_parser("maintain-check")
    maintain_check_parser.add_argument("--registry", required=True)
    maintain_check_parser.add_argument("--bundles")
    maintain_check_parser.add_argument("--overlap-groups")
    maintain_check_parser.add_argument("--references")
    maintain_check_parser.add_argument("--claude-skills-candidate-map")
    maintain_check_parser.set_defaults(func=maintain_check_command)

    schema_check_parser = subparsers.add_parser("schema-check")
    schema_check_parser.add_argument("--registry", required=True)
    schema_check_parser.set_defaults(func=schema_check_command)

    contract_check_parser = subparsers.add_parser("contract-check")
    contract_check_parser.add_argument("--registry", required=True)
    contract_check_parser.add_argument("--bundles", required=True)
    contract_check_parser.add_argument("--scenario", action="append")
    contract_check_parser.add_argument("--minimum-ratio", type=ratio, default=0.0)
    contract_check_parser.set_defaults(func=contract_check_command)

    reference_check_parser = subparsers.add_parser("reference-check")
    reference_check_parser.add_argument("--references", required=True)
    reference_check_parser.set_defaults(func=reference_check_command)

    router_eval_parser = subparsers.add_parser("router-eval")
    router_eval_parser.add_argument("--eval", required=True)
    router_eval_parser.add_argument("--registry", required=True)
    router_eval_parser.add_argument("--bundles", default="bundles/index.json")
    router_eval_parser.add_argument("--overlap-groups")
    router_eval_parser.add_argument("--max-skills", type=positive_int, default=8)
    router_eval_parser.set_defaults(func=router_eval_command)

    router_eval_v2_parser = subparsers.add_parser("router-eval-v2")
    router_eval_v2_parser.add_argument("--eval", required=True)
    router_eval_v2_parser.add_argument("--registry", default="catalog")
    router_eval_v2_parser.add_argument("--bundles", default="bundles/index.json")
    router_eval_v2_parser.add_argument("--require-production-ready", action="store_true")
    router_eval_v2_parser.set_defaults(func=router_eval_v2_command)

    claude_skills_bulk_plan_parser = subparsers.add_parser("claude-skills-bulk-plan")
    claude_skills_bulk_plan_parser.add_argument("--candidate-map", required=True)
    claude_skills_bulk_plan_parser.add_argument("--batch-size", type=int, default=50)
    claude_skills_bulk_plan_parser.set_defaults(func=claude_skills_bulk_plan_command)

    claude_skills_bulk_draft_parser = subparsers.add_parser("claude-skills-bulk-draft")
    claude_skills_bulk_draft_parser.add_argument("--candidate-map", required=True)
    claude_skills_bulk_draft_parser.add_argument("--out", required=True)
    claude_skills_bulk_draft_parser.add_argument("--batch-size", type=int, default=50)
    claude_skills_bulk_draft_parser.add_argument("--batch-index", type=int, default=1)
    claude_skills_bulk_draft_parser.set_defaults(func=claude_skills_bulk_draft_command)

    claude_skills_bulk_assess_parser = subparsers.add_parser("claude-skills-bulk-assess")
    claude_skills_bulk_assess_parser.add_argument("--candidate-map", required=True)
    claude_skills_bulk_assess_parser.add_argument("--draft-root", required=True)
    claude_skills_bulk_assess_parser.add_argument("--registry", required=True)
    claude_skills_bulk_assess_parser.set_defaults(func=claude_skills_bulk_assess_command)

    batch_check_parser = subparsers.add_parser("batch-check")
    batch_check_parser.add_argument("--batches", required=True)
    batch_check_parser.add_argument("--catalog", required=True)
    batch_check_parser.add_argument("--index", required=True)
    batch_check_parser.set_defaults(func=batch_check_command)

    batch_compact_parser = subparsers.add_parser("batch-compact")
    batch_compact_parser.add_argument("--batches", required=True)
    batch_compact_parser.add_argument("--catalog", required=True)
    batch_compact_parser.add_argument("--index", required=True)
    batch_compact_parser.add_argument("--source-commit", required=True)
    batch_compact_parser.set_defaults(func=batch_compact_command)

    depth_check_parser = subparsers.add_parser("depth-check")
    depth_check_parser.add_argument("--catalog", required=True)
    depth_check_parser.add_argument("--policy", required=True)
    depth_check_parser.set_defaults(func=depth_check_command)

    reseal_content_parser = subparsers.add_parser("reseal-content")
    reseal_content_parser.add_argument("skill_dir")
    reseal_content_parser.set_defaults(func=reseal_content_command)

    reindex_parser = subparsers.add_parser("reindex")
    reindex_parser.add_argument("--registry", required=True)
    reindex_parser.set_defaults(func=reindex_command)

    return parser


def positive_int(value: str) -> int:
    try:
        parsed = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("must be an integer greater than or equal to 1") from exc
    if parsed < 1:
        raise argparse.ArgumentTypeError("must be greater than or equal to 1")
    return parsed


def ratio(value: str) -> float:
    try:
        parsed = float(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("must be a number from 0 to 1") from exc
    if not math.isfinite(parsed) or parsed < 0 or parsed > 1:
        raise argparse.ArgumentTypeError("must be from 0 to 1")
    return parsed


def add_provenance_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--source-url")
    parser.add_argument("--source-usage", choices=sorted(SOURCE_USAGE_VALUES))
    parser.add_argument("--author")
    parser.add_argument("--license")
    parser.add_argument("--reference")
    parser.add_argument("--collected-by")


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
