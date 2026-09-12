# Router v3 生产就绪路线图

**更新日期**: 2026-09-12  
**当前状态**: Phase 1 完成，准备进入 Phase 2  
**预计完成**: 2-3 周

---

## 当前进展

### Phase 1: 快速修复 ✅ 完成

**完成日期**: 2026-09-12

**修改内容**:
1. 降低选择阈值：0.35 → 0.10
2. 添加启发式 Need Gate 规则

**结果**:
- ✅ Need Gate 通过率：20% → 100%
- ✅ Scenario Match Rate：20% → 74%
- ❌ Skill F1：仍为 0%

**结论**: Need Gate 修复成功，但需要 Scenario Bundle 路由才能继续提升

---

## Phase 2: Scenario Bundle 集成 🔄 待开始

**优先级**: P0（最高）  
**预计时间**: 1-2 周  
**目标**: Scenario Match ≥ 90%, Skill F1 ≥ 60%

### 实现任务

#### Task 2.1: 实现 Scenario Bundle 匹配逻辑
**文件**: `src/onecode_skill_sanitizer/scenario_matcher.py`（新建）

```python
def match_scenario_bundle(task: str, bundles_dir: Path) -> Optional[str]:
    """
    匹配任务到最佳 scenario bundle
    
    Args:
        task: 标准化的任务描述
        bundles_dir: scenario bundles 目录
    
    Returns:
        scenario_name or None
    """
    # 1. 加载所有 scenario bundles
    scenarios = load_all_scenarios(bundles_dir)
    
    # 2. 对每个 scenario 计算匹配分数
    scores = []
    for scenario in scenarios:
        score = calculate_scenario_score(task, scenario)
        scores.append((scenario["name"], score))
    
    # 3. 返回最高分的 scenario（如果超过阈值）
    if scores:
        best_scenario, best_score = max(scores, key=lambda x: x[1])
        if best_score > SCENARIO_MATCH_THRESHOLD:  # 0.3
            return best_scenario
    
    return None

def calculate_scenario_score(task: str, scenario: Dict) -> float:
    """计算任务与 scenario 的匹配分数"""
    score = 0.0
    
    # 1. 关键词匹配
    keyword_score = keyword_overlap(task, scenario.get("keywords", []))
    score += keyword_score * 0.4
    
    # 2. 示例相似度
    example_score = max_example_similarity(task, scenario.get("examples", []))
    score += example_score * 0.3
    
    # 3. 技能描述相似度
    desc_score = description_similarity(task, scenario.get("description", ""))
    score += desc_score * 0.3
    
    return score
```

**预计时间**: 2-3 天

#### Task 2.2: 集成到 task_pack_v3
**文件**: `src/onecode_skill_sanitizer/task_pack_v3.py`

**修改点**: 在 `build_task_pack_v3()` 函数中添加 scenario 路由逻辑

```python
def build_task_pack_v3(
    task: str,
    registry_dir: Path,
    bundles_dir: Path,
    ...
) -> Dict:
    """构建 v3 任务包，支持 scenario bundle 路由"""
    
    # 1. Need gate 判断
    need = decide_skill_need(normalized_task, task_profile)
    
    # 2. 如果需要专业技能，尝试 scenario match
    if need["specialized_need"]:
        # 优先尝试 scenario bundle
        scenario = match_scenario_bundle(normalized_task, bundles_dir)
        
        if scenario:
            # 使用 scenario bundle 的技能
            return build_scenario_based_pack(
                scenario, registry_dir, need, ...
            )
        
        # 回退到 cohort 单技能选择
        return build_cohort_based_pack(
            normalized_task, COHORT_SKILLS, registry_dir, need, ...
        )
    
    # 3. 不需要技能，返回空包
    return build_empty_pack(need)
```

**预计时间**: 2 天

#### Task 2.3: 实现 scenario-based pack 构建
**文件**: `src/onecode_skill_sanitizer/task_pack_v3.py`

```python
def build_scenario_based_pack(
    scenario_name: str,
    registry_dir: Path,
    need_decision: Dict,
    ...
) -> Dict:
    """基于 scenario bundle 构建任务包"""
    
    # 1. 加载 scenario 定义
    scenario = load_scenario(scenario_name, bundles_dir)
    
    # 2. 获取 scenario 的技能列表
    skill_names = scenario.get("skills", [])
    
    # 3. 加载每个技能的详细信息
    skills = []
    for skill_name in skill_names:
        skill = load_skill(skill_name, registry_dir)
        if skill:
            skills.append(skill)
    
    # 4. 构建执行图
    execution_graph = build_execution_graph(skills, scenario)
    
    # 5. 返回完整的任务包
    return {
        "selected_scenario": scenario_name,
        "selected_skills": skill_names,
        "execution_graph": execution_graph,
        "need_decision": need_decision,
        ...
    }
```

**预计时间**: 2 天

#### Task 2.4: 测试和验证
**任务**:
1. 单元测试：scenario matcher
2. 集成测试：完整的 task pack 构建
3. 运行 50 任务评估
4. 分析结果，调整阈值

**预计时间**: 2-3 天

### Phase 2 验收标准

- [ ] Scenario Match Rate ≥ 90%
- [ ] Skill F1 ≥ 60%
- [ ] Route Completion Rate ≥ 80%
- [ ] 所有单元测试通过
- [ ] 50 任务评估通过

---

## Phase 3: Cohort 扩展与优化 📋 计划中

**优先级**: P1  
**预计时间**: 1 周  
**目标**: Skill F1 ≥ 75%, 覆盖率 ≥ 50%

### 实现任务

#### Task 3.1: 扩展 Cohort 到 15 技能
**文件**: `src/onecode_skill_sanitizer/skill_selection.py`

**新增技能**:
```python
COHORT_SKILLS = [
    # 原有 7 个
    "codebase-explore-map",
    "code-review-risk",
    "code-test-regression",
    "execution-browser-check",
    "research-source-check",
    "design-ui-review",
    "security-supply-chain-review",
    
    # 新增 8 个
    "design-responsive-viewport-check",  # 响应式设计
    "content-seo-review",                 # SEO 优化
    "data-table-analysis",                # 数据分析
    "security-auth-review",               # 认证安全
    "ai-llamaindex-rag-knowledge-workflow", # RAG 系统
    "code-refactor-risk",                 # 代码重构
    "document-extract-structure",         # 文档处理
    "commerce-listing-optimize",          # 电商优化
]
```

**预计时间**: 1 天

#### Task 3.2: 降低选择阈值
**文件**: `src/onecode_skill_sanitizer/skill_selection.py`

```python
# 从 0.10 降低到 0.01
SELECTION_THRESHOLD = 0.01
```

**预计时间**: 5 分钟

#### Task 3.3: 优化评分权重
**文件**: `src/onecode_skill_sanitizer/skill_selection.py`

**调整**:
- 提高示例匹配权重：0.3 → 0.4
- 提高关键词匹配权重
- 降低对精确 token overlap 的依赖

**预计时间**: 1-2 天

#### Task 3.4: 测试和回归
**任务**:
1. 运行 50 任务评估
2. 检查是否破坏现有功能
3. 调整权重和阈值
4. 验证 F1 提升

**预计时间**: 2-3 天

### Phase 3 验收标准

- [ ] Cohort 扩展到 15 技能
- [ ] Skill F1 ≥ 75%
- [ ] Skill Precision ≥ 70%
- [ ] Skill Recall ≥ 70%
- [ ] 无回归错误

---

## Phase 4: 完整验收测试 ✅ 最终目标

**优先级**: P0  
**预计时间**: 3-5 天  
**目标**: 通过所有验收标准

### 验收标准

#### 功能指标
- [ ] Scenario Match Rate ≥ 90%
- [ ] Avg Skill F1 ≥ 85%
- [ ] Avg Skill Precision ≥ 85%
- [ ] Avg Skill Recall ≥ 85%
- [ ] Route Completion Rate ≥ 95%
- [ ] Route Blocked Rate < 5%

#### 质量指标
- [ ] 所有单元测试通过
- [ ] 所有集成测试通过
- [ ] 50 任务完整评估通过
- [ ] 无关键 bug
- [ ] 性能满足要求（<100ms 路由延迟）

#### 文档完整性
- [ ] API 文档完整
- [ ] 使用示例齐全
- [ ] 故障排查指南
- [ ] 迁移指南（v2 → v3）

### Final Test

**要求**: 获得授权重新运行 Final Test

**前提**:
1. 所有验收标准通过
2. 完整的测试报告
3. 性能基准测试
4. 安全审查通过

---

## 时间表总结

| Phase | 任务 | 时间 | 累计 | 状态 |
|-------|------|------|------|------|
| Phase 1 | 快速修复 | 1 天 | 1 天 | ✅ 完成 |
| Phase 2 | Scenario Bundle 集成 | 1-2 周 | 2 周 | 🔄 待开始 |
| Phase 3 | Cohort 扩展 | 1 周 | 3 周 | 📋 计划中 |
| Phase 4 | 完整验收 | 3-5 天 | 3.5 周 | 📋 计划中 |

**预计总时间**: **2-3 周**

---

## 风险和缓解措施

### 风险 1: Scenario 匹配不准确

**影响**: 可能选错 scenario，导致技能不匹配

**缓解**:
- 实现回退机制：scenario 不匹配时回退到 cohort
- 添加置信度评估
- 人工审查前 10 个匹配结果

### 风险 2: 性能问题

**影响**: 路由延迟超过 100ms

**缓解**:
- 缓存 scenario 和技能定义
- 优化匹配算法
- 性能基准测试

### 风险 3: 与 v2 不兼容

**影响**: v2 用户无法平滑迁移

**缓解**:
- 保持 v2 作为默认
- 提供 v3 opt-in 机制
- 兼容层和迁移工具

---

## 决策记录

### 决策 1: 不继续调整阈值 (2026-09-12)

**背景**: Phase 1 结果显示 Skill F1 仍为 0%

**选项**:
- A: 继续降低阈值（0.10 → 0.01）
- B: 直接进入 Scenario Bundle 集成

**决定**: 选择 B

**理由**:
1. 阈值调整只是治标不治本
2. 74% scenario match 证明 need gate 已成功
3. 剩余问题需要 scenario bundle 解决
4. 调阈值会增加误选率

### 决策 2: Phase 2 优先于 Phase 3

**背景**: Scenario Bundle 和 Cohort 扩展都重要

**决定**: 先做 Scenario Bundle（Phase 2），后做 Cohort 扩展（Phase 3）

**理由**:
1. Scenario Match (74% → 90%) 对验收标准影响更大
2. 13 个失败任务都需要 scenario bundle
3. Cohort 扩展可以并行但非阻塞
4. 先解决架构问题，再优化覆盖率

---

## 成功标准

**Router v3 成为生产默认的前提**:

1. ✅ 通过所有验收标准（≥85% 各项指标）
2. ✅ 完整的测试覆盖（单元 + 集成 + E2E）
3. ✅ 性能满足要求（<100ms 路由延迟）
4. ✅ 文档齐全（API + 示例 + 故障排查）
5. ✅ Final Test 授权通过
6. ✅ 无关键安全或性能问题

**预计达标日期**: 2026-10-03（3 周后）
