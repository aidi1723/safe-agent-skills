# Recent Social Signal Reference

## Summary

Added `mvanhorn/last30days-skill` as a metadata-only external reference and
introduced `research-recent-social-signal-brief` as a review-required candidate
skill for recent multi-source public signal briefs.

## Safety Decision

- `last30days-skill` is treated as a candidate reference, not copied runtime.
- The local skill is `review_required` and `high` risk.
- Default task packs must not auto-install, scrape, execute connectors, or use
  external accounts/API access from this reference.
- `Antigravity CLI provenance watch` is recorded as reference-only because the
  user-supplied `google/antigravity-cli` repository path was not found.

## Verification

- registry verification: ok
- schema check: ok
- reference check: ok
- maintain check: ok
