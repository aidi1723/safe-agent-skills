# Router Eval Prefix Constraints

Date: 2026-07-03

## Summary

Extended `router-eval` negative constraints with prefix-based forbidden skill
checks.

Eval cases can now include:

- `forbidden_skill_prefixes`: skill-name prefixes that must not appear in the
  selected task pack.

## What Changed

- Added `router-eval-forbidden-skill-prefix` failures when a selected skill
  starts with a forbidden prefix.
- Upgraded vague `general` fallback eval cases from enumerating specific
  browser skill names to forbidding the broader `execution-browser*` and
  `execution-playwright*` families.
- Kept exact `forbidden_skills` support for targeted exclusions such as
  `execution-publish-check`.
- Added focused CLI regression coverage for exact, prefix, and count
  constraints in the same eval case.
- Kept the full-script test baseline at 135 tests while expanding the existing
  negative-constraint regression case.

## Verification Targets

- `PYTHONPATH=src python3 -m unittest tests.test_registry_cli.RegistryCliTest.test_router_eval_fails_forbidden_skills_prefixes_and_skill_count_limit`
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
