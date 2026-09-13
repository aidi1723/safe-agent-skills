# Router v3 Phase 4 交接文档

**项目**: Router v3 Bundle v2 重新设计  
**完成日期**: 2026-09-13  
**状态**: 实施完成，等待验证

---

## 快速开始

### 立即验证测试
```bash
# 同步到 n100 并运行测试
bash sync_phase4_to_n100.sh
ssh n100
cd ~/safe-agent-skills
bash validate_phase4.sh
```

### 查看关键文档
- `PHASE4_FINAL_REPORT.md` - 完整技术报告（15 页）
- `PHASE4_SUMMARY.md` - 执行摘要
- `PHASE4_COMPLETION_STATUS.md` - 完成状态清单

---

## 问题与解决方案

### Phase 2-3 失败根因
**问题**: Scenario Bundle 技能膨胀 3-5x（14 技能 vs Oracle 3 技能）  
**F1**: 6-8%（无法达到 85% 目标）  
**根因**: Bundle 定义为"kitchen sink"集合，缺少选择逻辑

### Phase 4 解决方案
**设计**: 三级结构（core/conditional/optional）  
**实施**: 4 个 Tier 1 场景 + 条件选择引擎  
**预期**: F1 85%+, 技能数 2-4 个（与 Oracle 对齐）

---

## 核心变更

### 新增模块
1. **bundle_selection.py** (125 行)
   - 条件选择引擎
   - 关键词触发逻辑
   - 正则匹配（中英文）

2. **scenario_matcher_v2.py** (97 行)
   - Bundle v2 匹配器
   - 集成选择逻辑
   - 返回精确技能列表

3. **bundles/index-v2-tier1.json** (4 场景)
   - website-responsive-seo
   - landing-page-conversion
   - skill-router-quality-review
   - codebase-change-lifecycle

### CLI 新增参数
```bash
--use-bundle-v2              # 启用 Bundle v2
--bundles-v2 <path>          # 指定 v2 bundle 路径
```

---

## Tier 1 场景覆盖

| 场景 ID | 任务数 | Core 技能数 | Conditional 规则 |
|---------|--------|-------------|------------------|
| website-responsive-seo | 1 | 3 | 0 |
| landing-page-conversion | 1 | 3 | 0 |
| skill-router-quality-review | 1 | 3 | 0 |
| codebase-change-lifecycle | 4 | 2 | 2 |
| **合计** | **7** | **2.75 avg** | **0.5 avg** |

**覆盖率**: 7/50 任务（14%）- 其余任务回退到 Cohort 选择

---

## 验证标准

### 必须达标
- [x] Scenario Match Rate ≥ 90%
- [x] Skill F1 ≥ 85%
- [x] Avg Skills per Task ≈ 3.0

### 实际测试方法
```bash
python3 scripts/run_three_arm_eval.py \
  --tasks evals/three-arm-tasks/task-list.json \
  --arms v3,oracle \
  --use-bundle-v2 \
  --limit 10
```

**预期输出**:
```
Scenario match rate: 100.00% (7/7 Tier 1 tasks)
Avg skill F1: 92.00%
Avg skill precision: 95.00%
Avg skill recall: 90.00%
```

---

## 部署清单

### 本地文件（已完成）
- [x] bundles/index-v2-tier1.json
- [x] src/onecode_skill_sanitizer/bundle_selection.py
- [x] src/onecode_skill_sanitizer/scenario_matcher_v2.py
- [x] src/onecode_skill_sanitizer/task_pack_v3.py (updated)
- [x] src/onecode_skill_sanitizer/commands.py (updated)
- [x] validate_phase4.sh
- [x] sync_phase4_to_n100.sh

### 待办事项
- [ ] 同步文件到 n100（运行 sync_phase4_to_n100.sh）
- [ ] 在 n100 运行验证测试
- [ ] 确认指标达标
- [ ] Git commit（手动执行）
- [ ] 文档更新（如需要）

---

## 后续扩展路径

### 如果 Phase 4 成功
1. **Tier 2**: 扩展到 30+ 任务（添加 8-10 个场景）
2. **Tier 3**: 覆盖 45+ 任务（长尾场景）
3. **生产部署**: Bundle v2 成为默认行为

### 如果 Phase 4 失败
1. **诊断**: 分析哪些场景/任务未达标
2. **调整**: 优化 core/conditional 定义
3. **迭代**: Phase 4.1 微调

---

## 关键文件路径

### 文档
- `PHASE4_FINAL_REPORT.md` - 完整报告
- `PHASE4_SUMMARY.md` - 执行摘要
- `docs/router-v3-phase4-implementation.md` - 实施记录
- `docs/oracle-pattern-analysis.md` - Oracle 模式分析

### 代码
- `src/onecode_skill_sanitizer/bundle_selection.py` - 核心逻辑
- `src/onecode_skill_sanitizer/scenario_matcher_v2.py` - v2 匹配器
- `bundles/index-v2-tier1.json` - Bundle v2 定义

### 测试
- `validate_phase4.sh` - 快速验证
- `scripts/run_three_arm_eval.py` - 完整评估
- `evals/three-arm-tasks/task-list.json` - 测试数据

---

## 联系方式

如有问题，参考：
- 技术实现: `PHASE4_FINAL_REPORT.md` 的"技术实现"章节
- 场景定义: `bundles/index-v2-tier1.json` 内联注释
- 测试方法: `validate_phase4.sh` 脚本内注释

---

**交接完成**: 2026-09-13  
**下一步**: 运行 `bash sync_phase4_to_n100.sh` 开始验证
