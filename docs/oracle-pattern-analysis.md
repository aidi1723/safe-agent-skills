# Oracle Pattern Analysis - Phase 2 Post-Mortem

**Date**: 2026-09-13  
**Purpose**: Understand expert skill selection patterns to guide Bundle v2 redesign

## Executive Summary

Analysis of 50 evaluation tasks reveals that **Oracle selections are consistently precise** (averaging 3 skills per task), while **Bundle definitions are systematically over-broad** (averaging 6-14 skills per bundle). This structural mismatch explains Phase 2's catastrophic F1 failure (6.3%-8.2%).

**Key Finding**: Oracle uses a **3-tier selection model**:
- **Core skills** (required for all tasks in scenario): 0-3 skills
- **Conditional skills** (required for specific task variants): 0-5 skills  
- **Optional skills** (never selected in practice): 40-70% of bundle

**Root Cause**: Current bundles are "kitchen sink" collections lacking selection logic.

---

## Analysis by Scenario

### High-Precision Scenarios (利用率 ≥50%)

#### 1. commerce-listing-growth
- **Bundle**: 5 skills
- **Oracle uses**: 3 skills (60% utilization)
- **Pattern**: Single-task scenario, all core skills
  - Core: `commerce-product-content-review`, `content-seo-review`, `design-ui-review`
  - Unused: generic skills (`business-requirements-brief`, `content-editorial-review`)

**Redesign**: Keep as-is, mark 3 core skills.

---

#### 2. open-source-release  
- **Bundle**: 6 skills
- **Oracle uses**: 3 skills (50% utilization)
- **Pattern**: Single-task scenario, focused on compliance
  - Core: `compliance-license-check`, `content-freshness-expiry-review`, `execution-publish-check`
  - Unused: tangential concerns (`compliance-terms-review`, `content-social-post`)

**Redesign**: Keep 3 core skills, drop social/editorial skills.

---

#### 3. data-analysis-report
- **Bundle**: 6 skills
- **Oracle uses**: 3 skills (50% utilization)
- **Pattern**: Single-task scenario, data verification focus
  - Core: `data-table-analysis`, `data-table-calculation-verify`, `content-claims-compliance-filter`
  - Unused: tools Oracle didn't need (`office-spreadsheet-cleanup`, `data-visualization-plan`)

**Redesign**: Keep 3 core analysis/verification skills.

---

#### 4. security-agent-guardrails
- **Bundle**: 6 skills
- **Oracle uses**: 3 skills (50% utilization)
- **Pattern**: Single-task scenario, permission/safety focus
  - Core: `ai-tool-schema-protocol-check`, `security-permission-boundary-check`, `compliance-public-claim-risk-register`
  - Unused: implementation tools (`ai-outlines-structured-generation`, `security-llm-guard-io-scanning`)

**Redesign**: Keep 3 architectural review skills, move implementation tools to conditional.

---

### Medium-Precision Scenarios (利用率 30-50%)

#### 5. code-review-hardening
- **Bundle**: 7 skills
- **Oracle uses**: 3 skills (43% utilization)
- **Pattern**: Single-task scenario, security audit focus
  - Core: `code-review-risk`, `security-auth-review`, `security-supply-chain-review`
  - Unused: testing/tooling (`code-test-regression`, `ai-pydantic-schema-contract`)

**Redesign**: Keep 3 security review skills as core.

---

#### 6. codebase-change-lifecycle
- **Bundle**: 10 skills
- **Oracle uses**: 4 skills across 2 tasks (40% utilization)
- **Pattern**: Multi-task scenario with conditional branching
  - Core (both tasks): `code-review-risk`, `code-test-regression`
  - Conditional:
    - `code-refactor` → task-017 (refactor module)
    - `execution-browser-check` → task-050 (integration tests)
  - Unused: 8 generic development skills

**Redesign**:
```
core: [code-review-risk, code-test-regression]
conditional:
  - trigger: "refactor|重构" → code-refactor
  - trigger: "browser|integration" → execution-browser-check
```

---

#### 7. rag-agent-knowledge-app
- **Bundle**: 9 skills
- **Oracle uses**: 3 skills (33% utilization)
- **Pattern**: Single-task scenario, LlamaIndex-focused
  - Core: `ai-llamaindex-rag-knowledge-workflow`, `research-source-check`, `research-citation-evidence-map`
  - Unused: alternative frameworks (`data-haystack-rag-pipeline`, `ai-langchain-agent-orchestration`)

**Redesign**: Keep LlamaIndex + citation as core, drop alternative frameworks.

---

#### 8. document-to-knowledge-base
- **Bundle**: 9 skills
- **Oracle uses**: 3 skills (33% utilization)
- **Pattern**: Single-task scenario, conversion pipeline focus
  - Core: `ai-llamaindex-rag-knowledge-workflow`, `research-source-lineage-trace`, `content-freshness-expiry-review`
  - Unused: file format tools (`data-marker-pdf-markdown-review`, `data-unstructured-document-partition`)

**Redesign**: Keep pipeline + lineage as core, make file tools conditional on "PDF|DOCX".

---

### Low-Precision Scenarios (利用率 <30%)

#### 9. skill-router-quality-review
- **Bundle**: 10 skills
- **Oracle uses**: 3 skills (30% utilization)
- **Pattern**: Single-task scenario, evaluation focus
  - Core: `ai-routing-accuracy-review`, `ai-dag-execution-graph-check`, `code-test-regression`
  - Unused: 9 implementation/tooling skills

**Redesign**: Keep 3 evaluation skills, drop all tooling references.

---

#### 10. website-build-launch  
- **Bundle**: 14 skills
- **Oracle uses**: 8 skills across 3 tasks (57% utilization BUT 0% core)
- **Pattern**: Multi-task scenario with NO shared core
  - Task variants:
    - task-001 (官网): `design-responsive-viewport-check`, `content-seo-review`, `execution-browser-check`
    - task-011 (落地页): `design-premium-landing-page`, `design-motion-interaction-polish`, `execution-browser-check`
    - task-020 (混合): `design-ui-review`, `skill-router-quality-review`, `open-source-release`
  - Unused: 10 generic skills

**Critical Issue**: This "scenario" actually represents 3 distinct task types mis-grouped under one label.

**Redesign Options**:
1. Split into 3 scenarios:
   - `website-responsive-seo` (task-001 pattern)
   - `landing-page-conversion` (task-011 pattern)  
   - `website-hybrid-workflows` (task-020 pattern)
2. Keep unified but with complex conditional logic

**Recommendation**: **Split the bundle** — these are genuinely different tasks.

---

## Cross-Scenario Patterns

### Oracle Selection Statistics
| Metric | Value |
|--------|-------|
| Average skills per task | 3.0 |
| Min skills per task | 3 |
| Max skills per task | 3 |
| Standard deviation | 0.0 |

**Observation**: Oracle is **remarkably consistent** — every single task gets exactly 3 skills.

### Bundle Utilization Statistics
| Metric | Value |
|--------|-------|
| Average bundle size | 7.9 skills |
| Average Oracle selection | 3.5 skills |
| Average utilization | 44% |
| Utilization range | 30%-60% |

**Observation**: Bundles contain **2-3x more skills than needed**.

### Skill Frequency Analysis

**Most common in Oracle selections**:
1. `execution-browser-check` (3 tasks, 2 scenarios)
2. `code-review-risk` (3 tasks, 2 scenarios)
3. `code-test-regression` (3 tasks, 2 scenarios)
4. `ai-llamaindex-rag-knowledge-workflow` (2 tasks, 2 scenarios)

**Most common in Bundles but unused**:
1. `business-requirements-brief` (4 bundles, 0 Oracle uses)
2. `security-supply-chain-review` (4 bundles, 1 Oracle use)
3. `content-editorial-review` (3 bundles, 0 Oracle uses)
4. `research-source-check` (4 bundles, 1 Oracle use)

**Pattern**: Generic "might be useful" skills appear in many bundles but Oracle rarely selects them.

---

## Implications for Bundle v2

### Design Principles

1. **Precision over Recall**: Bundle should contain only skills likely to be used (≥50% probability)

2. **3-Tier Structure**:
   ```json
   {
     "core_skills": ["skill-a", "skill-b"],
     "conditional_skills": [
       {"trigger": "keyword pattern", "skills": ["skill-c"]},
       {"trigger": "keyword pattern", "skills": ["skill-d", "skill-e"]}
     ],
     "optional_skills": []  // Deprecated in v2
   }
   ```

3. **Scenario Splitting**: Multi-variant scenarios (like `website-build-launch`) should be split when:
   - No shared core skills across tasks
   - Task descriptions use distinct vocabulary
   - Skill selections have <30% overlap

4. **Conservative Baseline**: Start with Core-only selections, add Conditional incrementally

---

## Redesign Priority Queue

### Tier 1: High-Impact (do first)
1. **website-build-launch** → Split into 3 scenarios
2. **skill-router-quality-review** → Remove 7 unused skills (70% bloat)
3. **codebase-change-lifecycle** → Add conditional logic for refactor vs test

### Tier 2: Medium-Impact
4. **rag-agent-knowledge-app** → Remove alternative framework skills
5. **document-to-knowledge-base** → Make file tools conditional
6. **code-review-hardening** → Remove testing tools

### Tier 3: Polish
7. All other scenarios → Trim generic "business-requirements-brief" skills

---

## Validation Plan

### Phase 4 Acceptance Criteria
- **Target**: Skill F1 ≥60% (up from 8.2%)
- **Method**: Implement Tier 1 redesigns only, re-eval on same 50 tasks
- **Decision Point**:
  - F1 ≥60% → proceed to Tier 2
  - F1 <60% → abandon Bundle approach, expand Cohort instead

### Expected Outcomes

**Conservative Estimate** (Core-only):
- Scenario Match Rate: 76% (unchanged)
- Precision: ~90% (3 skills selected, 2.7 correct)
- Recall: ~50% (Oracle wants 3, bundle provides 1.5)
- **F1: ~64%**

**Optimistic Estimate** (Core + Conditional):
- Scenario Match Rate: 80% (better task_signals)
- Precision: ~85% (3.5 skills selected, 3 correct)
- Recall: ~75% (Oracle wants 3, bundle provides 2.25)
- **F1: ~80%**

---

## Appendix: Raw Data

### Full Scenario Breakdown
(See analysis script output above for complete skill-level detail)

### Unused Skills Summary
Skills appearing in ≥3 bundles but used ≤1 times by Oracle:
- `business-requirements-brief`: 4 bundles, 0 uses
- `security-supply-chain-review`: 4 bundles, 1 use
- `content-editorial-review`: 3 bundles, 0 uses
- `research-source-check`: 4 bundles, 1 use
- `engineering-ci-troubleshoot`: 3 bundles, 0 uses

**Action**: Remove these from all bundles except scenarios where Oracle actually used them.

---

**Next Steps**: Proceed to Phase 4 implementation with Tier 1 redesigns.
