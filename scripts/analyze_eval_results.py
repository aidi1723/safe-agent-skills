#!/usr/bin/env python3
"""
Analyze three-arm evaluation results.

Usage:
    python scripts/analyze_eval_results.py evals/three-arm-results/eval-20260912-*.json
    python scripts/analyze_eval_results.py evals/three-arm-results/eval-20260912-*.json --report report.md
"""

import argparse
import json
from pathlib import Path
from typing import Dict, List
from collections import defaultdict


def load_results(result_file: Path) -> Dict:
    """Load evaluation results from JSON file."""
    with open(result_file, 'r', encoding='utf-8') as f:
        return json.load(f)


def analyze_by_category(results: List[Dict]) -> Dict:
    """Analyze results grouped by task category."""
    by_category = defaultdict(list)

    for result in results:
        category = result["category"]
        by_category[category].append(result)

    category_stats = {}
    for category, tasks in by_category.items():
        scenario_matches = sum(
            1 for t in tasks
            if t["metrics"].get("scenario_match", False)
        )
        avg_f1 = sum(
            t["metrics"].get("skill_f1", 0)
            for t in tasks
        ) / len(tasks)

        category_stats[category] = {
            "task_count": len(tasks),
            "scenario_match_rate": scenario_matches / len(tasks),
            "avg_skill_f1": avg_f1
        }

    return category_stats


def analyze_by_complexity(results: List[Dict]) -> Dict:
    """Analyze results grouped by task complexity."""
    by_complexity = defaultdict(list)

    for result in results:
        complexity = result["complexity"]
        by_complexity[complexity].append(result)

    complexity_stats = {}
    for complexity, tasks in by_complexity.items():
        scenario_matches = sum(
            1 for t in tasks
            if t["metrics"].get("scenario_match", False)
        )
        avg_f1 = sum(
            t["metrics"].get("skill_f1", 0)
            for t in tasks
        ) / len(tasks) if tasks else 0

        complexity_stats[complexity] = {
            "task_count": len(tasks),
            "scenario_match_rate": scenario_matches / len(tasks) if tasks else 0,
            "avg_skill_f1": avg_f1
        }

    return complexity_stats


def find_failure_cases(results: List[Dict]) -> Dict:
    """Find and categorize failure cases."""
    failures = {
        "scenario_mismatch": [],
        "low_precision": [],
        "low_recall": [],
        "blocked_route": [],
        "incomplete_route": []
    }

    for result in results:
        task_id = result["task_id"]
        metrics = result["metrics"]

        if not metrics.get("scenario_match", True):
            failures["scenario_mismatch"].append({
                "task_id": task_id,
                "description": result["description"][:60],
                "expected": result["arms"]["oracle"]["selected_scenario"],
                "actual": result["arms"]["v3"]["selected_scenario"]
            })

        if metrics.get("skill_precision", 1.0) < 0.7:
            failures["low_precision"].append({
                "task_id": task_id,
                "description": result["description"][:60],
                "precision": metrics["skill_precision"]
            })

        if metrics.get("skill_recall", 1.0) < 0.7:
            failures["low_recall"].append({
                "task_id": task_id,
                "description": result["description"][:60],
                "recall": metrics["skill_recall"]
            })

        if metrics.get("route_blocked", False):
            failures["blocked_route"].append({
                "task_id": task_id,
                "description": result["description"][:60]
            })

        if not metrics.get("route_complete", True):
            failures["incomplete_route"].append({
                "task_id": task_id,
                "description": result["description"][:60]
            })

    return failures


def generate_markdown_report(
    data: Dict,
    category_stats: Dict,
    complexity_stats: Dict,
    failures: Dict
) -> str:
    """Generate markdown report."""
    report = []

    report.append("# Three-Arm Evaluation Report")
    report.append("")
    report.append(f"**Evaluated At**: {data['evaluated_at']}")
    report.append(f"**Task Count**: {data['task_count']}")
    report.append(f"**Arms**: {', '.join(data['arms_evaluated'])}")
    report.append("")

    # Aggregate metrics
    report.append("## Overall Results")
    report.append("")
    metrics = data['aggregate_metrics']
    report.append(f"- **Scenario Match Rate**: {metrics['scenario_match_rate']:.2%}")
    report.append(f"- **Avg Skill Precision**: {metrics['avg_skill_precision']:.2%}")
    report.append(f"- **Avg Skill Recall**: {metrics['avg_skill_recall']:.2%}")
    report.append(f"- **Avg Skill F1**: {metrics['avg_skill_f1']:.2%}")
    report.append(f"- **Route Completion Rate**: {metrics['route_completion_rate']:.2%}")
    report.append(f"- **Route Blocked Rate**: {metrics['route_blocked_rate']:.2%}")
    report.append("")

    # Passing criteria
    report.append("## Acceptance Criteria")
    report.append("")
    report.append("| Criterion | Status |")
    report.append("|-----------|--------|")
    for criterion, passed in metrics['passing_criteria'].items():
        status = "✅ PASS" if passed else "❌ FAIL"
        report.append(f"| {criterion} | {status} |")
    report.append("")

    # Category breakdown
    report.append("## Results by Category")
    report.append("")
    report.append("| Category | Tasks | Scenario Match | Avg F1 |")
    report.append("|----------|-------|----------------|--------|")
    for category, stats in sorted(category_stats.items()):
        report.append(
            f"| {category} | {stats['task_count']} | "
            f"{stats['scenario_match_rate']:.0%} | "
            f"{stats['avg_skill_f1']:.2f} |"
        )
    report.append("")

    # Complexity breakdown
    report.append("## Results by Complexity")
    report.append("")
    report.append("| Complexity | Tasks | Scenario Match | Avg F1 |")
    report.append("|------------|-------|----------------|--------|")
    for complexity in ["low", "medium", "high", "very-high"]:
        if complexity in complexity_stats:
            stats = complexity_stats[complexity]
            report.append(
                f"| {complexity} | {stats['task_count']} | "
                f"{stats['scenario_match_rate']:.0%} | "
                f"{stats['avg_skill_f1']:.2f} |"
            )
    report.append("")

    # Failure analysis
    report.append("## Failure Analysis")
    report.append("")

    if failures["scenario_mismatch"]:
        report.append(f"### Scenario Mismatches ({len(failures['scenario_mismatch'])})")
        report.append("")
        for f in failures["scenario_mismatch"][:10]:
            report.append(f"- **{f['task_id']}**: {f['description']}")
            report.append(f"  - Expected: `{f['expected']}`")
            report.append(f"  - Actual: `{f['actual']}`")
        report.append("")

    if failures["low_precision"]:
        report.append(f"### Low Precision (<0.7) ({len(failures['low_precision'])})")
        report.append("")
        for f in failures["low_precision"][:10]:
            report.append(f"- **{f['task_id']}**: {f['description']} (precision: {f['precision']:.2f})")
        report.append("")

    if failures["low_recall"]:
        report.append(f"### Low Recall (<0.7) ({len(failures['low_recall'])})")
        report.append("")
        for f in failures["low_recall"][:10]:
            report.append(f"- **{f['task_id']}**: {f['description']} (recall: {f['recall']:.2f})")
        report.append("")

    if failures["blocked_route"]:
        report.append(f"### Blocked Routes ({len(failures['blocked_route'])})")
        report.append("")
        for f in failures["blocked_route"][:10]:
            report.append(f"- **{f['task_id']}**: {f['description']}")
        report.append("")

    # Recommendations
    report.append("## Recommendations")
    report.append("")

    overall_pass = all(metrics['passing_criteria'].values())

    if overall_pass:
        report.append("✅ **Router v3 passes all acceptance criteria.**")
        report.append("")
        report.append("Recommended actions:")
        report.append("1. Proceed with final_test under explicit authorization")
        report.append("2. Make Router v3 the default schema")
        report.append("3. Keep Router v2 as fallback (--schema-version 2)")
    else:
        report.append("❌ **Router v3 does not meet all acceptance criteria.**")
        report.append("")
        report.append("Required improvements:")

        if metrics['scenario_match_rate'] < 0.90:
            report.append("- Improve scenario matching logic")
        if metrics['avg_skill_f1'] < 0.85:
            report.append("- Refine skill selection algorithm")
        if metrics['route_completion_rate'] < 0.95:
            report.append("- Fix incomplete route issues")
        if metrics['route_blocked_rate'] >= 0.05:
            report.append("- Resolve blocked route cases")

    report.append("")

    return "\n".join(report)


def main():
    parser = argparse.ArgumentParser(
        description="Analyze three-arm evaluation results"
    )
    parser.add_argument(
        "result_file",
        type=Path,
        help="Path to evaluation result JSON file"
    )
    parser.add_argument(
        "--report",
        type=Path,
        default=None,
        help="Output markdown report file"
    )

    args = parser.parse_args()

    # Load results
    data = load_results(args.result_file)
    results = data["results"]

    # Analyze
    category_stats = analyze_by_category(results)
    complexity_stats = analyze_by_complexity(results)
    failures = find_failure_cases(results)

    # Generate report
    report = generate_markdown_report(
        data,
        category_stats,
        complexity_stats,
        failures
    )

    # Output
    if args.report:
        with open(args.report, 'w', encoding='utf-8') as f:
            f.write(report)
        print(f"Report saved to: {args.report}")
    else:
        print(report)


if __name__ == "__main__":
    main()
