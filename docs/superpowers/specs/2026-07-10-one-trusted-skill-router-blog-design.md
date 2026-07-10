# One Trusted Skill Router Blog Design

Date: 2026-07-10

## Goal

Publish a Chinese engineering blog that introduces Safe-Agent-Skills through
the user's practical problem: community Skills are numerous, difficult to
evaluate, difficult to combine, and may contain unsafe instructions.

The article should explain that users can install one trusted routing entry and
describe their goal directly. The router then selects trusted Skills, composes
scenario workflows, and emits an execution and verification plan for the host
Agent.

## Core Message

Use this concise promise:

> 只需安装一个安全路由入口，就能根据任务自动选择、组合可信 Skill，并生成可验证的执行方案。

Do not claim that one Skill directly performs every possible operation. The
router is a trusted selector and workflow compiler. Filesystem, shell, network,
browser, account, and publication actions remain controlled by the host
runtime.

## Audience

- AI Agent users who do not know which community Skills to install.
- Developers maintaining Codex, Claude Code, or other Agent workflows.
- Platform teams concerned about Skill supply-chain safety.
- Skill ecosystem maintainers dealing with overlap and orchestration.

## Narrative

1. Start with the user's confusion rather than the architecture.
2. Explain why installing more Skills can reduce reliability.
3. Contrast manual discovery and configuration with one trusted entry.
4. Explain scanning, sanitization, provenance, and trusted-only selection.
5. Show how a natural-language compound task becomes multiple scenarios and a
   global DAG.
6. Explain Contract v2, approval signaling, verification gates, and the host
   execution boundary.
7. Present measured evidence: 321 tests, the compound route, and the 100-case
   evaluator.
8. Disclose quality gaps and the next milestone without marketing inflation.
9. End with installation, example commands, GitHub participation, and a clear
   statement that users describe goals instead of becoming Skill experts.

## Recommended Title

社区 Skill 太多、太乱、还不安全？只安装一个可信路由 Skill 就够了

## Tone

- Engineering retrospective rather than promotional copy.
- Accessible opening, progressively deeper architecture sections.
- Concrete commands, diagrams, and measured results.
- Objective limitations remain visible.
- No claim of autonomous execution or production-ready semantic routing.

## Deliverable

Create a publication-ready Markdown article at:

`docs/blog-one-trusted-skill-router-2026-07-10.md`

The article should include a title, summary, problem framing, architecture,
real example, metrics, limitations, quick start, and conclusion.
