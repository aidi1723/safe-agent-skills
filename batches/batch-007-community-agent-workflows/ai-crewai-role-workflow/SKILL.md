---
name: ai-crewai-role-workflow
description: Use when designing role-based agent teams, task delegation, process sequencing, or collaborative agent workflows.
---

# AI CrewAI Role Workflow

## When To Use

Use this skill when a task benefits from role-based agents such as researcher,
planner, builder, reviewer, and publisher.

## Safe Workflow

1. Define the goal, roles, artifacts, and owner of final approval.
2. Assign each role only the minimum context and tools required.
3. Sequence tasks so review happens before publication or production action.
4. Require evidence from each role before accepting its output.
5. Merge outputs through a single final accountable answer.

## Expected Output

- role plan
- task sequence
- artifact ownership
- review gates
- final synthesis notes

## Verifier Expectations

- role scope check
- evidence check
- final approval check
- publication boundary check

## Failure Handling

If a role cannot provide evidence, mark its output as advisory and route it to
human or operator review.

## Boundary

This is a reference skill inspired by CrewAI. It documents role workflow
patterns and does not bundle agent framework code.
