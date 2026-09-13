#!/bin/bash
# Manual test script for Bundle v2 validation
# Run: bash scripts/test_bundle_v2_manual.sh

set -e

cd "$(dirname "$0")/.."

echo "=== Bundle v2 Manual Test ==="
echo

# Test 1: Website task with Bundle v2
echo "Test 1: Website responsive SEO task"
echo "Task: 构建一个产品官网，包含响应式设计、SEO优化和性能检查"
echo

PYTHONPATH=src python3 -m onecode_skill_sanitizer smart \
  "构建一个产品官网，包含响应式设计、SEO优化和性能检查" \
  --schema-version 3 \
  --registry catalog \
  --bundles bundles/index.json \
  --routing-examples evals/routing-examples.json \
  --format json \
  --use-bundle-v2 \
  2>&1 | jq -r '
"✓ Need Decision: \(.need_decision.decision)",
"✓ Specialized: \(.need_decision.specialized_need)",
"✓ Selection Method: \(.selection.selection_method)",
"✓ Selected Scenario: \(.selection.selected_scenario // "none")",
"✓ Skill Count: \(.selection.selected_skills | length)",
"✓ Skills: \(.selection.selected_skills | map(.name) | join(", "))"
'

echo
echo "Expected: 3 skills (design-responsive-viewport-check, content-seo-brief, execution-browser-check)"
echo

# Test 2: Code refactor task with conditional triggering
echo "Test 2: Code refactor task (should trigger conditional)"
echo "Task: 重构这个模块，提升可读性和可维护性，保持功能不变"
echo

PYTHONPATH=src python3 -m onecode_skill_sanitizer smart \
  "重构这个模块，提升可读性和可维护性，保持功能不变" \
  --schema-version 3 \
  --registry catalog \
  --bundles bundles/index.json \
  --routing-examples evals/routing-examples.json \
  --format json \
  --use-bundle-v2 \
  2>&1 | jq -r '
"✓ Need Decision: \(.need_decision.decision)",
"✓ Specialized: \(.need_decision.specialized_need)",
"✓ Selection Method: \(.selection.selection_method)",
"✓ Selected Scenario: \(.selection.selected_scenario // "none")",
"✓ Skill Count: \(.selection.selected_skills | length)",
"✓ Skills: \(.selection.selected_skills | map(.name) | join(", "))"
'

echo
echo "Expected: 3 skills (code-review-risk, code-test-regression, code-refactor)"
echo

# Test 3: Compare Bundle v1 vs v2
echo "Test 3: Bundle v1 (without --use-bundle-v2)"
PYTHONPATH=src python3 -m onecode_skill_sanitizer smart \
  "构建一个产品官网，包含响应式设计、SEO优化和性能检查" \
  --schema-version 3 \
  --registry catalog \
  --bundles bundles/index.json \
  --routing-examples evals/routing-examples.json \
  --format json \
  2>&1 | jq -r '"Bundle v1 skills: \(.selection.selected_skills | length)"'

echo
echo "=== Tests Complete ==="
