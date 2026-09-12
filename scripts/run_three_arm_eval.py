#!/usr/bin/env python3
"""
Three-arm evaluation script for Router v3 acceptance testing.

Compares three approaches:
- Arm 1: Router v3 automatic skill selection
- Arm 2: Oracle (expert manual selection)
- Arm 3: Baseline (no skill guidance)

Usage:
    python scripts/run_three_arm_eval.py --tasks evals/three-arm-tasks/task-list.json
    python scripts/run_three_arm_eval.py --tasks evals/three-arm-tasks/task-list.json --arms v3,oracle
"""

import argparse
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional


def load_tasks(task_file: Path) -> Dict:
    """Load task list from JSON file."""
    with open(task_file, 'r', encoding='utf-8') as f:
        return json.load(f)


def run_v3_router(task_description: str, registry: Path, bundles: Path) -> Dict:
    """
    Run Router v3 on a task and return selected skills.

    Returns:
        {
            "selected_scenario": str or None,
            "selected_skills": List[str],
            "execution_graph": Dict,
            "route_status": str  # "complete" | "incomplete" | "blocked"
        }
    """
    cmd = [
        "python3", "-m", "onecode_skill_sanitizer",
        "smart",
        task_description,
        "--schema-version", "3",
        "--registry", str(registry),
        "--bundles", str(bundles),
        "--format", "json"
    ]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30,
            env={"PYTHONPATH": "src"}
        )

        if result.returncode == 0:
            output = json.loads(result.stdout)
            return {
                "selected_scenario": output.get("selection", {}).get("selected_scenario"),
                "selected_skills": [
                    skill["name"]
                    for skill in output.get("selection", {}).get("selected_skills", [])
                ],
                "execution_graph": output.get("execution_graph", {}),
                "route_status": output.get("route_status", "unknown"),
                "raw_output": output
            }
        else:
            return {
                "selected_scenario": None,
                "selected_skills": [],
                "execution_graph": {},
                "route_status": "error",
                "error": result.stderr
            }
    except Exception as e:
        return {
            "selected_scenario": None,
            "selected_skills": [],
            "execution_graph": {},
            "route_status": "error",
            "error": str(e)
        }


def get_oracle_selection(task: Dict) -> Dict:
    """
    Get oracle (expert) selection for a task.
    This uses the expected_skills from the task definition as the oracle.

    In a real evaluation, this would be manual expert selection.
    """
    return {
        "selected_scenario": task.get("expected_scenario"),
        "selected_skills": task.get("expected_skills", []),
        "source": "oracle_predefined"
    }


def get_baseline_selection() -> Dict:
    """
    Baseline: no skill guidance.
    """
    return {
        "selected_scenario": None,
        "selected_skills": [],
        "source": "baseline_no_skills"
    }


def evaluate_single_task(
    task: Dict,
    arms: List[str],
    registry: Path,
    bundles: Path
) -> Dict:
    """
    Evaluate a single task across selected arms.

    Args:
        task: Task definition
        arms: List of arms to evaluate ("v3", "oracle", "baseline")
        registry: Path to skill registry
        bundles: Path to bundles index

    Returns:
        Evaluation result for this task
    """
    task_id = task["id"]
    description = task["description"]

    print(f"Evaluating {task_id}: {description[:60]}...")

    result = {
        "task_id": task_id,
        "description": description,
        "category": task["category"],
        "complexity": task["complexity"],
        "arms": {}
    }

    if "v3" in arms:
        print(f"  Running v3 router...")
        result["arms"]["v3"] = run_v3_router(description, registry, bundles)

    if "oracle" in arms:
        print(f"  Getting oracle selection...")
        result["arms"]["oracle"] = get_oracle_selection(task)

    if "baseline" in arms:
        print(f"  Getting baseline (no skills)...")
        result["arms"]["baseline"] = get_baseline_selection()

    # Calculate metrics
    result["metrics"] = calculate_task_metrics(result, task)

    return result


def calculate_task_metrics(result: Dict, task: Dict) -> Dict:
    """
    Calculate metrics for a single task evaluation.

    Metrics:
    - scenario_match: Does v3 match expected scenario?
    - skill_precision: Precision of v3 vs oracle
    - skill_recall: Recall of v3 vs oracle
    - skill_f1: F1 score of v3 vs oracle
    - route_quality: Is route complete/incomplete/blocked?
    """
    metrics = {}

    v3_result = result["arms"].get("v3", {})
    oracle_result = result["arms"].get("oracle", {})

    # Scenario match
    if v3_result and oracle_result:
        v3_scenario = v3_result.get("selected_scenario")
        expected_scenario = oracle_result.get("selected_scenario")
        metrics["scenario_match"] = (v3_scenario == expected_scenario)

    # Skill precision/recall
    if v3_result and oracle_result:
        v3_skills = set(v3_result.get("selected_skills", []))
        oracle_skills = set(oracle_result.get("selected_skills", []))

        if len(v3_skills) > 0:
            true_positives = len(v3_skills & oracle_skills)
            precision = true_positives / len(v3_skills)
            metrics["skill_precision"] = precision
        else:
            metrics["skill_precision"] = 0.0

        if len(oracle_skills) > 0:
            true_positives = len(v3_skills & oracle_skills)
            recall = true_positives / len(oracle_skills)
            metrics["skill_recall"] = recall
        else:
            metrics["skill_recall"] = 1.0 if len(v3_skills) == 0 else 0.0

        # F1 score
        if metrics["skill_precision"] + metrics["skill_recall"] > 0:
            metrics["skill_f1"] = (
                2 * metrics["skill_precision"] * metrics["skill_recall"] /
                (metrics["skill_precision"] + metrics["skill_recall"])
            )
        else:
            metrics["skill_f1"] = 0.0

    # Route quality
    if v3_result:
        route_status = v3_result.get("route_status", "unknown")
        metrics["route_complete"] = (route_status == "complete")
        metrics["route_blocked"] = (route_status == "blocked")

    return metrics


def calculate_aggregate_metrics(results: List[Dict]) -> Dict:
    """Calculate aggregate metrics across all tasks."""
    total_tasks = len(results)

    if total_tasks == 0:
        return {}

    # Aggregate metrics
    scenario_matches = sum(
        1 for r in results
        if r["metrics"].get("scenario_match", False)
    )

    avg_precision = sum(
        r["metrics"].get("skill_precision", 0)
        for r in results
    ) / total_tasks

    avg_recall = sum(
        r["metrics"].get("skill_recall", 0)
        for r in results
    ) / total_tasks

    avg_f1 = sum(
        r["metrics"].get("skill_f1", 0)
        for r in results
    ) / total_tasks

    complete_routes = sum(
        1 for r in results
        if r["metrics"].get("route_complete", False)
    )

    blocked_routes = sum(
        1 for r in results
        if r["metrics"].get("route_blocked", False)
    )

    return {
        "total_tasks": total_tasks,
        "scenario_match_rate": scenario_matches / total_tasks,
        "avg_skill_precision": avg_precision,
        "avg_skill_recall": avg_recall,
        "avg_skill_f1": avg_f1,
        "route_completion_rate": complete_routes / total_tasks,
        "route_blocked_rate": blocked_routes / total_tasks,
        "passing_criteria": {
            "scenario_match_rate >= 0.90": scenario_matches / total_tasks >= 0.90,
            "avg_skill_f1 >= 0.85": avg_f1 >= 0.85,
            "route_completion_rate >= 0.95": complete_routes / total_tasks >= 0.95,
            "route_blocked_rate < 0.05": blocked_routes / total_tasks < 0.05
        }
    }


def main():
    parser = argparse.ArgumentParser(
        description="Run three-arm evaluation for Router v3"
    )
    parser.add_argument(
        "--tasks",
        type=Path,
        required=True,
        help="Path to task list JSON file"
    )
    parser.add_argument(
        "--arms",
        type=str,
        default="v3,oracle,baseline",
        help="Comma-separated list of arms to evaluate (default: v3,oracle,baseline)"
    )
    parser.add_argument(
        "--registry",
        type=Path,
        default=Path("catalog"),
        help="Path to skill registry (default: catalog)"
    )
    parser.add_argument(
        "--bundles",
        type=Path,
        default=Path("bundles/index.json"),
        help="Path to bundles index (default: bundles/index.json)"
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Output file for results (default: evals/three-arm-results/<timestamp>.json)"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Limit number of tasks to evaluate (for testing)"
    )

    args = parser.parse_args()

    # Load tasks
    task_data = load_tasks(args.tasks)
    tasks = task_data["tasks"]

    if args.limit:
        tasks = tasks[:args.limit]
        print(f"Limiting evaluation to {args.limit} tasks")

    arms = args.arms.split(",")
    print(f"Evaluating {len(tasks)} tasks across arms: {', '.join(arms)}")
    print()

    # Run evaluation
    results = []
    for i, task in enumerate(tasks, 1):
        print(f"[{i}/{len(tasks)}] ", end="")
        result = evaluate_single_task(task, arms, args.registry, args.bundles)
        results.append(result)
        print()

    # Calculate aggregate metrics
    aggregate = calculate_aggregate_metrics(results)

    # Prepare output
    output_data = {
        "evaluation_name": "three_arm_router_v3_acceptance",
        "evaluated_at": datetime.now().isoformat(),
        "task_file": str(args.tasks),
        "arms_evaluated": arms,
        "task_count": len(tasks),
        "results": results,
        "aggregate_metrics": aggregate
    }

    # Save results
    if args.output:
        output_file = args.output
    else:
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        output_file = Path(f"evals/three-arm-results/eval-{timestamp}.json")

    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)

    print(f"\n{'='*60}")
    print(f"Evaluation complete!")
    print(f"{'='*60}")
    print(f"Results saved to: {output_file}")
    print()
    print("Aggregate Metrics:")
    print(f"  Total tasks: {aggregate['total_tasks']}")
    print(f"  Scenario match rate: {aggregate['scenario_match_rate']:.2%}")
    print(f"  Avg skill precision: {aggregate['avg_skill_precision']:.2%}")
    print(f"  Avg skill recall: {aggregate['avg_skill_recall']:.2%}")
    print(f"  Avg skill F1: {aggregate['avg_skill_f1']:.2%}")
    print(f"  Route completion rate: {aggregate['route_completion_rate']:.2%}")
    print(f"  Route blocked rate: {aggregate['route_blocked_rate']:.2%}")
    print()
    print("Passing Criteria:")
    for criterion, passed in aggregate["passing_criteria"].items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"  {status} {criterion}")
    print()

    # Exit with appropriate code
    all_passed = all(aggregate["passing_criteria"].values())
    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    main()
