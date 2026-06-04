---
name: data-haystack-rag-pipeline
description: Use when reviewing modular RAG pipelines, retrieval routing, semantic search, memory, or production LLM application flows.
---

# Data Haystack RAG Pipeline

## When To Use

Use this skill when a RAG or LLM application needs modular retrieval,
generation, routing, memory, and evaluation stages.

## Safe Workflow

1. Identify documents, retrievers, rankers, generators, memory, and output
   validators.
2. Define the pipeline order and what each component is allowed to see.
3. Keep retrieval confidence and generation confidence separate.
4. Add evaluation checks for grounding, citation, latency, and failure cases.
5. Record production readiness gaps before release.

## Expected Output

- RAG pipeline map
- component boundary notes
- grounding and citation checks
- evaluation plan
- production readiness gaps

## Verifier Expectations

- source and retriever check
- citation and grounding check
- pipeline component check
- evaluation and latency check

## Failure Handling

If the pipeline cannot ground answers reliably, keep outputs advisory and
report which stage failed.

## Boundary

This is a reference skill inspired by Haystack. It documents modular RAG
pipeline review patterns and does not bundle orchestration code.
