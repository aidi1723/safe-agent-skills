#!/bin/bash
# Bundle v2 Simple Test Script
# Run this manually: bash scripts/test_bundle_v2_simple.sh

set -e

echo "=== Bundle v2 Test ==="
echo

# Test 1: Single task
echo "[1/2] Testing single task..."
PYTHONPATH=src python3 -c "
from pathlib import Path
from onecode_skill_sanitizer.task_pack_v3 import build_task_pack_v3

import os
os.chdir('/Users/aidi/大字典/safe-agent-skills')

result = build_task_pack_v3(
    task='构建一个产品官网，包含响应式设计、SEO优化和性能检查',
    registry_dir=Path('catalog'),
    bundles_path=Path('bundles/index-v2-tier1.json'),
    routing_examples_path=Path('catalog/routing-examples.json'),
    use_bundle_v2=True
)

scenario = result.get('selection', {}).get('selected_scenario')
skills = [s['name'] for s in result.get('selection', {}).get('selected_skills', [])]
print(f'Scenario: {scenario}')
print(f'Skills ({len(skills)}): {skills}')

if scenario == 'website-responsive-seo' and len(skills) == 3:
    print('\n✓ SUCCESS: Bundle v2 工作正常')
    exit(0)
elif len(skills) == 14:
    print('\n✗ FAIL: 仍使用旧 Bundle')
    exit(1)
else:
    print(f'\n? UNEXPECTED: scenario={scenario}, count={len(skills)}')
    exit(2)
"

echo
echo "=== Test Complete ==="
