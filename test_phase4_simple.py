#!/usr/bin/env python3
"""
Simple test for Phase 4 Bundle v2 implementation
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from onecode_skill_sanitizer.task_pack_v3 import build_task_pack_v3

def test_refactor_with_conditional():
    """Test that refactor task triggers code-refactor conditional"""
    task = "重构这个模块，提升可读性和可维护性，保持功能不变"

    result = build_task_pack_v3(
        registry_dir=Path("catalog"),
        task=task,
        bundles_path=Path("bundles/index-v2-tier1.json"),
        routing_examples_path=Path("bundles/routing-examples.json"),
        max_candidates=3,
        use_bundle_v2=True,
    )

    skills = [s["name"] for s in result["selection"]["selected_skills"]]

    print("Test 1: Refactor task (should trigger conditional)")
    print(f"  Task: {task}")
    print(f"  Selected skills: {skills}")
    print(f"  Expected: code-review-risk, code-test-regression, code-refactor")

    has_refactor = "code-refactor" in skills
    print(f"  ✓ PASS: code-refactor triggered" if has_refactor else "  ✗ FAIL: code-refactor NOT triggered")

    return has_refactor

def test_write_tests_without_conditional():
    """Test that test task does NOT trigger code-refactor conditional"""
    task = "为这个模块编写测试用例，覆盖核心功能和边界情况"

    result = build_task_pack_v3(
        registry_dir=Path("catalog"),
        task=task,
        bundles_path=Path("bundles/index-v2-tier1.json"),
        routing_examples_path=Path("bundles/routing-examples.json"),
        max_candidates=3,
        use_bundle_v2=True,
    )

    skills = [s["name"] for s in result["selection"]["selected_skills"]]

    print("\nTest 2: Write tests (should NOT trigger refactor conditional)")
    print(f"  Task: {task}")
    print(f"  Selected skills: {skills}")
    print(f"  Expected: code-review-risk, code-test-regression (NO code-refactor)")

    has_refactor = "code-refactor" in skills
    print(f"  ✗ FAIL: code-refactor triggered incorrectly" if has_refactor else "  ✓ PASS: code-refactor NOT triggered")

    return not has_refactor

def test_website_scenario():
    """Test website scenario selection"""
    task = "构建一个产品官网，包含响应式设计、SEO优化和性能检查"

    result = build_task_pack_v3(
        registry_dir=Path("catalog"),
        task=task,
        bundles_path=Path("bundles/index-v2-tier1.json"),
        routing_examples_path=Path("bundles/routing-examples.json"),
        max_candidates=3,
        use_bundle_v2=True,
    )

    skills = [s["name"] for s in result["selection"]["selected_skills"]]
    scenario = result["selection"].get("selected_scenario")

    print("\nTest 3: Website task")
    print(f"  Task: {task}")
    print(f"  Scenario: {scenario}")
    print(f"  Selected skills: {skills}")
    print(f"  Expected: 3 skills (not 14 like old bundle)")

    is_correct_count = len(skills) == 3
    print(f"  ✓ PASS: Correct skill count" if is_correct_count else f"  ✗ FAIL: Wrong skill count ({len(skills)})")

    return is_correct_count

if __name__ == "__main__":
    print("=" * 60)
    print("Phase 4 Bundle v2 Quick Tests")
    print("=" * 60)

    test1 = test_refactor_with_conditional()
    test2 = test_write_tests_without_conditional()
    test3 = test_website_scenario()

    print("\n" + "=" * 60)
    print("Summary:")
    print(f"  Test 1 (refactor conditional): {'PASS' if test1 else 'FAIL'}")
    print(f"  Test 2 (no conditional): {'PASS' if test2 else 'FAIL'}")
    print(f"  Test 3 (website precision): {'PASS' if test3 else 'FAIL'}")
    print("=" * 60)

    sys.exit(0 if all([test1, test2, test3]) else 1)
