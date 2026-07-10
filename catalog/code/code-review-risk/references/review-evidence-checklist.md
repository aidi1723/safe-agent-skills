# Code Review Evidence Checklist

Use this checklist for a high-confidence review of a change set. Review the
requested behavior and changed boundary, not the repository in the abstract.

## Intent And Reachability

- Record the intended behavior, affected users, entry points, changed files,
  and observable success criteria.
- Trace whether each suspected path is reachable with realistic inputs and
  configuration. Do not report purely hypothetical behavior as a defect.
- Separate facts visible in the diff from assumptions that require execution,
  external state, or product clarification.

## Correctness And State

- Check input validation, output contracts, error paths, cleanup, retries,
  partial failure, ordering, concurrency, idempotency, caching, and persistence.
- Follow data across module, process, API, schema, and storage boundaries.
- Review compatibility, migrations, feature flags, defaults, and rollback when
  the change affects shared or persisted behavior.

## Finding Standard

Each finding must state severity, file and line, triggering conditions,
concrete impact, supporting evidence, and the smallest correction target.
Classify severity from impact, likelihood, reachability, blast radius, and
recoverability. Keep optional cleanup separate from defects.

## Test And Residual Risk

Map risky behavior to existing or missing tests. Name unverified assumptions,
unavailable runtime evidence, generated files not reviewed, and downstream
consumers that may still require validation.
