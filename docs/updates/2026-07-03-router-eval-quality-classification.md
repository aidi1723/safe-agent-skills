# Router Eval Quality Classification

Date: 2026-07-03

## Summary

Extended `router-eval` quality reporting with explicit issue classification
and low-confidence trend fields.

This closes the next router-quality slice from the delivery follow-up:
false-positive / false-negative classification and low-confidence route
tracking are now machine-readable in the eval output.

## What Changed

- Added `classification` to router-eval case issues.
- Added `quality_summary.by_issue_class` with deterministic buckets:
  - `false_positive`
  - `false_negative`
  - `route_mismatch`
  - `task_type_mismatch`
  - `eval_contract`
  - `unclassified`
- Added confidence trend fields to every routed eval case:
  - `actual_confidence`
  - `actual_low_confidence`
- Added quality summary low-confidence counters:
  - `low_confidence_case_count`
  - `low_confidence_passed_count`
  - `low_confidence_failed_count`
  - `by_confidence`
- Kept routing behavior unchanged. This update changes reporting and
  verification visibility only.

## Verification

- Added failing-first regression coverage:
  `test_router_eval_reports_issue_classification_and_low_confidence_trend`.
- Targeted router-eval test group passes: 9 / 9.
- Real catalog router eval passes: 39 / 39 cases.

Current real eval quality summary:

```text
router-eval: 39 / 39 cases OK
by_confidence.high: 36 passed, 0 failed
by_confidence.low: 3 passed, 0 failed
low_confidence_case_count: 3
low_confidence_failed_count: 0
by_issue_class: {}
```

## Boundary

This update does not change scenario selection, skill trust status, catalog
contents, external imports, network access, browser automation, connectors,
runtime permissions, or publication authority.

Remaining non-blocking follow-up now moves to first-class skill preconditions,
exclusions, collision diagnostics, host semantic gateway integration, networked
source-import automation, and documentation consolidation.
