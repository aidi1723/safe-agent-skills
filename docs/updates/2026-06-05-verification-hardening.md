# Update Statement: Verification Hardening

Date: 2026-06-05

Repository:

```text
https://github.com/aidi1723/safe-agent-skills
```

## Summary

This update hardens the Safe-Agent-Skills maintenance and publication path.
The project now checks more than registry hash integrity: it also validates
catalog schema shape, detects stale registry indexes, runs in GitHub Actions,
and catches more dangerous shell guidance during skill intake.

The goal is to make catalog drift, weak validation, and unsafe imported
instructions easier to catch before a skill pack is published or routed to an
agent.

## What Changed

- Added GitHub Actions verification for pushes and pull requests.
- Added `schema-check` to validate real catalog manifests, registry index
  entries, and verify-report structure without external runtime dependencies.
- Added registry index freshness checks to `maintain-check`.
- Extended scanner detection for privilege escalation, broad permission
  changes, and recursive destructive shell deletion.
- Added Chinese task signals for deterministic scenario routing.
- Updated `scripts/verify.sh` so local and CI verification use the same gate.
- Updated tests to cover schema validation, stale index detection, Chinese
  routing, and dangerous shell variants.

## Safety Boundary

This update does not grant skills any new execution authority.

Skills remain method guidance only. Filesystem, shell, network, browser,
connector, account, credential, and production actions still belong to the host
runtime's approval and policy layer.

## Verification Evidence

Release gate:

```bash
bash scripts/verify.sh
PYTHONPATH=src python3 -m onecode_skill_sanitizer schema-check --registry catalog
PYTHONPATH=src python3 -m onecode_skill_sanitizer maintain-check --registry catalog --bundles bundles/index.json
```

Verified baseline:

```text
tests: 38 passed
skill_manifest_count: 75
schema-check: ok
skill_count: 75
trusted_count: 70
tampered_count: 0
unknown_provenance_count: 0
trusted_bundle_count: 9
bundle issues: 0
```

## Files Updated

- `.github/workflows/verify.yml`
- `scripts/verify.sh`
- `src/onecode_skill_sanitizer/cli.py`
- `src/onecode_skill_sanitizer/router.py`
- `src/onecode_skill_sanitizer/scanner.py`
- `schemas/skill-manifest.schema.json`
- `tests/test_registry_cli.py`
- `tests/test_router.py`
- `tests/test_scan_cli.py`
