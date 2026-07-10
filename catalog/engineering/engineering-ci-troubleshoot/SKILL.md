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

## Decision Guidance

Classify the first actionable failure as `code`, `configuration`,
`dependency_or_lock`, `cache`, `environment`, `infrastructure`, or `flake`.
Ignore downstream cancellations and repeated symptoms until the earliest causal
failure is understood. Compare passing and failing matrix dimensions, revisions,
tool versions, environment variables, dependency state, and job configuration
before choosing a fix.

Form one evidence-backed hypothesis at a time and use the smallest bounded
reproduction or diagnostic that can distinguish it. A retry that passes may
support a flake classification but does not prove the underlying race,
resource, or external dependency is fixed. Prefer changes tied directly to
observed evidence and verify the same failing command or equivalent job.

## Evidence Minimum

- workflow, run, branch/revision, job, matrix dimension, and failing command
- first actionable log with surrounding context and downstream symptoms
- recent code, config, dependency, image, runner, secret-reference, or cache changes
- classification and one hypothesis supported by passing/failing comparison
- bounded local or CI diagnostic and its result
- minimal correction target plus rerun or equivalent verification evidence
- skipped jobs, flakes, external dependencies, and residual pipeline risk

## References

Load [the CI diagnosis evidence guide](references/ci-diagnosis-evidence.md) for
matrix-only failures, dependency or cache drift, intermittent jobs, runner
differences, incomplete logs, release pipelines, or multiple downstream errors.

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
bounded diagnostic command. Do not rerun remote jobs, change secrets, bypass
required checks, alter release permissions, or mutate production without
separate host authorization.
