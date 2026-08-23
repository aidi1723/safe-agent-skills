# GitHub Update Summary

Date: 2026-08-23

## Summary

This update fixes a scanner false-positive gap in `safe-agent-skills`: text
that warns against a dangerous action (for example "Never run
`rm -rf /tmp/cache` without confirmation.") could be flagged as though it were
an instruction to perform that action, on the real `scan` CLI command.

Authoritative write-up:

- [Dated Update Note](updates/2026-08-23-scanner-protective-phrasing-fix.md)
- [Maintenance Log](maintenance-log.md)

## What Was Updated

### Scanner engine (`src/onecode_skill_sanitizer/scanner.py`)

- Extracted a shared `rule_findings(line, status)` helper that applies
  `PROTECTIVE_SENSITIVE_BOUNDARY_PATTERN` before matching a rule.
- Extended `PROTECTIVE_EXEMPT_RULE_IDS` from `{"broad-filesystem-access"}` to
  `{"broad-filesystem-access", "destructive-shell", "privilege-escalation"}`.
- Rewrote `scan_text` (used by `build_scan_report`, the implementation behind
  the `scan` CLI command) to apply the exemption per line. Previously this
  function had no protective-phrasing exemption logic at all, so a prior
  exemption that existed only in the sanitize/removal path never reached
  real scan reports.
- `line_findings` now calls the same shared helper instead of duplicating the
  loop.

### Tests (`tests/test_scan_cli.py`)

- Added `test_scan_does_not_flag_protective_shell_guidance`, scanning
  protective phrasing ("Never run...", "Do not run...", "Avoid using...")
  and asserting `destructive-shell` / `privilege-escalation` are absent with
  `risk_level: low`.
- All pre-existing true-positive regression tests (real destructive shell,
  privilege escalation, download-and-execute, obfuscated payloads,
  cross-shell bypasses) continue to pass unchanged.

## Gate Status

| Gate | Status |
| --- | --- |
| `tests/test_scan_cli.py` | PASS (17/17) |
| Full suite (`unittest discover -s tests`) | PASS (578 tests, was 577) |
| `ruff check` on changed files | PASS |
| Scoped private-path check (tracked content only) | PASS, no matches |
| Raw `bash scripts/verify.sh` | Not used as evidence; see note below |

`bash scripts/verify.sh`'s private-path grep matches local-only artifacts in
this dev environment: `.venv/` (ruff's bundled SBOM metadata referencing
upstream CI build paths) and `.worktrees/*/.git` gitlink files. Both
directories are gitignored and absent from a clean checkout; the script
excludes `.git/**` from its scan but not `.venv/**` or `.worktrees/**`. This
is a pre-existing local-environment gap in the script, unrelated to this
change. Re-running the same regex scoped to tracked content only
(`.venv` and `.worktrees` excluded) returns no matches.

## Operator Example

```bash
PYTHONPATH=src python3 -m onecode_skill_sanitizer.cli scan <skill-dir> --out report.json
```

A skill whose `SKILL.md` says "Never run `rm -rf /tmp/cache` without
confirmation." now reports `risk_level: low` instead of being flagged for
`destructive-shell`. A skill that actually instructs `sudo chmod -R 777 ...`
or an unguarded `rm -rf /` is still flagged as `critical`.

## Privacy And Publication Hygiene

Before this GitHub publication:

- Local absolute home paths and private workspace markers remain blocked by
  `scripts/verify.sh` private-path checks.
- Local-only review drafts (`项目审查报告*.md`) stay gitignored and are not
  published; they were annotated locally to record that the false-positive
  risk they described is now fixed, but that annotation is not part of this
  push.
- Untracked local files `uv.lock` and `CLAUDE.md` are not included in this
  push; they are out of scope for this fix.
- No API keys, tokens, or credential material are added by this change.
- Fixture strings used only to test detection/exemption stay synthetic.

## Related Links

- [Dated Update Note](updates/2026-08-23-scanner-protective-phrasing-fix.md)
- [Maintenance Log](maintenance-log.md)
- [Sanitization Policy](sanitization-policy.md)
- [Documentation Index](index.md)
