# Update Record Follow-Up Routing

Date: 2026-07-03

## Summary

Fixed a continuation-task routing gap for update-record follow-up requests.

The regression case:

```text
写好更新记录后，继续优化任务
```

now routes to `skill-router-quality-review` instead of falling back to the
low-confidence `general` task pack.

## What Changed

- Added narrow skill-router review signals for update-record continuation
  wording.
- Added focused unit coverage for the task profile classification.
- Added the same task to the real catalog scenario regression set.
- Added a reusable router-eval case:
  `skill-router-update-record-followup`.
- Updated the router-eval baseline from 36 to 37 cases.
- Updated the full-script test baseline from 131 to 132 tests.

## Verification Targets

- `PYTHONPATH=src python3 -m unittest tests.test_router.RouterTest.test_build_task_profile_routes_update_record_followup_to_skill_router_review`
- `PYTHONPATH=src python3 -m unittest tests.test_registry_cli.RegistryCliTest.test_real_catalog_scenario_router_handles_real_world_regression_set`
- `PYTHONPATH=src python3 -m onecode_skill_sanitizer router-eval --eval evals/router-quality.json --registry catalog --bundles bundles/index.json`
- `bash scripts/verify.sh`
- `PYTHONPATH=src python3 -m onecode_skill_sanitizer maintain-check --registry catalog --bundles bundles/index.json --references external-references/index.json --claude-skills-candidate-map docs/claude-skills-candidate-map.json`
- `PYTHONPATH=src python3 -m onecode_skill_sanitizer verify --registry catalog`
- `git diff --check`

## Boundary

This update changes routing signals, eval data, regression tests, and
documentation only. It does not add external dependencies, import upstream
project code, or grant runtime, browser, network, connector, account,
credential, production, or publication permissions.
