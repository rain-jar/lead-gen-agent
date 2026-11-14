# FDE Lead Generation MVP — Codex Project Package

This repository package is the canonical starting point for the restarted Lead Generation MVP.

## Start here

1. Read `AGENTS.md` for durable repository workflow, approval, documentation, security, verification, and handoff rules.
2. Read `docs/PROJECT.md` for the approved product definition, MVP scope, architecture, evaluation plan, implementation roadmap, decisions, and unresolved questions.
3. Read `docs/STATUS.md` for the current milestone, stage coverage, approval state, and next action.
4. Read the active record in `docs/work/` before implementing anything.

## Current position

- Stages 1–4 are covered for the current milestone.
- Stage 5 has started with benchmark tooling; application discovery behavior is not built yet.
- Benchmark setup (001) and the approved v2 coverage expansion (003) are complete. Both benchmark versions are frozen.
- Slice 2's 58-query provider run and first-pass URL judging are done. Raj approved Exa primary, Serper fallback, and dropped Brave; full pooled precision judging remains open.
- The founder-first, organizer-fill 10-slot mix is defined in `docs/PROJECT.md` and work record 004. Slice 3 is complete pending its first held-out weekly test (A10); see work record 005 for results and carry-forward issues.

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
- `docs/work/002-search-provider-benchmark.md` — active Slice 2 record and result summary
