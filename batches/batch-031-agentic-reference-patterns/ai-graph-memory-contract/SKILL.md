---
name: ai-graph-memory-contract
description: Use when designing or reviewing long-term agent memory, graph memory, remember/recall/forget/improve operations, tenant isolation, memory correction, retrieval disclosure, or durable cross-session context.
---

# AI Graph Memory Contract

## When To Use

Use this skill when an agent workflow needs durable memory across sessions,
graph or vector-backed recall, user preference memory, shared team knowledge,
or correction and deletion behavior.

This skill defines a contract only. It does not run a memory service, write to
an index, or grant access to external databases.

## Safe Workflow

1. Classify each memory record by scope: user, project, tenant, task, document,
   organization, or system.
2. Define four operations before any integration:
   `remember`, `recall`, `forget`, and `improve`.
3. Require each record to include source, timestamp, owner, scope, confidence,
   retention rule, allowed use, and deletion path.
4. Separate session cache from durable graph memory. Session memory can speed
   continuity, but durable memory needs provenance and retention review.
5. Treat recalled memory as advisory evidence. Current user instructions,
   policy, and task-local source material remain higher authority.
6. Keep tenant, project, and access boundaries explicit in retrieval filters.
7. Show recalled memory or a compact citation trace before it influences a
   decision, tool route, or final answer.
8. Define improvement behavior as a visible correction or link update, not a
   hidden rewrite of prior facts.

## Expected Output

- memory operation contract
- memory record schema
- tenant and project boundary map
- retrieval and disclosure policy
- correction, deletion, and retention path
- source, freshness, and confidence notes

## Verifier Expectations

- no secret or sensitive data retention
- source and timestamp check for every durable record
- tenant and namespace filter check
- recall trace visibility check
- forget and correction path check
- current request authority check

## Failure Handling

If source authority, tenant scope, or deletion behavior is unclear, keep memory
use disabled for execution and produce a contract draft with the blocked field
marked as a decision requirement.
