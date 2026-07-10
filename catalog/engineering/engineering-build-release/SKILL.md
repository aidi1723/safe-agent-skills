---
name: engineering-build-release
description: Use when preparing a local build, release readiness check, or engineering handoff with explicit smoke tests and rollback notes.
---

# Build And Release Readiness

## When To Use

Use this skill when the task asks to prepare a build, package, release note,
deployment handoff, or engineering readiness check.

## Safe Workflow

1. Identify the project type, build command, output artifact, and target environment.
2. Confirm the intended scope: local build, staging release, or production handoff.
3. Run only approved local build and smoke-test commands.
4. Record generated artifacts, versions, and configuration changes.
5. Prepare rollback notes for any release-affecting change.
6. Keep credential and infrastructure actions behind explicit approval.

## Expected Output

- build status
- artifact paths
- smoke-test result
- release or handoff notes
- rollback considerations

## Verifier Expectations

- build check
- smoke test
- artifact existence check
- configuration diff review

## Decision Guidance

Classify readiness as `ready_for_local_use`, `ready_for_staging`,
`ready_for_release_approval`, or `blocked`. A successful compilation alone is
not release readiness. The claimed level must match the evidence actually run:
tests, artifact identity, configuration review, migration checks, security or
license gates, smoke results, and rollback feasibility.

Keep build verification separate from deployment authority. Producing a
release candidate or handoff does not authorize publishing, credential use,
infrastructure mutation, or production rollout. When a required verifier is
unavailable, mark the corresponding gate unresolved rather than substituting a
weaker result without disclosure.

## Evidence Minimum

- source revision and reproducible build command
- artifact name, version, checksum, and location
- test and smoke-check results tied to the artifact
- configuration, dependency, schema, and migration changes
- rollback trigger, owner, and recovery procedure
- unresolved gates and explicit release approval owner

## References

Load [the release gates guide](references/release-gates.md) for staging or
production handoffs, packages with migrations, multi-artifact releases, or
changes that require a coordinated rollback.

## Failure Handling

If the build fails, report the first actionable failure and do not continue into
release steps.
