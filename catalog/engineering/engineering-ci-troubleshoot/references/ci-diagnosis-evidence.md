# CI Diagnosis Evidence

Use this guide to isolate the earliest actionable pipeline failure.

## Run Context

Record workflow, run, revision, trigger, job, matrix values, runner image,
toolchain, dependency lock, cache keys, environment assumptions, and the first
failed command. Separate causal failures from skipped or cancelled jobs.

## Classification

Compare passing and failing runs to distinguish code, configuration,
dependency or lock drift, stale cache, environment mismatch, infrastructure,
and flakiness. Note recent changes at each boundary and avoid changing multiple
variables in one diagnostic.

## Reproduction And Fix

Use the smallest workspace-bounded command or CI diagnostic that tests one
hypothesis. Tie the correction to observed evidence. For intermittent failures,
identify timing, shared state, resource, or external-service conditions rather
than relying on retries.

## Verification

Record the formerly failing command, relevant job or matrix rerun, broader
checks, skipped coverage, and remaining pipeline or release risk.
