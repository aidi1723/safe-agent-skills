#!/usr/bin/env python3
"""Quick test for Bundle v2 selection logic"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from onecode_skill_sanitizer.task_pack_v3 import build_task_pack_v3

# Test case 1: Refactor task (should trigger code-refactor conditional)
print("Test 1: Refactor task")
print("-" * 60)
task = "重构这个模块，提升可读性和可维护性，保持功能不变"
result = build_task_pack_v3(
    Path("catalog"),
    task,
    Path("bundles/index-v2-tier1.json"),
    Path("catalog/routing-examples.json"),
    use_bundle_v2=True,
)

selected_skills = [s["name"] for s in result["selection"]["selected_skills"]]
print(f"Selected skills: {selected_skills}")
print(f"Selection method: {result['selection'].get('selection_method')}")

if "scenario_match" in result["selection"]:
    sm = result["selection"]["scenario_match"]
    print(f"Scenario: {sm.get('id')} (score: {sm.get('score'):.3f})")
    print(f"Core count: {sm.get('core_count')}")
    print(f"Conditional matched: {sm.get('conditional_matched')}")
    print(f"Conditional skipped: {sm.get('conditional_skipped')}")

print()
if "code-refactor" in selected_skills:
    print("✓ PASS: code-refactor conditional triggered")
else:
    print("✗ FAIL: code-refactor NOT found")
    print(f"   Expected: code-refactor to be in {selected_skills}")
