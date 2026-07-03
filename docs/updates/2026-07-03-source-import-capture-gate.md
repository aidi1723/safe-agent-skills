# Source Import Capture Gate

Date: 2026-07-03

## Summary

Closed the remaining delivery-blocking source-import metadata gap with a
schema gate.

Any manifest, registry index entry, or sanitization report that declares:

```json
"source": {
  "usage": "source_import"
}
```

must now include a `source.capture` object with auditable upstream capture
metadata.

## Required Capture Fields

`source.capture` must include:

- `upstream_url`
- `upstream_ref_type`
- `upstream_ref`
- `captured_at`
- `license_snapshot`
- `upstream_sha256`
- `content_path`
- `capture_method`

Additional validation requires:

- `upstream_url` starts with `http://` or `https://`;
- `upstream_ref_type` is one of `archive`, `branch`, `commit`, `release`, or
  `tag`;
- `upstream_sha256` is a 64-character lowercase SHA-256 hex digest.

## What Changed

- Added `schema-missing-source-import-capture` when `source_import` omits
  capture metadata.
- Added `schema-invalid-source-import-capture` for malformed capture fields.
- Added regression coverage for both missing and valid capture metadata.
- Kept `github_reference` and `web_reference` restricted to
  `reference_only`.
- Did not add a networked import command or any upstream fetch behavior.

## Delivery Impact

The public catalog can now treat `source_import` as a stricter audited state
instead of a loose label. Real network or Git import automation remains a
future enhancement, but the current release no longer permits trusted
`source_import` records without capture evidence.

## Verification Targets

- `PYTHONPATH=src python3 -m unittest tests.test_registry_cli.RegistryCliTest.test_schema_check_rejects_source_import_without_capture_metadata tests.test_registry_cli.RegistryCliTest.test_schema_check_accepts_source_import_with_capture_metadata`
- `PYTHONPATH=src python3 -m unittest tests.test_registry_cli.RegistryCliTest.test_schema_check_rejects_source_import_without_capture_metadata tests.test_registry_cli.RegistryCliTest.test_schema_check_accepts_source_import_with_capture_metadata tests.test_registry_cli.RegistryCliTest.test_schema_check_requires_source_usage tests.test_registry_cli.RegistryCliTest.test_schema_check_rejects_invalid_source_usage tests.test_registry_cli.RegistryCliTest.test_schema_check_validates_sanitization_report_source_consistency tests.test_registry_cli.RegistryCliTest.test_schema_check_rejects_incompatible_source_type_usage_pair`
- `PYTHONPATH=src python3 -m onecode_skill_sanitizer schema-check --registry catalog`
- `bash scripts/verify.sh`
- `PYTHONPATH=src python3 -m onecode_skill_sanitizer maintain-check --registry catalog --bundles bundles/index.json --references external-references/index.json --claude-skills-candidate-map docs/claude-skills-candidate-map.json`
- `PYTHONPATH=src python3 -m onecode_skill_sanitizer verify --registry catalog`
- `git diff --check`

## Boundary

This update changes schema validation, tests, and documentation only. It does
not clone repositories, download archives, execute upstream content, install
third-party skills, or grant network, filesystem, browser, connector,
credential, production, or publication permissions.
