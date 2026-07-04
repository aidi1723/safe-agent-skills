# Smart Router And Claude Skills Closure

Date: 2026-07-02

This update closes the audit follow-up for smarter skill selection, execution
planning, scanner hardening, and the `claude-skills` community candidate
absorption pass.

## What Changed

- Added task-profile capability promotion in the smart router. If the current
  task explicitly requires a capability, that capability is kept for the route
  even when the reusable scenario bundle marks it optional. This prevents
  important checks such as `ci_check` from being dropped by `max-skills`.
- Improved Chinese and typo-normalized routing for skill-library, automatic
  recommendation, and task orchestration requests so they select
  `skill-router-quality-review`.
- Added gate evidence fields to pipeline plans: `status`, `evidence`,
  `failed_checks`, `unresolved_assumptions`, and `residual_risks`.
- Added acceptance criteria and completion contracts to task-pack output so host
  agents have clearer handoff and verification obligations.
- Hardened scanner coverage for JavaScript `fetch(...)` followed by dynamic
  execution through `eval(...)`, in addition to the earlier scanner bypass
  samples.
- Added `rg` to `grep -RInE` fallback behavior in `scripts/verify.sh`.
- Sorted and reconciled the `claude-skills` candidate map by evaluation
  priority.
- Added a closure report at
  `docs/smart-router-claude-skills-closure-report.md`.

## Claude Skills Result

The current `claude-skills` evaluation state is:

```text
canonical candidates: 336
converted or covered by trusted local skills: 336
remaining reference-only candidates: 0
missing drafts: 0
author_local_skill backlog: 0
merge_existing backlog: 0
invalid converted mappings: 0
```

The former 283 reference-only candidates are covered by nine trusted local
category-cluster skills from `batch-029-claude-skills-backlog-clusters`.
Candidate-map conversion means covered by local OneCode-authored guidance; it
does not mean upstream skill bodies were copied or executed.

## Baseline At Closure

```text
catalog skills: 161
trusted skills: 155
scenario bundles: 14 trusted
overlap groups: 7
top-level categories: 15 / 15
tampered skills: 0
unknown provenance records: 0
```

## Local Router Update Behavior

The installed `safe-agent-router` is a single entry skill plus a wrapper
command. The wrapper points `SAFE_AGENT_SKILLS_HOME` at this repository and
reads the live `catalog/`, `bundles/`, and `src/` content.

Implication:

- updating this repository checkout is enough for the installed router to use
  the updated catalog and router logic;
- reinstalling the router skill is only needed if the integration skill files,
  wrapper scripts, or repository path change;
- host agents may still need a fresh session to reload copied skill
  descriptions.

## Verification

Fresh verification:

```text
bash scripts/verify.sh: passed
116 unittest tests passed
git diff --check: passed
verify --registry catalog: status ok
claude-skills-bulk-assess: 336 already_converted
```

## Safety Boundary

External `claude-skills` content remains metadata-only. It is not installed,
copied, executed, or trusted directly. Trusted catalog skills remain method
guidance only; runtime permissions stay with the host agent and operator
approval layer.
