# Bundle v2 Testing Instructions

## Quick Test on n100

Run the automated deployment and test script:

```bash
./scripts/deploy_and_test_n100.sh
```

This script will:
1. Copy all necessary files to n100
2. Run a single task test with Bundle v2
3. Parse and display results
4. Run a 5-task evaluation

## Expected Results

**Success criteria for single task** ("构建一个产品官网，包含响应式设计、SEO优化和性能检查"):
- Scenario: `website-responsive-seo`
- Skill count: 3
- Skills: `design-responsive-viewport-check`, `content-seo-brief`, `execution-browser-check`

**Success criteria for 5-task evaluation**:
- Scenario match rate should be similar to Phase 2.3 (~76%)
- Skill F1 should improve from 6.3% to 40-60%
- Skill precision should improve from 5.6% to 60-80%

## Manual Test (if script fails)

```bash
# 1. Copy files
rsync -avz --exclude='__pycache__' --exclude='*.pyc' \
  src/onecode_skill_sanitizer \
  bundles \
  catalog \
  evals/routing-examples.json \
  evals/three-arm-tasks \
  scripts/run_three_arm_eval.py \
  n100:~/router-v3-test/

# 2. Test single task on n100
ssh n100 'cd ~/router-v3-test && PYTHONPATH=. python3 -m onecode_skill_sanitizer smart "构建一个产品官网，包含响应式设计、SEO优化和性能检查" --schema-version 3 --registry catalog --bundles bundles/index-v2-tier1.json --routing-examples evals/routing-examples.json --format json --use-bundle-v2'

# 3. Run full evaluation (50 tasks)
ssh n100 "cd ~/router-v3-test && PYTHONPATH=. python3 run_three_arm_eval.py --tasks evals/three-arm-tasks/task-list.json --arms v3 --registry catalog --bundles bundles/index-v2-tier1.json --output evals/bundle-v2-results/eval-full.json --use-bundle-v2"
```

## Bundle v2 Features

**Four Tier-1 Scenarios** (from Oracle analysis):
1. `website-responsive-seo` - 3 core skills
2. `landing-page-conversion` - 3 core skills  
3. `skill-router-quality-review` - 3 core skills
4. `codebase-change-lifecycle` - 2 core + 2 conditional skills

**Selection Logic**:
- Core skills: Always selected
- Conditional skills: Selected when trigger keywords match task
- Example: `code-refactor` only selected when task mentions "重构|refactor|可读性|maintainability"

## Files Deployed

- `src/onecode_skill_sanitizer/` - Router v3 code with Bundle v2 support
- `bundles/index-v2-tier1.json` - Bundle v2 definitions (4 scenarios)
- `bundles/index.json` - Original 23 scenarios (for comparison)
- `catalog/` - Skill registry
- `evals/routing-examples.json` - Routing examples
- `evals/three-arm-tasks/` - 50 evaluation tasks
- `scripts/run_three_arm_eval.py` - Three-arm evaluation script

## Next Steps After Test

If Bundle v2 achieves F1 ≥40%:
- Expand to all 10 Tier-1 scenarios from Oracle analysis
- Target: F1 ≥60%

If Bundle v2 achieves F1 ≥60%:
- Add Tier-2 scenarios (medium utilization)
- Target: F1 ≥85%, Scenario Match ≥90%
