# Tabular Analysis Evidence

Use this guide for reproducible analysis of structured rows and columns.

## Source And Grain

Record source identity, schema, row/column counts, grain, candidate keys,
freshness, units, date/time conventions, and sensitive fields. Preserve the
original and identify missing, duplicate, invalid, or outlier records.

## Transformations

Document filters, joins and cardinality, type coercion, null handling,
deduplication, derived fields, grouping, unit or currency conversion, and
outlier policy. Make each transformation reproducible and count affected rows.

## Metrics And Reconciliation

Define measures, dimensions, denominators, baselines, comparison periods, and
uncertainty. Reconcile aggregates to source totals or an independent method and
explain discrepancies rather than forcing agreement.

## Output

Record output identity, shape, checksums or diffs, validation results, excluded
data, limitations, and why conclusions do not exceed the available evidence.
