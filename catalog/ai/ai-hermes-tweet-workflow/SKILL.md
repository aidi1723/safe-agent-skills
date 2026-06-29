---
name: ai-hermes-tweet-workflow
description: Use when reviewing Hermes Agent workflows that need X social signal, read-first exploration, or approval-gated account actions through Hermes Tweet.
---

# AI Hermes Tweet Workflow

## When To Use

Use this skill when a Hermes Agent workflow needs X social listening, account
status review, trend awareness, community evidence gathering, or controlled
publishing through the Hermes Tweet plugin.

## Safe Workflow

1. Confirm the target runtime is Hermes Agent and the task needs X social
   signal or account-aware actions.
2. Start with discovery and read-only planning before any account-changing
   step.
3. Keep exploration, reads, and actions as separate phases with clear operator
   review between them.
4. Treat publishing, replies, follows, messages, monitor changes, and webhook
   changes as opt-in actions that require explicit operator approval.
5. Keep runtime configuration values outside prompts, skill packs, issue text,
   and generated task output.
6. Link to the Hermes Tweet source repository and package metadata instead of
   copying plugin code or endpoint catalogs into another skill.

## Expected Output

- Hermes Tweet workflow fit note
- read and action boundary
- approval checklist
- validation references
- unresolved assumptions

## Verifier Expectations

- Hermes Agent is the intended host runtime
- Hermes Tweet source and package metadata are linked
- no private account material appears in prompts or task packs
- account-changing actions remain opt-in and operator-approved
- the workflow stays method-only and does not import runtime code

## Failure Handling

If the target catalog requires hosted uploads, source-free registry entries,
vendored plugin code, or platform-specific actions instead of a source-linked
Hermes Tweet package reference, mark the route as not suitable.

## Boundary

This is a reference skill inspired by Hermes Tweet. It preserves workflow
method, review gates, and source metadata only. It does not import plugin code,
tool catalogs, runtime configuration, or account operation behavior.
