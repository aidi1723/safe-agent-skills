# Skill Router Execution Order

Date: 2026-07-03

## Summary

Improved `skill-router-quality-review` selection output and execution order so
agents see and execute skills in the same stage-aware order.

For skill-router quality tasks, the effective order is now:

```text
preflight -> planning -> review -> verification -> handoff
```

## What Changed

- Moved `security-supply-chain-review` into the Review stage for
  `skill-router-quality-review`.
- Kept `ai-rule-failure-log-synthesis` in Handoff so failure/rule synthesis
  happens after verification evidence exists.
- Reordered the `skill-router-quality-review` bundle execution order so
  supply-chain review runs before regression/CI checks and failure synthesis
  runs after them.
- Reordered smart-router `skills` output with the same scenario stage map used
  by the pipeline plan and execution plan.
- Added regression assertions for both selected-skill order and execution-plan
  order.

## Verification Targets

- `PYTHONPATH=src python3 -m unittest tests.test_registry_cli.RegistryCliTest.test_real_catalog_smart_router_selects_skill_router_quality_review_bundle`
- `PYTHONPATH=src python3 -m unittest tests.test_router.RouterTest.test_build_pipeline_plan_for_skill_router_quality_review`
- `PYTHONPATH=src python3 -m onecode_skill_sanitizer router-eval --eval evals/router-quality.json --registry catalog --bundles bundles/index.json`
- `bash scripts/verify.sh`
- `PYTHONPATH=src python3 -m onecode_skill_sanitizer maintain-check --registry catalog --bundles bundles/index.json --references external-references/index.json --claude-skills-candidate-map docs/claude-skills-candidate-map.json`
- `PYTHONPATH=src python3 -m onecode_skill_sanitizer verify --registry catalog`
- `git diff --check`

## Boundary

This update changes routing order, bundle order, pipeline-stage assignment,
regression tests, and documentation only. It does not add external
dependencies, import upstream project code, or grant runtime, browser, network,
connector, account, credential, production, or publication permissions.
