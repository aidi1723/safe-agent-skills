# Community Reference Maintenance Path

## Purpose

This document is the operator path for maintaining external community and
official skill references.

Use it when adding, reviewing, converting, or retiring entries in:

```text
external-references/index.json
```

External references are source intelligence only. They do not grant runtime
authority, do not install tools, and do not become selectable task-pack skills
until converted into local sanitized catalog entries and approved.

## Maintained Files

Primary files:

- `external-references/index.json`: metadata-only external reference index
- `docs/external-reference-roadmap.md`: reference strategy and phases
- `docs/catalog-status.md`: current public catalog and reference baseline
- `docs/maintenance-guide.md`: release and verification path
- `docs/community-skill-reference-closure-report.md`: latest review closure

Related governance files:

- `docs/sanitization-policy.md`: trusted, quarantined, and review-required rules
- `docs/source-baseline.md`: source and usage semantics
- `docs/agent-task-pack.md`: trusted task-pack boundary
- `bundles/index.json`: trusted scenario bundle definitions
- `catalog/index.json`: trusted catalog index

Do not edit historical closure reports only to refresh old counts. They are
dated evidence snapshots.

## Intake Checklist

For every new external reference, record:

- source URL
- source type
- author or organization
- license
- captured date
- project category
- claimed capabilities
- mapped local taxonomy categories
- runtime permission notes
- adoption status
- review notes
- `metadata_only: true`

Allowed `adoption_status` values:

- `reference_only`: architecture, workflow, or source-discovery reference
- `candidate`: worth drafting into a local reviewed skill later
- `converted`: already represented by a local sanitized catalog skill
- `rejected`: unsuitable or unsafe for local adoption

If license, ownership, or provenance cannot be confirmed, keep the reference as
`reference_only` or `rejected`. Do not mark it trusted.

## Conversion Path

Convert a reference into a local skill only through this path:

1. Record upstream provenance and license.
2. Summarize useful capability without copying upstream text wholesale.
3. Create or update a local `SKILL.md` under an incoming or batch path.
4. Run sanitizer, schema checks, and risk scan.
5. Keep status as `quarantined` or `review_required` until reviewed.
6. Promote to `trusted` only after manifest, sanitization report, hash, and
   registry verification pass.
7. Update `catalog/index.json`, batch notes, `docs/catalog-status.md`, and
   relevant closure or update docs.

Do not bulk-import external directories. Do not execute external code during
intake. Runtime connectors, MCP servers, browser sessions, account access,
network calls, package installs, and scanner commands need a separate explicit
review path.

## Verification Path

Run these checks after editing external references or related documentation:

```bash
PYTHONPATH=src python3 -m onecode_skill_sanitizer reference-check --references external-references/index.json
PYTHONPATH=src python3 -m onecode_skill_sanitizer maintain-check \
  --registry catalog \
  --bundles bundles/index.json \
  --references external-references/index.json
PYTHONPATH=src python3 -m onecode_skill_sanitizer router-eval \
  --eval evals/router-quality.json \
  --registry catalog \
  --bundles bundles/index.json
bash scripts/verify.sh
```

Expected current result:

```text
reference_count: 9
skill_count: 109
trusted_count: 103
tampered_count: 0
unknown_provenance_count: 0
router-eval: ok
tests: 69 passed
```

## Publish Path

Before pushing reference-maintenance work:

1. Run `git status --short` and confirm unrelated files are not staged.
2. Stage only the intended reference, catalog-status, maintenance, roadmap, and
   closure/update docs.
3. Run `bash scripts/verify.sh`.
4. Commit with a message that names the reference review or maintenance cycle.
5. Push to `origin/main` only after verification succeeds.

Use this final check:

```bash
git status --short --branch
git log -1 --oneline --decorate
```

The branch should be aligned with `origin/main` after push, except for any
operator-local untracked files that are intentionally left out.

## Current External References

As of 2026-06-16:

- OpenAI Skills Catalog for Codex: `reference_only`
- Agent Skills Specification: `reference_only`
- Snyk Agent Scan: `reference_only`
- andrej-karpathy-skills CLAUDE.md: `reference_only`
- AnyTool: `reference_only`
- Awesome MCP Servers: `reference_only`
- AskBudi Roundtable MCP: `reference_only`
- last30days-skill: `candidate`
- Antigravity CLI provenance watch: `reference_only`

All current entries are `metadata_only: true`.
