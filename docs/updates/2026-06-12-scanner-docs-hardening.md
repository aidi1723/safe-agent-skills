# Scanner and Documentation Hardening

## Summary

Tightened the project truth-in-advertising boundary after review of the public
catalog, sanitizer claims, source provenance wording, and verification script.

## Changes

- Updated public baseline counts to 109 total skills and 103 trusted skills.
- Clarified that the scanner is a deterministic risk preflight guardrail, not a
  complete malware detector or standalone sandbox.
- Clarified that `github_reference` entries may be locally authored reference
  skills inspired by public projects, not verbatim upstream imports.
- Added scanner coverage for inline interpreter execution, encoded payload
  execution, and environment or credential exfiltration wording.
- Made `scripts/verify.sh` fail closed when `rg` is unavailable, so privacy and
  placeholder scans cannot be silently skipped.

## Safety Decision

The catalog remains useful as a governance, provenance, routing, and
verification scaffold. It should not be described as fully sanitizing arbitrary
malicious third-party skills without human review and host-runtime controls.

## Verification

- targeted scanner tests: ok
- verify script dependency test: ok
- unit test suite: ok
- maintain check: ok
- full verification script: ok
