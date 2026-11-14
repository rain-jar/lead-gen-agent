# Project Status

- Last updated: 2026-11-14
- Repository branch / commit / uncommitted changes: To be inspected by Codex in the target repository
- Current milestone: Prove one fresh end-to-end lead-discovery run can produce up to 7 verified founders + 3 verified organizers with >=60% Useful among reviewed verified leads when 10 are available
- Active implementation scope: None; Slice 1 and the separately approved benchmark v2 expansion (003) are complete
- Next work record: Slice 2 — Search Provider Benchmark (002; query design frozen, provider implementation/run pending approval)
- Next action: Review provider readiness and authorize the Slice 2 implementation/run under the frozen 58-query set and US$5 cap

## Stage Coverage

| Stage | Status | Output / evidence / revisit trigger |
| --- | --- | --- |
| 1. Define the problem | Covered for current milestone | User, manual workflow, demand evidence, cost constraint, and success metrics recorded in `PROJECT.md` |
| 2. Scope the product | Covered for current milestone | Narrow founder/organizer validation segment, 7/3 target, geography/date rules, non-goals, no-padding rule, architecture intent recorded |
| 3. Design the experience | Covered for current milestone | Fresh digest flow, result fields, CSV, Useful/Not useful review, shortfall/failure states recorded |
| 4. Plan the system | Covered for current milestone | Pipeline boundaries, Python/FastAPI/Pydantic, provider benchmark, TinyFetch/Firecrawl hierarchy, hybrid deterministic+LLM strategy, evaluation plan recorded |
| 5. Build | Not started | No implementation slice approved yet |
| 6. Validate | Deferred until build slices produce testable behavior | Benchmark/evaluation design begins in Slice 1; end-to-end validation is Slice 10 |
| 7. Launch | Deferred | Trigger: successful end-to-end validation and explicit pilot launch proposal |
| 8. Operate and improve | Deferred | Trigger: pilot launch / repeated-run operation |

## Current Reality

### Approved product/system direction
- Initial user: Montréal public-speaking coach.
- Validation segment: newer founders preparing for upcoming pitches/public presentations plus organizers serving newer founders.
- First milestone: one fresh end-to-end run before weekly repeatability.
- Target: 7 Verified founders + 3 Verified organizers when available.
- Coach-quality target: >=60% Useful among reviewed verified leads when 10 verified leads are available.
- Canada first; U.S. fallback; tech and non-tech sectors allowed.
- Opportunity window: +7 days through +6 months.
- Same-event-edition evidence integrity required.
- No padding weak leads.
- Core pipeline: Request → Discovery → Evidence Retrieval → Extraction → Qualification → Ranking → Presentation → Review.
- Backend: Python + FastAPI + Pydantic.
- Search provider final choice unresolved; Exa/Brave/Serper must be benchmarked fairly.
- TinyFetch intended default retrieval; Firecrawl advanced fallback.
- Deterministic rules for strict qualification; LLM only where semantic interpretation adds value.

### Implemented
Slice 1 artifacts are present under `docs/benchmark/v1/`: frozen JSON benchmark v1, case-format documentation, and a Pydantic validator. The approved expansion in `docs/work/003-benchmark-v2.md` added frozen v2 (14 eligible editions, 12 Canadian), its guide, and v2 validator checks while preserving v1. V2 separates live and replay cases and documents weekly held-out evaluation. This is benchmark tooling/data only; no application discovery behavior has been implemented. No previous experimental code is present in this workspace.

### Verified
Product decisions above were approved in planning conversation. No new application behavior has been verified under this restart.

### Checks not run / uncertainty
- Benchmark v1 and v2 are frozen at `docs/benchmark/v1/benchmark.json` and `docs/benchmark/v2/benchmark.json`.
- No provider benchmark run.
- No current API credentials/limits verified in the target repository.
- No frontend framework, database, LLM/model, hosting, auth, or deployment choice approved.
- No live end-to-end run completed under the restarted scope.
- The Pydantic validator ran successfully on frozen v1 and v2 according to work records 001 and 003. V1's founder cases all come from one U.S. edition. V2 has no live Canadian founder positives; its Canadian founder positives are replay cases. Report split-specific results and keep both limits visible.

### Main blocker / risk
Top-of-funnel discovery quality remains the largest technical uncertainty.

### Next slice
`002 — Search Provider Benchmark` — 58-query design frozen on 2026-11-14; provider implementation/run not yet approved.

## Planned Implementation Slices

1. Benchmark Setup
2. Search Provider Benchmark
3. Opportunity Discovery
4. Evidence Retrieval
5. Structured Extraction
6. Qualification
7. Ranking and Digest Assembly
8. User-Facing Results
9. Review State
10. End-to-End Validation
11. Pilot Hardening

Each slice requires its own proposal and explicit approval. The roadmap is not blanket authorization.

## Handoff

A receiving agent must:
1. read `AGENTS.md`, `docs/PROJECT.md`, this file, and the active work record;
2. inspect branch/commit/worktree status before edits;
3. reconcile any pre-existing repository behavior against the approved restart definition rather than silently adopting it;
4. preserve unrelated user changes;
5. do not implement any slice until its proposal is explicitly approved;
6. update this file and the relevant work record after each approved slice with actual observed evidence, not claims.
