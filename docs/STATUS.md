# Project Status

- Last updated: 2026-11-14
- Repository branch / commit / uncommitted changes: `main`; Slice 3 source and docs committed locally after review, not pushed. Run artifacts, including A5/A7 audits and Raj's precision labels, remain gitignored under `artifacts/`.
- Current milestone: Prove one fresh end-to-end run can fill a founder-first 10-slot digest: founders first up to 7, organizers fill remaining slots with at least 2 reserved by default; never pad. Target >=60% Useful when 10 verified leads are reviewed.
- Active implementation scope: Slice 3 — Opportunity Discovery (005), **Complete (A10 pending)** on the first held-out weekly set, around early December. Raj approved closure on 2026-11-14 and accepted precision 16/25, because discovery's job is to find candidates and later stages filter them. A1a, A2a, A2b, A3, A4, A5, A6, A7, A8 and A9 pass on saved responses.
- Next work record: Slice 4 — Evidence Retrieval proposal
- Next action: Write the Slice 4 (Evidence Retrieval) proposal. Carry forward: (a) calendars and listing pages stay as candidates, flagged as a list of events, and Slice 4 opens them to pull out each event; (b) non-events and press releases never take a weekly slot — Slice 6 drops them, or sends them to the watch list if they name an organizer; (c) programs and accelerators count only through a dated demo day or pitch event, otherwise they go on the watch list. Also fix same-site organiser-name over-merges early in Slice 4, add `twitter.com` to the social-site list, and drop implausible years taken from statistics. A10 remains around early December. No further paid run is implied.

## Stage Coverage

| Stage | Status | Output / evidence / revisit trigger |
| --- | --- | --- |
| 1. Define the problem | Covered for current milestone | User, manual workflow, demand evidence, cost constraint, and success metrics recorded in `PROJECT.md` |
| 2. Scope the product | Covered for current milestone | Narrow founder/organizer segment, founder-first 10-slot assembly, geography/date rules, non-goals, no-padding rule recorded |
| 3. Design the experience | Covered for current milestone | Fresh digest flow, result fields, CSV, Useful/Not useful review, shortfall/failure states recorded |
| 4. Plan the system | Covered for current milestone | Pipeline boundaries, Python/FastAPI/Pydantic, provider benchmark, TinyFetch/Firecrawl hierarchy, hybrid deterministic+LLM strategy, evaluation plan recorded |
| 5. Build | Slice 3 discovery committed locally; Slice 4 not started | Query generation, Exa/Serper adapters, normalization, date windows, dedupe, watch list, scorer and precision sample in `src/leadgen/discovery/` and `scripts/` |
| 6. Validate | Slice 3 complete pending A10 | One bounded live discovery run (US$0.910) plus US$0 reprocessing; official A5, A7, and Raj's accepted 16/25 precision review are recorded in 005. A10 held-out set and end-to-end validation remain |
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
Slice 1 artifacts are present under `docs/benchmark/v1/`: frozen JSON benchmark v1, case-format documentation, and a Pydantic validator. The approved expansion in `docs/work/003-benchmark-v2.md` added frozen v2 (14 eligible editions, 12 Canadian), its guide, and v2 validator checks while preserving v1. Slice 2 added minimal provider adapters, a saved 58-query-per-provider run, and an offline scorer. Slice 3 discovery is committed locally: bounded query families, Exa primary and Serper fallback adapters, normalization, EN/FR date windows with event-date role selection, URL, same-site and cross-site dedupe, a watch list, a scorer and a seeded precision sample. One bounded live discovery run has been made; no end-to-end lead run has.

### Verified
The frozen comparison completed 58 successful requests per provider and 174 total with no retries. After first-pass same-site judging, v2 union recall@10 is Exa 9/14, Brave 6/14, Serper 6/14; live CA is 6/7, 3/7, 4/7. Three focused tests passed. No application behavior or fresh end-to-end lead run has been verified.

Raj approved A1a candidate retention as the live-spend gate and A1b exact city/year as a report-only metric. An earlier amended replay failed because Arena URLs split across conflicting Serper snippets; that failure and its repair are recorded in 005.

The approved canonical-URL repair brought A1a union and true Exa-only replay to 9/14 overall and 6/7 live Canada, with A9 byte-for-byte repeatability. Official pricing and a US$0.007 Exa highlights probe passed D3-1. One live evaluation used 130 Exa requests and reported US$0.910 cost; Serper fallback did not fire. Fresh candidate recall was 6/14 overall and 5/7 live CA (A2 fail); Arena remained `unknown` for A3, and Startup TNT had two records for A6. A4 and measured parts of A7/A8 passed; A5 needs full adjudication and A10 awaits a held-out set. See 005 Results for case-level diagnostics and the interrupted sandbox attempt.

Raj approved on 2026-11-14 a restated A2 (A2a: live Canadian editions returned by search ≥ 6/7; A2b: kept with no wrong city/year ≥ 6/7) and four generic date/dedupe fixes. Reprocessing the saved responses for US$0 on the Mac gave these results:
- A1a is unchanged: 9/14 overall and 6/7 live Canada, union and Exa-only.
- A2a and A2b are each 6/7.
- A3: 6 of 6 surfaced editions are in window. UBC is restored, and Arena resolves to 2027.
- A4: no date trap is in window.
- A6: one record per surfaced edition.
- A7: no program page is in window, and all 98 social records are flagged.
- A9: outputs are byte-identical on repeat.

Raj judged the 25-row precision sample (report only): 16/25 real in-window events, 6/13 among Canada-located records, agreeing with the advisory labels on 16/25. On 2026-11-14 he accepted 16/25 and closed Slice 3 pending A10, because discovery's job is to find candidates and later stages filter them. Official A5 passes (0 v2-related records merge different years or cities). A7 passes (no program pages emitted as candidates; all social and Meetup sources flagged and retained; no event pages fetched). A broader city/year audit found 7 same-site over-merges of different events and one implausible `2000` year parse; those do not fail the official A5 gate and are carried into Slice 4, along with adding `twitter.com` to the social-site list. 44 tests pass. The fixes were motivated by v2 traces, so the held-out trend must confirm them. No API calls were made in the close-out.

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
Slice 3 (`005 — Opportunity Discovery`) is **Complete (A10 pending)** and committed locally. Next: the Slice 4 (Evidence Retrieval) proposal, carrying forward calendar expansion, non-event/press-release filtering in Slice 6, program-via-demo-day rules, the same-site over-merge fix, `twitter.com` on the social-site list, and dropping implausible years taken from statistics. A10 remains: score the first frozen held-out weekly set once, about early December. Slice 2's remaining pooled judging is a separate open follow-up.

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
