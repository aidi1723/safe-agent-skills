---
name: headroom-context-compression
description: Use when compressing long task context, tool outputs, logs, retrieval chunks, chat history, notes, or documents before an AI workflow while preserving key facts.
---

# Headroom Context Compression

## When To Use

Use this skill when a task has too much text for the available context window or
when token cost needs to be reduced across tool results, logs, RAG chunks,
files, chat history, or notes without losing decisions, constraints, or
evidence.

## Safe Workflow

1. Classify inputs as `tool_result`, `log`, `rag_chunk`, `file_excerpt`,
   `chat_history`, or `note` before compression.
2. Separate source facts, user instructions, decisions, open questions, and
   disposable narration.
3. Keep exact names, dates, paths, versions, commands, links, ownership
   records, error codes, stack-frame anchors, line numbers, and retrieval
   source IDs.
4. Remove repeated explanations, social filler, speculative wording, stale
   intermediate reasoning, and low-signal duplicates.
5. Preserve risk warnings, unresolved assumptions, consent requirements, safety
   boundaries, and provenance as explicit notes.
6. Record when the original source must be retrieved again, especially for
   destructive actions, security claims, legal/compliance claims, numeric
   decisions, or exact code edits.
7. Produce a compressed brief that can be audited against representative source
   samples.

## Expected Output

- compressed context brief
- input type inventory
- preserved constraints
- retained provenance and links
- source recheck triggers
- unresolved questions
- compression risk notes

## Verifier Expectations

- important facts remain traceable
- no new facts are invented
- provenance fields remain intact
- safety or approval requirements are not removed
- representative source samples can reconstruct the compressed claim
- exact errors, paths, line numbers, commands, and retrieval IDs are retained

## Boundary

This is a reference skill inspired by the Headroom project. It provides a
OneCode-safe compression workflow and does not copy Headroom implementation,
run Headroom tools, install proxies, expose MCP tools, or create cross-agent
memory.
