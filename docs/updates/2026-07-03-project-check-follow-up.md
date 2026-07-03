# Project Check Follow-Up

Date: 2026-07-03

## Summary

A full project check found and fixed a sanitizer false-positive removal issue:
protective sensitive-data guidance that mentioned credentials, private files,
or broad workspace access could be stripped from catalog skills.

The scanner now preserves defensive boundary wording that starts with verbs
such as remove, redact, check, review, avoid, do not, never, block, stop, flag,
and require, while still removing dangerous instructions such as searching the
whole machine for credentials.

## Affected Catalog Entries

Regenerated and reindexed:

- `ai-rule-failure-log-synthesis`
- `execution-mcp-tool-connector-review`

## Regression Coverage

Added tests for:

- preserving protective sensitive-data guidance during sanitization
- rejecting dangerous credential-search wording
- contiguous `Safe Workflow` numbering across catalog skills

## Current Verified Baseline

```text
catalog skills: 172
trusted skills: 166
trusted scenario bundles: 23
external references: 19
trusted overlap groups: 7
claude-skills candidate coverage: 336 / 336
router eval cases: 34
tampered skills: 0
unknown provenance records: 0
full script: 129 tests OK
```

## Boundary

This update only changes sanitizer/catalog behavior, regression tests, and
documentation. It does not grant new runtime, network, browser, connector,
account, credential, production, regulated-domain, or publication permissions.

The deterministic scanner and sanitizer remain preflight guardrails, not a
complete malware detector or substitute for host runtime sandboxing.

## Verification Targets

- `bash scripts/verify.sh`
- `PYTHONPATH=src python3 -m onecode_skill_sanitizer verify --registry catalog`
- `PYTHONPATH=src python3 -m onecode_skill_sanitizer maintain-check --registry catalog --bundles bundles/index.json --references external-references/index.json --claude-skills-candidate-map docs/claude-skills-candidate-map.json`
- `PYTHONPATH=src python3 -m onecode_skill_sanitizer router-eval --eval evals/router-quality.json --registry catalog --bundles bundles/index.json`
- `git diff --check`
