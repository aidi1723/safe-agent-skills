# Router v3 深度分析总结

**日期**: 2026-09-12  
**状态**: 快速修复部分成功，需要进入 Phase 2

---

## 核心发现

### 1. Need Gate 修复成功 ✅

**改进**:
- 启发式规则正确识别 100% 任务需要技能
- Scenario Match Rate: 20% → **74%** (提升 270%)
- 不再出现 `no_specialized_need` 误判

**证据**:
```json
"need_decision": {
  "decision": "single",
  "specialized_need": true,
  "reason_codes": ["heuristic_task_type_domain_match"]
}
```

### 2. 阈值悖论导致零选择 🔴

**问题**: 虽然阈值从 0.35 降到 0.10，但所有候选技能得分仍在 0.008-0.02 之间

**示例** (task-001):
```
Top candidate: design-ui-review
Score: 0.017143
Threshold: 0.10
Result: rejected (0.017 < 0.10)
```

**原因**: 确定性评分基于 token overlap，普遍很低：
- Token overlap: 2
- Token union: 35  
- Score: (2/35) * 0.3 = 0.017

**结果**: **Skill F1 仍然是 0%**

### 3. 缺少 Scenario Bundle 路由

**影响的 13 个任务**:
- 构建产品官网 (需要 design-responsive + content-seo + execution-browser)
- API安全审查 (需要 code-review + security-auth + security-supply-chain)
- 数据分析报告 (需要 data-table-analysis + data-calculation + content-claims)
- RAG问答系统 (需要 ai-llamaindex-rag + research-source + research-citation)

这些都是 **复杂场景**，需要多个技能协作，但 v3 只能返回单个技能或空结果。

---

## 数据分析

### 按复杂度

| 复杂度 | 任务数 | Scenario Match | 结论 |
|--------|--------|----------------|------|
| low | 2 | 100% | ✅ 简单任务完美 |
| medium | 23 | 87% | 🟡 大部分成功 |
| high | 24 | 62% | 🔴 复杂任务失败多 |
| very-high | 1 | 0% | 🔴 超高复杂度完全失败 |

### 按类别（0% 匹配的）

- `website-build` (2) - 缺 design-responsive, content-seo
- `code-review` (1) - 缺 security-auth-review  
- `data-analysis` (1) - 缺 data-table-analysis
- `rag-agent` (1) - 缺 ai-llamaindex-rag
- `commerce` (1) - 缺 commerce-listing
- `document` (1) - 缺 document-to-knowledge-base
- `code-refactor` (1) - 缺 codebase-change

**模式**: 失败的都是 **cohort 中没有对应技能** 的类别

---

## 三个根本问题

### 问题 1: 评分系统过于严格

**当前评分**:
- 基于 token overlap 的确定性评分
- 典型得分: 0.008-0.02
- 无语义相似度

**后果**:
- 即使降低阈值到 0.10，仍然选不中任何技能
- 需要降到 0.01 或更低才有效果

### 问题 2: Cohort 覆盖率只有 20%

**统计**:
- Cohort 技能: 7 个
- 50 任务预期需要: 约 30-40 个不同技能
- 覆盖率: ~20%

**缺失的高频技能**:
1. design-responsive-viewport-check
2. content-seo-review
3. data-table-analysis
4. security-auth-review
5. ai-llamaindex-rag-knowledge-workflow

### 问题 3: 无法处理多技能协作

**场景**:
- 13/50 任务需要 2-4 个技能协作
- v3 只能返回单个技能或空结果
- 无法像 v2 那样组合 scenario bundle

---

## 三条修复路径

### 路径 A: 继续调整阈值（快但治标不治本）⚡

**操作**:
```python
SELECTION_THRESHOLD = 0.01  # 从 0.10 再降到 0.01
```

**预期**:
- Skill F1: 0% → 20-30%
- Scenario Match: 74% → 80%

**优点**: 5 分钟修复  
**缺点**: 误选率高，解决不了根本问题

**建议**: ⚠️ 不推荐，只是拖延时间

### 路径 B: 扩展 Cohort（中期方案）⭐

**操作**: 从 7 个扩展到 15 个技能

**新增 8 个**:
- design-responsive-viewport-check
- content-seo-review
- data-table-analysis
- security-auth-review
- ai-llamaindex-rag-knowledge-workflow
- code-refactor-risk
- document-extract-structure
- commerce-listing-optimize

**预期**:
- 覆盖率: 20% → 50%
- Scenario Match: 74% → 85%
- Skill F1: 0% → 40-50%

**时间**: 1 周

**建议**: 🟡 可以并行进行，但不是优先级

### 路径 C: 集成 Scenario Bundle 路由（推荐）⭐⭐⭐

**目标**: 让 v3 支持返回完整的 scenario bundle

**实现要点**:
```python
def build_v3_task_pack(task, registry, bundles):
    # 1. Need gate 判断
    need = decide_need(task)
    
    if need["decision"] == "composite":
        # 2. 尝试匹配 scenario bundle
        scenario = match_scenario_bundle(task, bundles)
        if scenario:
            return build_scenario_pack(scenario, registry)
    
    # 3. 回退到单技能选择
    if need["specialized_need"]:
        return select_from_cohort(task, cohort)
    
    return empty_pack()
```

**预期效果**:
- Scenario Match: 74% → **90%+** ✅ 达标
- Skill F1: 0% → **60-70%**
- 解决 13 个复杂任务的多技能需求

**时间**: 1-2 周

**建议**: ✅ **强烈推荐，这是最快达标的路径**

---

## 推荐行动计划

### 第 1 周: Scenario Bundle 集成 (路径 C)

**任务**:
1. 实现 scenario bundle 匹配逻辑
2. 在 v3 task pack 中集成 scenario 路由
3. 优先级: composite task → scenario match → cohort fallback
4. 测试 50 任务

**预期达标**: Scenario Match ≥ 90%

### 第 2 周: Cohort 扩展 + 阈值优化

**任务**:
1. 扩展 cohort 到 15 技能 (路径 B)
2. 调整阈值到 0.01
3. 运行回归测试
4. 验证 Skill F1

**预期达标**: Skill F1 ≥ 70%

### 第 3-4 周: 最终优化

**任务**:
1. 扩展 cohort 到 30 技能（如果需要）
2. 添加语义评分（如果 F1 仍不足）
3. 完整回归测试
4. Final test 验收

**预期达标**: 所有验收标准 ≥ 85%

---

## 决策建议

### 问题: 是否继续快速修复？

**答案**: ❌ 不建议

**理由**:
- 再次降低阈值只是临时缓解，不解决根本问题
- Scenario Match 已经 74%，证明 need gate 成功
- 剩下的 26% 和 0% F1 都需要 scenario bundle
- 继续调阈值只会浪费时间

### 问题: 应该优先做什么？

**答案**: ✅ 路径 C - Scenario Bundle 集成

**理由**:
1. **影响最大**: 直接解决 13 个复杂任务
2. **达标最快**: 1-2 周内可达 90% scenario match
3. **利用现有资源**: 23 个 scenario bundles 已经存在
4. **架构正确**: 符合 v3 的设计理念

### 问题: Router v3 还能成为默认吗？

**答案**: ✅ 可以，但需要 2-3 周

**前提条件**:
1. ✅ Week 1: 完成 Scenario Bundle 集成
2. ✅ Week 2: 扩展 Cohort + 阈值优化
3. ✅ Week 3: 通过完整验收测试
4. ✅ Week 4: Final test 授权通过

---

## 总结

### 快速修复的价值 ✅

虽然 Skill F1 仍是 0%，但快速修复验证了：
1. **Need Gate 逻辑正确**: 启发式规则成功识别任务需求
2. **架构可行**: v3 的设计方向是对的
3. **问题明确**: 瓶颈在 scenario 路由和 cohort 覆盖

### 下一步清晰 📍

**不要**: 继续微调阈值  
**要做**: 集成 Scenario Bundle 路由

**目标明确**:
- Week 1: Scenario Match ≥ 90%
- Week 2: Skill F1 ≥ 70%  
- Week 3-4: 全面达标

**预计时间**: 2-3 周后，Router v3 可以成为生产默认路由器。
