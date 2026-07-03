# Router Quality Summary

Date: 2026-07-03

## Summary

Added deterministic aggregate quality metrics to `router-eval` so router
quality is visible beyond total pass/fail counts and individual case rows.

`router-eval` output now includes a `quality_summary` object with:

- total, passed, and failed case counts;
- pass/fail counts grouped by expected scenario;
- pass/fail counts grouped by actual scenario;
- pass/fail counts grouped by expected task type;
- issue counts grouped by structured `router-eval-*` issue id.

## What Changed

- Added `build_router_eval_quality_summary` as a pure aggregation helper over
  existing per-case results.
- Kept `schema_version: 1` and all existing case-level fields unchanged, so
  current JSON consumers remain compatible.
- Normalized empty or missing scenario/task-type buckets to explicit summary
  labels such as `(none)` and `(unspecified)`.
- Counted both case-level issues and top-level eval issues in
  `quality_summary.by_issue`.
- Added regression coverage for mixed pass/fail eval output with deterministic
  scenario, task-type, and issue-id buckets.

## Verification Targets

- `PYTHONPATH=src python3 -m unittest tests.test_registry_cli.RegistryCliTest.test_router_eval_reports_quality_summary_by_scenario_task_type_and_issue`
- `PYTHONPATH=src python3 -m unittest tests.test_registry_cli.RegistryCliTest.test_router_eval_passes_expected_scenario_cases tests.test_registry_cli.RegistryCliTest.test_router_eval_fails_unexpected_scenario_case tests.test_registry_cli.RegistryCliTest.test_router_eval_reports_quality_summary_by_scenario_task_type_and_issue tests.test_registry_cli.RegistryCliTest.test_router_eval_fails_forbidden_skills_prefixes_subcategories_and_skill_count_limit tests.test_registry_cli.RegistryCliTest.test_router_eval_rejects_invalid_constraint_field_types tests.test_registry_cli.RegistryCliTest.test_router_eval_rejects_invalid_expectation_field_types tests.test_registry_cli.RegistryCliTest.test_router_eval_rejects_invalid_control_field_types tests.test_registry_cli.RegistryCliTest.test_real_router_eval_file_covers_current_catalog_scenarios`
- `PYTHONPATH=src python3 -m onecode_skill_sanitizer router-eval --eval evals/router-quality.json --registry catalog --bundles bundles/index.json`
- `bash scripts/verify.sh`
- `PYTHONPATH=src python3 -m onecode_skill_sanitizer maintain-check --registry catalog --bundles bundles/index.json --references external-references/index.json --claude-skills-candidate-map docs/claude-skills-candidate-map.json`
- `PYTHONPATH=src python3 -m onecode_skill_sanitizer verify --registry catalog`
- `git diff --check`

## Boundary

This update changes router evaluation reporting, tests, and documentation
only. It does not change router selection behavior, catalog trust state,
runtime permissions, external imports, network access, browser automation,
connectors, credentials, production systems, or publication authority.

Remaining router-quality work includes explicit false-positive /
false-negative classification fields, low-confidence trend tracking, and
broader documentation consolidation for historical baselines.
