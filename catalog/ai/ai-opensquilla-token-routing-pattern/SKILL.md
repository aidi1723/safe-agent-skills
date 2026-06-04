---
name: ai-opensquilla-token-routing-pattern
description: Use when reviewing token-aware skill loading, model routing, task-pack compression, or cost-sensitive agent planning.
---

# AI OpenSquilla Token Routing Pattern

## When To Use

Use this skill when an agent workflow needs to reduce context waste, choose
only necessary skills, or plan model/tool usage under a fixed budget.

## Safe Workflow

1. Classify the task before loading long instructions.
2. Select only the smallest useful set of trusted skills or bundles.
3. Keep review-required and quarantined skills out of default execution packs.
4. Record why each selected skill is needed.
5. Estimate whether the selected context is proportional to the task risk and
   output value.

## Expected Output

- compact task-pack selection
- selected skill rationale
- omitted skill rationale
- token and context risk notes
- review-mode warning when needed

## Verifier Expectations

- trusted-only selection check
- registry verification check
- bundle trusted-reference check
- token budget review for large packs

## Failure Handling

If the task requires many broad skills, prefer a scenario bundle or split the
task into smaller phases instead of loading the whole catalog.

## Boundary

This is a reference skill inspired by OpenSquilla's token-efficiency and
on-demand skill loading positioning. It documents selection policy only and
does not implement model routing.
