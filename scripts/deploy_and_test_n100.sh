#!/bin/bash
set -e

echo "=== Router v3 Bundle v2 Deployment to n100 ==="
echo

# 1. Copy files to n100
echo "[1/2] Copying files to n100..."
rsync -avz --exclude='__pycache__' --exclude='*.pyc' \
  src/onecode_skill_sanitizer \
  bundles \
  catalog \
  evals/three-arm-tasks \
  scripts/run_three_arm_eval.py \
  n100:~/router-v3-test/

echo "✓ Files copied"
echo

# 2. Instructions
echo "[2/2] Test commands to run on n100:"
echo
echo "# Single task test:"
echo 'ssh n100 "cd ~/router-v3-test && PYTHONPATH=. python3 -m onecode_skill_sanitizer smart \"构建一个产品官网，包含响应式设计、SEO优化和性能检查\" --schema-version 3 --registry catalog --bundles bundles/index-v2-tier1.json --routing-examples catalog/routing-examples.json --format json --use-bundle-v2"'
echo
echo "# 5-task evaluation:"
echo 'ssh n100 "cd ~/router-v3-test && mkdir -p evals/bundle-v2-results && PYTHONPATH=. python3 run_three_arm_eval.py --tasks three-arm-tasks/task-list.json --arms v3 --registry catalog --bundles bundles/index-v2-tier1.json --limit 5 --output evals/bundle-v2-results/eval-test.json 2>&1"'
echo
echo "=== Deployment Complete ==="
