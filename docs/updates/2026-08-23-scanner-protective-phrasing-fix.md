# Scanner Protective-Phrasing False-Positive Fix

Date: 2026-08-23

## Summary

Fixed a scanner false-positive where protective guidance (text warning
against a dangerous action, such as "Never run `rm -rf /tmp/cache` without
confirmation.") could be flagged as if it were an instruction to perform that
action. The exemption for this phrasing previously never reached the real
`scan` CLI command.

## What Landed

- `rule_findings(line, status)`: shared helper in
  `src/onecode_skill_sanitizer/scanner.py` that checks
  `PROTECTIVE_SENSITIVE_BOUNDARY_PATTERN` before matching a rule against a
  line.
- `PROTECTIVE_EXEMPT_RULE_IDS` extended from `{"broad-filesystem-access"}` to
  also include `"destructive-shell"` and `"privilege-escalation"`.
- `scan_text` now applies the exemption per line instead of matching against
  the whole joined text blob with no exemption check. Previously this
  function (used by `build_scan_report`, the backing implementation of the
  `scan` CLI command) had no protective-phrasing exemption at all.
- `line_findings` (the sanitize/removal path) now calls the same shared
  helper instead of duplicating the loop.
- New regression test:
  `test_scan_does_not_flag_protective_shell_guidance` in
  `tests/test_scan_cli.py`.

## Gate Status

| Gate | Status |
| --- | --- |
| Targeted test (`tests/test_scan_cli.py`) | PASS (17/17) |
| Full suite (`unittest discover -s tests`) | PASS (578 tests, was 577) |
| `ruff check` on changed files | PASS |
| True-positive regression (real threats still detected) | PASS |
| Scoped private-path check (`.venv`/`.worktrees` excluded) | PASS, no matches |
| Raw `bash scripts/verify.sh` | Not used as evidence here; see note below |

Note on `verify.sh`: in this local dev environment the script's private-path
grep matches content inside `.venv/` (ruff's bundled SBOM metadata) and
`.worktrees/*/.git` gitlink files. Both directories are gitignored and absent
from a clean checkout. The script excludes `.git/**` from its scan but not
`.venv/**` or `.worktrees/**`; this is a pre-existing local-environment gap,
not a regression from this change. A scoped rerun of the same regex with
those two directories excluded returns no matches against tracked content.

## Operator Boundaries

- This fix does not retroactively rescan the 172 skills already recorded in
  `catalog/index.json`. Their sealed manifests already recorded
  `findings: []` for the affected rules, so their `trusted` status is
  unaffected.
- True-positive detection is unchanged: `sudo chmod -R 777`,
  unguarded `rm -rf`, and `curl ... | bash` still report
  `privilege-escalation`, `destructive-shell`, and `shell-download-execute`.

## Authoritative Write-Up

- [Maintenance Log](../maintenance-log.md)
