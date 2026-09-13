#!/bin/bash
# Manual test for Phase 4 Bundle v2

echo "=== Testing Phase 4 Bundle v2 ==="
echo ""

# Test 1: website-responsive-seo scenario
echo "Test 1: Website with responsive design and SEO"
python3 -m onecode_skill_sanitizer smart \
  "构建一个产品官网，包含响应式设计、SEO优化和性能检查" \
  --schema-version 3 \
  --registry catalog \
  --bundles bundles/index-v2-tier1.json \
  --use-bundle-v2 \
  --format json \
  > /tmp/test1.json 2>&1

if [ $? -eq 0 ]; then
  echo "✓ Test 1 passed"
  echo "Selected skills:"
  cat /tmp/test1.json | python3 -c "import json, sys; data=json.load(sys.stdin); print('  - ' + '\n  - '.join([s['name'] for s in data['selection']['selected_skills']]))"
else
  echo "✗ Test 1 failed"
  cat /tmp/test1.json
fi
echo ""

# Test 2: codebase-change-lifecycle with refactor trigger
echo "Test 2: Refactor module (should trigger conditional)"
python3 -m onecode_skill_sanitizer smart \
  "重构这个模块，提升可读性和可维护性，保持功能不变" \
  --schema-version 3 \
  --registry catalog \
  --bundles bundles/index-v2-tier1.json \
  --use-bundle-v2 \
  --format json \
  > /tmp/test2.json 2>&1

if [ $? -eq 0 ]; then
  echo "✓ Test 2 passed"
  echo "Selected skills:"
  cat /tmp/test2.json | python3 -c "import json, sys; data=json.load(sys.stdin); print('  - ' + '\n  - '.join([s['name'] for s in data['selection']['selected_skills']]))"
else
  echo "✗ Test 2 failed"
  cat /tmp/test2.json
fi
echo ""

# Test 3: codebase-change-lifecycle without refactor trigger
echo "Test 3: Write tests (should NOT trigger refactor conditional)"
python3 -m onecode_skill_sanitizer smart \
  "为这个模块编写测试用例，覆盖核心功能和边界情况" \
  --schema-version 3 \
  --registry catalog \
  --bundles bundles/index-v2-tier1.json \
  --use-bundle-v2 \
  --format json \
  > /tmp/test3.json 2>&1

if [ $? -eq 0 ]; then
  echo "✓ Test 3 passed"
  echo "Selected skills:"
  cat /tmp/test3.json | python3 -c "import json, sys; data=json.load(sys.stdin); print('  - ' + '\n  - '.join([s['name'] for s in data['selection']['selected_skills']]))"
else
  echo "✗ Test 3 failed"
  cat /tmp/test3.json
fi
echo ""

echo "=== Tests complete ==="
