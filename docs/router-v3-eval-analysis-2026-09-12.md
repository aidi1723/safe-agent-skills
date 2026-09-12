# Router v3 评估结果深度分析

**日期**: 2026-09-12  
**评估文件**: `eval-20260912-222915.json`  
**分析人**: Claude Code

---

## 执行摘要

快速修复**部分成功**：

| 指标 | Before | After | 目标 | 状态 |
|------|--------|-------|------|------|
| Scenario Match Rate | 20% | **74%** | 90% | 🟡 大幅改进但未达标 |
| Avg Skill F1 | 0% | **0%** | 85% | 🔴 无改进 |
| Need Gate 通过率 | 20% | **100%** | >90% | ✅ 已修复 |

**核心发现**: Need Gate 修复成功，但所有选中的技能得分都低于 0.1 阈值，导致零技能被实际选择。

---

## 问题诊断

### 问题 1: Scenario Match 提升但仍不足 🟡

**改进**:
- 20% → 74% (提升 270%)
- 37/50 任务的 need gate 正确识别需要技能
- 启发式规则成功工作

**仍然失败的 13 个任务**:
```
task-001: 构建产品官网 (website-build-launch)
task-002: API安全审查 (code-review-hardening)
task-003: 数据分析报告 (data-analysis-report)
task-004: RAG问答系统 (rag-agent-knowledge-app)
task-010: 开源发布 (open-source-release)
task-011: 落地页构建 (website-build-launch)
task-012: 电商优化 (commerce-listing-growth)
task-014: AI Agent护栏 (security-agent-guardrails)
task-016: 文档转知识库 (document-to-knowledge-base)
task-017: 代码重构 (codebase-change-lifecycle)
```

**失败原因**: 这些都是复杂场景，需要 **scenario bundle**，而 v3 只返回单个技能。

### 问题 2: Skill F1 仍然是 0% 🔴

**根本原因**: 阈值悖论

查看 task-001 的详细输出：
```json
"confidence": {
  "selection_threshold": 0.1,
  "top_score": 0.017143,
  "level": "medium",
  "reason_codes": ["low_score_margin"]
},
"candidates": [
  {
    "skill": "design-ui-review",
    "final_score": 0.017143,
    "selected": false,
    "reason_codes": ["deterministic_candidate", "rejected"]
  },
  {
    "skill": "security-supply-chain-review",
    "final_score": 0.008333,
    "selected": false
  }
]
```

**问题分析**:
1. ✅ Need gate 通过：`"specialized_need": true, "reason_codes": ["heuristic_task_type_domain_match"]`
2. ✅ 找到候选技能：design-ui-review (0.017), security-supply-chain-review (0.008)
3. ❌ 所有得分 < 0.1 阈值：最高分 0.017 << 0.1
4. ❌ 结果：`"selected": false` 所有技能被拒绝

**为什么得分这么低？**

确定性评分公式：
```python
deterministic_score = (matched_tokens / total_unique_tokens) * weight
```

对于 task-001:
- 任务："构建一个产品官网，包含响应式设计、SEO优化和性能检查"
- design-ui-review 匹配示例 "rt-near-04"
- Token overlap: 2, Token union: 35
- Score: (2/35) * 0.3 = 0.017

**得分低的原因**:
1. Token overlap 方法过于严格（只有 2 个 token 匹配）
2. 7 个 cohort 技能的示例与任务描述的 token 重叠度很低
3. 没有语义相似度计算（`"semantic_score": null`）

### 问题 3: 缺失关键技能 ⚠️

预期需要但不在 cohort 中的技能：
- `design-responsive-viewport-check` (网站构建)
- `content-seo-review` (SEO优化)
- `data-table-analysis` (数据分析)
- `ai-llamaindex-rag-knowledge-workflow` (RAG系统)
- `security-auth-review` (API安全)

即使评分正常，这些任务也无法得到正确的技能。

---

## 复杂度分析

| 复杂度 | 任务数 | Scenario Match | 观察 |
|--------|--------|----------------|------|
| low | 2 | 100% | ✅ 简单任务完美 |
| medium | 23 | 87% | 🟡 大部分成功 |
| high | 24 | 62% | 🔴 复杂任务失败多 |
| very-high | 1 | 0% | 🔴 超高复杂度完全失败 |

**结论**: 复杂任务需要 scenario bundle，单技能路由不足。

---

## 按类别失败分析

**0% 匹配的类别** (需要但不在 cohort 的技能):
- `website-build` (2 任务) - 缺 design-responsive, content-seo
- `code-review` - 缺 security-auth-review
- `data-analysis` - 缺 data-table-analysis
- `rag-agent` - 缺 ai-llamaindex-rag
- `commerce` - 缺 commerce-specific 技能
- `document` - 缺 document-to-knowledge-base
- `code-refactor` - 缺 codebase-change 技能

**100% 匹配的类别** (cohort 有相关技能):
- `codebase-explore` - ✅ 有 codebase-explore-map
- `browser-automation` - ✅ 有 execution-browser-check
- `security` - ✅ 有 security-supply-chain-review

---

## 根本问题总结

### 1. 阈值悖论 🔴

**矛盾**:
- 降低阈值到 0.1 是为了接受更多技能
- 但实际得分都在 0.008-0.02 之间
- 仍然低于 0.1 阈值
- 需要降到 0.005 才能选中任何技能

**新阈值计算**:
```
当前最高分: 0.017
要求选中率: 50%
建议阈值: 0.015 或更低
保守建议: 0.01 (接受 1% token overlap)
激进建议: 0.005 (接受任何候选)
```

### 2. Cohort 覆盖不足 🟡

**统计**:
- Cohort 技能: 7
- 50 个任务预期需要的唯一技能: 约 30-40 个
- 覆盖率: ~20%

**缺失的高频技能**:
1. design-responsive-viewport-check
2. content-seo-review  
3. data-table-analysis
4. security-auth-review
5. ai-llamaindex-rag-knowledge-workflow

### 3. 缺少 Scenario Bundle 路由 🔴

**影响**:
- 13/50 任务需要多技能协作
- v3 只返回空结果或单技能
- 无法组合技能形成完整解决方案

---

## 修复方案升级

### 方案 A: 再次降低阈值（最快）⚡

**修改**:
```python
# skill_selection.py
SELECTION_THRESHOLD = 0.01  # 从 0.10 降到 0.01
```

**预期效果**:
- Scenario Match: 74% → 80%
- Skill F1: 0% → 20-30%

**风险**:
- 误选率会上升
- 可能选中不相关的技能
- 治标不治本

**建议**: ⚠️ 可以尝试，但这不是长期方案

### 方案 B: 扩展 Cohort 到 15 技能（中期）⭐

**新增 8 个高频技能**:
```python
EXTENDED_COHORT_PHASE1 = [
    # 原有 7 个
    "codebase-explore-map",
    "code-review-risk",
    "code-test-regression",
    "execution-browser-check",
    "research-source-check",
    "design-ui-review",
    "security-supply-chain-review",
    
    # 新增 8 个
    "design-responsive-viewport-check",  # 网站构建
    "content-seo-review",                 # SEO
    "data-table-analysis",                # 数据分析
    "security-auth-review",               # API安全
    "ai-llamaindex-rag-knowledge-workflow", # RAG
    "code-refactor-risk",                 # 重构
    "document-extract-structure",         # 文档处理
    "commerce-listing-optimize",          # 电商
]
```

**预期效果**:
- 覆盖 26% → 50% 的任务
- Scenario Match: 74% → 85%
- Skill F1: 0% → 40-50%

**时间**: 1 周

### 方案 C: 集成 Scenario Bundle 路由（推荐）⭐⭐⭐

**目标**: 让 v3 支持返回 scenario bundle，不只是单个技能

**实现要点**:
1. 在 need_decision 判断 composite 时，尝试匹配 scenario
2. 如果匹配到 scenario，返回该 scenario 的技能集合
3. 如果未匹配，回退到 cohort 单技能选择

**预期效果**:
- Scenario Match: 74% → 90%+
- Skill F1: 0% → 60-70%
- 解决复杂任务的多技能需求

**时间**: 1-2 周

### 方案 D: 添加语义评分（长期）📈

**问题**: 当前只有确定性评分（token overlap），得分普遍偏低

**方案**: 集成语义相似度
```python
# 使用 embedding 计算任务与技能描述的相似度
semantic_score = cosine_similarity(
    embed(task_description),
    embed(skill_description)
)

# 混合评分
final_score = 0.4 * deterministic_score + 0.6 * semantic_score
```

**预期效果**:
- 提升得分到 0.3-0.6 范围
- 更智能的匹配
- 减少对 token overlap 的依赖

**成本**: 需要 embedding 模型和 API 调用

**时间**: 2-3 周

---

## 推荐行动计划

### 立即行动（今天）

**选项 1: 激进修复** ⚡
- 降低阈值到 0.01
- 重新评估 50 任务
- 预期 F1 提升到 20-30%

**选项 2: 保守策略** 📊
- 承认快速修复的局限
- 跳过阈值调整
- 直接进入方案 C (Scenario Bundle)

### 本周行动

**推荐**: 方案 C - 集成 Scenario Bundle 路由

**理由**:
1. Scenario match 已经 74%，说明 need gate 工作良好
2. 失败的 13 个任务都是需要多技能的复杂场景
3. 现有 23 个 scenario bundles 可直接利用
4. 这是达到 90% 目标的最快路径

### 下周行动

**如果 Scenario Bundle 集成成功**:
- 扩展 Cohort 到 15 技能 (方案 B)
- 并行优化阈值和评分逻辑
- 运行完整回归测试

---

## 结论

### 快速修复成果 ✅

1. **Need Gate 完全修复**: 100% 任务通过判断
2. **Scenario Match 大幅提升**: 20% → 74%
3. **启发式规则有效**: 正确识别任务类型和领域

### 仍然存在的问题 ❌

1. **Skill F1 仍为 0%**: 阈值过高导致零选择
2. **Cohort 覆盖不足**: 只有 7 技能，缺失关键技能
3. **无 Scenario 路由**: 无法处理多技能协作任务

### 下一步优先级

**P0 (本周)**:
- 集成 Scenario Bundle 路由

**P1 (下周)**:
- 扩展 Cohort 到 15 技能
- 调整阈值到 0.01

**P2 (后续)**:
- 添加语义评分
- 优化确定性评分算法

**预计达标时间**: 2-3 周后，Router v3 可以达到 90% scenario match 和 85% skill F1 的验收标准。
