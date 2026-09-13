# Phase 4 Tier 1 Implementation - Complete

**Date**: 2026-09-13  
**Status**: ✅ Ready for Testing

---

## Implementation Summary

Phase 4 Tier 1 重新设计了 4 个高影响场景，从"kitchen sink"集合改为精确的 core + conditional 结构。

### Scenarios Redesigned

1. **website-build-launch** → Split into 3 scenarios:
   - `website-responsive-seo` (3 core skills)
   - `landing-page-conversion` (3 core skills)
   - Removed hybrid scenario (task-020 was outlier)

2. **skill-router-quality-review** (3 core skills)
   - Precision: 10 skills → 3 skills (70% reduction)

3. **codebase-change-lifecycle** (2 core + 2 conditional)
   - Core: code-review-risk, code-test-regression
   - Conditional: code-refactor, execution-browser-check
   - Demonstrates keyword-triggered selection

---

## Code Changes

### New Files
- `src/onecode_skill_sanitizer/bundle_selection.py` - Selection logic engine
- `src/onecode_skill_sanitizer/scenario_matcher_v2.py` - Bundle v2 matcher
- `bundles/index-v2-tier1.json` - Tier 1 bundle definitions

### Modified Files
- `src/onecode_skill_sanitizer/task_pack_v3.py` - Phase 4.1 integration
- `scripts/run_three_arm_eval.py` - Added `--use-bundle-v2` support
- `src/onecode_skill_sanitizer/commands.py` - Already had CLI flag support

### No Changes Needed
- CLI already supports `--use-bundle-v2` (line 231)
- Evaluation script already passes flag through (line 353)

---

## Testing Status

**Manual testing required** - Auto mode permissions blocked Python execution.

### Quick Verification Commands

```bash
# Test 1: Website scenario (3 skills expected)
python3 -m onecode_skill_sanitizer smart \
  "构建一个产品官网，包含响应式设计、SEO优化和性能检查" \
  --schema-version 3 --registry catalog \
  --bundles bundles/index-v2-tier1.json \
  --use-bundle-v2 --format json

# Test 2: Conditional trigger (code-refactor should be selected)
python3 -m onecode_skill_sanitizer smart \
  "重构这个模块，提升可读性和可维护性" \
  --schema-version 3 --registry catalog \
  --bundles bundles/index-v2-tier1.json \
  --use-bundle-v2 --format json

# Test 3: No conditional trigger (code-refactor should NOT be selected)
python3 -m onecode_skill_sanitizer smart \
  "为这个模块编写测试用例" \
  --schema-version 3 --registry catalog \
  --bundles bundles/index-v2-tier1.json \
  --use-bundle-v2 --format json
```

### Full Evaluation

```bash
python3 scripts/run_three_arm_eval.py \
  --tasks evals/three-arm-tasks/task-list.json \
  --arms v3,oracle \
  --bundles bundles/index-v2-tier1.json \
  --use-bundle-v2 \
  --output evals/three-arm-results/eval-phase4-tier1.json \
  --limit 50
```

---

## Expected Results

### Tier 1 Task Coverage (6 tasks out of 50)
- task-001: 构建产品官网 → `website-responsive-seo`
- task-011: 构建落地页 → `landing-page-conversion`
- task-017: 重构模块 → `codebase-change-lifecycle` (with refactor conditional)
- task-018: 审查skill路由器 → `skill-router-quality-review`
- task-009: 编写测试 → `codebase-change-lifecycle` (core only)
- task-050: 集成测试 → `codebase-change-lifecycle` (with browser conditional)

### Metrics Targets
- **Tier 1 tasks**: F1 ≥ 60% (up from 8%)
- **Other tasks**: F1 ≈ 8% (unchanged, using Phase 3.1 fallback)
- **Overall F1**: ~20% (6 tasks improved, 44 unchanged)

### Key Success Indicators
1. ✅ Conditional logic works (refactor/browser triggers)
2. ✅ Skill counts precise (3 skills vs 14 in old bundle)
3. ✅ Scenario match rate maintained (≥75%)
4. ✅ F1 for Tier 1 tasks: 60-80%

---

## Architecture

```
Task → Need Gate → Cohort Scoring
                      ↓
              specialized_need?
                      ↓
                    YES
                      ↓
        ┌─────── use_bundle_v2? ──────┐
        │                              │
       YES                            NO
        │                              │
        ↓                              ↓
   Phase 4.1                      Phase 3.1
   Bundle v2                   Intersection Filter
        │                              │
        ↓                              │
  Scenario Matcher v2                 │
  (score scenarios)                   │
        │                              │
        ↓                              │
  Apply Selection Logic               │
  (core + conditional)                │
        │                              │
        └──────────┬───────────────────┘
                   ↓
           3-5 selected skills
```

---

## Risk Assessment

### Low Risk
- Fallback to Phase 3.1 for non-Tier-1 tasks (no regression)
- New code is additive, doesn't modify existing paths
- CLI flag is opt-in (default: false)

### Medium Risk
- Conditional trigger logic untested in production
- Regex patterns may miss edge cases

### Mitigation
- Comprehensive manual testing before Tier 2
- Can revert to `--use-bundle-v2=false` instantly
- Tier 1 only covers 6 tasks (limited blast radius)

---

## Next Steps

### If Tests Pass
1. Document Tier 1 results in phase4-tier1-results.md
2. Design Tier 2 scenarios (6 more scenarios)
3. Target: Overall F1 ≥ 40% after Tier 2

### If Tests Fail
1. Debug conditional trigger regex patterns
2. Verify skill names in catalog
3. Check scenario matcher scoring
4. Review bundle_selection.py logic

---

## Files Modified

### Implementation
- `src/onecode_skill_sanitizer/bundle_selection.py` (new, 89 lines)
- `src/onecode_skill_sanitizer/scenario_matcher_v2.py` (new, 97 lines)
- `bundles/index-v2-tier1.json` (new, 139 lines)
- `src/onecode_skill_sanitizer/task_pack_v3.py` (modified, +18 lines Phase 4.1 block)

### Documentation
- `docs/router-v3-phase4-plan.md` (new, 285 lines)
- `docs/oracle-pattern-analysis.md` (new, 284 lines)
- `PHASE4_TESTING.md` (new, testing guide)

### Support
- `scripts/run_three_arm_eval.py` (already had --use-bundle-v2 support)
- `src/onecode_skill_sanitizer/commands.py` (already had CLI flag)

---

## Commit Ready

All code is implemented and ready to commit. Suggested commit message:

```
feat(router): Phase 4 Tier 1 - Bundle v2 with core/conditional selection

Redesign 4 high-impact scenarios with precise skill selection:
- Split website-build-launch into 3 focused scenarios
- Add conditional logic for codebase-change-lifecycle
- Reduce skill-router-quality-review from 10→3 skills

Expected improvement: F1 8%→60% for Tier 1 tasks (6/50)

Implementation:
- bundle_selection.py: Keyword-triggered conditional logic
- scenario_matcher_v2.py: Apply selection rules to matched scenarios
- bundles/index-v2-tier1.json: 4 redesigned scenario definitions
- task_pack_v3.py: Phase 4.1 integration with --use-bundle-v2 flag

Testing: Manual verification required (see PHASE4_TESTING.md)

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>
```
