# Batch 029 Claude Skills Backlog Clusters

This batch converts the remaining `claude-skills` reference-only backlog into
local OneCode-authored cluster skills.

It does not copy, install, execute, or trust upstream `claude-skills` bodies.
Each cluster is a bounded local workflow that covers one backlog category and
keeps runtime permissions with the host agent.

## Cluster Skills

| Skill | Category | Covered Backlog |
| --- | --- | --- |
| `ai-claude-skills-meta-workflow-review` | ai | loop-library and meta-workflow references |
| `business-claude-skills-backlog-orchestration` | business | product, SaaS, executive, and operating templates |
| `code-claude-skills-engineering-role-review` | code | developer-role and cloud architecture templates |
| `compliance-claude-skills-regulated-review` | compliance | RA/QM, AI governance, privacy, ISO, FDA, and GDPR references |
| `content-claude-skills-growth-review` | content | marketing, lifecycle, CRO, copy, ASO, and social growth references |
| `engineering-claude-skills-operations-review` | engineering | MCP, onboarding, observability, environment, setup, run, and status references |
| `execution-claude-skills-productivity-review` | execution | capture, inbox, reflection, and personal execution templates |
| `office-claude-skills-document-review` | office | Markdown, HTML, document, slides, and review helpers |
| `research-claude-skills-evidence-review` | research | grants, literature review, patent, dossier, syllabus, and deep-research references |

## Scenario Bundle

The batch also adds `claude-skills-backlog-coverage` to `bundles/index.json`.
The bundle is selected for `claude-skills`, reference-only backlog, candidate
map, and skill-library inclusion tasks. It composes the nine cluster skills
with `security-supply-chain-review` so future backlog maintenance keeps
coverage, routing noise, and upstream-supply-chain risks in one execution plan.

## Safety Boundary

- Upstream content remains metadata-only reference material.
- Trusted cluster skills provide method guidance only.
- Connector, shell, browser, filesystem, account, deployment, and production
  permissions remain controlled by the host runtime and operator approval
  layer.
- Candidate-map conversion means covered by a trusted local skill, not copied
  from upstream.
