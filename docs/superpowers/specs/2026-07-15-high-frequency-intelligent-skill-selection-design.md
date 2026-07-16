# High-Frequency Intelligent Skill Selection Design

Date: 2026-07-15

> **Delivery status (2026-07-16):** Structural delivery for the opt-in Router
> v3 cohort path is **closed** on local `main` at structural tip `6710ba8`.
> Validation-split
> acceptance **passed**. The one permitted `final_test` one-shot **failed**
> (`final_acceptance_failed`). Three-arm task oracle evidence is **missing**
> (`task_evaluation_missing`). Semantic influence remains disabled on the
> public CLI. v2 remains the default schema.
>
> Wrap-up evaluation rigor beyond the original list: dependency edges use
> **exact set equality**; aggregate `dependency_edge_precision` is tracked with
> the same `>= 0.70` floor as recall; task-pack v3 candidates are bounded to
> `maxItems: 7` with a `cohortSkillName` enum.
>
> Authoritative gate status:
> [v3 Closure Report](../../high-frequency-intelligent-skill-selection-v3-closure-report-2026-07-16.md).
> This design remains the normative intent for the milestone; it does not
> override the closure report's delivery verdict.

## Outcome

Improve skill-selection intelligence for the router and an initial cohort of
high-frequency trusted skills. The new selector must decide whether a skill is
needed, distinguish adjacent skills, compose only skills with marginal value,
construct real dependencies, and abstain or clarify when confidence is low.

Execution speed, token count, task-pack size, and full-catalog optimization are
explicitly outside this milestone. They may be measured for diagnostics, but
they are not acceptance criteria.

## Context

The current catalog contains 172 skills, including 166 trusted skills and 23
trusted scenario bundles. The deterministic router provides strong scenario
recall but still treats scenario membership too much like an all-or-nothing
execution plan.

Fresh baseline evidence gathered during design:

- Router v1 evaluation: 43 of 43 declared cases pass.
- Router v2 evaluation: 100 cases.
- Scenario precision: 0.927710843373494.
- Scenario recall: 0.9625.
- Scenario F1: 0.9447852760736196.
- Multi-intent exact match: 0.85.
- DAG validity: 0.89.
- Dependency-edge recall: 0.14285714285714285.
- Forbidden-scenario false-positive rate: 0.08181818181818182.

The v2 negative cases demonstrate important failure modes. Negated requests
such as "do not publish" or "do not build a website" may still select the
corresponding scenario. Vague requests can be forced into unrelated scenarios,
and the compiler commonly creates scenario-order edges instead of evidence of
real data dependencies.

The existing v2 task-pack schema cannot truthfully represent a semantic
provider. Its provider fields are fixed to `none`, and its top level rejects
additional properties. v1 and v2 therefore remain frozen compatibility
contracts; intelligent selection is introduced as an opt-in v3 contract.

## Community Evidence

This design adapts methods rather than importing community runtime code.

### Agent Skills Specification

Source: https://github.com/agentskills/agentskills

Reviewed commit: `38a2ff82958afee88dadf4831509e6f7e9d8ef4e`

Adopt:

- progressive disclosure driven by concise name and description metadata;
- realistic positive and near-miss negative trigger cases;
- held-out evaluation rather than tuning against every known query;
- explicit measurement of whether skill use improves the output.

Do not adopt:

- automatic trust in locally discovered or community-provided skills.

### MetaTool

Source: https://github.com/HowieHwong/MetaTool

Reviewed commit: `35e81bb7576826e980c80fed8f8c0a2b4a1e6fbb`

Adopt the separation between tool-use awareness and tool selection. The router
must first decide whether specialized skill guidance is needed, then decide
which skill or skill set is appropriate.

### Tool2Vec And ToolRefiner

Source: https://github.com/SqueezeAILab/Tool2Vec

Reviewed commit: `5e8e7986b19d3c623d36bd20a50d5a400310c5db`

Adopt:

- usage-example-driven candidate representation;
- staged recall and refinement;
- Recall@K and ranking metrics;
- domain-specific evaluation sets.

The first milestone uses audited examples and deterministic evidence as the
primary representation. An optional semantic provider may rerank the trusted
candidate set but may not expand it.

### OpenSquilla

Source: https://github.com/opensquilla/opensquilla

Reviewed commit: `b679e593cb31186b4707aa92d08578bd70854c86`

Adopt:

- explicit MetaSkill composition only for repeatable workflows;
- abstention and manual activation for uncertain compositions;
- parallel treatment of steps without dependencies;
- enforced DAG, recursion, and risk boundaries at the runtime boundary.

Do not adopt its model router, runtime, connectors, credentials, or execution
permissions into this method-only router.

### SkillsBench

Source: https://github.com/benchflow-ai/skillsbench

Reviewed commit: `13170e74a32ea01fb15bc344b766e77bec498de3`

Adopt:

- clean isolation between available, selected, and actually used skills;
- gold or oracle skill-pack comparison;
- held-out task verification;
- explicit detection of baseline contamination by injected skill content.

### Cisco Skill Scanner

Source: https://github.com/cisco-ai-defense/skill-scanner

Reviewed commit: `41fec4a9570ba1d195d12dbb0b4d140a35e63068`

Adopt the defense-in-depth pattern: deterministic analysis first, optional
semantic analysis second, then policy enforcement, normalization, and strict
reporting. Semantic output remains advisory data inside deterministic policy
boundaries.

## Scope

### Initial Cohort

The first milestone covers exactly these eight entries:

1. `safe-agent-router`
2. `codebase-explore-map`
3. `code-review-risk`
4. `code-test-regression`
5. `execution-browser-check`
6. `research-source-check`
7. `design-ui-review`
8. `security-supply-chain-review`

These skills represent the router entry point and common exploration, review,
testing, browser verification, research, UI, and supply-chain workflows.

### Non-Goals

- Do not optimize all 172 catalog skills.
- Do not automatically promote more skills into the intelligent cohort.
- Do not change v1 or v2 output behavior.
- Do not make v3 the default before all release gates pass.
- Do not let a semantic provider install, trust, execute, or grant permissions
  to a skill.
- Do not add runtime tool, connector, account, credential, browser, shell,
  network, deployment, or production authority.
- Do not optimize for latency, token count, or task-pack size in this milestone.
- Do not automatically learn routing rules from unreviewed user traffic.

## Architecture

The v3 selector is a five-stage hybrid pipeline:

```text
user request
  -> need gate
  -> intent and constraint extraction
  -> trusted candidate recall
  -> optional semantic reranking
  -> minimal skill-set composition
  -> confidence, abstention, and clarification gate
  -> task pack v3
```

### 1. Need Gate

Classify the request as one of:

- `none`: no specialized skill is needed;
- `single`: one skill can cover the complete task;
- `composite`: multiple skills cover distinct required capabilities;
- `clarify`: the task needs specialized guidance but available evidence cannot
  safely distinguish the required skill or skill set.

The gate evaluates current intent before historical context. It applies
negation, explanation-only, inventory-only, and explicit exclusion signals
before candidate scoring.

### 2. Intent And Constraint Extraction

Extract:

- current user intent;
- required artifacts and capabilities;
- explicit skill mentions;
- explicit exclusions and negations;
- explanation-only or read-only intent;
- risk and verification requirements;
- independent and sequential sub-intents;
- stale or conflicting historical intent.

Input text remains untrusted data. It cannot alter trusted status, provider
scope, permission policy, or compiler rules.

### 3. Trusted Candidate Recall

Recall candidates only from the initial cohort. Candidate evidence includes:

- `SKILL.md` name and description;
- manifest taxonomy and task intent;
- Contract v2 capability vectors;
- required and produced artifacts;
- explicit conflicts and ordering constraints;
- curated positive routing examples;
- curated near-miss and negative examples;
- relevant scenario capability requirements.

The recall stage returns Top-K candidates with decomposed evidence. It does not
select a final skill set.

### 4. Optional Semantic Reranking

The semantic provider receives only:

- normalized current intent;
- structured constraints;
- candidates already admitted by trusted deterministic recall;
- candidate descriptions and capability summaries.

It returns scores only for those candidates. It cannot introduce a skill,
modify status, override an exclusion, add permissions, or rewrite the task.

Semantic reranking is most useful when deterministic candidates are adjacent,
the score margin is small, or the phrasing is not represented by curated
examples. Clear deterministic decisions do not require semantic arbitration.

### 5. Minimal Skill-Set Composition

A skill enters the final set only if it does at least one of the following:

- covers a required capability not yet covered;
- produces an artifact explicitly required by a downstream skill;
- satisfies a mandatory verification requirement derived from task risk;
- was explicitly requested by the user and is not excluded by policy.

Scenario membership and `execution_order` alone are insufficient reasons for
selection.

Dependency edges come only from:

- `requires_context` matched to `produces_artifacts` or
  `produces_evidence`;
- `requires_after`;
- explicit user ordering;
- mandatory safety or verification preconditions.

Skills without such dependencies remain parallel nodes.

## Components

The implementation plan should preserve focused ownership boundaries. Final
filenames may follow existing module patterns, but responsibilities remain:

### Need Decision

Own:

- need classification;
- current-versus-stale intent policy;
- negation and explanation-only suppression;
- clarification reason codes.

### Candidate Retrieval

Own:

- cohort filtering;
- deterministic feature extraction;
- training-example matching;
- Top-K recall;
- evidence records for every candidate.

### Semantic Provider Boundary

Own:

- provider protocol and configuration;
- request redaction and candidate-scope enforcement;
- response schema validation;
- score normalization;
- fallback reason codes.

### Selection And Composition

Own:

- deterministic and semantic score combination;
- hard exclusions and conflicts;
- marginal capability coverage;
- exact selected-skill set;
- dependency construction.

### Confidence And Abstention

Own:

- threshold and score-margin policy;
- `none`, `clarify`, `incomplete`, and `blocked` decisions;
- final selection rationale;
- rejected-candidate rationale.

### Task-Pack v3

Own:

- strict schema;
- route identity;
- provider evidence;
- selection trace;
- execution graph;
- v3-to-v2 and v3-to-v1 compatibility-loss reports.

## Data Design

### Existing Sources Of Truth

Continue using:

- `SKILL.md` for user-intent-facing description and skill instructions;
- `skill.json` for identity, taxonomy, trust, provenance, policy, hashes, and
  contracts;
- `bundles/index.json` for reusable scenario capability requirements;
- Contract v2 for capabilities, inputs, outputs, conflicts, and order.

Do not duplicate these fields in a new profile format.

### Runtime Routing Examples

Add `catalog/routing-examples.json` for the initial cohort only. It contains
reviewed training examples and near-misses used by deterministic example
retrieval. Each record includes:

- stable example id;
- query;
- expected need decision;
- required skills;
- forbidden skills;
- relevant intent and capability labels;
- example class: positive, near-miss, negation, explanation-only, or
  composition;
- review metadata and source classification.

This file is part of route identity and catalog verification. Only reviewed
examples may affect runtime routing.

### Held-Out Evaluation Data

Add `evals/high-frequency-skill-selection.json`. Runtime code must never read
this file. It contains validation and final-test cases with:

- stable case id and category;
- realistic query;
- expected need decision;
- expected intents;
- required, allowed, and forbidden skills;
- expected dependency edges;
- expected routing status;
- expected clarification or abstention reason when applicable;
- fixed validation or test split.

The final-test labels are not exposed to description, rule, weight, or prompt
optimization.

## Task-Pack v3 Contract

v3 is opt-in through `--schema-version 3`. Its strict top-level contract
includes:

- `schema_version`;
- `route_id`;
- `routing_mode`;
- `routing_status`;
- `provider`;
- `normalized_task`;
- `need_decision`;
- `intent_graph`;
- `candidates`;
- `selection`;
- `capability_resolution`;
- `execution_graph`;
- `confidence`;
- `host_execution_protocol`;
- `routing_metrics`;
- `registry_verification`;
- `compatibility`.

### Provider Record

Record:

- `requested`;
- `used`;
- `model_or_adapter`;
- `fallback_reason`;
- `candidate_scope_hash`;
- provider response status;
- provider validation reason codes.

### Candidate Record

Every admitted candidate records:

- skill name and trusted identity;
- deterministic score;
- semantic score when available;
- final score;
- matched intents and capabilities;
- matched examples;
- positive evidence;
- penalties and exclusions;
- selected or rejected status;
- reason codes.

### Selection Record

Record:

- need decision;
- selected skills;
- marginal capability contribution per skill;
- rejected adjacent candidates;
- conflict resolutions;
- clarification or abstention reason;
- confidence and score margins.

## Decision Rules

Apply decisions in this order:

1. Verify registry and cohort identity.
2. Apply trusted-status, explicit exclusion, policy, and conflict hard filters.
3. Compute the need decision.
4. Extract current intents and constraints.
5. Recall trusted Top-K candidates.
6. Invoke semantic reranking only when configured and useful.
7. Validate provider output and enforce candidate scope.
8. Combine deterministic and semantic evidence.
9. Compose the minimum capability-complete skill set.
10. Compile real dependency edges.
11. Apply confidence, abstention, clarification, incomplete, and blocked gates.
12. Emit v3 plus explicit compatibility loss.

### Positive Evidence

Score evidence includes:

- intent and task-type match;
- required capability coverage;
- description match;
- reviewed positive-example match;
- scenario capability support;
- explicit user selection.

### Hard Exclusions Or Strong Penalties

Apply for:

- explicit negation;
- reviewed near-miss examples;
- explanation-only or inventory-only intent;
- skill conflicts;
- missing required inputs;
- untrusted, disabled, tampered, or out-of-cohort skills;
- stale historical intent contradicted by the current request.

Deterministic evidence remains primary. Semantic weighting is calibrated only
on training and validation data, never on the final test split.

## Failure Handling

### Semantic Provider Failure

- Unavailable, timeout, or transport failure: use deterministic ranking and
  record fallback.
- Unknown or out-of-scope skill: reject the complete semantic response.
- Duplicate candidates: reject the complete semantic response.
- Non-numeric, non-finite, or out-of-range score: reject the complete semantic
  response.
- Schema mismatch: reject the complete semantic response.
- Low-confidence semantic result: retain deterministic ordering.

Provider failures do not make a deterministic route fail unless deterministic
evidence is independently incomplete.

### Selection Failure

- No skill needed: return `none` rather than an empty successful composition.
- Required capability uncovered: return `incomplete` and name the gap.
- Mutually exclusive candidates with insufficient margin: return `clarify`.
- Low confidence with no specialized need: return `none`.
- Low confidence with clear specialized need: return `clarify`.
- Missing upstream artifact producer: return `incomplete`.
- Cyclic or invalid dependency graph: return `blocked`.

The router never substitutes an adjacent skill merely to produce a complete
task pack.

### Feedback Safety

Runtime traces may identify candidate examples for later review. They must be
redacted, task-local, and non-authoritative. No trace becomes a routing rule or
training example until an operator reviews and commits it.

## Evaluation Design

### Dataset

Create 120 held-out cases for the initial cohort:

- 48 single-skill positive cases;
- 24 adjacent-skill near-miss cases;
- 16 no-skill, negation, and explanation-only cases;
- 16 multi-skill composition cases;
- 16 ordering, dependency, and conflict cases.

Include Chinese, English, mixed language, typos, abbreviations, casual phrasing,
explicit skill requests, current-versus-history conflict, unknown domains, and
requests outside the intelligent cohort.

### Verification Layers

#### Unit Layer

Verify:

- need decisions;
- negation and explanation-only detection;
- hard filters;
- conflict handling;
- provider result validation;
- deterministic fallback;
- score bounds and reason codes.

#### Retrieval Layer

Measure:

- Top-1 accuracy;
- Recall@3;
- mean reciprocal rank;
- adjacent-skill discrimination;
- no-skill decision accuracy.

#### Composition Layer

Measure:

- exact selected-skill set;
- required capability coverage;
- forbidden-skill false positives;
- dependency-edge recall;
- DAG validity;
- correct incomplete, blocked, none, and clarify states.

#### Task Layer

Run representative tasks using:

- the v3 selected skill pack;
- an independently curated gold or oracle pack;
- a clean no-skill condition when applicable.

Verify final task artifacts and requirements. Keep baselines isolated so skill
content cannot leak into no-skill runs.

### Provider Test Modes

- `none`: deterministic baseline;
- `fake`: malformed output, timeout, unknown candidate, duplicate candidate,
  invalid score, and low-confidence fixtures;
- actual semantic provider: isolated evaluation and shadow mode only until all
  gates pass.

## Acceptance Criteria

The v3 milestone must meet all of these on held-out data:

- forbidden-scenario false-positive rate below 0.02;
- DAG validity at least 0.98;
- dependency-edge recall at least 0.70;
- dependency-edge precision at least 0.70 (wrap-up rigor: exact edge-set
  equality at the case level; unexpected edges fail the case);
- multi-intent exact match at least 0.92;
- scenario F1 at least 0.96;
- high-frequency skill Recall@3 at least 0.95;
- high-frequency skill Top-1 accuracy at least 0.90;
- no-skill decision accuracy at least 0.90;
- exact selected-skill set accuracy at least 0.85;
- no critical task assertion passed by the gold or oracle pack may fail because
  of an incorrect v3 selection;
- aggregate v3 task pass rate must be at least 95% of the gold or oracle pass
  rate and no more than five percentage points lower;
- no semantic-provider path can add an out-of-scope or untrusted skill;
- v1 and v2 compatibility tests remain unchanged and passing.

Latency, token use, and output size are not release gates for this milestone.

## Rollout

### Phase 1: Freeze Baseline

Preserve current v1 and v2 fixtures, payload-shape checks, and metrics. Record
the v2 baseline in a machine-readable artifact.

### Phase 2: Deterministic v3

Implement the Need Gate, routing-example retrieval, hard exclusions, marginal
capability composition, confidence states, and v3 schema without a semantic
provider.

### Phase 3: Semantic Shadow Mode

Run deterministic selection and semantic reranking together, but continue
using the deterministic result. Record disagreements, invalid provider output,
and gold-label comparison.

### Phase 4: Opt-In Semantic Influence

Allow semantic scores to affect v3 selection only after shadow evaluation meets
all acceptance gates. Keep deterministic fallback mandatory.

### Phase 5: Default Decision

After sustained held-out and task-level success, make a separate reviewed
decision about setting v3 as the default. This milestone does not make that
decision automatically.

## Risks And Controls

### Semantic Opacity

Control with candidate-scope enforcement, decomposed scores, reason codes,
shadow mode, and deterministic fallback.

### Evaluation Overfitting

Control with separate runtime examples, validation cases, and final-test cases.
Do not expose final-test failures to tuning.

### Metadata Duplication

Keep identity, trust, taxonomy, provenance, policy, and contracts in existing
sources of truth. The routing-example file stores examples only.

### False Confidence

Expose confidence and margins. Prefer `none` or `clarify` over forced
selection.

### Catalog Scope Creep

Keep an explicit cohort allowlist. Adding another skill requires demonstrated
high-frequency demand, new examples, held-out cases, and operator approval.

### Baseline Contamination

Use isolated task runs and verify that no-skill trajectories contain no skill
injection or invocation evidence.

## Verification And Release Gates

Implementation planning must include:

- schema validation for v3 and provider responses;
- focused unit and integration tests;
- existing v1 and v2 regression suites;
- the current 100-case v2 gold evaluation;
- the new high-frequency held-out evaluation;
- task-level selected-pack versus oracle evaluation;
- registry, manifest, provenance, hash, batch, depth, and contract checks;
- documentation link and private-path checks.

The current workspace does not have the optional development dependencies
`jsonschema` and `ruff` installed. The design review observed 290 executable
standard-library tests plus three import errors caused by missing
`jsonschema`. Implementation verification must install the declared `dev`
extra and run the complete release gate before making passing claims.

## Resolved Decisions

- Optimize intelligent selection rather than execution time.
- Limit the milestone to the router and eight high-frequency skills.
- Use a hybrid deterministic and optional semantic architecture.
- Keep semantic selection inside trusted deterministic candidate boundaries.
- Preserve v1 and v2 and introduce opt-in v3.
- Make abstention and clarification first-class outcomes.
- Require held-out routing and task-level evaluation before semantic influence.
- Do not expand to the full catalog without a separate evidence-backed review.
