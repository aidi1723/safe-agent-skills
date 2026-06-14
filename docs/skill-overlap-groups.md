# Skill Overlap Groups

`catalog/overlap-groups.json` records functional overlap between trusted skills.
It is a selection hint layer, not a removal list.

The catalog intentionally keeps adjacent trusted skills when they protect
different failure modes. The overlap file helps routers and operators avoid
loading too many similar skills for a narrow task while preserving the stronger
guardrail for broader workflows.

## Current Status

```text
overlap groups: 7
group status: all trusted
referenced trusted skills: 29
source file: catalog/overlap-groups.json
```

Current groups:

| Group | Primary skill | Adjacent scope |
| --- | --- | --- |
| AI Routing, Budget, and Context | `ai-model-route-fallback-review` | token budget, context compression, OpenSquilla routing, tool schema checks |
| RAG Retrieval Boundaries | `ai-llamaindex-rag-knowledge-workflow` | Haystack pipeline, Qdrant retrieval, namespace boundaries |
| Source, Fact, and Evidence | `research-source-check` | source lineage, citation maps, contradiction review |
| Table and Numeric Evidence | `data-table-calculation-verify` | table analysis, office table reconciliation, spreadsheet cleanup |
| UI Quality Review | `design-ui-review` | design system consistency, accessibility, responsive viewport, Tailwind/Radix system, motion, and premium landing checks |
| Browser Execution Verification | `execution-playwright-browser-automation` | browser checks and web-task execution guidance |
| Public Claims Compliance | `content-claims-compliance-filter` | public claim risk, terms review, freshness review |

## Selection Rule

Use `primary_skill` first when the user task is narrow and directly matches the
group. Add `adjacent_skills`, `use_before`, or `use_after` only when the task
requires the extra boundary.

Examples:

- A quick UI review starts with `design-ui-review`.
- A UI release with accessibility and mobile regressions adds
  `design-accessibility-check` and `design-responsive-viewport-check`.
- A premium Tailwind/Radix landing page adds `design-tailwind-radix-system`,
  `design-premium-landing-page`, and `design-motion-interaction-polish`.
- A basic factual answer starts with `research-source-check`.
- A public report with citations and inconsistency risk adds
  `research-citation-evidence-map` and
  `content-fact-contradiction-review`.

## Maintenance Gate

`maintain-check` auto-loads `catalog/overlap-groups.json` when the file exists
under the selected registry directory. A custom path can be passed explicitly:

```bash
PYTHONPATH=src python3 -m onecode_skill_sanitizer maintain-check \
  --registry catalog \
  --bundles bundles/index.json \
  --overlap-groups catalog/overlap-groups.json
```

The gate fails when:

- `group_count` does not match the number of groups
- a group does not declare `status: trusted`
- a group id is duplicated
- a referenced skill is missing
- a referenced skill is not `trusted`
- the same skill is repeated inside one group

This keeps overlap metadata aligned with the same trusted-only standard used by
scenario bundles.
