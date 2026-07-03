# Maintenance Log

Date: 2026-07-03

## Current Maintained Baseline

```text
branch: main
catalog skills: 164
trusted skills: 158
trusted scenario bundles: 15
trusted overlap groups: 7
tracked claude-skills candidates: 336
covered claude-skills candidates: 336
router eval cases: 26
verification command: bash scripts/verify.sh
```

## Maintenance Gates

Run these gates before publishing catalog, router, bundle, or documentation
changes:

```bash
bash scripts/verify.sh
env PYTHONPATH=src python3 -m onecode_skill_sanitizer.cli verify --registry catalog
env PYTHONPATH=src python3 -m onecode_skill_sanitizer.cli maintain-check --registry catalog --bundles bundles/index.json --references external-references/index.json --claude-skills-candidate-map docs/claude-skills-candidate-map.json
env PYTHONPATH=src python3 -m onecode_skill_sanitizer router-eval --eval evals/router-quality.json --registry catalog --bundles bundles/index.json
git diff --check
```

Expected current results:

```text
verify: ok, 164 skills, 158 trusted, 0 tampered, 0 unknown provenance
maintain-check: ok, 15 bundles, 336 / 336 candidates covered
router-eval: ok, 26 / 26 cases
full script: 122 tests OK
```

## Routine Maintenance Checklist

- Keep `README.md`, `catalog/README.md`, `docs/catalog-status.md`, and
  `docs/feature-log.md` in sync with `catalog/index.json` and
  `bundles/index.json`.
- Add or update router eval cases when a new scenario profile, bundle, or major
  signal family is added.
- Keep default task packs trusted-only. Use review-required or quarantined
  skills only for explicit review work.
- Do not copy or execute upstream community skills directly. Convert useful
  patterns through local authoring, scan, schema check, approval, manifest
  sealing, and registry verification.
- Update `docs/claude-skills-candidate-map.json` only when a candidate maps to
  an existing trusted local skill or is intentionally queued for future work.
- Reinstall `safe-agent-router` only when integration skill files or wrapper
  scripts change, or when the local repository path changes.

## Next Maintenance Backlog

- Watch upstream reference sources for new or changed skill candidates.
- Promote cluster-covered candidates into dedicated local skills only when
  repeated real tasks show that a cluster is too broad.
- Continue expanding multilingual routing signals for common Chinese, English,
  and mixed-language task phrasing.
- Add deeper parser-backed checks where deterministic regex scanning is too
  shallow for a recurring risk class.

