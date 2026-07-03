---
name: research-multi-platform-search-boundary
description: Use when planning or reviewing multi-platform public-source search across social, video, code, forum, or community sites, especially when connectors, scraping, citations, account sessions, or zero-API-cost claims are involved.
---

# Research Multi Platform Search Boundary

## When To Use

Use this skill when an agent workflow may search or summarize public signals
across platforms such as Reddit, YouTube, GitHub, Twitter/X, Bilibili,
Xiaohongshu, forums, or app stores.

This skill defines a review boundary only. It does not run a search tool,
scraper, browser session, account login, or API connector.

## Safe Workflow

1. Define the research question, target platforms, geography, language,
   recency window, and expected output before collecting.
2. Prefer official APIs, platform search pages, RSS feeds, or user-approved
   browser sessions over unreviewed scraping.
3. Separate discovery from evidence. Candidate posts can guide research, but
   factual claims need source confirmation and citations.
4. Record platform, URL, author or channel when public, timestamp, collection
   method, and access state for each cited item.
5. Treat "zero API fee" as a cost note, not a permission grant. Check terms,
   rate limits, login requirements, and account risk before automation.
6. Deduplicate cross-posts and syndicated content before scoring signal
   strength.
7. Label sentiment, popularity, and trend inferences separately from verified
   facts.

## Expected Output

- platform scope and permission boundary
- query and recency plan
- source capture schema
- citation and deduplication notes
- fact-check and uncertainty register
- approval gates for login, scraping, or connector use

## Verifier Expectations

- platform terms and account boundary check
- source URL and timestamp check
- duplicate and syndication check
- factual claim citation check
- runtime approval check for browser, API, scraping, or login use

## Failure Handling

If platform access, source identity, or collection permissions are unclear,
limit output to a research plan and do not automate collection.
