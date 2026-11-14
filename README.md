# FDE Lead Generation MVP — Codex Project Package

This repository package is the canonical starting point for the restarted Lead Generation MVP.

## Start here

1. Read `AGENTS.md` for durable repository workflow, approval, documentation, security, verification, and handoff rules.
2. Read `docs/PROJECT.md` for the approved product definition, MVP scope, architecture, evaluation plan, implementation roadmap, decisions, and unresolved questions.
3. Read `docs/STATUS.md` for the current milestone, stage coverage, approval state, and next action.
4. Read the active record in `docs/work/` before implementing anything.

## Current position

- Stages 1–4 are covered for the current milestone.
- Stage 5 has not started implementation.
- No application code is authorized by this package alone.
- Benchmark setup (001) and the approved v2 coverage expansion (003) are complete. Both benchmark versions are frozen.
- The next slice is `002 — Search Provider Benchmark`; its 58-query design is frozen, and provider implementation/run is pending approval.
- Codex must obtain explicit approval of the Slice 2 proposal before changing application code/configuration or running providers.

## Operating cycle

Read context → inspect repository → propose scoped slice → explicit approval → implement → verify → record evidence → update canonical docs → next proposal.

## Important project principle

The MVP test is deliberately narrow: a Montréal public-speaking coach seeking newer founders preparing for public pitches and organizers of relevant pitch opportunities. The underlying pipeline should remain reasonably reusable through clean boundaries and configurable qualification/discovery profiles, without prematurely building a generic lead-generation platform.

## Canonical files

- `AGENTS.md` — durable repository instructions
- `docs/PROJECT.md` — product/system source of truth
- `docs/STATUS.md` — current execution state
- `docs/WORK_TEMPLATE.md` — work-record template
- `docs/work/001-benchmark-setup.md` — completed v1 setup
- `docs/work/003-benchmark-v2.md` — completed v2 expansion
- `docs/work/002-search-provider-benchmark.md` — canonical next slice; query design frozen
