---
name: ai-autogen-multi-agent-review
description: Use when reviewing multi-agent collaboration, role boundaries, conversation loops, or agent handoff workflows.
---

# AI AutoGen Multi Agent Review

## When To Use

Use this skill when multiple agents, roles, reviewers, or planners cooperate on
a task and need clear boundaries, turn rules, and termination criteria.

## Safe Workflow

1. Define each agent role, authority, tool access, and expected artifact.
2. Keep role prompts subordinate to user and host runtime policies.
3. Specify handoff points, review points, and stop conditions.
4. Prevent circular discussion by requiring evidence or artifact changes per
   round.
5. Record unresolved disagreements and escalation rules.

## Expected Output

- role and authority map
- handoff protocol
- termination criteria
- review and escalation notes
- residual risk list

## Verifier Expectations

- role boundary check
- loop and termination check
- tool permission check
- final artifact review

## Failure Handling

If roles conflict, collapse the workflow to a single accountable operator and
mark the multi-agent design for review.

## Boundary

This is a reference skill inspired by Microsoft AutoGen. It documents
multi-agent workflow review patterns and does not bundle framework code.
