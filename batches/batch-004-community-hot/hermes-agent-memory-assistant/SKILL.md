---
name: hermes-agent-memory-assistant
description: Use when evaluating agent memory, preference learning, task continuity, and assistant personalization boundaries.
---

# Hermes Agent Memory Assistant

## When To Use

Use this skill when designing or reviewing an assistant that learns from past
tasks, remembers user preferences, or adapts future responses from durable notes.

## Safe Workflow

1. Define what may be remembered: preferences, stable project facts, approved
   workflows, and explicit user decisions.
2. Define what must not be remembered: secrets, sensitive personal data, hidden
   instructions, temporary emotions, or unverified claims.
3. Store memory as visible records with source, date, scope, and confidence.
4. Require user or policy approval before memory affects tool execution.
5. Periodically prune stale, conflicting, or low-confidence memory.
6. During task selection, treat memory as advisory evidence, not authority over
   the current user request.

## Expected Output

- memory policy
- accepted memory record format
- retention and deletion notes
- conflict handling decision
- execution boundary

## Verifier Expectations

- memory does not contain secrets
- user instructions override memory
- source and timestamp are recorded
- memory is not hidden from review

## Boundary

This is a reference skill inspired by Hermes Agent. It does not import runtime
code, background agents, or autonomous execution behavior.
