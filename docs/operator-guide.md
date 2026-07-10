# Operator Guide

## Goal

Use this guide to collect, clean, review, and select skills without executing
untrusted source content.

Run all commands from the `onecode-skill-sanitizer` folder.

Verify the local project first:

```bash
python3 -m pip install -e ".[dev]"
bash scripts/verify.sh
```

`jsonschema` is required by the verification suite. Install development checks with: `python3 -m pip install -e ".[dev]"` before running `bash scripts/verify.sh`.

Hybrid Router v2 also requires the development install for `ruff` and schema
validation. Schema v2 is the default; request Schema v1 only when the consumer
requires the frozen, independently executed v1 routing behavior. Do not treat
that selection as equivalent to the v2 payload's lossy `to_legacy_v1`
projection or its `compatibility_loss` migration information.

```bash
PYTHONPATH=src python3 -m onecode_skill_sanitizer smart \
  "构建官网，同时审计 skill 路由器，验证通过后发布更新" \
  --schema-version 2 --format json
PYTHONPATH=src python3 -m onecode_skill_sanitizer smart \
  "build a product website" --schema-version 1 --format json
PYTHONPATH=src python3 -m onecode_skill_sanitizer router-eval-v2 \
  --eval evals/multi-intent-gold.json --registry catalog \
  --bundles bundles/index.json
```

Interpret v2 states conservatively: `complete` is fully covered, `incomplete`
requires host clarification or additional method coverage, and `blocked` must
not execute. `route_id` is only a privacy-aware correlation hash, never an
authorization token. The provider fields remain `none` with a semantic-provider
fallback placeholder in this deterministic milestone.

## Folder Layout

```text
onecode-skill-sanitizer/
  incoming/
    office-pdf/
      SKILL.md
  registry/
    office/
      office-pdf/
        SKILL.md
        skill.json
        SANITIZATION_REPORT.json
    index.json
```

`incoming/` and `registry/` are local runtime folders and are ignored by git.

## Single Skill Intake

```bash
PYTHONPATH=src python3 -m onecode_skill_sanitizer.cli scan ./incoming/office-pdf \
  --out ./incoming/office-pdf.scan.json \
  --source-url https://github.com/example/skills/office-pdf \
  --author example-team \
  --license MIT \
  --reference https://github.com/example/skills \
  --collected-by onecode-local
```

```bash
PYTHONPATH=src python3 -m onecode_skill_sanitizer.cli sanitize ./incoming/office-pdf \
  --out ./registry/office/office-pdf \
  --source-url https://github.com/example/skills/office-pdf \
  --author example-team \
  --license MIT \
  --reference https://github.com/example/skills \
  --collected-by onecode-local
```

## Batch Intake

```bash
PYTHONPATH=src python3 -m onecode_skill_sanitizer.cli import ./incoming \
  --registry ./registry \
  --collected-by onecode-local
```

Batch import sanitizes every direct child folder of `incoming/` and writes each
skill into `registry/<category>/<name>/`.

## Review

Inspect before approval:

```bash
PYTHONPATH=src python3 -m onecode_skill_sanitizer.cli inspect office-pdf \
  --registry ./registry
```

Approve, reject, or disable:

```bash
PYTHONPATH=src python3 -m onecode_skill_sanitizer.cli approve ./registry/office/office-pdf
PYTHONPATH=src python3 -m onecode_skill_sanitizer.cli reject ./registry/security/unsafe-skill
PYTHONPATH=src python3 -m onecode_skill_sanitizer.cli disable ./registry/office/old-skill
```

## Selection

Normal selection returns only `trusted` skills:

```bash
PYTHONPATH=src python3 -m onecode_skill_sanitizer.cli select "process a pdf report" \
  --registry ./registry
```

Review-mode selection can include `review_required` skills:

```bash
PYTHONPATH=src python3 -m onecode_skill_sanitizer.cli select "process a pdf report" \
  --registry ./registry \
  --include-review-required
```

## Agent Task Pack

Use `task-pack` when an agent needs ready-to-use skill instructions, not just a
candidate list:

```bash
PYTHONPATH=src python3 -m onecode_skill_sanitizer.cli task-pack \
  "process a pdf report" \
  --registry ./registry \
  --top 3 \
  --format json
```

For agents that consume plain text, use Markdown:

```bash
PYTHONPATH=src python3 -m onecode_skill_sanitizer.cli task-pack \
  "review security risk" \
  --registry ./registry \
  --top 2 \
  --format markdown
```

To include trusted scenario bundle suggestions:

```bash
PYTHONPATH=src python3 -m onecode_skill_sanitizer.cli task-pack \
  "design a RAG document agent with vector retrieval and citation checks" \
  --registry ./registry \
  --top 5 \
  --include-bundles \
  --bundles ./bundles/index.json \
  --format markdown
```

`task-pack` verifies the registry before output. If provenance is incomplete or
a sanitized hash does not match, generation is refused.

Default mode only emits `trusted` skills. `--include-review-required` can add
`review_required` skills for review workflows, but `quarantined`, `rejected`,
and `disabled` entries are still excluded.

The task pack is safe to hand to any host agent as method guidance. It does not
grant runtime permissions; shell, filesystem, network, connector, and
production actions remain controlled by the host runtime.

Markdown task packs escape task-controlled Markdown and HTML syntax. Operators
should still treat task text as untrusted input and avoid embedding secrets.

## Verification

Run this before handing a registry to OneCode runtime:

```bash
PYTHONPATH=src python3 -m onecode_skill_sanitizer.cli verify --registry ./registry
```

`verify` fails when approved skills are tampered with or provenance is unknown.

Rebuild the index after manual edits or external sync:

```bash
PYTHONPATH=src python3 -m onecode_skill_sanitizer.cli reindex --registry ./registry
```

Run the maintenance gate before publishing a registry and bundle set:

```bash
PYTHONPATH=src python3 -m onecode_skill_sanitizer.cli maintain-check \
  --registry ./registry \
  --bundles ./bundles/index.json
```

`maintain-check` combines registry verification with bundle validation. It
fails if a trusted bundle references a missing, quarantined, review-required,
rejected, or disabled skill. When `overlap-groups.json` exists under the
registry, it also validates that every overlap-group reference points to an
existing trusted skill.
