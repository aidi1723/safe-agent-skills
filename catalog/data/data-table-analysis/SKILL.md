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

## Decision Guidance

Classify the task as `profile`, `clean`, `analyze`, or `reconcile`. Profiling
describes schema, keys, counts, missingness, duplicates, distributions, and
quality without changing data. Cleaning creates an explicit transformation
from preserved source data. Analysis answers a defined question with named
metrics, dimensions, filters, units, and denominators. Reconciliation compares
independent totals or records and explains remaining differences.

Validate grain and key uniqueness before joins or aggregation. Check join
cardinality, filter effects, type coercion, date/time zones, currency and unit
conversion, null handling, denominators, and outlier policy. Distinguish
descriptive association from causal claims, and do not hide excluded records or
quality limitations behind a single summary metric.

## Evidence Minimum

- approved source files, schema, grain, keys, row/column counts, and freshness
- missingness, duplicates, types, invalid values, outliers, and excluded rows
- joins, filters, grouping, units, denominators, date/time and conversion rules
- reproducible transformation steps with preserved source data
- source totals and independent aggregate or record reconciliation
- analysis question, metric definitions, uncertainty, and quality limitations
- output identity, row/column counts, checksums or diffs, and privacy boundary

## References

Load [the tabular analysis evidence guide](references/tabular-analysis-evidence.md)
for joins, multi-file inputs, financial or operational totals, time series,
unit conversion, complex cleaning, reconciliation, or sensitive data.

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
conclusions. Preserve source data, keep cleaning separate from analysis, avoid
unsupported causality, and do not upload private data to external services
without explicit approval.
