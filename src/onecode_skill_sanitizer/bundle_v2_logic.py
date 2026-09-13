"""
Bundle v2 Selection Logic

Applies core/conditional skill selection for Bundle v2 scenarios.
"""

from __future__ import annotations

import re
from typing import Any


def apply_bundle_selection_logic(
    task: str,
    bundle: dict[str, Any]
) -> list[str]:
    """
    Apply Bundle v2 selection logic to extract task-specific skills.
    
    Args:
        task: Normalized task description
        bundle: Bundle v2 dict with core_skills, conditional_skills, selection_logic
    
    Returns:
        List of selected skill names (core + matching conditionals)
    """
    # Always select core skills
    selected = list(bundle.get("core_skills", []))
    
    # Check conditional skills
    selection_logic = bundle.get("selection_logic", {})
    conditionals = selection_logic.get("conditional", [])
    
    task_lower = task.lower()
    
    for condition in conditionals:
        skill_name = condition["skill"]
        trigger_pattern = condition["trigger"]
        
        # Check if task matches trigger pattern (case-insensitive regex)
        if re.search(trigger_pattern, task_lower, re.IGNORECASE):
            selected.append(skill_name)
    
    return selected


def is_bundle_v2(bundle: dict[str, Any]) -> bool:
    """
    Check if a bundle uses v2 structure (has core_skills field).
    
    Args:
        bundle: Bundle dict
    
    Returns:
        True if bundle has v2 structure
    """
    return "core_skills" in bundle
