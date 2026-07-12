# Release Readiness Proposition Parser Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace release-readiness proximity heuristics with bounded clause-level action-object propositions so genuine preparation requests route consistently while references, headings, filenames, non-software releases, and locally negated actions remain safe.

**Architecture:** Add a focused, pure parser that extracts release-readiness propositions with source offsets, action, software object, discourse role, and local polarity. Generation and validation consume the same parsed propositions; rejected generic release signals canonicalize to `general`, and a positive readiness proposition owns the evidence polarity even when a separate publish action is negated in the same sentence.

**Tech Stack:** Python 3.11+, frozen dataclasses, bounded regular-expression tokenization, `unittest`, existing intent decomposition/compiler APIs.

---

### Task 1: Define Proposition Contracts And RED Tests

**Files:**
- Create: `src/onecode_skill_sanitizer/release_propositions.py`
- Modify: `tests/test_intent.py`
- Modify: `tests/test_intent_spans.py`
- Modify: `tests/test_compiler.py`

- [ ] **Step 1: Add parser contract tests before implementation**

Test a pure API with this shape:

```python
@dataclass(frozen=True)
class ReleaseReadinessProposition:
    start: int
    end: int
    action: str
    object_text: str
    polarity: str       # positive or negative
    discourse_role: str # request or reference

def parse_release_readiness_propositions(source: str) -> tuple[ReleaseReadinessProposition, ...]:
    ...
```

Positive request matrices must include direct checklist/readiness commands, repository and maintainer packets, `npm` packages, Docker images, and versioned artifacts. Equivalent coordination forms must yield one positive proposition:

```python
"Prepare a repository release packet for review, but do not publish it."
"Do not publish it yet, but prepare a repository release checklist."
"Audit unauthorized access and prepare a repository release packet."
"Prepare an npm release packet."
"Draft a Docker image release checklist."
"Review the release checklist for v1.0."
```

Negative/reference matrices must include `can't`, `cannot`, `no need`, `not authorized`, `mustn't`, `should not`, quoted text, Markdown/HTML headings, blockquotes, checkboxes, labels, titles, filenames, README descriptions, navigation text, and talent/model/content releases.

- [ ] **Step 2: Add end-to-end RED assertions**

For every rejected control, assert all three properties:

```python
graph = decompose_task_detailed(task).intent_graph
assert graph.validate() == []
assert all(item.task_type != "open_source_release" for item in graph.intent_evidence)
assert compile_task_pack(graph, ...)["reason_codes"] != ["invalid_intent_graph"]
```

For positive readiness, assert `open_source_release/readiness/positive`, a valid graph, and a ready compiler result. Preserve release-action controls unchanged.

- [ ] **Step 3: Run RED**

```bash
PYTHONPATH=src python3 -m unittest \
  tests.test_intent tests.test_intent_spans tests.test_compiler -v
```

Expected: the new parser import/API and reviewer examples fail for the confirmed proximity/polarity behavior.

### Task 2: Implement The Bounded Proposition Parser

**Files:**
- Create: `src/onecode_skill_sanitizer/release_propositions.py`
- Test: `tests/test_intent.py`

- [ ] **Step 1: Implement bounded structural scanning**

Use `bound_task_text()` before parsing. Locate readiness objects (`release checklist`, `release packet`, `release readiness`, `发布清单`) with exact token boundaries and bounded occurrence count. For each occurrence:

1. derive the containing clause and coordinated proposition using punctuation plus `and/but/then` and Chinese connector boundaries;
2. reject occurrences structurally enclosed by quotes/code, headings, blockquotes, checklist labels, navigation/title labels, or filename suffixes;
3. bind the nearest allowed action to the object rather than accepting any action in a 192-character window;
4. compute polarity from modifiers attached to that action (`not`, `n't`, `never`, `no need`, `not authorized`, and Chinese negators);
5. require a software artifact anchor from repository/package/maintainer/code/open-source terms, ecosystem identifiers such as npm/Docker, or a version token; retain only the exact historical standalone checklist command as a compatibility form;
6. return source offsets and never raise for arbitrary bounded text.

Do not add broad deny-word lists such as `stale` or `without publishing`; those describe packet contents or constraints, not the polarity of the preparation action.

- [ ] **Step 2: Run parser tests GREEN**

```bash
PYTHONPATH=src python3 -m unittest tests.test_intent -v
```

Expected: proposition matrices pass, including equivalent clause-order cases.

### Task 3: Integrate One Parser Into Generation And Validation

**Files:**
- Modify: `src/onecode_skill_sanitizer/intent_evidence.py`
- Modify: `src/onecode_skill_sanitizer/intent_spans.py`
- Test: `tests/test_intent_spans.py`
- Test: `tests/test_compiler.py`

- [ ] **Step 1: Replace readiness heuristics with parser consumption**

Keep `source_supports_release_readiness()` as a compatibility wrapper, but implement it by selecting a positive request proposition from `parse_release_readiness_propositions()`. Remove proximity-window and expanding deny-list logic.

In `_profile_evidence()`:

- emit `open_source_release/readiness` only for a positive request proposition;
- set readiness evidence polarity from the proposition (`positive`), not an unrelated negative publish clause;
- preserve confirmed release action evidence;
- canonicalize every other generic release match to empty `general/none` evidence.

In semantic validation, reparse the complete bound source and require a matching positive proposition. Do not trust caller-supplied evidence and do not weaken provenance hashing.

- [ ] **Step 2: Run decomposition/compiler tests GREEN**

```bash
PYTHONPATH=src python3 -m unittest \
  tests.test_intent tests.test_intent_spans tests.test_intent_dependencies \
  tests.test_compiler -v
```

Expected: all new matrices and existing release action/readiness tests pass.

- [ ] **Step 3: Commit the architectural replacement**

```bash
git add src/onecode_skill_sanitizer/release_propositions.py \
  src/onecode_skill_sanitizer/intent_evidence.py \
  src/onecode_skill_sanitizer/intent_spans.py \
  tests/test_intent.py tests/test_intent_spans.py tests/test_compiler.py \
  docs/superpowers/plans/2026-07-12-release-readiness-proposition-parser.md
git commit -m "refactor: parse release readiness propositions"
```

### Task 4: Verify The Root Cause Boundary

**Files:**
- Read: `evals/router-production/index.json`
- Read: `/tmp/router-production-after-readiness.json`

- [ ] **Step 1: Run focused and full verification**

```bash
PATH=/tmp/safe-agent-skills-structural-venv/bin:$PATH PYTHONPATH=src \
  bash scripts/verify.sh
```

Expected: exit 0 with no existing regression.

- [ ] **Step 2: Run the held-out suite without changing gold**

```bash
PYTHONPATH=src python3 -m onecode_skill_sanitizer router-eval-v2 \
  --suite evals/router-production/index.json \
  --registry catalog --bundles bundles/index.json \
  > /tmp/router-production-after-readiness.json
```

Expected for this task boundary: `normal-122` and `multi-intent-039` no longer produce invalid release evidence. If the command still exits 2, record the next independent case and begin a new systematic-debugging cycle; do not change corpus labels.

- [ ] **Step 3: Independent reviews**

Run specification review, then code-quality/adversarial review. Rework the same commit until both approve before starting the `multi-intent-013` negation fix.

## Plan Self-Review

- Spec coverage: positive requests, structural references, local polarity, clause order, safe downgrade, generation/validation parity, provenance, legacy compatibility, and held-out verification are all assigned to explicit tasks.
- Placeholder scan: no TODO/TBD or unspecified implementation step remains.
- Type consistency: the parser returns immutable `ReleaseReadinessProposition` records; generation and validation share the same tuple API.
- Scope: no schema, evaluator, catalog, bundle, or gold change is authorized.
