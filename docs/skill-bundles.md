# Skill Bundles

Skill bundles combine multiple trusted skills into scenario playbooks.

They answer a different question from `task-pack`:

- `task-pack`: Which individual skills match this task?
- `skill bundles`: Which proven skill combination should an agent use for this
  whole scenario?

For example, building a website is rarely only a design task. A good website
workflow may need requirements, engineering, UI review, content, SEO, browser
verification, and publish readiness. A bundle records that combination so an
agent can start from a more complete plan.

## Files

- human-readable bundle catalog: `bundles/README.md`
- machine-readable bundle index: `bundles/index.json`

## Current Scenario Coverage

| Bundle | Use Case |
| --- | --- |
| `website-build-launch` | Build or polish a website and prepare release checks |
| `code-review-hardening` | Review code, tests, schema contracts, and dependency risk |
| `security-agent-guardrails` | Review agent guardrails, I/O scanning, and prompt injection |
| `document-to-knowledge-base` | Convert documents into Markdown, chunks, summaries, and notes |
| `data-analysis-report` | Clean data, analyze tables, plan visuals, and write reports |
| `open-source-release` | Prepare a public repository or artifact for release |
| `content-seo-publication` | Draft and review SEO/GEO content for publication |
| `commerce-listing-growth` | Prepare marketplace listings and buyer communication |

## Safety Rule

Bundles do not grant permissions. They only recommend a sequence of trusted
skills and expected outputs. The host runtime still controls filesystem,
network, shell, connector, account, and production permissions.

## Future Runtime Integration

The next step is to let `task-pack` optionally include bundle suggestions:

```bash
PYTHONPATH=src python3 -m onecode_skill_sanitizer task-pack \
  "build a product landing page and prepare launch copy" \
  --registry catalog \
  --include-bundles
```

Until then, bundles can be used manually by reading `bundles/README.md` or by
loading `bundles/index.json` from another agent runtime.
