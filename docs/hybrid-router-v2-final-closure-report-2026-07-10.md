# Hybrid Router v2 Final Closure Report

Date: 2026-07-10

## Closure Decision

The Hybrid Router v2 first milestone is closed and merged into `main` at
commit `d07f8a6`.

The delivered system is a method-only hybrid Skill routing and orchestration
compiler. It can select trusted Skills, decompose multi-intent tasks, compose
multiple trusted scenario bundles, compile a dependency-aware execution DAG,
emit verification and completion gates, and identify actions that require host
runtime handling. It does not execute Skills, grant permissions, or replace the
host runtime.

The structural delivery milestone is **complete**. The production router
quality gate is **not complete** and must not be represented as passed.

## Delivered Scope

- Schema v2 is the default for `smart` and `task-pack`.
- Deterministic multi-intent decomposition and multi-scenario composition.
- Trusted-only scenario and Skill retrieval.
- Global DAG compilation with verification, completion, dependency, and
  fail-closed gates.
- Contract v2 metadata and coverage validation.
- Host-action flags derived from Contract v2 approval classes.
- Preserved Skill Contracts in generated task packs; missing contracts are not
  synthesized.
- Stable, secret-redacted route identities.
- Controlled JSON and Markdown errors for malformed routing assets and empty
  tasks.
- Frozen, independently executed Schema v1 compatibility behavior.
- A curated 100-case multi-intent evaluation corpus and evaluator.
- Operator, architecture, development, migration, readiness, and milestone
  documentation.

## Final Verification Evidence

Verification was rerun on `main` after the fast-forward merge.

| Verification | Result |
| --- | --- |
| Ruff | Passed |
| `bash scripts/verify.sh` | Passed |
| Unit and integration tests | 321 passed, 0 failed |
| Independent final code review | 0 Critical, 0 Important |
| Git worktree | Clean after merge |
| Feature branch and temporary worktree | Removed after verification |

The mandatory compound task was:

```text
构建官网，同时审计 skill 路由器，验证通过后发布更新
```

Its final v2 task pack selected:

- `website-build-launch`
- `skill-router-quality-review`
- `open-source-release`

The compiled execution graph was ready and acyclic with 30 nodes, 31 edges,
and 7 host-action nodes. Configured overlap groups were validated and recorded
as `validated_not_applied`, because v2 overlap pruning remains outside this
milestone.

For those three scenarios, Contract v2 coverage was 24 of 26 referenced Skills
(`92.31%`), above the required `80%` gate. Across the eight core scenarios, the
persisted milestone baseline remains 39 of 48 (`81.25%`).

## Objective Capability Assessment

| Capability | Assessment |
| --- | --- |
| Trusted Skill selection | Delivered |
| Multi-intent detection | Delivered for the deterministic first milestone |
| Multi-scenario composition | Delivered |
| Dependency-aware orchestration | Structurally delivered |
| Verification and completion gates | Delivered |
| Host approval signaling | Delivered through Contract v2 approval classes |
| Autonomous execution | Intentionally not delivered |
| Runtime permission management | Intentionally delegated to the host |
| Semantic Provider routing | Not delivered; deterministic fallback remains the current implementation |
| Production-grade routing quality | Not yet approved |

## Production Quality Status

The final 100-case evaluation reported:

| Metric | Current | Production target | Status |
| --- | ---: | ---: | --- |
| Multi-intent exact match | 0.85 | 0.80 | Pass |
| Scenario precision | 0.9277 | tracked | Baseline |
| Scenario recall | 0.9625 | tracked | Baseline |
| Scenario F1 | 0.9448 | 0.90 | Pass |
| Dependency-edge recall | 0.1429 | 0.90 | Major gap |
| DAG validity | 0.89 | 1.00 | Fail |
| Forbidden-scenario false-positive rate | 8.18% | 0.5% maximum | Fail |

The evaluator recorded 103 issue instances across 42 cases. Task-type macro F1
and required-capability recall are not yet reported. Independent external label
review is also not evidenced by a persisted review artifact.

Therefore this release may be described as a completed structural milestone,
but not as a production-ready autonomous or semantic router.

## Required Next Milestone

Before adding a semantic Provider, complete a deterministic quality-remediation
iteration that:

1. Reports task-type macro F1 and required-capability recall.
2. Reduces forbidden-scenario false positives to at most `0.5%`.
3. Reaches `1.0` DAG validity.
4. Raises dependency-edge recall toward the `0.90` target.
5. Adds persisted independent dataset-review evidence.
6. Adds a machine-readable overall production quality-gate result.
7. Tightens nested Task Pack v2 schemas for candidates, capability records,
   graph nodes, graph edges, and selected Skill Contracts.

Semantic reranking should remain optional and must preserve deterministic
fallback, privacy controls, structured output validation, and the method-only
runtime boundary.

## Final Repository State

- Branch: `main`
- Closure commit before this report: `d07f8a6`
- Delivery delta: 35 commits, 79 files changed
- Structural milestone: **PASS**
- Production quality gate: **FAIL / further remediation required**
- Release statement: suitable for repository publication with the limitations
  in this report explicitly retained
