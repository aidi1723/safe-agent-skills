---
name: headroom-context-compression
description: Use when compressing long task context, chat history, notes, or documents before an AI workflow while preserving key facts.
---

# Headroom Context Compression

## When To Use

Use this skill when a task has too much text for the available context window or
when token cost needs to be reduced without losing decisions, constraints, or
evidence.

## Safe Workflow

1. Separate source facts, user instructions, decisions, open questions, and
   disposable narration.
2. Keep exact names, dates, paths, versions, commands, links, and ownership
   records.
3. Remove repeated explanations, social filler, speculative wording, and stale
   intermediate reasoning.
4. Preserve risk warnings and unresolved assumptions as explicit notes.
5. Produce a compressed brief that can be audited against the original source.
6. Never compress away consent requirements, safety boundaries, or provenance.

## Expected Output

- compressed context brief
- preserved constraints
- retained provenance and links
- unresolved questions
- compression risk notes

## Verifier Expectations

- important facts remain traceable
- no new facts are invented
- provenance fields remain intact
- safety or approval requirements are not removed

## Boundary

This is a reference skill inspired by the Headroom project. It provides a
OneCode-safe compression workflow and does not copy Headroom implementation.
