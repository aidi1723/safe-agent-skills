---
name: office-pdf-report
description: Use when extracting, reviewing, summarizing, or checking PDF reports inside an approved workspace.
---

# PDF Report Workflow

## When To Use

Use this skill when the task involves a PDF report, document review, extraction,
summary, layout check, or evidence-backed office output.

## Safe Workflow

1. Confirm the exact PDF files provided by the user.
2. Inspect only files inside the approved workspace or explicitly supplied paths.
3. Extract text and metadata before summarizing.
4. Use visual rendering when layout, tables, or signatures matter.
5. Cite page numbers or extracted sections when making claims.
6. Report extraction gaps, unreadable pages, or layout uncertainty.

## Expected Output

- concise summary or structured report
- page references for key claims
- extraction or rendering verification notes

## Verifier Expectations

- text extraction check
- render check for layout-sensitive files
- output format check

## Failure Handling

If the document cannot be opened or rendered, report the specific file and
failure mode.
