---
name: data-qdrant-vector-retrieval
description: Use when reviewing vector search, embedding indexes, retrieval filters, similarity results, or RAG database boundaries.
---

# Data Qdrant Vector Retrieval

## When To Use

Use this skill when an agent or RAG system needs vector search, embedding
storage, metadata filters, similarity review, or retrieval quality checks.

## Safe Workflow

1. Identify indexed data, embedding model, metadata fields, and retention
   policy.
2. Separate retrieval relevance from factual correctness.
3. Define filters, namespaces, and access boundaries before query use.
4. Review sample nearest-neighbor results for quality and leakage.
5. Record index freshness, deletion rules, and privacy limits.

## Expected Output

- vector index boundary
- metadata and filter plan
- retrieval quality notes
- privacy and retention notes
- sample query checks

## Verifier Expectations

- source data provenance check
- metadata filter check
- sample retrieval review
- privacy and deletion policy check

## Failure Handling

If retrieval results are noisy or leak unrelated data, keep the index out of
trusted answers until filters and source boundaries are fixed.

## Boundary

This is a reference skill inspired by Qdrant. It documents vector retrieval
review patterns and does not bundle vector database code or cloud access.
