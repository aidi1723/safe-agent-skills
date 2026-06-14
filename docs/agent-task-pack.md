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
- `bundles`: optional trusted scenario bundles when `--include-bundles` is used
- `router`: optional router metadata when `--router scenario` is used
- `task_profile`: optional deterministic task profile for scenario routing
- `selected_scenario`: optional best matching trusted scenario bundle
- `coverage`: optional capability coverage records for the selected scenario
- `execution_plan`: optional ordered skill execution guidance
- `selection_explanations`: optional reasons for selected bundles and skills
- `execution_graph`: optional mesh DAG with `stage`, `gate`,
  `parallel_group`, and `stage_order` edges when `smart` or `--router mesh` is
  used
- `invariant_capabilities`: optional capability mapping from user invariants
- `pruned_skills`: optional overlap-pruned skill names
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

## Bundle-Aware Output

Use `--include-bundles` when the host agent should receive both individual
skill guidance and matching scenario playbooks:

```bash
PYTHONPATH=src python3 -m onecode_skill_sanitizer task-pack \
  "design a RAG document agent with vector retrieval and citation checks" \
  --registry catalog \
  --top 5 \
  --include-bundles \
  --bundles bundles/index.json \
  --format json
```

Only `trusted` bundles are emitted, and trusted bundles must reference only
existing `trusted` skills. Use `maintain-check` before publishing bundle
changes.

## Scenario Router

Use `--router scenario` when the host agent should receive a task-aware skill
composition rather than a simple match-score list.

```bash
PYTHONPATH=src python3 -m onecode_skill_sanitizer task-pack \
  "build a product website and prepare launch checks" \
  --registry catalog \
  --include-bundles \
  --bundles bundles/index.json \
  --router scenario \
  --max-skills 8 \
  --format json
```

Scenario router output adds:

- `router`
- `task_profile`
- `selected_scenario`
- `coverage`
- `execution_plan`
- `selection_explanations`

The router is deterministic. It does not call an external model, does not
execute selected skills, and does not grant runtime permissions. It chooses a
trusted scenario, maps required capabilities to trusted skills, and emits an
ordered plan that the host agent can follow under its own permission policy.

## Smart Router

Use `smart` when the operator wants the simplest default entry. It enables the
mesh router, trusted scenario bundles, overlap groups, and optional invariant
mapping without requiring the operator to choose skills manually.

```bash
PYTHONPATH=src python3 -m onecode_skill_sanitizer smart \
  "build a landing page and prepare launch checks" \
  --invariants "不能泄露密钥；公开文案必须合规；必须响应式验证" \
  --format json
```

The same mesh router is available through `task-pack` for advanced integrations:

```bash
PYTHONPATH=src python3 -m onecode_skill_sanitizer task-pack \
  "build a landing page and prepare launch checks" \
  --registry catalog \
  --include-bundles \
  --bundles bundles/index.json \
  --router mesh \
  --invariants "不能泄露密钥；公开文案必须合规；必须响应式验证" \
  --max-skills 8 \
  --format json
```

Mesh output adds an execution graph, invariant capability coverage, and an
overlap-pruned skill list. It remains deterministic and permission-neutral.

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
3. Optionally include trusted scenario bundles with `--include-bundles`.
4. Use `--router scenario` when the task should be composed from a known
   scenario, required capabilities, and an ordered skill plan.
5. Inject `agent_instructions` into the agent's planning context.
6. Execute only under the host runtime's existing permission policy.
7. Run the verifier expectations listed by the selected skills.
8. Record selected skill names, source URLs, and sanitized hashes in the final
   evidence or task report.

This makes the skill catalog a shared capability layer: different agents can
use the same cleaned instructions while keeping their own execution controls.
