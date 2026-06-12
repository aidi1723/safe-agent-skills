# Update Statement: Provenance Usage Hardening

Date: 2026-06-12

Repository:

```text
https://github.com/aidi1723/safe-agent-skills
```

## Summary

This update adds a required `source.usage` field to every skill source record.
The field separates source type from content relationship so external
references are not mistaken for verbatim imports.

## What Changed

- Added `source.usage` to manifest schema, registry schema checks, scan output,
  and import/sanitize provenance handling.
- Added accepted values:
  - `source_import`: content was imported from the cited source and sanitized.
  - `reference_only`: the cited source is inspiration or comparison only.
  - `local_authoring`: the skill is locally authored or seeded from local
    material.
- Migrated the catalog and regenerated `catalog/index.json`.
- Marked existing `github_reference` and `web_reference` entries as
  `reference_only`.
- Marked existing local-folder entries as `local_authoring`.
- Clarified that `smart` is deterministic metadata routing, not LLM-based
  autonomous skill selection.

## Why It Matters

The previous `source.type` field mixed transport/source category with content
relationship. For example, `github_reference` could be read as if upstream
repository content had been copied and sanitized. `source.usage` makes that
claim explicit and machine-checkable.

## Verification

Run:

```bash
PYTHONPATH=src python3 -m unittest tests.test_scan_cli.ScanCliTest.test_scan_records_required_provenance_fields tests.test_scan_cli.ScanCliTest.test_scan_preserves_explicit_source_usage tests.test_registry_cli.RegistryCliTest.test_schema_check_requires_source_usage tests.test_registry_cli.RegistryCliTest.test_schema_check_rejects_invalid_source_usage
bash scripts/verify.sh
```
