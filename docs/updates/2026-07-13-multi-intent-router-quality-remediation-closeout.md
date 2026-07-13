# Multi-Intent Router Quality Remediation Closeout

Date: 2026-07-13

## Scope

This closeout records the completed non-action-context remediation slice on
`docs/multi-intent-router-quality-remediation` at commit `11f6ef8`.

The slice prevents profile signals from becoming actionable intents when they
appear only in explicit inventories, quoted examples, future roadmaps,
no-authority statements, historical records, or work owned by another team.
It does not change corpus labels, the evaluator, compiler behavior, quality
thresholds, catalog trust, or runtime permissions.

## Delivered Behavior

- Added bounded `NonActionSourceRange` filtering before profile evidence is
  emitted.
- Suppressed structural inventory, quoted-text, and future-roadmap clauses to
  canonical `general` evidence.
- Suppressed only the local range for authority, historical, and other-owner
  statements; profile evidence outside that range remains eligible.
- Preserved direct current work after `but`, Chinese adversatives, and tested
  comma continuations such as `complete the website launch`.
- Added regression coverage for the positive, negative, quoted, inventory,
  future, historical, ownership, English, and Chinese controls above.

## Verification

Fresh local verification completed on 2026-07-13:

```text
PATH=/tmp/safe-agent-skills-structural-venv/bin:$PATH \
  PYTHONPATH=src bash scripts/verify.sh

747 tests OK
```

The 450-case production suite was also evaluated without changing its manual
labels:

```text
suite: router-production-v1
suite SHA-256: 323c92502bc1bdec988e315bda2138d37f436e3644bed3d3ee78440cdab40e9a
DAG validity: 1.0 (pass)
core bundle contract coverage: 0.8125 (pass)
production_ready: false
```

## Quality Gate

The production claim remains blocked. The following gates still fail:

| Metric | Result | Threshold |
| --- | ---: | ---: |
| Dependency-edge recall | 0.06818 | at least 0.90 |
| Forbidden-scenario false-positive rate | 0.32867 | at most 0.005 |
| Forbidden-Skill false-positive rate | 0.08750 | at most 0.005 |
| High-confidence error rate | 0.59783 | at most 0.02 |
| Multi-intent exact match | 0.23333 | at least 0.80 |
| Required-capability recall | 0.25227 | at least 0.97 |
| Scenario F1 | 0.41316 | at least 0.88 |
| Task-type macro F1 | 0.39541 | at least 0.90 |

The evaluation also has no source-bound independent review record for this
commit, so the independent-label-review gate remains missing. This branch must
not be described as production-ready automatic orchestration.

## Accepted Residual Risk

The operator selected the bounded release path rather than replacing the
continuation grammar with a fuller command parser. A comma followed by words
such as `build`, `design`, `plan`, `review`, or `release` can still be a noun
phrase rather than a command. In that form, the local range filter can expose
an otherwise non-actionable profile signal.

This risk is documented, not resolved. The next router-quality tranche should
replace the lexical continuation check with a command-shape predicate and add
noun-phrase controls before broadening the non-action grammar.

## Handoff

- Branch: `docs/multi-intent-router-quality-remediation`
- Implementation commit: `11f6ef8 fix: suppress non-action routing evidence`
- Remote: `origin/docs/multi-intent-router-quality-remediation`
- Safety boundary: routing remains deterministic and method-only; skill
  selection does not grant filesystem, network, browser, connector, credential,
  publication, or runtime execution permission.
