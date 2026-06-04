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

## Failure Handling

If the build fails, report the first actionable failure and do not continue into
release steps.
