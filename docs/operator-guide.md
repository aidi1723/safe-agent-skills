# Operator Guide

## Goal

Use this guide to collect, clean, review, and select skills without executing
untrusted source content.

Run all commands from the `onecode-skill-sanitizer` folder.

Verify the local project first:

```bash
bash scripts/verify.sh
```

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

`task-pack` verifies the registry before output. If provenance is incomplete or
a sanitized hash does not match, generation is refused.

Default mode only emits `trusted` skills. `--include-review-required` can add
`review_required` skills for review workflows, but `quarantined`, `rejected`,
and `disabled` entries are still excluded.

The task pack is safe to hand to any host agent as method guidance. It does not
grant runtime permissions; shell, filesystem, network, connector, and
production actions remain controlled by the host runtime.

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
