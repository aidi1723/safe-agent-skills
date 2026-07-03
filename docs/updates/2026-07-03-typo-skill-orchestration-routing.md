# Typo Skill Orchestration Routing

Date: 2026-07-03

## Summary

Fixed a real conversation routing gap for typo-prone skill orchestration
requests.

The regression case is:

```text
继续，优化和编排sikll，继续补充和优化，做好记录和测试
```

This task now routes to `skill-router-quality-review` instead of
`code-review-hardening`.

## What Changed

- Adjusted task-text normalization so alias replacements such as `sikll` ->
  `skill` do not duplicate the replacement target during signal normalization.
- Added focused unit coverage for typo-prone skill orchestration follow-up
  requests.
- Added the same task to the real-world regression set.
- Added a reusable router-eval case for the same task.
- Updated public baseline records from 35 to 36 router eval cases and from 130
  to 131 full-script tests.

## Verification Targets

- `PYTHONPATH=src python3 -m unittest tests.test_router.RouterTest.test_build_task_profile_routes_typo_skill_orchestration_followup_to_skill_router_review`
- `PYTHONPATH=src python3 -m unittest tests.test_registry_cli.RegistryCliTest.test_real_catalog_scenario_router_handles_real_world_regression_set`
- `PYTHONPATH=src python3 -m onecode_skill_sanitizer router-eval --eval evals/router-quality.json --registry catalog --bundles bundles/index.json`
- `bash scripts/verify.sh`
- `PYTHONPATH=src python3 -m onecode_skill_sanitizer maintain-check --registry catalog --bundles bundles/index.json --references external-references/index.json --claude-skills-candidate-map docs/claude-skills-candidate-map.json`
- `PYTHONPATH=src python3 -m onecode_skill_sanitizer verify --registry catalog`
- `git diff --check`

## Boundary

This update changes normalization, routing eval data, regression tests, and
documentation only. It does not add external dependencies, import upstream
project code, or grant runtime, browser, network, connector, account,
credential, production, or publication permissions.
