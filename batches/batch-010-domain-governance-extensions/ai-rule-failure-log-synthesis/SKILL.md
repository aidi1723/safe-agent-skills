---
name: ai-rule-failure-log-synthesis
description: Use when reviewing agent failures, policy blocks, verifier failures, repeated mistakes, or logs that should become safer future rules.
---

# AI Rule Failure Log Synthesis

## When To Use

Use this skill when blocked agent actions, failed verifiers, rejected outputs,
or repeated review findings need to be turned into safer deterministic rules.

## Safe Workflow

1. Collect only task-local failure samples, reviewer notes, verifier output,
   command summaries, and affected artifact names.
2. Remove credentials, private content, customer data, and unrelated logs before
   analysis.
3. Group failures by invariant violated: source gap, permission boundary,
   schema mismatch, unsafe wording, missing verification, or stale assumption.
4. Draft candidate rules as narrow preconditions, checklists, or verifier
   expectations instead of broad behavioral slogans.
5. Record evidence, false-positive risk, and where the rule should live:
   skill text, automated validator, CI check, or operator policy.

## Expected Output

- sanitized failure sample summary
- repeated invariant list
- candidate rule wording
- false-positive risks
- recommended enforcement location

## Verifier Expectations

- sensitive data removal check
- failure grouping check
- rule specificity check
- enforcement location check

## Failure Handling

If the logs contain sensitive or production data, stop summarizing details and
only report the redaction requirement and rule category.
