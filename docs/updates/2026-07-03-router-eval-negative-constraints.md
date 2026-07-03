# Router Eval Negative Constraints

Date: 2026-07-03

## Summary

Deepened router quality evaluation so `router-eval` can now assert both
positive and negative selection constraints.

Eval cases can now include:

- `forbidden_skills`: skills that must not appear in the selected task pack.
- `max_skill_count`: the maximum allowed selected-skill count for a case.

## What Changed

- Added `router-eval-forbidden-skill` failures when a selected pack includes a
  forbidden skill.
- Added `router-eval-max-skill-count-exceeded` failures when a selected pack is
  larger than the case allows.
- Upgraded vague `general` fallback eval cases with forbidden browser,
  Playwright, and publish skills.
- Kept scenario selection and positive expected-skill checks unchanged.
- Added focused CLI regression coverage for the new negative constraints.
- Updated the full-script test baseline from 134 to 135 tests.

## Verification Targets

- `PYTHONPATH=src python3 -m unittest tests.test_registry_cli.RegistryCliTest.test_router_eval_fails_forbidden_skills_and_skill_count_limit`
- `PYTHONPATH=src python3 -m onecode_skill_sanitizer router-eval --eval evals/router-quality.json --registry catalog --bundles bundles/index.json`
- `bash scripts/verify.sh`
- `PYTHONPATH=src python3 -m onecode_skill_sanitizer maintain-check --registry catalog --bundles bundles/index.json --references external-references/index.json --claude-skills-candidate-map docs/claude-skills-candidate-map.json`
- `PYTHONPATH=src python3 -m onecode_skill_sanitizer verify --registry catalog`
- `git diff --check`

## Boundary

This update changes the deterministic router evaluation contract, eval data,
regression tests, and documentation only. It does not change runtime
permissions, import external code, or grant browser, network, connector,
account, credential, production, or publication access.
