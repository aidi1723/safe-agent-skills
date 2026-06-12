# Update Statement: Report Schema and Scanner Hardening

Date: 2026-06-12

Repository:

```text
https://github.com/aidi1723/safe-agent-skills
```

## Summary

This update extends catalog schema validation from manifests and registry
indexes into each `SANITIZATION_REPORT.json`, and adds scanner regression
coverage for split shell pipelines and environment-variable pipe exfiltration.

## What Changed

- Added `schemas/sanitization-report.schema.json`.
- Updated `schema-check` to validate every `SANITIZATION_REPORT.json`.
- Added consistency checks requiring report `source`, `hashes`, and `taxonomy`
  to match the sibling `skill.json` manifest.
- Migrated catalog reports so `source.usage` and provenance fields match
  manifests.
- Added scan normalization for backslash-newline and newline-split shell
  pipelines.
- Added detection for `printenv`/`env` piped into `curl` or `wget`.

## Why It Matters

The manifest and registry index already carried the strengthened provenance
contract. Sanitization reports still needed the same enforcement so scan
evidence cannot drift from approved manifests.

The scanner remains a deterministic preflight guardrail, not a complete malware
detector. These regressions close common string-format bypasses without
claiming full command semantics.

## Verification

Run:

```bash
PYTHONPATH=src python3 -m unittest tests.test_registry_cli.RegistryCliTest.test_schema_check_validates_sanitization_report_source_consistency tests.test_scan_cli.ScanCliTest.test_scan_detects_split_download_execution_and_env_pipe_exfiltration
bash scripts/verify.sh
```
