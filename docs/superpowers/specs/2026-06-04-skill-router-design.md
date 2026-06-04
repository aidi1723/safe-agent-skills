# Skill Router Design

Date: 2026-06-04

Project: `Safe-Agent-Skills`

## Goal

Upgrade `task-pack` from a simple trusted skill selector into a more accurate
task-aware skill router.

The first implementation should focus on deterministic scenario composition:

```text
user task
  -> task profile
  -> scenario bundle candidates
  -> required skill coverage
  -> supplemental trusted skills
  -> ordered execution plan
  -> verification and safety boundary
```

The router should help any host agent, including Claude, Codex, OpenClaw,
Cursor, MCP hosts, local agents, and custom agents, choose the right cleaned
skills for a task without granting runtime permissions.

## Current Problem

The current selector is useful but still first-generation:

- It classifies the task into a taxonomy category.
- It scores skills by taxonomy match and simple token overlap.
- It can include scenario bundles only when they overlap with selected skills.

This is safe and deterministic, but it can miss intent. For example, a website
task should usually combine requirements, UI, engineering, SEO, browser
verification, and publish checks. A keyword-only selector may pick a few nearby
skills but fail to explain the correct execution order or coverage gaps.

## Recommended Approach

Build the next version as a deterministic `Skill Router`, not a model-driven
planner.

Why:

- It keeps safety and explainability stronger.
- It is easy to test with fixed tasks and expected selections.
- It works without external model calls or network access.
- It preserves the current open-source value: any agent can call the tool.

Model-assisted routing can be added later as an optional review layer, but it
should not be required for the first router release.

## Non-Goals For First Router Release

The first release should not:

- execute selected skills
- grant host runtime permissions
- call external LLM APIs
- crawl GitHub automatically
- learn from private user task history
- select `quarantined`, `rejected`, or `disabled` skills
- include `review_required` skills unless review mode is explicitly enabled

## Router Concepts

### Task Profile

The router should convert a task into a structured profile:

```json
{
  "task_type": "website_build",
  "primary_domain": "web",
  "secondary_domains": ["design", "content", "engineering"],
  "artifact_types": ["website", "copy", "release_checklist"],
  "risk_flags": ["public_release"],
  "required_capabilities": [
    "requirements",
    "engineering_release",
    "ui_review",
    "seo_copy",
    "browser_verification",
    "publish_check"
  ]
}
```

This profile can be produced with deterministic keyword and taxonomy rules at
first. The profile should be included in JSON and Markdown outputs so the host
agent knows why the tool made a selection.

### Scenario Bundle First

If a task clearly matches a scenario bundle, the router should choose the
bundle first, then choose skills inside or near that bundle.

Examples:

| Task signal | Preferred bundle |
| --- | --- |
| website, landing page, official site, dashboard launch | `website-build-launch` |
| PR review, generated code, bug fix, refactor risk | `code-review-hardening` |
| prompt injection, connector, tool permission, agent safety | `security-agent-guardrails` |
| PDF, docs, markdown conversion, knowledge base | `document-to-knowledge-base` |
| RAG, retrieval, vector DB, citations | `rag-agent-knowledge-app` |
| dataset, spreadsheet, chart, report | `data-analysis-report` |
| open source, publish repo, release statement | `open-source-release` |
| article, SEO, social copy, public content | `content-seo-publication` |
| listing, keyword, inquiry, trade reply | `commerce-listing-growth` |

Bundle-first routing gives the system better task-level judgment than picking
individual skills in isolation.

### Required Capability Coverage

Each scenario should define required capabilities. A selected task pack should
show which capabilities are covered and which are missing.

Example for website launch:

```text
requirements: covered by business-requirements-brief
engineering_release: covered by engineering-build-release
ui_review: covered by design-ui-review
design_consistency: covered by design-system-consistency
seo_copy: covered by content-seo-brief
browser_verification: covered by execution-browser-check
publish_check: covered by execution-publish-check
```

This makes the result easier to trust than a raw score list.

### Supplemental Skill Selection

After bundle selection, the router should add supplemental trusted skills only
when they improve coverage or match the task strongly.

Rules:

- Prefer skills from the selected bundle.
- Add external skills only when they match an uncovered required capability.
- Keep the output small by default.
- Never add a skill only because of weak token overlap.
- Preserve stable ordering for deterministic outputs.

### Execution Order

The task pack should include an ordered execution plan:

```text
1. Clarify requirements and acceptance criteria.
2. Plan implementation or content structure.
3. Apply domain-specific skill guidance.
4. Run safety and quality checks.
5. Run verification commands or manual checks.
6. Report evidence, selected skills, sources, and unresolved risks.
```

For known bundles, this order should be scenario-specific.

Website example:

```text
1. business-requirements-brief
2. engineering-build-release
3. design-ui-review
4. design-system-consistency
5. content-seo-brief
6. execution-browser-check
7. execution-publish-check
8. content-social-post
```

### Explanation Output

Every selected skill and bundle should include an explanation:

```json
{
  "name": "design-ui-review",
  "role": "core",
  "confidence": 0.86,
  "matched_capabilities": ["ui_review"],
  "selection_reason": "The task asks for a website build and needs interface review before launch."
}
```

This makes the tool easier to debug, easier to trust, and easier to publish as
a general-purpose agent utility.

### Safety Boundary

The safety statement remains unchanged:

```text
skill guidance is method, not execution authority
```

The router may choose skills, order them, and explain why. It must not:

- execute commands
- expand tool permissions
- bypass host approvals
- hide selected skill provenance
- treat community reference workflows as runtime code

The host runtime still controls filesystem, shell, browser, network,
connector, credential, deployment, and production permissions.

## Output Contract Additions

The next task-pack JSON should add:

```json
{
  "router": {
    "mode": "deterministic_scenario_router",
    "version": 1
  },
  "task_profile": {},
  "selected_scenario": {},
  "coverage": [],
  "execution_plan": [],
  "selection_explanations": []
}
```

Markdown output should add matching sections:

- `Task Profile`
- `Selected Scenario`
- `Capability Coverage`
- `Execution Plan`
- `Selection Explanations`

The existing fields should remain compatible:

- `skills`
- `bundles`
- `agent_instructions`
- `safety_boundary`
- `registry_verification`

## CLI Shape

Keep the current `task-pack` command and add router options:

```bash
PYTHONPATH=src python3 -m onecode_skill_sanitizer task-pack \
  "build a product website and prepare launch checks" \
  --registry catalog \
  --include-bundles \
  --bundles bundles/index.json \
  --router scenario \
  --format json
```

Suggested options:

- `--router simple`: current behavior, preserved for compatibility
- `--router scenario`: deterministic scenario router, recommended default
- `--max-skills N`: maximum selected skills after routing
- `--explain`: include verbose explanation records

The initial release can keep `simple` as default and document `scenario` as
the recommended mode. After enough tests, `scenario` can become the default.

## Data Model Changes

Bundle records should optionally support:

```json
{
  "task_signals": ["website", "landing page", "launch"],
  "required_capabilities": [
    {
      "id": "ui_review",
      "required": true,
      "preferred_skills": ["design-ui-review", "design-system-consistency"]
    }
  ],
  "execution_order": [
    "business-requirements-brief",
    "engineering-build-release",
    "design-ui-review"
  ]
}
```

The current bundle format should remain valid. Missing new fields can be
derived from existing `scenario`, `skills`, and `expected_output`.

## Testing Plan

Add focused tests for:

- website task selects `website-build-launch`
- RAG task selects `rag-agent-knowledge-app`
- PDF-to-knowledge-base task selects `document-to-knowledge-base`
- code review task selects `code-review-hardening`
- security agent task selects `security-agent-guardrails`
- selected bundle must reference only trusted skills
- router output includes execution plan and explanations
- `quarantined` and `review_required` skills remain excluded by default
- `simple` router remains backward compatible

## Acceptance Criteria

The router is ready when:

- `task-pack --router scenario --include-bundles` produces deterministic
  scenario-aware results.
- Output explains why each bundle and skill was selected.
- Output includes ordered execution steps.
- Existing task-pack tests still pass.
- Registry and bundle verification still gate generation.
- No runtime permissions are granted by router output.

## Open Questions

1. Should `scenario` become the default immediately, or should it be opt-in
   for one release?
2. Should each skill manifest add explicit capability tags, or should the first
   release derive capabilities from bundle metadata?
3. Should confidence be a normalized `0.0-1.0` value or a simpler
   `low/medium/high` label?

## Recommendation

Implement the first router release as:

- opt-in: `--router scenario`
- deterministic only
- bundle-first
- coverage-aware
- explanation-rich
- backward compatible with current `task-pack`

This gives the project a stronger public value without weakening the safety
model or requiring external AI calls.
