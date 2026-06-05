# Update Statement: Skill Overlap Groups

Date: 2026-06-05

Repository:

```text
https://github.com/aidi1723/safe-agent-skills
```

## Summary

This update adds catalog-level skill overlap metadata for the trusted skill
set. It records where skills are adjacent in function and which one should be
treated as the primary choice for narrow tasks.

The overlap layer does not delete, merge, or downgrade any skill. It is a
selection hint for routers and operators so broad tasks can still load multiple
guardrails while narrow tasks avoid redundant skill selection.

## What Changed

- Added `catalog/overlap-groups.json` with 7 trusted-only overlap groups.
- Added `docs/skill-overlap-groups.md` with selection rules and current group
  coverage.
- Extended `maintain-check` so it validates overlap groups when an
  `overlap-groups.json` file exists under the selected registry.
- Added `--overlap-groups` for explicit overlap metadata validation.
- Added a regression test for blocking non-trusted overlap references.
- Updated README, architecture notes, operator guide, maintenance guide, and
  catalog status.

## Source Boundary

The grouping is local OneCode catalog metadata derived from the existing
trusted registry. It does not adopt unverified repository names, Star counts,
or third-party runtime instructions as provenance.

## Verification Evidence

Release gate:

```bash
PYTHONPATH=src python3 -m unittest tests.test_registry_cli.RegistryCliTest.test_maintain_check_fails_when_overlap_group_references_non_trusted_skill
PYTHONPATH=src python3 -m onecode_skill_sanitizer schema-check --registry catalog
PYTHONPATH=src python3 -m onecode_skill_sanitizer maintain-check --registry catalog --bundles bundles/index.json
bash scripts/verify.sh
```

Expected baseline:

```text
skill_count: 105
trusted_count: 100
trusted_bundle_count: 9
overlap_group_count: 7
tampered_count: 0
unknown_provenance_count: 0
```

## Files Added

- `catalog/overlap-groups.json`
- `docs/skill-overlap-groups.md`
