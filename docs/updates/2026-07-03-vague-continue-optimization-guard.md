# Vague Continue Optimization Guard

Date: 2026-07-03

## Summary

Tightened the update-record follow-up routing fix so vague continuation
requests do not overmatch `skill-router-quality-review`.

The negative regression case:

```text
继续优化任务
```

now remains a low-confidence `general` task instead of being routed to
`skill-router-quality-review`.

The more specific update-record follow-up remains covered:

```text
写好更新记录后，继续优化任务
```

## What Changed

- Removed the broad `继续优化任务` signal from the skill-router review profile.
- Kept the narrower `写好更新记录` and `更新记录后` signals.
- Added focused unit coverage for the vague continuation guard.
- Added real catalog regression coverage for the same negative case.
- Added a reusable router-eval case:
  `unsupported-vague-continue-optimization`.
- Updated the router-eval baseline from 37 to 38 cases.
- Updated the full-script test baseline from 132 to 133 tests.

## Verification Targets

- `PYTHONPATH=src python3 -m unittest tests.test_router.RouterTest.test_build_task_profile_does_not_route_vague_continue_optimization_to_skill_router_review`
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
