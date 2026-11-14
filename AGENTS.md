# Codex Repository Instructions

## Purpose

Build the smallest credible version of this new web application while keeping its foundations clear, secure, testable, and easy to evolve.

Project-specific requirements belong in the user's task prompt or approved product specification. This file contains durable rules that apply across repository work.

## Canonical Project Context

- Read `docs/PROJECT.md` for product purpose, users, vision, approved scope, architecture, constraints, and decision rationale.
- Read `docs/STATUS.md` for current stage, milestone, active slice, blockers, and next action.
- Read relevant `docs/work/` records for proposals, approvals, and observed results.
- Reuse equivalent existing locations. Do not duplicate canonical facts across documents.
- Template placeholders are unknowns, never approvals or established facts.

## Commands

Replace placeholders after tooling is approved and configured.

- Install: `[command]`
- Development: `[command]`
- Format or lint: `[command]`
- Type-check: `[command]`
- Unit or integration tests: `[command]`
- Build: `[command]`
- End-to-end tests: `[command or not yet configured]`

Use approved tooling consistently. Do not replace it or add major dependencies without approval.

## Work Modes and Approval

Classify the request before acting:

- Explain, advise, evaluate, review, investigate, or propose: read-only. Do not edit files or implement recommendations.
- Build, implement, fix, update, change, or refactor: prepare a scoped proposal. Implement only after explicit approval of that proposal, unless the user explicitly approves an already defined proposal in the request.
- Questions such as "How would you build this?" or "Do you recommend this feature?" do not authorize implementation.
- If the mode is materially unclear, ask before editing.

Before substantial implementation, obtain approval for the foundational decisions needed by the current scope, including as applicable:

- framework, language, rendering model, package manager, and major dependencies;
- application boundaries, routing, state strategy, backend or API shape, and persistence;
- authentication, authorization, sensitive-data handling, and external services;
- supported browsers, hosting, deployment, and environment strategy.

Do not front-load decisions the current milestone does not need. Once a foundation is approved, implement within it without repeatedly reopening the same decision.

Also obtain approval before migrations, destructive or difficult-to-reverse operations, breaking changes, major architectural revisions, new paid services, production deployment, or behavior beyond the approved MVP.

Before requesting approval, state the proposal, why it is needed now, affected areas, risks and alternatives, and verification or rollback approach.

## Engineering Rules

- Treat the approved MVP, current milestone, and acceptance criteria as the authorized scope.
- Do not invent requirements or add speculative features, integrations, abstractions, infrastructure, or polish.
- Build thin, complete vertical slices that deliver observable user value.
- Prefer simple, well-supported patterns over premature generalization or enterprise-scale architecture.
- Make only supporting changes directly required by the approved outcome; report unrelated opportunities without implementing them.
- If safe completion requires wider scope or a new foundational decision, stop and request approval.
- Once conventions exist, follow them consistently and reuse established components and utilities.
- Keep domain logic separate from presentation and external services where that materially improves clarity or testability.
- Do not weaken tests, validation, accessibility, security, privacy, or error handling.
- Do not edit generated files directly.
- Do not commit, push, deploy, migrate production data, purchase services, or change remote state unless explicitly requested.

## Contextual Inspection

Inspect only what the current task requires.

- At project start, read the approved requirements, designs, constraints, and existing repository configuration.
- For later tasks, inspect the affected implementation plus representative established patterns and consumers.
- For UI work, inspect relevant layouts, components, tokens, and responsive behavior.
- For data or service work, inspect contracts, validation, security boundaries, tests, and failure handling.
- Before editing, check repository status and preserve unrelated user changes.
- Do not infer approved decisions from this template; use the project profile and user direction.

## Development Documentation

Keep documentation proportional, canonical, and useful to future work. Reuse an established documentation structure when present; do not create parallel sources or duplicate facts.

- Maintain `docs/PROJECT.md`, or an approved equivalent, as the durable source for product purpose, users, MVP scope, non-goals, approved architecture, constraints, and unresolved decisions.
- For each normal feature or implementation phase, maintain one living record at the established location or `docs/work/<number>-<short-name>.md`.
- Even tiny implementation changes require a proposal and approval. Their living record may be a short entry in the active work record; do not create a separate document for every small edit.
- Record a durable architectural decision separately, using the repository's ADR convention or `docs/decisions/ADR-<number>-<short-name>.md`, only when future work needs that decision and rationale.

For each implementation slice, with record detail scaled to commitment cost:

1. Perform read-only discovery first.
2. Before changing application code or configuration, create or update the work record with status `Proposed`. Use the proposal depth below; include additional fields only when material. Documentation drafting requested by the user and recording decisions are allowed before implementation approval. Review-only requests remain read-only.
3. Present the proposal and wait for explicit implementation approval. Creating or reviewing documentation does not authorize implementation.
4. After approval, mark the phase `Approved` or `In progress`. Update it only for material decisions, scope changes, deviations, blockers, or findings that future work must know.
5. At completion, record actual changes, observed verification evidence, checks not run, residual risks, and follow-up items. Mark it `Complete` only when acceptance criteria are satisfied.

Do not use documentation as a transcript or scratchpad. Exclude routine command output, step-by-step narration, inconsequential dead ends, duplicated source material, credentials, and secrets. Link to canonical sources rather than copying them.

### Security Documentation

- Every security-related change, including a routine dependency patch, must include a `Security Impact` section in its phase record before implementation.
- Scale the Security Impact section to actual exposure and switching cost. For a routine patch, briefly record affected versions, exposure, compatibility, verification, and rollback. For material vulnerabilities, also record severity rationale, data or user impact, remediation alternatives, migration effects, rollout and monitoring, disclosure status, and residual risk. Mark unknowns explicitly.
- For a material vulnerability, create a dedicated record using the repository's security process or `docs/security/SEC-<year>-<number>-<short-name>.md`; link it from the phase record instead of duplicating it.
- Include trust boundaries, authentication and authorization, data classification, routes and APIs, third-party dependencies, browsers, hosting, and deployment surfaces when relevant.
- Keep exploit details, credentials, personal data, active exposure, and other sensitive material out of public repositories. Store them only in an approved private security system and keep repository documentation sanitized.
- Do not publish or disclose an unpatched vulnerability, claim remediation, deploy, or mark security work complete without explicit authorization and observed verification evidence.

## Product and Web Experience

- Create a small, coherent set of reusable UI primitives and design tokens; avoid building a broad design system before it is needed.
- Keep information architecture, content hierarchy, and interaction behavior consistent.
- Design mobile-first where appropriate and verify relevant viewport sizes and supported browsers.
- Use semantic HTML and provide keyboard access, visible focus, meaningful labels, sufficient contrast, and appropriate motion behavior.
- Implement relevant loading, empty, error, success, and unavailable states.
- Do not substitute invented copy, branding, assets, or product rules for missing requirements.

## Data and Security

- Define explicit data contracts and validate at trust boundaries.
- Apply authentication and authorization server-side where required; do not rely on hidden UI as access control.
- Keep secrets in approved environment or secret-management mechanisms and out of source, client bundles, logs, and examples.
- Minimize collected data and avoid logging sensitive information.
- Handle relevant missing, invalid, duplicate, stale, and failed data safely.
- Make date, time, locale, and timezone behavior explicit where product behavior depends on it.

## Verification and Completion

Use the smallest verification set that credibly covers the change and regression risk:

- Foundation or tooling: verify a clean install, development startup, and production build.
- Page or component: run relevant lint and type checks; verify states, responsive layouts, keyboard use, and accessibility.
- Domain logic: run focused unit tests covering relevant success, edge, and failure cases.
- Data or API: verify validation, authorization, contracts, and focused integration paths.
- Critical MVP flow: once usable, verify one representative end-to-end path; expand only when risk warrants it.
- Deployment or production configuration: verify only after explicit authorization.

Always review the complete diff. Do not run unrelated expensive checks unless project policy or risk warrants them. Explain checks that cannot run and resulting uncertainty. Fix and rerun failures caused by the task; do not absorb unrelated work without approval.

The task is complete only when acceptance criteria are met, approved boundaries are respected, relevant checks pass, no unintended behavior or files were added, and assumptions or risks are reported.

## Final Report

Briefly report what changed, files changed, approved decisions applied, checks and results, checks not run, and remaining assumptions or concerns. Do not present optional follow-up work as completed or authorized.

## Guided Product Development Workflow

Guide the user through the following eight stages. They are coverage areas, not a waterfall or a requirement to produce 24 files. Start small; revisit earlier decisions when evidence changes. Security, verification, and operations apply throughout.

| Stage | Cover when relevant | Typical outputs |
| --- | --- | --- |
| 1. Define the problem | Users, current workflow, pain, alternatives, demand evidence, outcome and how to measure it | Problem statement; user/research findings; success metrics |
| 2. Scope the product | MVP, non-goals, journeys, acceptance criteria, priorities, budget, timeline, dependencies, ownership, reliability and performance expectations | PRD sections; prioritized backlog; milestone/release plan |
| 3. Design the experience | Navigation, task flows, content, screens, responsive behavior, accessibility, loading/empty/error/success states, user feedback | User flows; wireframes/prototype; UI specifications |
| 4. Plan the system | Boundaries, stack, data, APIs, integrations, identity/permissions, privacy and retention, hosting, environments, cost, capacity, risks | Technical design; data/API contracts; significant decision records |
| 5. Build | Complete vertical slices, configuration, migrations, tests, CI/CD, instrumentation | Working software; infrastructure/pipeline configuration; automated checks |
| 6. Validate | Requirements, usability, accessibility, security, permissions, integrations, performance, recovery, user acceptance | Verification evidence; defects; release-readiness assessment |
| 7. Launch | Production setup, rollout/migration, onboarding, support owner, alerts, backups/restore, rollback and incident readiness | Production release; release/onboarding material; operational runbook |
| 8. Operate and improve | Health, cost, product outcomes, feedback, incidents, updates, restore drills, scaling, debt, retirement/data disposal | Dashboards; incident/learning reviews; improvement backlog |

### Start and Resume

1. Read canonical context and inspect only the repository material needed. Check worktree status before edits.
2. Briefly state the current understanding, active milestone/slice, approval state, and next unresolved question. Do not restart discovery already answered.
3. For a new project, ask up to three focused questions at a time, beginning with the problem, user, and desired outcome. Offer recommendations and explain technical choices in plain language.
4. Identify gaps required for the next useful slice. Do not skip necessary discovery, but do not demand decisions for later milestones. An approved experiment may test an unknown first.
5. Draft stage outputs proportionally, usually as sections in PROJECT.md. Ask the user to confirm consequential requirements and decisions; mark drafts and assumptions until confirmed. Clarification answers alone are not implementation approval.
6. Propose one useful slice with acceptance criteria, then wait for approval. Stages may overlap within that slice. Record a deferred or not-applicable area with a short reason and revisit trigger where useful.

### Vision, Milestone, Slice

- Vision: long-term outcomes, plausible future capabilities, enduring constraints, and uncertainties. Future ideas are not authorized features.
- Current milestone: smallest useful outcome to deliver and validate now, with success and acceptance criteria.
- Next slice: a coherent implementable change within that milestone. One approval may cover related edits and necessary tests.
- Evaluate current decisions against known future needs. Prefer the simplest solution with acceptable switching cost. Do not build speculative abstractions or infrastructure merely to preserve hypothetical options.
- For material decisions, record the rationale, realistic reversal effort, and evidence or condition that would justify reconsideration. Do not claim every decision is reversible.
- Define production expectations concretely (users, traffic, data, latency, uptime, budget) when needed. Do not equate production readiness with enterprise architecture.

### Proportional Proposals, Mandatory Approval

Recommend a depth and briefly explain it. Judge by user/data impact, exposure, cost, dependencies, uncertainty, and switching effort—not lines of code. When uncertain, investigate read-only or propose a small experiment.

| Depth | When | Required content |
| --- | --- | --- |
| Short | Localized, low exposure, cheap to undo | Outcome and scope; recommended change and reason; future fit/reversal in one sentence; acceptance and verification. A few sentences can suffice. |
| Standard | Several components or meaningful switching cost | Short contents plus findings, affected interfaces, alternatives, dependencies, risks, deferred work, and reversal effort. |
| Full | Hard-to-reverse commitments, sensitive data, broad security impact, migrations, breaking interfaces, significant recurring cost, production rollout | Standard contents plus impact/exposure, cost, migration/compatibility, rollout/monitoring, recovery limits and rollback, ownership, and unresolved decisions. |

- Present proposals in language the user can understand; define unfamiliar technical terms only as needed.
- Name the proposal/slice and record the user's explicit approval, date, approved revision/scope, and any conditions. Never invent approval or treat silence as approval.
- Do not ask again for routine implementation choices, tests, or fixes needed to satisfy the approved slice. Scope, risk, cost, or foundational changes require an amended proposal and renewed approval before affected work.
- Separate approval to implement from approval to commit, push, deploy, purchase, disclose, or mutate production data. Request those actions explicitly unless already explicitly authorized for that exact scope.
- Approval to an experiment authorizes only that experiment; its findings do not approve the eventual production implementation.

### Just-in-Time Teaching

Before seeking approval for a consequential choice, explain any unfamiliar concept, why it matters here, and the practical tradeoff. Connect it to concepts the user already knows. Invite the user's reasoning when it informs the decision. After verification, explain what worked, what failed, and what the evidence implies for the next slice.

### Evaluation for LLMs, Search, and Discovery

When the product materially depends on an LLM, retrieval, web search, or discovery, agree on a proportional evaluation plan in PROJECT.md before tuning. Define a fair baseline, representative cases, scoring rules, and pass thresholds. Compare under comparable constraints and record material differences. Keep the benchmark and scoring independent of the implementation. Version the benchmark, preserve case-level failures, and require evidence plus explicit approval for ground-truth changes. Rerun both approaches against the same revised version when a change is approved.

For ranked discovery, use verified sources and a small set of known eligible results. Measure known-item recall and precision at a fixed cutoff where useful. Credit newly found items once verified. Treat recall against the known set as a limited measure when the full population is unknown. Measure search, extraction, qualification, and end-to-end quality separately where those steps exist. Save dated results for replay and use fresh live runs to check current performance.

### State, Evidence, and Stop Conditions

- Distinguish proposed, approved, implemented, and verified behavior. Work status: Proposed → Approved → In progress → Complete; use Blocked or Superseded when appropriate.
- Mark Complete only when acceptance criteria and relevant verification are satisfied. An implementation with checks unavailable remains explicitly unverified; never turn an agent's claim into evidence.
- Update documentation after each slice and before handoff. Link commands/results, screenshots, or test artifacts where useful; include checks not run and residual uncertainty.
- Compare plans with observed code and behavior. Flag discrepancies. Record actual behavior without silently redefining approved requirements; propose reconciliation when needed.
- Pause affected implementation for conflicting requirements, unapproved scope or foundations, unexpected material cost/exposure, data-loss risk, or failed verification that cannot be fixed within the approved scope. Report the blocker and a concrete recommendation. Preserve unrelated changes.
- Do not continue dependent slices while their prerequisite is unresolved. Independent work may proceed only within existing approval.

### Cross-Tool Handoff

- Keep the repository documents authoritative once development starts. Do not rely on shared chat memory or assume another tool sees local/unpushed changes.
- Before switching tools, update PROJECT.md, STATUS.md, and the relevant work record. Include current branch/commit if available, uncommitted work, approvals, actual versus planned behavior, evidence, blockers, and next decision.
- Share only the relevant documents/code/diffs through available connections or files. Never include secrets or sensitive logs.
- A receiving agent must read the latest supplied sources, state what repository revision it can inspect, flag missing/stale context, and honor recorded approval boundaries.
- Decisions made outside the repository must be reconciled into canonical documents before dependent implementation resumes. Obtain approval for material changes; avoid copying entire chat transcripts.
