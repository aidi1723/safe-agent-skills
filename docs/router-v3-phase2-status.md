# Router v3 Phase 2 状态更新

**时间**: 2026-09-12 23:20  
**状态**: Phase 2.1 修复完成，等待评估结果 ⏳

---

## 修复内容

### 问题诊断
第一次降低阈值后，scenario fallback 仍然只触发了 3/50 次，原因是：
- ❌ **代码逻辑错误**: 在 `task_pack_v3.py:116` 使用了双重检查
  ```python
  # 错误的写法
  matched = match_scenario_bundle(routing_current, bundles_path)
  if matched and matched.get("match_score", 0) > 0.12:
  ```
- ❌ **阈值未生效**: `match_scenario_bundle()` 使用默认阈值 0.15，然后又检查 > 0.12
- ❌ **逻辑冗余**: 先按 0.15 过滤，再按 0.12 检查 —— 0.12 永远不会生效

### 修复方案
将阈值传递给 `match_scenario_bundle()` 函数，避免双重检查：
```python
# 正确的写法
matched = match_scenario_bundle(routing_current, bundles_path, threshold=0.12)
if matched:
    # 如果函数返回了结果，说明已经通过了 0.12 阈值
```

### 代码变更
**文件**: `src/onecode_skill_sanitizer/task_pack_v3.py`

**修改位置**: Line 115-116

**Before**:
```python
matched = match_scenario_bundle(routing_current, bundles_path)
if matched and matched.get("match_score", 0) > 0.12:
```

**After**:
```python
matched = match_scenario_bundle(routing_current, bundles_path, threshold=0.12)
if matched:
```

---

## 预期效果

基于之前的手动测试（前10个任务）：

### Before (阈值 0.15)
- Matched: 4/10 (40%)
- task-001 ✅, task-002 ✅, task-005 ✅, task-006 ✅

### After (阈值 0.12)
- Expected: 6/10 (60%)
- 新增: task-004 (0.139), task-008 (0.125)

### 完整 50 任务预期
- **Scenario Match Rate**: 74% → **80%+**
- **Scenario Fallback 触发**: 3/50 → **6-8/50**
- **Skill F1**: 0% → **10-20%** (仍然较低，因为还需要补充关键词)

---

## 当前状态

### 完成项 ✅
1. ✅ 诊断出阈值未生效的根本原因
2. ✅ 修复代码逻辑，将阈值正确传递给函数
3. ✅ 启动新的评估（eval-20260912-232xxx.json）

### 进行中 ⏳
- ⏳ 等待评估完成（预计 3-5 分钟）

### 待验证 📊
- 验证 scenario fallback 触发次数是否增加到 6+ 次
- 验证 scenario match rate 是否提升到 78-82%
- 检查哪些任务被新覆盖

---

## 下一步计划

### 如果 Phase 2.1 成功（scenario match 78-82%）

**立即执行 Phase 2.2**: 补充中文关键词

**目标 bundle** (按得分排序):
1. **data-analysis** (0.066) - 最需要优化
   - 添加: "销售", "月度", "趋势", "报告", "洞察", "数据", "分析", "图表"
   
2. **testing** (0.039) - 最需要优化
   - 添加: "测试", "用例", "覆盖", "边界", "单元测试", "集成测试"
   
3. **deployment** (0.093)
   - 添加: "发布", "开源", "许可证", "清单", "部署", "上线"
   
4. **document-processing** (0.100)
   - 添加: "pdf", "转换", "提取", "结构化", "文档", "表格"
   
5. **rag-agent** (0.139) - 接近阈值
   - 添加: "问答", "知识库", "检索", "rag系统", "向量"

**预期效果**: Scenario Match 80% → **88-92%**

### 如果 Phase 2.1 仍然失败

**回退并重新分析**:
- 检查是否有其他代码路径问题
- 考虑直接补充关键词，跳过阈值调整

---

## 技术笔记

### 为什么之前的修复无效？

**阈值的两种用法**:
1. **函数内部过滤** (推荐): `match_scenario_bundle(..., threshold=0.12)`
   - 函数内部用 `best_score >= threshold` 过滤
   - 返回 None 或 matched bundle
   
2. **外部双重检查** (错误): 
   ```python
   matched = match_scenario_bundle(...)  # 默认 threshold=0.15
   if matched and matched.get("match_score", 0) > 0.12:
   ```
   - 函数已经过滤掉 < 0.15 的结果
   - 外部检查 > 0.12 永远不会生效

**正确的做法**: 只在一个地方检查阈值（函数内部）

---

## 评估输出

**文件**: `evals/three-arm-results/eval-20260912-232xxx.json`

**关键指标监控**:
```bash
# 检查 scenario fallback 触发次数
jq -r '.results[] | select(.arms.v3.raw_output.selection.selected_scenario != null) | .task_id' eval-xxx.json | wc -l

# 检查 scenario match rate
jq '.aggregate_metrics.scenario_match_rate' eval-xxx.json

# 列出所有匹配的 scenario
jq -r '.results[] | select(.arms.v3.raw_output.selection.selected_scenario != null) | "\(.task_id): \(.arms.v3.raw_output.selection.selected_scenario)"' eval-xxx.json
```

---

## 时间线

- **23:00** - 第一次降低阈值到 0.12（代码错误）
- **23:17** - 评估完成，发现 fallback 仍只触发 3 次
- **23:18** - 诊断出双重检查问题
- **23:19** - 修复代码，正确传递阈值参数
- **23:20** - 启动第二次评估
- **23:25** (预计) - 评估完成，验证修复效果

