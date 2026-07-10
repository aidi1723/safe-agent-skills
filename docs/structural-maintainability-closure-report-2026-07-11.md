# Structural Maintainability Closure Report

Date: 2026-07-11

## Outcome

The structural maintainability redesign is complete. The public CLI and router
facades remain compatible, while implementation ownership is distributed into
focused modules. Batch drafts, current documentation, historical records, and
skill-depth expectations now have explicit lifecycle rules and verification
gates.

## Before And After

| Area | Before | After |
| --- | ---: | ---: |
| `cli.py` | 4,010 lines | 348 lines |
| `router.py` | 2,408 lines | 381 lines |
| `test_registry_cli.py` | 5,417 lines | 277 lines |
| largest split CLI test module | 5,417 lines | 1,483 lines |
| README Markdown links | 79 | 25 |
| batch items | 471 implicit directories | 471 indexed lifecycle records |
| compacted promoted bodies | 0 | 167 |
| depth-governed catalog skills | 0 | 172 |
| specialist reference assets | 0 | 7 |

The split implementation modules are intentionally cohesive rather than
uniformly tiny. The largest current owners are `task_packs.py` at 1,160 lines,
`routing_profiles.py` at 1,046 lines, and `routing_execution.py` at 999 lines.

## Delivered Boundaries

- `cli.py` is now parser assembly and a compatibility facade. Commands,
  rendering, bulk workflows, registry operations, task-pack construction, and
  router evaluation have dedicated owners.
- `router.py` is now a compatibility facade over profile/scoring and execution
  graph owners.
- The former CLI regression module is split by catalog maintenance, routing,
  bulk workflows, Schema v2 task packs, router evaluation, scan, and workflow
  behavior.
- Identity-based facade tests and the Schema v1 payload-shape hash protect the
  established public imports and JSON contract.

## Batch And Documentation Governance

`batches/index.json` records 471 items: 303 `active_draft` and 168 `promoted`.
There are 167 historical byte-identical compactions represented by
`PROMOTED.md`. Eight promoted records no longer match the current catalog: the
pre-existing `ai-litellm-gateway-cost-control` mismatch and seven catalog
skills deliberately deepened during this redesign and its high-frequency
follow-up batches. Their original source hashes, promotion records, and current
catalog hashes remain explicit and validated.

Documentation was not bulk-deleted. The repository contains 161 Markdown files
compared with 152 at the starting commit because this redesign adds maintained
policy, index, history, plan, and closure records. `docs/index.md` is the
current source-of-truth entry, `docs/history.md` routes dated evidence, and the
README no longer exposes dozens of historical reports as peer entry points.

## Skill Depth

The depth policy classifies 165 catalog entries as `routing_card` and seven as
`specialist`. The following specialists now include decision criteria,
evidence minimums, failure/escalation paths, and an on-demand reference guide:

- `security-supply-chain-review`
- `compliance-privacy-check`
- `engineering-build-release`
- `design-ui-review`
- `code-review-risk`
- `code-test-regression`
- `research-source-check`

Auxiliary content under `references/` and `scripts/` is covered by an optional
canonical SHA-256 manifest field. Registry verification detects auxiliary
tampering, while the legacy Schema v1 task-pack hash shape remains unchanged.

## Verification Evidence

The final feature-branch verification command was:

```bash
PATH=/tmp/safe-agent-skills-structural-venv/bin:$PATH bash scripts/verify.sh
```

Result: exit 0, 347 tests passed. Ruff, compilation, catalog maintenance,
private-path scanning, router evaluation v1 and v2, manifest and task-pack
schemas, registry verification, batch lifecycle, depth policy, contract
coverage, JSON syntax, and documentation links all passed.

Catalog verification remained at 172 skills, 166 trusted, 0 tampered, and 0
unknown provenance records. Router evaluation passed 43 of 43 cases. Depth
audit passed 172 skills with 0 errors and 0 warnings. Batch validation passed
471 records with 167 compacted and 0 issues.

## Residual Risks

- Three extracted owner modules remain near or above 1,000 lines. Split them
  only when ownership or change patterns justify another boundary.
- The 303 active drafts remain maintenance inventory. Lifecycle checks prevent
  them from being mistaken for production catalog entries but do not remove
  the review backlog.
- The depth audit measures deterministic structure, not semantic expertise.
  Only seven representative skills were promoted to specialist depth.
- Historical documentation remains sizable. The index/history split reduces
  discovery noise, but periodic archival review is still required.
- Static scanning, hashes, and schemas support review; they do not replace host
  sandboxing, approval controls, or qualified security/legal judgment.

## Recommended Follow-Up

Review active drafts by value and duplication rather than directory age. Track
change frequency in the three largest owner modules before splitting further.
Promote additional skills to `playbook` or `specialist` only when repeated real
tasks demonstrate that routing-card depth is insufficient.
