---
name: code-dead-path-cleanup-review
description: Use when reviewing unused code, stale branches, dead feature paths, unreachable logic, cleanup diffs, or tree-shaking candidates.
---

# Code Dead Path Cleanup Review

## When To Use

Use this skill when code appears unused, unreachable, obsolete, duplicated, or
safe to remove from a project.

## Safe Workflow

1. Identify the candidate code path, callers, exports, runtime entry points,
   tests, feature flags, scheduled jobs, and external consumers.
2. Distinguish truly unused code from conditionally used code, plugin entry
   points, reflection-based loading, generated hooks, and migration helpers.
3. Check references with static search, runtime configuration, docs, scripts,
   tests, and package manifests.
4. Prefer small cleanup diffs with rollback notes over broad deletion waves.
5. Verify with tests, build, type checks, or targeted smoke checks covering
   affected entry points.

## Expected Output

- cleanup candidate list
- reference search evidence
- conditional-use risks
- removal recommendation
- verification plan

## Verifier Expectations

- static reference check
- entry point check
- feature flag or config check
- regression test check

## Failure Handling

If external or dynamic usage cannot be ruled out, mark the cleanup as review
required and keep the code until ownership is confirmed.
