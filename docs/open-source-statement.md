# Open Source Statement

## Safe Agent Skills: Agent 时代的安全技能公用仓库

AI Agent 工程真正难的地方，往往不是没有工具，而是工具太散、来源太杂、边界太不清楚。

社区里已经有大量有价值的 skill、prompt、工具配置和工作流经验：有人写了 PDF 处理技巧，有人沉淀了代码审查流程，有人做了记忆、上下文压缩、安全扫描、交易研究、浏览器执行等方向的探索。但这些资产通常散落在不同仓库、论坛、视频和个人笔记里。开发者想用它们，常常要自己搜索、判断、改写、适配、测试，还要承担提示词注入、隐藏执行、权限越界、账单失控和供应链污染的风险。

`OneCode Skill Sanitizer` 的目标，就是把这些碎片化的 Agent 技能资产，变成一个可审计、可追踪、可维护的安全目录。

本仓库公开出来的 skill，不是未经验证的 prompt 合集。它们已经经过 OneCode 的治理流程：来源记录、确定性静态风险预检、状态审查、哈希记录和 registry 完整性验证。部分社区项目条目是参考公开项目后本地撰写的 reference skill，不代表复制或清洗了上游仓库内容。因此，这个项目相比直接复制互联网上未经验证的提示词或 Agent 指令，更可审计、更适合长期维护；但它不应被当作独立安全沙箱或完整恶意内容检测器。

## 我们要解决什么

### 1. 技能太散

开发者不应该为了完成一个常见任务，到处复制未经验证的 prompt 或脚本。

这个仓库会持续沉淀常见 Agent 任务需要的技能目录，例如：

- 设计与 UI 审查
- 代码调试、测试、评审
- 工程构建、CI、发布检查
- 安全审计、供应链检查、提示词注入防护
- 办公文档、表格、报告处理
- 数据分析、研究、内容、贸易、媒体、合规和行业流程
- 热门社区 Agent 项目的参考型技能卡

当前公开基线已经覆盖 15 个一级分类，每个分类至少 3 个 `trusted` skill。

最新更新声明：
[Bundle-Aware Task Packs and OpenSquilla Reference Batch](updates/2026-06-04-bundle-aware-task-pack-opensquilla.md)。

本次更新后，`task-pack` 不仅可以根据任务自动选择单个优秀 skill，也可以通过
`--include-bundles` 自动匹配场景组合，例如建站、RAG 知识库、代码审查、
Agent 安全、开源发布、内容 SEO 和贸易增长。也就是说，用户不需要自己到处
找 prompt，Agent 可以从这个经过 OneCode 治理和验证过的 skill 仓库中，
按任务自动搭配更合适的安全 skill 和场景 playbook。

### 2. 技能不可信

一个从网上复制来的 skill，不应该天然获得执行权限。

本项目坚持一个原则：

> 没有经过记录、清洗、审查和验证的 skill，默认不可信。

所有外部或社区来源的 skill 都必须先进入隔离状态，再经过确定性风险预检、内容审查、来源记录、哈希校验和人工审批，才可以成为默认可选择的 `trusted` skill。

`trusted` 的含义是：该 skill 已通过当前 OneCode 审查与验证流程，可以进入默认选择范围。它不代表来源内容 100% 安全，也不代表无边界执行权限；文件系统、网络、连接器、生产环境操作等能力仍必须由宿主运行时的策略和审批层控制。

### 3. 技能难维护

普通 prompt 合集最大的问题，是后续无法判断：

- 它来自哪里
- 谁写的
- 什么许可证
- 是否被改过
- 为什么被批准
- 是否还适合默认调用

本项目要求每个 skill 都记录：

- source URL
- source path
- author
- license
- reference
- collector
- capture timestamp
- source hash
- sanitized hash

这让 skill 不再是散落的文本片段，而是可以进入长期维护的工程资产。

## 项目定位

`OneCode Skill Sanitizer` 不是一个“网上 prompt 大杂烩”。

它更接近一个 Agent 技能的安全配置中心：

```text
untrusted community skill
  -> source capture
  -> deterministic risk preflight scan
  -> instruction distillation
  -> policy rewrite or bounded local synthesis
  -> provenance record
  -> hash verification
  -> quarantined registry entry
  -> operator approval
  -> trusted skill
```

Skills provide method.

OneCode provides boundary, execution control, verification, and evidence.

## 所有 Agent 都可以安全调用

这些 skill 不是 Claude 专属，也不是 Codex 专属。

每个 skill 都是经过审查和哈希记录的 `SKILL.md` 说明书，场景组合则是由多个
`trusted` skill 组成的任务 playbook。Claude、Codex、OpenClaw、
Cursor、本地 Agent、MCP Host、CI Worker 和自研 Agent 都可以读取这些
Markdown 或 JSON 说明，并把它们放进自己的规划上下文中。

通用调用方式有两种：

- 直接读取单个 `SKILL.md`
- 通过 `task-pack` 根据任务自动选择匹配的 `trusted` skill

场景组合适合更大的任务，例如：

- 建站：需求、工程、UI、文案、SEO、浏览器验证、发布检查组合使用
- RAG 知识库：编排、文档索引、检索、向量库、结构化输出、来源核验组合使用
- 代码审查：风险审查、回归测试、结构化输出、供应链、安全沙箱和 CI 组合使用
- Agent 安全：提示词注入、输出护栏、I/O 扫描、供应链、隐私边界组合使用

安全边界保持不变：

> skill guidance is method, not execution authority.

skill 可以告诉 Agent 如何做任务，但不能自动授予文件系统、Shell、网络、
浏览器、连接器、账号或生产环境写入权限。这些权限必须由 Claude、Codex、
OpenClaw、OneCode 或其他宿主运行时自己的安全策略控制。

详见 [Agent-Compatible Skill Bundles](agent-compatible-skill-bundles.md)。

## 安全边界

这个仓库不会默认执行第三方 skill。

进入目录的社区项目，优先以“参考型 skill”方式重写：保留有价值的方法、检查清单、任务流程和安全边界，不直接复制第三方 runtime code、隐藏 prompt 或危险执行逻辑。

当前安全机制包括：

- 确定性静态风险预检
- 危险片段移除或本地安全重写
- trusted / quarantined / review_required 状态分离
- 默认只选择 `trusted` skill
- 来源与许可证记录
- `SKILL.md` 哈希校验
- registry 完整性验证
- 批次文档和维护记录

未来可以继续增强：

- 更严格的 AST / 结构化审计
- CI PR 自动拦截
- connector 权限模型
- 沙箱测试用例
- lockfile 化的运行时加载保护
- 社区贡献评分与回溯机制

## 当前公开基线

当前 catalog 状态：

```text
total skills: 114
trusted skills: 108
quarantined skills: 3
review_required skills: 3
scenario bundles: 13 trusted
top-level categories: 15 / 15
minimum trusted coverage: 3 trusted skills per category
tampered skills: 0
unknown provenance records: 0
registry verification: ok
bundle maintenance check: ok
```

这意味着仓库已经具备公开维护的最低基础：不是只放几个示例，而是每个核心分类都有可默认选择的安全 skill。

这些 `trusted` skill 均保留了清洗报告和哈希记录，后续如被篡改，可以通过 registry verify 流程发现。

## 我们欢迎什么贡献

欢迎贡献：

- 新的安全 skill
- 对现有 skill 的改写和压缩
- 更好的分类、验证器和风险规则
- 社区热门 Agent 项目的参考型清洗记录
- 更严格的审计、哈希、CI、沙箱和连接器方案

不欢迎：

- 未注明来源的复制内容
- 隐藏执行逻辑
- 要求绕过沙箱、审批或系统规则的指令
- 宽泛读取本机文件或凭证的指令
- 未经验证的金融、医疗、法律、生产环境自动执行流程
- 会导致成本失控的无限循环或无边界调用流程

## 一句话介绍

不要再到处复制未经验证、来源不明、边界不清的 Agent 技能了。

`OneCode Skill Sanitizer` 是一个面向 AI Agent 的安全技能公用仓库：它把社区和工程实践中的高价值技能，清洗成来源可追踪、默认不越权、可哈希验证、可长期维护的 `trusted` skill 资产。
