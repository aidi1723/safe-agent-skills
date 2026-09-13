# Router v3 Phase 2 结论报告

**日期**: 2026-09-13  
**阶段**: Phase 2 完成  
**状态**: 未达标，需要重新设计 ❌

---

## 执行摘要

Phase 2 目标是将 Scenario Bundle 集成到 Router v3，提升复杂任务的技能选择准确性。经过 4 个子阶段的迭代（Phase 2.0-2.2, 2.3, 3.0, 3.1），最终未能达到目标指标。

**最终结果** (Phase 3.1):
- Scenario Match Rate: 76% (目标 ≥90%) ❌
- Avg Skill F1: 8.2% (目标 ≥85%) ❌
- Route Completion: 0% (目标 ≥95%) ❌

**核心问题**: Scenario Bundle 定义过于宽泛（平均 9-14 技能），而实际任务只需要 2-3 个技能，导致 Precision-Recall 无法平衡。

---

## 尝试路径回顾

### Phase 2.0-2.2: Fallback 策略
**策略**: Cohort 选择失败时回退到 Scenario Bundle

**结果**:
- Scenario Match: 76%
- Skill F1: 9.5%

**问题**: 
- Fallback 条件太严格（只有 Cohort 选 0 技能时才触发）
- Cohort 通常会选 1 个低质量技能，阻止 fallback

---

### Phase 2.3: Scenario-First 策略
**策略**: 对所有 specialized 任务优先尝试场景匹配，直接使用 Bundle 全部技能

**结果**:
- Scenario Match: 76%
- Skill F1: 6.3%
- Precision: 5.6%
- Recall: 12.0%

**问题**:
- 技能膨胀 3-5x（Bundle 有 14 技能，Oracle 只需 3 个）
- Precision 极低，选了大量无关技能

---

### Phase 3.0: Cohort-Constrained 策略
**策略**: 约束 Cohort 评分范围到 Scenario Bundle 技能

**结果**:
- 灾难性失败：48/50 任务选择 0 技能
- Skill F1: 2.0%

**问题**:
- 违反 `retrieve_skill_candidates()` 的类型安全约束
- 函数要求完整的 7-skill cohort profiles，不接受子集
- 抛出 `RoutingExampleError`，导致选择失败

**教训**: Router v3 的 Cohort 机制是封闭的，不支持动态约束

---

### Phase 3.1: Intersection Filtering 策略
**策略**: 选择同时出现在 Cohort Top-7 和 Scenario Bundle 中的技能

**结果**:
- Scenario Match: 76%
- Skill F1: 8.2%
- Precision: 12.7% ✓ 改善
- Recall: 6.7% ✗ 下降

**问题**:
- 交集太小（V3 平均 0.5 技能 vs Oracle 需要 2.5 技能）
- Cohort Top-7 和 Scenario Bundle 重合度低
- Precision 提升但 Recall 严重下降

---

## 根本问题分析

### 问题 1: Scenario Bundle 设计缺陷

**当前设计**:
```json
{
  "id": "website-build-launch",
  "name": "网站构建与发布",
  "skills": [
    "design-responsive-viewport-check",
    "content-seo-review",
    "execution-browser-check",
    "design-ui-accessibility-review",
    "code-review-hardening",
    "research-source-check",
    "data-table-calculation-verify",
    "security-supply-chain-review",
    "code-review-quality",
    "content-claims-compliance-filter",
    "security-auth-review",
    "data-table-analysis",
    "execution-lighthouse-perf",
    "content-text-translation"
  ]
}
```

**问题**:
- **Kitchen Sink 定义**: 包含所有可能相关的技能（14 个）
- **无优先级**: 核心技能和可选技能无区分
- **无条件逻辑**: 缺少"如果 X 则需要 Y"的规则
- **实际使用**: Oracle 只选其中 3 个核心技能

**对比 Oracle 选择**:
```
Task: 构建一个产品官网，包含响应式设计、SEO优化和性能检查
Oracle 选择 (3): 
  - design-responsive-viewport-check
  - content-seo-review
  - execution-browser-check

Scenario Bundle (14): 上述 3 个 + 另外 11 个
```

→ 4.7x 技能膨胀

### 问题 2: Cohort 7-skill 限制

**Cohort 范围**:
- 只包含 7 个高频技能
- 固定不可扩展
- 类型安全机制强制完整性

**矛盾**:
- Scenario Bundle 包含的技能可能不在 Cohort 中
- 交集策略无法选择 Cohort 之外的技能
- 约束策略违反类型安全

### 问题 3: Precision-Recall 权衡困境

| 策略 | Precision | Recall | F1 | 说明 |
|------|-----------|--------|-----|------|
| 全选 Bundle | 5.6% | 12.0% | 6.3% | 选太多无关技能 |
| 交集过滤 | 12.7% | 6.7% | 8.2% | 交集太小 |
| Cohort Only | ~15% | ~8% | ~10% | Baseline |

无论如何调整，都无法突破 10% F1 的瓶颈。

---

## 为什么无法达到 85% F1

### 1. 数据质量问题

**Scenario Bundle 定义不准确**:
- Bundle 是"kitchen sink"集合，不是精确的技能列表
- 缺少针对具体任务变化的适应性
- 没有反映"专家如何选择技能"的模式

### 2. 架构限制

**Cohort 封闭性**:
- 7-skill 固定限制
- 类型安全约束不允许动态调整
- 无法支持场景驱动的候选生成

**评分机制单一**:
- 基于固定规则和示例
- 无法适应场景上下文
- 排名不准确

### 3. 方法论问题

**自下而上 vs 自上而下**:
- 当前方法: 先生成候选，再后处理过滤 (自下而上)
- 需要的方法: 根据场景直接生成精确技能列表 (自上而下)

---

## 学到的教训

### ✓ 有效的发现

1. **Scenario Matcher 可以识别任务类型**
   - 76% 场景匹配率证明场景识别是可行的
   - 问题不在于识别，而在于如何使用场景信息

2. **交集策略方向正确但执行受限**
   - Precision 提升证明过滤是有效的
   - 受限于 Cohort 范围和交集大小

3. **Router v3 架构的边界清晰**
   - Cohort 机制是封闭的，不支持动态约束
   - 必须在 Cohort 框架内工作

### ✗ 无效的尝试

1. **直接使用 Scenario Bundle 技能列表**
   - Bundle 太宽泛，无法直接使用
   - 导致 Precision 极低

2. **约束 Cohort 到场景范围**
   - 违反类型安全，实现不可行
   - 架构不支持

3. **在 Precision 和 Recall 之间寻找平衡点**
   - 在当前 Bundle 定义下，平衡点仍然很低（8% F1）
   - 无法达到 85% 目标

---

## 建议的后续路径

### Option A: 重新设计 Scenario Bundle (推荐)

**目标**: 将 Bundle 从"kitchen sink"改为"智能模板"

**设计方案**:
```json
{
  "id": "website-build-launch",
  "name": "网站构建与发布",
  "core_skills": [
    "design-responsive-viewport-check",
    "content-seo-review",
    "execution-browser-check"
  ],
  "conditional_skills": [
    {
      "skill": "design-ui-accessibility-review",
      "condition": "task mentions 无障碍 or accessibility"
    },
    {
      "skill": "execution-lighthouse-perf",
      "condition": "task mentions 性能 or performance"
    }
  ],
  "optional_skills": [
    "code-review-hardening",
    "security-supply-chain-review"
  ]
}
```

**优点**:
- 核心技能直接使用，匹配 Oracle 模式
- 条件技能根据任务动态添加
- 减少技能膨胀

**工作量**: 中等（需要重新标注 23 个 bundles）

### Option B: 扩展 Cohort 规模

**目标**: 将 Cohort 从 7 个扩展到 15-20 个技能

**方案**:
- 分析所有 Scenario Bundle 中的技能
- 提取出现频率最高的 15-20 个
- 扩展 Cohort 覆盖范围

**优点**:
- 提升交集策略的有效性
- 不需要修改 Bundle 定义

**缺点**:
- 需要修改 Router v3 架构（Cohort 大小限制）
- 评分复杂度增加

**工作量**: 大（需要修改核心架构）

### Option C: 放弃 Scenario Bundle 路径

**目标**: 回归纯 Cohort 策略，专注提升评分质量

**方案**:
- 改进 Cohort 评分算法
- 添加更多 routing examples
- 微调评分权重

**优点**:
- 不依赖 Bundle 质量
- 架构简单

**缺点**:
- 无法利用场景信息
- 可能仍然达不到 85% F1

**工作量**: 小

---

## 推荐行动

**立即行动**: 

1. **暂停 Phase 2 路径**
   - 当前方向已证明无法达标
   - 避免继续迭代浪费时间

2. **分析 Oracle 选择模式**
   - 统计 Oracle 在不同场景下的技能选择规律
   - 理解"专家决策逻辑"
   - 为 Bundle 重新设计提供数据支持

3. **评估 Option A 可行性**
   - 计算重新标注 Bundle 的工作量
   - 设计新的 Bundle 结构原型
   - 在小规模样本上验证

**长期方向**:

如果 Option A 可行：
- 重新设计并标注所有 Scenario Bundles
- 实现 Phase 4: 条件技能选择
- 目标: Skill F1 ≥ 85%

如果 Option A 成本过高：
- 评估 Option B 或 C
- 或接受当前 Cohort-only 的性能水平

---

## 附录: 完整指标对比

| Phase | Strategy | Scenario Match | Precision | Recall | F1 |
|-------|----------|----------------|-----------|--------|-----|
| 2.0-2.2 | Fallback | 76% | 7.8% | 11.5% | 9.5% |
| 2.3 | Scenario-First | 76% | 5.6% | 12.0% | 6.3% |
| 3.0 | Cohort-Constrained | 74% | 4.0% | 1.3% | 2.0% |
| 3.1 | Intersection | 76% | 12.7% | 6.7% | 8.2% |
| **Target** | | **≥90%** | **-** | **-** | **≥85%** |

---

**结论**: Phase 2 未能达成目标。需要重新设计 Scenario Bundle 结构或探索其他路径。
