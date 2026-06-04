# Agent Task Pack

## Goal

`task-pack` is the universal skill-selection interface for agents.

It turns a natural-language task into a verified instruction pack that any
agent runtime can read as JSON or Markdown. The pack selects matching skills
from the sanitized catalog, includes their capability notes and safe workflow,
and repeats the runtime safety boundary before the agent starts work.

This is intentionally not a OneCode-only API. OneCode provides the validation
and cleaning chain, but the emitted task pack can be consumed by Codex, Claude
Code, Cursor, local agents, MCP hosts, CI workers, or custom orchestration
systems.

## Command

```bash
PYTHONPATH=src python3 -m onecode_skill_sanitizer task-pack \
  "review security risk in this package" \
  --registry catalog \
  --top 3 \
  --format json
```

Markdown output is useful when the host agent consumes plain text:

```bash
PYTHONPATH=src python3 -m onecode_skill_sanitizer task-pack \
  "polish this dashboard interface" \
  --registry catalog \
  --top 2 \
  --format markdown
```

## Output Contract

The JSON output includes:

- `task`: original task text
- `task_taxonomy`: inferred category, subcategory, intent, artifact type, and
  collection priority
- `registry_verification`: integrity and provenance verification result
- `skills`: selected skill records with status, source, taxonomy, hashes,
  capability description, safe workflow, expected output, verifier
  expectations, and failure handling
- `agent_instructions`: ready-to-paste runtime instructions for the host agent
- `safety_boundary`: the fixed rule that skills provide method, not permissions

## Selection Rule

Default mode selects only `trusted` skills.

```bash
PYTHONPATH=src python3 -m onecode_skill_sanitizer task-pack \
  "process a pdf report" \
  --registry catalog
```

Review mode can additionally include `review_required` skills:

```bash
PYTHONPATH=src python3 -m onecode_skill_sanitizer task-pack \
  "process a pdf report" \
  --registry catalog \
  --include-review-required
```

`quarantined`, `rejected`, and `disabled` skills are never selected by
`task-pack`, even in review mode.

## Safety Boundary

Before building a task pack, the command verifies the registry. If hashes do
not match or provenance is incomplete, task-pack generation is refused.

The generated instructions do not grant runtime permissions. The host agent
must still enforce its own:

- filesystem policy
- network policy
- shell and connector approval policy
- production-write approval policy
- verifier and evidence policy

The skill pack tells the agent how to approach the task. The host runtime
decides what the agent is allowed to do.

## Agent Integration Pattern

1. Receive the user task.
2. Run `task-pack` against the local or synced safe skill catalog.
3. Inject `agent_instructions` into the agent's planning context.
4. Execute only under the host runtime's existing permission policy.
5. Run the verifier expectations listed by the selected skills.
6. Record selected skill names, source URLs, and sanitized hashes in the final
   evidence or task report.

This makes the skill catalog a shared capability layer: different agents can
use the same cleaned instructions while keeping their own execution controls.
