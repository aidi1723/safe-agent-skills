# Lightweight General Fallback

Date: 2026-07-03

## Summary

Reduced low-confidence `general` task packs so vague continuation requests do
not default to browser automation, web-task, sandbox, or publish-check guidance.

The regression case:

```text
可以，按照步骤，继续优化
```

now remains a low-confidence `general` task with a lightweight local fallback:

- `execution-file-batch`
- `execution-rollback-checkpoint-plan`

## What Changed

- Added a shared lightweight fallback for `general` profiles with no matched
  scenario and no matched router signals.
- Applied the same fallback to both scenario task packs and the smart mesh
  router.
- Kept explicit browser, publish, website, RAG, media, code-review, and
  skill-router signals unchanged.
- Added CLI regression coverage for scenario and smart outputs.
- Added a router-eval case:
  `unsupported-vague-stepwise-continue-optimization-lightweight`.
- Updated the router-eval baseline from 38 to 39 cases.
- Updated the full-script test baseline from 133 to 134 tests.

## Verification Targets

- `PYTHONPATH=src python3 -m unittest tests.test_registry_cli.RegistryCliTest.test_real_catalog_scenario_router_keeps_vague_general_fallback_lightweight`
- `PYTHONPATH=src python3 -m onecode_skill_sanitizer router-eval --eval evals/router-quality.json --registry catalog --bundles bundles/index.json`
- `bash scripts/verify.sh`
- `PYTHONPATH=src python3 -m onecode_skill_sanitizer maintain-check --registry catalog --bundles bundles/index.json --references external-references/index.json --claude-skills-candidate-map docs/claude-skills-candidate-map.json`
- `PYTHONPATH=src python3 -m onecode_skill_sanitizer verify --registry catalog`
- `git diff --check`

## Boundary

This update changes routing fallback behavior, eval data, regression tests, and
documentation only. It does not add external dependencies, import upstream
project code, or grant runtime, browser, network, connector, account,
credential, production, or publication permissions.
