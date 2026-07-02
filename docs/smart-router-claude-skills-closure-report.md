# Smart Router And Claude Skills Closure Report

Date: 2026-07-02

## Scope

This closure covers the audit follow-up for two goals:

- make skill selection and execution planning smarter, safer, and more
  complete;
- evaluate, rank, and absorb useful `claude-skills` community candidates into
  the Safe-Agent-Skills governance system.

The work keeps the existing safety boundary: skills provide method guidance
only. They do not grant filesystem, shell, network, connector, browser,
account, deployment, or production permissions.

## Router Closure

Completed router improvements:

- Chinese and typo-normalized task phrasing now routes skill-library,
  automatic recommendation, and task orchestration requests to
  `skill-router-quality-review`.
- Ambiguous `report` / `报告` wording no longer over-routes to data analysis
  without supporting data-analysis signals.
- Scenario output includes selection quality, execution roles, acceptance
  criteria, and a completion contract.
- Pipeline stages include a gate evidence template with `status`, `evidence`,
  `failed_checks`, `unresolved_assumptions`, and `residual_risks`.
- Required task-profile capabilities are promoted for the current route even
  when a reusable bundle marks the capability optional. This prevents critical
  checks such as `ci_check` from being dropped by `max-skills`.
- `scripts/verify.sh` falls back from `rg` to `grep -RInE` when ripgrep is not
  installed.

Current representative route:

```text
task: 优化技能库的自动推荐和任务编排能力
selected_scenario: skill-router-quality-review
coverage: skill_selection_quality, bundle_quality, routing_contract,
output_schema_eval, regression_test, failure_synthesis, ci_check,
supply_chain_review
selection_quality: high
```

## Security Closure

Completed audit hardening:

- `skill.json` manifests carry `hashes.manifest_sha256`.
- `verify` detects manifest tampering, including policy or `allowed_tools`
  changes.
- `schema-check` rejects unbounded policy scopes and permission-like tool
  values.
- Scanner bypass coverage now includes:
  - variable-indirected destructive shell commands;
  - Python `eval(compile(...))`;
  - Chinese-language secret exfiltration intent;
  - SSH key copying through `scp`;
  - netcat shell execution through `nc -e`;
  - PowerShell encoded commands;
  - JavaScript `fetch(...)` followed by dynamic execution through `eval(...)`.

The scanner remains a deterministic preflight guardrail, not a complete
malware detector or a replacement for host runtime sandboxing.

## Claude Skills Closure

Current `claude-skills` evaluation state:

```text
canonical candidates: 336
converted or covered by trusted local skills: 336
remaining reference-only candidates: 0
missing drafts: 0
author_local_skill backlog: 0
merge_existing backlog: 0
invalid converted mappings: 0
```

The former 283 reference-only items are now covered by nine trusted local
category-cluster skills added in `batch-029-claude-skills-backlog-clusters`.
They are mapped as converted coverage in `docs/claude-skills-candidate-map.json`
without copying upstream bodies. They were not promoted as 283 separate default
runtime skills because one or more of these conditions applied:

- lower current priority, mostly P3;
- persona-like or broad advisory templates rather than concrete reusable
  execution guidance;
- partial overlap with existing trusted local skills;
- no current project demand strong enough to justify default routing;
- upstream content cannot be copied, installed, executed, or trusted directly;
- connector-aware or runtime-dependent assumptions require separate host
  adapter review.

Detailed grouping, category counts, cluster mappings, and future dedicated-skill
promotion criteria are tracked in
[Claude Skills Reference-Only Backlog](claude-skills-reference-only-backlog.md).

Promotion rule:

```text
reference-only candidate
  -> local OneCode-authored rewrite
  -> scan
  -> schema validation
  -> manifest sealing
  -> serial approval
  -> registry verify
  -> trusted catalog inclusion
```

## Current Catalog Baseline

```text
catalog skills: 161
trusted skills: 155
scenario bundles: 14 trusted
overlap groups: 7
top-level categories: 15 / 15
tampered skills: 0
unknown provenance records: 0
```

## Local Installation And Update Behavior

The local `safe-agent-router` installation is a single entry skill plus a
wrapper command. The installed wrapper sets `SAFE_AGENT_SKILLS_HOME` to this
repository path, then runs the router against the live repository catalog and
source code:

```text
SAFE_AGENT_SKILLS_HOME=/path/to/safe-agent-skills
PYTHONPATH=$SAFE_AGENT_SKILLS_HOME/src
python3 -m onecode_skill_sanitizer task-pack ...
```

Implication:

- If this same local repository path is updated, the installed router can use
  the updated catalog, bundles, router code, and trusted skills without
  reinstalling every skill.
- If only the online repository is updated, the local computer must first pull
  or sync those changes into this repository checkout.
- Reinstall `safe-agent-router` only when the integration skill files or wrapper
  scripts themselves change, or when the repository path changes.
- Host agents may need a new session to reload the copied `SKILL.md`
  description, but the task-pack command reads the live repository through
  `SAFE_AGENT_SKILLS_HOME`.

## Verification

Fresh verification command:

```bash
bash scripts/verify.sh
```

Observed result:

```text
116 unittest tests passed
compileall passed
maintain-check passed
reference-check passed
router-eval passed
schema-check passed
smart smoke passed
JSON checks passed
```

Additional checks:

```text
git diff --check: passed
verify --registry catalog: status ok, 161 skills, 155 trusted, 0 tampered,
0 unknown provenance records
claude-skills-bulk-assess: 336 already_converted
```

## Residual Risks

- No live upstream synchronization was run in this closure; the result is based
  on the current local candidate map and draft pool.
- External `claude-skills` content remains metadata-only and must not be
  executed or trusted directly.
- The scanner is still regex and structure based. Deeper AST or parser-backed
  detection remains future hardening work.
- Trusted skills are method guidance only. Runtime permissions still belong to
  the host agent and operator approval layer.
