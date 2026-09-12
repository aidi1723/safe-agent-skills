# Safe Agent Skills 优化计划

**制定日期**: 2026-09-12  
**目标**: 实现"单一安装 → 智能编排 → 完美执行"的设计标准  
**当前完成度**: 70%

---

## 📊 现状评估

### ✅ 已实现（70%）

1. **单一安装入口**: safe-agent-router 作为唯一需要安装的技能
2. **技能治理体系**: 96.5% 技能通过信任审核，完整的来源追溯和哈希验证
3. **确定性编排**: DAG 执行图、多意图分解、场景组合（23 bundles）
4. **Router v2**: 生产就绪的确定性路由（默认）

### ⚠️ 关键差距（30%）

1. **Router v3**: 智能技能选择能力存在，但未通过最终验收
   - 状态: opt-in，仅支持 7 个高频技能
   - 阻塞: final_test 失败、缺少三臂任务评估
   
2. **执行能力**: 当前是 method-only，只提供方法指导，不负责执行监控

3. **覆盖范围**: v3 仅覆盖 7/172 技能（4%）

---

## 🎯 三阶段优化路线图

### 阶段一：Router v3 生产化（2-4周）⚡

#### 目标
- Router v3 从 opt-in 变为默认
- 智能度从 60% → 85%

#### 任务清单

**任务 1.1：三臂任务评估** (Week 1-2)
- [ ] 准备 50 个真实任务（覆盖所有主要场景）
  - website-build: 10 个
  - code-review: 8 个
  - data-analysis: 8 个
  - security: 6 个
  - rag-agent: 6 个
  - office: 6 个
  - commerce: 6 个
- [ ] 建立三臂评估框架
  - Arm 1: v3 路由选择
  - Arm 2: 人工专家选择（oracle）
  - Arm 3: 无技能基线
- [ ] 运行评估并收集数据
  - 任务完成率
  - 执行质量评分
  - 时间效率
- [ ] 分析结果，确保 v3 ≥ oracle 的 90%

**任务 1.2：Final Test 重新验收** (Week 3)
- [ ] 获得明确授权重新运行 final_test
- [ ] 确保所有质量门禁达标
  - forbidden_skill_false_positive_rate < 0.02 ✓
  - dag_validity >= 0.98 ✓
  - dependency_edge_precision >= 0.70 ✓
  - dependency_edge_recall >= 0.70 ✓
  - multi_intent_exact_match >= 0.92 ✓
- [ ] 生成完整的评估证据文档

**任务 1.3：生产化部署** (Week 4)
- [ ] 将 Router v3 设为默认 schema
- [ ] Router v2 保留为 fallback（--schema-version 2）
- [ ] 更新所有文档和 README
- [ ] 发布 v3 生产就绪声明

**验收标准**:
- ✅ 三臂评估通过（v3 完成率 ≥ 90% oracle）
- ✅ Final test 所有门禁通过
- ✅ v3 成为默认 router

---

### 阶段二：扩展智能覆盖（1-2个月）📈

#### 目标
- 从 7 个技能扩展到 30+ 核心技能
- 覆盖率从 4% → 18%

#### 任务清单

**任务 2.1：技能频率分析** (Week 5)
- [ ] 分析现有 172 个技能的使用频率
- [ ] 识别高频但未在 v3 cohort 的技能
- [ ] 按优先级排序（P0 > P1 > P2）

**任务 2.2：渐进式扩展** (Week 6-12)
- [ ] 每周新增 3-5 个技能到 v3 cohort
- [ ] 为每个新技能准备数据
  - 至少 20 个路由示例
  - Contract v2 元数据完整
  - 评估集覆盖
- [ ] 持续运行回归测试

**优先扩展的技能类别**:
1. **code** (Week 6-7)
   - code-refactor
   - code-dependency-check
   - code-architecture-review
   
2. **security** (Week 8)
   - security-auth-review
   - security-api-boundary-review
   
3. **data** (Week 9)
   - data-pipeline-review
   - data-quality-check
   
4. **business** (Week 10)
   - business-requirement-review
   - business-metric-design
   
5. **content** (Week 11)
   - content-seo-review
   - content-i18n-check

**任务 2.3：启用语义影响** (Week 12)
- [ ] 分析 semantic shadow disagreement 数据
- [ ] 设计 fallback 机制
- [ ] 渐进式开启（10% → 50% → 100%）

**验收标准**:
- ✅ v3 cohort 包含 30+ 技能
- ✅ 每个类别至少 2 个技能在 cohort
- ✅ 语义影响启用且 disagreement < 5%

---

### 阶段三：执行引导模式（3-6个月）🎯

#### 目标
- 从 method-only 演进到 guided_execution
- 任务完成率从 70% → 90%

#### 任务清单

**任务 3.1：执行监控模块** (Month 3)
- [ ] 设计执行协议规范
  - 执行事件 schema
  - 进度报告格式
  - 验证器结果格式
- [ ] 实现 ExecutionMonitor 模块
  - track_execution_progress()
  - detect_execution_drift()
  - suggest_recovery_path()
- [ ] 单元测试和集成测试

**任务 3.2：扩展 Task Pack Schema** (Month 3)
- [ ] 添加 guided_execution 模式支持
- [ ] 定义监控配置
- [ ] 定义恢复策略
- [ ] 更新 schema 验证

**任务 3.3：宿主 Agent 集成** (Month 4-5)
- [ ] Claude Code 深度集成
  - MCP 执行监控接口
  - 节点完成回调
  - 实时引导提示
- [ ] Codex 集成
  - 执行日志自动上报
  - 问题检测和提示
- [ ] 通用集成协议
  - REST API 设计
  - 认证和授权
  - 速率限制

**任务 3.4：质量闭环** (Month 6)
- [ ] 实现执行质量追踪
  - task_completion_rate
  - execution_accuracy
  - verifier_pass_rate
- [ ] 建立反馈学习机制
- [ ] 自动生成改进建议

**验收标准**:
- ✅ guided_execution 模式上线
- ✅ 至少 1 个宿主 Agent 深度集成
- ✅ 任务完成率 > 85%

---

## 📋 即时行动计划（本周）

### 行动 1：建立评估框架

```bash
# 创建评估目录结构
mkdir -p evals/three-arm-tasks
mkdir -p evals/three-arm-results

# 创建任务模板
cat > evals/three-arm-tasks/task-template.json
```

### 行动 2：准备真实任务集

需要准备 50 个真实任务，覆盖：
- 网站构建和发布
- 代码审查和测试
- 数据分析和报告
- 安全审计
- RAG 应用设计
- 办公文档处理
- 电商运营

### 行动 3：设计评估脚本

```bash
# 创建评估脚本
touch scripts/run_three_arm_eval.py
touch scripts/analyze_eval_results.py
```

---

## 🎯 成功标准（里程碑）

### Level 1：基础达标 ✅（当前）
- [x] 单一安装入口
- [x] 确定性编排
- [x] 完整的治理体系

### Level 2：智能达标（3个月内目标）⭐
- [ ] Router v3 为默认
- [ ] 覆盖 30+ 核心技能
- [ ] 语义理解能力启用
- [ ] 多意图准确率 > 95%

### Level 3：执行达标（6个月内目标）⭐⭐
- [ ] guided_execution 模式上线
- [ ] 实时执行监控
- [ ] 自动恢复建议
- [ ] 任务完成率 > 85%

### Level 4：完美达标（12个月目标）⭐⭐⭐
- [ ] 全目录智能路由（172 技能）
- [ ] 端到端质量保证
- [ ] 自适应学习机制
- [ ] 任务完成率 > 95%

---

## 📅 时间线

```
Week 1-2:  三臂任务评估
Week 3:    Final test 验收
Week 4:    v3 生产化部署
Week 5-12: 扩展到 30 技能
Month 3:   执行监控模块
Month 4-5: 宿主集成
Month 6:   质量闭环

里程碑：
- 1 个月后: Router v3 为默认
- 3 个月后: 30+ 技能智能路由
- 6 个月后: guided_execution 上线
```

---

## 🔗 相关文档

- [审计报告](AUDIT_REPORT.md)
- [Router v2 里程碑报告](docs/hybrid-router-v2-first-milestone-report.md)
- [Router v3 关闭报告](docs/high-frequency-intelligent-skill-selection-v3-closure-report-2026-07-16.md)
- [路由器开发指南](docs/router-development.md)

---

**下一步**: 开始任务 1.1 - 建立三臂评估框架
