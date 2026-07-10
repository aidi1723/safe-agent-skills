# Batch Lifecycle

`batches/` is an intake and provenance workspace. It is not a runtime skill
registry. Only skills under `catalog/` can be selected as trusted guidance.

The canonical machine-readable inventory is `batches/index.json`. Every item
uses one lifecycle value:

- `active_draft`: editable metadata-only draft
- `review_ready`: source material awaiting catalog review
- `promoted`: canonical skill exists under `catalog/`
- `superseded`: historical material retained for provenance only

When a promoted batch `SKILL.md` is byte-identical to its catalog body, the
duplicate is replaced by `PROMOTED.md`. The promotion record retains the
original SHA-256, source commit, original path, and canonical catalog path.
Non-identical promoted bodies are never compacted automatically.

Validate the boundary with:

```bash
PYTHONPATH=src python3 -m onecode_skill_sanitizer batch-check \
  --batches batches \
  --catalog catalog \
  --index batches/index.json
```

Regenerate and compact only after reviewing the current Git diff:

```bash
PYTHONPATH=src python3 -m onecode_skill_sanitizer batch-compact \
  --batches batches \
  --catalog catalog \
  --index batches/index.json \
  --source-commit <reviewed-commit>
```
