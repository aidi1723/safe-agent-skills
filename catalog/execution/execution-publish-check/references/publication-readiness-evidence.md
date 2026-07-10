# Publication Readiness Evidence

Use this guide to bind a readiness decision to one exact artifact and target.

## Identity And Target

Record target, environment, artifact name, version, checksum, source revision,
storage location, owner, and approval authority. Confirm the evidence belongs
to this candidate rather than an earlier build or different configuration.

## Required Gates

Collect build, test, schema, integrity, provenance, license, security,
generated-file, dependency, configuration, feature-flag, and migration results
required by the release type. Mark unavailable, skipped, waived, or flaky gates
with owner and rationale.

## Recovery

Define rollback triggers, last known-good artifact, procedure, data or migration
implications, operator, communication path, and post-rollback verification.

## Decision Record

State readiness level, blockers, warnings, residual risks, approver, timestamp,
allowed target, and actions still prohibited. Approval for one artifact or
environment does not authorize another.
