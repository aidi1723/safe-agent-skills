---
name: office-spreadsheet-cleanup
description: Use when cleaning, reviewing, formatting, or summarizing spreadsheets, CSV files, tables, and business data sheets.
---

# Office Spreadsheet Cleanup

## When To Use

Use this skill when a table or spreadsheet needs cleanup, formatting,
summarization, or sanity checks before business use.

## Safe Workflow

1. Identify the file, sheet, columns, row count, and intended output.
2. Check headers, missing values, duplicates, formats, and suspicious outliers.
3. Preserve original data unless the user requests a transformed artifact.
4. Summarize changes and keep a clear before or after note.
5. Validate formulas, totals, and filters when applicable.

## Expected Output

- data quality findings
- cleanup actions
- summary table
- formula or total checks

## Verifier Expectations

- row and column count check
- duplicate and missing value check
- formula review when relevant
- output format check

## Failure Handling

If the input format cannot be parsed, report the exact file and parser blocker.
