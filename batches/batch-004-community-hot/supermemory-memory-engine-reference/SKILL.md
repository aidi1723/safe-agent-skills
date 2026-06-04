---
name: supermemory-memory-engine-reference
description: Use when designing, evaluating, or integrating persistent AI memory retrieval without exposing private data or secrets.
---

# SuperMemory Memory Engine Reference

## When To Use

Use this skill when an AI workflow needs durable memory, fast retrieval, or a
memory connector design for projects, users, documents, or repeated tasks.

## Safe Workflow

1. Classify memory records by scope: user, project, task, document, or system.
2. Record source URL or local path, author, capture date, and allowed use.
3. Store only the minimum useful summary unless the source is explicitly approved
   for full retention.
4. Block auth material, private keys, payment data, and sensitive personal data
   from memory ingestion.
5. Retrieve memory with relevance and recency limits.
6. Show retrieved memory in the task trace before it influences output.

## Expected Output

- memory schema
- ingestion allowlist and denylist
- retrieval policy
- deletion and correction path
- privacy review notes

## Verifier Expectations

- no secret or sensitive data retention
- provenance exists for each memory record
- retrieval can be audited
- current user request remains the top authority

## Boundary

This is a reference skill inspired by SuperMemory. It does not copy service code
or require external memory APIs during skill selection.
