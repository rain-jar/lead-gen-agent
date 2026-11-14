# 005 — Opportunity Discovery (Slice 3)

- Status: **Approved — 2026-11-14 by Raj** (America/Toronto), with the decisions in "Decisions (approved 2026-11-14)" below. Implementation is authorized within this scope and the spend caps. Commit, push, deploy, and purchases are **not** authorized.
- Proposal depth and reason: Standard. This is the first product-pipeline code. It sets the opportunity record contract that Slices 4–7 consume, and it makes recurring paid search calls. It handles no private data and deploys nothing.
- Source requirements / milestone: `docs/PROJECT.md` §2 (geography, date window, edition integrity), §4 (discovery strategy, provider abstraction, opportunity model), §6 (evaluation), §7 Slice 3; `docs/STATUS.md`; work records 002 (+ Amendment A), 003 (benchmark v2), and 004 (lead mix, L2 watch list, L4 evidence findings); Slice 2 run `artifacts/search-provider/20261114T131952Z/` (`report.md`, `judgments/recall_after_first_pass.md`, `founder_reachability_spike.md`, `founder_reachability_replay.md`).
- Decisions this record relies on (Raj, 2026-11-14): Exa primary, Serper fallback, Brave dropped (D16, to be recorded in canonical docs by Codex); amendment 004 lead mix; student capstone teams are not founders unless pitching a venture.

## Proposal

### Outcome
One command runs fresh, bounded discovery with no seed list. It returns a deduplicated set of **candidate opportunity editions** (event + specific edition) with window status, lineup status, provenance, and a **watch list** of editions to recheck. Every record traces back to the query, provider, and URL that found it. Saved raw responses can be reprocessed offline with no new API calls.

Slice 3 finds and normalizes *events*. It does not fetch pages, name people, or verify contacts. Those are Slices 4–5.

### Scope
1. A `SearchProvider` boundary (PROJECT.md §4) with Exa and Serper adapters, ported from `scripts/search_provider_benchmark.py` (same request shapes, CA certificate handling, key redaction, per-attempt cost reservation). Brave is not ported.
2. Deterministic query-family generation from a checked-in config, with Canada first and a separate US phase.
3. Deterministic normalization: URL canonicalization, page-kind classification, edition key, date and window parsing, and lineup hints from title, URL, and snippet only.
4. Edition dedupe/merge, and watch-list derivation.
5. Run outputs written to a dated run folder: `run.json` (settings, query file hash, counts, cost, latency, fallback firings), `raw.ndjson`, `candidates.jsonl`, `watchlist.jsonl`, and `excluded.jsonl` (with reasons).
6. An offline scorer, kept separate from discovery code, that scores candidates against frozen v2 and later held-out sets.
7. Focused tests.

### Non-goals
- No page fetching, TinyFetch/Firecrawl, or crawling (Slice 4). No extraction of people, ventures, or contacts (Slice 5). No Verified/Provisional/Rejected states (Slice 6). No ranking or digest mix (Slice 7). No UI, FastAPI routes, database, scheduler, or LLM.
- No changes to frozen v1/v2, the frozen Slice 2 query file, or `PROJECT.md`/`STATUS.md` (canonical updates follow approval and completion).
- Discovery code never reads benchmark files and never contains a benchmark event, organizer, person, domain, or URL.

### Recommended approach and why
- **Plain Python package plus CLI** (for example `src/leadgen/discovery/` and `python -m leadgen.discovery run`) with Pydantic models. The project already uses Pydantic, and this keeps domain logic separate from the provider adapters (AGENTS.md). FastAPI waits until a UI slice needs it.
- **Deterministic rules only.** Window, edition, and dedupe are strict rules (PROJECT.md §4, D18). The exact model is unresolved (D19), so no LLM is used here.
- **Union across query families, not single-query precision.** In Slice 2, Exa's per-query hit fraction was 2.7% overall, but its union recall was 9/14. Coverage comes from breadth across families and geographies.

## Record contracts

### `CandidateEdition` (one per deduped edition)

| Field | Type / values | Notes |
| --- | --- | --- |
| `dedupe_key` | str | `slug(event_name) + "|" + city_slug + "|" + edition_token`; see the dedupe rules |
| `event_name` | str | Title with the site suffix stripped; original titles kept in `sources` |
| `series_key` | str | Same key without `edition_token`; links editions of one series |
| `edition_token` / `edition_year` | str / int or null | Year, or year+season/month when needed; null if unresolved |
| `edition_conflict` | bool | True when sources show more than one year (for example a 2027 header over 2026 content) |
| `event_date`, `event_end_date` | date or null | Only when an explicit date is parsed |
| `date_text` | str or null | Raw date phrase ("Spring 2027", "février 2027") when not exact |
| `date_confidence` | `explicit` / `inferred_year` / `season_or_month` / `none` | |
| `city`, `region`, `country` | str or null | `country` ∈ {CA, US, other, null} |
| `geo_tier` | `canada` / `us_fallback` / `other` | Phase that produced it |
| `page_kind` | `event_edition` / `event_series` / `program` / `listing_or_aggregator` / `news` / `social` / `other` | Primary source's kind |
| `window_status` | `in_window` / `pending_date` / `too_soon` / `past` / `too_far` / `unknown` | Relative to `reference_date` |
| `lineup_status` | `unknown` / `pending` / `announced` | From the snippet or title only; `announced` is a hint, not verification |
| `expected_announce_date` | date or null | Only if a snippet states it ("finalists announced Dec 1") |
| `recheck_date` | date or null | See the watch-list rules |
| `discovery_confidence` | `high` / `medium` / `low` | Rule-based, defined below |
| `needs_alternate_source` | bool | Login-walled, bot-blocked, or social primary source |
| `sources[]` | list | `{url, canonical_url, title, snippet, provider, query_id, query_family, rank, retrieved_at, is_official_guess, access_hint}` |
| `providers`, `query_families` | sets | For per-family contribution reporting |
| `reference_date`, `run_id` | date, str | `reference_date` is the run date in America/Toronto unless overridden for evaluation |

### `WatchItem`
`dedupe_key`, `reason` (`lineup_pending` / `date_pending` / `enters_window_later` / `alternate_source_needed`), `expected_announce_date`, `recheck_date`, `last_seen_run_id`, and primary source URLs. Per 004 L2, the watch list is a **run output only**. Cross-run merging and scheduling stay deferred (D23).

### Excluded records
Records from `excluded.jsonl` carry the same fields plus `exclude_reason`: `past`, `too_soon`, `program_without_dated_event`, `non_event`, `duplicate_of:<key>`, or `out_of_geography`. They are kept for audit and scoring, never silently dropped.

## Query strategy

Config-driven and checked in. The generated query list is saved and hashed per run. Families use only category, geography, and date terms (v2 leakage rule).

**Time phrase (rolling):** derived from the window. It contains the years spanned by `[reference_date + 7 days, reference_date + 6 months]`: EN `upcoming <y1> <y2>`, FR `à venir <y1> <y2>`. This replaces the hard-coded `upcoming 2026 2027`.

**Canada phase (runs first): 97 queries** (48 + 24 + 25), plus up to 15 second-hop queries.

| Family | Terms | Scopes | Queries |
| --- | --- | --- | ---: |
| EN core (Slice 2, kept) | `startup pitch competition finalists`; `startup accelerator demo day founders`; `university entrepreneurship pitch showcase`; `entrepreneurship competition finalists` | 12 Canadian scopes from Slice 2 | 48 |
| EN early-announcement (new) | `call for applications startup pitch competition`; `demo day founders pitch night` | same 12 | 24 |
| FR (expanded) | `concours de pitch startup`; `demo day entrepreneurs`; `concours entrepreneuriat finalistes`; `finale concours de pitch étudiant`; `appel de candidatures concours startup` | `Montréal`, `Ville de Québec`, `Québec` (province), `Sherbrooke`, `Gatineau` | 25 |
| Second hop (new, capped) | `<discovered series/program name> demo day OR pitch finale <years>` | Generated only from discovered `program`/`event_series` pages with no dated edition | ≤15 |

Why: the early-announcement family targets apply and call pages (UBC was found through its apply-to-pitch PDF). In Slice 2 the FR family was weak: the three French intents averaged 0.5, 0, and 0 editions per query on Exa and 0 on Serper, and UdeM Demoday was missed by every provider. Second-hop queries turn program pages into their dated demo days (004 L4) without fetching pages.

**US phase (fallback tier):** the `United States` scope × 6 EN intents (6 queries), plus the 10 largest US metropolitan areas (fixed list in config, chosen by a published population ranking before any held-out scoring) × the two Slice 2 intents with the highest per-query yield (`startup pitch competition finalists`, `university entrepreneurship pitch showcase`) = 20 queries. Total 26. Reason: US recall was 0/2 for every provider with one national scope. Results are tagged `geo_tier=us_fallback` and always sort after Canada.

**US trigger:** Slice 3 cannot see verified-lead shortfalls, because those come from Slices 6–7. So the US phase is a separate callable phase. In Slice 3 evaluation runs it always runs (so US recall can be measured). In normal product runs it fires **only on request** (`--us`) (decision D3-2). Slice 7 wires the trigger based on the digest shortfall. The end-to-end trigger based on the digest shortfall is wired in Slice 7.

**Exa primary, Serper fallback: when the fallback fires.** It fires per query and is logged with its reason:
- **F1 provider failure:** Exa errors or times out after one retry → the same query goes to Serper (`gl`/`hl` as in Slice 2).
- **F2 empty yield:** Exa returns no result that survives normalization as an event-like page (`event_edition`, `event_series`, or `listing_or_aggregator`) → the same query goes to Serper.
- No other triggers. Serper calls are capped at the Exa query count per run.

Honest expectation: on v2, Serper found no eligible edition that Exa missed (Exa ∪ Serper union = Exa's 9/14 after first-pass judging). The fallback is resilience and cheap breadth ($0.001/query list price), not a proven recall gain.

**Request settings:** Exa `/search` with `numResults: 10` and `userLocation` (CA/US), as in Slice 2. Slice 2 Exa responses returned **only id, title, URL — no snippet or date**, so Exa-only results can be classified from title and URL alone. Exa snippets are handled by decision D3-1: a cost check comes first, and snippets are enabled only if they pass it. No date filters or domain restrictions by default.

## Normalization, page kind, dedupe

**URL canonicalization:** the Slice 2 rule (scheme, host case, trailing slash), plus dropping `www.`, `utm_*`, `fbclid`, `gclid`, and fragments. Known alias redirects are not followed in Slice 3 (no fetching). Same-site aliases are merged by the dedupe key instead.

**Page kind (rules on URL path, title, snippet):**
- `program`: accelerator, incubator, or cohort language with no dated pitch event.
- `event_series`: evergreen event page with no year.
- `event_edition`: named event plus a year or date.
- `listing_or_aggregator`: Luma, Eventbrite, Meetup, arclight-style mirrors, calendars.
- `social`: Facebook, LinkedIn, Instagram, X.

Program and series pages never become `in_window` candidates by themselves. They are seeds for second-hop queries and `related_sources` on a matching edition (004 L4: incubators are not direct sources).

**Edition key and merge rules:**
1. City is part of the key: same organizer, different city = different edition (Slice 2 traps: NEXT AI Toronto vs Montréal on Luma; Startup TNT Edmonton vs Calgary).
2. Year/edition is part of the key. If sources for one series disagree on year, keep separate editions. If one source shows two years (Arena 2026 names with 2027 dates; Startupfest 2026 pages with a 2027 header), set `edition_conflict=true`, `edition_year=null`, `discovery_confidence=low`. Never pick one.
3. Merge sources into one edition when the normalized name tokens match (token-set similarity ≥ a configurable threshold), with the same city and same edition token. The official domain is preferred as the primary source over listings and mirrors.
4. A URL year older than the window's prior year (for example a 2023 session URL) → `past`.
5. Deterministic, order-independent: the same inputs always give the same keys and merges.

**Blocked, social, and login-walled starts (SPIE/Incapsula-type, Facebook, Meetup, LinkedIn):** never dropped at discovery. Mark `needs_alternate_source=true` and `access_hint` by domain class, and add a watch item with reason `alternate_source_needed`. Slice 4 looks for an official alternative.

## Date-window rules
- `reference_date` = run date in America/Toronto. Window = `[ref + 7 days, ref + 6 calendar months]` (D08). Evaluation may override `reference_date` (live v2 = 2026-11-14; replay = R3 announcement date).
- Parse EN and FR dates (`December 2, 2026`, `2 décembre 2026`, ISO, `Dec 2–4`). A day/month with no year is assigned a year only if exactly one candidate year falls within ref−1 month to ref+12 months (`date_confidence=inferred_year`). Otherwise `none`.
- Multi-day events: both ends must be in the window (v2 README).
- `in_window`: explicit date inside the window. `too_soon` / `past` / `too_far`: explicit date outside it. `pending_date`: only a month, season, or year that overlaps the window. `unknown`: no date signal.
- Only explicit-date `too_soon`/`past` records go to `excluded.jsonl`. `too_far` explicit dates go to the watch list with `recheck_date = event_date − 6 months` (the day they enter the window). `pending_date` and `unknown` go downstream to Slice 4.
- Past editions of a series are kept in `excluded.jsonl` as `series_history`. They are never candidates, and their names are never carried forward (D10).

## Lineup status, watch list, confidence
- `lineup_status=announced` when the title or snippet signals a same-year finalists/winners/lineup page (`finalists`, `meet the teams`, `finalistes`, `lauréats`) and the year matches the edition. `pending` when it signals applications or deadlines. Otherwise `unknown`. This is a hint for Slice 4, never verification; titles like "Meet the Founders" were company-only in the replay spike.
- `recheck_date` = `expected_announce_date + 1 day` if stated; otherwise `reference_date + 7 days` for `lineup_pending`/`date_pending`/`alternate_source_needed`.
- `discovery_confidence`:
  - `high`: `event_edition` on an official-looking domain, explicit in-window date, no conflict.
  - `medium`: edition with a `pending_date`, or a listing/social source with an explicit date.
  - `low`: everything else, including any `edition_conflict`.

## Cost and rate budget (targets; re-verify prices before the first call)
- List prices from Slice 2: Exa $0.007/request (Exa-reported), Serper $0.001/query.
- Maximum per run without snippets: Canada 97 + second hop 15 + US 26 = 138 Exa ≈ **$0.97**, plus at most 138 Serper ≈ $0.14, for a worst case of about $1.10. A typical normal run (Canada only, no US phase) is 97–112 Exa queries ≈ $0.68–0.78.
- **Hard caps (approved 2026-11-14):** US$1.25 per run and US$4 total for Slice 3 development and evaluation runs. These are ceilings, not expected spend. They are enforced on reserved list price per attempt, including retries. Stop at the cap and report partial results. No purchases or plan upgrades.
- If Exa snippets are enabled (D3-1), include their per-request price in the reservation. If an evaluation run (US phase on) would then exceed US$1.25, the cap governs. Report it, and run snippets for the Canada phase only rather than raising the cap.
- Rate: sequential calls, one retry for transient errors, record latency per call. In Slice 2, Exa's median latency was 0.514 s and the 58 calls took 35 s in total.

## Acceptance criteria (targets, measured against frozen v2 and recorded per run)

Small-n caveat: 14 eligible editions, so one edition = 7.1 points overall, 12.5 live, and about 14.3 live-Canada. v2 is **not held out** for this slice, because the Slice 2 misses shaped this design. v2 numbers are regression checks, and held-out sets are the real test.

| ID | Criterion | Target |
| --- | --- | --- |
| A1 | **Gate before any live spend.** Offline dry run on Slice 2's saved Exa + Serper responses (no spend; Brave excluded): v2 eligible editions present as a correctly keyed candidate | ≥ 9/14 overall, ≥ 6/7 live-CA (= Slice 2 Exa after first pass; normalization must not lose what search found) |
| A2 | Fresh live run (Canada + US phases): candidate-level union edition recall on v2 | ≥ 9/14 overall and ≥ 6/7 live-CA (no regression). Reported, not gating: UdeM Demoday, and US editions (were 0/2) |
| A3 | Window classification with `reference_date=2026-11-14`: surfaced v2 live eligible editions | 100% `in_window` or `pending_date`, 0 excluded |
| A4 | Surfaced v2 date traps (McMaster live view 2026-11-18, Startupfest 2027-07-07, Velocity 2026-09-12) | 0 marked `in_window` |
| A5 | Edition integrity on adjudicated v2-related records (Arena 2026/2027, NEXT AI Toronto/Montréal, Startup TNT Edmonton/Calgary) | 0 records merging different years or cities |
| A6 | Dedupe | Each surfaced v2 edition → exactly 1 candidate record (mirrors such as arclight merge into the official record) |
| A7 | Program pages and blocked starts | 0 `program` pages emitted as `in_window` without a dated event; every social/blocked source retained with `needs_alternate_source` |
| A8 | Cost, logging, security | Within the caps; query count, fallback firings, latency, and cost in `run.json`; 0 key values in artifacts or logs |
| A9 | Determinism | Reprocessing a run's `raw.ndjson` reproduces identical `candidates.jsonl` and `watchlist.jsonl` |
| A10 | First held-out weekly set | Scored once with discovery frozen; result and set SHA recorded; **no pass threshold** (it is the trend baseline) |

**Report-only (no threshold; no baseline exists):** candidate precision on a 30-record sample Raj judges (real, dated founder-pitch event edition: yes/no); counts by `window_status`, `lineup_status`, and `page_kind`; watch-list size by reason; unique editions found by each query family alone; fallback firings by reason.

## Evaluation
- Benchmark/version: frozen v2 (SHA-256 `d7efe922893222b8e60e9847d548190098baedc66f2fb7c1a89402561c9c7c81`), live and replay reported separately. Replay window checks use the R3 reference dates.
- Baseline: Slice 2 Exa after first pass (9/14 overall, 6/7 live-CA, 3/6 replay, 0/2 US).
- Matching: the scorer (in `scripts/`, not in discovery code) maps candidate source URLs to `edition_key` using v2 cited URLs plus the existing `same_site_first_pass.csv` labels. Unmatched candidates that look related go to a manual adjudication CSV, and unjudged candidates are never credited. New qualifying editions go to a separate new-discoveries log (v2 is never edited).
- **Held-out protocol:** freeze discovery code, config, and query-list hash before the next weekly set (planned for about early December, adding NEXT AI and Total Mom Pitch finalists). The set is frozen and its SHA is recorded before the discovery run. Score it once, record the result, then move it to the tuning pool. Judge the trend across several weekly sets, never one week.

## Verification
- Unit tests:
  - query generation (determinism, rolling time phrase, Canada before US, and a leakage test asserting that no v2 event, organizer, or domain string appears in generated queries or config);
  - URL canonicalization;
  - page-kind rules;
  - EN/FR date parsing and window edges (+6 days, +7 days, +6 months exactly, multi-day straddling, year inference);
  - edition key and merge (city split, year split, conflict flag, mirror merge);
  - Serper fallback F1/F2 with mocked Exa and the fallback cap;
  - cost-cap stop;
  - watch-list `recheck_date` rules.
- Offline integration: A1 and A9 on Slice 2's saved responses.
- One live run after approval of this record's spend: A2–A8.
- Full diff review, `git diff --check`, and a key-value scan as in Slice 2.

## Interfaces / dependencies
- New: the `SearchProvider.search(query, options) -> list[SearchResult]` contract, the `CandidateEdition` and `WatchItem` models, and the run-folder layout. Slices 4–7 consume these.
- Credentials: `EXA_API_KEY` and `SERPER_API_KEY` from the ignored `.env`. `BRAVE_API_KEY` is no longer needed. No new dependencies beyond Pydantic and the standard library (any other dependency needs approval).

## Risks / deferred work
- **Exa returns no snippets in metadata-only mode.** If the D3-1 cost check fails, many Exa candidates will be `unknown`/`pending_date` until Slice 4 fetches pages.
- **Benchmark tuning risk.** The FR, US, and early-announcement families were shaped by the v2 misses, so v2 gains are not clean evidence. The held-out trend decides.
- **US metro list** may happen to cover a v2 US city; the rule is fixed before held-out scoring, and this is noted.
- **Rule-based classification** will misfile some pages, which is acceptable because ambiguous records go downstream as `unknown` rather than being dropped.
- Search indexes drift. Every run is dated and saved.
- Deferred: cross-run watch-list merge and scheduler (D23), LLM classification (D19), Exa native natural-language mode, and LinkedIn-only lineups (not counted, per 004 L4).
- Reversal effort: low. This is new code and local artifacts, with no product data or remote state.

## Decisions (approved 2026-11-14)

Raj approved this record on 2026-11-14 (America/Toronto) with these answers to the former open questions:

| ID | Decision |
| --- | --- |
| D3-1 | **Exa snippets: test them, behind a cost check.** Before enabling snippets, check Exa's current official pricing, and confirm the reported `costDollars` on one test request. Enable snippets only if they add no more than about the search price per request (about US$0.007). Otherwise keep metadata-only, leave dating to Slice 4, and report the price found. |
| D3-2 | **US phase:** on request only (`--us`) in normal runs; always on in evaluation runs. |
| D3-3 | **Caps:** US$1.25 per run and US$4 for the slice, approved as ceilings. Expected spend: about US$0.97 Exa worst case per evaluation run, plus up to about US$0.14 Serper. |
| D3-4 | **French scopes:** `Montréal`, `Ville de Québec`, `Québec` (province), `Sherbrooke`, `Gatineau`. That is 5 × 5 = 25 French queries, for a Canada phase of 97. |
| D3-5 | **Second-hop queries** from program or series pages: up to 15 per run. |
| D3-6 | **Too-far events** go on the watch list, with `recheck_date = event_date − 6 months`. |
| D3-7 | **Code layout:** the first product package goes at `src/leadgen/`, with a CLI entry point (`python -m leadgen.discovery`). |

## Security Impact
Not material to this slice beyond existing handling. Keys are read from the ignored `.env` and never printed or saved, with redaction carried over from Slice 2 and HTTPS verification on. Search results are untrusted external input and are validated by Pydantic at the boundary. Only event-level business facts, titles, and snippets are stored, with no extraction of people or contacts. Run artifacts stay local and gitignored. No Brave results are reused, given its retention terms.

## Approval
- User approval / date / proposal revision or scope: **Approved by Raj on 2026-11-14 (America/Toronto)**, for this record with decisions D3-1 to D3-7.
- Conditions: A1 (offline replay) must pass before any live API spend. Spend stays within US$1.25 per run and US$4 for the slice. The snippet cost check (D3-1) runs before snippets are enabled. Prerequisite: the 004 / Slice 2 close-out documentation pass is done first.
- Separately authorized external actions: Exa and Serper API spend within the caps above. Commit, push, deploy, and purchases are **not** authorized.
- Material amendments / renewed approval: none.

## Results (after implementation)
Pending.
