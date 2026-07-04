# Maintenance Log

Date: 2026-07-04

## Current Maintained Baseline

```text
branch: main
catalog skills: 172
trusted skills: 166
trusted scenario bundles: 23
external references: 19
trusted overlap groups: 7
tracked claude-skills candidates: 336
covered claude-skills candidates: 336
router eval cases: 42
verification command: bash scripts/verify.sh
```

## 2026-07-04 Maintenance Boundary Refactor

Continued the project-wide maintenance pass by reducing `cli.py` ownership and
documenting the maintenance workflow.

Code boundaries added or clarified:

- `onecode_skill_sanitizer.paths` owns repository asset path resolution and
  `SAFE_AGENT_SKILLS_HOME` support.
- `onecode_skill_sanitizer.validation` owns manifest hashing, sealing, and
  pure schema validation.
- `onecode_skill_sanitizer.references` owns external reference index loading
  and metadata-only reference validation.
- `cli.py` remains the command orchestration layer and compatibility wrapper.

Maintenance docs updated:

- [Maintenance Guide](maintenance-guide.md)
- [Module Boundary Refactor Plan](module-boundary-refactor-plan.md)

Verification target for this maintenance slice:

```text
PYTHONPATH=src python3 -m unittest discover -s tests -v
ruff check .
bash scripts/verify.sh
git diff --check
```

## 2026-07-04 Router Skill Script Resolution

Locked down the `skill-router-quality-review` bundle's real-catalog
`supply_chain_review` coverage and corrected the repository-local router skill
script path resolution.

Changes:

- Added a real-catalog regression asserting `security-supply-chain-review`
  covers the required `supply_chain_review` capability with no missing required
  coverage for `skill-router-quality-review`.
- Updated `integrations/skills/safe-agent-router/scripts/task_pack.sh` to prefer
  the repository beside the script before falling back to `SAFE_AGENT_SKILLS_HOME`.
- Documented the script-local repository precedence in the router skill README.

Why this matters: a globally exported `SAFE_AGENT_SKILLS_HOME` can point at an
older checkout during development. Repository-local script resolution keeps the
checked-out integration script aligned with the code and catalog under review.

Verification evidence:

```text
targeted regression tests: 2 tests OK
repository task_pack.sh with stale SAFE_AGENT_SKILLS_HOME: selected skill-router-quality-review and security-supply-chain-review
ruff check .: OK
PYTHONPATH=src python3 -m unittest discover -s tests -v: 164 tests OK
bash scripts/verify.sh: 164 tests OK
git diff --check: clean
```

## 2026-07-04 Structured Context Routing

Added a structured context summary contract for router task text.

Task strings can now include explicit `current_intent`, `history_summary`, and
`stale_context` fields. The router uses current intent as the primary signal,
keeps history as weak context, and records stale context while excluding it
from scenario selection, direct skill matching, and runtime approval-gate
task-signal checks.

Routed outputs now expose:

- `structured_context_detected`;
- `stale_context_text`;
- `stale_context_policy`.

Reusable router-eval coverage was extended with
`structured-context-stale-history-vague-current-intent`.

Final verification evidence:

```text
bash scripts/verify.sh: 157 tests OK
schema-check --registry catalog: OK, 172 manifests
tests.test_router: 57 tests OK
router-eval: 41 / 41 cases OK
by_confidence.high: 36 passed, 0 failed
by_confidence.low: 5 passed, 0 failed
low_confidence_case_count: 5
low_confidence_failed_count: 0
by_issue_class: {}
maintain-check: OK with 23 trusted bundles, 19 references, and 336 / 336 claude-skills candidates covered
verify --registry catalog: 172 skills, 166 trusted, 0 tampered, 0 unknown provenance
```

Update note:
[Structured Context Routing](updates/2026-07-04-structured-context-routing.md).

## 2026-07-04 Current Intent Routing

Added current-intent weighting and deterministic low-confidence explanations to
the router.

When task text contains explicit history/current markers, the router now scores
the current request as the primary intent and keeps historical context as weak
context. This prevents stale historical website, publish, browser, or test
signals from forcing an unrelated scenario for vague current follow-up
requests.

Routed outputs now expose:

- `current_intent_detected`;
- `current_intent_text`;
- `history_context_text`;
- `current_intent_weight`;
- `history_context_weight`;
- `selection_quality.reason_codes`;
- `selection_quality.explanations`;
- `selection_quality.recommended_actions`;
- `pipeline_plan.low_confidence_reasons`.
- runtime approval gates use current request text for task-signal checks when
  a history/current split is detected.

Real catalog baseline after the update:

```text
bash scripts/verify.sh: 154 tests OK
router-eval: 40 / 40 cases OK
by_confidence.high: 36 passed, 0 failed
by_confidence.low: 4 passed, 0 failed
low_confidence_case_count: 4
low_confidence_failed_count: 0
by_issue_class: {}
```

Update note:
[Current Intent Routing](updates/2026-07-04-current-intent-routing.md).

## 2026-07-04 Stage Acceptance

Accepted the current milestone as ready for handoff.

Acceptance report:
[Stage Acceptance Report](stage-acceptance-report-2026-07-04.md).

The report records the delivered router, contract-diagnostics,
`contract.requires_after`, router-eval, scanner, source-import capture, and
publication-documentation improvements, plus the current verification baseline.

## 2026-07-04 Requires After Contract Ordering

Added explicit `contract.requires_after` ordering metadata to schema
validation, contract graph construction, and routed task-pack diagnostics.

Routed outputs now include missing ordering diagnostics with:

- `missing_ordering_count`;
- `missing_ordering`;
- source records pointing to `contract.requires_after`.

Selected `requires_after` predecessors now become `contract_requires_after`
graph edges, so contract topology can order skills even when no artifact
dependency exists between them.

Update note:
[Requires After Contract Ordering](updates/2026-07-04-requires-after-contract-ordering.md).

## 2026-07-04 Contract Diagnostics

Added first-class contract diagnostics to scenario and mesh routed task packs.

Routed outputs now include `contract_diagnostics` with:

- missing preconditions from `contract.requires_context`;
- explicit exclusions from `contract.excludes`;
- legacy conflicts from `contract.conflicts_with`;
- contract graph fallback or cycle issues.

The same diagnostics are rendered in JSON, Markdown task packs, and agent
instructions. This keeps skill contracts advisory and method-only while making
precondition and collision risks visible before execution.

Update note:
[Contract Diagnostics](updates/2026-07-04-contract-diagnostics.md).

## 2026-07-03 Final Closure

Ran the final closure verification matrix and recorded the handoff report.

Final closure evidence:

- `bash scripts/verify.sh`: 148 tests OK.
- `schema-check --registry catalog`: OK, 172 manifests.
- `router-eval`: 39 / 39 cases OK, no issues in `quality_summary.by_issue`.
- latest router-eval quality classification: 36 high-confidence cases passed,
  3 low-confidence cases passed, 0 low-confidence failures, and no
  `by_issue_class` entries in the real catalog eval.
- `maintain-check`: OK with 23 trusted bundles, 19 references, and 336 / 336
  claude-skills candidates covered.
- `verify --registry catalog`: 172 skills, 166 trusted, 0 tampered, 0 unknown
  provenance.
- `git diff --check`: OK.

Update note:
[Final Closure Report](final-closure-report.md).

GitHub-facing update summary:
[GitHub Update Summary](github-update-summary-2026-07-03.md).

## 2026-07-03 Router Eval Quality Classification

Extended `router-eval` quality reporting with explicit issue classification
and low-confidence route trend fields.

Case-level issues now include a deterministic `classification` field. The
quality summary now includes:

- `by_issue_class`
- `by_confidence`
- `low_confidence_case_count`
- `low_confidence_passed_count`
- `low_confidence_failed_count`

This closes the follow-up item for false-positive / false-negative
classification and low-confidence trend tracking while keeping router
selection behavior unchanged.

Real catalog baseline after the update:

```text
router-eval: 39 / 39 cases OK
by_confidence.high: 36 passed, 0 failed
by_confidence.low: 3 passed, 0 failed
low_confidence_case_count: 3
low_confidence_failed_count: 0
by_issue_class: {}
```

Update note:
[Router Eval Quality Classification](updates/2026-07-03-router-eval-quality-classification.md).

## 2026-07-03 Source Import Capture Gate

Closed the source-import metadata delivery gap with a schema gate.

Records that declare `source.usage = source_import` now require
`source.capture` metadata with upstream URL, ref type, ref value, capture time,
license snapshot, upstream content hash, content path, and capture method.
Malformed capture metadata produces structured schema issues:
`schema-missing-source-import-capture` or
`schema-invalid-source-import-capture`.

This does not add a networked import command. It prevents unaudited
`source_import` records from passing schema validation while keeping real Git
or archive import automation as future non-blocking work.

Update notes:

- [Source Import Capture Gate](updates/2026-07-03-source-import-capture-gate.md)
- [Delivery Readiness Report](delivery-readiness-report.md)

## 2026-07-03 Router Quality Summary

Added deterministic aggregate metrics to `router-eval` output.

`router-eval` now returns `quality_summary` with pass/fail counts grouped by:

- expected scenario;
- actual scenario;
- expected task type;
- structured issue id.

This closed the compact quality-summary slice from the project-wide review
follow-up. False-positive / false-negative classification and low-confidence
trend tracking were completed later in
[Router Eval Quality Classification](updates/2026-07-03-router-eval-quality-classification.md).

Boundary: this is reporting-only. It does not change router selection
behavior, trusted skill state, runtime permissions, external imports, or
publication authority.

Update note:
[Router Quality Summary](updates/2026-07-03-router-quality-summary.md).

## 2026-07-03 Scanner Variable Path Hardening

Continued Phase 1 scanner engine hardening with downloaded-file path data-flow
coverage.

The scanner now detects path variables used as remote download output targets
and later executed by an interpreter or shell, reporting
`variable-path-download-execution`.

Added regression coverage for:

- `PAYLOAD=/tmp/payload.sh`, `curl ... -o "$PAYLOAD"`, `bash "$PAYLOAD"`;
- `SECOND=/tmp/setup.py`, `wget ... --output-document=${SECOND}`,
  `python3 ${SECOND}`.

Boundary: the scanner remains deterministic preflight analysis. It does not
execute shell content, fetch URLs, resolve filesystem paths, or perform runtime
variable expansion beyond simple static variable-name matching.

Update note:
[Scanner Variable Path Hardening](updates/2026-07-03-scanner-variable-path-hardening.md).

## 2026-07-03 Scanner Substitution Download Hardening

Continued Phase 1 scanner engine hardening with substitution-focused bypass
coverage.

The scanner now detects remote downloads passed into interpreters through:

- process substitution such as `bash <(curl -fsSL ...)`;
- here-string command substitution such as `sh <<< "$(wget -qO- ...)"`.

Both patterns report `substitution-download-execution`.

Boundary: the scanner remains deterministic preflight analysis. It does not
execute shell content, evaluate substitutions, fetch URLs, or grant runtime
permissions.

Update note:
[Scanner Substitution Download Hardening](updates/2026-07-03-scanner-substitution-download-hardening.md).

## 2026-07-03 Scanner Variable Download Hardening

Started Phase 1 scanner engine hardening with a small bypass-focused slice.

The scanner now detects variables that store a `curl` or `wget` command and
are later expanded into `sh` or `bash`, reporting
`indirect-download-execution`.

Added regression coverage for:

- `INSTALLER='curl ...'` followed by `$INSTALLER | bash`;
- `FETCH="wget ... -O /tmp/setup.sh"` followed by `${FETCH} && sh ...`.

Boundary: the scanner remains deterministic preflight analysis. It does not
execute shell content, fetch URLs, or grant runtime permissions.

Update note:
[Scanner Variable Download Hardening](updates/2026-07-03-scanner-variable-download-hardening.md).

## 2026-07-03 Project-Wide Review Follow-Up

Reviewed the full project against earlier audit, closure, roadmap, and
release-follow-up reports.

Current verification remains clean:

- `bash scripts/verify.sh`: 144 tests OK.
- `router-eval`: 39 / 39 cases OK.
- `maintain-check`: OK with 23 trusted bundles, 19 references, and 336 / 336
  claude-skills mappings.
- `verify --registry catalog`: 172 skills, 166 trusted, 0 tampered, 0 unknown
  provenance.

Remaining next-phase optimization tracks:

- scanner engine hardening with tokenized command extraction and bypass
  fixtures;
- networked source-import automation after the schema capture gate;
- deeper scheduler metadata such as explicit `requires_after` ordering;
- semantic gateway and context-record host integration, kept separate from
  trusted skill content;
- documentation consolidation so current baselines are not confused with dated
  closure-report baselines.

Update note:
[Project-Wide Review Follow-Up](updates/2026-07-03-project-wide-review-follow-up.md).

## 2026-07-03 Router Eval Constraint Schema

Hardened `router-eval` so malformed control, expectation, and constraint
fields fail as structured evaluation issues before task-pack generation.

Eval cases now validate:

- `router` as a string before router-mode comparison.
- `strategy` as one of `fast`, `balanced`, or `deep`.
- `invariants` as a string or array of strings when present.
- `expected_scenario` and `expected_task_type` as strings when present.
- `expected_skills`, `forbidden_skills`, `forbidden_skill_prefixes`, and
  `forbidden_skill_subcategories` as arrays of strings.
- `max_skill_count` as a non-negative integer.

Invalid fields now produce `router-eval-invalid-case-field` instead of being
silently ignored or causing runtime type errors during comparison.
Malformed scenario and task-type expectations are now rejected before normal
mismatch checks run.
Malformed router control fields are now rejected before router-mode comparison.

Update note:
[Router Eval Constraint Schema](updates/2026-07-03-router-eval-constraint-schema.md).

## 2026-07-03 Router Eval Taxonomy Constraints

Extended `router-eval` negative constraints with taxonomy-aware forbidden
subcategory checks.

Eval cases now support:

- `forbidden_skill_subcategories`: selected skills whose taxonomy subcategory
  should fail the eval case.

Upgraded vague `general` fallback eval cases to forbid browser-related
execution subcategories: `execution.browser`, `execution.browser_agent`, and
`execution.browser_test`. Exact skill and prefix constraints remain available
for targeted and family-level guards.

Update note:
[Router Eval Taxonomy Constraints](updates/2026-07-03-router-eval-taxonomy-constraints.md).

## 2026-07-03 Router Eval Prefix Constraints

Extended `router-eval` negative constraints with prefix-based forbidden skill
checks.

Eval cases now support:

- `forbidden_skill_prefixes`: skill-name prefixes that should fail the eval
  case when any selected skill starts with one of them.

Upgraded vague `general` fallback eval cases from enumerating specific browser
skill names to forbidding the broader `execution-browser*` and
`execution-playwright*` families. Exact `forbidden_skills` remains available
for targeted exclusions such as `execution-publish-check`.

Update note:
[Router Eval Prefix Constraints](updates/2026-07-03-router-eval-prefix-constraints.md).

## 2026-07-03 Router Eval Negative Constraints

Deepened `router-eval` so long-term quality cases can assert negative
constraints as well as expected selections.

Eval cases now support:

- `forbidden_skills`: selected skills that should fail the eval case.
- `max_skill_count`: an upper bound for selected-skill count.

Upgraded vague `general` fallback eval cases so browser automation,
Playwright automation, and publish checks cannot silently return to
low-confidence packs.

Update note:
[Router Eval Negative Constraints](updates/2026-07-03-router-eval-negative-constraints.md).

## 2026-07-03 Lightweight General Fallback

Reduced low-confidence `general` task packs so vague continuation requests do
not default to browser automation, web-task, sandbox, or publish-check
guidance.

The regression case:

```text
可以，按照步骤，继续优化
```

now remains `general` and selects only the lightweight local fallback:
`execution-file-batch` and `execution-rollback-checkpoint-plan`.

Added scenario-router and smart-router CLI coverage plus router-eval case:
`unsupported-vague-stepwise-continue-optimization-lightweight`.

Update note:
[Lightweight General Fallback](updates/2026-07-03-lightweight-general-fallback.md).

## 2026-07-03 Vague Continue Optimization Guard

Tightened the update-record follow-up routing fix so vague continuation
requests do not overmatch `skill-router-quality-review`.

The negative regression case:

```text
继续优化任务
```

now remains a low-confidence `general` task. The more specific update-record
follow-up remains routed to `skill-router-quality-review`:

```text
写好更新记录后，继续优化任务
```

Added focused unit coverage, real-world catalog regression coverage, and a
router-eval guard case: `unsupported-vague-continue-optimization`.

Update note:
[Vague Continue Optimization Guard](updates/2026-07-03-vague-continue-optimization-guard.md).

## 2026-07-03 Update Record Follow-Up Routing

Fixed a continuation-task routing gap where:

```text
写好更新记录后，继续优化任务
```

fell back to the low-confidence `general` task pack instead of selecting
`skill-router-quality-review`.

Added narrow update-record continuation signals, focused unit coverage,
real-world catalog regression coverage, and a reusable router-eval case:
`skill-router-update-record-followup`.

Update note:
[Update Record Follow-Up Routing](updates/2026-07-03-update-record-followup-routing.md).

## 2026-07-03 Skill Router Execution Order

Improved `skill-router-quality-review` orchestration so selected skills,
pipeline stages, and the flat execution plan follow the same stage-aware
sequence:

```text
preflight -> planning -> review -> verification -> handoff
```

Moved `security-supply-chain-review` into the Review stage so provenance,
permission, and dependency risks are checked before regression and CI
verification. Kept `ai-rule-failure-log-synthesis` in Handoff so failure-rule
updates are synthesized after verification evidence exists.

Also reordered smart-router `skills` output with the same scenario stage map,
so the visible selected-skill list no longer starts with a later-stage review
skill.

Update note:
[Skill Router Execution Order](updates/2026-07-03-skill-router-execution-order.md).

## 2026-07-03 Typo Skill Orchestration Routing

Fixed a real conversation routing gap where:

```text
继续，优化和编排sikll，继续补充和优化，做好记录和测试
```

was routed to `code-review-hardening` because typo normalization did not let the
skill-router signals win over the generic Chinese `测试` code-review signal.

Adjusted alias normalization so `sikll` becomes `skill` without duplicating the
replacement target during signal normalization. Added focused unit,
real-world regression, and router-eval coverage for the same task.

Update note:
[Typo Skill Orchestration Routing](updates/2026-07-03-typo-skill-orchestration-routing.md).

## 2026-07-03 Project Release Follow-Up Routing

Added a regression fix for mixed Chinese/English project follow-up requests
such as writing changelogs, GitHub update notes, verification notes, and
publication handoff. These tasks now route to `skill-router-quality-review`
instead of being pulled into `website-build-launch` by broad publish signals.

Updated the `skill-router-quality-review` bundle so release-follow-up routing
can include the optional `publish_check` capability and
`execution-publish-check` verifier guidance when the task mentions changelogs,
GitHub update notes, publication, or project closure.

Added focused unit, real-world regression, and router-eval coverage for:

```text
继续项目复查收尾，写好更新日志和 GitHub 更新说明，验证后发布
```

Update note:
[Project Release Follow-Up Routing](updates/2026-07-03-project-release-follow-up-routing.md).

## 2026-07-03 Project Check Follow-Up

Full project check found that sanitizer line-level removal could strip
protective sensitive-data guidance from catalog skills when the line mentioned
credentials, private files, or broad workspace access in a defensive context.

Fixed the scanner to preserve protective boundary wording that starts with
verbs such as remove, check, review, avoid, or do not, while still removing
dangerous instructions such as searching the whole machine for credentials.

Regenerated affected catalog entries:

- `ai-rule-failure-log-synthesis`
- `execution-mcp-tool-connector-review`

Added regression coverage for protective sensitive-data guidance and contiguous
`Safe Workflow` numbering across catalog skills.

## 2026-07-03 Reference Pattern Expansion

Added five trusted, locally authored method skills based on external reference
project review:

- `research-multi-platform-search-boundary`
- `business-value-investment-research-framework`
- `ai-agent-role-library-governance`
- `design-design-md-system-contract`
- `compliance-private-communication-boundary`

Added five trusted scenario bundles:

- `multi-platform-research-discovery`
- `investment-research-diligence`
- `agent-role-library-governance`
- `design-md-system-governance`
- `private-communication-governance`

Recorded metadata-only external references for Agent-Reach, ai-berkshire,
agency-agents, Google DESIGN.md ecosystem references, and SimpleX Chat.
OpenMontage and codebase-memory-mcp were reviewed again and remain covered by
batch 031 skills. No upstream code, prompts, installers, connectors, accounts,
scrapers, investment agents, role packs, design skills, messaging servers, or
cryptographic implementations were imported or enabled.

Updated router profiles and eval coverage so multi-platform research,
investment diligence, role-library governance, DESIGN.md governance, and
private communication tasks route to dedicated trusted bundles instead of
generic RAG, website, multi-agent, or general scenarios.

## 2026-07-03 Agentic Reference Patterns

Added three trusted, locally authored method skills based on external reference
project review:

- `media-agentic-video-pipeline-plan`
- `ai-graph-memory-contract`
- `code-codebase-graph-index-boundary`

Added three trusted scenario bundles:

- `agentic-media-production`
- `agent-long-term-memory-governance`
- `codebase-graph-intelligence`

Recorded metadata-only external references for OpenMontage, cognee, and
codebase-memory-mcp. The references remain non-runtime provenance records; no
upstream code, prompts, installers, renderers, memory services, MCP servers, or
background indexers were imported or enabled.

Updated router profiles and regression coverage so reference-video media
production, long-term graph memory governance, and MCP code graph intelligence
route to dedicated trusted bundles instead of older generic video, RAG, or code
review scenarios.

Historical verified baseline after this update:

```text
branch: main
catalog skills: 172
trusted skills: 166
trusted scenario bundles: 23
external references: 19
trusted overlap groups: 7
tracked claude-skills candidates: 336
covered claude-skills candidates: 336
router eval cases: 39
verification command: bash scripts/verify.sh
```

## Maintenance Gates

Run these gates before publishing catalog, router, bundle, or documentation
changes:

```bash
bash scripts/verify.sh
env PYTHONPATH=src python3 -m onecode_skill_sanitizer.cli verify --registry catalog
env PYTHONPATH=src python3 -m onecode_skill_sanitizer.cli maintain-check --registry catalog --bundles bundles/index.json --references external-references/index.json --claude-skills-candidate-map docs/claude-skills-candidate-map.json
env PYTHONPATH=src python3 -m onecode_skill_sanitizer router-eval --eval evals/router-quality.json --registry catalog --bundles bundles/index.json
git diff --check
```

Expected current results:

```text
verify: ok, 172 skills, 166 trusted, 0 tampered, 0 unknown provenance
maintain-check: ok, 23 bundles, 336 / 336 candidates covered
router-eval: ok, 41 / 41 cases
full script: 157 tests OK
```

## Routine Maintenance Checklist

- Keep `README.md`, `catalog/README.md`, `docs/catalog-status.md`, and
  `docs/feature-log.md` in sync with `catalog/index.json` and
  `bundles/index.json`.
- Add or update router eval cases when a new scenario profile, bundle, or major
  signal family is added.
- Keep default task packs trusted-only. Use review-required or quarantined
  skills only for explicit review work.
- Do not copy or execute upstream community skills directly. Convert useful
  patterns through local authoring, scan, schema check, approval, manifest
  sealing, and registry verification.
- Update `docs/claude-skills-candidate-map.json` only when a candidate maps to
  an existing trusted local skill or is intentionally queued for future work.
- Reinstall `safe-agent-router` only when integration skill files or wrapper
  scripts change, or when the local repository path changes.

## Next Maintenance Backlog

- Watch upstream reference sources for new or changed skill candidates.
- Promote cluster-covered candidates into dedicated local skills only when
  repeated real tasks show that a cluster is too broad.
- Continue expanding multilingual routing signals for common Chinese, English,
  and mixed-language task phrasing.
- Add deeper parser-backed checks where deterministic regex scanning is too
  shallow for a recurring risk class.
