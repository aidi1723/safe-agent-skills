# Router Eval Constraint Schema

Date: 2026-07-03

## Summary

Hardened `router-eval` so invalid constraint field types fail as structured
eval issues before task-pack generation.

Eval case fields now require:

- `expected_scenario`: string when present
- `expected_task_type`: string when present
- `expected_skills`: array of strings
- `forbidden_skills`: array of strings
- `forbidden_skill_prefixes`: array of strings
- `forbidden_skill_subcategories`: array of strings
- `max_skill_count`: non-negative integer

## What Changed

- Added `router-eval-invalid-case-field` failures for malformed constraint
  fields.
- Added the same structured failures for malformed expected scenario and task
  type fields.
- Rejected negative, boolean, or non-integer `max_skill_count` values before
  selection comparison.
- Prevented malformed prefix or subcategory constraints from raising runtime
  type errors during evaluation.
- Prevented malformed scenario or task-type expectations from being reported
  as normal mismatch failures.
- Added regression coverage for invalid constraint and expectation field types.

## Verification Targets

- `PYTHONPATH=src python3 -m unittest tests.test_registry_cli.RegistryCliTest.test_router_eval_rejects_invalid_constraint_field_types`
- `PYTHONPATH=src python3 -m unittest tests.test_registry_cli.RegistryCliTest.test_router_eval_rejects_invalid_expectation_field_types`
- `PYTHONPATH=src python3 -m unittest tests.test_registry_cli.RegistryCliTest.test_router_eval_passes_expected_scenario_cases tests.test_registry_cli.RegistryCliTest.test_router_eval_fails_unexpected_scenario_case tests.test_registry_cli.RegistryCliTest.test_router_eval_fails_forbidden_skills_prefixes_subcategories_and_skill_count_limit tests.test_registry_cli.RegistryCliTest.test_router_eval_rejects_invalid_constraint_field_types tests.test_registry_cli.RegistryCliTest.test_real_router_eval_file_covers_current_catalog_scenarios`
- `PYTHONPATH=src python3 -m onecode_skill_sanitizer router-eval --eval evals/router-quality.json --registry catalog --bundles bundles/index.json`
- `bash scripts/verify.sh`
- `PYTHONPATH=src python3 -m onecode_skill_sanitizer maintain-check --registry catalog --bundles bundles/index.json --references external-references/index.json --claude-skills-candidate-map docs/claude-skills-candidate-map.json`
- `PYTHONPATH=src python3 -m onecode_skill_sanitizer verify --registry catalog`
- `git diff --check`

## Boundary

This update changes deterministic eval schema validation, regression tests, and
documentation only. It does not change router matching behavior, import
external code, or grant browser, network, connector, account, credential,
production, or publication access.
