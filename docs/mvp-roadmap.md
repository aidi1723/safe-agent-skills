# MVP Roadmap

## MVP 0: Documentation And Fixtures

Deliverables:

- standalone project folder
- architecture document
- skill taxonomy
- sanitization policy
- manifest schema
- example report

Success:

- project can be understood without reading OneCode core
- clear boundary between skill guidance and kernel authority
- collection and runtime selection can use a shared category directory

## MVP 1: Local Sanitizer CLI

Command shape:

```bash
onecode-skill-sanitizer scan ./incoming/skill
onecode-skill-sanitizer sanitize ./incoming/skill --out ./registry/skill-name
onecode-skill-sanitizer audit ./registry/skill-name
```

Capabilities:

- parse local folders
- hash source files
- detect `SKILL.md`
- classify skills into the shared taxonomy
- run deterministic risk scanner
- generate sanitized `SKILL.md`
- generate `skill.json`
- generate `SANITIZATION_REPORT.json`
- audit approved skills against sanitized hashes
- approve reviewed skills into `trusted` state
- reject and disable reviewed skills
- batch import local incoming folders into category registry paths
- generate and rebuild `registry/index.json`
- list, inspect, and select skills from the registry
- verify registry integrity, tamper state, and provenance completeness

No network crawling yet.

## MVP 2: OneCode Integration

OneCode commands:

```bash
onecode skills list
onecode skills inspect <name>
onecode skills sanitize --source ./incoming/foo --out ./skills/foo
onecode run-model "task" --skill foo
```

Capabilities:

- load trusted sanitized skills
- inject skill instructions into model planning prompt
- record selected skills and skill hashes in evidence
- reject untrusted skills by default
- consume `registry/index.json` and verify selected skill manifest hash before use

## MVP 3: Verifier Binding

Capabilities:

- each skill declares required verifiers
- `run-model --skill` checks verifier availability
- missing verifier blocks delivery or marks review-required
- verifier result is tied to skill evidence

## MVP 4: Community Intake

Capabilities:

- import from Git URL
- record commit and source hash
- scan without execution
- quarantine by default
- produce diff between source and sanitized output

No automatic trust.

## MVP 5: Registry And Review UI

Capabilities:

- list quarantined skills
- show risk findings
- approve / reject / disable
- compare source and sanitized versions
- show usage history

## Open Questions

- Should sanitized skills be stored inside OneCode repo or a user-level registry?
- Which verifier presets are required for `design`, `code`, `engineering`, `security`, `office`, and `execution`?
- Should LLM-based distillation be optional, with deterministic extraction as a fallback?
- How much source text can be preserved before token cost becomes unacceptable?
- What human review role is needed for `high` and `critical` findings?
