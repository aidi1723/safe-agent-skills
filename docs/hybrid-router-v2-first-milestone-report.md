# Hybrid Router v2 First Milestone Report

Date: 2026-07-10

## Decision

The deterministic multi-intent structural milestone is complete. The
production-ready router quality gate is **not met**.

The gates are separate: structural first-milestone acceptance passes, while
production-ready release approval fails.

Schema v2 decomposes and composes multiple trusted workflows, but remains
method-only. It does not execute selected skills or grant runtime permissions.
It is not an autonomous runtime and is not a semantic router yet.

## Fresh Release Evidence

Commands were run from the `hybrid-router-v2` worktree with its `.venv/bin` at
the front of `PATH` after confirming the system Python lacked the documented
development dependencies.

| Command | Exit | Result |
| --- | ---: | --- |
| `python3 --version` | 0 | Python 3.12.12 |
| `python3 -m ruff check .` | 0 | `All checks passed!` |
| `bash scripts/verify.sh` | 0 | 315 tests passed; schemas, maintenance, v1 eval, v2 eval, contract gate, five-capability invariant stage/edge acceptance, and smoke routes passed |
| `PYTHONPATH=src python3 -m onecode_skill_sanitizer smart "构建官网，同时审计 skill 路由器，验证通过后发布更新" --schema-version 2 --format json` | 0 | Complete route with three required scenarios and an acyclic ready graph |
| `PYTHONPATH=src python3 -m onecode_skill_sanitizer router-eval-v2 --eval evals/multi-intent-gold.json --registry catalog --bundles bundles/index.json` | 0 | 100 cases evaluated; metrics recorded below |
| `PYTHONPATH=src python3 -m onecode_skill_sanitizer contract-check --registry catalog --bundles bundles/index.json --scenario website-build-launch --scenario code-review-hardening --scenario codebase-change-lifecycle --scenario skill-router-quality-review --scenario open-source-release --scenario rag-agent-knowledge-app --scenario document-to-knowledge-base --scenario security-agent-guardrails --minimum-ratio 0.80` | 0 | 39/48 core skills covered; 81.25% |
| `PYTHONPATH=src python3 -m onecode_skill_sanitizer router-eval --eval evals/router-quality.json --registry catalog --bundles bundles/index.json` | 0 | Schema v1 regression: 43/43 passed |
| `PYTHONPATH=src python3 -m onecode_skill_sanitizer smart "构建官网，同时审计 skill 路由器，验证通过后发布更新" --schema-version 1 --format json` | 0 | Legacy output remains available with one primary scenario |

The system Python 3.14.4 attempt correctly failed the release preflight because
`ruff` and development dependencies were not installed. The documented
prerequisite is `python3 -m pip install -e ".[dev]"`.

## Compound Acceptance

The mandatory task decomposed to:

```text
i1 website_build
i2 skill_router_review
i3 open_source_release depends_on [i1, i2]
```

It selected, in intent order:

```text
website-build-launch
skill-router-quality-review
open-source-release
```

The compiled graph was `ready`, `acyclic: true`, with 30 nodes and 31 edges.
Release evidence included both required predecessor paths:

```text
i1 completion -> i3 execution-publish-check
i1 verification -> i3 execution-publish-check
i2 completion -> i3 execution-publish-check
i2 verification -> i3 execution-publish-check
```

The host protocol was `method_only`. Provider fields were `requested: none`,
`used: none`, with
`semantic_provider_not_enabled_in_first_milestone` as the fallback placeholder.

## Invariant Hardening

Schema v2 now parses invariant capabilities through the existing deterministic
mapping and resolves only trusted safeguard skills. Invariant node stages come
from the loaded skill contract `stage_hint`, with deterministic pipeline-stage
fallback, and graph edges never move backward across pipeline stages. This also
covers source and browser verification as verification-stage safeguards. The
invariant capability records are explicit in `capability_resolution`; an
unavailable required safeguard produces `missing` coverage and an `incomplete`
route rather than a false `complete` result.

Route identity sanitization now removes realistic OpenAI-style keys, common
GitHub token prefixes, AWS `AKIA`/`ASIA` access keys, JWTs, and URI passwords
without redacting benign token-like routing text. Schema v2 `smart` and
`task-pack` commands return bounded exit-code-2 JSON or Markdown errors for
malformed JSON and valid-JSON wrong-shape asset or registry failures without
tracebacks, absolute paths, or credential values.

## Contract Coverage

The eight core scenarios cover 39 of 48 referenced skills with complete
Contract v2 metadata: **81.25%**, above the required 80% gate. Nine referenced
skills remain outside complete Contract v2 coverage and are reported by
`contract-check`; future additions to core bundles must preserve the gate.

## Curated Evaluator

`evals/multi-intent-gold.json` contains exactly 100 manually curated cases in a
separate corpus from the copied v1 regression data. The repository declares
`generated_from_router: false`. Its currently enforced literal metadata also
contains `method: manual_review`, `reviewer_role: independent_dataset_review`,
and `reviewed_at: 2026-07-10`; those strings are not evidence of a named or
external reviewer, and no persisted external-review artifact exists in this
repository. Independent external label review remains a production-readiness
gap. Scenario coverage includes every bundle scenario with at least five
expected examples.

| Metric | Current | Target | Assessment |
| --- | ---: | ---: | --- |
| Multi-intent exact match | 0.85 | 0.80 | Above target |
| Scenario precision | 0.9277 | tracked | Baseline |
| Scenario recall | 0.9625 | tracked | Baseline |
| Scenario F1 | 0.9448 | 0.90 | Above target |
| Dependency-edge recall | 0.1429 | 0.90 | Major gap |
| DAG validity | 0.89 | 1.00 | Below target |
| Forbidden-scenario false-positive rate | 8.18% | 0.5% maximum | Above limit |

The evaluator recorded 103 issue instances across 42 cases. The largest classes
were status mismatches, missing dependency edges, intent-order mismatches,
unexpected scenarios, and blocked/DAG coherence failures. These results are
quality evidence, not a command failure: `router-eval-v2` reports current
metrics without pretending the quality targets passed.

## Corrected Acceptance Script

The corrected acceptance commands and assertion block from the implementation
plan were rerun exactly after standardizing selected scenario records on
`scenario_id`. The block also validates 81.25% Contract v2 coverage, both
release dependency paths, the 100-case curated dataset contract, and
finite evaluator output without asserting that the current DAG metric is
already 1.0.

```text
structural first-milestone acceptance: PASS
production-ready quality gate: FAIL
- task_type_macro_f1: not reported
- required_capability_recall: not reported
- forbidden_scenario_false_positive_rate: 8.1818% > 0.5%
- dag_validity: 0.8900 < 1.0
- independent_external_label_review: not evidenced
diagnostic dependency_edge_recall: 0.1429
```

Scenario F1 is 0.9448 and multi-intent exact match is 0.85, so those measured
production thresholds pass. Production approval still fails because of the
listed false-positive, DAG, missing-metric, and external-review evidence gates.

## Compatibility And Safety

Schema v2 is the default. Explicit Schema v1 remains available, and the v1
regression corpus passes 43/43 cases. Migration to v1 is intentionally lossy:
the compatibility view retains one primary scenario and drops secondary
intents, secondary scenarios, and cross-scenario dependency edges.

`route_id` is a canonical SHA-256 correlation identity, not an authorization
token. Recognized secret assignments and bearer values are redacted before
identity hashing. Markdown rendering escapes task-controlled headings, lists,
links, HTML, quotes, code fences, and newlines.

Complete, incomplete, and blocked are distinct contract states. Vague or
unsupported work is incomplete. Cyclic intent graphs are blocked and cannot be
represented as ready execution graphs.

## Pending Work

- Routing-quality remediation: add task-type macro F1 and required-capability
  recall, reduce forbidden false positives, reach 1.0 DAG validity, and improve
  dependency-edge recall before semantic-provider implementation.
- Independent external dataset review: persist reviewer provenance or a review
  artifact rather than inferring independence from repository metadata labels.
- Semantic providers: strict provider protocol, privacy policy, structured
  output, semantic reranking, deterministic fallback, and calibration.
- Host replanning: execution-event schema, transition validation, ready-node
  calculation, approval propagation, and method-only replan integration.
- Quality closure: dependency-edge recall, perfect DAG validity, and forbidden
  scenario false positives must reach their targets before production-ready
  claims are allowed.

The first milestone therefore closes structural implementation and release
verification only. It does not close the production-ready quality gate.
