---
name: data-quality-audit
description: Use when checking datasets for missing values, duplicates, schema drift, outliers, freshness, and readiness for analysis.
---

# Data Quality Audit

## When To Use

Use this skill when a dataset must be checked before analysis, modeling,
reporting, or import.

## Safe Workflow

1. Identify data source, schema, row count, column count, and expected use.
2. Check missing values, duplicates, type mismatch, outliers, and stale records.
3. Preserve original data and propose transformations separately.
4. Record assumptions and data gaps.
5. Produce a readiness decision for the next workflow.

## Expected Output

- data profile
- quality issue table
- recommended cleanup
- readiness status

## Verifier Expectations

- schema check
- row and column count check
- missing and duplicate check
- source freshness check

## Failure Handling

If the dataset is too large to fully inspect, sample deterministically and state
the sampling method.
