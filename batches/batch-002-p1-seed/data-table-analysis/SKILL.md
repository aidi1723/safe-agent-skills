---
name: data-table-analysis
description: Use when cleaning, summarizing, validating, or explaining tabular datasets inside an approved workspace.
---

# Data Table Analysis

## When To Use

Use this skill when the task involves CSV, spreadsheet, database export,
metrics table, or structured data that needs analysis or validation.

## Safe Workflow

1. Identify the input files, schema, row counts, and key columns.
2. Inspect missing values, duplicates, data types, and outliers before analysis.
3. Keep transformations reproducible and describe them clearly.
4. Check aggregate totals against source totals when available.
5. Avoid uploading private data to external services.
6. Present conclusions with caveats about data quality.

## Expected Output

- input summary
- data quality notes
- analysis results
- reproducible transformation notes
- assumptions and limitations

## Verifier Expectations

- schema validation
- row count check
- aggregate consistency check
- output diff or generated report check

## Failure Handling

If data is incomplete or inconsistent, report the issue and avoid unsupported
conclusions.
