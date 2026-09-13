# Oracle 选择模式分析报告

**日期**: 2026-09-13  
**分析数据**: 50个评估任务，13个有场景标注的任务，10个不同场景  
**目标**: 为 Scenario Bundle v2 重新设计提供数据支持

---

## 执行摘要

通过分析 50 个评估任务中 Oracle（专家）的技能选择模式，发现当前 Scenario Bundle 设计存在严重的"kitchen sink"问题：

- **覆盖率低**: Bundle 平均只覆盖 36.7% 的 Oracle 所选技能
- **膨胀严重**: Bundle 包含的技能数是实际使用的 2.7 倍
- **浪费巨大**: Bundle 中 84.6% 的技能从未被 Oracle 使用
- **缺失严重**: 100% 的场景都有 Oracle 选择的技能不在 Bundle 中

**关键洞察**: Oracle 的选择模式清晰——每个场景平均有 2.6 个核心技能（≥70% 任务使用），加上 1.0 个条件技能（30-70% 使用）。这为 Bundle v2 的三层结构（core/conditional/optional）提供了明确的数据支持。

---

## 分析方法

### 数据来源
- 评估文件: `evals/three-arm-results/eval-phase2-3.json`
- Bundle 定义: `bundles/index.json`
- 任务数: 50 个，其中 13 个有场景标注

### 分类标准
- **Core 技能**: ≥70% 的任务都使用
- **Conditional 技能**: 30-70% 的任务使用
- **Optional 技能**: <30% 的任务使用

---

## 关键统计指标

| 指标 | 数值 | 说明 |
|------|------|------|
| 平均 Bundle 覆盖率 | 36.7% | Bundle 平均只包含 Oracle 所选技能的 1/3 |
| 平均技能膨胀率 | 2.7x | Bundle 是实际需求的 2.7 倍 |
| 平均未使用技能占比 | 84.6% | Bundle 中超过 4/5 的技能无用 |
| 平均 Core 技能数 | 2.6 个/场景 | 每个场景的核心技能 |
| 平均 Conditional 技能数 | 1.0 个/场景 | 条件依赖技能 |
| 平均 Optional 技能数 | 0.0 个/场景 | 低频技能基本不存在 |
| 场景 100% 有技能缺失 | 10/10 | 所有场景都有遗漏 |

---

## 场景详细分析

### 1. Website Build Launch (网站构建与发布)

**任务数**: 3  
**Bundle 技能数**: 14  
**问题**: 任务变化大，无固定 core 技能

**Oracle 技能使用频率**:
- execution-browser-check: 2/3 (67%) - Conditional
- design-responsive-viewport-check: 1/3 (33%) - Conditional
- content-seo-review: 1/3 (33%) - Conditional
- design-premium-landing-page: 1/3 (33%) - Conditional
- design-motion-interaction-polish: 1/3 (33%) - Conditional
- design-ui-review: 1/3 (33%) - Conditional

**Bundle 中未使用技能**: 10 个
- business-requirements-brief
- content-seo-brief
- content-social-post
- design-system-consistency
- design-tailwind-radix-system
- design-visual-quality-review
- engineering-build-release
- execution-browser-use-web-task
- execution-playwright-browser-automation
- execution-publish-check

**Bundle 缺失但 Oracle 使用**:
- design-responsive-viewport-check ✗
- content-seo-review ✗
- open-source-release ✗
- skill-router-quality-review ✗

**重新设计建议**:
```json
{
  "id": "website-build-launch",
  "name": "网站构建与发布",
  "core_skills": [],
  "conditional_skills": [
    {
      "skill": "design-responsive-viewport-check",
      "triggers": ["响应式", "自适应", "移动端", "responsive"],
      "priority": "high"
    },
    {
      "skill": "content-seo-review",
      "triggers": ["SEO", "优化", "搜索", "排名"],
      "priority": "high"
    },
    {
      "skill": "execution-browser-check",
      "triggers": ["性能", "检查", "测试", "performance"],
      "priority": "medium"
    },
    {
      "skill": "design-premium-landing-page",
      "triggers": ["落地页", "landing", "转化"],
      "priority": "medium"
    },
    {
      "skill": "design-motion-interaction-polish",
      "triggers": ["动效", "交互", "animation"],
      "priority": "low"
    }
  ]
}
```

**特殊处理**: 该场景任务变化大，建议完全依赖条件触发，无固定 core。

---

### 2. RAG Agent Knowledge App (RAG 知识问答应用)

**任务数**: 1  
**Bundle 技能数**: 9  
**膨胀率**: 3.0x

**Oracle 技能使用频率**:
- ai-llamaindex-rag-knowledge-workflow: 1/1 (100%) ✓ Core
- research-source-check: 1/1 (100%) ✓ Core
- research-citation-evidence-map: 1/1 (100%) ✗ Core (不在 Bundle 中)

**Bundle 中未使用技能**: 7 个
- ai-langchain-agent-orchestration
- ai-output-schema-eval
- ai-pydantic-schema-contract
- business-requirements-brief
- data-haystack-rag-pipeline
- data-qdrant-vector-retrieval
- security-prompt-injection-review

**重新设计建议**:
```json
{
  "id": "rag-agent-knowledge-app",
  "name": "RAG知识问答应用",
  "core_skills": [
    "ai-llamaindex-rag-knowledge-workflow",
    "research-source-check",
    "research-citation-evidence-map"
  ],
  "conditional_skills": [
    {
      "skill": "data-qdrant-vector-retrieval",
      "triggers": ["向量", "vector", "embedding", "Qdrant", "Pinecone"],
      "priority": "high"
    }
  ]
}
```

**改进**: 从 9 个技能缩减到 3 core + 1 conditional = 4 个，减少 56%

---

### 3. Code Review Hardening (代码审查加固)

**任务数**: 1  
**Bundle 技能数**: 7  
**膨胀率**: 2.3x

**Oracle 技能使用频率**:
- code-review-risk: 1/1 (100%) ✓ Core
- security-supply-chain-review: 1/1 (100%) ✓ Core
- security-auth-review: 1/1 (100%) ✗ Core (不在 Bundle 中)

**Bundle 中未使用技能**: 5 个
- ai-output-schema-eval
- ai-pydantic-schema-contract
- code-test-regression
- engineering-ci-troubleshoot
- execution-e2b-sandbox-boundary

**重新设计建议**:
```json
{
  "id": "code-review-hardening",
  "name": "代码审查加固",
  "core_skills": [
    "code-review-risk",
    "security-supply-chain-review",
    "security-auth-review"
  ],
  "conditional_skills": [
    {
      "skill": "code-test-regression",
      "triggers": ["测试", "test", "覆盖率", "coverage"],
      "priority": "medium"
    }
  ]
}
```

**改进**: 从 7 个技能缩减到 3 core + 1 conditional = 4 个，减少 43%

---

### 4. Data Analysis Report (数据分析报告)

**任务数**: 1  
**Bundle 技能数**: 6  
**膨胀率**: 2.0x

**Oracle 技能使用频率**:
- data-table-analysis: 1/1 (100%) ✓ Core
- data-table-calculation-verify: 1/1 (100%) ✗ Core (不在 Bundle 中)
- content-claims-compliance-filter: 1/1 (100%) ✗ Core (不在 Bundle 中)

**Bundle 中未使用技能**: 5 个
- data-quality-audit
- data-visualization-plan
- office-docx-brief
- office-spreadsheet-cleanup
- research-source-check

**重新设计建议**:
```json
{
  "id": "data-analysis-report",
  "name": "数据分析报告",
  "core_skills": [
    "data-table-analysis",
    "data-table-calculation-verify",
    "content-claims-compliance-filter"
  ],
  "conditional_skills": [
    {
      "skill": "data-visualization-plan",
      "triggers": ["可视化", "图表", "visualization", "chart"],
      "priority": "medium"
    }
  ]
}
```

**改进**: 从 6 个技能缩减到 3 core + 1 conditional = 4 个，减少 33%

---

### 5. Codebase Change Lifecycle (代码库变更生命周期)

**任务数**: 2  
**Bundle 技能数**: 10

**Oracle 技能使用频率**:
- code-test-regression: 2/2 (100%) ✓ Core
- code-review-risk: 2/2 (100%) ✓ Core
- code-refactor: 1/2 (50%) ✗ Conditional (不在 Bundle 中)
- execution-browser-check: 1/2 (50%) ✗ Conditional (不在 Bundle 中)

**Bundle 中未使用技能**: 8 个

**重新设计建议**:
```json
{
  "id": "codebase-change-lifecycle",
  "name": "代码库变更生命周期",
  "core_skills": [
    "code-test-regression",
    "code-review-risk"
  ],
  "conditional_skills": [
    {
      "skill": "code-refactor",
      "triggers": ["重构", "refactor", "优化", "简化"],
      "priority": "high"
    },
    {
      "skill": "execution-browser-check",
      "triggers": ["浏览器", "UI", "界面", "前端"],
      "priority": "medium"
    }
  ]
}
```

**改进**: 从 10 个技能缩减到 2 core + 2 conditional = 4 个，减少 60%

---

### 6. Commerce Listing Growth (电商产品增长)

**任务数**: 1  
**Bundle 技能数**: 5

**Oracle 技能使用频率**:
- commerce-product-content-review: 1/1 (100%) ✗ Core
- content-seo-review: 1/1 (100%) ✗ Core
- design-ui-review: 1/1 (100%) ✗ Core

**所有 Oracle 技能都不在 Bundle 中！**

**Bundle 中未使用技能**: 5 个（全部）

**重新设计建议**:
```json
{
  "id": "commerce-listing-growth",
  "name": "电商产品增长",
  "core_skills": [
    "commerce-product-content-review",
    "content-seo-review",
    "design-ui-review"
  ]
}
```

**改进**: Bundle 需要完全重新定义

---

### 7. Document To Knowledge Base (文档转知识库)

**任务数**: 1  
**Bundle 技能数**: 9

**Oracle 技能使用频率**:
- ai-llamaindex-rag-knowledge-workflow: 1/1 (100%) ✓ Core
- research-source-lineage-trace: 1/1 (100%) ✗ Core
- content-freshness-expiry-review: 1/1 (100%) ✗ Core

**重新设计建议**:
```json
{
  "id": "document-to-knowledge-base",
  "name": "文档转知识库",
  "core_skills": [
    "ai-llamaindex-rag-knowledge-workflow",
    "research-source-lineage-trace",
    "content-freshness-expiry-review"
  ]
}
```

**改进**: 从 9 个技能缩减到 3 core，减少 67%

---

### 8. Open Source Release (开源发布)

**任务数**: 1  
**Bundle 技能数**: 6

**Oracle 技能使用频率**:
- compliance-license-check: 1/1 (100%) ✗ Core
- content-freshness-expiry-review: 1/1 (100%) ✗ Core
- execution-publish-check: 1/1 (100%) ✓ Core

**重新设计建议**:
```json
{
  "id": "open-source-release",
  "name": "开源发布",
  "core_skills": [
    "compliance-license-check",
    "content-freshness-expiry-review",
    "execution-publish-check"
  ]
}
```

**改进**: 从 6 个技能缩减到 3 core，减少 50%

---

### 9. Security Agent Guardrails (Agent 安全护栏)

**任务数**: 1  
**Bundle 技能数**: 6

**Oracle 技能使用频率**:
- ai-tool-schema-protocol-check: 1/1 (100%) ✗ Core
- security-permission-boundary-check: 1/1 (100%) ✗ Core
- compliance-public-claim-risk-register: 1/1 (100%) ✗ Core

**所有 Oracle 技能都不在 Bundle 中！**

**重新设计建议**:
```json
{
  "id": "security-agent-guardrails",
  "name": "Agent安全护栏",
  "core_skills": [
    "ai-tool-schema-protocol-check",
    "security-permission-boundary-check",
    "compliance-public-claim-risk-register"
  ],
  "conditional_skills": [
    {
      "skill": "security-prompt-injection-review",
      "triggers": ["提示词", "prompt", "注入", "injection"],
      "priority": "high"
    }
  ]
}
```

**改进**: Bundle 需要完全重新定义

---

### 10. Skill Router Quality Review (路由器质量审查)

**任务数**: 1  
**Bundle 技能数**: 10

**Oracle 技能使用频率**:
- ai-routing-accuracy-review: 1/1 (100%) ✗ Core
- ai-dag-execution-graph-check: 1/1 (100%) ✗ Core
- code-test-regression: 1/1 (100%) ✓ Core

**重新设计建议**:
```json
{
  "id": "skill-router-quality-review",
  "name": "路由器质量审查",
  "core_skills": [
    "ai-routing-accuracy-review",
    "ai-dag-execution-graph-check",
    "code-test-regression"
  ]
}
```

**改进**: 从 10 个技能缩减到 3 core，减少 70%

---

## 跨场景模式总结

### 1. Core 技能数量分布
- 最少: 0 个 (website-build-launch，任务变化大)
- 最多: 3 个
- 平均: 2.6 个
- **结论**: 大部分场景有 2-3 个核心技能

### 2. Bundle 膨胀率分布
- 最低: 2.0x (data-analysis-report)
- 最高: 4.7x (website-build-launch)
- 平均: 2.7x
- **结论**: Bundle 平均包含接近 3 倍的冗余技能

### 3. 覆盖率问题
- 100% 场景都有 Oracle 技能不在 Bundle 中
- 平均覆盖率只有 36.7%
- **结论**: Bundle 定义与实际需求严重脱节

### 4. 技能缺失模式
**高频缺失技能**（多个场景需要但不在 Bundle 中）:
- `research-citation-evidence-map` (研究引用映射)
- `data-table-calculation-verify` (数据计算验证)
- `content-claims-compliance-filter` (内容合规过滤)
- `security-auth-review` (认证安全审查)
- `code-refactor` (代码重构)

---

## Bundle v2 设计原则

基于分析结果，提出以下设计原则：

### 1. 三层结构
```json
{
  "core_skills": [...],           // 必选，≥70% 任务使用
  "conditional_skills": [         // 条件选择，30-70% 使用
    {
      "skill": "...",
      "triggers": ["keyword1", "keyword2"],
      "priority": "high|medium|low"
    }
  ],
  "optional_skills": [...]        // 可选，<30% 使用（大部分场景为空）
}
```

### 2. 技能数量控制
- **Core**: 2-3 个（平均 2.6）
- **Conditional**: 0-2 个（平均 1.0）
- **Total**: 目标控制在 3-5 个

### 3. 条件触发机制
- 基于任务描述关键词
- 优先级分级 (high/medium/low)
- 支持中英文触发词

### 4. 特殊场景处理
- **任务变化大的场景** (如 website-build-launch):
  - 无固定 core，全部使用 conditional
  - 或拆分为更细粒度的子场景

- **Bundle 与 Oracle 完全不匹配的场景** (如 commerce-listing-growth):
  - 完全重新定义
  - 基于 Oracle 实际选择而非假设

---

## 量化改进预期

基于重新设计，预期改进：

| 指标 | 当前 | 目标 (v2) | 改进 |
|------|------|-----------|------|
| 平均 Bundle 技能数 | 8.1 | 3-5 | -40%~60% |
| 技能膨胀率 | 2.7x | 1.2-1.5x | -50%~60% |
| 未使用技能占比 | 84.6% | <20% | -75% |
| Bundle 覆盖率 | 36.7% | >80% | +120% |
| Skill F1 (预期) | 8.2% | >50% | +500% |

---

## 下一步行动

### Phase 4.1: 原型验证 (3-5 个 Bundle)
1. 选择代表性场景:
   - website-build-launch (变化大)
   - rag-agent-knowledge-app (典型 core)
   - code-review-hardening (混合型)
   - commerce-listing-growth (完全重定义)
   - data-analysis-report (简单场景)

2. 实施 v2 重新设计
3. 实现条件触发逻辑
4. 小规模评估 (10-15 个任务)
5. **目标**: F1 > 30% (当前 8.2%)

### Phase 4.2: 全面推广
- 如果原型验证成功 → 重新设计剩余 18 个 Bundles
- 完整 50 任务评估，目标 F1 ≥ 85%

---

## 附录: 完整数据表

### A. 场景技能统计

| 场景 ID | Bundle 技能数 | Oracle 平均技能数 | 膨胀率 | 未使用占比 |
|---------|--------------|------------------|--------|-----------|
| website-build-launch | 14 | 3.0 | 4.7x | 71% |
| rag-agent-knowledge-app | 9 | 3.0 | 3.0x | 78% |
| code-review-hardening | 7 | 3.0 | 2.3x | 71% |
| document-to-knowledge-base | 9 | 3.0 | 3.0x | 89% |
| security-agent-guardrails | 6 | 3.0 | 2.0x | 100% |
| skill-router-quality-review | 10 | 3.0 | 3.3x | 90% |
| data-analysis-report | 6 | 3.0 | 2.0x | 83% |
| open-source-release | 6 | 3.0 | 2.0x | 83% |
| commerce-listing-growth | 5 | 3.0 | 1.7x | 100% |
| codebase-change-lifecycle | 10 | 3.5 | 2.9x | 80% |

### B. 技能分类汇总

各场景 Core/Conditional/Optional 技能数量，参见各场景详细分析部分。

---

**结论**: 数据明确支持 Bundle v2 的三层结构设计。通过精确定义 core 技能和条件触发规则，可以将技能膨胀率从 2.7x 降低到 1.2-1.5x，显著提升 Precision 和 Recall。
