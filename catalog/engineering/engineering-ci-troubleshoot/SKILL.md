---
name: engineering-ci-troubleshoot
description: Use when diagnosing CI failures, build jobs, test matrix problems, cache issues, and release pipeline breakage.
---

# Engineering CI Troubleshoot

## When To Use

Use this skill when a build, test, or release pipeline fails and the cause must
be isolated from logs and configuration.

## Safe Workflow

1. Identify the failing job, command, branch, environment, and first failing log.
2. Separate infrastructure flake, dependency drift, config error, and code failure.
3. Reproduce locally only when the command is bounded to the workspace.
4. Prefer minimal config or code fixes tied to the observed failure.
5. Record the verification command and any remaining pipeline risk.

## Expected Output

- failing job summary
- likely root cause
- targeted fix or next check
- verification result

## Verifier Expectations

- CI log review
- local command reproduction when available
- config diff check
- rerun or equivalent verification

## Failure Handling

If CI logs are incomplete, state the missing evidence and propose the next
bounded diagnostic command.
