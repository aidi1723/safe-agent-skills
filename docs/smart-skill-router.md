# Smart Skill Router

`smart` is the simple default entry for agents and operators who do not want to
manually choose, combine, or order skills.

The command name is a convenience label. Current selection is deterministic
keyword, taxonomy, scenario-signal, invariant, and overlap-group routing; it is
not an LLM planner and does not infer capability beyond recorded catalog
metadata.

It builds a verified task pack from:

- the trusted skill catalog
- trusted scenario bundles
- deterministic task intent and capability matching
- optional natural-language invariants
- overlap-group pruning
- a deterministic mesh execution graph

It does not call an external model, install skills, execute tools, or grant
runtime permissions.

## Design References

`smart` adopts the practical shape of modern open tool orchestration without
copying their runtime trust model:

- AnyTool-style routing: retrieve and trim the relevant tools before exposing a
  compact tool pack to an agent (`https://github.com/HKUDS/AnyTool`).
- MCP aggregator-style simplicity: keep one operator-facing entry while
  hiding server or skill fragmentation behind a unified interface
  (`https://github.com/punkpeye/awesome-mcp-servers`,
  `https://github.com/1mcp-app/agent`,
  `https://github.com/askbudi/roundtable`).

Unlike open-ended MCP aggregation, `smart` only routes skills already present
in this repository's verified `trusted` catalog. External MCP servers or
community tools must still pass provenance capture, sanitization, approval,
and registry verification before selection.

## Quick Start

```bash
PYTHONPATH=src python3 -m onecode_skill_sanitizer smart \
  "build a landing page and prepare launch checks" \
  --invariants "不能泄露密钥；公开文案必须合规；必须响应式验证" \
  --max-skills 10
```

Defaults:

```text
registry: catalog
bundles: bundles/index.json
strategy: balanced
max skills: 8
format: json
```

`max-skills` is a target cap. If the selected scenario and invariants require
more skills to cover mandatory gates, `smart` keeps those required skills
instead of dropping a safety, verification, or release capability.

## Low-Confidence Tasks

`smart` and `task-pack --router scenario` do not force a scenario bundle when
the task text does not contain a trusted scenario signal. In that case:

- `task_profile.task_type` is `general`
- `selected_scenario.id` is empty
- `bundle_count` is `0`
- only directly matched trusted skills are returned

This is intentional. For vague or unsupported repository-maintenance tasks, the
safer behavior is to return a smaller pack than to attach an unrelated workflow
such as website launch or public publishing.

Markdown output:

```bash
PYTHONPATH=src python3 -m onecode_skill_sanitizer smart \
  "review this package before publishing" \
  --strategy deep \
  --format markdown
```

## Strategies

| Strategy | Behavior |
| --- | --- |
| `fast` | Keeps required gates and directly useful non-verification matches; trims optional verification depth. |
| `balanced` | Keeps required gates plus task-matched skills up to `max-skills`. |
| `deep` | Prioritizes optional verification and review skills before other optional matches and may exceed the normal cap up to the deep limit. |

## Invariants

Use `--invariants` to describe hard boundaries in natural language:

```bash
--invariants "绝对不泄露 API 密钥"
--invariants "公开文案必须合规"
--invariants "前端必须做响应式验证"
```

The current deterministic mapper recognizes these capability families:

- `secret_redaction`
- `claims_compliance`
- `responsive_check`
- `source_check`
- `browser_verification`

Each capability maps to existing trusted skills. If no trusted skill can cover
an invariant, the output marks the capability as `missing`.

## Output

`smart` emits the normal task-pack fields plus:

- `router.mode`: `deterministic_mesh_router`
- `router.strategy`
- `router.strategy_profile`
- `invariant_capabilities`
- `coverage`
- `execution_plan`
- `execution_graph`
- `pipeline_plan`
- `selection_explanations`
- `pruned_skills`

The execution graph is a deterministic DAG with node-level stage gates and
parallel-group hints:

```text
preflight -> source -> planning -> review -> execution -> verification
```

Each node includes `stage`, `gate`, and `parallel_group`. Edges use
`type: "stage_order"` to show ordering between stages; skills in the same
parallel group can be considered independently by a host runtime unless its
own policy requires stricter sequencing.

The graph is guidance for the host agent. It does not execute anything by
itself.

`pipeline_plan` is a method-only orchestration contract layered on top of the
selected trusted skills. It groups selected skills into stages such as
`preflight`, `source`, `planning`, `production`, `review`, `verification`, and
`handoff`; each stage includes inputs, outputs, a gate condition, verification
notes, and failure handling guidance. The plan is advisory: it does not execute
tools or grant runtime permissions.

## When To Use

Use `smart` as the default command for normal tasks:

- website, landing page, dashboard, or launch checks
- code review or release readiness
- document-to-knowledge-base conversion
- RAG planning
- skill router, skill catalog, or automatic skill-composition review
- data analysis
- commerce listing or public content work

Use `task-pack --router scenario` when you need the older scenario-only output
shape for a host integration that has not adopted mesh fields yet.
