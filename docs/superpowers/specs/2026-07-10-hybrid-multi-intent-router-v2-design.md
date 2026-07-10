# Hybrid Multi-Intent Router Schema v2 Design

Date: 2026-07-10

Project: `Safe-Agent-Skills`

## Goal

Upgrade the project from a single-primary-scenario deterministic router into a
hybrid, multi-intent skill selection and orchestration system while preserving
the project's method-only safety boundary.

The upgraded system must:

- decompose compound requests into explicit intents and dependencies
- select and compose multiple trusted scenario bundles
- use optional semantic providers for intent refinement and candidate reranking
- preserve deterministic trust, policy, capability, overlap, and approval gates
- compile selected skills into a validated global execution DAG
- expose a machine-readable host execution and replanning protocol
- provide calibrated, independently measured routing quality
- retain a bounded Schema v1 compatibility path

## Product Boundary

The project remains an enhanced router and orchestration compiler. It does not
become an autonomous runtime.

The project owns:

- task normalization
- intent decomposition
- candidate retrieval and ranking
- trusted skill and scenario selection
- capability resolution
- contract validation
- execution graph compilation
- approval and verification gates
- host execution event contracts
- method-only replanning
- routing quality evaluation

The host agent or runtime continues to own:

- filesystem writes
- shell execution
- network requests
- browser automation
- connectors and account access
- credentials
- publishing and production actions
- operator approval collection
- actual skill method execution

Semantic providers provide proposals and scores only. They never grant
permissions, approve skills, override invariants, or execute actions.

## Current Limitations

The current router has strong deterministic foundations, but the following
limitations prevent it from satisfying the target capability:

1. `build_task_profile()` chooses one best task profile, so compound requests
   collapse into a single primary scenario.
2. Signal matching is largely based on curated keywords and aliases, limiting
   paraphrase and out-of-distribution generalization.
3. Most catalog skills do not yet have contract metadata, so orchestration
   frequently falls back to stage and naming heuristics.
4. The execution graph is advisory and lacks a complete machine-readable host
   event and replanning contract.
5. Existing router evaluations are useful regressions but are too small and too
   closely maintained with the routing rules to prove broad generalization.
6. Confidence values are deterministic quality labels rather than calibrated
   estimates tied to measured error rates.

## Design Principles

1. **Deterministic authority:** Trust state, policy, invariants, approvals,
   contract validation, and final admission remain deterministic.
2. **Semantic assistance:** Embeddings or LLMs may split intent and rerank
   bounded candidates, but cannot invent executable skills or scenarios.
3. **Graceful degradation:** Provider absence, timeout, invalid output, or
   network failure must return a valid deterministic route.
4. **Evidence-first routing:** Every selected intent, scenario, skill, score,
   pruning decision, fallback, and warning must be auditable.
5. **Explicit incompleteness:** Missing capabilities or invalid dependency
   graphs must be reported as blocked or incomplete, never hidden.
6. **Backward migration:** Schema v2 becomes the default, while a lossy Schema
   v1 adapter remains available during the migration window.
7. **No mandatory semantic dependency:** The base package remains functional
   with the Python standard library and the existing deterministic catalog.

## Considered Approaches

### Deterministic Rules Only

Continue expanding keyword aliases, profiles, bundles, and contract rules.

Advantages:

- reproducible and inexpensive
- offline by default
- straightforward to audit

Disadvantages:

- does not address paraphrase and semantic generalization well
- increases manual rule maintenance
- remains weak for compound or ambiguous requests

This remains the mandatory fallback but is insufficient as the only router.

### Semantic Model as Primary Router

Delegate decomposition, scenario choice, and skill choice to an LLM.

Advantages:

- strong natural-language interpretation
- simpler initial implementation

Disadvantages:

- weak reproducibility and calibration
- can invent unavailable or untrusted skills
- increases cost, latency, privacy, and availability risk
- conflicts with the project's deterministic safety position

This approach is rejected.

### Hybrid Router

Use deterministic logic for candidate generation and safety authority, with an
optional semantic provider for bounded intent refinement and reranking.

Advantages:

- improves multi-intent and paraphrase handling
- preserves trusted catalog and policy boundaries
- remains operational without a model
- exposes both deterministic and semantic evidence

Disadvantages:

- requires more schemas and evaluation infrastructure
- provider behavior must be isolated and validated
- confidence calibration becomes more complex

This is the selected approach.

## Target Architecture

```text
user task
  -> context normalizer
  -> deterministic intent splitter
  -> optional semantic intent refinement
  -> intent graph
  -> deterministic candidate retrieval
  -> optional semantic reranking
  -> trust and policy gate
  -> multi-scenario composer
  -> capability resolver
  -> contract compiler
  -> global execution DAG
  -> host execution protocol
  -> Schema v2 task pack
```

The pipeline is split into focused modules rather than continuing to grow
`router.py` and `cli.py`.

```text
src/onecode_skill_sanitizer/
  intent.py
  candidates.py
  composer.py
  compiler.py
  contracts.py
  compatibility.py
  execution_protocol.py
  semantic.py
  providers/
    __init__.py
    base.py
    none.py
    local_http.py
    openai_compatible.py
```

Existing routing functions remain available during migration and are gradually
rewired through the new modules.

## Schema v2 Task Pack

Schema v2 becomes the default output of `smart` and the advanced `task-pack`
router modes.

```json
{
  "schema_version": 2,
  "route_id": "sha256:...",
  "routing_mode": "hybrid",
  "provider": {},
  "normalized_task": {},
  "intent_graph": {},
  "scenario_candidates": [],
  "selected_scenarios": [],
  "selected_skills": [],
  "capability_resolution": {},
  "execution_graph": {},
  "host_execution_protocol": {},
  "routing_metrics": {},
  "compatibility": {}
}
```

### Route Identity

`route_id` is a canonical hash of routing-relevant inputs:

- normalized task
- structured current and history context
- invariant declarations
- strategy
- provider mode and model identifier
- catalog index hash
- bundle index hash
- overlap group hash
- router version

Credentials, raw provider secrets, and unrelated workspace state are excluded.

### Intent Graph

```json
{
  "intents": [
    {
      "id": "i1",
      "summary": "Build the product website",
      "task_type": "website_build",
      "required_artifacts": ["website", "release_checklist"],
      "risk_flags": ["public_release"],
      "depends_on": [],
      "source": "deterministic",
      "confidence": 0.91
    },
    {
      "id": "i2",
      "summary": "Review the skill router",
      "task_type": "skill_router_review",
      "required_artifacts": ["review_report"],
      "risk_flags": [],
      "depends_on": [],
      "source": "hybrid",
      "confidence": 0.88
    },
    {
      "id": "i3",
      "summary": "Publish the verified update",
      "task_type": "open_source_release",
      "required_artifacts": ["release_record"],
      "risk_flags": ["public_release"],
      "depends_on": ["i1", "i2"],
      "source": "deterministic",
      "confidence": 0.86
    }
  ],
  "unresolved_dependencies": []
}
```

### Scenario Selection

Schema v2 permits multiple selected scenarios. Each selection records its
supporting intents and score breakdown.

```json
{
  "scenario": "skill-router-quality-review",
  "intent_ids": ["i2"],
  "score": 0.89,
  "score_breakdown": {
    "deterministic_signal": 0.92,
    "taxonomy": 0.90,
    "capability_coverage": 1.0,
    "contract_compatibility": 0.84,
    "semantic_similarity": 0.82,
    "semantic_rerank": 0.86
  }
}
```

### Compatibility

The CLI accepts `--schema-version 1|2`. Schema v2 is the default after the
migration release.

`to_legacy_v1()` converts a Schema v2 route by selecting its primary intent and
highest-ranked scenario. It must record losses explicitly:

```json
{
  "compatibility_loss": {
    "multi_intent_dropped": true,
    "scenarios_dropped": ["skill-router-quality-review"],
    "cross_scenario_edges_dropped": 4
  }
}
```

Schema v1 support remains for at least two minor releases after Schema v2
becomes the default.

## Intent Decomposition

### Deterministic Splitter

The deterministic splitter always runs first and recognizes:

- Chinese and English conjunctions
- sequential markers such as `then`, `after`, `完成后`, and `验证后`
- numbered and bulleted lists
- Markdown checklists
- structured current, history, and stale context
- explicit dependency language
- approval and verification prerequisites

It must avoid splitting noun phrases and closely coupled operations that belong
to one artifact lifecycle.

### Semantic Refinement

The semantic provider receives only bounded routing data:

```python
@dataclass(frozen=True)
class SemanticIntentRequest:
    task: str
    deterministic_intents: tuple[Intent, ...]
    allowed_task_types: tuple[str, ...]
    allowed_scenario_ids: tuple[str, ...]
```

It returns schema-validated proposals:

```python
@dataclass(frozen=True)
class SemanticIntentResponse:
    intents: tuple[IntentProposal, ...]
    confidence: float
    rationale_codes: tuple[str, ...]
```

Semantic output is rejected when it:

- references unknown task types or scenario IDs
- exceeds configured intent limits
- removes deterministic safety or approval intents
- introduces circular dependencies
- fails JSON or schema validation
- falls below the configured confidence threshold

Rejected semantic output is recorded with a reason code and the deterministic
intent graph continues unchanged.

## Semantic Provider Interface

```python
class SemanticProvider(Protocol):
    name: str

    def decompose(
        self,
        request: SemanticIntentRequest,
    ) -> SemanticIntentResponse:
        ...

    def rank(
        self,
        intent: Intent,
        candidates: tuple[RouteCandidate, ...],
    ) -> tuple[SemanticScore, ...]:
        ...
```

Supported modes:

- `none`: deterministic routing only
- `local`: user-configured local HTTP model or embedding endpoint
- `openai-compatible`: remote structured-output API
- `auto`: local provider, then configured remote provider, then `none`

Provider configuration is explicit and credentials remain environment-only:

```toml
[router.semantic]
provider = "auto"
timeout_seconds = 8
minimum_confidence = 0.65
max_intents = 8
remote_data_policy = "task_only"
```

```text
SAFE_AGENT_ROUTER_PROVIDER
SAFE_AGENT_ROUTER_ENDPOINT
SAFE_AGENT_ROUTER_MODEL
SAFE_AGENT_ROUTER_API_KEY
```

The base package retains no mandatory semantic dependency. Optional dependency
groups may provide HTTP or provider SDK support.

## Candidate Retrieval and Hybrid Ranking

Each intent receives candidates from:

- deterministic task-profile signals
- taxonomy similarity
- bundle task signals
- required capability overlap
- direct trusted skill matches
- optional embedding similarity
- optional semantic reranking

The initial scoring policy is:

```text
final_score =
  0.30 * deterministic_signal_score
  + 0.20 * taxonomy_score
  + 0.15 * capability_coverage_score
  + 0.15 * contract_compatibility_score
  + 0.10 * semantic_similarity_score
  + 0.10 * semantic_rerank_score
  - conflict_penalty
  - missing_contract_penalty
  - trust_penalty
```

Rules:

- non-trusted candidates are inadmissible rather than merely penalized
- semantic components contribute no more than 20 percent of the score
- missing required capabilities prevent high-confidence classification
- missing contract metadata lowers orchestration confidence
- every component is recorded in `routing_metrics.score_breakdown`
- weights are configurable only through a validated local policy file

Weights and confidence thresholds must later be calibrated against held-out
evaluation results rather than treated as permanent constants.

## Multi-Scenario Composition

For every intent, the composer keeps a bounded set of trusted scenario
candidates. It then:

1. selects the smallest scenario set covering required intents and capabilities
2. merges duplicate skills while preserving intent attribution
3. applies overlap-group pruning
4. retains mandatory review and verification skills for every affected intent
5. validates cross-scenario conflicts and exclusions
6. creates cross-scenario dependencies from the intent graph
7. records uncovered intents and missing capabilities

The first implementation uses a deterministic greedy set-cover algorithm. A
more complex optimizer is not justified until evaluation proves a need.

If a required intent cannot be covered, the route remains usable for supported
intents but is marked `incomplete`. It cannot claim full task coverage.

## Contract Schema v2

Contract metadata becomes the primary orchestration interface.

```json
{
  "contract": {
    "schema_version": 2,
    "stage_hint": "review",
    "capability_vector": [],
    "requires_context": [],
    "optional_context": [],
    "produces_artifacts": [],
    "produces_evidence": [],
    "requires_after": [],
    "conflicts_with": [],
    "excludes": [],
    "approval_classes": [],
    "estimated_cost": {
      "time": 2,
      "tokens": 1,
      "runtime": 0
    },
    "idempotent": true,
    "retry_policy": "host_decides"
  }
}
```

### Contract Suggestion Workflow

Two commands are introduced:

```text
onecode-skill-sanitizer contract-suggest --registry catalog
onecode-skill-sanitizer contract-check --registry catalog
```

`contract-suggest` uses local metadata and optionally a semantic provider to
produce review artifacts. It does not directly alter trusted manifests.

Suggestions derive from:

- taxonomy
- Skill description and sections
- verifier expectations
- bundle stage and neighboring contracts
- existing artifact vocabulary

Suggested contracts remain review-required until explicitly validated and
applied through the existing trusted maintenance workflow.

### Coverage Gates

Contract coverage CI gates increase in stages:

1. core scenario skills: at least 80 percent
2. all skills referenced by bundles: at least 95 percent
3. all trusted catalog skills: at least 90 percent

Skills without contracts may remain selectable during migration, but routes
using them must expose `stage_fallback` and cannot claim complete dependency
validation.

## Global Execution DAG

The compiler combines:

- intent dependencies
- scenario execution order
- skill contracts
- artifact producer and consumer relationships
- approval classes
- review and verification gates
- overlap and conflict decisions

Each node retains intent and scenario provenance:

```json
{
  "id": "skill:i2:code-test-regression",
  "intent_ids": ["i2"],
  "scenario_ids": ["skill-router-quality-review"],
  "skill": "code-test-regression",
  "stage": "verification",
  "requires": ["routing_selection_plan"],
  "produces": ["regression_test_evidence"],
  "approval_classes": [],
  "host_action": false
}
```

Compilation validates:

- cycles
- missing artifact producers
- incompatible multiple producers
- missing `requires_after` nodes
- approval-sensitive nodes without gates
- required intents without verification nodes
- isolated or unreachable nodes

A cycle or critical missing prerequisite produces `status: blocked`. The
compiler must not silently replace an invalid contract graph with a graph that
appears fully valid. Non-critical contract gaps may use an explicit
`stage_fallback` with warnings.

## Host Execution Protocol

The task pack exposes a method-only protocol consumable by Codex, Claude Code,
OneCode, or another host.

```json
{
  "host_execution_protocol": {
    "mode": "method_only",
    "nodes": [],
    "event_schema": {},
    "completion_policy": {},
    "replan_policy": {}
  }
}
```

Hosts return execution events:

```json
{
  "route_id": "sha256:...",
  "node_id": "skill:i2:code-test-regression",
  "status": "completed",
  "artifacts": [],
  "evidence": [],
  "failed_checks": [],
  "residual_risks": []
}
```

Supported states are:

```text
pending
ready
running
waiting_approval
completed
failed
blocked
skipped
```

The project validates event transitions and computes ready nodes. It never
performs the host action represented by a node.

## Replanning

The CLI adds:

```text
onecode-skill-sanitizer replan \
  --task-pack task-pack.json \
  --events execution-events.json
```

Replanning may:

- remove completed nodes from the ready queue
- propagate failed or blocked prerequisites
- add trusted diagnostic or verification skills when policy allows
- recalculate subsequent ready nodes
- mark affected intents incomplete
- preserve previous route and event evidence

Replanning may not:

- execute a tool
- change a completed event
- bypass approval gates
- admit an untrusted skill
- remove a required invariant
- conceal a failed check

Every replan produces a new route revision linked to the previous `route_id`.

## Evaluation System

The evaluation suite is expanded into independent datasets:

```text
evals/
  router-quality-v2.json
  multi-intent-gold.json
  adversarial-routing.json
  contract-graph-gold.json
```

The initial target dataset contains at least:

- 200 normal tasks
- 80 multi-intent tasks
- 50 ambiguous tasks
- 50 negative tasks
- 40 multilingual, spelling, and paraphrase perturbations
- 30 safety and prompt-injection routing cases
- at least 5 cases for every trusted scenario bundle

Evaluation reports:

- task-type macro F1
- scenario precision, recall, and F1
- skill precision, recall, and F1
- required-capability recall
- forbidden-skill false-positive rate
- multi-intent exact match
- dependency-edge precision and recall
- DAG validity rate
- contract fallback rate
- high-confidence error rate
- provider fallback success rate
- route latency
- provider token and API cost

Gold-set changes require separate review from router rule changes. CI reports
metric regressions rather than only per-case pass or fail.

## Acceptance Criteria

The first production-ready Schema v2 release must meet:

| Metric | Threshold |
| --- | ---: |
| Task-type macro F1 | at least 0.90 |
| Scenario F1 | at least 0.88 |
| Required-capability recall | at least 0.97 |
| Forbidden-skill false-positive rate | at most 0.5% |
| Multi-intent exact match | at least 0.80 |
| DAG validity | 100% |
| High-confidence error rate | at most 2% |
| Provider-failure deterministic fallback | 100% |
| Core bundle contract coverage | at least 80% |

The compound request below is a mandatory acceptance fixture:

```text
构建官网，同时审计 skill 路由器，验证通过后发布更新
```

It must select:

```text
website-build-launch
skill-router-quality-review
open-source-release
```

The release scenario must depend on the verification outputs of both preceding
scenarios.

## Delivery Phases

### Phase 0: Schema and Baseline

- freeze current tests and router evaluation output
- introduce Schema v2 data models and JSON Schemas
- implement Schema v1 conversion
- add v2 metric reporting without changing current routes

Estimated effort: 3 to 4 engineering days.

### Phase 1: Deterministic Multi-Intent Routing

- implement intent and dependency parsing
- produce multiple scenario candidates
- compose multiple selected scenarios
- compile a global execution DAG
- add compound-task acceptance fixtures

Estimated effort: 5 to 7 engineering days.

### Phase 2: Contract Expansion

- implement Contract Schema v2
- add contract suggestion and coverage checks
- cover at least 80 percent of core scenario skills
- then cover at least 95 percent of bundle-referenced skills

Estimated effort: 7 to 10 engineering days.

### Phase 3: Semantic Providers

- implement provider protocol and deterministic `none` provider
- implement local HTTP provider
- implement OpenAI-compatible provider
- add timeout, schema rejection, privacy, and fallback tests
- calibrate hybrid scoring against held-out data

Estimated effort: 5 to 8 engineering days.

### Phase 4: Host Protocol and Replanning

- define execution event schemas and transitions
- calculate ready and blocked nodes
- implement method-only `replan`
- add host integration examples

Estimated effort: 5 to 7 engineering days.

### Phase 5: Independent Evaluation and Release Gate

- expand the evaluation corpus
- add aggregate quality metrics
- enforce CI thresholds
- publish a measured capability report

Estimated effort: 5 to 8 engineering days.

The total estimate is 25 to 40 engineering days. The recommended first
milestone includes Phases 0, 1, and the core-contract portion of Phase 2 before
semantic providers are enabled.

## First Milestone

The first milestone delivers the highest-value structural improvements without
requiring a model:

1. Schema v2
2. deterministic multi-intent decomposition
3. multi-scenario composition
4. global execution DAG
5. Schema v1 compatibility conversion
6. at least 100 new multi-intent and negative evaluation cases
7. at least 80 percent contract coverage for core bundle skills

Semantic providers are integrated only after this deterministic foundation is
passing and measurable.

## Failure Handling

| Failure | Required behavior |
| --- | --- |
| Provider unavailable | Record fallback and continue deterministically |
| Provider timeout | Discard semantic result and continue deterministically |
| Invalid semantic schema | Record rejection reason and continue deterministically |
| Unknown scenario or skill proposal | Reject proposal before ranking |
| Missing required capability | Mark affected intent incomplete |
| Contract cycle | Mark route blocked and report cycle |
| Missing critical producer | Mark dependent nodes blocked |
| Missing non-critical contract | Use explicit stage fallback with warning |
| Approval required | Mark node `waiting_approval`; never execute |
| Host event conflict | Reject event and retain previous state |

## Security and Privacy

- Remote providers receive only the data permitted by `remote_data_policy`.
- Credentials are never serialized into task packs, logs, or route hashes.
- Provider responses are untrusted input and must pass strict parsing and
  allow-list validation.
- Prompt content inside imported skills is never sent to a semantic provider
  unless an operator explicitly enables that policy.
- Trusted skill status remains determined by the existing registry workflow.
- Runtime permissions remain controlled by the host environment.

## Non-Goals

This design does not:

- implement a shell, browser, connector, or publishing runtime
- execute selected Skill instructions
- automatically approve suggested contracts
- automatically trust imported skills
- require an LLM or embedding service
- replace deterministic invariants with model judgments
- optimize the DAG using an external solver in the first release
- remove Schema v1 immediately
- treat confidence as calibrated until held-out evaluation proves it

## Documentation Deliverables

Implementation must update:

- `README.md`
- `docs/smart-skill-router.md`
- `docs/agent-task-pack.md`
- `docs/router-development.md`
- `docs/operator-guide.md`
- `docs/architecture.md`

It must add host examples for deterministic-only, local-provider, remote-provider,
and provider-fallback operation.

## Final Positioning

After this design is implemented, the accurate product description is:

> A trusted hybrid skill router and orchestration compiler that decomposes
> multi-intent tasks, composes verified skill workflows, emits auditable host
> execution contracts, and degrades safely without a semantic provider.

It remains intentionally distinct from a complete autonomous Agent Runtime.
