# Router v3 诊断报告

**日期**: 2026-09-12  
**诊断人**: Claude Code  
**问题**: Router v3 三臂评估失败

---

## 问题概述

Router v3 在初步三臂评估（5个任务）中表现严重不佳：

| 指标 | 实际值 | 目标值 | 状态 |
|------|--------|--------|------|
| Scenario Match Rate | 20% | ≥90% | ❌ FAIL |
| Avg Skill F1 | 0% | ≥85% | ❌ FAIL |
| Route Completion Rate | 0% | ≥95% | ❌ FAIL |

**核心问题**: 5个任务中有4个被判定为 `no_specialized_need`，路由器拒绝选择任何技能。

---

## 根本原因分析

### 问题 1：Need Gate 过于保守 🔴

**现象**：
```json
"need_decision": {
  "decision": "none",
  "reason_codes": ["no_specialized_need"],
  "specialized_need": false
}
```

**分析**：
- task-001（构建官网）、task-002（API安全审查）、task-003（数据分析）都被判定为"不需要专业技能"
- 只有 task-004（RAG系统设计）被正确识别为需要技能（因为匹配到了 `research.source` capability）

**根本原因**：
Router v3 的 `need_gate.py` 模块判断逻辑过于严格，只有明确匹配到 required_capabilities 时才认为需要专业技能。但大多数任务没有明确声明 capabilities。

### 问题 2：仅支持 7 个技能的 Cohort 限制 🔴

**现状**：
```python
# Router v3 cohort (固定的7个技能)
COHORT_SKILLS = [
    "codebase-explore-map",
    "code-review-risk",
    "code-test-regression",
    "execution-browser-check",
    "research-source-check",
    "design-ui-review",
    "security-supply-chain-review"
]
```

**问题**：
- task-003 需要的 `data-table-analysis` 不在 cohort 中
- 许多预期技能（如 `design-responsive-viewport-check`、`content-seo-review`）不在 cohort 中
- 即使 need gate 通过，也只能从这 7 个技能中选择

### 问题 3：缺少 Scenario Bundle 路由 🔴

**观察**：
```json
"selected_scenario": null
```

所有任务都没有选择 scenario bundle，尽管 oracle 预期了：
- `website-build-launch`
- `code-review-hardening`
- `data-analysis-report`
- `rag-agent-knowledge-app`

**原因**：
Router v3 专注于单个技能选择，没有实现 scenario bundle 路由机制。

### 问题 4：Deterministic Score 阈值过高 🟡

**观察**：
```json
"confidence": {
  "selection_threshold": 0.35,
  "top_score": 0.017143,  // task-001
  "level": "low"
}
```

即使候选技能有一定匹配度（如 design-ui-review 得分 0.017），但远低于阈值 0.35，因此被拒绝。

---

## 影响评估

### 当前状态

| 能力维度 | 实现程度 | 评估 |
|---------|---------|------|
| Need Gate | 50% | 过于保守，误判率高 |
| Cohort 覆盖 | 4% (7/172) | 严重不足 |
| Scenario 路由 | 0% | 未实现 |
| 评分机制 | 30% | 阈值不合理 |

### 为什么 Router v2 更好？

Router v2（默认）虽然是确定性的，但：
- ✅ 支持全部 172 个技能
- ✅ 支持 23 个 scenario bundles
- ✅ 不需要 need gate 判断
- ✅ 多意图分解和组合

Router v3 试图变"智能"，但引入了过多限制，反而降低了实用性。

---

## 修复方案

### 方案 A：修复 Need Gate（推荐）⭐

**目标**: 让 need gate 更宽松，识别更多需要技能的任务

**实现**:
```python
# src/onecode_skill_sanitizer/need_gate.py

def decide_need(normalized_task: str, task_profile: Dict) -> Dict:
    """决定是否需要专业技能"""
    
    # 新增：基于任务类型的启发式规则
    task_type = task_profile.get("task_type", "general")
    
    # 明确需要技能的任务类型
    NEEDS_SKILLS = {
        "website_build", "code_review", "data_analysis", 
        "rag_agent", "security_audit", "design_review",
        "testing", "deployment", "documentation"
    }
    
    if task_type in NEEDS_SKILLS:
        return {
            "decision": "composite",  # 可能需要多个技能
            "specialized_need": True,
            "reason_codes": ["task_type_requires_skills"]
        }
    
    # 基于关键词的启发式
    SKILL_KEYWORDS = {
        "审查", "review", "检查", "check", "验证", "verify",
        "设计", "design", "构建", "build", "分析", "analysis",
        "测试", "test", "部署", "deploy", "优化", "optimize"
    }
    
    if any(kw in normalized_task.lower() for kw in SKILL_KEYWORDS):
        return {
            "decision": "single",
            "specialized_need": True,
            "reason_codes": ["keyword_match"]
        }
    
    # 默认：不确定时，倾向于提供技能
    return {
        "decision": "single",
        "specialized_need": True,
        "reason_codes": ["conservative_default"]
    }
```

**优点**:
- 快速修复，1-2天
- 不改变 cohort 限制
- 提升 need detection 准确率

**缺点**:
- 仍然只能从 7 个技能选择
- 无法解决覆盖率问题

### 方案 B：扩展 Cohort 到 30 技能（中期）⭐⭐

**目标**: 覆盖主要场景的核心技能

**新增技能**:
```python
EXTENDED_COHORT = [
    # 原有 7 个
    "codebase-explore-map",
    "code-review-risk",
    "code-test-regression",
    "execution-browser-check",
    "research-source-check",
    "design-ui-review",
    "security-supply-chain-review",
    
    # 新增 23 个
    # Design (5)
    "design-responsive-viewport-check",
    "design-accessibility-check",
    "design-visual-quality-review",
    "design-tailwind-radix-system",
    "design-premium-landing-page",
    
    # Content (3)
    "content-seo-review",
    "content-claims-compliance-filter",
    "content-i18n-check",
    
    # Data (4)
    "data-table-analysis",
    "data-table-calculation-verify",
    "data-qdrant-vector-retrieval",
    "data-haystack-rag-pipeline",
    
    # Security (3)
    "security-auth-review",
    "security-api-boundary-review",
    "security-permission-boundary-check",
    
    # AI (4)
    "ai-llamaindex-rag-knowledge-workflow",
    "ai-langchain-agent-orchestration",
    "ai-token-rate-budget-guard",
    "ai-tool-schema-protocol-check",
    
    # Business (2)
    "business-requirement-review",
    "business-metric-design",
    
    # Office (2)
    "office-pdf-extract",
    "office-spreadsheet-cleanup"
]
```

**时间**: 2-3周（每周新增7-8个技能）

### 方案 C：集成 Scenario Bundle 路由（推荐）⭐⭐⭐

**目标**: 让 v3 支持 scenario 选择，不只是单个技能

**实现**:
```python
# src/onecode_skill_sanitizer/task_pack_v3.py

def build_v3_task_pack(task: str, registry: Path, bundles: Path) -> Dict:
    # 1. Need gate 判断
    need = decide_need(task, task_profile)
    
    if need["decision"] == "none":
        # 2. 尝试 scenario 匹配（新增）
        matched_scenario = match_scenario_bundle(task, bundles)
        
        if matched_scenario:
            # 使用 scenario bundle 的技能
            return build_scenario_pack(matched_scenario, registry)
    
    # 3. 原有的 cohort 技能选择
    if need["specialized_need"]:
        return select_from_cohort(task, cohort_skills)
    
    # 4. 返回空包
    return empty_pack()
```

**优点**:
- 利用现有的 23 个 scenario bundles
- 大幅提升覆盖率
- 保持 v3 架构

**时间**: 1-2周

### 方案 D：降低选择阈值（快速修复）⚡

**修改**:
```python
# src/onecode_skill_sanitizer/skill_selection.py

# 当前阈值
SELECTION_THRESHOLD = 0.35

# 修改为
SELECTION_THRESHOLD = 0.10  # 更宽松的阈值
```

**优点**:
- 5分钟修复
- 立即提升选择率

**缺点**:
- 可能增加误选率
- 治标不治本

---

## 推荐实施计划

### 阶段 1：快速修复（本周）⚡

**任务**:
1. ✅ 诊断问题（已完成）
2. 降低选择阈值：0.35 → 0.10
3. 修复 need gate：添加启发式规则
4. 重新运行 5 个任务评估

**预期**:
- Scenario Match Rate: 20% → 60%
- Avg Skill F1: 0% → 40%

### 阶段 2：集成 Scenario 路由（1-2周）⭐

**任务**:
1. 实现 scenario bundle 匹配逻辑
2. 在 v3 中集成 scenario 路由
3. 运行 50 个任务完整评估

**预期**:
- Scenario Match Rate: 60% → 85%
- Avg Skill F1: 40% → 70%

### 阶段 3：扩展 Cohort（2-4周）📈

**任务**:
1. 每周新增 7-8 个核心技能
2. 为新技能准备路由示例
3. 持续运行回归测试

**预期**:
- Scenario Match Rate: 85% → 95%
- Avg Skill F1: 70% → 90%

---

## 关键决策点

### 决策 1：是否继续 Router v3？

**建议**: ✅ 继续，但调整策略

**理由**:
- v3 的架构设计是正确的（need gate + cohort + dependency edges）
- 当前问题是实现细节，不是架构缺陷
- 修复后有望超越 v2

### 决策 2：v3 何时成为默认？

**建议**: 🕐 延后到阶段 3 完成后

**前提条件**:
- ✅ 三臂评估 50 个任务通过（F1 ≥ 85%）
- ✅ Cohort 扩展到 30+ 技能
- ✅ Scenario 路由集成完成
- ✅ Final test 通过

**预计时间**: 1-2个月

### 决策 3：是否需要语义提供者？

**建议**: 🕐 暂时不需要

**理由**:
- 确定性路由 + scenario bundle 已经能解决大部分问题
- 语义提供者增加复杂度和成本
- 先把基础做好，再考虑智能化

---

## 下一步行动

### 立即（今天）
- [ ] 降低选择阈值到 0.10
- [ ] 添加启发式 need gate 规则
- [ ] 重新运行 5 个任务测试

### 本周
- [ ] 实现 scenario bundle 匹配
- [ ] 集成到 v3 task pack
- [ ] 运行 20 个任务评估

### 下周
- [ ] 扩展 cohort：7 → 15 技能
- [ ] 运行 50 个任务完整评估
- [ ] 生成 final test 证据

---

## 结论

Router v3 的设计理念是正确的，但当前实现过于保守和受限。通过：

1. **放宽 need gate** - 识别更多需要技能的任务
2. **集成 scenario 路由** - 利用现有 23 个 bundles
3. **扩展 cohort** - 从 7 个到 30+ 核心技能

可以让 v3 在 1-2 个月内达到生产就绪标准，成为默认路由器。

**当前不建议将 v3 设为默认**，应继续使用 Router v2，直到 v3 通过所有验收测试。
