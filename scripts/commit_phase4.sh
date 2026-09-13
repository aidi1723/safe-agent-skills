#!/bin/bash
# Router v3 Phase 4 提交脚本

set -e

echo "=== Router v3 Phase 4 提交到 GitHub ==="
echo

# 1. 暂存核心文件
echo "[1/4] 暂存 Bundle v2 核心文件..."
git add bundles/index-v2-tier1.json
git add src/onecode_skill_sanitizer/scenario_matcher_v2.py
git add src/onecode_skill_sanitizer/bundle_selection.py
git add src/onecode_skill_sanitizer/scenario_matcher.py
git add src/onecode_skill_sanitizer/need_gate.py

echo "[2/4] 暂存文档和脚本..."
git add bundles/README.md
git add docs/ROUTER_V3_PHASE4_COMPLETION.md
git add BUNDLE_V2_TEST_INSTRUCTIONS.md
git add scripts/deploy_and_test_n100.sh

echo "[3/4] 提交..."
git commit -m "feat(router): implement Router v3 Phase 4 - Bundle v2 with core/conditional selection

Core Changes:
- Add Bundle v2 architecture with scenario_matcher_v2 and bundle_selection modules
- Implement core/conditional skill selection logic
- Create 4 Tier 1 scenarios with precise skill targeting
- Update scenario matching algorithm (task_signals weighted 60%)

Scenarios Added:
- website-responsive-seo: 3 core skills (design, SEO, browser check)
- landing-page-conversion: 3 core skills (landing page, motion, browser check)
- skill-router-quality-review: 3 core skills (routing accuracy, DAG, testing)
- codebase-change-lifecycle: 2 core + 2 conditional skills (code review + refactor/browser)

Impact:
- Reduces over-selection from 6-14 skills to 2-3 skills per task
- Enables scenario-based skill routing with conditional logic
- Maintains backward compatibility with Bundle v1

Testing:
- Local testing verified for website and code review tasks
- n100 deployment script ready (scripts/deploy_and_test_n100.sh)
- Documentation complete (BUNDLE_V2_TEST_INSTRUCTIONS.md)

Files:
- New: bundles/index-v2-tier1.json
- New: src/onecode_skill_sanitizer/scenario_matcher_v2.py
- New: src/onecode_skill_sanitizer/bundle_selection.py
- Modified: src/onecode_skill_sanitizer/scenario_matcher.py (threshold 0.15)
- Modified: src/onecode_skill_sanitizer/need_gate.py (capability patterns)
- New: docs/ROUTER_V3_PHASE4_COMPLETION.md (completion report)
- New: scripts/deploy_and_test_n100.sh (deployment script)
"

echo "[4/4] 推送到 GitHub..."
git push origin feature/router-v3-phase4-bundle-v2

echo
echo "✅ 提交完成！"
echo "分支: feature/router-v3-phase4-bundle-v2"
echo
echo "下一步："
echo "1. 在 GitHub 上创建 Pull Request"
echo "2. 运行 n100 测试验证: bash scripts/deploy_and_test_n100.sh"
