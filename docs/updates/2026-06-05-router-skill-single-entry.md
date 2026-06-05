# Update Statement: Single-Entry Router Skill

Date: 2026-06-05

Repository:

```text
https://github.com/aidi1723/safe-agent-skills
```

## Summary

This update clarifies the recommended integration model for
`Safe-Agent-Skills`:

```text
install one router skill -> route every non-trivial task -> use the selected trusted task pack
```

Users do not need to manually install, choose, or combine every skill in the
catalog. A host agent only needs `safe-agent-router` as the entry skill. The
router reads the OneCode-verified registry, chooses the best trusted scenario
bundle and selected skills for the task, then returns a Markdown or JSON task
pack.

## What The Router Provides

For each routed task, the task pack includes:

- task profile
- selected trusted scenario bundle
- selected trusted skills
- capability coverage
- ordered execution plan
- verifier expectations
- source and hash records
- fixed safety boundary

This lets Claude, Codex, OpenClaw, Cursor, MCP hosts, local agents, CI workers,
and custom agents share the same trusted skill selection behavior without each
agent having to learn the whole catalog.

## User-Facing Rule

After installing `safe-agent-router`, users do not need to:

- copy every skill into their agent one by one
- decide which category or bundle fits each task
- manually compose website, RAG, data, security, office, or publishing
  workflows
- inspect every community source before each run
- teach each agent the full catalog

The router performs task-to-skill matching on demand.

## Installation

Codex:

```bash
integrations/skills/safe-agent-router/scripts/install.sh ~/.codex/skills
```

Claude Code:

```bash
integrations/skills/safe-agent-router/scripts/install.sh ~/.claude/skills
```

Custom agents can copy:

```text
integrations/skills/safe-agent-router/
```

Then expose this read-only command:

```bash
safe-agent-router-task-pack "$TASK"
```

## Safety Boundary

The router selects trusted guidance. It does not grant runtime authority.

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

## Verification Evidence

Release gate:

```bash
bash scripts/verify.sh
PYTHONPATH=src python3 -m onecode_skill_sanitizer verify --registry catalog
PYTHONPATH=src python3 -m onecode_skill_sanitizer maintain-check --registry catalog --bundles bundles/index.json
git diff --check
```

Expected baseline:

```text
tests: 34 passed
skill_count: 75
trusted_count: 70
tampered_count: 0
unknown_provenance_count: 0
trusted_bundle_count: 9
bundle issues: 0
```

## Files Updated

- `README.md`
- `docs/router-skill-integration.md`
- `integrations/skills/safe-agent-router/SKILL.md`
- `docs/updates/2026-06-05-router-skill-single-entry.md`
