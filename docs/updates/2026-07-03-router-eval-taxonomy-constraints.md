# Router Eval Taxonomy Constraints

Date: 2026-07-03

## Summary

Extended `router-eval` negative constraints with taxonomy-aware forbidden
subcategory checks.

Eval cases can now include:

- `forbidden_skill_subcategories`: skill taxonomy subcategories that must not
  appear in the selected task pack.

## What Changed

- Added `router-eval-forbidden-skill-subcategory` failures when a selected
  skill belongs to a forbidden taxonomy subcategory.
- Upgraded vague `general` fallback eval cases to forbid browser-related
  execution subcategories:
  - `execution.browser`
  - `execution.browser_agent`
  - `execution.browser_test`
- Kept exact skill and prefix constraints in place so evals can combine
  targeted, family-level, and taxonomy-level guards.
- Expanded the existing negative-constraint CLI regression case to cover
  subcategory failures.

## Verification Targets

- `PYTHONPATH=src python3 -m unittest tests.test_registry_cli.RegistryCliTest.test_router_eval_fails_forbidden_skills_prefixes_subcategories_and_skill_count_limit`
- `PYTHONPATH=src python3 -m onecode_skill_sanitizer router-eval --eval evals/router-quality.json --registry catalog --bundles bundles/index.json`
- `bash scripts/verify.sh`
- `PYTHONPATH=src python3 -m onecode_skill_sanitizer maintain-check --registry catalog --bundles bundles/index.json --references external-references/index.json --claude-skills-candidate-map docs/claude-skills-candidate-map.json`
- `PYTHONPATH=src python3 -m onecode_skill_sanitizer verify --registry catalog`
- `git diff --check`

## Boundary

This update changes deterministic eval checks, eval data, regression tests, and
documentation only. It does not change router runtime permissions, import
external code, or grant browser, network, connector, account, credential,
production, or publication access.
