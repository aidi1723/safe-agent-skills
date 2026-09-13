#!/bin/bash
# Deploy Phase 4 to n100 for testing

set -e

echo "=== Phase 4 Deployment to n100 ==="
echo ""

# 1. Archive Phase 4 changes
echo "Step 1: Creating deployment archive..."
tar -czf phase4-deployment.tar.gz \
  bundles/index-v2-tier1.json \
  src/onecode_skill_sanitizer/bundle_selection.py \
  src/onecode_skill_sanitizer/scenario_matcher_v2.py \
  src/onecode_skill_sanitizer/task_pack_v3.py \
  src/onecode_skill_sanitizer/commands.py \
  validate_phase4.sh \
  test_phase4_simple.py \
  PHASE4_SUMMARY.md

echo "✓ Archive created: phase4-deployment.tar.gz"
echo ""

# 2. Display deployment instructions
echo "Step 2: Deploy to n100"
echo "------------------------"
echo "Run the following commands:"
echo ""
echo "# Copy archive to n100"
echo "scp phase4-deployment.tar.gz n100:~/phase4-test/"
echo ""
echo "# SSH to n100"
echo "ssh n100"
echo ""
echo "# Extract and run tests"
echo "cd ~/phase4-test"
echo "tar -xzf phase4-deployment.tar.gz"
echo "bash validate_phase4.sh"
echo ""
echo "=== Deployment archive ready ==="
