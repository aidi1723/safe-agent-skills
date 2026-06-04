---
name: ai-llamaindex-rag-knowledge-workflow
description: Use when designing RAG, document agents, knowledge indexing, citation retrieval, or OCR-backed knowledge workflows.
---

# AI LlamaIndex RAG Knowledge Workflow

## When To Use

Use this skill when documents, files, knowledge bases, or OCR outputs must be
indexed and retrieved for grounded agent answers.

## Safe Workflow

1. Identify source documents, owners, licenses, freshness, and privacy limits.
2. Choose indexing units: document, section, page, table, or semantic chunk.
3. Preserve metadata needed for citations and audit trails.
4. Separate retrieved evidence from generated interpretation.
5. Verify answer claims against retrieved source references.

## Expected Output

- knowledge source inventory
- indexing and chunking plan
- retrieval and citation policy
- answer grounding checklist
- freshness and privacy notes

## Verifier Expectations

- source provenance check
- citation check
- retrieval sample review
- privacy boundary check

## Failure Handling

If retrieved context is insufficient, report the source gap instead of filling
the answer with unsupported claims.

## Boundary

This is a reference skill inspired by LlamaIndex. It documents knowledge and
RAG workflow patterns and does not bundle runtime code or indexes.
