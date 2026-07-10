# High-Frequency Core Specialists Batch 1 Design

Date: 2026-07-11
Status: approved direction, pending implementation

## Goal

Promote three established high-frequency catalog skills to specialist depth:
`code-review-risk`, `code-test-regression`, and `research-source-check`.
Strengthen their decision quality and evidence requirements without adding
duplicate skills, new scenario bundles, or router behavior changes.

## Delivery Model

The three skills form one maintenance batch but will be implemented and
verified sequentially. Each skill receives its own failing regression test,
reference asset, body and manifest reseal, focused validation, and commit before
the next skill is changed. Shared batch indexes and maintained reports are
synchronized only after all three individual specialists pass.

This order keeps failures attributable and follows the repository rule that a
skill must be verified before another skill is deployed.

## Specialist 1: Code Review Risk

`code-review-risk` will own findings-first review of diffs, pull requests,
patches, generated code, and behavior changes. It will add decision guidance
for:

- review scope and intended behavior;
- correctness, data-flow, state, boundary, concurrency, and error-path risks;
- compatibility, dependency, security, and migration implications;
- severity based on user impact, likelihood, reachability, and recoverability;
- distinguishing actionable defects from optional maintainability advice;
- identifying missing tests and residual risk.

Its on-demand reference will be a code review evidence checklist. It will not
own implementation, broad refactoring, test execution, supply-chain approval,
or CI diagnosis.

## Specialist 2: Code Test Regression

`code-test-regression` will own tests that prove a feature or bug fix and
protect it from future breakage. It will add decision guidance for:

- choosing unit, integration, contract, end-to-end, or system-level coverage;
- demonstrating RED against the old behavior and GREEN after the change;
- selecting behavior assertions instead of implementation-coupled assertions;
- minimizing fixtures, mocks, snapshots, timing dependence, and shared state;
- scaling targeted and broader verification to blast radius;
- recording skipped, flaky, unavailable, or non-reproducible verification.

Its on-demand reference will be a regression test evidence guide. It will not
grant shell execution, dependency installation, CI reruns, or production test
authority.

## Specialist 3: Research Source Check

`research-source-check` will own claim-level source verification across
research, content, data, product, finance, and public communication workflows.
It will add decision guidance for:

- matching each claim to primary or authoritative evidence;
- source authority, independence, recency, scope, and directness;
- separating sourced facts, calculations, inference, and opinion;
- resolving conflicting sources without silent averaging;
- handling dynamic facts, archived evidence, access limits, and citation drift;
- marking claims verified, qualified, disputed, stale, or unverified.

Its on-demand reference will be a source evidence assessment guide. It will
not fabricate citations, treat search snippets as evidence, bypass access
controls, or replace qualified legal, medical, financial, or regulatory review.

## Existing Routing And Ownership

No bundle or router changes are required:

- `code-review-risk` and `code-test-regression` remain required capabilities in
  `code-review-hardening` and `codebase-change-lifecycle`;
- `research-source-check` remains the overlap primary for source verification
  and a required or preferred capability across research, content, data, and
  governance scenarios;
- existing narrower skills continue to own source lineage, citation maps, CI
  troubleshooting, supply-chain review, and schema validation.

The Safe-Agent Router selected `code-review-hardening` for the combined design
request and covered its required capabilities. It treated the mixed request as
one code-review intent and did not independently select the research skill.
That deterministic intent parsing limit is recorded but intentionally excluded
from this content-depth batch.

## Integrity And Batch History

Each specialist will receive one `references/*.md` file and an
`auxiliary_sha256` manifest hash. `reseal-content` will update sanitized,
auxiliary, and manifest hashes, and `reindex` will update catalog entries
without rewriting unrelated reports.

The three catalog bodies were historically compacted from promoted batch
copies. Their `PROMOTED.md` records, original source hashes, and source commits
must remain unchanged. `batches/index.json` will record each evolved catalog
hash and `content_match: false` while retaining 471 items and 167 historical
compactions.

## Depth And Documentation Outcome

After this batch, the catalog will contain 165 routing cards and 7 specialists.
The three new specialist references raise the specialist reference asset count
from 4 to 7. The depth policy and maintained reports will state that these
skills were promoted due to repeated high-frequency use and decision
complexity, not to inflate all catalog entries uniformly.

## Verification

Each skill must pass:

- a real-catalog depth and auxiliary-integrity regression test;
- `quick_validate.py` for skill directory structure;
- focused depth, registry, and schema checks;
- confirmation that unrelated reports remain unchanged.

The completed batch must pass:

- 165 routing cards, 7 specialists, 0 depth errors, and 0 warnings;
- 172 catalog skills, 166 trusted, 0 tampered, and 0 unknown provenance;
- 471 batch items, 167 historical compactions, and 0 batch issues;
- unchanged Schema v1 task-pack shape and existing router evaluation results;
- the full `scripts/verify.sh` suite locally and on the GitHub Actions Python
  matrix.

## Safety Boundary

These skills provide review and verification methods only. They do not grant
filesystem, shell, network, browser, package, account, credential, publishing,
CI, or production permissions. The host runtime and operator remain the
authority for execution and external access.
