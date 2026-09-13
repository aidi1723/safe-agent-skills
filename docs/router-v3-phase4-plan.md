# Router v3 Phase 4 Implementation Plan

**Date**: 2026-09-13  
**Goal**: Implement Bundle v2 with core/conditional/optional structure  
**Target Metrics**: Skill F1 ≥60%, Scenario Match ≥80%

---

## Phase 4 Strategy

Based on Oracle pattern analysis, implement 3-tier bundle structure:

```json
{
  "id": "scenario-id",
  "name": "Scenario Name",
  "task_signals": ["keyword1", "keyword2"],
  "core_skills": ["skill-a", "skill-b"],
  "conditional_skills": [
    {
      "trigger": "regex pattern",
      "description": "When to activate",
      "skills": ["skill-c"]
    }
  ]
}
```

**Selection Logic**:
1. Match scenario via `task_signals` (existing mechanism)
2. Always include all `core_skills`
3. For each conditional, test `trigger` regex against task description
4. Return: core_skills + matched conditional skills

---

## Implementation Scope

### Tier 1: High-Impact Redesigns (Do First)

#### 1. Split website-build-launch → 3 scenarios

**Current problem**: 14 skills, 0% core utilization, 3 distinct task types

**New scenarios**:

```json
{
  "id": "website-responsive-seo",
  "name": "Website Responsive SEO",
  "task_signals": ["官网", "响应式", "SEO优化", "产品网站"],
  "core_skills": [
    "design-responsive-viewport-check",
    "content-seo-review",
    "execution-browser-check"
  ],
  "conditional_skills": []
}
```

```json
{
  "id": "landing-page-conversion",
  "name": "Landing Page Conversion",
  "task_signals": ["落地页", "landing page", "动效", "转化", "表单验证"],
  "core_skills": [
    "design-premium-landing-page",
    "design-motion-interaction-polish",
    "execution-browser-check"
  ],
  "conditional_skills": []
}
```

```json
{
  "id": "website-hybrid-workflow",
  "name": "Website + Workflow Orchestration",
  "task_signals": ["构建.*审计", "发布.*验证", "官网.*同时"],
  "core_skills": [
    "design-ui-review"
  ],
  "conditional_skills": [
    {
      "trigger": "路由|router|skill.*选择",
      "description": "When task involves router validation",
      "skills": ["skill-router-quality-review"]
    },
    {
      "trigger": "开源|发布|release",
      "description": "When task involves publishing",
      "skills": ["open-source-release"]
    }
  ]
}
```

**Expected impact**: 
- Precision: 85% → 95% (eliminate cross-contamination)
- Recall: 12% → 90% (tight skill match)
- F1: 8% → 92%

---

#### 2. Trim skill-router-quality-review (30% → 100% utilization)

**Current**: 10 skills, Oracle uses 3

**Redesign**:
```json
{
  "id": "skill-router-quality-review",
  "name": "Skill Router Quality Review",
  "task_signals": ["路由器", "skill.*选择", "执行图", "routing"],
  "core_skills": [
    "ai-routing-accuracy-review",
    "ai-dag-execution-graph-check",
    "code-test-regression"
  ],
  "conditional_skills": []
}
```

**Removed**: 7 implementation/tooling skills that Oracle never selected

---

#### 3. Add conditional logic to codebase-change-lifecycle

**Current**: 10 skills flat, Oracle uses 4 across 2 tasks

**Redesign**:
```json
{
  "id": "codebase-change-lifecycle",
  "name": "Codebase Change Lifecycle",
  "task_signals": ["重构", "编写测试", "代码变更", "refactor", "test"],
  "core_skills": [
    "code-review-risk",
    "code-test-regression"
  ],
  "conditional_skills": [
    {
      "trigger": "重构|refactor",
      "description": "When task is about refactoring",
      "skills": ["code-refactor"]
    },
    {
      "trigger": "浏览器|browser|集成测试|integration",
      "description": "When task involves browser/integration testing",
      "skills": ["execution-browser-check"]
    }
  ]
}
```

**Removed**: 6 generic development skills

---

### Tier 2: Medium-Impact Redesigns (After Tier 1 validation)

#### 4. rag-agent-knowledge-app: Remove alternative frameworks
```json
{
  "core_skills": [
    "ai-llamaindex-rag-knowledge-workflow",
    "research-source-check",
    "research-citation-evidence-map"
  ]
}
```
**Remove**: `data-haystack-rag-pipeline`, `ai-langchain-agent-orchestration` (Oracle never chose them)

---

#### 5. document-to-knowledge-base: Conditional file tools
```json
{
  "core_skills": [
    "ai-llamaindex-rag-knowledge-workflow",
    "research-source-lineage-trace",
    "content-freshness-expiry-review"
  ],
  "conditional_skills": [
    {
      "trigger": "PDF|pdf",
      "skills": ["data-marker-pdf-markdown-review"]
    },
    {
      "trigger": "DOCX|Word|文档",
      "skills": ["data-markitdown-file-to-markdown"]
    }
  ]
}
```

---

#### 6. code-review-hardening: Remove testing tools
```json
{
  "core_skills": [
    "code-review-risk",
    "security-auth-review",
    "security-supply-chain-review"
  ]
}
```
**Remove**: `code-test-regression`, `ai-pydantic-schema-contract` (testing not part of security audit)

---

### Tier 3: Polish (After Tier 1+2 meet targets)

Remove generic "business-requirements-brief" from all bundles where Oracle didn't select it:
- commerce-listing-growth
- rag-agent-knowledge-app
- (4 total occurrences, 0 Oracle uses)

---

## Implementation Steps

### Step 1: Schema Update
File: `bundles/index.json`

Add new fields to bundle schema:
```json
{
  "schema_version": 2,
  "bundles": [
    {
      "id": "...",
      "name": "...",
      "task_signals": [...],
      "core_skills": [...],           // NEW
      "conditional_skills": [...],    // NEW
      "skills": [...]                 // DEPRECATED in v2
    }
  ]
}
```

**Backward compatibility**: Keep `skills` field during transition, populate as `core_skills + all conditional skills`

---

### Step 2: Matcher Update
File: `src/onecode_skill_sanitizer/scenario_matcher.py`

Add function:
```python
def apply_bundle_selection_logic(
    bundle: dict[str, Any],
    task: str
) -> list[str]:
    """
    Apply core/conditional selection logic to bundle.
    
    Returns:
        List of skill names to select for this task
    """
    selected = list(bundle.get("core_skills", []))
    
    for conditional in bundle.get("conditional_skills", []):
        trigger = conditional["trigger"]
        if re.search(trigger, task, re.IGNORECASE):
            selected.extend(conditional["skills"])
    
    return selected
```

---

### Step 3: Router Integration
File: `src/onecode_skill_sanitizer/task_pack_v3.py`

Update Phase 2.3 code (lines 111-127):
```python
# Phase 4 (2026-09-13): Bundle v2 with core/conditional logic
selected_scenario = None
if need["specialized_need"]:
    matched = match_scenario_bundle(routing_current, bundles_path, threshold=0.12)
    if matched:
        selected_scenario = matched["id"]
        
        # Apply core/conditional selection logic
        from .scenario_matcher import apply_bundle_selection_logic
        selected_skills = apply_bundle_selection_logic(matched, routing_current)
        
        composed = dict(composed)
        composed["selected_skill_names"] = selected_skills
        composed["selection_method"] = "scenario_bundle_v2"
        composed["scenario_match"] = {
            "id": matched["id"],
            "name": matched["name"],
            "score": matched["match_score"],
            "confidence": matched["match_confidence"],
            "core_skills": matched.get("core_skills", []),
            "triggered_conditionals": [
                c for c in matched.get("conditional_skills", [])
                if re.search(c["trigger"], routing_current, re.IGNORECASE)
            ]
        }
```

---

### Step 4: Update Tier 1 Bundles

Create: `bundles/index-v2-tier1.json`

Contains:
1. Split `website-build-launch` into 3 scenarios
2. Trimmed `skill-router-quality-review` (10→3 skills)
3. Conditional `codebase-change-lifecycle` (10→2+2 skills)
4. All other 20 bundles unchanged (use legacy `skills` field)

**Migration strategy**: Router falls back to `skills` field if `core_skills` is absent

---

### Step 5: Evaluation

Run three-arm eval on Tier 1 changes:
```bash
python scripts/run_three_arm_eval.py \
  --tasks evals/three-arm-tasks/task-list.json \
  --bundles bundles/index-v2-tier1.json \
  --output evals/three-arm-results/eval-phase4-tier1.json \
  --limit 50
```

**Decision criteria**:
- ✓ **F1 ≥60%** → Proceed to Tier 2
- ✗ **F1 <60%** → Investigate, possibly abandon Bundle approach

---

## Risk Mitigation

### Risk 1: Conditional triggers too broad/narrow
**Mitigation**: Log all trigger matches during eval, manually review false positives/negatives

### Risk 2: Core skills still over-inclusive
**Mitigation**: Start ultra-conservative (2 skills), add incrementally based on precision drops

### Risk 3: Scenario splitting breaks existing tasks
**Mitigation**: Keep original `website-build-launch` as fallback with low priority (score penalty)

---

## Success Metrics

### Phase 4 Tier 1 Targets
| Metric | Current | Target | Stretch |
|--------|---------|--------|---------|
| Scenario Match Rate | 76% | 80% | 85% |
| Skill Precision | 13% | 85% | 90% |
| Skill Recall | 7% | 70% | 80% |
| Skill F1 | 8% | 60% | 80% |
| Route Completion | 0% | 95% | 98% |

### Phase 4 Full (Tier 1+2+3) Targets
| Metric | Target |
|--------|--------|
| Scenario Match Rate | 85% |
| Skill F1 | 85% |
| Route Completion | 95% |

---

## Timeline Estimate

- **Tier 1 Implementation**: 4-6 hours
  - Schema design: 1h
  - Matcher logic: 1h  
  - Bundle redesign (3 scenarios): 2h
  - Integration + testing: 1-2h

- **Tier 1 Validation**: 1-2 hours
  - Run eval: 30min
  - Analyze results: 30min
  - Iteration (if needed): 0-1h

- **Tier 2 Implementation**: 2-3 hours (if Tier 1 succeeds)

- **Tier 3 Polish**: 1-2 hours

**Total**: 8-13 hours for complete Phase 4

---

## Next Actions

1. ✅ Complete Oracle pattern analysis
2. ⏭️ Implement Tier 1 bundle redesigns
3. ⏭️ Update scenario matcher with conditional logic
4. ⏭️ Run Phase 4 Tier 1 evaluation
5. ⏭️ Decision: proceed to Tier 2 or pivot

**Ready to proceed with Tier 1 implementation.**
