from __future__ import annotations

import json
from pathlib import Path

from .registry import utc_now
from .task_packs import build_task_pack


def load_router_eval(eval_path: Path) -> dict:
    if not eval_path.exists():
        raise SystemExit(f"missing router eval file: {eval_path}")
    payload = json.loads(eval_path.read_text(encoding="utf-8"))
    schema_version = payload.get("schema_version")
    if schema_version not in {1, 2}:
        raise SystemExit(f"invalid router eval schema_version: {eval_path}")
    if not isinstance(payload.get("cases"), list):
        raise SystemExit(f"invalid router eval cases: {eval_path}")
    if schema_version == 2:
        dataset = payload.get("dataset")
        if not isinstance(dataset, str) or not dataset:
            raise SystemExit(f"invalid router eval dataset: {eval_path}")
        split = payload.get("split")
        if split != "regression":
            raise SystemExit(f"invalid router eval split: {eval_path}")
        case_count = payload.get("case_count")
        if (
            not isinstance(case_count, int)
            or isinstance(case_count, bool)
            or case_count != len(payload["cases"])
        ):
            raise SystemExit(f"invalid router eval case_count: {eval_path}")
        case_ids = [case.get("id") if isinstance(case, dict) else None for case in payload["cases"]]
        invalid_case_id = any(not isinstance(case_id, str) or not case_id for case_id in case_ids)
        if invalid_case_id or len(case_ids) != len(set(case_ids)):
            raise SystemExit(f"invalid router eval unique case id: {eval_path}")
    return payload

ROUTER_EVAL_STRING_LIST_FIELDS = (
    "expected_skills",
    "forbidden_skills",
    "forbidden_skill_prefixes",
    "forbidden_skill_subcategories",
    "expected_trace_selected",
    "expected_trace_pruned",
    "expected_trace_required",
    "expected_trace_reason_codes",
)

ROUTER_EVAL_OPTIONAL_STRING_FIELDS = (
    "expected_scenario",
    "expected_task_type",
)

ROUTER_EVAL_ROUTER_VALUES = {"scenario", "mesh"}

ROUTER_EVAL_STRATEGY_VALUES = {"fast", "balanced", "deep"}

def validate_router_eval_case(case: dict) -> list[dict]:
    issues = []
    router_mode = case.get("router", "scenario")
    if not isinstance(router_mode, str):
        issues.append(
            {
                "id": "router-eval-invalid-case-field",
                "field": "router",
                "expected": "scenario or mesh",
                "actual": type(router_mode).__name__,
            }
        )
    strategy = case.get("strategy", "balanced")
    if not isinstance(strategy, str) or strategy not in ROUTER_EVAL_STRATEGY_VALUES:
        issues.append(
            {
                "id": "router-eval-invalid-case-field",
                "field": "strategy",
                "expected": "fast, balanced, or deep",
                "actual": type(strategy).__name__,
            }
        )
    invariants = case.get("invariants")
    if invariants is not None:
        invalid_invariants = not isinstance(invariants, (str, list)) or (
            isinstance(invariants, list) and any(not isinstance(item, str) for item in invariants)
        )
        if invalid_invariants:
            issues.append(
                {
                    "id": "router-eval-invalid-case-field",
                    "field": "invariants",
                    "expected": "string or array of strings",
                    "actual": type(invariants).__name__,
                }
            )
    for field in ROUTER_EVAL_OPTIONAL_STRING_FIELDS:
        value = case.get(field)
        if value is not None and not isinstance(value, str):
            issues.append(
                {
                    "id": "router-eval-invalid-case-field",
                    "field": field,
                    "expected": "string",
                    "actual": type(value).__name__,
                }
            )
    for field in ROUTER_EVAL_STRING_LIST_FIELDS:
        value = case.get(field, [])
        if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
            issues.append(
                {
                    "id": "router-eval-invalid-case-field",
                    "field": field,
                    "expected": "array of strings",
                    "actual": type(value).__name__,
                }
            )
    max_skill_count = case.get("max_skill_count")
    if max_skill_count is not None and (
        not isinstance(max_skill_count, int) or isinstance(max_skill_count, bool) or max_skill_count < 0
    ):
        issues.append(
            {
                "id": "router-eval-invalid-case-field",
                "field": "max_skill_count",
                "expected": "non-negative integer",
                "actual": type(max_skill_count).__name__,
            }
        )
    return issues

def router_eval_summary_key(value: object, empty_label: str) -> str:
    if isinstance(value, str) and value:
        return value
    return empty_label

def router_eval_empty_bucket() -> dict:
    return {"case_count": 0, "passed_count": 0, "failed_count": 0}

def classify_router_eval_issue(issue: dict, result_context: dict | None = None) -> str:
    issue_id = router_eval_summary_key(issue.get("id"), "unknown-issue")
    context = result_context or {}
    if issue_id == "router-eval-scenario-mismatch":
        expected = issue.get("expected", context.get("expected_scenario"))
        actual = issue.get("actual", context.get("actual_scenario"))
        if not expected and actual:
            return "false_positive"
        if expected and not actual:
            return "false_negative"
        return "route_mismatch"
    if issue_id == "router-eval-missing-skill":
        return "false_negative"
    if issue_id in {
        "router-eval-trace-missing-selected",
        "router-eval-trace-missing-required",
    }:
        return "false_negative"
    if issue_id in {
        "router-eval-forbidden-skill",
        "router-eval-forbidden-skill-prefix",
        "router-eval-forbidden-skill-subcategory",
        "router-eval-max-skill-count-exceeded",
        "router-eval-trace-missing-pruned",
    }:
        return "false_positive"
    if issue_id == "router-eval-trace-missing-reason-code":
        return "route_mismatch"
    if issue_id == "router-eval-task-type-mismatch":
        return "task_type_mismatch"
    if issue_id in {
        "router-eval-count-mismatch",
        "router-eval-invalid-case-field",
        "router-eval-invalid-router",
        "router-eval-missing-task",
    }:
        return "eval_contract"
    return "unclassified"

def annotate_router_eval_issues(issues: list[dict], result_context: dict | None = None) -> list[dict]:
    annotated = []
    for issue in issues:
        item = dict(issue)
        item["classification"] = classify_router_eval_issue(item, result_context)
        annotated.append(item)
    return annotated

def build_router_eval_quality_summary(results: list[dict], top_level_issues: list[dict] | None = None) -> dict:
    by_expected_scenario: dict[str, dict] = {}
    by_actual_scenario: dict[str, dict] = {}
    by_expected_task_type: dict[str, dict] = {}
    by_confidence: dict[str, dict] = {}
    by_issue: dict[str, int] = {}
    by_issue_class: dict[str, int] = {}

    def bump_bucket(target: dict[str, dict], key: str, status: str) -> None:
        bucket = target.setdefault(key, router_eval_empty_bucket())
        bucket["case_count"] += 1
        if status == "ok":
            bucket["passed_count"] += 1
        else:
            bucket["failed_count"] += 1

    def bump_issue(issue: dict) -> None:
        issue_id = router_eval_summary_key(issue.get("id"), "unknown-issue")
        by_issue[issue_id] = by_issue.get(issue_id, 0) + 1
        issue_class = router_eval_summary_key(issue.get("classification"), "unclassified")
        by_issue_class[issue_class] = by_issue_class.get(issue_class, 0) + 1

    for result in results:
        status = result.get("status", "failed")
        bump_bucket(
            by_expected_scenario,
            router_eval_summary_key(result.get("expected_scenario"), "(none)"),
            status,
        )
        bump_bucket(
            by_actual_scenario,
            router_eval_summary_key(result.get("actual_scenario"), "(none)"),
            status,
        )
        bump_bucket(
            by_expected_task_type,
            router_eval_summary_key(result.get("expected_task_type"), "(unspecified)"),
            status,
        )
        bump_bucket(
            by_confidence,
            router_eval_summary_key(result.get("actual_confidence"), "(unknown)"),
            status,
        )
        for issue in result.get("issues", []):
            bump_issue(issue)
    for issue in annotate_router_eval_issues(top_level_issues or []):
        bump_issue(issue)

    failed_count = sum(1 for item in results if item.get("status") != "ok")
    low_confidence_results = [item for item in results if item.get("actual_low_confidence") is True]
    low_confidence_failed_count = sum(1 for item in low_confidence_results if item.get("status") != "ok")
    return {
        "case_count": len(results),
        "passed_count": len(results) - failed_count,
        "failed_count": failed_count,
        "low_confidence_case_count": len(low_confidence_results),
        "low_confidence_passed_count": len(low_confidence_results) - low_confidence_failed_count,
        "low_confidence_failed_count": low_confidence_failed_count,
        "by_expected_scenario": dict(sorted(by_expected_scenario.items())),
        "by_actual_scenario": dict(sorted(by_actual_scenario.items())),
        "by_expected_task_type": dict(sorted(by_expected_task_type.items())),
        "by_confidence": dict(sorted(by_confidence.items())),
        "by_issue": dict(sorted(by_issue.items())),
        "by_issue_class": dict(sorted(by_issue_class.items())),
    }

def run_router_eval(
    eval_path: Path,
    registry_dir: Path,
    bundles_path: Path,
    overlap_groups_path: Path | None = None,
    max_skills: int = 8,
) -> dict:
    payload = load_router_eval(eval_path)
    cases = payload["cases"]
    declared_count = payload.get("case_count")
    results = []
    issues = []
    if declared_count is not None and declared_count != len(cases):
        issues.append(
            {
                "id": "router-eval-count-mismatch",
                "severity": "medium",
                "expected": len(cases),
                "actual": declared_count,
            }
        )
    for index, case in enumerate(cases):
        case_id = case.get("id", f"case-{index + 1}")
        task = case.get("task", "")
        router_mode = case.get("router", "scenario")
        case_issues = []
        if not isinstance(task, str) or not task:
            case_issues.append({"id": "router-eval-missing-task"})
        if isinstance(router_mode, str) and router_mode not in ROUTER_EVAL_ROUTER_VALUES:
            case_issues.append({"id": "router-eval-invalid-router", "router": router_mode})
        case_issues.extend(validate_router_eval_case(case))
        if case_issues:
            results.append(
                {
                    "id": case_id,
                    "status": "failed",
                    "actual_confidence": "",
                    "actual_low_confidence": False,
                    "issues": annotate_router_eval_issues(case_issues),
                }
            )
            continue

        task_pack = build_task_pack(
            registry_dir=registry_dir,
            task=task,
            top=max_skills,
            include_review_required=False,
            include_bundles=True,
            bundles_path=bundles_path,
            router_mode=router_mode,
            max_skills=max_skills,
            invariants=case.get("invariants"),
            strategy=case.get("strategy", "balanced"),
            overlap_groups_path=overlap_groups_path,
        )
        actual_scenario = task_pack.get("selected_scenario", {}).get("id", "")
        actual_task_type = task_pack.get("task_profile", {}).get("task_type", "")
        actual_selection_quality = task_pack.get("selection_quality", {})
        actual_confidence = actual_selection_quality.get("confidence", "")
        actual_low_confidence = actual_selection_quality.get("low_confidence") is True
        actual_skills = [skill["name"] for skill in task_pack.get("skills", [])]
        actual_skill_subcategories = {
            skill["name"]: skill.get("taxonomy", {}).get("subcategory", "") for skill in task_pack.get("skills", [])
        }
        actual_selection_trace = router_eval_trace_summary(task_pack.get("selection_trace", {}))
        expected_scenario = case.get("expected_scenario")
        expected_task_type = case.get("expected_task_type")
        expected_skills = case.get("expected_skills", [])
        forbidden_skills = case.get("forbidden_skills", [])
        forbidden_skill_prefixes = case.get("forbidden_skill_prefixes", [])
        forbidden_skill_subcategories = case.get("forbidden_skill_subcategories", [])
        expected_trace_selected = case.get("expected_trace_selected", [])
        expected_trace_pruned = case.get("expected_trace_pruned", [])
        expected_trace_required = case.get("expected_trace_required", [])
        expected_trace_reason_codes = case.get("expected_trace_reason_codes", [])
        max_skill_count = case.get("max_skill_count")

        if expected_scenario is not None and actual_scenario != expected_scenario:
            case_issues.append(
                {
                    "id": "router-eval-scenario-mismatch",
                    "expected": expected_scenario,
                    "actual": actual_scenario,
                }
            )
        if expected_task_type is not None and actual_task_type != expected_task_type:
            case_issues.append(
                {
                    "id": "router-eval-task-type-mismatch",
                    "expected": expected_task_type,
                    "actual": actual_task_type,
                }
            )
        for skill_name in expected_skills:
            if skill_name not in actual_skills:
                case_issues.append(
                    {
                        "id": "router-eval-missing-skill",
                        "skill": skill_name,
                    }
                )
        for skill_name in forbidden_skills:
            if skill_name in actual_skills:
                case_issues.append(
                    {
                        "id": "router-eval-forbidden-skill",
                        "skill": skill_name,
                    }
                )
        for prefix in forbidden_skill_prefixes:
            for skill_name in actual_skills:
                if skill_name.startswith(prefix):
                    case_issues.append(
                        {
                            "id": "router-eval-forbidden-skill-prefix",
                            "prefix": prefix,
                            "skill": skill_name,
                        }
                    )
        for subcategory in forbidden_skill_subcategories:
            for skill_name, actual_subcategory in actual_skill_subcategories.items():
                if actual_subcategory == subcategory:
                    case_issues.append(
                        {
                            "id": "router-eval-forbidden-skill-subcategory",
                            "subcategory": subcategory,
                            "skill": skill_name,
                        }
                    )
        if isinstance(max_skill_count, int) and len(actual_skills) > max_skill_count:
            case_issues.append(
                {
                    "id": "router-eval-max-skill-count-exceeded",
                    "expected_max": max_skill_count,
                    "actual": len(actual_skills),
                }
            )
        for skill_name in expected_trace_selected:
            if skill_name not in actual_selection_trace["selected"]:
                case_issues.append(
                    {
                        "id": "router-eval-trace-missing-selected",
                        "skill": skill_name,
                    }
                )
        for skill_name in expected_trace_required:
            if skill_name not in actual_selection_trace["required"]:
                case_issues.append(
                    {
                        "id": "router-eval-trace-missing-required",
                        "skill": skill_name,
                    }
                )
        for skill_name in expected_trace_pruned:
            if skill_name not in actual_selection_trace["pruned"]:
                case_issues.append(
                    {
                        "id": "router-eval-trace-missing-pruned",
                        "skill": skill_name,
                    }
                )
        for reason_code in expected_trace_reason_codes:
            if reason_code not in actual_selection_trace["reason_codes"]:
                case_issues.append(
                    {
                        "id": "router-eval-trace-missing-reason-code",
                        "reason_code": reason_code,
                    }
                )

        result_context = {
            "expected_scenario": expected_scenario,
            "actual_scenario": actual_scenario,
            "expected_task_type": expected_task_type,
            "actual_task_type": actual_task_type,
        }
        results.append(
            {
                "id": case_id,
                "status": "failed" if case_issues else "ok",
                "router": router_mode,
                "task": task,
                "expected_scenario": expected_scenario,
                "actual_scenario": actual_scenario,
                "expected_task_type": expected_task_type,
                "actual_task_type": actual_task_type,
                "actual_confidence": actual_confidence,
                "actual_low_confidence": actual_low_confidence,
                "max_skill_count": max_skill_count,
                "actual_skills": actual_skills,
                "actual_selection_trace": actual_selection_trace,
                "issues": annotate_router_eval_issues(case_issues, result_context),
            }
        )

    failed_count = sum(1 for item in results if item["status"] != "ok")
    return {
        "schema_version": 1,
        "generated_at": utc_now(),
        "status": "failed" if failed_count or issues else "ok",
        "case_count": len(cases),
        "passed_count": len(cases) - failed_count,
        "failed_count": failed_count,
        "issues": issues,
        "quality_summary": build_router_eval_quality_summary(results, issues),
        "cases": results,
    }

def router_eval_trace_summary(selection_trace: dict) -> dict:
    candidates = selection_trace.get("candidates", [])
    selected = [
        item.get("name", "")
        for item in candidates
        if item.get("selected") is True and item.get("name")
    ]
    required = [
        item.get("name", "")
        for item in candidates
        if item.get("required") is True and item.get("name")
    ]
    pruned = [
        item.get("name", "")
        for item in selection_trace.get("pruned", [])
        if item.get("name")
    ]
    quality = selection_trace.get("quality", {})
    return {
        "selected_count": selection_trace.get("selected_count", len(selected)),
        "candidate_count": selection_trace.get("candidate_count", len(candidates)),
        "required_skill_count": selection_trace.get("required_skill_count", len(required)),
        "selected": selected,
        "required": required,
        "pruned": pruned,
        "reason_codes": list(quality.get("reason_codes", [])),
    }
