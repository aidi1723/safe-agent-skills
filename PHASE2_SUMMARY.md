# Router v3 Phase 2 最终总结

**状态**: ❌ 未达标  
**日期**: 2026-09-13  
**执行者**: Claude Code

---

## 目标 vs 实际结果

| 指标 | 目标 | 实际 (Phase 3.1) | 状态 |
|------|------|------------------|------|
| Scenario Match Rate | ≥90% | 76% | ❌ |
| Avg Skill F1 | ≥85% | 8.2% | ❌ |
| Route Completion | ≥95% | 0% | ❌ |

---

## 尝试的 4 个策略

1. **Phase 2.0-2.2: Fallback** → F1 9.5%
   - Cohort 失败时用 Scenario Bundle
   - 问题: 触发条件太严格

2. **Phase 2.3: Scenario-First** → F1 6.3%
   - 优先场景匹配，全选 Bundle 技能
   - 问题: 技能膨胀 3-5x

3. **Phase 3.0: Cohort-Constrained** → F1 2.0% (灾难)
   - 约束 Cohort 到场景技能
   - 问题: 违反类型安全，实现失败

4. **Phase 3.1: Intersection** → F1 8.2% (最优)
   - Cohort Top-7 ∩ Scenario Bundle
   - 问题: 交集太小

---

## 根本原因

**Scenario Bundle 设计缺陷**:
- 平均包含 9-14 个技能 ("kitchen sink")
- Oracle 实际只需 2-3 个技能
- 技能膨胀 3-5x
- 无优先级、无条件逻辑

**示例**:
```
website-build-launch bundle: 14 技能
Oracle 实际选择: 3 技能
→ 4.7x 膨胀
```

**架构限制**:
- Cohort 固定 7 技能，不可扩展
- 类型安全约束不允许动态调整
- 场景技能可能不在 Cohort 中

---

## 关键发现

✓ **有效的**:
- Scenario Matcher 能识别任务类型 (76% 匹配率)
- 交集过滤能提升 Precision (5.6% → 12.7%)
- Router v3 架构边界清晰

✗ **无效的**:
- 直接使用 Bundle 技能列表 → Precision 极低
- 约束 Cohort 到场景范围 → 违反类型安全
- Precision-Recall 权衡 → 无法突破 10% F1

---

## 推荐下一步

### Option A: 重新设计 Scenario Bundle ⭐ 推荐

将 Bundle 从 "kitchen sink" 改为 "智能模板":

```json
{
  "core_skills": ["skill-1", "skill-2"],
  "conditional_skills": [
    {"skill": "skill-3", "condition": "task mentions X"}
  ],
  "optional_skills": ["skill-4"]
}
```

**优点**: 匹配 Oracle 选择模式，减少膨胀  
**工作量**: 中等 (重新标注 23 个 bundles)

### Option B: 扩展 Cohort 规模

从 7 技能扩展到 15-20 技能

**优点**: 提升交集覆盖  
**工作量**: 大 (修改核心架构)

### Option C: 放弃 Scenario Bundle

回归纯 Cohort，改进评分算法

**优点**: 架构简单  
**工作量**: 小

---

## 行动建议

1. **暂停当前路径** - 已证明无法达标
2. **分析 Oracle 模式** - 理解专家决策逻辑
3. **评估 Option A** - 计算重新设计成本
4. **小规模验证** - 在样本上测试新结构

---

## 文档

- 完整实施记录: `docs/router-v3-phase2-implementation.md`
- 结论报告: `docs/router-v3-phase2-conclusion.md`
- 评估结果: `evals/three-arm-results/eval-phase*.json`

