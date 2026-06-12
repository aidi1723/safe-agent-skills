# Update Statement: Consistency Rule Hardening

Date: 2026-06-12

Repository:

```text
https://github.com/aidi1723/safe-agent-skills
```

## Summary

This update tightens schema validation around provenance semantics and
sanitization-report state consistency.

## What Changed

- Added deterministic `source.type` and `source.usage` compatibility checks:
  - `local_folder` requires `local_authoring`.
  - `github_reference` and `web_reference` require `reference_only`.
  - `archive`, `git`, and `community_index` require `source_import`.
- Mirrored those compatibility rules in manifest, registry-index, and
  sanitization-report JSON schemas.
- Updated `schema-check` to reject sanitization reports whose summary
  `status` or `risk_level` differs from the sibling manifest.
- Updated `schema-check` to reject sanitization reports whose
  `required_verifiers` differs from the sibling manifest.

## Why It Matters

The previous hardening made source usage explicit. This update prevents
internally inconsistent combinations, such as marking a GitHub reference as a
source import without using the source-import path. It also prevents report
evidence from drifting away from the approved manifest state.

## Verification

Run:

```bash
PYTHONPATH=src python3 -m unittest tests.test_registry_cli.RegistryCliTest.test_schema_check_rejects_incompatible_source_type_usage_pair tests.test_registry_cli.RegistryCliTest.test_schema_check_validates_report_summary_and_verifier_consistency
bash scripts/verify.sh
```
