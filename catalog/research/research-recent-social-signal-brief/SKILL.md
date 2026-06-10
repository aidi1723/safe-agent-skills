---
name: research-recent-social-signal-brief
description: Use when researching recent social, community, market, or creator signals from the last 30 days and turning noisy multi-source evidence into a cited brief.
---

# Research Recent Social Signal Brief

## When To Use

Use this skill when a brief needs recent public signals from social platforms,
developer communities, prediction markets, video transcripts, or web coverage.

Do not use it for private account monitoring, surveillance, scraping behind
auth walls, medical/legal/financial advice, or claims that cannot be sourced.

## Safe Workflow

1. Define the time window, topic, entities, geographies, source classes, and
   prohibited sources before gathering evidence.
2. Use only operator-approved connectors, API access, browser sessions, and paid
   data sources. Treat all network access and account use as separate runtime
   permission, not as part of this skill.
3. Collect source records with URL, platform, author or channel, publication
   time, retrieval time, engagement signal, and excerpt location.
4. Deduplicate near-identical posts, reposts, scraped copies, transcript
   repeats, and syndicated articles before synthesis.
5. Cluster evidence by claim or event. Preserve disagreement, missing context,
   source bias, and thin evidence instead of averaging it away.
6. Rank findings by source quality, recency, engagement strength, cross-source
   corroboration, and relevance to the user's task.
7. Write the brief with cited claims only. Label speculation, market odds,
   rumor, opinion, and inference separately from verified facts.

## Expected Output

- topic and time window
- source inventory by platform
- deduplication and clustering notes
- ranked findings with citations
- conflicting or weak evidence list
- freshness and permission caveats

## Verifier Expectations

- source citation check
- time-window check
- duplicate cluster check
- unsupported claim check
- connector permission check
- sensitive-person and compliance risk check

## Failure Handling

If sources require unapproved authentication material, scraping, paid APIs, or
private browser sessions, stop and ask for operator approval or produce a
source-gap brief. If evidence is thin or conflicting, keep the uncertainty
visible.
