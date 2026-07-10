---
name: code-review-risk
description: Use when reviewing code changes for bugs, regressions, missing tests, unsafe assumptions, and maintainability risks.
---

# Code Review Risk

## When To Use

Use this skill when reviewing a diff, pull request, patch, or generated code
before it is accepted.

## Safe Workflow

1. Identify the review scope, base revision, changed files, intended behavior, affected users, and observable success criteria.
2. Trace changed inputs, outputs, state, errors, cleanup, and side effects across module, API, schema, storage, process, and dependency boundaries.
3. Check correctness, reachability, edge cases, compatibility, concurrency, idempotency, defaults, migrations, feature flags, and rollback implications that apply to the change.
4. Map risky behavior to existing tests and name missing failure, boundary, or integration coverage.
5. Validate each finding against concrete triggering conditions and impact. Separate defects from optional maintainability advice.
6. Prioritize findings by severity and user impact, then record assumptions, unreviewed generated artifacts, and residual risk.
7. Avoid unrelated refactor suggestions unless they materially affect the safety or correctness of the reviewed change.

## Expected Output

- findings first, ordered by severity
- file and line references when available
- missing test notes
- brief residual risk summary

## Decision Guidance

Classify findings as `critical`, `high`, `medium`, `low`, or `advisory` using
impact, likelihood, reachability, blast radius, and recoverability. `critical`
and `high` findings require a concrete failure or security path with material
impact. `medium` and `low` findings still require behavior that can occur, not
only a preferred coding style. Use `advisory` for maintainability improvements
that do not demonstrate a current defect.

Review the changed contract rather than searching for theoretical issues in
unrelated code. Confirm whether the suspect path is reachable under realistic
inputs, configuration, permissions, and lifecycle order. When intent is
unclear, state the assumption and lower confidence instead of overstating the
finding.

## Evidence Minimum

- intended behavior, review scope, base revision, and affected users
- file and line reference plus the relevant changed contract or data flow
- realistic triggering conditions and concrete impact
- severity and confidence with the factors that justify them
- existing test evidence and the specific missing coverage
- compatibility, migration, dependency, or rollback implications when present
- unverified assumptions, unavailable runtime evidence, and residual risk

## References

Load [the code review evidence checklist](references/review-evidence-checklist.md)
for multi-file changes, shared contracts, concurrency, persistence, security,
migrations, dependencies, or release-sensitive behavior.

## Verifier Expectations

- diff review
- relevant test command review
- behavior contract check
- dependency or API compatibility check when relevant

## Failure Handling

If the intended behavior is unclear, state the assumption and review against
that assumption. Do not run code, edit the change, contact external services,
approve a release, or accept the patch unless the host workflow separately
authorizes those actions.
