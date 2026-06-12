# Update Statement: Structural Scanner Hardening

Date: 2026-06-12

Repository:

```text
https://github.com/aidi1723/safe-agent-skills
```

## Summary

This update adds a lightweight structural scanner layer for multi-step unsafe
execution patterns that single-line regular expressions miss.

## What Changed

- Added structural detection for downloaded files later executed by `sh`,
  `bash`, `python`, or `node`.
- Added heredoc interpreter detection for shell, Python, Node, Perl, and Ruby.
- Kept existing deterministic regex rules and deduplicated repeated finding
  IDs in scan output.
- Added regression coverage for:
  - `curl -o /tmp/install.sh` followed by `bash /tmp/install.sh`
  - `python <<'PY'` heredoc execution
  - command-substitution download pipes such as `curl $(...) | bash`

## Why It Matters

The scanner is still a deterministic preflight guardrail, not a complete
malware detector. This change raises the floor by catching common multi-step
execution patterns while keeping the implementation dependency-free and
auditable.

## Verification

Run:

```bash
PYTHONPATH=src python3 -m unittest tests.test_scan_cli.ScanCliTest.test_scan_detects_staged_download_execution_and_heredoc_interpreters
bash scripts/verify.sh
```
