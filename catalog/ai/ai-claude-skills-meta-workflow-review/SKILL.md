---
name: ai-claude-skills-meta-workflow-review
description: Use when reviewing meta-workflow, loop-library, reusable agent-process, or skill-library orchestration references from the claude-skills backlog.
---

# AI Claude Skills Meta Workflow Review

## When To Use

Use this skill when a `claude-skills` backlog item describes a reusable agent
loop, meta workflow, skill library, or workflow orchestration pattern that
should be evaluated for local Safe-Agent-Skills adoption.

## Safe Workflow

1. Identify the repeated task, expected artifact, stop condition, owner, and
   verification evidence.
2. Separate reusable method guidance from runtime permissions, hidden tools,
   memory assumptions, or account access.
3. Map the workflow to existing trusted skills or scenario bundles before
   proposing a new catalog entry.
4. Convert only bounded local guidance with explicit inputs, outputs, gates,
   and failure handling.
5. Keep upstream material as metadata-only reference and record all coverage
   mappings in the candidate map.

## Expected Output

- workflow purpose and artifact contract
- existing trusted-skill coverage map
- proposed orchestration stages
- verification and stop-condition checklist
- adoption decision: covered, cluster-mapped, local authoring, or reject

## Verifier Expectations

- trusted-only dependency check
- runtime permission boundary check
- duplicate workflow check
- candidate-map coverage check

## Failure Handling

If a meta workflow depends on hidden state, account access, or unverified
runtime tools, keep it as reference coverage and do not add it to default
routing.
