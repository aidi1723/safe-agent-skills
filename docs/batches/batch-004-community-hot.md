# Batch 004 Community Hot Skills

## Purpose

Collect and sanitize reference-style skills from currently popular community
agent, memory, compression, security, and trading projects.

This batch does not copy third-party prompt bodies or runtime code. Each skill
is rewritten in OneCode's own words as a bounded workflow card with provenance,
license, and safety status.

## Provenance

| Skill | Source | Author | License | Status | Decision |
| --- | --- | --- | --- | --- | --- |
| `ecc-agent-coding-safety` | https://github.com/affaan-m/ecc | affaan-m | MIT | trusted | Safe as a context-engineering and coding-safety workflow |
| `headroom-context-compression` | https://github.com/chopratejas/headroom | chopratejas | Apache-2.0 | trusted | Safe as a context compression workflow |
| `hermes-agent-memory-assistant` | https://github.com/NousResearch/hermes-agent | NousResearch | MIT | quarantined | Kept for memory policy review; not normal task selection yet |
| `supermemory-memory-engine-reference` | https://github.com/supermemoryai/supermemory | supermemoryai | MIT | quarantined | Kept for memory-engine design review; connector approval needed |
| `trivy-container-security-scan` | https://github.com/aquasecurity/trivy | Aqua Security | Apache-2.0 | trusted | Safe as a bounded security scan review workflow |
| `vibe-trading-research-assistant` | https://github.com/HKUDS/Vibe-Trading | HKUDS | MIT | quarantined | Finance and broker-adjacent risk; research-only until compliance review |

## Included Skills

| Skill | Category | Subcategory | Purpose |
| --- | --- | --- | --- |
| `ecc-agent-coding-safety` | ai | ai.context-engineering | Adapt context-engineering patterns for safer AI coding |
| `headroom-context-compression` | ai | ai.context-compression | Compress context while preserving decisions and safety boundaries |
| `hermes-agent-memory-assistant` | ai | ai.memory | Review assistant memory and personalization policies |
| `supermemory-memory-engine-reference` | ai | ai.memory | Design persistent memory retrieval with privacy controls |
| `trivy-container-security-scan` | security | security.container | Review container, dependency, IaC, secret, and SBOM scan findings |
| `vibe-trading-research-assistant` | compliance | compliance.finance | Review trading research with financial safety boundaries |

## Publication Notes

These entries are suitable for a public catalog as reference-style records
because:

- no third-party skill text, prompts, or executable code are copied
- every item records URL, author, license, collector, and capture timestamp
- community inspiration is credited explicitly
- trusted status is limited to non-autonomous, low-risk workflows
- memory and finance-adjacent items remain quarantined until connector and
  compliance review exist

## Batch Status

Completed.

Result:

- imported skills: 6
- trusted skills in this batch: 3
- quarantined skills in this batch: 3
- catalog total skills after batch: 21
- catalog trusted skills after batch: 18
- tampered skills: 0
- unknown provenance records: 0
- registry verification: `ok`

Verified catalog entries:

- `catalog/ai/ecc-agent-coding-safety`
- `catalog/ai/headroom-context-compression`
- `catalog/ai/hermes-agent-memory-assistant`
- `catalog/ai/supermemory-memory-engine-reference`
- `catalog/security/trivy-container-security-scan`
- `catalog/compliance/vibe-trading-research-assistant`
