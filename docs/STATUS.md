# Project Status

- Last updated: 2026-11-14
- Repository branch / commit / uncommitted changes: `main`; Slice 2 close-out commit authorized locally; Slice 3 implementation remains uncommitted; no push authorized
- Current milestone: Prove one fresh end-to-end run can fill a founder-first 10-slot digest: founders first up to 7, organizers fill remaining slots with at least 2 reserved by default; never pad. Target >=60% Useful when 10 verified leads are reviewed.
- Active implementation scope: Slice 3 — Opportunity Discovery (005), approved with A1 offline replay gate and US$1.25/run, US$4/slice caps
- Next work record: 005 — Opportunity Discovery
- Next action: Complete Slice 2 local commit, then implement Slice 3 tests and offline A1 replay before any new paid call

## Stage Coverage

| Stage | Status | Output / evidence / revisit trigger |
| --- | --- | --- |
| 1. Define the problem | Covered for current milestone | User, manual workflow, demand evidence, cost constraint, and success metrics recorded in `PROJECT.md` |
| 2. Scope the product | Covered for current milestone | Narrow founder/organizer segment, founder-first 10-slot assembly, geography/date rules, non-goals, no-padding rule recorded |
| 3. Design the experience | Covered for current milestone | Fresh digest flow, result fields, CSV, Useful/Not useful review, shortfall/failure states recorded |
| 4. Plan the system | Covered for current milestone | Pipeline boundaries, Python/FastAPI/Pydantic, provider benchmark, TinyFetch/Firecrawl hierarchy, hybrid deterministic+LLM strategy, evaluation plan recorded |
| 5. Build | Slice 2 benchmark tooling built | Three minimal search adapters and offline scorer; no application discovery behavior yet |
| 6. Validate | Slice 2 preliminary scoring done | 174 successful API requests and exact cited-page scoring; manual URL judgments and end-to-end validation remain |
| 7. Launch | Deferred | Trigger: successful end-to-end validation and explicit pilot launch proposal |
| 8. Operate and improve | Deferred | Trigger: pilot launch / repeated-run operation |

## Current Reality

### Approved product/system direction
- Initial user: Montréal public-speaking coach.
- Validation segment: newer founders preparing for upcoming pitches/public presentations plus organizers serving newer founders.
- First milestone: one fresh end-to-end run before weekly repeatability.
- Target: 10 slots, founders first up to 7; organizers fill remaining slots with at least 2 reserved by default (configurable). Never pad; log split and shortfall reason.
- Pending-lineup events go on a run watch list with expected-announce/recheck dates; an organizer may qualify now, while founders need official same-edition names. Weekly runs log pending count; revisit the founder channel if founders stay below about 2 for 3–4 consecutive weeks. Automated scheduling remains deferred.
- Student class/capstone teams count as founders only with official evidence that they pitch a venture.
- Coach-quality target: >=60% Useful among reviewed verified leads when 10 verified leads are available.
- Canada first; U.S. fallback; tech and non-tech sectors allowed.
- Opportunity window: +7 days through +6 months.
- Same-event-edition evidence integrity required.
- No padding weak leads.
- Core pipeline: Request → Discovery → Evidence Retrieval → Extraction → Qualification → Ranking → Presentation → Review.
- Backend: Python + FastAPI + Pydantic.
- D16 approved: Exa primary, Serper fallback; Brave dropped.
- TinyFetch intended default retrieval; Firecrawl advanced fallback.
- Deterministic rules for strict qualification; LLM only where semantic interpretation adds value.

### Implemented
Slice 1 artifacts are present under `docs/benchmark/v1/`: frozen JSON benchmark v1, case-format documentation, and a Pydantic validator. The approved expansion in `docs/work/003-benchmark-v2.md` added frozen v2 (14 eligible editions, 12 Canadian), its guide, and v2 validator checks while preserving v1. Slice 2 added minimal provider adapters, a saved 58-query-per-provider run, and an offline scorer. No application discovery behavior has been implemented.

### Verified
The frozen comparison completed 58 successful requests per provider and 174 total with no retries. After first-pass same-site judging, v2 union recall@10 is Exa 9/14, Brave 6/14, Serper 6/14; live CA is 6/7, 3/7, 4/7. Three focused tests passed. No application behavior or fresh end-to-end lead run has been verified.

### Checks not run / uncertainty
- Benchmark v1 and v2 are frozen at `docs/benchmark/v1/benchmark.json` and `docs/benchmark/v2/benchmark.json`.
- Provider comparison and first-pass judging are saved in `artifacts/search-provider/20261114T131952Z/`; the full pooled URL precision and new discoveries remain unjudged. Slice 2's full acceptance remains open even though D16 is approved.
- API key presence, current published pricing, and request parameter names were checked; actual Brave/Serper billed cash cost and account credit balances were not available from search responses.
- No frontend framework, database, LLM/model, hosting, auth, or deployment choice approved.
- No live end-to-end run completed under the restarted scope.
- The Pydantic validator ran successfully on frozen v1 and v2 according to work records 001 and 003. V1's founder cases all come from one U.S. edition. V2 has no live Canadian founder positives; its Canadian founder positives are replay cases. Report split-specific results and keep both limits visible.

### Main blocker / risk
Top-of-funnel discovery quality remains the largest technical uncertainty. V2 has no live Canadian founder positives; weekly held-out sets will test that path. Brave's published result-retention terms remain a limit on the local Slice 2 artifacts.

### Next slice
`005 — Opportunity Discovery` — approved for local implementation, beginning with tests and A1 offline replay. Slice 2's remaining pooled judging is a separate open follow-up.

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
