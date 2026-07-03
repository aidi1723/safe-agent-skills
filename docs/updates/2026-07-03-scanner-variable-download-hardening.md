# Scanner Variable Download Hardening

Date: 2026-07-03

## Summary

Started the Phase 1 scanner engine upgrade from
`docs/next-development-plan.md` with a focused variable-assigned download
execution bypass case.

## What Changed

- Added shell-word parsing for simple variable assignments using `shlex`.
- Added structural detection for variables that store a `curl` or `wget`
  command and are later expanded into `sh` or `bash`.
- Added the finding ID `indirect-download-execution` for this bypass family.
- Added regression coverage for:
  - `INSTALLER='curl ...'` followed by `$INSTALLER | bash`
  - `FETCH="wget ... -O /tmp/setup.sh"` followed by `${FETCH} && sh ...`

## Boundary

This remains deterministic preflight scanning. It does not execute shell
content, expand variables at runtime, fetch remote URLs, or grant runtime
permissions.

Regex rules remain as fallback while structural scanner coverage grows.

## Verification

Run:

```bash
PYTHONPATH=src python3 -m unittest tests.test_scan_cli.ScanCliTest.test_scan_detects_variable_assigned_download_execution_bypasses
PYTHONPATH=src python3 -m unittest tests.test_scan_cli
bash scripts/verify.sh
```
