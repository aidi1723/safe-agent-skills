---
name: data-table-calculation-verify
description: Use when checking tables, spreadsheets, reports, financial summaries, percentages, totals, averages, or numeric claims for calculation consistency.
---

# Data Table Calculation Verify

## When To Use

Use this skill when generated or edited content includes tables, totals,
percentages, averages, ratios, financial figures, or metric summaries.

## Safe Workflow

1. Identify numeric columns, units, time periods, filters, and stated formulas.
2. Recalculate totals, subtotals, averages, percentages, deltas, and ratios from
   the visible source values.
3. Compare calculated values with written claims and table summaries.
4. Flag rounding differences separately from material calculation errors.
5. Record assumptions when source rows, formulas, or units are incomplete.

## Expected Output

- calculation check summary
- mismatched totals or percentages
- rounding notes
- source data assumptions
- corrected values or escalation questions

## Verifier Expectations

- row and column inventory check
- formula or calculation check
- unit and rounding check
- claim-to-table consistency check

## Failure Handling

If source rows or formulas are missing, avoid recalculating hidden values and
request the missing data before approving numeric claims.
