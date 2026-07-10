---
name: office-docx-brief
description: Use when drafting, editing, structuring, or reviewing Word-style documents, briefs, memos, and formatted reports.
---

# Office DOCX Brief

## When To Use

Use this skill when preparing a structured document such as a memo, project
brief, proposal, policy note, or formatted report.

## Safe Workflow

1. Identify audience, purpose, required sections, and formatting constraints.
2. Build a concise outline before writing detailed content.
3. Preserve source facts and mark assumptions.
4. Keep headings, tables, and lists readable after export.
5. Verify final content against the requested sections.

## Decision Guidance

Classify the task as `draft`, `edit`, `format`, or `review`. Drafting creates a
new structure from approved requirements and sourced facts. Editing changes
content while preserving intended meaning, tracked boundaries, and existing
document conventions. Formatting applies styles and layout without silently
rewriting content. Review identifies content, structure, consistency, and
rendering issues without claiming to have modified the artifact.

Prefer semantic styles for headings, body text, captions, lists, and tables
instead of direct formatting. Treat headers, footers, page breaks, section
breaks, references, comments, tracked changes, fields, and embedded objects as
part of the document contract when present. A produced DOCX requires rendered
inspection because XML or extracted text cannot prove pagination and layout.

## Evidence Minimum

- approved input/output files, audience, purpose, required sections, and format
- source facts, citations, assumptions, and content that must remain unchanged
- outline and semantic style map for headings, body, lists, tables, and captions
- headers/footers, sections, page numbering, references, and tracked boundaries
- rendered page evidence for tables, spacing, pagination, clipping, and overflow
- reopened file, section completeness, spelling, links, and export result
- inferred requirements, unsupported facts, layout risks, and unreviewed objects

## References

Load [the DOCX delivery evidence guide](references/docx-delivery-evidence.md)
for generated documents, complex styles, tables, headers/footers, page layout,
references, comments, tracked content, or export-sensitive delivery.

## Expected Output

- document outline
- drafted or revised sections
- source and assumption notes
- formatting checks

## Verifier Expectations

- section completeness check
- source fact check
- layout or render check when a file is produced
- spelling and consistency pass

## Failure Handling

If the document requirements are incomplete, infer a minimal structure and mark
the inference. Preserve originals and do not claim layout quality without a
rendered check when a file is produced. Generated content is not automatically
verified source material.
