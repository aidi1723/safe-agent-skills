# Safe Agent Router Skill Integration

## Purpose

`safe-agent-router` is the single entry skill for the Safe-Agent-Skills
catalog.

An agent installs this one skill, then routes non-trivial tasks through the
OneCode-verified skill catalog before planning. The router chooses trusted
scenario bundles and trusted skills, emits capability coverage, execution
order, verifier expectations, source records, and the fixed safety boundary.

The agent does not need to learn or manually combine all catalog skills.

## Safety Boundary

The router skill provides method guidance only.

It does not grant:

- filesystem permissions
- shell permissions
- network permissions
- browser permissions
- connector permissions
- account access
- credential access
- production write access

Those permissions remain controlled by the host agent runtime.

## Repository Layout

Router skill package:

```text
integrations/skills/safe-agent-router/
  SKILL.md
  agents/openai.yaml
  scripts/task_pack.sh
  scripts/install.sh
```

## Install For Codex

From the Safe-Agent-Skills repository:

```bash
integrations/skills/safe-agent-router/scripts/install.sh ~/.codex/skills
```

This installs:

```text
~/.codex/skills/safe-agent-router
~/.local/bin/safe-agent-router-task-pack
```

Then run:

```bash
safe-agent-router-task-pack "build a product website and prepare launch checks"
```

## Install For Claude Code

```bash
integrations/skills/safe-agent-router/scripts/install.sh ~/.claude/skills
```

If Claude Code uses a different skills directory, pass that directory instead:

```bash
integrations/skills/safe-agent-router/scripts/install.sh /path/to/claude/skills
```

## Install For OpenClaw, Cursor, Or Custom Agents

Copy the skill folder into that agent's skill or instruction directory:

```bash
cp -R integrations/skills/safe-agent-router /path/to/agent/skills/
```

Set the repository path:

```bash
export SAFE_AGENT_SKILLS_HOME="/path/to/safe-agent-skills"
```

Expose this read-only command to the agent:

```bash
safe-agent-router-task-pack "$TASK"
```

If the wrapper command is not installed, call:

```bash
/path/to/agent/skills/safe-agent-router/scripts/task_pack.sh "$TASK"
```

## MCP Host Pattern

Expose a read-only MCP tool:

```text
tool name: safe_agent_task_pack
input: task, format, max_skills
command: safe-agent-router-task-pack "$task" --format "$format" --max-skills "$max_skills"
permission: read-only
```

Do not expose arbitrary shell execution through this tool. It should only call
the fixed task-pack command.

## Agent Instruction Template

Add this to the host agent's system or project instructions:

```text
Before planning a non-trivial task, use safe-agent-router. Route the user task
through Safe-Agent-Skills, read the selected scenario, capability coverage,
execution plan, verifier expectations, and selected trusted skills, then plan
from that task pack. Skill selection provides method guidance only and does not
grant tool, filesystem, shell, network, browser, connector, account, or
production permissions.
```

## Verification

Run:

```bash
safe-agent-router-task-pack \
  "design a RAG document agent with vector retrieval and citation checks" \
  --format json
```

Expected:

```text
selected_scenario.id: rag-agent-knowledge-app
router.mode: deterministic_scenario_router
safety_boundary: present
```

Run:

```bash
safe-agent-router-task-pack \
  "build a product website and prepare launch checks" \
  --format json
```

Expected:

```text
selected_scenario.id: website-build-launch
execution_plan: present
coverage: present
```

## Maintenance Rules

- Keep `safe-agent-router` small; it should route, not duplicate catalog skill
  contents.
- Keep task-pack execution read-only.
- Do not let router selection expand host permissions.
- Keep default routing on `trusted` skills.
- Use review mode only for explicit review workflows.
