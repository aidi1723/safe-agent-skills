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
- deterministic alias expansion for common Chinese and English task phrasing
- optional natural-language invariants
- overlap-group pruning
- a deterministic mesh execution graph

It does not call an external model, install skills, execute tools, or grant
runtime permissions.

## Hybrid Router v2 First Milestone

Schema v2 is the default. It decomposes and composes multiple trusted
workflows, but remains method-only. It does not execute selected skills or
grant runtime permissions. The first milestone is deterministic: it is not an
autonomous runtime and is not a semantic router yet.

```bash
PYTHONPATH=src python3 -m onecode_skill_sanitizer smart \
  "构建官网，同时审计 skill 路由器，验证通过后发布更新" \
  --schema-version 2 --format json

PYTHONPATH=src python3 -m onecode_skill_sanitizer smart \
  "build a product website" --schema-version 1 --format json
```

Schema v2 fields are:

- `schema_version`, `generated_at`, `route_id`, `routing_mode`, and
  `routing_status` for the envelope and route identity.
- `provider` with `requested`, `used`, and `fallback_reason`. The first
  milestone uses `none`/`none` and the explicit fallback placeholder
  `semantic_provider_not_enabled_in_first_milestone`.
- `normalized_task` with `raw`, `current`, `history`, `stale`, and
  `stale_policy`.
- `intent_graph` with `intents` and `unresolved_dependencies`. Every intent has
  `id`, `summary`, `task_type`, `required_artifacts`, `risk_flags`,
  `depends_on`, `source`, and `confidence`.
- `scenario_candidates`, `selected_scenarios`, `uncovered_intents`, and
  `selected_skills` for deterministic retrieval and trusted composition.
- `capability_resolution`, `execution_graph`, and `host_execution_protocol`
  for method ordering, graph state, and the fixed host-owned runtime boundary.
- `routing_metrics`, `registry_verification`, and `compatibility` for
  diagnostics, registry evidence, and explicit v2-to-v1 projection loss
  reporting.

`routing_status` has three meanings:

```json
{"routing_status":"complete","uncovered_intents":[],"execution_graph":{"status":"ready","acyclic":true}}
{"routing_status":"incomplete","uncovered_intents":["i1"],"execution_graph":{"status":"ready","acyclic":true}}
{"routing_status":"blocked","uncovered_intents":[],"execution_graph":{"status":"blocked","acyclic":false,"reason_codes":["dependency_cycle"]}}
```

Complete means every intent has a trusted scenario and required capability
coverage. Incomplete means the method pack is partial, such as a vague or
unsupported intent. Blocked means compilation cannot safely produce a ready
graph; cyclic intent dependencies must be blocked, never silently reordered.

`route_id` is a stable SHA-256 identity over canonical routing inputs and
catalog assets. Secret-like assignments and bearer values are redacted before
hashing, but operators must still avoid placing credentials or unnecessary
private text in tasks. Markdown output escapes headings, lists, links, HTML,
quotes, code fences, and newlines from task-controlled values so supplied text
cannot forge trusted sections.

Schema v1 remains available as the frozen, independently executed v1 router;
its selection is not defined as a projection of the v2 route. Schema v2
separately reports migration information through `compatibility_loss`. The
programmatic `to_legacy_v1` projection keeps one primary v2 scenario and reports
`multi_intent_dropped`, `scenarios_dropped`, and
`cross_scenario_edges_dropped`.

## Router v3 Opt-In Cohort Path

Router v3 remains opt-in; Router v2 remains the default. Request v3 only for
the fixed high-frequency cohort path:

```bash
PYTHONPATH=src python3 -m onecode_skill_sanitizer smart \
  "review this patch" --schema-version 3 --format json
```

v3 adds a need gate, reviewed routing-example retrieval, seven-skill candidate
bounds, marginal composition with real dependency edges, and a strict
task-pack v3 envelope. Deterministic selection is active. Semantic providers
are candidate-bounded and run in shadow only; semantic influence is disabled
through the public CLI. Skills remain method guidance, not permission grants.

The validation split passes. Final-test release acceptance and three-arm task
oracle evidence are not established. Prefer the
[Agent Task Pack](agent-task-pack.md) v3 section and the
[v3 Closure Report](high-frequency-intelligent-skill-selection-v3-closure-report-2026-07-16.md)
for current gate status.

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
When the task profile itself explicitly requires a capability, that capability
is promoted for the current route even if the reusable scenario bundle marks it
optional; this prevents important checks such as CI review from being reported
as merely omitted by the skill limit.

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

Under Schema v2, the equivalent safe state is `routing_status: incomplete`
with the affected IDs in `uncovered_intents`; it is not a successful complete
route.

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

## Alias Expansion

Before scenario scoring, task text is normalized with a small audited alias
table. This catches common operator phrasing such as `技能库`, `技能选择`,
`自动推荐`, `任务编排`, `更聪明`, and typo variants such as `sikll`.
Alias expansion is deterministic and recorded in code; it is not semantic LLM
inference.

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
- `selection_trace`
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

`selection_trace` is the maintainer-facing audit trail for smarter routing. It
records the compact task profile, selected scenario, candidate count, selected
and required skills, overlap-pruned skills, capability coverage summary,
low-confidence reasons, and one candidate record per considered skill. Use it
when tuning aliases, scenario signals, capability mappings, overlap groups, or
router evals.

`pipeline_plan` is a method-only orchestration contract layered on top of the
selected trusted skills. It groups selected skills into stages such as
`preflight`, `source`, `planning`, `production`, `review`, `verification`, and
`handoff`; each stage includes inputs, outputs, a gate condition, verification
notes, failure handling guidance, and a gate evidence template. The evidence
template asks host agents to record `status`, `evidence`, `failed_checks`,
`unresolved_assumptions`, and `residual_risks` before treating a stage as
complete. The plan is advisory: it does not execute tools or grant runtime
permissions.

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

See [Router Development Guide](router-development.md) for the maintainer
workflow for extending scenarios, contracts, traces, and regression tests.
