# Project Release Follow-Up Routing

Date: 2026-07-03

## Summary

Added routing protection for project maintenance follow-up tasks that mention
changelogs, GitHub update notes, verification, publication, or closure reports.

The regression case is:

```text
继续项目复查收尾，写好更新日志和 GitHub 更新说明，验证后发布
```

This task now routes to `skill-router-quality-review` instead of being
misclassified as `website-build-launch` by broad publish-related signals.

## What Changed

- Added Chinese and mixed-language project closure signals to the
  `skill_router_review` profile.
- Added dynamic `publish_check` capability for skill-router review tasks that
  explicitly mention release notes, changelogs, GitHub update notes,
  publication, or closure.
- Added optional `execution-publish-check` guidance to the
  `skill-router-quality-review` bundle.
- Added focused unit, real-world scenario, and reusable router-eval coverage.
- Updated public baseline records from 34 to 36 router eval cases and from 129
  to 131 full-script tests after the same-day typo skill orchestration routing
  follow-up.

## Verification Targets

- `PYTHONPATH=src python3 -m unittest tests.test_router.RouterTest.test_build_task_profile_routes_project_release_followup_to_skill_router_review`
- `PYTHONPATH=src python3 -m unittest tests.test_registry_cli.RegistryCliTest.test_real_catalog_scenario_router_handles_real_world_regression_set`
- `PYTHONPATH=src python3 -m onecode_skill_sanitizer router-eval --eval evals/router-quality.json --registry catalog --bundles bundles/index.json`
- `bash scripts/verify.sh`
- `PYTHONPATH=src python3 -m onecode_skill_sanitizer maintain-check --registry catalog --bundles bundles/index.json --references external-references/index.json --claude-skills-candidate-map docs/claude-skills-candidate-map.json`
- `PYTHONPATH=src python3 -m onecode_skill_sanitizer verify --registry catalog`
- `git diff --check`

## Boundary

This update changes routing, bundle composition, eval data, regression tests,
and documentation only. It does not add external dependencies, import upstream
project code, or grant runtime, browser, network, connector, account,
credential, production, or publication permissions.
