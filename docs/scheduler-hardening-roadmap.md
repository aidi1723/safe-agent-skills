# Scheduler Hardening Roadmap

Date: 2026-06-06

This document captures the engineering critique of lightweight Markdown skill
systems and turns it into a concrete hardening roadmap for Safe-Agent-Skills.

## Core Diagnosis

A `.agents/skills` or Claude Code-style skill folder is useful, but its base
form is not an industrial scheduler. At its simplest, it is a dynamic system
prompt loader plus optional helper scripts.

That architecture has three hard limits:

- matching is often token or regex based
- multiple loaded skills can contradict each other
- most rules are soft prompt guidance, not runtime enforcement

Safe-Agent-Skills already improves this baseline with provenance records,
trusted status, scenario bundles, overlap groups, `smart` routing, and a
deterministic execution graph. The next stage is to move more control from
model interpretation into local white-box program logic.

## Current Coverage

The current project already addresses part of the problem:

- `smart` reduces manual skill selection and avoids loading the whole catalog.
- Scenario bundles group stable workflows into trusted task packs.
- Low-confidence tasks do not force unrelated scenario bundles.
- Overlap groups prune redundant adjacent skills while preserving required
  gates.
- `execution_graph` gives the host agent a deterministic DAG-shaped plan.
- `reference-check` keeps external ecosystem learning metadata-only.

These are routing and packaging improvements. They are not yet hard runtime
interceptors.

## Remaining Gaps

### 1. Fragile Triggering

Simple keyword matching can misroute tasks when long-context history contains
stale tokens. A user may say to ignore tests, while earlier context still
contains test-related terms. A pure token matcher can then load test guidance
at the wrong time.

Required direction:

- add confidence thresholds for task profiles
- separate current user intent from historical context
- add negative signals and recency weighting
- evaluate router choices against a fixed task suite

### 2. Skill Collision

Skills are currently composed as ordered guidance. That reduces confusion, but
it does not fully model dependency constraints, mutual exclusions, or
contradictory output requirements.

Required direction:

- encode preconditions for bundles and skills
- encode mutual exclusions for incompatible guidance
- require capability coverage before execution
- produce a collision report when two selected skills constrain the same output
  in incompatible ways

### 3. Soft Enforcement

Most skills say what an agent should do. They do not physically stop tool calls,
file writes, unsafe text, malformed JSON, or unsupported publishing actions.

Required direction:

- add semantic gateway assertions before tool execution
- validate structured outputs with schemas
- add content and command interceptors for high-risk domains
- return deterministic system feedback when an assertion fails

### 4. Token and Context Waste

Even correct skills can become expensive if their full instructions remain in
context after their phase is complete.

Required direction:

- summarize completed skill phases into compact evidence records
- flush stale skill text from future task-pack stages where the host supports
  context replacement
- keep only final artifacts, hashes, decisions, and unresolved risks
- track token cost per selected skill or bundle

## Target Architecture

The long-term target is a two-layer scheduler:

```text
Layer 1: deterministic local scheduler
  - task profile
  - confidence score
  - scenario or no-scenario decision
  - dependency graph
  - overlap and collision pruning
  - invariant and verifier gates

Layer 2: runtime semantic gateway
  - tool-call preconditions
  - schema validation
  - command and content assertions
  - policy feedback
  - context compaction records
```

The model should receive the smallest useful pack at the right time. The local
scheduler should decide when a rule is mandatory, incompatible, missing, or
complete.

## Implementation Phases

### Phase 1: Router Quality Evaluation

Create a task set that measures routing quality.

Status: implemented as a first fixed evaluation suite via
`evals/router-quality.json` and the `router-eval` CLI command. The suite is
now part of `scripts/verify.sh`.

Minimum task groups:

- website launch
- code review
- RAG planning
- document conversion
- data analysis
- commerce content
- public claims
- agent security
- skill router review
- vague unsupported tasks

Acceptance criteria:

- known tasks select the intended bundle
- vague tasks select no bundle
- required invariant skills survive `max-skills`
- unrelated website, SEO, or publish skills are not selected for meta-review
  tasks

Current coverage:

- 10 fixed scenario cases covering website launch, code review, RAG, document
  knowledge base, data analysis, commerce, content SEO, agent security, router
  review, and vague unsupported tasks
- expected scenario and task-type checks
- expected skill-presence checks for key workflow gates
- failure exit code for CI use

### Phase 2: Skill Preconditions and Exclusions

Add optional metadata for skills and bundles:

```json
{
  "preconditions": ["workspace_available", "task_is_frontend"],
  "excludes": ["content-copy-compression"],
  "requires_after": ["business-requirements-brief"]
}
```

Acceptance criteria:

- router output includes dependency and collision diagnostics
- selected packs are acyclic
- incompatible skills are pruned or reported

### Phase 3: Semantic Gateway Assertions

Add deterministic validators for high-risk actions.

Candidate validators:

- command risk preflight
- secret redaction
- public claim and advertising wording
- JSON schema output
- markdown link and reference integrity
- publish readiness

Acceptance criteria:

- validators run outside the model
- failures return structured feedback
- failed assertions block promotion to publish or execution-ready states

### Phase 4: Adaptive Context Records

Define compact records for completed skill stages.

Example:

```json
{
  "skill": "design-responsive-viewport-check",
  "status": "complete",
  "evidence": ["viewport smoke test passed"],
  "artifact_hashes": ["..."],
  "open_risks": []
}
```

Acceptance criteria:

- completed stages can be summarized without retaining full prompt text
- task packs distinguish active guidance from completed evidence
- future host integrations can use these records for context pruning

### Phase 5: Host Runtime Integration

Integrate with hosts that can enforce pre-tool-call checks.

Possible integration points:

- Codex approval and sandbox boundaries
- Claude Code hooks where available
- CI checks for catalog, bundle, reference, and schema integrity
- local wrapper scripts for command and content validators

Acceptance criteria:

- skill guidance remains method-only
- enforcement happens in host policy or local scripts
- no skill grants permissions by itself

## Design Rules

- Prefer a smaller correct pack over a larger impressive pack.
- Treat LLM instructions as advisory unless backed by local validation.
- Keep all external references metadata-only until reviewed.
- Make every automatic selection explainable.
- Never confuse routing confidence with execution authority.
- Preserve human approval for trust promotion and external connectors.

## Near-Term Recommendation

The next practical step is Phase 1: a router quality evaluation suite.

That gives the project measurable selection quality before adding more complex
gateway assertions or context-pruning machinery.
