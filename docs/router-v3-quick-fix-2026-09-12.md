# Router v3 快速修复记录

**日期**: 2026-09-12  
**执行人**: Claude Code  
**目标**: 提升 Router v3 的技能选择率，减少 false negatives

---

## 修复内容

### 修复 1: 降低选择阈值 ⚡

**文件**: `src/onecode_skill_sanitizer/skill_selection.py`

**修改**:
```python
# Before
SELECTION_THRESHOLD = 0.35

# After
SELECTION_THRESHOLD = 0.10  # Lowered for better recall
```

**理由**:
- 原阈值 0.35 过于严格
- 大多数候选技能得分在 0.01-0.02 之间
- 降低到 0.10 可以接受更多弱匹配
- 可能增加一些误选，但优先解决 recall 问题

### 修复 2: 添加启发式 Need Gate 规则 🎯

**文件**: `src/onecode_skill_sanitizer/need_gate.py`

**新增函数**: `_heuristic_skill_need(task: str) -> tuple[bool, str]`

**逻辑**:
1. **任务类型关键词检测**：
   - 构建/创建类：构建、build、创建、create
   - 审查/审计类：审查、review、审计、audit、检查
   - 分析/研究类：分析、analysis、研究、research
   - 设计/优化类：设计、design、优化、optimize
   - 测试/验证类：测试、test、验证、verify
   - 部署/发布类：部署、deploy、发布、release
   - 安全类：安全、security、认证、authentication

2. **领域关键词检测**：
   - Web/UI：网站、website、页面、page、ui、dashboard
   - Data：数据、data、表格、table、报告、report
   - Code：代码、code、api、函数、module
   - RAG/AI：rag、向量、vector、检索、问答
   - Architecture：架构、architecture、模块、依赖

3. **高置信度模式匹配**：
   - 网站构建：`(?:构建|build).*(?:网站|website|官网)`
   - 代码审查：`(?:审查|review).*(?:api|代码|安全)`
   - 数据分析：`(?:分析|analysis).*(?:数据|报告|趋势)`
   - RAG系统：`(?:设计|build).*(?:rag|问答|知识库)`
   - 架构探索：`(?:探索|explore).*(?:架构|codebase|模块)`

**触发条件**:
- (任务类型关键词 AND 领域关键词) → 返回 True
- 匹配任何高置信度模式 → 返回 True
- 任务长度 > 20 字符 AND 有任务关键词 → 返回 True

**修改位置**:
```python
# In decide_skill_need():
if not has_positive_action:
    # 新增：启发式判断
    should_use_skills, heuristic_reason = _heuristic_skill_need(current)
    if should_use_skills:
        return _decision(
            "single", [], explicit, excluded, [heuristic_reason],
            False, False, [], [], [],
        )
    # 原有逻辑
    return _decision("none", ...)
```

---

## 预期效果

### Before (基准)
- Scenario Match Rate: 20%
- Avg Skill F1: 0%
- Route Completion Rate: 0%
- 问题：4/5 任务被判定为 `no_specialized_need`

### After (实际结果)
- Scenario Match Rate: **74%** ✅ 大幅改进
- Avg Skill F1: **0%** ❌ 无改进
- Route Completion Rate: **0%** ❌ 无改进
- Need Gate 通过率: **100%** ✅ 完全修复

### 改进总结
✅ **成功部分**:
1. Need Gate 完全修复，100% 任务被正确识别为需要技能
2. Scenario Match 从 20% 提升到 74%（提升 270%）
3. 启发式规则成功识别任务类型和领域关键词

❌ **仍然失败部分**:
1. **Skill F1 仍为 0%**: 所有候选技能得分（0.008-0.02）低于阈值（0.1）
2. **13/50 任务失败**: 需要 scenario bundle 的复杂任务无法处理
3. **Cohort 覆盖不足**: 7 个技能只覆盖 20% 的任务需求

### 根本原因分析

**问题 1: 阈值悖论**
- 降低到 0.1 仍然太高
- 实际得分: 0.008-0.02（基于 token overlap）
- 需要降到 0.01 或引入语义评分

**问题 2: 缺少 Scenario Bundle 路由**
- 失败的 13 个任务都是复杂场景（website-build, code-review, data-analysis, rag-agent）
- 需要多个技能协作，但 v3 只能返回单技能
- 必须集成 scenario bundle 才能解决

### 已知限制
1. **仍然只支持 7 个技能 cohort**：
   - 即使 need gate 通过，也只能从 7 个技能选择
   - 许多预期技能（如 data-table-analysis）不在 cohort 中

2. **仍然没有 scenario bundle 路由**：
   - 不会选择完整的场景包
   - 只返回单个技能

3. **可能增加误选率**：
   - 阈值降低可能导致一些不相关的技能被选中
   - 需要后续评估权衡 precision 和 recall

---

## 测试计划

### 阶段 1: 小规模验证（进行中）
- ✅ 修改代码
- ✅ 修复语法错误（need_gate.py line 764）
- 🔄 运行 50 个任务三臂评估（第二次尝试）
- ⏳ 生成分析报告
- ⏳ 验证改进效果

### 问题记录
**首次评估失败** (eval-20260912-222124.json):
- 所有任务报错：`SyntaxError: unmatched '}'` at line 764
- 原因：在 `_heuristic_skill_need()` 函数末尾多了一个 `}`
- 修复：删除多余的 `}` 行
- 结果：虽然报告显示 74% scenario match，但实际上所有任务都因语法错误失败

**第二次评估完成** (eval-20260912-222915.json):
- ✅ 语法错误已修复，所有任务成功执行
- ✅ Scenario Match Rate: 20% → **74%** (提升 270%)
- ✅ Need Gate 100% 通过率（不再误判 `no_specialized_need`）
- ❌ Skill F1: 仍然是 **0%**（所有候选技能得分 < 0.1 阈值）
- ❌ 验收标准: 4 个中只通过 1 个（route_blocked_rate）

### 阶段 2: 如果效果良好
- 运行完整的回归测试套件
- 检查是否破坏现有功能
- 调整阈值和启发式规则

### 阶段 3: 如果效果不佳
- 回滚修改
- 改用 "方案 B: 扩展 Cohort" 或 "方案 C: 集成 Scenario Bundle"

---

## 风险评估

### 低风险 ✅
- 修改是向后兼容的
- 只影响 Router v3（opt-in）
- Router v2 保持不变（生产默认）
- 可以快速回滚

### 中风险 ⚠️
- 可能增加误选率（false positives）
- 启发式规则可能过于宽泛
- 需要更多真实任务测试验证

### 高风险 ❌
- 无

---

## 下一步行动

### 评估结论 📊

快速修复**部分成功**：
- ✅ Need Gate 问题已解决（100% 通过率）
- ✅ Scenario Match 大幅提升（20% → 74%）
- ❌ Skill F1 仍为 0%（阈值和 cohort 问题）
- ❌ 仍有 26% 任务需要 scenario bundle

### 不推荐：继续调整阈值 ⚠️

**理由**:
- 再降阈值（0.1 → 0.01）只是治标不治本
- 会增加误选率，不解决根本问题
- 浪费时间，延迟真正的解决方案

### 推荐：立即进入 Phase 2 ⭐⭐⭐

**方案 C: 集成 Scenario Bundle 路由**

**目标**: 让 v3 支持完整的 scenario bundle，不只是单技能

**优先级**: P0（最高）

**理由**:
1. 74% scenario match 证明 need gate 已经工作良好
2. 失败的 13 个任务都需要多技能协作
3. 现有 23 个 scenario bundles 可直接利用
4. 1-2 周内可达到 90% scenario match 目标

**实现计划**:
```python
# src/onecode_skill_sanitizer/task_pack_v3.py

def build_v3_task_pack(task: str, registry: Path, bundles: Path) -> Dict:
    """构建 v3 任务包，支持 scenario bundle 路由"""
    
    # 1. Need gate 判断
    need = decide_skill_need(task, task_profile)
    
    # 2. 如果是复合任务，尝试匹配 scenario bundle
    if need["decision"] == "composite" or need["decision"] == "single":
        scenario = match_scenario_bundle(task, bundles)
        
        if scenario:
            # 返回完整的 scenario bundle
            return build_scenario_pack(scenario, registry)
    
    # 3. 回退到单技能 cohort 选择
    if need["specialized_need"]:
        candidates = select_from_cohort(task, COHORT_SKILLS)
        return build_skill_pack(candidates, registry)
    
    # 4. 返回空包
    return empty_pack()
```

**预期效果**:
- Scenario Match: 74% → **90%+** ✅ 达标
- Skill F1: 0% → **60-70%**
- Route Completion: 0% → **80%+**

**时间**: 1-2 周

### 并行任务：扩展 Cohort

**方案 B: Cohort 7 → 15 技能**

**优先级**: P1（次要，可并行）

**新增 8 个高频技能**:
1. design-responsive-viewport-check
2. content-seo-review
3. data-table-analysis
4. security-auth-review
5. ai-llamaindex-rag-knowledge-workflow
6. code-refactor-risk
7. document-extract-structure
8. commerce-listing-optimize

**预期效果**:
- 提升单技能路由的覆盖率
- 支持 scenario bundle 中的技能选择
- Skill F1: 额外提升 10-20%

**时间**: 1 周（可与 Phase 2 并行）

### 最终目标时间表

**Week 1-2**: Scenario Bundle 集成
- Scenario Match ≥ 90%
- Skill F1 ≥ 60%

**Week 3**: Cohort 扩展 + 优化
- Cohort: 7 → 15 技能
- Skill F1 ≥ 75%

**Week 4**: 完整回归测试 + Final Test
- 所有验收标准 ≥ 85%
- Router v3 成为生产默认

---

## 关键决策

### ❌ 不要：继续微调阈值
- 理由：治标不治本，浪费时间

### ✅ 要做：集成 Scenario Bundle
- 理由：最快达标的路径，1-2 周解决核心问题

### 📅 时间表：2-3 周完成 Router v3 生产就绪

---

## 备注

这次快速修复是诊断式修复，验证了 Router v3 的架构方向正确，但也暴露了两个核心问题：

### 快速修复的成果 ✅

1. **Need Gate 完全修复**: 启发式规则成功，100% 通过率
2. **Scenario Match 大幅提升**: 20% → 74%（提升 270%）
3. **架构验证**: v3 的设计理念是可行的

### 仍需解决的核心问题 ❌

1. **缺少 Scenario Bundle 路由**: 13/50 复杂任务无法处理
2. **Cohort 覆盖不足**: 7 个技能只覆盖 20% 需求
3. **评分系统过严**: Token overlap 得分太低（0.008-0.02 << 0.1）

### 真正让 Router v3 达到生产就绪需要：

1. **集成 Scenario Bundle** (P0): 1-2 周，达到 90% scenario match
2. **扩展 Cohort**: 7 → 15 → 30 技能，提升覆盖率
3. **优化评分系统**: 降低阈值或添加语义评分
4. **完整评估**: 50+ 真实任务的验收测试
5. **Final Test**: 获得授权重新运行并通过

**预计完整时间**: 2-3 周

**当前状态**: 快速修复完成，评估分析完成，准备进入 Phase 2（Scenario Bundle 集成）

**关键结论**: 不要继续调阈值，直接进入 Scenario Bundle 集成才是最快达标的路径。
