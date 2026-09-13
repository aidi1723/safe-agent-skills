"""
Bundle v2 Selection Logic for Router v3 Phase 4

Applies core/conditional skill selection from Bundle v2 scenarios.
"""

from __future__ import annotations

import re
from typing import Any


def apply_bundle_selection_logic(
    task: str,
    bundle: dict[str, Any]
) -> list[str]:
    """
    Apply bundle selection logic to determine actual skills to use.

    Args:
        task: Normalized task description
        bundle: Bundle v2 dict with selection_logic field

    Returns:
        List of selected skill names (core + matched conditionals)
    """
    selection_logic = bundle.get("selection_logic", {})

    # Always select core skills
    selected = list(selection_logic.get("always_select", []))

    # Check conditional skills
    conditional_rules = selection_logic.get("conditional", [])
    task_lower = task.lower()

    for rule in conditional_rules:
        skill = rule.get("skill")
        trigger = rule.get("trigger")

        if not skill or not trigger:
            continue

        # Check if any trigger keyword appears in task
        if re.search(trigger, task_lower, re.IGNORECASE):
            selected.append(skill)

    return selected
