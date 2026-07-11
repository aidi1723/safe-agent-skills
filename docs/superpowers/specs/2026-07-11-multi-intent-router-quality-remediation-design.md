# Multi-Intent Router Quality Remediation Design

Date: 2026-07-11

## Purpose

Raise the deterministic Schema v2 router from a structurally complete
multi-intent implementation to a measurable quality-remediation milestone.
The work must improve real default task-pack behavior, preserve frozen Schema
v1 compatibility, and keep the method-only host permission boundary.

The motivating failure is a real compound request containing UI design, code
review, browser and CI verification, PDF and DOCX work, table analysis, SEO,
and publication checks. The current router treats the entire comma-separated
request as one clause, assigns `data_analysis`, and selects only
`data-analysis-report`. The v2 composer and compiler already support multiple
intents; the deterministic decomposition entry point does not recognize this
common enumeration form.

Fresh baseline evidence on 2026-07-11:

- 100 evaluation cases
- multi-intent exact match: `0.85`
- scenario F1: `0.9447852760736196`
- dependency-edge recall: `0.14285714285714285`
- DAG validity: `0.89`
- forbidden-scenario false-positive rate: `0.08181818181818182`
- repository verification: 355 tests passed

## Goals

1. Decompose common Chinese, English, and mixed-language capability
   enumerations into ordered, independently classified intents.
2. Improve dependency inference for explicit sequencing and verification or
   completion gates without inventing dependencies for parallel work.
3. Make task-type quality, capability recall, and overall production readiness
   machine-decidable.
4. Tighten nested Task Pack v2 schemas so malformed router output fails closed.
5. Expand and govern the evaluation corpus without tuning labels to router
   output.
6. Apply the behavior to the default Schema v2 task pack while preserving
   Schema v1 compatibility.

## Non-Goals

- No semantic or hosted model provider is added.
- No runtime tool execution, permission management, or autonomous publishing
  is added.
- No catalog Skill, scenario bundle, overlap group, or public identifier is
  renamed solely to improve the metrics.
- No broad comma-splitting rule treats every noun list as a task list.
- No production-ready claim is made without a real independent review record.

## Considered Approaches

### Separator-Only Expansion

Treat `,`, `，`, `、`, `and`, `和`, and similar tokens as unconditional intent
boundaries. This is small but unsafe: product features, file types, report
sections, and ordinary object lists would become false tasks. It is rejected
because the current false-positive rate is already above the accepted target.

### Profile-Aware Span Decomposition

Retain existing strong clause boundaries, then look inside broad clauses for
separate spans supported by distinct high-confidence task profiles. Merge
adjacent signals belonging to the same profile, exclude ambiguous generic
signals, and split only when at least two independent profiles survive. This is
the selected approach because it remains deterministic, auditable, and bounded
by the existing profile catalog.

### Semantic Provider Reranking

Use a model to infer intents from free-form text. This may improve recall, but
introduces privacy, cost, nondeterminism, and offline reproducibility concerns.
It remains a later optional layer after the deterministic production quality
gate is satisfied.

## Architecture

The existing routing pipeline remains authoritative:

```text
current-intent normalization
  -> strong clause and list splitting
  -> bounded profile-aware span decomposition
  -> explicit dependency inference
  -> trusted scenario candidate generation
  -> multi-scenario composition
  -> capability resolution
  -> global DAG compilation
  -> strict Task Pack v2 validation
  -> quality evaluation and production gate
```

The decomposition, selection, and orchestration responsibilities stay
separate. `intent.py` determines task intents and dependencies. `composer.py`
selects trusted scenarios for those intents. `compiler.py` consumes a validated
intent graph and produces the execution DAG. Neither the composer nor the
compiler reparses natural language.

Quality-gate calculation belongs in a focused module rather than expanding
`router_eval_v2.py` into another owner module. The evaluator produces raw
per-case results and counts. The quality module computes derived metrics,
threshold outcomes, missing evidence, and the overall gate status.

## Deterministic Decomposition

### Strong Boundaries

Existing numbered or bulleted lists, semicolons, `同时`, `以及`, `then`, and
explicit release boundaries remain the first pass. Their established behavior
and regression tests are preserved.

### Candidate Spans

For a clause still classified as one unit, the router finds profile signals
with source offsets. Candidate spans must satisfy all of these rules:

- the signal belongs to a configured task profile;
- the signal is not an ambiguous generic term such as `report` or `报告`;
- adjacent or overlapping signals for the same profile are merged;
- a span has a distinctive signal score of at least `2`, which corresponds to
  deterministic confidence of at least `0.70` under the current formula;
- a span has one unique winning task type; tied task types remain ambiguous;
- at least two different task profiles survive for the clause.

Connectors such as commas, enumeration punctuation, `and`, `和`, or `/` may delimit
surviving spans, but never create an intent without profile evidence. When the
rules do not establish multiple intents, the original single-clause
classification is retained.

The implementation must use bounded deterministic work. One task may inspect
at most 128 candidate signal matches and emit at most 12 intents. If either
limit is exceeded, the router keeps the first 12 proven intents in source
order, records `candidate_signal_limit_exceeded` or
`intent_limit_exceeded` plus the observed bounded counts, and reports
`incomplete`. It does not claim an exact omitted count after scanning stops and
must not silently truncate a successful route.

### Intent Ordering And Summaries

Emitted intents follow source-text order. Each summary retains the smallest
readable source span that includes the distinctive signal and its local object.
Intent IDs remain `i1`, `i2`, and so on. The existing source and confidence
contracts remain valid.

### Dependencies

Parallel enumerated intents have no dependency merely because one appears
first. Dependencies are created only from explicit relations, including:

- `先 ... 再 ...` or `first ... then ...`;
- `完成后`, `测试通过后`, `验证通过后`, or equivalent English gates;
- release or publication actions explicitly conditioned on earlier work;
- verification actions whose text explicitly names a preceding artifact.

Unknown references are recorded as unresolved dependencies. Cycles, unknown
intent IDs, and missing verification anchors continue to block DAG readiness.

## Task Pack Behavior

Schema v2 uses the improved intent graph by default. Every recognized intent
participates in candidate generation, scenario composition, capability
resolution, and DAG compilation. The router must never collapse a recognized
multi-intent request to one successful scenario merely because a Skill or
intent limit was reached.

Ambiguous or over-limit decomposition produces an auditable reason and an
`incomplete` route. Invalid dependencies, cycles, malformed graph data, or
missing mandatory capability coverage remain fail-closed conditions.
Schema v2 records the decomposition mode, observed candidate count, emitted
intent count, limit flags, and reason codes under
`routing_metrics.decomposition`.

Schema v1 stays frozen. Its public fields, hash shape, and compatibility tests
must not change. The existing v2-to-v1 compatibility boundary may record that
multi-intent information was dropped, but it does not expose new v2 structures
through the v1 contract.

## Quality Metrics And Gate

The evaluator must report finite values and supporting counts for:

- task-type macro precision, recall, and F1;
- scenario precision, recall, and F1;
- required-capability recall;
- forbidden scenario and forbidden Skill false-positive rates;
- multi-intent exact match;
- dependency-edge precision and recall;
- DAG validity;
- high-confidence error rate;
- core bundle Contract v2 coverage.

The `router-eval-v2` JSON result gains a top-level `quality_gate` object. It
contains a status for every metric, a list of missing or failed gates, dataset
and review identities, and an overall `production_ready` boolean. A missing
metric, non-finite value, missing review record, or failed threshold makes
`production_ready` false. This aggregate evaluation result is not embedded in
each ordinary task pack.

The accepted thresholds are:

| Metric | Threshold |
| --- | ---: |
| Task-type macro F1 | at least `0.90` |
| Scenario F1 | at least `0.88` |
| Required-capability recall | at least `0.97` |
| Forbidden scenario or Skill false-positive rate | at most `0.005` |
| Multi-intent exact match | at least `0.80` |
| DAG validity | exactly `1.0` |
| High-confidence error rate | at most `0.02` |
| Core bundle Contract v2 coverage | at least `0.80` |
| Dependency-edge recall | at least `0.90` remediation target |
| Independent label review | valid persisted evidence required |

Dependency-edge recall is both a reported diagnostic and a required target for
this remediation milestone. A future provider-fallback metric is not required
while the only supported provider is deterministic `none`; the task pack must
continue to report that provider boundary explicitly.

## Evaluation Data Governance

The corpus is organized into normal, multi-intent, ambiguous, negative,
multilingual/typo/paraphrase, sequential, and safety-sensitive cases. Before a
production-ready claim, the versioned corpus must contain at least 200 normal
tasks, 80 multi-intent tasks, 50 ambiguous tasks, 50 negative tasks, 40
multilingual/typo/paraphrase perturbations, and 30 safety-sensitive cases, with
at least five cases for every trusted scenario. Sequential cases may also carry
one of the preceding semantic categories, but every reported category count is
derived from explicit case labels. The new cases specifically cover:

- comma, enumeration-punctuation, conjunction, and slash-separated capability
  requests;
- Chinese, English, and mixed-language variants;
- common misspellings and paraphrases;
- ordinary noun and file-type lists that must not split;
- negated, hypothetical, and preflight-only actions;
- explicit parallel, sequential, verification, completion, and publication
  dependencies;
- broad requests that exceed configured intent or Skill limits.

Rule-development cases and held-out acceptance cases are separate. A commit
that changes routing rules must not also relabel held-out cases to match the new
output. Dataset contract validation rejects duplicate IDs, unknown scenarios,
malformed dependency edges, non-finite thresholds, and missing required label
fields.

Independent review evidence is a separate persisted artifact validated by
`schemas/router-eval-review.schema.json`. Accepted records live under
`evals/reviews/` and record the dataset hash, reviewed commit, reviewed case IDs
or declared complete set, a stable reviewer identifier, accountable role,
review time, decision, independence attestation, and exceptions. The reviewer
cannot be the author of the routing-rule commit under review. The implementation
may provide a schema and unsigned template, but it must not fabricate reviewer
provenance. Until a real accepted record exists, the production quality gate
remains false even if all technical metrics pass.

## Schema Tightening

`task-pack-v2.schema.json` replaces broad nested
`additionalProperties: true` allowances with explicit definitions for:

- scenario candidates and score breakdowns;
- selected Skill records and preserved Contract v2 data;
- capability-resolution status, counts, and entries;
- execution graph nodes, edges, statuses, and reason codes;
- routing metrics and decomposition diagnostics;
- registry verification and compatibility records.

Schemas must accept complete, incomplete, and blocked task packs produced by
the implementation and reject unknown nested fields, invalid enums, malformed
IDs, boolean-as-number values, and inconsistent required structures. Existing
valid output examples become fixtures before the schema is tightened.

## Testing Strategy

Testing follows red-green-refactor and includes four layers.

### Unit Tests

- failing reproduction for the real high-frequency compound request;
- span offsets, same-profile merging, generic-signal exclusion, and stable
  source ordering;
- Chinese and English connectors, mixed language, typos, and negation;
- noun-list and file-list false-positive protections;
- parallel and explicit sequential dependency inference;
- deterministic bounds and no silent truncation.

### Integration Tests

- Schema v2 compound tasks select all expected trusted scenarios in intent
  order;
- capability resolution covers required capabilities across composed
  scenarios;
- release gates depend on the verified preceding paths;
- incomplete and blocked routes preserve diagnostics and fail closed;
- Schema v1 fixtures remain byte-shape compatible.

### Evaluator And Schema Tests

- metric math uses explicit micro or macro definitions and zero-denominator
  behavior;
- task-type Macro F1 and required-capability recall have hand-calculated
  fixtures;
- every quality threshold has pass, boundary, fail, missing, and non-finite
  cases;
- dataset and review artifacts are schema validated;
- strict Task Pack v2 schemas accept all supported statuses and reject malformed
  nested records.

### Release Verification

- focused intent, composer, compiler, task-pack, evaluator, and schema tests;
- complete `router-eval-v2` development and held-out runs;
- complete `bash scripts/verify.sh`;
- GitHub Actions on Python 3.11, 3.12, and 3.13.

## Delivery Sequence

1. Freeze the baseline report and add failing real-request and negative-list
   tests.
2. Implement bounded profile-aware span decomposition.
3. Implement explicit dependency inference and close DAG validity failures.
4. Add missing metrics and the focused quality-gate module.
5. Tighten nested Task Pack v2 schemas using current valid fixtures.
6. Expand the evaluation datasets and add dataset/review schemas.
7. Run remediation against development cases without changing held-out labels.
8. Obtain and persist independent review evidence.
9. Run held-out evaluation, full verification, documentation updates, and CI.

If independent review is not yet available, steps 1 through 7 may be delivered
as a technical milestone, but the closure report must state that
`production_ready` remains false and identify the missing review gate.

## Acceptance Criteria

The phase is complete only when:

- the motivating compound request produces multiple correct intents and
  scenarios under default Schema v2;
- ordinary lists and negative cases do not create unrelated scenarios;
- explicit dependencies compile into valid graph edges and parallel work stays
  independent;
- all required metrics and counts are emitted deterministically;
- every technical threshold and the dependency-remediation target passes on
  the held-out corpus;
- Task Pack v2 nested schemas are strict and all supported status fixtures
  validate;
- Schema v1 compatibility tests pass unchanged;
- a genuine independent review artifact passes validation;
- `production_ready` is true only after every gate passes;
- full local verification and the Python CI matrix pass;
- the final report records evidence, remaining risks, and the method-only
  runtime boundary.

## Residual Boundaries

Even after this gate passes, deterministic routing will not understand every
paraphrase or domain-specific request. The router must continue to prefer
incomplete, auditable output over unsupported confidence. Semantic reranking,
runtime enforcement, context compaction, and token-cost optimization remain
separate later milestones.
