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

## Decision Guidance

Classify the task as `text_extraction`, `content_review`, `layout_review`, or
`artifact_generation`. Text extraction may rely on parsed text when page order
and characters are verified. Content review requires page-level evidence for
material claims. Layout review requires rendered pages because extracted text
cannot prove tables, columns, signatures, forms, clipping, or visual order.
Artifact generation must preserve source identity and verify the produced file
through extraction plus rendering.

Use OCR only for image-only or materially incomplete pages, and identify which
pages used it. Treat OCR output, table reconstruction, handwritten content,
signatures, and damaged pages as uncertain until visually checked. Never infer
that a signature is authentic or a form is complete from appearance alone.

## Evidence Minimum

- approved input path, filename, checksum or identity, page count, and metadata
- extraction method, OCR pages, parsing warnings, and unreadable content
- rendered evidence for layout, tables, forms, signatures, or generated output
- page numbers and exact sections supporting material claims
- table row/column checks and order reconstruction when applicable
- output file identity, page count, text check, and visual verification
- encryption, corruption, missing pages, uncertainty, and unverified elements

## References

Load [the PDF evidence and rendering guide](references/pdf-evidence-rendering-guide.md)
for scanned documents, OCR, complex tables, forms, signatures, multi-column
layouts, damaged files, page-level citations, or generated PDF artifacts.

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
failure mode. Preserve the original, stay within approved paths, and do not
claim layout, signature, or form correctness from text extraction alone.
