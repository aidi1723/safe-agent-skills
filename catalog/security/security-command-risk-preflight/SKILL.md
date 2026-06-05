---
name: security-command-risk-preflight
description: Use when reviewing proposed terminal commands, file operations, scripts, dependency actions, or operational steps before execution.
---

# Security Command Risk Preflight

## When To Use

Use this skill when an agent or operator is about to run commands that may
change files, dependencies, build output, configuration, or repository state.

## Safe Workflow

1. Identify the command purpose, working directory, expected file changes, and
   whether approval is required by the host runtime.
2. Classify the action as read-only, local write, dependency change, network
   call, publication, credential-adjacent, or destructive-risk.
3. Check for broad path targets, recursive file changes, permission changes,
   generated artifact churn, hidden network use, and missing rollback notes.
4. Prefer narrow workspace-scoped commands and dry-run or list modes when
   available.
5. Record the risk class, required approvals, expected outputs, and post-action
   verification before execution.

## Expected Output

- command inventory
- risk classification
- approval needs
- rollback or checkpoint notes
- verification checklist

## Verifier Expectations

- working directory check
- file-change scope check
- approval policy check
- rollback readiness check

## Failure Handling

If the command scope or side effects are unclear, stop at review output and ask
for a narrower command or explicit operator approval.
