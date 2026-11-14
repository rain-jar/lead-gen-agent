# 005 — Opportunity Discovery (Slice 3)

- Status: **Complete pending A10.** Raj approved closure on 2026-11-14 (America/Toronto) and accepted precision 16/25, because discovery's job is to find candidates and later stages filter them. Official gates A1a, A2a, A2b, A3, A4, A5, A6, A7, A8 and A9 pass on saved responses. Source and documentation were committed locally after Raj's review request; no push. A10 (first frozen held-out weekly set, about early December) is still open. Carry-forward rules for Slices 4 and 6 are in the Closure note below.
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
| A2 | *Restated by the approved 2026-11-14 A2 amendment (below).* Fresh live run: **A2a** v2 live Canadian editions returned by search; **A2b** live Canadian editions kept as candidates with no wrong city or year. Replay and US: report returned-by-search and kept-or-correctly-excluded | A2a ≥ 6/7 and A2b ≥ 6/7. Reported, not gating: overall, replay and US splits, UdeM Demoday |
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
  - watch-list `recheck_date` rules;
  - event-date role selection (deadline, posted, byline, recap and ambiguous dates), year resolution from explicit dates, cross-site dedupe, A2a/A2b scoring and the seeded precision sample, all on made-up text (A2 amendment).
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
- Material amendments / renewed approval: the A1 amendment and the A2 amendment, both approved by Raj on 2026-11-14 (America/Toronto) and recorded below.

## Approved A1 amendment — 2026-11-14 (America/Toronto)

Raj approved an independent-review correction to the gate. **A1a** replaces A1 as the gate before live spend: saved Slice 2 Exa + Serper replay (no Brave) must retain at least 9/14 eligible v2 editions overall and 6/7 live Canadian as candidates, with no credited edition assigned a wrong city or year on any record. Unknown city/year is allowed and must be reason-coded and sent downstream. Report Exa-only beside the union. **A1b** is exact city-plus-edition-year matching, reported in Slice 3; it becomes a gate after Slice 4 page fetching. A9 remains a gate. Other criteria and caps are unchanged. The prior 5/14 result used A1b-like scoring and overstates lost candidate retention.

Generic implementation rules approved in the amendment: freeze a Canada city/province and US metro list and parser before rescoring; infer city from page title/URL/snippet (query scope only a hint); strip site/platform name from titles; ignore past champion/winner and copyright years; merge by canonical URL then site/event/year without combining conflicting city/year; preserve source provenance; retain unknowns; emit one watch row per edition with multiple reasons, distinguishing unknown and pending dates. The scorer stays in `scripts/`, folds city accents/case, uses R3 replay reference dates, and reports A1a/A1b, union/Exa-only, and distinct URLs. Raj authorized these repairs and the existing bounded live evaluation after A1a and A9 pass. No commit, push, deployment or purchase was authorized.

Frozen generic geography/parser inputs for this rescore: `CA_CITIES`, `CA_PROVINCES`, `US_METROS`, `CITY_ALIASES`, `clean_event_name`, `page_city`, and `event_years` in `src/leadgen/discovery/core.py` as written before the amended replay. They contain no benchmark event names, domains, people, or URLs. Source fields are examined in title → URL path → snippet order; no query city is used in the key. A missing city/year is recorded as unknown. Champion/winner and copyright clauses are excluded from year extraction. Further changes require a dated result entry, not silent tuning against v2.

## Approved A2 amendment and date/dedupe fixes — 2026-11-14 (America/Toronto)

Raj approved this amendment on 2026-11-14 (America/Toronto). An independent review of the live run found that search recall had not regressed: Exa returned 9/14 v2 editions overall and 6/7 live Canadian, the same as Slice 2. The A2 drop to 6/14 came from date logic (UBC was excluded as `past` from its post and deadline dates, although its text gives the event date) and from A2's definition, which also penalized correct exclusions.

**Restated A2** (A1a is unchanged):
- **A2a:** v2 live Canadian editions returned by search, meaning a cited or first-pass same-site URL appears in an HTTP 200 Exa or Serper result of the run. Target **≥ 6/7**.
- **A2b:** v2 live Canadian editions kept as candidates with no wrong city or year on any record. Unknown city or year is allowed. Target **≥ 6/7**.
- **Replay and US editions:** report "returned by search" and "kept or correctly excluded". A correct `past` or `too_soon` exclusion is not penalized.

`scripts/score_discovery.py` computes A2a, A2b and kept-or-correctly-excluded from the run's `raw.ndjson` and writes `a2_pass` to `score.json`.

**Approved generic fixes:**
1. **Event-date selection.** Deadline, application, posted, updated and byline dates are never event dates. The parser picks the earliest cued event date at least 7 days after the reference date. When conflicting dates remain and none is cued, the window is `unknown` with reason `date_ambiguous` instead of a guess.
2. **No past-to-future year inference.** A yearless date gets no inferred year when the text is a recap or carries an earlier explicit year.
3. **Year resolution.** A multi-year conflict resolves when explicit full event dates or year headings agree on one year, with past-winner and champion lines excluded. The record is flagged `year_resolved_by_explicit_date`.
4. **Cross-site dedupe.** Records from different sites merge only with the same known city, the same full event date, no conflict flags, compatible years and at least two shared meaningful name tokens.
5. **A2 restatement** as above.
6. **Precision sample.** `scripts/precision_sample.py` draws a fixed, seeded sample of 25 `in_window` candidates (seed `20261114`) into `precision_sample.csv` with blank review columns. It is report-only.

**Additions made during implementation, within the scope above and recorded for review:** a same-site merge for pages that share a host, an identical full event date and at least two meaningful name tokens; and a narrower past-clause rule, so that "champion" no longer matches "championship". Every rule is tested on made-up text. Discovery code contains no v2 names, domains, people or URLs, and a test now checks this against the frozen v2 file. No commit, push, deployment, purchase, API call or spend was authorized or made.

## Historical results: initial offline gate (superseded)

Tests were written first in `tests/test_discovery.py`. Initial local code is in `src/leadgen/discovery/`, with a separate scorer in `scripts/score_discovery.py`. The saved Slice 2 Exa and Serper responses were replayed, excluding Brave. The offline run is `artifacts/discovery/a1-replay/` and its `score.json` is reviewable. No Slice 3 keys were loaded or API calls made; Slice 3 spend is **US$0**.

| Criterion | Observed result |
| --- | --- |
| A1 | **Fail:** 5/14 correctly keyed eligible editions overall and 3/7 live CA, below 9/14 and 6/7. Replay 2/6; US 0/2. Search URLs matched more cases, but city/year extraction and keying lost NEXT AI, uOttawa, Arena, and McMaster. |
| A2–A8 | Not run: the A1 gate prohibits the live evaluation. No fresh recall, latency, fallback, or paid cost observations. |
| A9 | Pass for the offline run: a second processing pass with the same run ID produced byte-identical candidates, watch list, and excluded files. |
| A10 | Not run: no held-out weekly set is frozen yet. |

The replay produced 540 candidates, 349 excluded records, and 660 watch items (multiple reasons can apply to one candidate). Candidate windows: 61 in-window, 36 pending date, 18 too far, 425 unknown. Lineups: 95 announced hints, 31 pending, 414 unknown. Page kinds: 198 event edition, 119 event series, 36 listing/aggregator, 39 news, 148 social. Watch reasons: 150 alternate source, 461 date pending, 18 enters window later, 31 lineup pending. These are **diagnostics only**: broad classification and national-query city inference are still too weak. The saved replay currently uses one 2026-11-14 reference date; R3-specific replay window evaluation is not yet implemented. The second-hop family, live adapters, candidate dedupe quality, and A2–A8 remain unfinished.

Nine focused tests pass (six new rule/orchestration tests and three Slice 2 tests). `git diff --check` passes. A local scan found zero key values in the offline run artifacts and zero Brave sources in candidate output. The A1 miss is a real blocker to spending, so the approved live run was not attempted. Exa snippet pricing and `costDollars` were not checked because the live gate was not reached. The next implementation step is to fix city/edition extraction and R3 replay handling from generic evidence, rerun A1 and A9, then proceed to current-price checks and the bounded live run only if A1 passes. No benchmark names or domains may enter discovery code/config.

### Historical amended replay result (superseded by URL-merge repair)

The amended offline run is `artifacts/discovery/a1-amended/` (`run.json`, candidate/watch/excluded JSONL, `score.json`). **A1a fails:** Exa+Serper union retains 8/14 overall and 5/7 live CA; Exa-only retains 9/14 and 6/7. The union loses Arena because Serper snippets produce wrong city/year records for that cited URL; the rule forbids credit when *any* record has a wrong value. Union replay is 3/6 and US 0/2; Exa-only replay is 3/6 and US 0/2. **A1b, report only:** union 2/14 overall, 1/7 live CA, 1/6 replay, 0/2 US; Exa-only 1/14 overall, 0/7 live CA, 1/6 replay, 0/2 US. One edition is 7.1 points overall and 14.3 points among live Canadian cases. Six replay benchmark editions are in-window when evaluated against their individual R3 reference dates; the discovery replay still labels candidates with a single 2026-11-14 reference date, so candidate-level R3 handling remains unfinished.

The following table covers the nine v2 editions credited to Exa or Serper in Slice 2. Counts are actual candidate records that contain a credited source URL (the same URL can appear in multiple records). `?` means unknown. The first-pass adjudication labels are applied by the scorer, not embedded in discovery code.

| Edition | Before: records; cities; years | After: records; cities; years |
| --- | --- | --- |
| NEXT AI Montréal Open House | 1; Montreal; ? | 1; Montréal; ? |
| UBC Venture Showcase | 2; Vancouver; 2026 | 2; ?; 2026 |
| Startup TNT Calgary | 2; Calgary; 2026/? | 2; Calgary; 2026/? |
| uOttawa Engineering Pitch | 2; Ottawa/?; ? | 1; ?; ? |
| Arena 2027 | 17; nine query cities/?; 2026/2027/? | 20; Calgary/?; 2026/2027/? |
| U of T Desjardins Prize | 10; seven query cities/?; 2027/? | 1; ?; 2027 |
| SOAR 2026 | 2; Saskatoon; 2026/? | 2; ?; 2026/? |
| McMaster Startup Survivor | 1; ?; ? | 1; ?; ? |
| Startup World Cup Ottawa | 3; Ottawa; 2026/? | 3; Ottawa; 2026/? |

The Arena result exposes a remaining merge defect: 20 records containing its cited URL survive, although the scorer's deduplicated row reports four identities. Some Serper snippets mention Calgary and 2026 context around the Arena page. This is not evidence that the Arena edition is in Calgary or 2026. The A1a failure is therefore substantive, and the gate remains closed.

Amended replay totals: **442 candidates, 426 distinct candidate URLs, 281 excluded, 407 watch rows** (one per dedupe key; 1,030 reason memberships). The prior run had 540 candidates and 442 distinct URLs. Watch memberships by reason: alternate source 137, city unknown 272, date pending 26, date unknown 346, enters window later 14, lineup pending 32, year unknown 203. Candidate windows: 45 in-window, 29 pending date, 14 too far, 354 unknown. The individual watch rows list their edition key and reasons in `watchlist.jsonl`; `run.json` has the reason counts. These figures are provisional diagnostics because edition identity and merge are not yet sound.

**A9 passes offline:** reprocessing with the same run ID gave byte-identical candidate, watch, and excluded outputs. Fourteen focused tests pass, `git diff --check` passes, and a local artifact scan found zero API key values. A2–A8 and A10 were not run; there were no Slice 3 provider requests, latency observations, snippet cost test, or spend (**US$0**). Per the approved stop rule, no live evaluation was attempted. Repair the generic Arena snippet/merge logic and candidate-level R3 handling, then freeze and rerun A1a/A9 before checking prices or making API calls. Slice 3 code and this record remain uncommitted for Raj's review.

### Approved URL-merge repair and completed live evaluation (2026-11-14)

Raj approved one more generic repair, keeping A1a and all cost limits unchanged. `merge_candidates` now always consolidates a canonical URL, resolves conflicting city/year/date to unknown with explicit flags, then merges compatible same-site pages only with a unique target. `page_city` uses the full title and URL path and requires a venue phrase or city/province pattern in snippets. A true Exa-only replay filters Serper *before* normalization. These changes use no v2 names, domains, people or URLs in discovery code/config/tests.

The saved-response replay now **passes A1a and A9**. A1a union: 9/14 overall, 6/7 live Canada, 3/6 replay, 0/2 US; true Exa-only: the same. A1b (report only) union and true Exa-only: 2/14 overall, 1/7 live Canada, 1/6 replay, 0/2 US. No credited record has a wrong city or year. The Arena is one candidate with unknown city/year and a year-conflict flag; Desjardins is one candidate with Toronto and unknown year. The replay has 415 union candidates, 428 distinct candidate URLs, 402 watch rows, 36 year-conflict and 7 date-conflict flags. The true Exa-only replay has 251 candidates, 260 distinct URLs, 246 watch rows, and 4 year-conflict flags. Candidate, watch, and excluded files were byte-identical on repeated processing of each view. One edition changes overall recall by 7.1 points and live-Canada recall by 14.3 points.

| Slice 2 credited edition | Before repair: records; city; year | After repair: records; city; year |
| --- | --- | --- |
| NEXT AI Montréal Open House | 1; Montréal; ? | 1; Montréal; ? |
| UBC Venture Showcase | 2; ?; 2026 | 2; ?; 2026 |
| Startup TNT Calgary | 2; Calgary; 2026/? | 2; Calgary; 2026/? |
| uOttawa Engineering Pitch | 1; ?; ? | 1; ?; ? |
| Arena 2027 | 20; Calgary/?; 2026/2027/? | **1; ?; ?** (year conflict) |
| U of T Desjardins Prize | 1; ?; 2027 | **1; Toronto; ?** |
| SOAR 2026 | 2; ?; 2026/? | 2; ?; 2026/? |
| McMaster Startup Survivor | 1; ?; ? | 1; ?; ? |
| Startup World Cup Ottawa | 3; Ottawa; 2026/? | 3; Ottawa; 2026/? |

Official prices checked before the live call: [Exa Auto Search](https://exa.ai/pricing) US$7/1,000 for up to ten results with highlights included; [Serper Starter](https://serper.dev/) US$1/1,000 queries. The first Exa request used `contents.highlights` and reported `costDollars.total = US$0.007`, so highlights stayed enabled (incremental price observed: US$0). No summary, answer, research, date filter, or domain filter was used. The live query file SHA-256 is in `artifacts/discovery/live-eval-20261114-network/run.json`.

The first sandboxed network attempt had 67 Exa and 66 Serper connection failures, no HTTP successes, and was aborted. Its conservative reserved list price was US$0.535, with no response-reported charges. The network-enabled evaluation made **130 successful Exa requests**, zero retries and zero Serper calls; each query's Exa result set had at least one event-like page, so neither F1 nor F2 fired. It ran 48 English core, 24 English early, 25 French, 7 second-hop, 6 US national and 20 US metro queries. Exa reported **US$0.910**; list-price reservation was also US$0.910. Combined conservative reservation for both attempts is US$1.445 against the US$4 slice ceiling; each run stayed under US$1.25. Exa total request latency was 81.064 seconds, median 0.412 seconds. Actual Serper charge was zero for the successful run; the failed sandbox attempts reported no provider charges.

Processing of the saved live NDJSON initially failed because `str.splitlines()` treats an embedded Unicode line separator inside a JSON string as a record break. Parsing now splits only on LF. The raw responses were processed offline with no extra API calls; a focused regression test covers this. The live run output is `artifacts/discovery/live-eval-20261114-network/` (`raw.ndjson`, `queries.tsv`, `run.json`, candidate/watch/excluded files, `score.json`, `evaluation.json`).

| Criterion | Observed live result |
| --- | --- |
| A2 | **Fail:** fresh v2 candidate recall 6/14 overall, 5/7 live CA, 1/6 replay, 0/2 US versus 9/14 and 6/7 targets. Only Exa was called; search index drift and normalization both remain plausible contributors. Unjudged new URLs are not credited, so this is a known-source lower bound. |
| A3 | **Fail:** five live eligible editions surfaced; Arena's window is `unknown`, so only four of five are `in_window` or `pending_date`. None of these five were excluded. |
| A4 | **Pass on cited-source traps:** McMaster live view was excluded `too_soon`; Startupfest was `too_far`; Velocity was `unknown` as a candidate and `past` as an excluded record. None was `in_window`. |
| A5 | **Partially checked:** conflicting same-URL evidence resolves to unknown with flags; no wrong city/year was credited on A1a replay. Full adjudication of all live cross-page city/year joins remains open. |
| A6 | **Fail:** Startup TNT Calgary has two candidate records containing cited edition pages. Other surfaced eligible editions have one each. |
| A7 | **Pass on measured parts:** no program page was emitted `in_window`; all 66 social candidates had `needs_alternate_source` and an alternate-source watch reason. Bot-blocked sources require separate adjudication. |
| A8 | **Pass:** US$0.910 response-reported Exa cost, below US$1.25/run and US$4/slice; 130 requests, latency and query hash logged; artifact scan found zero key values and zero Brave records. |
| A9 | **Pass:** replay and live raw-response reprocessing produced byte-identical candidate, watch and excluded files with the same run ID. |
| A10 | Not run; no frozen weekly held-out set exists. |

Live diagnostics: 414 candidates, 419 distinct candidate URLs, 410 excluded, **375 watch rows** (one per dedupe key, 877 reason memberships). Candidate windows: 172 `in_window`, 43 `pending_date`, 58 `too_far`, 141 `unknown`. Lineups: 96 announced hints, 166 pending, 152 unknown. Page kinds: 287 event edition, 10 event series, 27 listing, 24 news, 66 social. Watch reasons: alternate source 64, city unknown 224, date pending 43, date unknown 141, enters window later 57, lineup pending 163, year unknown 185. Query-family candidate-key counts are in `evaluation.json` (core 163, early 96, French 65, second-hop 28, US national 34, US metro 108); these are provisional edition counts because dedupe still fails A6. Candidate conflict flags: 172 year, 10 date, 1 city. Nineteen focused tests passed before the run, and twenty passed after the NDJSON fix; `git diff --check` passed. No commit, push, deployment, purchase or further paid evaluation was performed.

Remaining work before completing Slice 3: improve fresh candidate recall and date handling, eliminate the Startup TNT duplicate, audit blocked sources and the A5 city/year joins, and test against a frozen held-out weekly set when available. Resolving years from explicit dates or mapping institutions to cities is deferred to Slice 4 as an option, per Raj's latest instruction; it was not added to this run. *(Superseded for years: the A2 amendment below approved year resolution from explicit event dates. Institution-to-city mapping remains deferred.)*

## Results: A2 amendment fixes, reprocessed for US$0 (2026-11-14, current)

All results below come from offline reprocessing of saved responses. There were no API calls and no spend (**US$0**). Inputs:
- Slice 2 replay: `artifacts/search-provider/20261114T131952Z/raw.ndjson`, SHA-256 prefix `ec3a169f`.
- Live responses: `artifacts/discovery/live-eval-20261114-network/raw.ndjson`.

Reference date: 2026-11-14. Outputs:
- `artifacts/discovery/a1-fix3-union/`
- `artifacts/discovery/a1-fix3-exa/`
- `artifacts/discovery/live-reprocess-20261114-fix3/`

Each has a `-repeat` twin. Verification ran on Raj's Mac with the repo's own Python 3.12.6 and Pydantic 1.10.19.

"Before" is the previous code on the same inputs. Before-values for A2a and A2b come from running the new scorer on the earlier live output.

| Criterion | Before | After | Result |
| --- | --- | --- | --- |
| A1a union (replay) | 9/14 overall, 6/7 live CA, 3/6 replay, 0/2 US | 9/14, 6/7, 3/6, 0/2; 0 wrong city/year | **Pass** (unchanged) |
| A1a true Exa-only | 9/14, 6/7, 3/6, 0/2 | 9/14, 6/7, 3/6, 0/2 | **Pass** (unchanged) |
| A1b union / Exa-only (report only) | 2/14 (1/7 live CA) / 2/14 (1/7) | 3/14 (2/7) / 2/14 (1/7) | Report only |
| A2a live CA returned by search | 6/7 (9/14 overall) | 6/7 (9/14 overall) | **Pass** |
| A2b live CA kept, no wrong city/year | 5/7: UBC excluded `past` | 6/7 (7/14 overall) | **Pass** |
| Replay: returned / kept or correctly excluded | 3/6 / 3/6 | 3/6 / 3/6 | Report only |
| US: returned / kept or correctly excluded | 0/2 / 0/2 | 0/2 / 0/2 | Report only |
| A3 surfaced live eligible editions in window | 4 of 5: Arena `unknown` | 6 of 6 `in_window`, 0 excluded | **Pass** |
| A4 date traps | 0 `in_window` | 0 `in_window`: McMaster excluded `too_soon`, Startupfest `too_far`, Velocity `unknown` plus excluded `past` | **Pass** |
| A6 one record per surfaced edition | Startup TNT had 2 records | Every surfaced live edition has 1 record | **Pass** |
| A5 official (v2 city/year integrity) | Full live adjudication was open | 0 v2-related records merge different years or cities: Arena is 2027 with city unknown; NEXT AI Toronto and Montréal are separate; Startup TNT Calgary and Edmonton are separate | **Pass** (see the A5 section below) |
| A7 measured parts | 0 programs `in_window`; 66 social, all flagged | 0 programs `in_window`; 98 social + 2 Meetup, all with `needs_alternate_source` and a watch reason | **Pass** (full blocked-source audit now closed; see the A7 section below) |
| A9 determinism | Pass | Candidate, watch, excluded and run files byte-identical with the same run ID for all three views | **Pass** |

The live view of the nine Slice 2-credited editions (records containing a credited URL; city; year; window; `?` means unknown):

| Edition | Before | After |
| --- | --- | --- |
| NEXT AI Montréal Open House | 1; Montréal; 2026; in window | 1; Montréal; 2026; in window |
| UBC Venture Showcase | 0; excluded `past` | **1; ?; 2026; in window** |
| Startup TNT Calgary | **2**; Calgary; 2026; in window | **1**; Calgary; 2026; in window (cross-site merge) |
| uOttawa Engineering Pitch | 1; ?; 2026; in window | 1; ?; 2026; in window |
| Arena 2027 | 1; ?; ?; `unknown` | **1; ?; 2027; in window** (`year_resolved_by_explicit_date`) |
| U of T Desjardins Prize | 1; Toronto; ?; in window | 1; Toronto; **2027**; in window |
| SOAR 2026 (replay) | 1; ?; ?; `unknown`, plus one excluded `past` | unchanged |
| McMaster Startup Survivor (replay) | 0; excluded `too_soon` against 2026-11-14 (correct) | unchanged |
| Startup World Cup Ottawa (replay) | 0; excluded `past` (correct) | unchanged |

On the A1a replay union, only two editions changed:
- Arena moved from 1; ?; ? to 1; ?; 2027 in window.
- Desjardins moved from 1; Toronto; ? to 1; Toronto; 2027.

The replay still has multiple records for UBC (2), Startup TNT (2), SOAR (2) and Startup World Cup Ottawa (3). A6 was measured on the live run.

**Live totals before → after:**

| Measure | Before | After |
| --- | --- | --- |
| Candidates | 414 | 485 |
| Distinct candidate URLs | 419 | 501 |
| Excluded | 410 | 325 |
| Watch rows | 375 | 440 |
| Watch reason memberships | 877 | 1,010 |

Exclusion reasons before → after:
- `past`: 281 → 212
- `too_soon`: 55 → 41
- `program_without_dated_event`: 54 → 52
- `non_event`: 20 → 20

Candidate windows after: 199 `in_window`, 40 `pending_date`, 30 `too_far`, 216 `unknown`.

Other live diagnostics after:
- Lineups: 132 announced, 188 pending, 165 unknown.
- Page kinds: 328 event edition, 13 event series, 27 listing, 19 news, 98 social.
- Watch reasons: alternate source 99, city unknown 262, date ambiguous 26, date pending 40, date unknown 189, enters window later 29, lineup pending 188, year unknown 177.
- Conflict flags: 159 year, 5 date, 1 city. 82 records carry `year_resolved_by_explicit_date`.
- Query-family unique editions: core 182, early 124, French 72, second-hop 31, US national 43, US metro 124.

The A1a replay union has 422 candidates, 435 distinct URLs and 408 watch rows. Exa-only has 251, 260 and 246.

**Precision sample (report only).** The sample file is `artifacts/discovery/live-reprocess-20261114-fix3/precision_sample.csv`: seed `20261114`, 25 of 199 `in_window` candidates. Raj filled `raj_real_in_window_event` for all 25 rows (none blank) in the Numbers copy; those labels were copied back into the CSV. Comparison with the advisory labels is in `precision_comparison.csv`. Raj's label wins on disagreements.

Final precision, using Raj's labels:
- Real in-window events: **16/25**.
- Canada-located (same 13 records as the advisory `advisory_in_canada=yes` set): **6/13** real.
- Agreement with the advisory labels: **16/25**. Nine disagreements, listed below; no advisory fallback was used.
- Among Raj's 9 "no" rows, his reasons group as: not an event (3), program not an event (2), calendar (3), press release (1).

Disagreements (Raj wins; one-line rationale):
- Pitch & Plate: Raj yes vs advisory no. Raj treats a buyer-facing food pitch as a real in-window event; the advisory was stricter about on-stage founder pitches.
- Polsky "College Students": Raj yes vs advisory no. Raj counts the page as a real event; the stored date is still a deadline beside a listing.
- EFVC: Raj yes vs advisory no. The 2027 competition is a real pitch event; the stored date is the application deadline.
- Freirich: Raj yes vs advisory no. Raj counts the competition as real; the stored date is a judging or selection meeting.
- MacEwan Ventures: Raj no vs advisory yes. Raj treats the cohort-showcase page as a program, not an event edition.
- Must-attend Miami list: Raj yes vs advisory no. Raj counts the list as a real in-window event; it remains a third-party aggregator page.
- TechCon SouthWest: Raj no vs advisory yes. Raj rejects a press-release source even though the conference and pitch date are real.
- TiE Atlanta: Raj yes vs advisory no. Raj counts the program as a real event; the stored date is a mock round.
- VEF Events: Raj no vs advisory yes. Raj treats the organiser's events list as a calendar, not a single event edition.

The earlier informal sample (about 14/25 real) was a different random draw judged by a different reviewer, so it is not a measured improvement. The `geo_tier` column records the query phase, not the event's location.

**A5 official result: Pass.** Full row-level judgements are in `artifacts/discovery/live-reprocess-20261114-fix3/a5_adjudication.csv` and `a5_adjudication.md`. On the v2-related records named in 005, 0 records merge different years or cities.

Broader live city/year/merge audit (no 005 numeric threshold; no pass invented): 217 assigned cities, 0 wrong; 308 assigned years, 1 implausible year (`2000` taken from a statistic on a Startup TNT Summit X page); 18 merged records, of which 7 are same-site over-merges of different events (6 candidates, 1 excluded). Those over-merges happen when `clean_event_name` collapses both pages to the organiser name. Conflicting dates were cleared (`date_conflict`); no conflicting city or year was picked. A proposed follow-up threshold is 0 wrong city or year assignments and 0 merges of different events. A generic same-site name-join fix is recommended and was not applied in this pass, so the live totals and precision sample stay unchanged.

**A7 result: Pass.** The audit is in `artifacts/discovery/live-reprocess-20261114-fix3/a7_audit.md`. 0 program pages were emitted as candidates. All 98 social candidates, 22 social excluded records, and 2 Meetup candidates have `needs_alternate_source`, `access_hint=alternate_needed`, and (for candidates) a watch reason `alternate_source_needed`. No Facebook, Instagram, X, SPIE, or Incapsula-type sources appeared. The live raw file has 130 Exa search responses and no event-page fetches. Candidate records have no contact fields; incidental email-like and phone-like strings in snippets were not extracted. Residuals, not fails: `twitter.com` is not in the social host list (`x.com` is; 0 hits in this run), and historically fetch-blocked hosts such as `queertech.org` are retained but not auto-tagged because there is no blocked-host list beyond social and Meetup.

**Limits:**
- UdeM Demoday and both US benchmark editions are still not found by search.
- Cities are often unknown until Slice 4 fetches pages: 262 live watch rows carry `city_unknown`.
- The US phase stays opt-in in normal runs and sorts after Canada.
- Residual errors: deadlines in page headers or after weekday-time lines, program-start dates, and aggregator pages still reach `in_window`.

**Leakage caution.** Fixes 1–4 were motivated by v2 traces. Several implementation details were also tuned after looking at live candidates, including rows of an earlier precision draw. The v2 and precision numbers above are therefore not clean evidence. The first frozen held-out weekly set (A10) has to confirm these gains.

**Checks:**
- 44 tests pass: 24 new, all on made-up text, including a code-leakage test against the frozen v2 file.
- `git diff --check` passes, and the new files have no trailing whitespace.
- A key-value scan of the new artifacts and changed code found zero values for the three configured provider keys.
- Frozen benchmarks and the Slice 2 query file were not touched.
- No commit, push, deployment, purchase or API call was made.

**Remaining after Slice 3 closure:**
1. A10: score the first frozen held-out weekly set once, with discovery frozen (planned for about early December).

## Closure (2026-11-14, approved by Raj)

Raj approved closing Slice 3, pending A10, and accepted precision **16/25**. Discovery's job is to find candidates; later stages filter them. Official A5 and A7 pass. The following rules are carried forward:

1. **Calendars and listing pages** stay in as candidates, flagged as a list of events. Slice 4 (Evidence Retrieval) opens them and pulls out each event as its own candidate.
2. **Non-events and press releases** never take a weekly slot. Slice 6 (Qualify) drops them, or sends them to the watch list if they name an organizer.
3. **Programs and accelerators** count only through a dated demo day or pitch event, which becomes the candidate; otherwise they go on the watch list.

Also carry forward, to fix early in Slice 4:
- same-site over-merges of different events caused by organiser-name collapse;
- add `twitter.com` to the social-site list (`x.com` is already listed);
- drop implausible years taken from statistics (for example a `2000` parsed from a page metric).

No commit, push, deployment, purchase or API call was made in this close-out.
