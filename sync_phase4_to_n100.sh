#!/bin/bash
# 同步 Phase 4 更新文件到 n100 的完整仓库

set -e

echo "==================================================================="
echo "同步 Phase 4 文件到 n100"
echo "==================================================================="
echo ""

TARGET_REPO="n100:~/safe-agent-skills"

echo "1. 同步 Bundle v2 文件..."
scp bundles/index-v2-tier1.json ${TARGET_REPO}/bundles/
echo "   ✓ bundles/index-v2-tier1.json"

echo ""
echo "2. 同步核心实现文件..."
scp src/onecode_skill_sanitizer/bundle_selection.py ${TARGET_REPO}/src/onecode_skill_sanitizer/
echo "   ✓ bundle_selection.py"

scp src/onecode_skill_sanitizer/scenario_matcher_v2.py ${TARGET_REPO}/src/onecode_skill_sanitizer/
echo "   ✓ scenario_matcher_v2.py"

scp src/onecode_skill_sanitizer/task_pack_v3.py ${TARGET_REPO}/src/onecode_skill_sanitizer/
echo "   ✓ task_pack_v3.py"

scp src/onecode_skill_sanitizer/commands.py ${TARGET_REPO}/src/onecode_skill_sanitizer/
echo "   ✓ commands.py"

echo ""
echo "3. 同步测试文件..."
scp validate_phase4.sh ${TARGET_REPO}/
echo "   ✓ validate_phase4.sh"

scp test_phase4_simple.py ${TARGET_REPO}/
echo "   ✓ test_phase4_simple.py"

echo ""
echo "==================================================================="
echo "同步完成! 现在可以在 n100 上运行测试:"
echo "==================================================================="
echo ""
echo "  ssh n100"
echo "  cd ~/safe-agent-skills"
echo "  bash validate_phase4.sh"
echo ""
echo "或运行完整评估:"
echo ""
echo "  python3 scripts/run_three_arm_eval.py \\"
echo "    --tasks evals/three-arm-tasks/task-list.json \\"
echo "    --arms v3,oracle \\"
echo "    --use-bundle-v2 \\"
echo "    --limit 10"
echo ""
