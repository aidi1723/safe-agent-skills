# High-Frequency Specialists Batches 2 To 4 Design

Date: 2026-07-11
Status: approved direction, pending implementation

## Goal

Complete the identified high-frequency specialist backlog by promoting eight
existing trusted skills across engineering diagnosis, document/data delivery,
and content publication. Preserve current skill names, contracts, bundles,
overlap groups, and router behavior.

## Delivery Strategy

Work is divided into three independently verified batches:

1. Engineering diagnosis: `codebase-explore-map`,
   `execution-browser-check`, `engineering-ci-troubleshoot`.
2. Document and data delivery: `office-pdf-report`, `office-docx-brief`,
   `data-table-analysis`.
3. Content publication: `content-seo-brief`, `execution-publish-check`.

Within each batch, only one skill is edited at a time. Every skill receives a
failing real-catalog depth test, one focused on-demand reference, a specialist
policy override, resealed content hashes, registry/schema validation, and an
individual commit before the next skill begins. Batch history is synchronized
after each batch, and maintained reports are finalized after all three batches.

## Batch 2: Engineering Diagnosis

### Codebase Explore Map

The specialist will create a bounded repository map before non-trivial changes.
It will cover instruction precedence, entry points, runtime and data flow,
ownership boundaries, generated/vendor exclusions, configuration, tests,
release commands, likely change surface, and an explicit stopping condition.
Its reference will be a repository exploration evidence map.

It will not perform broad inventory for its own sake, infer architecture from
filenames alone, edit files, install dependencies, or execute unapproved
commands.

### Execution Browser Check

The specialist will define bounded browser verification for navigation,
visible state, URLs, DOM assertions, screenshots, forms, responsive viewports,
console/network failures, and reproducible failure traces. Its reference will
be a browser verification evidence guide.

It will stop at authentication, payment, destructive submission, account
mutation, private session data, uploads, downloads, or external hosts unless
the host workflow separately authorizes them.

### Engineering CI Troubleshoot

The specialist will isolate the first actionable CI failure and distinguish
code defects, configuration errors, dependency or lock drift, cache problems,
environment differences, infrastructure failures, and flakes. It will cover
matrix comparison, bounded local reproduction, minimal fixes, rerun evidence,
and residual pipeline risk. Its reference will be a CI diagnosis evidence
guide.

It will not rerun remote jobs, change secrets, bypass required checks, alter
release permissions, or treat a passing retry as proof that a flake is fixed.

## Batch 3: Document And Data Delivery

### Office PDF Report

The specialist will cover PDF text and metadata extraction, page rendering,
OCR decisions, tables, forms, signatures, page-level evidence, layout fidelity,
encrypted or damaged files, and explicit extraction gaps. Its reference will be
a PDF evidence and rendering guide.

It will preserve originals, operate only on approved files, and avoid claiming
layout or signature correctness from text extraction alone.

### Office DOCX Brief

The specialist will cover document purpose and audience, source facts,
structure, styles, headings, tables, lists, headers/footers, pagination,
references, tracked content boundaries, export, and rendered layout review. Its
reference will be a DOCX delivery evidence guide.

It will not silently invent requirements, overwrite originals, accept visual
quality without rendering when a file is produced, or treat generated text as
verified source material.

### Data Table Analysis

The specialist will cover schema and key definitions, row/column counts,
missingness, duplicates, types, joins, filters, outliers, units, denominators,
aggregate reconciliation, reproducible transformations, uncertainty, and
private-data boundaries. Its reference will be a tabular analysis evidence
guide.

It will preserve source data, distinguish cleaning from analysis, avoid
unsupported causality, and prohibit unapproved external uploads.

## Batch 4: Content Publication

### Content SEO Brief

The specialist will cover audience and market, search intent, page type,
keyword/entity roles, information architecture, canonical intent, internal
links, factual claims, source requirements, freshness, duplication, and
conversion boundaries. Its reference will be an SEO content evidence guide.

It will not promise rankings, keyword-stuff content, copy competitors, create
unsupported claims, or substitute a content brief for technical indexing and
structured-data verification.

### Execution Publish Check

The specialist will cover publish target, immutable artifact identity, version,
source revision, build/test evidence, provenance, license, generated files,
configuration, migration, rollback, approval owner, blockers, and readiness
status. Its reference will be a publication readiness evidence guide.

Readiness review remains separate from publication authority. The skill will
not upload, push, release, deploy, use credentials, mutate production, or waive
required gates without explicit host authorization.

## Existing Routing And Ownership

No new bundles or router changes are included. All eight skills already appear
as required or preferred capabilities in maintained scenarios and evaluation
cases. Narrower skills continue to own accessibility, source verification,
data quality, visual design, supply-chain review, release building, and runtime
execution where applicable.

The Safe-Agent Router selected `data-analysis-report` for the combined eight-
skill request and covered table analysis and DOCX reporting. It did not
independently decompose all engineering, browser, PDF, SEO, and publishing
intents. That deterministic single-primary-intent boundary is recorded but
excluded from these content-depth batches.

## Integrity And Historical Evidence

Each skill receives exactly one `references/*.md` asset protected by
`auxiliary_sha256`. `reseal-content` updates sanitized, auxiliary, and manifest
hashes. `reindex` must not rewrite unrelated reports.

The current batch lifecycle has 471 items and 167 historical compactions.
Where a promoted historical body exists, its `PROMOTED.md`, source hash, and
source commit remain unchanged; the batch index records the evolved current
catalog hash and `content_match: false`. Any skill without a compacted history
must retain its actual lifecycle semantics.

## Final Outcome

After all three batches:

- 157 catalog skills remain routing cards;
- 15 catalog skills are specialists;
- 15 specialist reference assets are integrity protected;
- all 172 catalog skills remain represented;
- trust status, contracts, bundle membership, overlap ownership, and public
  Schema v1 task-pack shape remain unchanged.

## Verification

Each individual skill must pass its failing-then-passing real-catalog test,
`quick_validate.py`, registry verification, schema check, and unrelated-diff
review before commit.

Each batch must pass depth and batch lifecycle checks before the next batch.
The final state must pass:

- 157 routing cards, 15 specialists, 0 depth errors, and 0 warnings;
- 172 catalog skills, 166 trusted, 0 tampered, and 0 unknown provenance;
- 471 batch items, 167 historical compactions, and 0 batch issues;
- unchanged Schema v1 payload shape and current router evaluation suite;
- complete local `scripts/verify.sh` and GitHub Actions Python matrix checks.

## Safety Boundary

All eight specialists provide method, analysis, and verification guidance only.
They do not grant filesystem, shell, browser, network, account, subscription,
credential, package installation, upload, publication, CI, deployment, or
production permissions. The host runtime and operator remain authoritative.
