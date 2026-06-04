---
name: data-unstructured-document-partition
description: Use when transforming complex documents into clean chunks, structured records, or retrieval-ready text.
---

# Data Unstructured Document Partition

## When To Use

Use this skill when PDFs, office files, web pages, or mixed documents must be
partitioned into clean text blocks before summarization, RAG, search, or import.

## Safe Workflow

1. Identify document type, source, owner, and allowed processing scope.
2. Preserve titles, tables, sections, page references, and metadata when useful.
3. Separate extraction errors from content meaning.
4. Normalize chunks for downstream retrieval without hiding missing pages or
   low-confidence extraction.
5. Record privacy and license limits before publishing extracted text.

## Expected Output

- document inventory
- chunking or partition plan
- metadata retention notes
- extraction quality issues
- downstream use recommendation

## Verifier Expectations

- source file scope check
- metadata preservation check
- sample chunk review
- privacy and license check

## Failure Handling

If extraction quality is low, keep original references and report uncertain
sections instead of inventing cleaned content.

## Boundary

This is a reference skill inspired by Unstructured. It documents document
partitioning patterns and does not bundle ETL libraries or external services.
