# One Trusted Skill Router Blog Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Produce a publication-ready Chinese engineering blog that explains how one trusted routing Skill replaces manual community Skill discovery, safety review, configuration, and orchestration.

**Architecture:** The article starts from user pain, introduces the single-entry model, then progressively explains supply-chain governance, deterministic routing, multi-intent DAG compilation, host execution boundaries, measured evidence, and current limitations. Every quantitative claim is checked against the repository closure and readiness reports.

**Tech Stack:** Markdown, repository documentation, CLI examples, Mermaid diagrams

---

### Task 1: Draft The User Problem And Promise

**Files:**
- Create: `docs/blog-one-trusted-skill-router-2026-07-10.md`

- [ ] **Step 1: Write the opening around community Skill overload**

Cover discovery difficulty, unsafe instructions, overlapping capabilities,
configuration cost, and orchestration uncertainty.

- [ ] **Step 2: State the bounded single-entry promise**

Use: “只需安装一个安全路由入口，就能根据任务自动选择、组合可信 Skill，并生成可验证的执行方案。”

### Task 2: Explain Architecture And Safety

**Files:**
- Modify: `docs/blog-one-trusted-skill-router-2026-07-10.md`

- [ ] **Step 1: Add the trusted supply-chain flow**

Describe capture, scan, sanitize, classify, contract, approve, and trusted-only routing.

- [ ] **Step 2: Add the routing compiler flow**

Describe intent decomposition, scenario retrieval, composition, DAG compilation,
verification gates, approval signals, and host execution.

- [ ] **Step 3: Add Mermaid diagrams**

Include manual workflow versus single-entry workflow and the system boundary.

### Task 3: Add The Real Compound Example

**Files:**
- Modify: `docs/blog-one-trusted-skill-router-2026-07-10.md`

- [ ] **Step 1: Use the mandatory Chinese compound task**

Show the three selected scenarios, 30 nodes, 31 edges, and 7 host-action nodes.

- [ ] **Step 2: Explain why this is orchestration, not keyword search**

Show that release depends on verification and completion from both preceding paths.

### Task 4: Add Evidence And Limitations

**Files:**
- Modify: `docs/blog-one-trusted-skill-router-2026-07-10.md`

- [ ] **Step 1: Add verified engineering evidence**

Include 321 passing tests, Contract coverage, and independent review status.

- [ ] **Step 2: Add the 100-case quality table**

Include exact match, precision, recall, F1, dependency recall, DAG validity, and
forbidden-scenario false-positive rate.

- [ ] **Step 3: State non-goals clearly**

Do not claim autonomous execution, permission grants, semantic routing, or
production quality approval.

### Task 5: Add Quick Start And Publication Polish

**Files:**
- Modify: `docs/blog-one-trusted-skill-router-2026-07-10.md`
- Modify: `README.md`

- [ ] **Step 1: Add installation and command examples**

Use the public GitHub repository and the single router entry workflow.

- [ ] **Step 2: Add a README blog link**

Place the article near the current closure and delivery documentation links.

- [ ] **Step 3: Verify formatting and claims**

Run:

```bash
git diff --check
rg -n "321|0.9448|0.1429|0.89|8.18|30 nodes|31 edges|7 host-action" docs/blog-one-trusted-skill-router-2026-07-10.md
```

Expected: no diff errors and all required evidence present.
