# Agent Task Pack

## Goal

`smart` is the recommended default skill-selection interface for agents.
`task-pack` remains the lower-level compatibility interface for hosts that need
the older simple or scenario-only output shape.

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
PYTHONPATH=src python3 -m onecode_skill_sanitizer smart \
  "review security risk in this package" \
  --registry catalog \
  --format json
```

Markdown output is useful when the host agent consumes plain text:

```bash
PYTHONPATH=src python3 -m onecode_skill_sanitizer smart \
  "polish this dashboard interface" \
  --registry catalog \
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
- `bundles`: optional trusted scenario bundles when `smart` or
  `--include-bundles` is used
- `router`: optional router metadata when `smart`, `--router scenario`, or
  `--router mesh` is used
- `task_profile`: optional deterministic task profile for smart, scenario, or
  mesh routing
- `selected_scenario`: optional best matching trusted scenario bundle
- `coverage`: optional capability coverage records for the selected scenario
  with `covered`, `missing`, or `omitted_by_limit` status. `omitted_by_limit`
  means the preferred trusted skill exists but was left out of the current
  `max-skills` execution pack.
- `execution_plan`: optional ordered skill execution guidance
- `selection_explanations`: optional reasons for selected bundles and skills
- `selection_trace`: optional machine-readable audit trail showing task
  profiling, scenario selection, candidate count, selected/pruned skills,
  required skill protection, capability coverage, and selection quality
- `execution_graph`: optional mesh DAG with `stage`, `gate`,
  `parallel_group`, and `stage_order` edges when `smart` or `--router mesh` is
  used
- `pipeline_plan`: optional method-only stage contract when `smart`,
  `--router scenario`, or `--router mesh` is used
- `invariant_capabilities`: optional capability mapping from user invariants
- `pruned_skills`: optional overlap-pruned skill names
- `agent_instructions`: ready-to-paste runtime instructions for the host agent
- `safety_boundary`: the fixed rule that skills provide method, not permissions

## Selection Rule

Default mode selects only `trusted` skills.

```bash
PYTHONPATH=src python3 -m onecode_skill_sanitizer smart \
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

`quarantined`, `rejected`, and `disabled` skills are never selected by default.
Review-required skills are available only through explicit review-mode
`task-pack` commands.

## Bundle-Aware Output

Use `smart` when the host agent should receive both individual skill guidance
and matching scenario playbooks:

```bash
PYTHONPATH=src python3 -m onecode_skill_sanitizer smart \
  "design a RAG document agent with vector retrieval and citation checks" \
  --registry catalog \
  --bundles bundles/index.json \
  --format json
```

Only `trusted` bundles are selected, and trusted bundles must reference only
existing `trusted` skills. Use `maintain-check` before publishing bundle
changes.

## Scenario Router

Use `--router scenario` when an older host integration needs task-aware skill
composition but has not adopted mesh router fields.

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
- `pipeline_plan`
- `selection_explanations`

The router is deterministic. It does not call an external model, does not
execute selected skills, and does not grant runtime permissions. It chooses a
trusted scenario, maps required capabilities to trusted skills, and emits an
ordered plan that the host agent can follow under its own permission policy.

## Pipeline Plan

Scenario and smart router task packs include `pipeline_plan`, a method-only
stage contract for host agents. Hosts can use it to decide what to do first,
what evidence to collect before moving to the next stage, and which actions
require operator or host-runtime approval.

The field does not grant permissions. Dependency installation, shell commands,
browser automation, network access, MCP/proxy startup, account or API-key use,
file upload, media rendering, paid provider calls, and destructive filesystem
or git actions remain controlled by the host runtime and operator policy.

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
overlap-pruned skill list. It also includes `selection_trace` so host agents
and maintainers can inspect why skills were selected, omitted, or pruned. It
remains deterministic and permission-neutral.

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
2. Run `safe-agent-router-task-pack` or `smart` against the local or synced
   safe skill catalog.
3. Use `task-pack --router scenario` only for older integrations that cannot
   consume mesh fields yet.
4. Confirm selected scenario, capability coverage, execution graph, pipeline
   plan, and verifier expectations before planning.
5. Inject `agent_instructions` into the agent's planning context.
6. Execute only under the host runtime's existing permission policy.
7. Run the verifier expectations listed by the selected skills.
8. Record selected skill names, source URLs, and sanitized hashes in the final
   evidence or task report.

This makes the skill catalog a shared capability layer: different agents can
use the same cleaned instructions while keeping their own execution controls.
