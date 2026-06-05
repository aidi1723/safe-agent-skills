---
name: engineering-error-log-noise-triage
description: Use when triaging stack traces, CI logs, runtime errors, noisy logs, repeated failures, or framework noise before debugging.
---

# Engineering Error Log Noise Triage

## When To Use

Use this skill when logs or stack traces are too noisy to identify the first
meaningful failure, regression point, or owner.

## Safe Workflow

1. Identify the command, environment, timestamp, exit status, changed files, and
   whether the failure is local, CI, runtime, or user-facing.
2. Separate first error, root-cause candidates, repeated follow-on errors,
   warnings, framework noise, and unrelated background output.
3. Preserve exact file paths, line numbers, exception names, failing test names,
   and command summaries.
4. Group repeated failures by signature instead of counting every duplicate
   line as a separate issue.
5. Recommend the smallest next diagnostic step and the verification command
   that should turn green after the fix.

## Expected Output

- first meaningful error
- grouped failure signatures
- likely owner or component
- ignored noise rationale
- next diagnostic step

## Verifier Expectations

- first-error check
- duplicate grouping check
- changed-file correlation check
- verification command check

## Failure Handling

If logs are incomplete, request the missing command output, environment, or
reproduction step before proposing a fix.
