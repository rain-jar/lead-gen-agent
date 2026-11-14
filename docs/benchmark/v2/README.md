# Lead Discovery Benchmark v2 (Frozen 2026-11-14)

`benchmark.json` is a versioned known-item benchmark for founder and organizer lead discovery. The user approved freezing it on 2026-11-14 (`status: frozen`, `frozen_date: 2026-11-14`). The frozen SHA-256 is recorded in `docs/work/003-benchmark-v2.md`. Do not edit it in place: corrections and additions go in a new versioned set (see Evaluation protocol). v2 replaces nothing: v1 (`docs/benchmark/v1/`) stays frozen and unchanged. Which set Slice 2 uses is decided in the Slice 2 proposal.

- Benchmark date: 2026-11-14. Evidence was checked on 2026-11-14 for every source.
- Live window for the live split: events from 2026-11-21 through 2027-05-14 (reference date +7 days to +6 calendar months, PROJECT.md D08).
- Validate with `python3 scripts/validate_benchmark.py docs/benchmark/v2/benchmark.json`. The same script still validates v1.

## Why v2

v1 has 5 opportunities and 12 cases. All 7 positive founder cases come from one U.S. edition (San Diego Startup Week), and it has only 2 negative cases. That makes known-event recall in the provider benchmark close to uninformative, and it barely tests Canada. v2 fixes this by:

- increasing eligible opportunity editions from 4 to 14, 12 of them Canadian;
- drawing verified founders from 6 editions, with at most 3 of 17 (18%) from any one edition;
- increasing verified organizers from 3 to 8, all live and in-window;
- increasing negative/ambiguous cases from 2 to 12, covering all 9 failure categories in PROJECT.md §6;
- making the live vs replay distinction explicit per opportunity (`split`) and keeping one edition identity across both views (`edition_key`).

### Carried forward from v1 (re-checked 2026-11-14)
- San Diego Founders Fight Club 2026: 2 of the 7 founders (Kanna (Uchida) Ecklund, Byron Ward). The other 5 are dropped to respect the edition cap.
- University of Toronto Desjardins Startup Prize 2027: the organizer case.
- McMaster Startup Survivor 2026: Turki Alturaifi stays a too-soon negative in the live view. The same edition now also has a replay view (reference date 2026-10-29, the McMaster News publication date) in which three other named pitchers are positives.
- Not carried: the Synapse organizer (still valid, dropped only to limit Southern Ontario concentration) and the Cornell presenter-unknown negative (the same rule is now covered by `negative-presenter-unknown-multi-01`).

## Approved ground-truth rules

The user (Raj) approved these on 2026-11-14. They are also stored in `ground_truth_rules` in `benchmark.json`.

- **R1 Presenter:** a finalist entry naming exactly one person, on an official page stating that the finalists pitch or take the stage, names the presenter. Entries naming several people without a presenter designation are `presenter_unknown`.
- **R2 Newer founder:** finalist status in a founder competition is newer-founder evidence, unless primary evidence shows the venture is established (e.g., a completed institutional Series A). In that case the case is `established_founder`.
- **R3 Replay reference date:** a replay opportunity's `reference_date` is the date of the dated public announcement naming that edition.

## Evaluation protocol (agreed with the user, 2026-11-14)

- **Additive sets:** add a new benchmark set roughly every week as a new version (v2.1, v3, ...). The next set is planned for about early December 2026 and should add Canadian live founders as finalists publish (e.g., NEXT AI Montréal after Nov 24, Total Mom Pitch's Top 5 planned for Dec 8). A frozen set is never edited; corrections go in a new version with a recorded reason and evidence.
- **Held-out first:** each new set is a held-out test. Score it once and never tune queries or pipeline settings against it. After it has been scored, it may join the tuning pool.
- **Judge by trend:** each weekly set contains different events, so judge improvement by the trend in held-out recall across several weeks, not by one week.
- **Ageing:** older live cases become replay cases as their events pass. Replay reference dates follow rule R3.
- **Reporting:** report every score with the set version and its SHA-256. Keep held-out and tuning-pool results separate.

## Schema additions (all optional, so v1 still validates)

| Level | Field | Meaning |
| --- | --- | --- |
| Benchmark | `schema_version` | `2` turns on v2 checks |
| Benchmark | `benchmark_date` | Reference date for every live opportunity |
| Benchmark | `frozen_date`, `ground_truth_rules` | Freeze date and the user-approved labelling rules (R1–R3) |
| Opportunity | `split` | `live` (reference = benchmark date) or `replay` (historical reference date = dated public announcement) |
| Opportunity | `edition_key` | Stable edition identity. The live and replay views of one edition share it, and scoring dedupes on it |
| Opportunity | `event_end_date` | For multi-day events (both ends must be in the window if eligible) |
| Opportunity | `opportunity_type`, `sector`, `operator`, `notes` | Coverage reporting and the operator of record |
| Case | `failure_category` | Required on every non-verified case. One of the 9 PROJECT.md categories |
| Case | `duplicate_of` | Canonical case that a duplicate must merge into |
| Case | `newer_founder_evidence` | Required on verified founders |
| Case | `audience_evidence`, `contact_route` | Required on verified organizers. Contact routes are public business routes only |
| Case | `sector` | tech / non-tech per venture |

A founder case may omit `person_name` only when it is a non-verified `presenter_unknown` case for a company-only lineup. That missing person is exactly the failure being tested.

## Coverage

### Opportunities (18 records; 14 eligible)

| Split | Opportunity | Event date | City | Type | Expected |
| --- | --- | --- | --- | --- | --- |
| live | Startup TNT Calgary Fall 2026 Summit Finale | 2026-11-26 | Calgary, AB | regional/national pitch final | eligible |
| live | Innovation UBC Venture Showcase 2026 | 2026-12-01 | Vancouver, BC | founder showcase | eligible |
| live | NEXT AI Montréal Open House pitch competition | 2026-12-02 | Montréal, QC | accelerator/incubator demo day | eligible |
| live | uOttawa Engineering Pitch Competition (Fall 2026) | 2026-12-03 | Ottawa, ON | university competition | eligible |
| live | Hen Hatch Finals 2026 (Univ. of Delaware) | 2026-12-03 | Newark, DE, US | university competition | eligible |
| live | UdeM Demoday 2026 (Millénium Québecor) | 2026-12-04 | Montréal, QC | accelerator/incubator demo day | eligible |
| live | The Arena 2027 (Arthur L. Irving Entrepreneurship Centre) | 2027-03-01 → 2027-04-06 | Halifax, NS | university competition | eligible |
| live | U of T Desjardins Startup Prize 2027 | 2027-03-04 | Toronto, ON | university competition | eligible |
| live | McMaster Startup Survivor 2026 (live view) | 2026-11-18 | Hamilton, ON | university competition | ineligible (too soon) |
| live | Startupfest 2027 | 2027-07-07 | Montréal, QC | festival pitch competition | ineligible (too far) |
| live | Velocity Pitch Competition 2026 | 2026-09-12 | Waterloo, ON | university competition | ineligible (past) |
| live | Toronto Demo Night (Oribo listing) | 2026-12-11 | Toronto, ON | founder showcase | ambiguous |
| replay (ref 2026-02-27) | MRU JMH LaunchPad 2026 | 2026-04-01 | Calgary, AB | university competition | eligible |
| replay (ref 2026-05-21) | Climate Solutions Prize 2026 – Trailblazer pitch | 2026-06-09 | Montréal, QC | regional/national pitch final | eligible |
| replay (ref 2026-05-28) | Startup World Cup Ottawa Regional 2026 | 2026-06-11 | Ottawa, ON | regional/national pitch final | eligible |
| replay (ref 2026-10-13) | SOAR Indigenous Entrepreneurship Competition 2026 | 2026-10-21 | Saskatoon, SK | social/non-tech competition | eligible |
| replay (ref 2026-10-28) | San Diego Founders Fight Club 2026 | 2026-11-06 | San Diego, CA, US | regional/national pitch final | eligible |
| replay (ref 2026-10-29) | McMaster Startup Survivor 2026 (replay view) | 2026-11-18 | Hamilton, ON | university competition | eligible |

Eligible editions (14):
- **By country:** Canada 12, U.S. 2.
- **By province:** QC 3 (all Montréal), ON 4 (Ottawa 2, Toronto 1, Hamilton 1), AB 2, BC 1, SK 1, NS 1.
- **By type:** university competition 6, regional/national pitch final 4, accelerator/incubator demo day 2, founder showcase 1, social/non-tech competition 1.
- **By sector:** tech 7, mixed 5, non-tech 1, unspecified 1.
- **By split:** live 8, replay 6.

### Cases (37)

| Group | Count | Detail |
| --- | --- | --- |
| Verified founders (category B) | 17 | 6 editions: MRU 3, SOAR 3, Climate Solutions Prize 3, McMaster 3, Hen Hatch 3, San Diego 2. Max edition share 3/17 = 18% (cap 30%). Canada 12 / U.S. 5. Live 3 / replay 14. Non-tech ventures 5. |
| Verified organizers | 8 | All live. NEXT AI Montréal, Millénium Québecor (UdeM), Innovation UBC, Startup TNT, uOttawa CEED, Arthur L. Irving Entrepreneurship Centre, U of T Entrepreneurship, Horn Entrepreneurship (U.S.) |
| Negative / ambiguous (category C) | 12 | 11 rejected, 1 provisional; 9 live-split, 3 replay-split |

Negative/ambiguous coverage by failure category:

| Category | Case(s) |
| --- | --- |
| past_edition | Serena Wittenberg (LARS), Velocity Pitch Competition held 2026-09-12 |
| presenter_unknown | Carapex Biotechnologies (UBC company-only lineup); Emmanuel Akande (GIGXY, two-person team, presenter not stated) |
| outside_date_window | Turki Alturaifi (McMaster live view, event +4 days); Startupfest organizer (next event 2027-07-07) |
| non_pitching_role | Keira Frosst, a founder serving as judge at Startup World Cup Ottawa 2026 |
| established_founder | Michael Kelland, a CSP 2026 finalist whose company Planetary has a completed US$11.35M Series A |
| mismatched_edition | Haden Harrison, the Arena **2026** champion shown on the same page as the **2027** dates |
| organizer_no_upcoming_event | Velocity: no in-window pitch event published |
| insufficient_evidence | Toronto Demo Night: individual host, third-party listing, no contact route, inconsistent time (provisional) |
| duplicate | Local Energy listed twice in CSP 2026 (merge into founder-csp-01); NEXT AI Open House mirrored on arclight.events (merge into organizer-nextai-01) |

## Live vs replay

- **Live** opportunities use `reference_date = 2026-11-14`. They answer: "On the benchmark date, could fresh discovery find and qualify this?" A live run should be recorded with its actual run date. If that date is not 2026-11-14, report live results as approximate, or freeze a new version with an updated live split.
- **Replay** opportunities use the date of the dated public announcement as their reference date (for example, the MRU finalist post of 2026-02-27). The event was 7 days to 6 months ahead on that date. Replay cases test known-item retrieval of evidence pages that still exist today. They do **not** reproduce what a search index returned on the historical date, and replay scores must not be presented as current discovery quality.
- One edition can appear in both splits (McMaster). Scoring dedupes by `edition_key` within a split. The two views have different expected labels by design.

## Known limitations

1. **Live founder positives are U.S.-only (3, Hen Hatch).** As of 2026-11-14 no checked Canadian event in the live window had published named presenters:
   - Innovation UBC published a company-only lineup.
   - NEXT AI finalists are chosen after November 24.
   - Startup TNT's Top 5 are only on LinkedIn, not the official page.
   - U of T and Arena finalists come later.
   - QueerTech OutPitch (Toronto, Nov 18–19) was too soon, and its page blocked automated fetches.

   Canadian founder coverage therefore comes from replay.
2. **Founder geography gaps.** No founder positives from Toronto, Vancouver, Ottawa, Waterloo, Atlantic Canada, or Québec City; those regions appear only as opportunities, organizers, or negatives. Québec City is absent entirely.
3. **The presenter rule (R1, approved 2026-11-14) carries a lot of weight.** Only San Diego and McMaster label a "Pitching" person explicitly. For MRU, SOAR, CSP and Hen Hatch, a finalist entry naming exactly one person, on a page saying the finalists pitch or take the stage, is treated as naming the presenter. Entries naming several people without a presenter designation are rejected, consistent with the v1 Cornell case.
4. **Some newer-founder evidence is weak.** SOAR, CSP-02/03 and the San Diego cases rely only on finalist status, which PROJECT.md lists as acceptable. Venture age was not checked, except Planetary, where contrary evidence made it a negative. SOAR finalists are non-tech small businesses whose age is not stated.
5. **McMaster replay realism.** The replay reference date (2026-10-29) comes from McMaster News, which names founders but not presenters. The "Pitching:" designations on The Forge page are undated (checked 2026-11-14).
6. **Source types.** The CSP release is organizer-authored but distributed via CNW. A few supporting sources are third-party: the Platform Calgary listing, the arclight mirror, the Oribo listing, and Planetary's company release. Required facts for positives come from organizer or official pages.
7. **Small known set.** Known-item recall over 14 editions is limited evidence. It is not population recall.
8. **Data-quality traps were excluded, not modelled.** The CSP release contains editorial placeholders ("[confirm name]") in its research-prize list, and the CodeLaunch Canada page attaches the wrong website to a finalist. No cases use those lists.

## Leakage prevention

- Product query generation, provider adapters and tuning code must not read this file or contain any event name, venture, person, organizer, domain or URL from it. Query families are frozen in the Slice 2 proposal **before** any provider run, using only category or geography/date terms (see PROJECT.md §4 illustrative shapes).
- All providers get the same frozen benchmark version, query families, query count/budget, geography order (Canada first) and result cutoff.
- Scoring runs offline after retrieval. It matches results to `edition_key` via the cited URLs/domains plus manual adjudication, and it logs every adjudication.
- Newly found qualifying editions or people go in a separate "new discoveries" log with their own evidence. They are never added to v2 mid-run. Any ground-truth change needs approval and a new version.
- Freeze by recording the SHA-256 in the work record. Never edit a frozen version in place.

## Metrics the Search Provider Benchmark (Slice 2) will calculate

Report each metric overall, by split (live / replay), by country (CA / US) and by `opportunity_type`. Dedupe results to `edition_key` before scoring.

1. **Known-event recall@10:** eligible editions with at least one official or event source in a provider's top 10 for any query in the frozen set, divided by eligible editions in scope. Also report per query family.
2. **Evidence-page recall@10 (founder/organizer):** verified cases whose cited evidence page (exact URL or same page on the same domain) appears in the top 10, divided by verified cases. This diagnoses whether the person evidence is reachable, not just the event.
3. **Precision/relevance@10:** each unique top-10 result manually judged with a recorded rubric (relevant edition / irrelevant / unjudged). Unjudged results are never credited.
4. **Trap exposure:** the share of category-C opportunities (past, too far, no upcoming event, unofficial listing) that surface in the top 10, plus the duplicate rate (the same `edition_key` at more than one URL in the top 10). This is informational for search; qualification must later reject them.
5. **Useful new discoveries:** independently verified qualifying editions not in v2, logged separately.
6. **Latency:** wall-clock time per query and per provider run, including failures (median and total).
7. **Cost:** the actual charge when the provider reports it, otherwise a dated estimate labelled as an estimate.

Later stages reuse the same cases:
- **Qualification:** v2 labels should yield 0 false-Verified on category C, correct Verified on the 17 founders and 8 organizers, and duplicates merged.
- **Extraction:** correct person, venture, date, operator and contact on positives.

## Provenance and privacy

Every opportunity and case lists its source URLs, `checked_date` 2026-11-14, and a short evidence quote or note. Only public business/event facts and necessary names are stored. Contact routes are official forms or published program/organization addresses. Named-staff emails visible on pages are referenced by page, not copied. No secrets are stored.
