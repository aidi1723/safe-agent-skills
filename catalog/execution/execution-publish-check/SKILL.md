---
name: execution-publish-check
description: Use when preparing controlled publishing, release handoff, artifact upload, or public repository readiness checks.
---

# Execution Publish Check

## When To Use

Use this skill when an artifact, catalog, package, or repository is nearly ready
to publish and needs a final controlled checklist.

## Safe Workflow

1. Identify the publish target, artifact version, owner, and approval path.
2. Verify source records, license notes, generated files, and release docs.
3. Run available tests or integrity checks before handoff.
4. Keep publishing action separate from readiness review unless explicitly
   approved.
5. Record blockers, warnings, and final checklist status.

## Decision Guidance

Classify readiness as `not_ready`, `ready_for_handoff`,
`ready_for_approval`, or `approved_to_publish`. `not_ready` has unresolved
required gates or artifact identity. `ready_for_handoff` has a reviewable
candidate and evidence but still needs operator work. `ready_for_approval` has
all required evidence and awaits the named authority. `approved_to_publish`
requires an explicit approval record for the exact target and artifact; it is
not inferred from tests, a merge, or a prior release.

Bind every decision to an immutable artifact identity, version, checksum,
source revision, target, configuration, and verification result. Review
provenance, license, generated files, migrations, compatibility, rollback, and
communication requirements that apply. Keep readiness review separate from
uploading, pushing, releasing, deploying, or changing production state.

## Evidence Minimum

- publish target, environment, owner, approval class, and exact authority
- artifact name, version, checksum, location, and source revision
- clean diff or release contents plus generated-file and dependency review
- build, test, schema, integrity, provenance, license, and security results
- configuration, secrets references, feature flags, migrations, and compatibility
- rollback trigger, last known-good artifact, procedure, owner, and verification
- blockers, warnings, waived/skipped gates, residual risk, and decision timestamp

## References

Load [the publication readiness evidence guide](references/publication-readiness-evidence.md)
for packages, repositories, catalogs, public artifacts, migrations, multi-target
releases, external uploads, or production-sensitive handoffs.

## Expected Output

- readiness checklist
- artifact and version record
- verification commands
- blockers and warnings
- publication decision

## Verifier Expectations

- registry or artifact integrity check
- license and provenance check
- test or build check
- final diff review

## Failure Handling

If publication authority is unclear, provide readiness status without publishing.
Never upload, push, release, deploy, use credentials, mutate production, or
waive required gates without explicit host authorization for the exact action.
