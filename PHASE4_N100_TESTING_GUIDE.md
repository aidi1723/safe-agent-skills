# Phase 4 - n100 部署和测试指南

## 前置条件
- n100 服务器 SSH 访问权限
- Python 3.8+ 环境
- safe-agent-skills 代码库

## 部署步骤

### 1. 上传部署包到 n100

```bash
# 在本地执行
cd /Users/aidi/大字典/safe-agent-skills
scp phase4-deployment.tar.gz n100:~/phase4-test/
```

### 2. 在 n100 上解压并设置

```bash
# SSH 到 n100
ssh n100

# 创建测试目录
mkdir -p ~/phase4-test
cd ~/phase4-test

# 解压部署包
tar -xzf phase4-deployment.tar.gz

# 克隆完整仓库（如果还没有）
git clone <repo-url> safe-agent-skills
cd safe-agent-skills

# 复制 Phase 4 文件到仓库
cp ~/phase4-test/bundles/index-v2-tier1.json bundles/
cp ~/phase4-test/src/onecode_skill_sanitizer/bundle_selection.py src/onecode_skill_sanitizer/
cp ~/phase4-test/src/onecode_skill_sanitizer/scenario_matcher_v2.py src/onecode_skill_sanitizer/
cp ~/phase4-test/src/onecode_skill_sanitizer/task_pack_v3.py src/onecode_skill_sanitizer/
cp ~/phase4-test/src/onecode_skill_sanitizer/commands.py src/onecode_skill_sanitizer/
cp ~/phase4-test/validate_phase4.sh .
cp ~/phase4-test/test_phase4_simple.py .
```

### 3. 运行验证测试

```bash
# 测试 1: 简单 Python 测试
python3 test_phase4_simple.py

# 测试 2: 完整验证脚本
bash validate_phase4.sh

# 测试 3: 单个任务测试
python -m onecode_skill_sanitizer smart \
  "重构这个模块，提升可读性和可维护性，保持功能不变" \
  --schema-version 3 \
  --bundles bundles/index-v2-tier1.json \
  --use-bundle-v2
```

## 预期测试结果

### Test 1: Refactor 任务（应触发 code-refactor conditional）
```
Expected skills:
- code-review-risk (core)
- code-test-regression (core)
- code-refactor (conditional - triggered by "重构|可读性")

Pass criteria: code-refactor 出现在选中的技能列表中
```

### Test 2: 纯测试任务（不应触发 code-refactor）
```
Task: "为这个模块编写测试用例，覆盖核心功能和边界情况"

Expected skills:
- code-review-risk (core)
- code-test-regression (core)
- NO code-refactor

Pass criteria: code-refactor 不在选中的技能列表中
```

### Test 3: 浏览器测试任务（应触发 execution-browser-check）
```
Task: "编写浏览器自动化脚本，测试网页功能和性能"

Expected skills:
- code-review-risk (core)
- code-test-regression (core)
- execution-browser-check (conditional - triggered by "浏览器")

Pass criteria: execution-browser-check 出现在列表中
```

### Test 4: 响应式网站（website-responsive-seo scenario）
```
Task: "构建一个产品官网，包含响应式设计、SEO优化和性能检查"

Expected:
- Scenario: website-responsive-seo
- Skills (3): design-responsive-viewport-check, content-seo-brief, execution-browser-check

Pass criteria: 匹配正确的 scenario，选中恰好 3 个技能
```

### Test 5: 落地页（landing-page-conversion scenario）
```
Task: "构建一个落地页，包含动效、表单验证和转化追踪"

Expected:
- Scenario: landing-page-conversion
- Skills (3): design-premium-landing-page, design-motion-interaction-polish, execution-browser-check

Pass criteria: 匹配正确的 scenario，选中恰好 3 个技能
```

## 调试命令

### 查看匹配详情
```bash
python -m onecode_skill_sanitizer smart "YOUR_TASK" \
  --schema-version 3 \
  --bundles bundles/index-v2-tier1.json \
  --use-bundle-v2 \
  --output-format json | jq '.selection'
```

### 查看 scenario 匹配分数
```bash
python -m onecode_skill_sanitizer smart "YOUR_TASK" \
  --schema-version 3 \
  --bundles bundles/index-v2-tier1.json \
  --use-bundle-v2 \
  --output-format json | jq '.selection.scenario_match'
```

### 检查条件触发逻辑
```bash
python3 << 'EOF'
import sys
sys.path.insert(0, 'src')

from onecode_skill_sanitizer.bundle_selection import apply_bundle_selection_logic

# 测试 bundle
bundle = {
    "selection_logic": {
        "always_select": ["code-review-risk", "code-test-regression"],
        "conditional": [
            {
                "skill": "code-refactor",
                "trigger": "重构|refactor|可读性|可维护性"
            }
        ]
    }
}

# 测试任务 1: 包含触发词
task1 = "重构这个模块，提升可读性"
result1 = apply_bundle_selection_logic(task1, bundle)
print(f"Task 1: {result1}")
assert "code-refactor" in result1, "FAIL: code-refactor should be triggered"
print("✓ PASS: code-refactor triggered correctly")

# 测试任务 2: 不包含触发词
task2 = "为这个模块编写测试用例"
result2 = apply_bundle_selection_logic(task2, bundle)
print(f"Task 2: {result2}")
assert "code-refactor" not in result2, "FAIL: code-refactor should NOT be triggered"
print("✓ PASS: code-refactor correctly skipped")

print("\n✓ All logic tests passed")
EOF
```

## 成功标准

Phase 4.1 验证通过需要：
- ✓ 5 个验证测试全部通过
- ✓ 条件触发逻辑正常工作（该触发的触发，不该触发的不触发）
- ✓ Scenario 匹配准确（4 个 Tier 1 场景正确匹配）
- ✓ 技能选择数量符合预期（3-4 个，不再是 7-14 个）

## 失败排查

### 如果 code-refactor 没有触发
1. 检查任务中是否包含触发词："重构|refactor|可读性|可维护性"
2. 检查 `bundle_selection.py` 的 regex 匹配逻辑
3. 检查是否匹配到了正确的 scenario (codebase-change-lifecycle)

### 如果 scenario 匹配失败
1. 检查 `bundles/index-v2-tier1.json` 是否正确部署
2. 检查 task_signals 是否包含任务关键词
3. 降低 threshold 重试：`--threshold 0.10`

### 如果选择了过多技能
1. 检查是否使用了 `--use-bundle-v2` flag
2. 检查是否回退到了 Phase 3.1 逻辑
3. 查看 `selection_method` 字段（应该是 "scenario_bundle_v2_conditional"）

## 完整评估（验证通过后）

```bash
# 运行 50 任务完整评估
python scripts/run_three_arm_eval.py \
  --tasks evals/three-arm-tasks/task-list.json \
  --arms v3,oracle \
  --output evals/three-arm-results/eval-phase4-bundle-v2.json \
  --use-bundle-v2

# 生成对比报告
python scripts/analyze_eval_results.py \
  --phase3 evals/three-arm-results/eval-phase3-1.json \
  --phase4 evals/three-arm-results/eval-phase4-bundle-v2.json
```

预期指标：
- Scenario Match Rate: ≥90%
- Skill F1: ≥85%
- Precision: ≥85%
- Recall: ≥85%

---

**部署包位置**: `/Users/aidi/大字典/safe-agent-skills/phase4-deployment.tar.gz`  
**文档更新**: 2026-09-13  
**状态**: 就绪，等待 n100 测试验证
