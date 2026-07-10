# Delivery Readiness Report

Date: 2026-07-10

## Summary

The deterministic multi-intent Hybrid Router v2 first-milestone structure is
implemented and release-verifiable as a method-only task-pack builder. The
production-ready router quality gate is **not met**.

Current delivery scope is intentionally bounded:

- local skill scanning and sanitization;
- provenance, source usage, and capture metadata validation;
- trusted-only selection and scenario task-pack routing;
- router quality evaluation and summary reporting;
- catalog, bundle, overlap, reference, and claude-skills coverage checks;
- release documentation and GitHub update notes.

## Delivery Gate Status

| Gate | Status |
| --- | --- |
| Catalog trust baseline | Ready |
| Registry integrity verification | Ready |
| Scenario router and task-pack output | Ready |
| Router quality eval suite | Ready |
| Router quality summary metrics | Ready |
| Scanner bypass hardening, Phase 1 slices | Ready |
| Source-import capture schema gate | Ready |
| Claude-skills candidate coverage | Ready |
| External references remain metadata-only | Ready |
| Runtime permission boundary | Ready |
| GitHub release notes | Ready |
| Schema v2 default and frozen independent v1 behavior | Ready |
| Schema v2 invariant safeguard enforcement | Ready |
| Schema v2 bounded CLI failure output | Ready |
| Deterministic multi-intent composition | Structurally complete |
| Core Contract v2 coverage | Ready at 81.25% |
| Curated 100-case v2 evaluation | Ready for structural evidence |
| Independent external label review | Not evidenced |
| Production router quality gate | Not ready |
| Routing-quality remediation | Required before semantic providers |
| Semantic providers | Pending |
| Host runtime replanning | Pending |

## Current Verified Baseline

Fresh milestone verification on 2026-07-10 records 318 passing tests, clean
Ruff lint, a passing `scripts/verify.sh`, explicit v2 invariant safeguard graph
acceptance, 81.25% core Contract v2 coverage, and 43/43 passing Schema v1
regression cases.

The v2 default now fails closed to `incomplete` when a required parsed invariant
cannot be covered by a trusted safeguard skill. All five current invariant
capabilities use effective skill contract stages, and acceptance checks reject
backward pipeline-stage edges. Expected malformed, missing, or structurally
invalid routing assets return stable exit-code-2 JSON or Markdown errors without
tracebacks, absolute temporary paths, or credential values. Credential matching
also avoids redacting benign token-like routing text. Frozen Schema v1 behavior
remains explicitly covered by its existing regression tests and runs
independently rather than as the v2 payload's `to_legacy_v1` projection.

When overlap groups are configured, v2 now validates their structure, trusted
status, and trusted skill references before canonical route hashing. The current
composer does not apply overlap pruning, so the output explicitly records
`routing_metrics.overlap_policy: validated_not_applied`.
Overlap group IDs must be nonempty strings; malformed ID types fail through the
same bounded v2 JSON or Markdown error path.

The manually curated 100-case v2 evaluator currently reports:

| Metric | Current | Target | Status |
| --- | ---: | ---: | --- |
| Multi-intent exact match | 0.85 | 0.80 | Above target |
| Scenario F1 | 0.9448 | 0.90 | Above target |
| Dependency-edge recall | 0.1429 | 0.90 | Major gap |
| DAG validity | 0.89 | 1.00 | Below target |
| Forbidden-scenario false-positive rate | 8.18% | 0.5% maximum | Above limit |

The structural milestone can be complete while the production-ready quality
gate remains unmet. No delivery statement may claim 100% DAG validity or
production readiness.

Production approval also remains blocked because task-type macro F1 and
required-capability recall are not yet reported. A deterministic routing-quality
remediation iteration should precede semantic-provider implementation.
Independent external review of the dataset labels is also not evidenced by a
persisted repository artifact and remains required for production approval.

## Required Quality Remediation

Before semantic-provider implementation, complete a deterministic routing-quality
iteration that:

- reports task-type macro F1 and required-capability recall;
- reduces forbidden scenario or skill false positives to at most 0.5%;
- reaches 1.0 DAG validity;
- improves dependency-edge recall as an additional diagnostic gap.
- obtains and persists independent external review of the curated labels.

## Other Follow-Up Work

These items are useful future work, but they are not required for the current
local-catalog delivery boundary:

- networked `source-import` command that captures upstream content directly;
- host semantic gateway and compact context-record integration;
- semantic provider protocol, privacy controls, reranking, fallback, and
  confidence calibration;
- host execution events, state transitions, approval propagation, and
  method-only replanning;
- documentation consolidation to reduce historical baseline duplication.

Same-day follow-up status: router false-positive / false-negative
classification fields and low-confidence routing trend tracking are now
covered by
[Router Eval Quality Classification](updates/2026-07-03-router-eval-quality-classification.md).
Later follow-up status: first-class contract diagnostics for preconditions,
exclusions, and collisions are now covered by
[Contract Diagnostics](updates/2026-07-04-contract-diagnostics.md).

## Delivery Boundary

This readiness report does not claim the project is a runtime sandbox, malware
detector, live upstream sync service, browser automation platform, connector
runtime, or production deployment system.

Skills remain method guidance. Runtime permissions remain host-owned.
Schema v2 is not an autonomous runtime and is not a semantic router yet.

## Verification Targets

- `bash scripts/verify.sh`
- `PYTHONPATH=src python3 -m onecode_skill_sanitizer schema-check --registry catalog`
- `PYTHONPATH=src python3 -m onecode_skill_sanitizer router-eval --eval evals/router-quality.json --registry catalog --bundles bundles/index.json`
- `PYTHONPATH=src python3 -m onecode_skill_sanitizer maintain-check --registry catalog --bundles bundles/index.json --references external-references/index.json --claude-skills-candidate-map docs/claude-skills-candidate-map.json`
- `PYTHONPATH=src python3 -m onecode_skill_sanitizer verify --registry catalog`
- `git diff --check`
- `PYTHONPATH=src python3 -m onecode_skill_sanitizer contract-check --registry catalog --bundles bundles/index.json --scenario website-build-launch --scenario code-review-hardening --scenario codebase-change-lifecycle --scenario skill-router-quality-review --scenario open-source-release --scenario rag-agent-knowledge-app --scenario document-to-knowledge-base --scenario security-agent-guardrails --minimum-ratio 0.80`
- `PYTHONPATH=src python3 -m onecode_skill_sanitizer router-eval-v2 --eval evals/multi-intent-gold.json --registry catalog --bundles bundles/index.json`
