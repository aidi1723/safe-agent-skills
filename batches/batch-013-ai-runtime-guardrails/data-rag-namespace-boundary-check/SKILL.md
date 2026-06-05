---
name: data-rag-namespace-boundary-check
description: Use when reviewing RAG namespaces, vector index filters, retrieval scopes, metadata boundaries, tenant isolation, or grounded answer source limits.
---

# Data RAG Namespace Boundary Check

## When To Use

Use this skill when a RAG workflow, vector index, or retrieval layer must keep
data sources, tenants, projects, or document classes separated.

## Safe Workflow

1. Identify indexed sources, namespace keys, metadata fields, access groups,
   freshness rules, and deletion requirements.
2. Check that retrieval filters match the user, task, project, document type,
   and allowed source boundary.
3. Separate retrieval relevance from factual correctness and source authority.
4. Review sample nearest matches for leakage across namespaces, stale content,
   weak metadata, and missing citations.
5. Record index freshness, retention limits, and fallback behavior when
   retrieval is empty or low confidence.

## Expected Output

- namespace boundary map
- metadata filter checklist
- sample retrieval review
- leakage or stale-source risks
- citation and freshness notes

## Verifier Expectations

- namespace filter check
- metadata completeness check
- sample retrieval check
- citation boundary check

## Failure Handling

If namespace or metadata filters are unclear, do not treat retrieval output as
trusted evidence until the boundary is defined and sample results are reviewed.
