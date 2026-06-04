---
name: execution-e2b-sandbox-boundary
description: Use when reviewing code execution sandboxes, tool environments, ephemeral workspaces, or agent runtime isolation.
---

# Execution E2B Sandbox Boundary

## When To Use

Use this skill when an agent needs a sandboxed environment for code execution,
tool use, file processing, or external workflow tests.

## Safe Workflow

1. Identify sandbox purpose, input files, allowed tools, network scope, and
   lifetime.
2. Keep sandbox files separate from host files unless explicit sync is approved.
3. Define what data may enter and leave the sandbox.
4. Record execution results, generated artifacts, and cleanup requirements.
5. Stop before production writes or credential use unless separately approved.

## Expected Output

- sandbox boundary plan
- allowed input and output data
- tool and network limits
- artifact record
- cleanup and evidence notes

## Verifier Expectations

- sandbox scope check
- host file isolation check
- artifact output check
- credential and network boundary check

## Failure Handling

If sandbox limits are unclear, treat execution as review-only and avoid running
state-changing commands.

## Boundary

This is a reference skill inspired by E2B. It documents sandbox boundary
patterns and does not bundle sandbox runtimes or grant execution rights.
