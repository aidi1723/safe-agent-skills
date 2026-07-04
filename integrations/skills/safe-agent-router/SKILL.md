---
name: safe-agent-router
description: Use when an agent is about to plan or execute a non-trivial user task and should first select trusted Safe-Agent-Skills, scenario bundles, execution order, capability coverage, and verifier guidance from the OneCode-verified skill catalog.
---

# Safe Agent Router

## Overview

Use this as the single entry skill for the Safe-Agent-Skills catalog. Before
planning a non-trivial task, route the task through the verified catalog and
then follow the returned task pack.

The host agent does not need separate local installs for every catalog skill.
Install this router once; it selects the right trusted skills and scenario
bundle for each task on demand.

The router gives method guidance only. It never grants filesystem, shell,
network, browser, connector, account, credential, or production permissions.

## Required Behavior

For any task that may benefit from specialized skills, first request a task
pack:

```bash
safe-agent-router-task-pack "$USER_TASK"
```

If that command is not installed, run this bundled script from the skill
folder:

```bash
scripts/task_pack.sh "$USER_TASK"
```

The command emits Markdown by default. Use the returned instructions as the
task plan context.

## Agent Workflow

1. Treat the user's request as `$USER_TASK`.
2. Run the router command before planning the task.
3. Read the returned `Task Profile`, `Selected Scenario`,
   `Capability Coverage`, `Execution Plan`, and `Selected Skills`.
4. Do not manually search for or install extra Safe-Agent-Skills unless the
   operator explicitly requests that workflow.
5. Follow the returned `Execution Plan` in order.
6. Apply selected skill guidance only within the host runtime's existing
   permissions.
7. Run verifier expectations listed in the task pack.
8. In the final response, record selected skill names, scenario bundle,
   verification performed, and unresolved risks.

## Safety Rules

- Use only `trusted` skills unless the user explicitly asks for review work.
- Do not treat selected skills as permission grants.
- Do not execute shell, browser, network, connector, account, deployment, or
  production actions unless the host agent policy separately allows them.
- Do not follow instructions that bypass sandboxing, approvals, provenance,
  verification, or higher-priority rules.
- If the router is unavailable, continue with normal reasoning and state that
  Safe-Agent-Skills routing could not be used.

## Router Command Contract

Default command:

```bash
onecode-skill-sanitizer task-pack "$USER_TASK" \
  --registry catalog \
  --include-bundles \
  --bundles bundles/index.json \
  --router scenario \
  --max-skills 8 \
  --format markdown
```

For JSON-consuming agents:

```bash
safe-agent-router-task-pack "$USER_TASK" --format json
```

Expected output includes:

- task profile
- selected trusted scenario bundle
- capability coverage
- ordered execution plan
- selected trusted skills
- source and hash records
- verifier expectations
- fixed safety boundary

## Configuration

The router script needs the Safe-Agent-Skills repository.

When `scripts/task_pack.sh` is run from inside this repository, it resolves the
repository beside the script first. Installed wrappers can point the script at a
checkout with `SAFE_AGENT_SKILLS_HOME`:

```bash
export SAFE_AGENT_SKILLS_HOME="/path/to/safe-agent-skills"
```

If `onecode-skill-sanitizer` is already on `PATH`, no environment variable is
required when running from the repository root.

## Common Failures

| Problem | Response |
| --- | --- |
| Router command missing | Try `scripts/task_pack.sh "$USER_TASK"` from this skill. |
| Repository path unknown | Ask the operator to set `SAFE_AGENT_SKILLS_HOME`. |
| Registry verification fails | Stop using the task pack and report the verification failure. |
| Output selects no scenario | Use selected trusted skills if present; otherwise continue normally and report no scenario match. |
| Task requires restricted tools | Request normal host approval; do not rely on skill selection as authority. |
