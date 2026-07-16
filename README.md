# OneCode Skill Sanitizer

OneCode Skill Sanitizer is a standalone project for turning external or community skill material, local seed workflows, and reference-derived guidance into OneCode-governed skill instructions.

Its purpose is not to execute third-party skills directly. Its purpose is to preserve useful domain workflows while applying deterministic risk preflight checks, provenance records, review status, hash verification, and explicit execution boundaries. The scanner is a guardrail and review aid; it is not a complete malware detector or a substitute for host-runtime sandboxing.

The CLI can also be used independently of OneCode. Users can bring their own
`incoming/` skill folders, build a private or public `registry/`, approve their
own trusted skills, and generate JSON or Markdown task packs for any host
agent. See [Standalone Tool Open Source Statement](docs/standalone-tool-open-source.md).

## Maintenance Boundary

Maintain this repository as its own checkout, separate from any host runtime or
core agent repository. Future skill catalog, router, documentation,
verification, commit, and release work should happen from this standalone
repository checkout. See [Workspace Boundary](docs/workspace-boundary.md).

## Recommended Entry: Install One Router Skill

The recommended user-facing entry is `safe-agent-router`, published inside
this main repository:

```text
integrations/skills/safe-agent-router/
```

Users do not need to install or combine every catalog skill manually. Install
this one router skill, then let it select the right OneCode-verified trusted
skills and scenario bundle for each task.

中文项目发布文章：

> [社区 Skill 太多、太乱、还不安全？只安装一个可信路由 Skill 就够了](docs/blog-one-trusted-skill-router-2026-07-10.md)

文章从实际使用痛点出发，介绍单一可信入口、Skill 供应链治理、多意图
路由、场景组合、DAG 编排、验证数据和当前能力边界。

```bash
integrations/skills/safe-agent-router/scripts/install.sh ~/.codex/skills
```

For Claude Code:

```bash
integrations/skills/safe-agent-router/scripts/install.sh ~/.claude/skills
```

After installation:

```bash
safe-agent-router-task-pack "build a product website and prepare launch checks"
```

Current publishing decision: keep the router skill in this main repository as
the primary entry point, because it depends on the same `catalog/`, `bundles/`,
provenance records, trusted status, hash checks, and OneCode safety rules. See
[Router Skill Primary Entry](docs/router-skill-primary-entry.md).

## Open Source Statement

This project is a public-safe skill catalog and sanitizer for AI agents. It is
designed to turn scattered community skills into provenance-recorded,
policy-bounded, hash-verifiable, and maintainable `trusted` skill assets.

All published catalog skills have passed the current OneCode governance
workflow: provenance recording, deterministic static risk scanning, status
review, sanitized hash recording, and registry verification. Many community
entries are locally authored reference skills inspired by public projects, not
verbatim imports from those repositories. This makes the project safer and more
auditable than copying unverified prompts or agent instructions directly from
the open internet, but it should not be treated as a standalone security
sandbox.

Current public baseline:

- 172 total skills
- 166 trusted skills
- 23 trusted scenario bundles
- 7 status-backed trusted-only skill overlap groups
- 15 / 15 top-level categories covered
- at least 3 trusted skills in every top-level category
- 336 / 336 tracked `claude-skills` candidates covered by trusted local mappings
- 0 tampered skills
- 0 unknown provenance records

For a domain-oriented map of the catalog and example router commands, see
[Catalog Overview](docs/catalog-overview.md).

For the maintained entry point to architecture, operator guidance, catalog
authoring, and historical records, see the [Documentation Index](docs/index.md).

The latest structural baseline, verification evidence, and remaining
maintenance risks are recorded in the
[Structural Maintainability Closure Report](docs/structural-maintainability-closure-report-2026-07-11.md).

For the maintainer workflow for smarter skill selection, orchestration traces,
scenario contracts, and router regression tests, see
[Router Development Guide](docs/router-development.md).

For the current feature surface, category counts, and scenario bundles, see
[Feature Log](docs/feature-log.md).

See [Open Source Statement](docs/open-source-statement.md) for the full project
positioning and contribution stance.

Current status and chronological evidence are separated intentionally. Use the
[Feature Log](docs/feature-log.md) for maintained capabilities and the
[Historical Documentation Map](docs/history.md) for dated updates, batch notes,
plans, acceptance records, and closure reports.

## Core Position

Skills provide method.

OneCode provides boundary, execution control, verification, and evidence.

When used outside OneCode, the host agent or operating environment provides
that boundary. The sanitizer still records provenance, cleans risky
instructions, verifies hashes, and emits bounded task packs, but it does not
grant runtime permissions.

This project is designed to stay usable even when the host product changes.
It does not assume that every OneCode or AgentCore OS runtime already exposes
the same connector, vault, publishing, or sandbox APIs. Those integrations must
be bound through explicit adapters.

The sanitizer sits between untrusted skill sources and the OneCode skill registry:

```text
external skill
  -> source capture
  -> deterministic risk preflight scan
  -> instruction distillation
  -> policy rewrite or bounded local synthesis
  -> verifier binding
  -> evidence manifest
  -> quarantined registry entry
  -> approval
  -> trusted OneCode skill
```

## First Principle

No imported skill is trusted by default.

Every external skill starts in `quarantined` state. It can become `trusted` only after the sanitizer produces a manifest, a sanitization report, and a clean deterministic risk scan under OneCode policy.

`trusted` means the skill has passed the current OneCode safety validation and
review process. It does not mean the source is perfectly safe, and it does not
grant unrestricted runtime permissions:
connectors, filesystem access, network access, and production actions still
belong to the host runtime's approval and policy layer.

## What Is Preserved

- task scope
- useful domain workflow
- input and output expectations
- verification requirements
- failure handling guidance
- reference material
- safe tool suggestions
- concise examples

## What Is Removed

- direct destructive commands
- shell download-and-execute patterns
- requests to disable sandboxing, approval, or verification
- instructions to ignore higher-priority policies
- secrets, tokens, and private credentials
- broad filesystem access
- unbounded network access
- hidden persistence or self-modifying behavior
- long non-operational explanation
- conflicting or ambiguous execution instructions

## Local CLI

From this repository checkout, use:

```bash
PYTHONPATH=src python3 -m onecode_skill_sanitizer --help
```

Several router commands use repository assets such as `catalog/`,
`bundles/index.json`, `catalog/overlap-groups.json`, and
`external-references/index.json`. When running the CLI from outside this
checkout, set `SAFE_AGENT_SKILLS_HOME` so default asset paths resolve back to
the verified catalog:

```bash
export SAFE_AGENT_SKILLS_HOME=/path/to/safe-agent-skills
onecode-skill-sanitizer smart "审查整个项目，看是否还有需要优化和完善的地方"
```

Private registry workflows can still pass explicit local paths such as
`--registry ./registry`; those paths remain relative to the current command
location when they already exist or are being created by write commands.

```bash
onecode-skill-sanitizer scan ./incoming/pdf-skill
onecode-skill-sanitizer sanitize ./incoming/pdf-skill --out ./registry/pdf \
  --source-url https://github.com/example/skills/pdf \
  --source-usage source_import \
  --author example-team \
  --license MIT \
  --reference https://github.com/example/skills \
  --collected-by onecode-local
onecode-skill-sanitizer audit ./registry/pdf
onecode-skill-sanitizer approve ./registry/pdf
```

Every scan and sanitize report records provenance. `source.usage` records the
relationship to the cited source: `source_import` for imported content,
`reference_only` for external projects used only as inspiration or comparison,
and `local_authoring` for local seed workflows. Missing provenance values are
written as `unknown`, not omitted.

Batch registry workflow:

```bash
onecode-skill-sanitizer import ./incoming --registry ./registry \
  --collected-by onecode-local
onecode-skill-sanitizer list --registry ./registry
onecode-skill-sanitizer inspect office-pdf --registry ./registry
onecode-skill-sanitizer select "process a pdf report" --registry ./registry
onecode-skill-sanitizer task-pack "process a pdf report" --registry ./registry \
  --top 3 \
  --format json
onecode-skill-sanitizer verify --registry ./registry
onecode-skill-sanitizer maintain-check --registry ./registry --bundles ./bundles/index.json
onecode-skill-sanitizer reindex --registry ./registry
```

Review workflow:

```bash
onecode-skill-sanitizer approve ./registry/office/office-pdf
onecode-skill-sanitizer reject ./registry/security/unsafe-skill
onecode-skill-sanitizer disable ./registry/office/old-skill
```

`select` returns only `trusted` skills by default. Use
`--include-review-required` only for review work, not normal execution.

`smart` is the recommended Agent-facing interface. It verifies the registry,
selects matching trusted skills, loads their sanitized `SKILL.md` instructions,
and emits a JSON or Markdown instruction pack that any host Agent can place in
its planning context. The pack provides method, verifier expectations,
provenance, capability coverage, and a deterministic mesh execution graph. It
does not grant filesystem, network, connector, shell, or production permissions;
those remain controlled by the host runtime.

Schema v2 is now the default for `smart` and `task-pack`. It decomposes and
composes multiple trusted workflows, but remains method-only. It does not
execute selected skills or grant runtime permissions. This deterministic first
milestone is not an autonomous runtime and is not a semantic router yet.

### Router v3 Evaluation Status

Router v3 remains opt-in; Router v2 remains the default. The v3 evaluation
scope is the router entry plus exactly seven high-frequency candidates:
`codebase-explore-map`, `code-review-risk`, `code-test-regression`,
`execution-browser-check`, `research-source-check`, `design-ui-review`, and
`security-supply-chain-review`. The public CLI opt-in mechanism is
`--schema-version 3` on `smart` or `task-pack`; it does not change the v2
default. Deterministic selection is active. Semantic providers are
candidate-bounded and run in shadow only. Semantic influence is disabled
through the public CLI.

The validation split passes, but the one permitted `final_test` run failed
release acceptance (`final_acceptance_failed`). The separate
`task_evaluation_missing` blocker means that no real three-arm task evidence
was generated, so task-level acceptance is not established. Router v3 has not
passed final release acceptance.

Runtime examples are reviewed routing data. The isolated 120 held-out cases
are evaluator-only and must not be runtime inputs.
Skills are method guidance, not permission grants. Structural delivery for the
opt-in path is closed on `main`; see the
[v3 Closure Report](docs/high-frequency-intelligent-skill-selection-v3-closure-report-2026-07-16.md)
and the [Router Development Guide](docs/router-development.md) for cohort,
exact dependency-edge scoring, and evaluation boundaries.

```bash
onecode-skill-sanitizer smart "review this patch" \
  --schema-version 3 --format json
onecode-skill-sanitizer smart "构建官网，同时审计 skill 路由器，验证通过后发布更新" \
  --schema-version 2 --format json
onecode-skill-sanitizer smart "build a product website" \
  --schema-version 1 --format json
onecode-skill-sanitizer contract-check --registry catalog \
  --bundles bundles/index.json --scenario website-build-launch \
  --minimum-ratio 0.80
onecode-skill-sanitizer router-eval-v2 --eval evals/multi-intent-gold.json \
  --registry catalog --bundles bundles/index.json
```

Explicit Schema v1 preserves the frozen, independently executed v1 routing
behavior; it is not the same selection as projecting a v2 result. Schema v2
separately reports `compatibility_loss`, and its `to_legacy_v1` projection keeps
one primary scenario while dropping secondary intents, secondary scenarios, and
cross-scenario dependency edges. See [Smart Skill Router](docs/smart-skill-router.md),
[Agent Task Pack](docs/agent-task-pack.md), and
[Hybrid Router v2 First Milestone Report](docs/hybrid-router-v2-first-milestone-report.md).

The `smart` name is a convenience label: selection is deterministic, non-LLM
routing over trusted catalog metadata, scenario signals, overlap groups, and
invariant hints:

```bash
onecode-skill-sanitizer smart \
  "build a landing page and prepare launch checks" \
  --invariants "不能泄露密钥；公开文案必须合规；必须响应式验证"
```

Schema v1 `smart` returns the legacy task-pack structure plus a mesh execution
graph with stage gates and parallel-group hints, invariant capability coverage,
and an overlap-pruned skill list. See
[Smart Skill Router](docs/smart-skill-router.md).

For vague or unsupported repository-maintenance tasks, `smart` is conservative:
if the task does not match a trusted scenario signal, it leaves
`selected_scenario.id` empty and returns only directly matched trusted skills.

`task-pack` remains available as a lower-level compatibility interface. Use
`task-pack --include-bundles` when an integration needs matching trusted
scenario bundles without the mesh router. Use `task-pack --router scenario`
only when a host integration has not adopted mesh fields yet:

```bash
onecode-skill-sanitizer task-pack "build a product website and prepare launch checks" \
  --registry ./registry \
  --include-bundles \
  --bundles ./bundles/index.json \
  --router scenario \
  --max-skills 8 \
  --format json
```

`--router scenario` adds a task profile, selected scenario, capability
coverage, ordered execution plan, and selection explanations. It still does
not grant filesystem, network, connector, shell, browser, or production
permissions.

Scenario bundles in `bundles/` combine multiple trusted skills for common
workflows such as website launch, code review hardening, document-to-knowledge
base, RAG agent design, data analysis, open source release, and commerce
listing growth.

Functional overlap between trusted skills is recorded in
[`catalog/overlap-groups.json`](catalog/overlap-groups.json) and explained in
[Skill Overlap Groups](docs/skill-overlap-groups.md). This is a selection hint
layer for routers and operators, not a deletion or merge list. Each overlap
group now declares `status: trusted`, and `maintain-check` rejects missing or
non-trusted group status.

These skills and bundles are agent-compatible by design. Claude, Codex,
OpenClaw, Cursor, local agents, MCP hosts, CI workers, and custom agent
systems can consume the same sanitized Markdown or JSON task packs. The safety
rule stays the same across all hosts: skill guidance is method, not execution
authority. See [Agent-Compatible Skill Bundles](docs/agent-compatible-skill-bundles.md).

Agents can also install the single router skill:
[Safe Agent Router Skill Integration](docs/router-skill-integration.md).
After installing `safe-agent-router`, a host agent does not need the operator
to manually choose, combine, or install every other catalog skill. The router
selects the best trusted skills and scenario bundle for the task, then returns
a task pack with the execution order, verifier expectations, source records,
and safety boundary.

This is the recommended default integration model:

```text
install one skill -> route every non-trivial task -> use selected trusted skill pack
```

The first MVP can also be exposed through OneCode:

```bash
onecode skills sanitize --source ./incoming/pdf-skill --out ./skills/pdf
onecode skills audit ./skills/pdf
onecode skills approve pdf
```

## Project Docs

- [Documentation Index](docs/index.md)
- [Architecture](docs/architecture.md)
- [Operator Guide](docs/operator-guide.md)
- [Maintenance Guide](docs/maintenance-guide.md)
- [Catalog Overview](docs/catalog-overview.md)
- [Historical Documentation Map](docs/history.md)

## Verify

```bash
python3 -m pip install -e ".[dev]"
bash scripts/verify.sh
```

`jsonschema` is required by the verification suite. `bash scripts/verify.sh`
is the safe routine verification command and skips `final_test` by default.
`ONECODE_RUN_ROUTER_V3_FINAL_TEST=1` is reserved for a future fresh, explicitly
authorized one-shot release evaluation. Do not set it for the current rollout;
its permitted run is exhausted and failed. Any other flag value fails with
exit status 2.
