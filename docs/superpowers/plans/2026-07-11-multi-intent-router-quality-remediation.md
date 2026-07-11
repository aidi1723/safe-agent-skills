# Multi-Intent Router Quality Remediation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make default Schema v2 routing preserve bounded compound intents, compile explicit dependencies, emit strict measurable quality evidence, and pass the approved production gate without changing Schema v1.

**Architecture:** Keep language decomposition in the intent boundary, scenario selection in the composer, and graph construction in the compiler. Add focused span, dependency, quality-gate, and review-evidence modules so the existing owner modules do not grow into new god modules; keep the existing 100-case corpus as development evidence and use a separately reviewed sharded production suite for final gates.

**Tech Stack:** Python 3.11+, dataclasses, regular expressions, JSON Schema Draft 2020-12, `unittest`, deterministic JSON hashing, Ruff, Git, GitHub Actions.

---

Worktree: `.worktrees/multi-intent-router-quality-remediation`

Baseline: `d73239e`, 355 tests passing.

## Fixed Contracts

- Schema v2 default behavior changes; Schema v1 shape and compatibility hash do not.
- The real compound request must resolve to the existing scenario-level intents
  `website_build`, `code_review`, `document_knowledge_base`, `data_analysis`,
  `content_seo`, and `open_source_release`. Browser, CI, PDF, DOCX, and UI
  specialists are verified through those scenario capability and Skill lists;
  they are not invented as new task types.
- Candidate signal matches are capped at 128 and emitted intents at 12.
- Comma and enumeration lists are parallel unless explicit sequencing is
  present. Strong semicolon-separated workflow steps are sequential unless the
  text explicitly marks them parallel.
- Missing, malformed, non-finite, unsigned, or failed quality evidence keeps
  `production_ready` false.
- No accepted reviewer record may be authored or fabricated by the routing-rule
  author.

## Task 1: Add The Detailed Decomposition Contract

**Files:**

- Create: `src/onecode_skill_sanitizer/intent_spans.py`
- Create: `tests/test_intent_spans.py`
- Modify: `src/onecode_skill_sanitizer/intent.py`
- Modify: `tests/test_intent.py`

- [ ] **Step 1: Write the failing diagnostics contract tests**

Add tests that import `decompose_task_detailed` and assert the public result
contract before implementing it:

```python
def test_detailed_decomposition_wraps_existing_strong_clause_behavior(self):
    result = decompose_task_detailed("构建官网，同时审计 skill router")

    self.assertEqual(
        [intent.task_type for intent in result.intent_graph.intents],
        ["website_build", "skill_router_review"],
    )
    self.assertEqual(result.diagnostics.mode, "strong_clauses")
    self.assertFalse(result.diagnostics.candidate_signal_limit_exceeded)
    self.assertFalse(result.diagnostics.intent_limit_exceeded)


def test_diagnostics_json_uses_arrays_and_bounded_counts(self):
    result = decompose_task_detailed("审计 skill router")

    self.assertEqual(result.diagnostics.emitted_intent_count, 1)
    self.assertEqual(result.diagnostics.reason_codes, ())
    self.assertIsInstance(result.diagnostics.to_json()["reason_codes"], list)
```

Add a compatibility assertion to `tests/test_intent.py`:

```python
def test_decompose_task_remains_graph_only_compatibility_wrapper(self):
    graph = decompose_task("审计 skill router")

    self.assertIsInstance(graph, IntentGraph)
    self.assertNotIsInstance(graph, TaskDecomposition)
```

- [ ] **Step 2: Run the focused tests and verify RED**

Run:

```bash
PYTHONPATH=src python3 -m unittest tests.test_intent_spans tests.test_intent -v
```

Expected: import failure for `decompose_task_detailed`,
`TaskDecomposition`, or `DecompositionDiagnostics`.

- [ ] **Step 3: Add frozen result and diagnostics models**

In `intent.py`, add frozen models and keep `decompose_task()` as the stable
wrapper:

```python
@dataclass(frozen=True)
class DecompositionDiagnostics:
    mode: str
    observed_candidate_count: int
    emitted_intent_count: int
    candidate_signal_limit_exceeded: bool
    intent_limit_exceeded: bool
    reason_codes: tuple[str, ...]

    @property
    def status(self) -> str:
        return "incomplete" if self.reason_codes else "complete"

    def to_json(self) -> dict[str, Any]:
        return _json_compatible(asdict(self))


@dataclass(frozen=True)
class TaskDecomposition:
    intent_graph: IntentGraph
    diagnostics: DecompositionDiagnostics


def decompose_task(task: str) -> IntentGraph:
    return decompose_task_detailed(task).intent_graph
```

Create `intent_spans.py` with immutable internal records and hard limits:

```python
MAX_CANDIDATE_SIGNALS = 128
MAX_EMITTED_INTENTS = 12


@dataclass(frozen=True)
class ProfileSignalSpan:
    start: int
    end: int
    task_type: str
    signal: str
    score: int


@dataclass(frozen=True)
class SpanDecomposition:
    clauses: tuple[str, ...]
    observed_candidate_count: int
    candidate_signal_limit_exceeded: bool
    intent_limit_exceeded: bool
```

Initially return the existing strong clauses through this contract. Use
`single_clause` for one clause and `strong_clauses` for multiple clauses. Do not
add new splitting behavior in this step.

- [ ] **Step 4: Run the model and legacy intent tests**

Run:

```bash
PYTHONPATH=src python3 -m unittest tests.test_intent_spans tests.test_intent tests.test_compatibility -v
```

Expected: model, wrapper, and compatibility tests pass.

- [ ] **Step 5: Commit the green contract and wrapper**

```bash
git add src/onecode_skill_sanitizer/intent.py \
  src/onecode_skill_sanitizer/intent_spans.py \
  tests/test_intent.py tests/test_intent_spans.py
git commit -m "refactor: define detailed intent decomposition contract"
```

## Task 2: Implement Profile-Aware Span Decomposition

**Files:**

- Modify: `src/onecode_skill_sanitizer/intent_spans.py`
- Modify: `src/onecode_skill_sanitizer/intent.py`
- Modify: `src/onecode_skill_sanitizer/routing_profiles.py`
- Modify: `tests/test_intent_spans.py`
- Modify: `tests/test_intent.py`

- [ ] **Step 1: Add the full red matrix**

Add table-driven cases for source order, same-profile merging, distinctive
score, unique winner, connectors, negation, and bounds:

```python
GOOD_CASES = [
    (
        "UI design, code review, PDF documents, spreadsheet analysis, SEO article",
        ["website_build", "code_review", "document_knowledge_base", "data_analysis", "content_seo"],
    ),
    (
        "UI 设计、代码审查、PDF/DOCX 文档、表格分析和 SEO 文章",
        ["website_build", "code_review", "document_knowledge_base", "data_analysis", "content_seo"],
    ),
    (
        "design system and component states, then review the pull request",
        ["design_md_system_governance", "code_review"],
    ),
]

NEGATIVE_CASES = [
    "Supported files: PDF, DOCX, XLSX, and CSV",
    "The report contains website, SEO, code, and release terminology",
    "Do not build a website, review code, or publish anything",
    "Compare GitHub, YouTube, Reddit, and Bilibili source names",
]
```

Add the motivating request as its own test and assert these task types in
order:

```python
[
    "website_build",
    "code_review",
    "document_knowledge_base",
    "data_analysis",
    "content_seo",
    "open_source_release",
]
```

Add limit cases that construct 129 distinctive signal occurrences and 13
valid intent segments. Assert explicit reason codes and no successful silent
truncation.

- [ ] **Step 2: Run focused tests and verify RED**

Run:

```bash
PYTHONPATH=src python3 -m unittest tests.test_intent_spans -v
```

Expected: the positive matrices remain one intent and limit diagnostics are
missing.

- [ ] **Step 3: Expose bounded signal iteration from routing profiles**

Add a public helper in `routing_profiles.py` so `intent_spans.py` does not
depend on `_signal_score` internals:

```python
def iter_profile_signal_matches(text: str) -> list[dict[str, object]]:
    lowered = text.lower()
    matches = []
    for profile in SCENARIO_PROFILES:
        signals = tuple(profile["signals"]) + PROFILE_SIGNAL_ALIASES.get(profile["task_type"], ())
        for signal in signals:
            normalized_signal = signal.lower()
            if normalized_signal in AMBIGUOUS_PROFILE_SIGNALS:
                continue
            for match in re.finditer(re.escape(normalized_signal), lowered):
                matches.append(
                    {
                        "start": match.start(),
                        "end": match.end(),
                        "task_type": profile["task_type"],
                        "signal": normalized_signal,
                        "score": 4 if " " in normalized_signal else 2,
                    }
                )
    return sorted(matches, key=lambda item: (item["start"], -item["score"], item["task_type"]))
```

Use lowercased source text without whitespace collapsing so match offsets still
refer to the original clause. Preserve the existing short-token boundary
behavior by using `signal_matches_text` semantics rather than accepting
substring matches for short ASCII signals. Add distinctive aliases only where the scenario contract
already covers the capability:

```python
PROFILE_SIGNAL_ALIASES = {
    "website_build": ("ui design", "UI 设计", "browser verification", "浏览器验证"),
    "code_review": ("ci troubleshooting", "CI 排障"),
    "document_knowledge_base": ("docx", "DOCX", "PDF/DOCX"),
}
```

- [ ] **Step 4: Implement span grouping and guarded splitting**

Implement the pure helpers
`find_profile_signal_spans(clause: str)`,
`merge_same_profile_spans(spans)`, and
`split_profile_enumeration(clause: str)` in `intent_spans.py`. Their return
types are respectively the ordered span tuple plus bounded count and flag, the
merged span tuple, and `SpanDecomposition`.

Required behavior:

- stop after observing the 129th candidate and set the candidate-limit flag;
- drop generic-only and negated spans;
- resolve overlaps by highest score, longest signal, then configured profile
  order;
- keep ties ambiguous instead of choosing lexically;
- split only when two task types survive;
- merge adjacent signals with the same task type;
- coalesce repeated task types within one enumeration into the first
  source-ordered intent and retain the later local phrases in its summary, so
  UI/browser and code-review/CI capability phrases do not emit duplicate
  scenario intents;
- retain the connector-local readable phrase;
- keep at most 12 source-ordered clauses and set `intent_limit_exceeded`.

Extend explicit release action detection, with existing negation protection,
for `推送 GitHub`, `push to GitHub`, and `push the repository` so those phrases
resolve to `open_source_release` rather than the research profile that also
contains `github`.

Update `decompose_task_detailed()` to use strong splitting first and span
splitting only inside broad clauses.

- [ ] **Step 5: Run focused and router compatibility tests**

Run:

```bash
PYTHONPATH=src python3 -m unittest \
  tests.test_intent_spans tests.test_intent tests.test_candidates \
  tests.test_composer tests.test_compatibility -v
```

Expected: all pass, including the real request and negative list cases.

- [ ] **Step 6: Commit the span implementation**

```bash
git add src/onecode_skill_sanitizer/intent_spans.py \
  src/onecode_skill_sanitizer/intent.py \
  src/onecode_skill_sanitizer/routing_profiles.py \
  tests/test_intent_spans.py tests/test_intent.py
git commit -m "feat: decompose bounded multi-intent enumerations"
```

## Task 3: Infer Explicit Intent Dependencies

**Files:**

- Create: `src/onecode_skill_sanitizer/intent_dependencies.py`
- Create: `tests/test_intent_dependencies.py`
- Modify: `src/onecode_skill_sanitizer/intent.py`
- Modify: `tests/test_intent.py`

- [ ] **Step 1: Write dependency and parallelism failures**

Add exact edge expectations:

```python
SEQUENTIAL_CASES = [
    ("first analyze the spreadsheet, then write the SEO article", [("i1", "i2")]),
    ("先做短视频脚本，再接入 agentic media workflow", [("i1", "i2")]),
    ("Review the PR; build the website; prepare an open-source release", [("i1", "i2"), ("i2", "i3")]),
    ("Govern the role library before planning the multi-agent workflow", [("i1", "i2")]),
]

PARALLEL_CASES = [
    "In parallel: review code, analyze the spreadsheet, and draft an SEO article",
    "同时做 UI 设计、代码审查和表格分析",
]
```

For release gates, assert that the release intent depends on all explicitly
preceding verification paths, preserving current behavior.

- [ ] **Step 2: Run tests and verify RED**

Run:

```bash
PYTHONPATH=src python3 -m unittest tests.test_intent_dependencies tests.test_intent -v
```

Expected: non-release sequential dependencies are absent.

- [ ] **Step 3: Implement dependency relations as a pure transformation**

Create the frozen `IntentRelation` record and the pure functions
`infer_intent_relations(current_text, intents)` and
`apply_intent_relations(intents, relations)`:

```python
@dataclass(frozen=True)
class IntentRelation:
    source_id: str
    target_id: str
    reason: str
```

Use explicit markers for `first/then`, `先/再`, `before`, completion and
verification gates, and release actions. Treat semicolon-separated workflow
steps as ordered unless the task contains `parallel`, `in parallel`, `同时`, or
`并行`. Deduplicate relations, reject self-edges, and preserve source order.
Avoid an `intent.py` import cycle: use `TYPE_CHECKING` for the `Intent` type and
`dataclasses.replace()` to apply `depends_on` at runtime.

Update `decompose_task_detailed()` to infer and apply relations after all
intents are classified. Keep `IntentGraph.validate()` as the final cycle and
unknown-ID boundary.

- [ ] **Step 4: Verify dependency and compiler behavior**

Run:

```bash
PYTHONPATH=src python3 -m unittest \
  tests.test_intent_dependencies tests.test_intent tests.test_compiler \
  tests.test_composer -v
```

Expected: all pass; explicit sequences have edges and parallel enumerations do
not.

- [ ] **Step 5: Commit**

```bash
git add src/onecode_skill_sanitizer/intent_dependencies.py \
  src/onecode_skill_sanitizer/intent.py \
  tests/test_intent_dependencies.py tests/test_intent.py
git commit -m "feat: infer explicit multi-intent dependencies"
```

## Task 3A: Isolate Verification From Local Workspaces

**Files:**

- Modify: `.gitignore`
- Modify: `scripts/verify.sh`
- Modify: `tests/test_verify_script.py`

- [ ] Add failing tests proving private-path and placeholder scans inspect only
  Git-tracked files when `rg` is present or absent. Local `.venv/`, `venv/`,
  `.worktrees/`, caches, and unrelated untracked files must not affect release
  verification.
- [ ] Add `.venv/` and `venv/` to `.gitignore` while retaining the existing
  `.worktrees/` rule.
- [ ] Replace the recursive `rg`/`grep` fallback with one tracked-file search
  contract, using `git grep` or `git ls-files -z` plus a bounded grep fallback.
  Preserve the existing optional exclude-path behavior and match/no-match exit
  semantics.
- [ ] Run `tests.test_verify_script`, a sandbox fixture containing private paths
  under untracked `.venv` and `.worktrees`, and full `scripts/verify.sh`.
- [ ] Commit: `fix: isolate verification from local workspaces`.

## Task 3B: Disambiguate Router Evaluation Artifacts

**Files:**

- Rename: `evals/router-quality-v2.json` to
  `evals/router-regression-v2.json`
- Modify: `src/onecode_skill_sanitizer/router_eval_v2.py`
- Modify: `tests/test_router_eval_cli.py`
- Modify: `tests/test_router_eval_v2.py`
- Modify: `docs/router-development.md`

- [ ] Add a failing CLI test showing the legacy `router-eval` Schema v2 payload
  produces an actionable `router-eval-v2` error instead of the generic
  `{labeling, cases}` failure.
- [ ] Rename the regression artifact and update active tests/current guidance;
  do not rewrite dated historical plans that record the old milestone path.
- [ ] Detect the `schema_version/dataset/split/case_count/cases` signature in
  `load_eval_dataset_v2()` and report that the file belongs to `router-eval`,
  while `router-eval-v2` expects the multi-intent gold/suite contract.
- [ ] Verify both commands with their intended files and run the focused Router
  Eval suites.
- [ ] Commit: `fix: disambiguate router evaluation datasets`.

## Task 3C: Cover The Real Chinese Review Brief Release Request

**Files:**

- Modify: `src/onecode_skill_sanitizer/intent_spans.py`
- Modify: `src/onecode_skill_sanitizer/routing_profiles.py`
- Modify: `tests/test_intent_spans.py`
- Modify: `tests/test_task_pack_v2_cli.py`
- Modify: `evals/multi-intent-gold.json`

- [ ] Add a failing real-task regression for
  `代码审查 + 老板简报 + 发布清单`. It must select, in order,
  `code_review`, `data_analysis`, and `open_source_release`, with scenarios
  `code-review-hardening`, `data-analysis-report`, and `open-source-release`;
  it must never select `website-build-launch`.
- [ ] Treat `+` and full-width `＋` as enumeration connectors only when distinct
  profile evidence survives. Add `老板简报`, `管理层简报`, `executive brief`, and
  `management brief` as bounded aliases for the existing `data_analysis`
  report scenario, and `发布清单`/`release checklist` as bounded aliases for
  the existing release-readiness scenario. Do not add a new task type, bundle,
  or Skill.
- [ ] Add negative controls for descriptive mentions and arithmetic plus signs,
  plus Chinese spacing/full-width variants.
- [ ] Run span, task-pack, composer, compatibility, and Router Eval tests.
- [ ] Commit: `fix: route Chinese review brief release tasks`.

## Task 4: Wire Diagnostics Into Default Schema v2

**Files:**

- Modify: `src/onecode_skill_sanitizer/task_packs.py`
- Modify: `src/onecode_skill_sanitizer/compatibility.py`
- Modify: `tests/test_task_pack_v2_cli.py`
- Modify: `tests/test_compatibility.py`

- [ ] **Step 1: Add failing task-pack diagnostics tests**

Add a new CLI test for the motivating high-frequency request; keep the existing
three-intent website/router/release test unchanged:

```python
decomposition = payload["routing_metrics"]["decomposition"]
self.assertEqual(decomposition["mode"], "profile_spans")
self.assertEqual(decomposition["emitted_intent_count"], 6)
self.assertEqual(decomposition["reason_codes"], [])
self.assertEqual(payload["routing_status"], "complete")
```

Add an over-limit test asserting:

```python
self.assertEqual(payload["routing_status"], "incomplete")
self.assertIn("intent_limit_exceeded", payload["routing_metrics"]["decomposition"]["reason_codes"])
self.assertLessEqual(len(payload["intent_graph"]["intents"]), 12)
```

Assert the Schema v1 shape checksum and `compatibility_loss` fixture remain
unchanged.

- [ ] **Step 2: Run tests and verify RED**

Run:

```bash
PYTHONPATH=src python3 -m unittest tests.test_task_pack_v2_cli tests.test_compatibility -v
```

Expected: missing `routing_metrics.decomposition` and over-limit route marked
complete.

- [ ] **Step 3: Use detailed decomposition in `build_task_pack_v2()`**

Replace the direct graph call with:

```python
decomposition = decompose_task_detailed(task)
intent_graph = decomposition.intent_graph
```

Add the diagnostics JSON under `routing_metrics`, and change `_routing_status`
to accept `decomposition_status`. Precedence stays `blocked`, then
`incomplete`, then `complete`:

The exact signature is
`_routing_status(composition_status: str, capability_resolution: dict,
execution_graph: dict, decomposition_status: str = "complete") -> str`.

Bump only the v2 route identity version string to
`hybrid-router-v2-quality-remediation`. Do not change v1 conversion fields.

- [ ] **Step 4: Run focused integration and shape tests**

Run:

```bash
PYTHONPATH=src python3 -m unittest \
  tests.test_task_pack_v2_cli tests.test_compatibility \
  tests.test_router_cli -v
```

Expected: all pass and the v1 shape hash remains unchanged.

- [ ] **Step 5: Commit**

```bash
git add src/onecode_skill_sanitizer/task_packs.py \
  src/onecode_skill_sanitizer/compatibility.py \
  tests/test_task_pack_v2_cli.py tests/test_compatibility.py
git commit -m "feat: expose v2 decomposition diagnostics"
```

## Task 5: Correct DAG Coherence And Dependency Evaluation

**Files:**

- Modify: `src/onecode_skill_sanitizer/router_eval_v2.py`
- Modify: `tests/test_router_eval_v2.py`
- Modify: `evals/multi-intent-gold.json`

- [ ] **Step 1: Freeze the eleven current DAG coherence failures**

Add evaluator fixtures for these coherent states:

```python
VALID_STATUS_GRAPH_PAIRS = [
    ("complete", "ready", True),
    ("incomplete", "blocked", True),
    ("blocked", "blocked", True),
]
```

The incomplete case must contain `incomplete_composition` or
`missing_required_capability`; a blocked graph without an allowed reason stays
invalid. Add a real-corpus assertion that the existing 100-case development
set reports `dag_validity == 1.0` after the fix.

- [ ] **Step 2: Run the evaluator tests and verify RED**

Run:

```bash
PYTHONPATH=src python3 -m unittest tests.test_router_eval_v2 -v
```

Expected: incomplete/blocked coherence cases fail and baseline DAG validity is
`0.89`.

- [ ] **Step 3: Refine `_dag_assessment()` without weakening fail-closed behavior**

Treat an incomplete route with a blocked, acyclic, empty graph as coherent only
when the compiler reason identifies an incomplete composition or missing
required capability. Keep malformed graphs, unexpected cycles, mismatched
flags, and complete routes with blocked graphs invalid.

Update dependency-pair extraction to count both
`intent_verification_dependency` and `intent_completion_dependency` as one
logical intent edge. It must not double-count the same source/target intent
pair.

- [ ] **Step 4: Run the existing 100-case corpus**

Run:

```bash
PYTHONPATH=src python3 -m onecode_skill_sanitizer router-eval-v2 \
  --eval evals/multi-intent-gold.json \
  --registry catalog \
  --bundles bundles/index.json > /tmp/router-quality-development.json
jq '.metrics | {dag_validity, dependency_edge_recall}' /tmp/router-quality-development.json
```

Expected: `dag_validity` is `1.0`; dependency-edge recall is at least `0.90`
after Task 3. Do not relabel corpus cases to force either result.

- [ ] **Step 5: Commit evaluator corrections**

Only commit `evals/multi-intent-gold.json` if contract fields were added without
changing existing labels.

```bash
git add src/onecode_skill_sanitizer/router_eval_v2.py \
  tests/test_router_eval_v2.py evals/multi-intent-gold.json
git commit -m "fix: evaluate coherent v2 dependency graphs"
```

## Task 6: Add Missing Quality Metrics

**Files:**

- Create: `src/onecode_skill_sanitizer/router_quality_metrics.py`
- Create: `tests/test_router_quality_metrics.py`
- Modify: `src/onecode_skill_sanitizer/router_eval_v2.py`
- Modify: `src/onecode_skill_sanitizer/commands.py`
- Modify: `tests/test_router_eval_v2.py`

- [ ] **Step 1: Write hand-calculated metric failures**

Use a three-case task-type fixture with expected labels
`[["a"], ["a"], ["b"]]` and actual labels
`[["a"], ["b"], ["b"]]`. Assert the hand-calculated values:

```python
self.assertEqual(metrics["task_type_macro_precision"], 0.75)
self.assertEqual(metrics["task_type_macro_recall"], 0.75)
self.assertAlmostEqual(metrics["task_type_macro_f1"], 2 / 3)
self.assertEqual(metrics["required_capability_recall"], 0.75)
self.assertEqual(metrics["dependency_edge_precision"], 0.5)
self.assertEqual(metrics["forbidden_skill_false_positive_rate"], 0.25)
self.assertEqual(metrics["high_confidence_error_rate"], 0.5)
```

Use separate four-capability, two-edge, four-forbidden-label, and two
high-confidence-case fixtures for the remaining ratios so every numerator and
denominator is explicit. Add zero-denominator and non-finite rejection cases.

- [ ] **Step 2: Run and verify RED**

Run:

```bash
PYTHONPATH=src python3 -m unittest tests.test_router_quality_metrics -v
```

Expected: module import failure.

- [ ] **Step 3: Implement pure metric accumulators**

Create `ClassificationCounts` and implement
`macro_classification_metrics(expected, actual)` plus
`finite_ratio(numerator: int, denominator: int, *, empty: float)`:

```python
@dataclass(frozen=True)
class ClassificationCounts:
    true_positive: int = 0
    false_positive: int = 0
    false_negative: int = 0
```

Definitions:

- task-type Macro F1 is the arithmetic mean of per-task-type F1 over the union
  of expected and actual task types;
- required capability expectations are derived from required capabilities of
  expected scenario bundles, while actual hits require `status == covered` in
  `capability_resolution`;
- dependency precision and recall use deduplicated logical intent-type pairs;
- high-confidence means intent confidence at least `0.80`; an error is an
  unexpected or missing intent on a case containing such an emitted intent;
- forbidden Skill rate uses explicit `forbidden_skills` labels and actual
  `selected_skills[].name` values.

Extend `_validate_case()` with optional `forbidden_skills`, defaulting to an
empty list for the existing corpus. Update `synthetic_route()` to emit intent
confidence, selected skills, and capability resolution.

- [ ] **Step 4: Pass bundle capability context from the CLI**

In `commands.py`, build a deterministic mapping from bundle ID to required
capability IDs and pass it to `evaluate_router_v2()`. Reuse
`contract_coverage()` for the documented core scenarios rather than duplicating
Contract v2 validation.

- [ ] **Step 5: Run metric and evaluator tests**

```bash
PYTHONPATH=src python3 -m unittest \
  tests.test_router_quality_metrics tests.test_router_eval_v2 \
  tests.test_contracts -v
```

Expected: all new metrics are finite and include supporting counts.

- [ ] **Step 6: Commit**

```bash
git add src/onecode_skill_sanitizer/router_quality_metrics.py \
  src/onecode_skill_sanitizer/router_eval_v2.py \
  src/onecode_skill_sanitizer/commands.py \
  tests/test_router_quality_metrics.py tests/test_router_eval_v2.py
git commit -m "feat: measure v2 routing production metrics"
```

## Task 7: Add The Machine-Readable Production Gate

**Files:**

- Create: `src/onecode_skill_sanitizer/router_quality_gate.py`
- Create: `tests/test_router_quality_gate.py`
- Modify: `src/onecode_skill_sanitizer/router_eval_v2.py`
- Modify: `src/onecode_skill_sanitizer/commands.py`
- Modify: `src/onecode_skill_sanitizer/cli.py`
- Modify: `tests/test_router_eval_v2.py`

- [ ] **Step 1: Write boundary tests for every gate**

Define the fixed thresholds in the test and cover pass, exact boundary, fail,
missing, boolean, NaN, and infinity:

```python
PRODUCTION_THRESHOLDS = {
    "task_type_macro_f1": ("minimum", 0.90),
    "scenario_f1": ("minimum", 0.88),
    "required_capability_recall": ("minimum", 0.97),
    "forbidden_scenario_false_positive_rate": ("maximum", 0.005),
    "forbidden_skill_false_positive_rate": ("maximum", 0.005),
    "multi_intent_exact_match": ("minimum", 0.80),
    "dag_validity": ("minimum", 1.0),
    "high_confidence_error_rate": ("maximum", 0.02),
    "core_bundle_contract_coverage": ("minimum", 0.80),
    "dependency_edge_recall": ("minimum", 0.90),
}
```

- [ ] **Step 2: Run and verify RED**

```bash
PYTHONPATH=src python3 -m unittest tests.test_router_quality_gate -v
```

Expected: module import failure.

- [ ] **Step 3: Implement the isolated gate**

Implement
`build_quality_gate(metrics, *, dataset_identity, review_identity)` with typed
dictionary inputs and a `dict[str, object]` result.

Return:

```python
{
    "production_ready": False,
    "metric_gates": {"task_type_macro_f1": {"status": "pass", "value": 0.91, "threshold": 0.90}},
    "failed_gates": [],
    "missing_gates": ["independent_label_review"],
    "dataset_identity": dataset_identity,
    "review_identity": {},
}
```

Never round values before comparison. Sort gate lists. Treat booleans as
invalid numbers.

- [ ] **Step 4: Expose CLI enforcement without breaking diagnostic runs**

Add `--require-production-ready` to `router-eval-v2`. A normal evaluation
returns exit 0 even when the quality gate is false so development baselines can
be measured. With the flag, return exit 2 unless `production_ready` is true.
JSON output is always printed.

- [ ] **Step 5: Run focused CLI and gate tests**

```bash
PYTHONPATH=src python3 -m unittest \
  tests.test_router_quality_gate tests.test_router_eval_v2 \
  tests.test_router_cli -v
```

- [ ] **Step 6: Commit**

```bash
git add src/onecode_skill_sanitizer/router_quality_gate.py \
  src/onecode_skill_sanitizer/router_eval_v2.py \
  src/onecode_skill_sanitizer/commands.py src/onecode_skill_sanitizer/cli.py \
  tests/test_router_quality_gate.py tests/test_router_eval_v2.py
git commit -m "feat: enforce router production quality gates"
```

## Task 8: Add Dataset Suite And Independent Review Contracts

**Files:**

- Create: `schemas/router-eval-suite.schema.json`
- Create: `schemas/router-eval-review.schema.json`
- Create: `src/onecode_skill_sanitizer/router_eval_review.py`
- Create: `tests/test_router_eval_review.py`
- Create: `evals/reviews/README.md`
- Modify: `src/onecode_skill_sanitizer/router_eval_v2.py`
- Modify: `src/onecode_skill_sanitizer/commands.py`
- Modify: `src/onecode_skill_sanitizer/cli.py`
- Modify: `scripts/verify.sh`

- [ ] **Step 1: Write review and suite validation failures**

Test missing files, hash mismatch, unknown shard path, duplicate case IDs across
shards, incorrect declared counts, reviewer/rule-author equality, false
independence attestation, rejected decision, expired dataset hash, and unknown
fields.

The accepted review shape is:

```json
{
  "schema_version": 1,
  "suite_id": "router-production-v1",
  "suite_sha256": "sha256:0000000000000000000000000000000000000000000000000000000000000000",
  "reviewed_commit": "0000000000000000000000000000000000000000",
  "rule_author_id": "routing-author",
  "reviewer_id": "independent-reviewer",
  "reviewer_role": "independent_dataset_review",
  "reviewed_at": "2026-07-11T00:00:00Z",
  "decision": "accepted",
  "independence_attestation": true,
  "reviewed_case_ids": ["normal-001"],
  "exceptions": []
}
```

- [ ] **Step 2: Run and verify RED**

```bash
PYTHONPATH=src python3 -m unittest tests.test_router_eval_review -v
```

- [ ] **Step 3: Implement canonical suite loading and hashing**

Create pure functions `load_eval_suite(index_path, known_scenarios)`,
`canonical_suite_sha256(index_path)`, and
`load_review_record(review_path, suite_identity)`. Return the validated cases
and suite identity from the first, a `sha256:` identity from the second, and a
validated review dictionary from the third.

The suite index lists safe relative shard paths, exact case counts, and SHA-256
hashes. Resolve every path below the index directory, reject traversal, sort by
declared shard order, and reject duplicate case IDs across shards.
Extend the suite-only category contract with `normal`, `multi_intent`,
`ambiguous`, `negative`, `multilingual_typo_paraphrase`, and
`safety_sensitive`; preserve the legacy single-file category contract.

- [ ] **Step 4: Add CLI review input**

Add `--suite` and `--review` to `router-eval-v2`, mutually exclusive with the
legacy single `--eval` only where both would provide cases. Keep `--eval`
required unless `--suite` is present. A suite without a review evaluates and
returns a false gate; `--require-production-ready` also requires an accepted
review.

- [ ] **Step 5: Register schemas in verification**

Add JSON syntax and schema self-checks for both new schemas to
`scripts/verify.sh`. Do not add an accepted review artifact in this task.

- [ ] **Step 6: Run focused and script tests**

```bash
PYTHONPATH=src python3 -m unittest \
  tests.test_router_eval_review tests.test_router_eval_v2 \
  tests.test_verify_script -v
```

- [ ] **Step 7: Commit**

```bash
git add schemas/router-eval-suite.schema.json \
  schemas/router-eval-review.schema.json \
  src/onecode_skill_sanitizer/router_eval_review.py \
  src/onecode_skill_sanitizer/router_eval_v2.py \
  src/onecode_skill_sanitizer/commands.py src/onecode_skill_sanitizer/cli.py \
  tests/test_router_eval_review.py evals/reviews/README.md scripts/verify.sh
git commit -m "feat: validate router evaluation review evidence"
```

## Task 9: Tighten Nested Task Pack v2 Schemas

**Files:**

- Create: `tests/test_task_pack_v2_schema.py`
- Create: `schemas/task-pack-v2-selected-skill.schema.json`
- Modify: `schemas/task-pack-v2.schema.json`
- Modify: `tests/registry_cli_helpers.py`
- Modify: `tests/test_task_pack_v2_cli.py`
- Modify: `scripts/verify.sh`

- [ ] **Step 1: Capture valid complete, incomplete, and blocked payloads**

Build all three states through public APIs in tests and validate them before
changing the schema. Add mutations for every currently broad nested object:

```python
INVALID_MUTATIONS = [
    ("scenario_candidates", lambda payload: payload["scenario_candidates"][0].update(extra=True)),
    ("selected_skills", lambda payload: payload["selected_skills"][0].update(extra=True)),
    ("capability_resolution", lambda payload: payload["capability_resolution"].update(extra=True)),
    ("execution_graph", lambda payload: payload["execution_graph"].update(extra=True)),
    ("routing_metrics", lambda payload: payload["routing_metrics"].update(extra=True)),
    ("registry_verification", lambda payload: payload["registry_verification"].update(extra=True)),
    ("compatibility", lambda payload: payload["compatibility"].update(extra=True)),
]
```

Assert invalid enum, malformed IDs, boolean-as-integer, missing keys, and
unknown fields are rejected.

- [ ] **Step 2: Run and verify RED**

```bash
PYTHONPATH=src python3 -m unittest tests.test_task_pack_v2_schema -v
```

Expected: mutations under `additionalProperties: true` validate unexpectedly.

- [ ] **Step 3: Add explicit `$defs` and selected Skill schema**

Define exact records for candidates, score breakdown, capabilities, graph
nodes and edges, decomposition diagnostics, registry verification, and
compatibility. `selected-skill` must enumerate the actual pack keys and reuse
the existing Contract v2 schema for optional `contract`; allow the manifest
fields currently produced by `load_trusted_skill_pack_items()` and nothing
else.

Keep `intent-graph.schema.json` unchanged. Use strict integer validation in
tests so `true` cannot satisfy integer fields.

- [ ] **Step 4: Run all task-pack and compatibility tests**

```bash
PYTHONPATH=src python3 -m unittest \
  tests.test_task_pack_v2_schema tests.test_task_pack_v2_cli \
  tests.test_compatibility tests.test_validation -v
```

- [ ] **Step 5: Update verification schema registration and commit**

Register the selected Skill schema with `referencing.Registry` in test helpers
and `scripts/verify.sh`.

```bash
git add schemas/task-pack-v2.schema.json \
  schemas/task-pack-v2-selected-skill.schema.json \
  tests/test_task_pack_v2_schema.py tests/registry_cli_helpers.py \
  tests/test_task_pack_v2_cli.py scripts/verify.sh
git commit -m "feat: tighten nested task pack v2 schemas"
```

## Task 10: Author The Production Evaluation Suite

**Files:**

- Create: `evals/router-production/index.json`
- Create: `evals/router-production/normal.json`
- Create: `evals/router-production/multi-intent.json`
- Create: `evals/router-production/ambiguous.json`
- Create: `evals/router-production/negative.json`
- Create: `evals/router-production/perturbations.json`
- Create: `evals/router-production/safety.json`
- Modify: `tests/test_router_eval_review.py`
- Modify: `tests/test_router_eval_v2.py`

- [ ] **Step 1: Add exact distribution and scenario-coverage tests**

```python
EXPECTED_PRODUCTION_COUNTS = {
    "normal": 200,
    "multi_intent": 80,
    "ambiguous": 50,
    "negative": 50,
    "multilingual_typo_paraphrase": 40,
    "safety_sensitive": 30,
}

self.assertEqual(len(cases), 450)
self.assertEqual(Counter(case["category"] for case in cases), EXPECTED_PRODUCTION_COUNTS)
self.assertEqual(set(scenario_counts), bundle_scenario_ids())
self.assertTrue(all(count >= 5 for count in scenario_counts.values()))
```

Assert all IDs are unique and prefixed by their shard category.

- [ ] **Step 2: Run the suite tests and verify RED**

```bash
PYTHONPATH=src python3 -m unittest \
  tests.test_router_eval_review tests.test_router_eval_v2 -v
```

- [ ] **Step 3: Author the 200 normal cases**

Use IDs `normal-001` through `normal-200`. Cover every trusted scenario at
least five times across Chinese and English direct tasks. Every case declares
expected intents, expected scenarios, required dependency edges, forbidden
scenarios, forbidden Skills, expected status, and manually written task text.
Do not copy actual router output into labels.

- [ ] **Step 4: Author 80 multi-intent and 50 ambiguous cases**

Use `multi-intent-001` through `multi-intent-080` and `ambiguous-001` through
`ambiguous-050`. Include comma, `、`, slash, conjunction, list, mixed-language,
parallel, sequential, completion, verification, and release forms. Ambiguous
cases cover ordinary noun lists, file lists, report sections, hypothetical
actions, shared keywords, and tasks with only generic signals.

- [ ] **Step 5: Author 50 negative, 40 perturbation, and 30 safety cases**

Use stable category prefixes. Negative cases explicitly forbid the matching
scenario and Skill. Perturbations include Chinese/English code switching,
spacing, casing, common misspellings, and paraphrases without changing the
gold intent. Safety cases cover prompt injection, permission claims, secret
handling, untrusted Skills, publishing authority, and stale context.

- [ ] **Step 6: Build the suite index hashes**

Record each shard path, category, exact count, and canonical SHA-256. Run the
loader and ensure recomputed hashes match. Do not create a review record.

- [ ] **Step 7: Validate data independently from router execution**

```bash
PYTHONPATH=src python3 -m unittest \
  tests.test_router_eval_review tests.test_router_eval_v2 -v
PYTHONPATH=src python3 -m onecode_skill_sanitizer router-eval-v2 \
  --suite evals/router-production/index.json \
  --registry catalog --bundles bundles/index.json \
  > /tmp/router-production-unreviewed.json
jq '.case_count, .quality_gate.production_ready, .quality_gate.missing_gates' \
  /tmp/router-production-unreviewed.json
```

Expected: 450 cases evaluate; `production_ready` is false and
`independent_label_review` is missing.

- [ ] **Step 8: Commit the unreviewed corpus separately from routing rules**

```bash
git add evals/router-production tests/test_router_eval_review.py tests/test_router_eval_v2.py
git commit -m "test: add held-out router production corpus"
```

## Task 11: Run The Technical Quality Checkpoint

**Files:**

- Read: `evals/router-production/index.json`
- Read: `/tmp/router-production-checkpoint.json`
- Modify only through a separately approved plan amendment if a threshold
  fails: the exact source and focused test responsible for that failure

- [ ] **Step 1: Run the production suite and save the exact failure report**

```bash
PYTHONPATH=src python3 -m onecode_skill_sanitizer router-eval-v2 \
  --suite evals/router-production/index.json \
  --registry catalog --bundles bundles/index.json \
  > /tmp/router-production-checkpoint.json
jq '{metrics, failed:.quality_gate.failed_gates, missing:.quality_gate.missing_gates}' \
  /tmp/router-production-checkpoint.json
```

- [ ] **Step 2: Verify every technical threshold before review**

Required technical metrics:

- task-type Macro F1 at least `0.90`;
- scenario F1 at least `0.88`;
- required-capability recall at least `0.97`;
- both forbidden false-positive rates at most `0.005`;
- multi-intent exact match at least `0.80`;
- DAG validity exactly `1.0`;
- high-confidence error rate at most `0.02`;
- core Contract v2 coverage at least `0.80`;
- dependency-edge recall at least `0.90`.

- [ ] **Step 3: Stop on any technical failure**

If any threshold fails, do not make an unspecified rule change under this
task. Record the exact case IDs, issue IDs, metric deltas, and first shared
deterministic cause; invoke `superpowers:systematic-debugging`; then amend this
plan with a concrete red test, exact source edit, focused verification command,
and commit boundary for that proven cause. Never edit held-out labels in the
same commit as the rule fix.

- [ ] **Step 4: Record the passing unreviewed checkpoint**

When all technical thresholds pass, save their exact values for the closure
report. The only allowed missing gate at this point is
`independent_label_review`. No source commit is required for this read-only
checkpoint.

## Task 12: Obtain Independent Dataset Review

**Files:**

- Create after an actual reviewer decision:
  `evals/reviews/router-production-v1.json`
- Modify only if the reviewer rejects labels:
  affected `evals/router-production/*.json`
- Modify after any accepted label correction:
  `evals/router-production/index.json`

- [ ] **Step 1: Pause and request an independent reviewer**

Provide the reviewer with the suite index, shard files, schema, suite hash,
routing-rule commit, and review checklist. The reviewer must not be the author
of the routing-rule commits.

- [ ] **Step 2: Record rejected label findings separately**

If labels are rejected, change only the reviewed data and suite hashes in a
dedicated commit. Do not change router code in that commit. Re-run suite schema
and count checks, then request review of the new suite hash.

- [ ] **Step 3: Persist the accepted review record**

Only after the reviewer explicitly accepts the exact suite hash, create the
record with their stable identifier, role, reviewed commit, timestamp,
attestation, covered case IDs, decision, and exceptions.

- [ ] **Step 4: Verify the quality gate with review evidence**

```bash
PYTHONPATH=src python3 -m onecode_skill_sanitizer router-eval-v2 \
  --suite evals/router-production/index.json \
  --review evals/reviews/router-production-v1.json \
  --require-production-ready \
  --registry catalog --bundles bundles/index.json \
  > /tmp/router-production-approved.json
jq '.quality_gate' /tmp/router-production-approved.json
```

Expected: exit 0, no failed or missing gates, and `production_ready: true`.

- [ ] **Step 5: Commit review evidence**

```bash
git add evals/reviews/router-production-v1.json \
  evals/router-production/index.json evals/router-production/*.json
git commit -m "test: record independent router dataset review"
```

## Task 13: Make The Production Gate A Release Check

**Files:**

- Modify: `scripts/verify.sh`
- Modify: `tests/test_verify_script.py`

- [ ] **Step 1: Add failing script-content tests**

Assert `scripts/verify.sh` invokes the reviewed production suite with
`--require-production-ready`. Read `.github/workflows/verify.yml` and confirm
it still covers Python 3.11, 3.12, and 3.13; do not edit the workflow when the
matrix is already correct.

- [ ] **Step 2: Run and verify RED**

```bash
PYTHONPATH=src python3 -m unittest tests.test_verify_script -v
```

- [ ] **Step 3: Add the reviewed suite command to verification**

Keep the existing 100-case development eval and add:

```bash
PYTHONPATH=src python3 -m onecode_skill_sanitizer router-eval-v2 \
  --suite evals/router-production/index.json \
  --review evals/reviews/router-production-v1.json \
  --require-production-ready \
  --registry catalog \
  --bundles bundles/index.json >/dev/null
```

Do not weaken or remove existing verify steps.

- [ ] **Step 4: Run script tests and full verification**

```bash
PYTHONPATH=src python3 -m unittest tests.test_verify_script -v
PATH=/tmp/safe-agent-skills-structural-venv/bin:$PATH bash scripts/verify.sh
```

Expected: every check passes.

- [ ] **Step 5: Commit**

```bash
git add scripts/verify.sh tests/test_verify_script.py
git commit -m "ci: enforce router production quality gate"
```

## Task 14: Publish Closure Evidence

**Files:**

- Create: `docs/multi-intent-router-quality-remediation-closure-report-2026-07-11.md`
- Modify: `docs/router-development.md`
- Modify: `docs/smart-skill-router.md`
- Modify: `docs/maintenance-log.md`
- Modify: `docs/history.md`

- [ ] **Step 1: Write measured documentation only after the gate passes**

Record:

- motivating request intents and selected scenarios;
- old and new metrics with counts;
- production suite ID, hash, category distribution, and scenario coverage;
- independent review identity and decision without sensitive data;
- strict schema coverage;
- Schema v1 compatibility evidence;
- local verification count and CI matrix;
- method-only boundary and residual deterministic-language limits.

- [ ] **Step 2: Update current router guidance and historical routing**

Document span rules, limits, incomplete diagnostics, quality-gate CLI commands,
and the fact that semantic providers remain future work. Link the closure report
from `docs/history.md`; do not turn a dated report into the current source of
truth.

- [ ] **Step 3: Run documentation and full verification**

```bash
PYTHONPATH=src python3 -m unittest tests.test_documentation -v
git diff --check
PATH=/tmp/safe-agent-skills-structural-venv/bin:$PATH bash scripts/verify.sh
```

- [ ] **Step 4: Commit closure documentation**

```bash
git add docs/multi-intent-router-quality-remediation-closure-report-2026-07-11.md \
  docs/router-development.md docs/smart-skill-router.md \
  docs/maintenance-log.md docs/history.md
git commit -m "docs: close multi-intent router quality remediation"
```

- [ ] **Step 5: Run final committed-HEAD verification and publication workflow**

Run `bash scripts/verify.sh` from committed feature HEAD, fast-forward `main`,
run it again on `main`, push without force, and wait for Python 3.11, 3.12, and
3.13 GitHub Actions jobs. Remove the worktree and merged branch only after CI
passes and `main` equals `origin/main`.

## Plan Completion Checks

Before implementation handoff, verify this plan against the approved spec:

- every goal has at least one task;
- every production threshold has a boundary test and release gate;
- Schema v1 remains frozen;
- corpus changes and rule changes use separate commits;
- external reviewer evidence is a real pause, not generated metadata;
- no semantic provider, runtime permission, or catalog rename entered scope;
- all implementation tasks use failing tests before production code.
