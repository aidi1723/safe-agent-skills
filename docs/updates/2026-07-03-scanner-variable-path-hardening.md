# Scanner Variable Path Hardening

Date: 2026-07-03

## Summary

Continued the Phase 1 scanner engine upgrade with a focused downloaded-file
path data-flow bypass case.

## What Changed

- Reused simple shell variable assignment parsing for path-like values.
- Added structural detection for files downloaded to a variable-expanded path
  and later executed through the same variable.
- Added the finding ID `variable-path-download-execution` for this bypass
  family.
- Added regression coverage for:
  - `PAYLOAD=/tmp/payload.sh`, `curl ... -o "$PAYLOAD"`, `bash "$PAYLOAD"`
  - `SECOND=/tmp/setup.py`, `wget ... --output-document=${SECOND}`,
    `python3 ${SECOND}`

## Boundary

This remains deterministic preflight scanning. It does not execute shell
content, fetch remote URLs, resolve filesystem paths, or perform runtime
variable expansion beyond simple static variable-name matching.

## Verification

Run:

```bash
PYTHONPATH=src python3 -m unittest tests.test_scan_cli.ScanCliTest.test_scan_detects_variable_path_download_execution_bypasses
PYTHONPATH=src python3 -m unittest tests.test_scan_cli
bash scripts/verify.sh
```
