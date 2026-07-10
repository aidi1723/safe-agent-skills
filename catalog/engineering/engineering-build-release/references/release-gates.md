# Build And Release Gates

Use these gates for release candidates and deployment handoffs. Running a gate
does not grant deployment or publication authority.

## Source And Build

- Record the source revision, clean-worktree state, toolchain, dependency lock,
  build command, and environment assumptions.
- Confirm the output can be tied to the reviewed source and configuration.
- Record artifact names, versions, checksums, and storage locations.

## Verification

- Run the required unit, integration, contract, schema, security, license, and
  smoke checks for the release scope.
- Bind results to the actual candidate artifact rather than an earlier local
  build.
- Mark skipped, unavailable, flaky, or waived checks explicitly with owner and
  rationale.

## Change And Migration Review

- Review configuration defaults, feature flags, secrets references, dependency
  changes, database or schema migrations, compatibility windows, and resource
  assumptions.
- For migrations, document ordering, forward compatibility, recovery, and the
  point after which rollback is no longer safe.

## Rollback And Handoff

Define rollback triggers, the last known-good artifact, recovery steps, data
restoration implications, operator, communication path, and post-rollback
verification. A rollback note that only says “revert” is insufficient when
state or data changes are involved.

The handoff must state the highest readiness level actually proven, unresolved
gates, required approvals, and actions that remain prohibited until the host
runtime or operator authorizes them.
