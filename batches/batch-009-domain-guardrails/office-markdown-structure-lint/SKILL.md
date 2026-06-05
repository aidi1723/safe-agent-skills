---
name: office-markdown-structure-lint
description: Use when reviewing Markdown, documentation, briefs, generated reports, or knowledge-base pages for heading structure, broken tables, links, frontmatter, or format consistency.
---

# Office Markdown Structure Lint

## When To Use

Use this skill before publishing or indexing Markdown documents, generated
reports, README updates, knowledge-base pages, or converted office content.

## Safe Workflow

1. Identify the expected document type, frontmatter needs, link policy, and
   heading structure.
2. Check that headings do not skip levels, tables are parseable, lists are
   consistent, and code fences are closed.
3. Verify links, anchors, image references, and local file paths when possible.
4. Separate structural lint issues from editorial style preferences.
5. Provide minimal fixes that preserve document meaning.

## Expected Output

- structure findings
- heading and table issues
- broken link or asset notes
- suggested fixes
- remaining publication risks

## Verifier Expectations

- heading hierarchy check
- table parseability check
- link or asset reference check
- Markdown formatting check

## Failure Handling

If linked targets cannot be accessed, record which references were unchecked
instead of treating them as valid.
