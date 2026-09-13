# Phase 4 Tier 1 Testing Guide

## Status: Implementation Complete ✓

All code has been implemented and is ready for testing.

## What Was Implemented

### 1. Bundle v2 Structure
- Created `bundles/index-v2-tier1.json` with 4 redesigned scenarios
- Added `core_skills` (always selected) and `conditional_skills` (keyword-triggered)
- Split `website-build-launch` into 3 focused scenarios

### 2. Selection Logic Engine
- Implemented `bundle_selection.py` with keyword matching
- Supports regex triggers for conditional skills
- Validates against catalog to ensure skill existence

### 3. Scenario Matcher v2
- Created `scenario_matcher_v2.py` that applies selection logic
- Returns selected skills (not full bundle) with selection metadata
- Reuses existing scenario scoring from Phase 2

### 4. Integration
- Updated `task_pack_v3.py` to support `--use-bundle-v2` flag
- CLI already supports the flag (line 231 in commands.py)
- Evaluation script supports the flag (line 329 in run_three_arm_eval.py)

---

## Manual Testing Steps

### Quick Smoke Test

Test each scenario type to verify conditional logic works:

```bash
# Test 1: Website with responsive design (website-responsive-seo)
python3 -m onecode_skill_sanitizer smart \
  "构建一个产品官网，包含响应式设计、SEO优化和性能检查" \
  --schema-version 3 \
  --registry catalog \
  --bundles bundles/index-v2-tier1.json \
  --use-bundle-v2 \
  --format json

# Expected: 3 skills (design-responsive-viewport-check, content-seo-brief, execution-browser-check)

# Test 2: Landing page (landing-page-conversion)
python3 -m onecode_skill_sanitizer smart \
  "构建一个落地页，包含动效、表单验证和转化追踪" \
  --schema-version 3 \
  --registry catalog \
  --bundles bundles/index-v2-tier1.json \
  --use-bundle-v2 \
  --format json

# Expected: 3 skills (design-premium-landing-page, design-motion-interaction-polish, execution-browser-check)

# Test 3: Refactor (should trigger conditional)
python3 -m onecode_skill_sanitizer smart \
  "重构这个模块，提升可读性和可维护性，保持功能不变" \
  --schema-version 3 \
  --registry catalog \
  --bundles bundles/index-v2-tier1.json \
  --use-bundle-v2 \
  --format json

# Expected: 3 skills (code-review-risk, code-test-regression, code-refactor)

# Test 4: Write tests (should NOT trigger refactor conditional)
python3 -m onecode_skill_sanitizer smart \
  "为这个模块编写测试用例，覆盖核心功能和边界情况" \
  --schema-version 3 \
  --registry catalog \
  --bundles bundles/index-v2-tier1.json \
  --use-bundle-v2 \
  --format json

# Expected: 2 skills (code-review-risk, code-test-regression) - NO code-refactor

# Test 5: Browser integration test (should trigger browser conditional)
python3 -m onecode_skill_sanitizer smart \
  "编写集成测试，覆盖端到端工作流，使用真实浏览器验证" \
  --schema-version 3 \
  --registry catalog \
  --bundles bundles/index-v2-tier1.json \
  --use-bundle-v2 \
  --format json

# Expected: 3 skills (code-review-risk, code-test-regression, execution-browser-check)
```

### Full Evaluation (Tier 1 Only)

Run on the 4 tasks covered by Tier 1 scenarios:

```bash
python3 scripts/run_three_arm_eval.py \
  --tasks evals/three-arm-tasks/task-list.json \
  --arms v3,oracle \
  --bundles bundles/index-v2-tier1.json \
  --use-bundle-v2 \
  --output evals/three-arm-results/eval-phase4-tier1.json \
  --limit 50
```

**Expected Results**:
- Tasks matching Tier 1 scenarios should show high F1 (60-80%+)
- Tasks not in Tier 1 will fall back to Phase 3.1 intersection filtering

### Compare Phase 3.1 vs Phase 4

```bash
# Phase 3.1 baseline (intersection filtering)
python3 scripts/run_three_arm_eval.py \
  --tasks evals/three-arm-tasks/task-list.json \
  --arms v3,oracle \
  --bundles bundles/index.json \
  --output evals/three-arm-results/eval-phase3-1-rerun.json \
  --limit 50

# Phase 4 Tier 1 (Bundle v2)
python3 scripts/run_three_arm_eval.py \
  --tasks evals/three-arm-tasks/task-list.json \
  --arms v3,oracle \
  --bundles bundles/index-v2-tier1.json \
  --use-bundle-v2 \
  --output evals/three-arm-results/eval-phase4-tier1.json \
  --limit 50
```

Then compare F1 scores for tasks covered by Tier 1.

---

## Verification Checklist

After running tests, verify:

1. **Conditional logic works**
   - [ ] Refactor task triggers `code-refactor` skill
   - [ ] Test task does NOT trigger `code-refactor` skill
   - [ ] Browser test triggers `execution-browser-check` skill

2. **Skill counts are precise**
   - [ ] Website tasks: 3 skills (not 14 like old bundle)
   - [ ] Landing page: 3 skills
   - [ ] Router review: 3 skills (not 10)
   - [ ] Code change tasks: 2-3 skills (conditional)

3. **F1 improvement**
   - [ ] Tasks in Tier 1: F1 ≥ 60% (huge improvement from 8%)
   - [ ] Other tasks: F1 ≈ 8% (unchanged, using Phase 3.1 fallback)

---

## Known Issues

### Issue 1: skill-router-quality-review uses wrong skills

**Problem**: Bundle defines `ai-output-schema-eval` and `ai-tool-schema-protocol-check`, but Oracle uses `ai-routing-accuracy-review` and `ai-dag-execution-graph-check`.

**Impact**: task-018 will have F1=0% even with Bundle v2.

**Fix**: Update `bundles/index-v2-tier1.json` line 67-78 to match Oracle selection.

---

## Next Steps After Testing

1. **If Tier 1 tests pass** (F1 ≥ 60% for covered tasks):
   - Fix skill-router-quality-review skill mismatch
   - Proceed to Tier 2 (6 more scenarios)
   - Document Tier 1 results

2. **If tests fail**:
   - Debug conditional trigger logic
   - Check skill name mappings in catalog
   - Review scenario matcher scoring
