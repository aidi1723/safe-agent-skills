---
name: office-table-source-reconciliation
description: Use when reconciling report tables, spreadsheet excerpts, copied figures, source datasets, table captions, or numeric document evidence.
---

# Office Table Source Reconciliation

## When To Use

Use this skill when a document table, spreadsheet excerpt, financial summary,
or numeric figure must be reconciled against a stated source.

## Safe Workflow

1. Identify the table, source artifact, extraction method, date, units, filters,
   and any transformations applied.
2. Compare row labels, column labels, totals, units, currencies, percentages,
   rounding, and omitted rows against the source.
3. Separate source data, copied values, calculated values, commentary, and
   formatting-only changes.
4. Flag mismatched totals, stale extracts, hidden filters, mixed units, and
   captions that overstate what the table supports.
5. Record unresolved source gaps and whether recalculation or manual review is
   needed.

## Expected Output

- table-to-source map
- mismatch list
- calculation and rounding notes
- unit and filter caveats
- reconciliation decision

## Verifier Expectations

- source artifact check
- row and column comparison
- unit and date check
- total or percentage check

## Failure Handling

If the source table is missing, label the table as unreconciled and avoid using
it as evidence for numeric claims.
