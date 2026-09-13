#!/bin/bash
# Deploy Bundle v2 to n100 and run comprehensive test

set -e

echo "=== Bundle v2 Deployment and Test ==="
echo

# 1. Sync files to n100
echo "[1/3] Syncing files to n100..."
rsync -avz --delete \
  --exclude='__pycache__' \
  --exclude='*.pyc' \
  --exclude='.git' \
  --exclude='node_modules' \
  src/onecode_skill_sanitizer \
  bundles \
  catalog \
  evals/three-arm-tasks \
  scripts/run_three_arm_eval.py \
  n100:~/router-v3-test/

echo "✓ Files synced"
echo

# 2. Run single task test
echo "[2/3] Testing single task (website-build-launch)..."
ssh n100 'cd ~/router-v3-test && PYTHONPATH=. python3 -m onecode_skill_sanitizer smart "构建一个产品官网，包含响应式设计、SEO优化和性能检查" --schema-version 3 --registry catalog --bundles bundles/index-v2-tier1.json --format json --use-bundle-v2' > /tmp/bundle-v2-single.json

python3 << 'PYEOF'
import json

with open('/tmp/bundle-v2-single.json') as f:
    result = json.load(f)

selection = result.get('selection', {})
scenario = selection.get('selected_scenario')
skills = selection.get('selected_skills', [])

print(f"\n场景: {scenario}")
print(f"技能数: {len(skills)}")
print(f"技能: {', '.join(s['name'] for s in skills)}")

if scenario == 'website-responsive-seo' and len(skills) == 3:
    print("\n✓ SUCCESS: Bundle v2 正确返回 3 个核心技能")
    exit(0)
elif scenario and len(skills) >= 10:
    print("\n✗ FAIL: 仍返回过多技能（可能未启用 Bundle v2）")
    exit(1)
else:
    print(f"\n? UNEXPECTED: 场景={scenario}, 技能数={len(skills)}")
    exit(1)
PYEOF

echo
echo "[3/3] Running full evaluation (first 10 tasks)..."
ssh n100 "cd ~/router-v3-test && mkdir -p evals/bundle-v2-results && PYTHONPATH=. python3 scripts/run_three_arm_eval.py --tasks three-arm-tasks/task-list.json --arms v3 --registry catalog --bundles bundles/index-v2-tier1.json --limit 10 --output evals/bundle-v2-results/phase4-tier1-test.json 2>&1" | tail -40

echo
echo "=== Test Complete ==="
echo "Results:"
echo "  Single task: /tmp/bundle-v2-single.json"
echo "  Full eval: check n100:~/router-v3-test/evals/bundle-v2-results/phase4-tier1-test.json"
