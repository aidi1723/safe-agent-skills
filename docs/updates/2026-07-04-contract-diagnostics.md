# Contract Diagnostics

Date: 2026-07-04

## Summary

Added first-class contract diagnostics to routed task packs.

The router can now surface missing preconditions, explicit skill exclusions,
and contract graph fallback or cycle issues as machine-readable output instead
of leaving those risks implicit in selected skill text.

## What Changed

- Added `contract_diagnostics` to scenario and mesh routed outputs.
- Added missing precondition detection from `contract.requires_context`.
- Treated external task inputs such as `task_brief`, `user_request`,
  `workspace_context`, and `operator_input` as host-provided context rather
  than missing skill artifacts.
- Added collision diagnostics from:
  - `contract.conflicts_with`
  - `contract.excludes`
- Added schema support for `contract.excludes`.
- Added `Contract diagnostics` to task-pack Markdown and agent instructions.

## Output Shape

```json
{
  "schema_version": 1,
  "status": "ok",
  "graph_mode": "contract",
  "fallback_reason": "",
  "missing_precondition_count": 0,
  "missing_preconditions": [],
  "collision_count": 0,
  "collisions": [],
  "graph_issue_count": 0,
  "graph_issues": []
}
```

## Verification Targets

- `PYTHONPATH=src python3 -m unittest tests.test_router.RouterTest.test_build_contract_diagnostics_reports_missing_preconditions_and_collisions`
- `PYTHONPATH=src python3 -m unittest tests.test_registry_cli.RegistryCliTest.test_schema_check_validates_optional_contract_shape`
- `PYTHONPATH=src python3 -m onecode_skill_sanitizer router-eval --eval evals/router-quality.json --registry catalog --bundles bundles/index.json`
- `bash scripts/verify.sh`
- `git diff --check`

## Boundary

This update changes routing diagnostics and schema validation only. It does not
grant runtime permissions, execute skills, import external content, invoke
connectors, run browser automation, or change trust status.

Remaining non-blocking work now focuses on host semantic gateway integration,
networked source-import automation, and documentation consolidation.
