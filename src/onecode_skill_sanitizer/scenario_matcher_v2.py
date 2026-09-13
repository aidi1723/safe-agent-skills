"""
Scenario Bundle Matcher v2 for Router v3 Phase 4

Matches tasks to Bundle v2 scenarios with core/conditional selection logic.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .bundle_selection import apply_bundle_selection_logic
from .scenario_matcher import (
    calculate_scenario_score,
    SCENARIO_MATCH_THRESHOLD,
)


def load_scenario_bundles_v2(bundles_path: Path) -> list[dict[str, Any]]:
    """Load Bundle v2 scenarios from index-v2-tier1.json"""
    if not bundles_path.exists():
        return []

    content = bundles_path.read_text(encoding="utf-8")
    data = json.loads(content)
    return data.get("bundles", [])


def match_scenario_bundle_v2(
    task: str,
    bundles_path: Path,
    threshold: float = SCENARIO_MATCH_THRESHOLD
) -> dict[str, Any] | None:
    """
    Match task to Bundle v2 scenario and apply selection logic.

    Args:
        task: Normalized task description
        bundles_path: Path to bundles/index-v2-tier1.json
        threshold: Minimum score to accept a match (default 0.15)

    Returns:
        Matched scenario dict with:
        - match_score: Scenario matching score
        - skills: List of selected skills after applying selection logic
        - skill_selection: Dict with core_count, conditional_matched, etc.
    """
    bundles = load_scenario_bundles_v2(bundles_path)

    if not bundles:
        return None

    # Score all bundles using existing scenario matcher logic
    scored_bundles = []
    for bundle in bundles:
        score = calculate_scenario_score(task, bundle)
        scored_bundles.append((bundle, score))

    # Sort by score descending
    scored_bundles.sort(key=lambda x: x[1], reverse=True)

    # Return best match if above threshold
    best_bundle, best_score = scored_bundles[0]

    if best_score >= threshold:
        # Apply selection logic to get actual skills
        selected_skills = apply_bundle_selection_logic(task, best_bundle)

        # Analyze selection
        selection_logic = best_bundle.get("selection_logic", {})
        core_skills = selection_logic.get("always_select", [])
        conditional_rules = selection_logic.get("conditional", [])

        conditional_matched = []
        conditional_skipped = []

        for rule in conditional_rules:
            skill = rule["skill"]
            if skill in selected_skills:
                conditional_matched.append(skill)
            else:
                conditional_skipped.append(skill)

        return {
            **best_bundle,
            "match_score": best_score,
            "match_confidence": "high" if best_score >= 0.6 else "medium",
            "skills": selected_skills,
            "skill_selection": {
                "core_count": len(core_skills),
                "conditional_matched": conditional_matched,
                "conditional_skipped": conditional_skipped,
            }
        }

    return None
