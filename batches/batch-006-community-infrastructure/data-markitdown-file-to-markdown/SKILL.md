---
name: data-markitdown-file-to-markdown
description: Use when converting mixed office files, documents, or local assets into clean Markdown for agent workflows.
---

# Data MarkItDown File To Markdown

## When To Use

Use this skill when an agent needs a simple text representation of files before
summarization, indexing, editing, or review.

## Safe Workflow

1. Confirm the input file list and allowed workspace scope.
2. Convert only declared files and keep generated Markdown separate from source
   files unless in-place output is requested.
3. Preserve headings, links, tables, captions, and file provenance.
4. Flag unsupported file types, conversion gaps, and low-confidence sections.
5. Review representative Markdown output before downstream agent use.

## Expected Output

- input file list
- generated Markdown paths
- retained structure notes
- skipped or unsupported files
- sample quality review

## Verifier Expectations

- file scope check
- output path check
- sample Markdown review
- source provenance check

## Failure Handling

If conversion loses critical structure, keep the original file reference and
request manual review before using the Markdown.

## Boundary

This is a reference skill inspired by Microsoft MarkItDown. It documents safe
file-to-Markdown workflow patterns and does not bundle converter code.
