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
