---
name: research-source-lineage-trace
description: Use when tracing claims back to sources, checking citation lineage, reviewing summaries, or preventing unsupported research assertions.
---

# Research Source Lineage Trace

## When To Use

Use this skill when research notes, summaries, briefs, or knowledge-base
entries must preserve the source chain behind important claims.

## Safe Workflow

1. Extract the key claims, named entities, dates, figures, and causal
   statements that need source support.
2. Map each claim to a primary source, official document, paper, filing, direct
   dataset, or clearly labeled secondary source.
3. Preserve publisher, publication date, access date, URL or local path, and
   quoted or paraphrased evidence location.
4. Mark inference separately from sourced fact, especially when multiple claims
   are compressed into one sentence.
5. Flag missing sources, stale sources, circular citations, and source chains
   that end in summaries instead of evidence.

## Expected Output

- claim-to-source map
- source lineage notes
- unsupported claim list
- stale or weak source warnings
- separated facts and inferences

## Verifier Expectations

- citation presence check
- source type check
- date and publisher check
- claim-to-evidence mapping check

## Failure Handling

If a claim cannot be traced to a reliable source, keep it out of trusted
summary output or label it explicitly as unverified.
