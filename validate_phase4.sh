#!/bin/bash
# Phase 4 Tier 1 Validation Script
# Run this manually to verify Bundle v2 implementation

set -e

# Set PYTHONPATH to find the module
export PYTHONPATH=src

echo "============================================================"
echo "Phase 4 Tier 1 Validation Tests"
echo "============================================================"
echo

# Test 1: Refactor task (should trigger conditional)
echo "Test 1: Refactor task (should trigger code-refactor conditional)"
echo "----------------------------------------------------------------"
python3 -m onecode_skill_sanitizer smart \
  "重构这个模块，提升可读性和可维护性，保持功能不变" \
  --schema-version 3 \
  --registry catalog \
  --bundles bundles/index-v2-tier1.json \
  --use-bundle-v2 \
  --format json > /tmp/test1.json

echo "Selected skills:"
cat /tmp/test1.json | python3 -c "import json,sys; d=json.load(sys.stdin); print('  ' + '\n  '.join([s['name'] for s in d['selection']['selected_skills']]))"

echo
echo "Expected: code-review-risk, code-test-regression, code-refactor"
echo "Checking for code-refactor..."
if grep -q "code-refactor" /tmp/test1.json; then
    echo "✓ PASS: code-refactor conditional triggered"
else
    echo "✗ FAIL: code-refactor NOT found"
fi
echo

# Test 2: Write tests (should NOT trigger refactor conditional)
echo "Test 2: Write tests (should NOT trigger code-refactor)"
echo "----------------------------------------------------------------"
python3 -m onecode_skill_sanitizer smart \
  "为这个模块编写测试用例，覆盖核心功能和边界情况" \
  --schema-version 3 \
  --registry catalog \
  --bundles bundles/index-v2-tier1.json \
  --use-bundle-v2 \
  --format json > /tmp/test2.json

echo "Selected skills:"
cat /tmp/test2.json | python3 -c "import json,sys; d=json.load(sys.stdin); print('  ' + '\n  '.join([s['name'] for s in d['selection']['selected_skills']]))"

echo
echo "Expected: code-review-risk, code-test-regression (NO code-refactor)"
echo "Checking that code-refactor is NOT selected..."
if grep -q "code-refactor" /tmp/test2.json; then
    echo "✗ FAIL: code-refactor incorrectly triggered"
else
    echo "✓ PASS: code-refactor correctly NOT triggered"
fi
echo

# Test 3: Browser integration test (should trigger execution-browser-check)
echo "Test 3: Integration test (should trigger browser conditional)"
echo "----------------------------------------------------------------"
python3 -m onecode_skill_sanitizer smart \
  "编写集成测试，覆盖端到端工作流，使用真实浏览器验证" \
  --schema-version 3 \
  --registry catalog \
  --bundles bundles/index-v2-tier1.json \
  --use-bundle-v2 \
  --format json > /tmp/test3.json

echo "Selected skills:"
cat /tmp/test3.json | python3 -c "import json,sys; d=json.load(sys.stdin); print('  ' + '\n  '.join([s['name'] for s in d['selection']['selected_skills']]))"

echo
echo "Expected: code-review-risk, code-test-regression, execution-browser-check"
echo "Checking for execution-browser-check..."
if grep -q "execution-browser-check" /tmp/test3.json; then
    echo "✓ PASS: execution-browser-check conditional triggered"
else
    echo "✗ FAIL: execution-browser-check NOT found"
fi
echo

# Test 4: Website task (should use 3 skills, not 14)
echo "Test 4: Website task (should select 3 skills precisely)"
echo "----------------------------------------------------------------"
python3 -m onecode_skill_sanitizer smart \
  "构建一个产品官网，包含响应式设计、SEO优化和性能检查" \
  --schema-version 3 \
  --registry catalog \
  --bundles bundles/index-v2-tier1.json \
  --use-bundle-v2 \
  --format json > /tmp/test4.json

echo "Selected scenario:"
cat /tmp/test4.json | python3 -c "import json,sys; d=json.load(sys.stdin); print('  ' + str(d['selection'].get('selected_scenario')))"

echo
echo "Selected skills:"
cat /tmp/test4.json | python3 -c "import json,sys; d=json.load(sys.stdin); print('  ' + '\n  '.join([s['name'] for s in d['selection']['selected_skills']]))"

echo
echo "Expected: 3 skills (not 14 like old bundle)"
SKILL_COUNT=$(cat /tmp/test4.json | python3 -c "import json,sys; d=json.load(sys.stdin); print(len(d['selection']['selected_skills']))")
echo "Actual count: $SKILL_COUNT"
if [ "$SKILL_COUNT" -eq 3 ]; then
    echo "✓ PASS: Correct skill count (3)"
else
    echo "✗ FAIL: Wrong skill count ($SKILL_COUNT, expected 3)"
fi
echo

# Test 5: Landing page (different scenario)
echo "Test 5: Landing page (should select landing-page-conversion)"
echo "----------------------------------------------------------------"
python3 -m onecode_skill_sanitizer smart \
  "构建一个落地页，包含动效、表单验证和转化追踪" \
  --schema-version 3 \
  --registry catalog \
  --bundles bundles/index-v2-tier1.json \
  --use-bundle-v2 \
  --format json > /tmp/test5.json

echo "Selected scenario:"
cat /tmp/test5.json | python3 -c "import json,sys; d=json.load(sys.stdin); print('  ' + str(d['selection'].get('selected_scenario')))"

echo
echo "Selected skills:"
cat /tmp/test5.json | python3 -c "import json,sys; d=json.load(sys.stdin); print('  ' + '\n  '.join([s['name'] for s in d['selection']['selected_skills']]))"

echo
echo "Expected scenario: landing-page-conversion"
if grep -q "landing-page-conversion" /tmp/test5.json; then
    echo "✓ PASS: Correct scenario selected"
else
    echo "✗ FAIL: Wrong scenario"
fi
echo

echo "============================================================"
echo "Quick Tests Complete"
echo "============================================================"
echo
echo "Next: Run full evaluation on 50 tasks"
echo
echo "  python3 scripts/run_three_arm_eval.py \\"
echo "    --tasks evals/three-arm-tasks/task-list.json \\"
echo "    --arms v3,oracle \\"
echo "    --bundles bundles/index-v2-tier1.json \\"
echo "    --use-bundle-v2 \\"
echo "    --output evals/three-arm-results/eval-phase4-tier1.json \\"
echo "    --limit 50"
echo
