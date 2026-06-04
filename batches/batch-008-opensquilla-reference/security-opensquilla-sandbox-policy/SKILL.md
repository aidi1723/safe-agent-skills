---
name: security-opensquilla-sandbox-policy
description: Use when reviewing agent sandbox boundaries, refusal logs, approval gates, or repeated unsafe action attempts.
---

# Security OpenSquilla Sandbox Policy

## When To Use

Use this skill when an agent workflow involves tools, browser actions,
connectors, files, shell commands, or other execution paths that need a clear
sandbox and refusal policy.

## Safe Workflow

1. Identify every runtime action the agent might request.
2. Map each action to host permissions: filesystem, network, shell, browser,
   connector, account, and production write access.
3. Require approval before any action outside the current approved workspace.
4. Record refused actions and do not keep retrying the same denied path.
5. Escalate repeated denials or ambiguous permission requests to operator
   review.

## Expected Output

- runtime action inventory
- permission boundary map
- approval and refusal policy
- repeated-denial escalation rule
- residual risk notes

## Verifier Expectations

- permission scope check
- refusal log check
- sandbox boundary check
- production write approval check

## Failure Handling

If the agent repeatedly asks for blocked access, stop the workflow and report
the unsafe request instead of searching for alternate bypass paths.

## Boundary

This is a reference skill inspired by OpenSquilla sandbox and policy concepts.
It documents safety review behavior only and does not grant sandbox,
filesystem, network, shell, browser, or connector permissions.
