---
name: data-marker-pdf-markdown-review
description: Use when reviewing PDF-to-Markdown extraction quality, layout preservation, table handling, or OCR uncertainty.
---

# Data Marker PDF Markdown Review

## When To Use

Use this skill when a PDF conversion result must be checked for clean Markdown,
table fidelity, page continuity, formulas, images, or OCR uncertainty.

## Safe Workflow

1. Identify source PDF, page range, document owner, and output purpose.
2. Compare representative pages against generated Markdown.
3. Check headings, tables, footnotes, equations, images, and page breaks.
4. Mark uncertain OCR or layout regions instead of treating them as facts.
5. Keep license and publication limits visible when extracted text is reused.

## Expected Output

- conversion quality summary
- page or section issue list
- table and layout notes
- uncertain OCR markers
- reuse boundary notes

## Verifier Expectations

- sample page comparison
- table structure check
- OCR uncertainty check
- license and source record check

## Failure Handling

If critical sections cannot be verified, keep them out of automated summaries
and request manual inspection.

## Boundary

This is a reference skill inspired by Marker. It documents PDF-to-Markdown
review patterns only and does not copy GPL project code or bundle converters.
