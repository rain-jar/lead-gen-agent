# Amendment A — Slice 2 Search Provider Benchmark

- Status: **Approved for the query freeze by Raj on 2026-11-14.** The canonical revised record is `002-search-provider-benchmark.md`. Provider implementation, calls, purchases, commits, and pushes remain unapproved.
- Applies to: `docs/work/002-search-provider-benchmark.md` in its current Proposed form (42 queries: three intent families × seven compound geographic scopes × two time modes).
- Companion document: a complete revised proposal is in `002-search-provider-benchmark.v2.md` (Proposed, revision 2, incorporates this amendment). Codex may either fold A1–A8 into the 002 record or replace that record with the revision-2 text.
- Review basis: frozen benchmark v2 (`docs/benchmark/v2/`, SHA-256 `d7efe922893222b8e60e9847d548190098baedc66f2fb7c1a89402561c9c7c81`), which has 14 eligible editions (8 live, 6 replay; 12 Canada, 2 U.S.).

If this amendment is approved, incorporate it and freeze the revised query file **before** any provider call. Do not treat discussion of this amendment as implementation approval.

---

## A1. Report the small sample honestly

**Where:** "Comparison and scoring", and the report requirements in "Acceptance and verification".

**Add:**

- Lead the written report with a per-edition × provider hit matrix covering all 14 eligible `edition_key` values, split into the 8 live and 6 replay editions, showing whether each provider found that edition in any query's top 10.
- State the small-n caveat in the report: v2 has 8 live eligible editions, so one hit or miss moves live recall by 12.5 points (1/8). Live Canadian recall uses 7 editions (the eighth live edition is Hen Hatch in Delaware), so one event is about 14.3 points.
- Do not name a winner when the difference is one or two editions; report that comparison as inconclusive.

**Rationale:** A gap such as 62% vs 75% is a single event. Recall percentages alone overstate what this sample can decide. The matrix makes that visible.

---

## A2. Use one place per query

**Where:** the Geography row of the frozen-query table, Scope item 2, and the paragraph that justifies the compound regional phrases.

**Replace** the seven geography phrases:

- `Canada`
- `Quebec Montreal`
- `Ontario Toronto Ottawa`
- `Alberta Saskatchewan Calgary Saskatoon`
- `British Columbia Vancouver`
- `Nova Scotia Halifax`
- `United States`

**with** thirteen single-place scopes, in this run order (Canada first, United States last):

`Canada`; `Montreal`; `Quebec City`; `Toronto`; `Ottawa`; `Hamilton`; `Waterloo`; `Calgary`; `Edmonton`; `Saskatoon`; `Vancouver`; `Halifax`; `United States`.

Each English query contains exactly one of these place strings. French queries use the French place forms in A3, still one place per query. Delete the claim that stacked regional keywords are the way to cover cities beyond Montréal and Toronto.

**Rationale:** Strings such as `Alberta Saskatchewan Calgary Saskatoon startup pitch competition finalists upcoming 2026 2027` are not realistic queries and are not an equal test across engines. Keyword indexes (Brave, and Google via Serper) tend to require or weight every term; Exa reads the same string as a fuzzy description. "Identical strings" would therefore quietly favour one engine type.

Hamilton is included because v2 has an eligible replay edition there (McMaster Startup Survivor 2026) with three verified founder cases. Waterloo, Edmonton, and Quebec City are included for Canada-first product coverage, not as known-item denominators: Waterloo appears in v2 only as a past, ineligible edition (Velocity Pitch Competition 2026); Edmonton and Québec City have no v2 opportunities.

---

## A3. Add a French intent family for Québec scopes

**Where:** "Frozen query design proposed for approval". The original text already flags English-only terms as a likely weakness and says that weakness must be reported, not silently tuned away after results. That is not enough.

**Add**, before the first provider call, three French queries for the Montreal scope and three for the Quebec City scope only:

| Dimension | Fixed phrases |
| --- | --- |
| Intent (3) | `concours de pitch startup`; `demo day entrepreneurs`; `concours entrepreneuriat finalistes` |
| Place form | `Montréal`; `Ville de Québec` |
| Time (1) | `à venir 2026 2027` |

No other geography gets French queries in this run. Adding this family before freeze is coverage, not post-hoc tuning.

**Rationale:** Three of v2's 14 eligible editions are in Montréal (live: NEXT AI Open House, UdeM Demoday; replay: Climate Solutions Prize). At least one official page (UdeM Demoday) is in French. The original proposal named this gap but left it unfixed. Fixing it now is cheaper and fairer than discovering it in the results.

---

## A4. Add a non-tech/inclusive intent and drop the replay time mode

**Where:** the Intent and Time rows of the frozen-query table, and the sentence that describes the second time phrase as a probe of replayable 2026 announcements.

**Add** a fourth English intent, in the same short natural keyword style as the original three:

`entrepreneurship competition finalists`

**Drop** the second time mode `2026 finalists`. Keep a single time mode: `upcoming 2026 2027` (and the French equivalent in A3).

**Rationale:** All three original intents read as tech startup events, but v2 intentionally includes social-venture, Indigenous (SOAR), and other non-tech cases. A generic entrepreneurship intent covers them. The replay-only time mode is the weaker of the two: replay scores already must not be presented as what a live user would find, and `upcoming 2026 2027` still retrieves 2026 announcement pages for offline replay scoring. Dropping it keeps the per-provider budget modest after A2 and A3.

---

## A5. Pin locale settings per scope

**Where:** "Comparison and scoring", the sentence "Use the same locale, safety, freshness and search-type settings where comparable; document unavailable or provider-specific controls."

**Replace** that sentence with a frozen locale table, recorded in the query/config file before the first call. Parameter names and enum values must be verified against current official API documentation at freeze time:

| Scope / language | Serper | Brave | Exa |
| --- | --- | --- | --- |
| Canadian scopes, English queries | `gl=ca`, `hl=en` | `country=CA`, `search_lang=en` | no country filter equivalent to Serper/Brave; set `userLocation` to `CA` if the current API supports it |
| Canadian scopes, French queries | `gl=ca`, `hl=fr` | `country=CA`, `search_lang=fr` | `userLocation=CA` if supported; no language parameter has been identified |
| United States, English queries | `gl=us`, `hl=en` | `country=US`, `search_lang=en` | `userLocation=US` if supported |

Do not use date filters, site restrictions, paid enrichment, crawling, or answer-generation options in this comparison. Request a top-10 cutoff with each provider's equivalent count parameter. In particular, Brave's default result count is not 10 and must be set explicitly.

**Rationale:** Locale changes rankings substantially. "Where comparable" leaves the values unpinned and can quietly favour a provider's default, which for several of these APIs is United States / English.

---

## A6. Define recall as both run-level union and per-query

**Where:** the known-event recall@10 bullet in "Comparison and scoring".

**Replace** the implicit single definition with both of the following, and report both:

- **Run-level union recall@10:** an eligible edition is found if an official or event source for that `edition_key` appears in the top 10 of **any** query in the frozen set, divided by eligible editions in scope. This is the primary known-event figure and answers "can this provider find it at all under the budget."
- **Per-query recall@10** and **mean official/event hits per query:** the fraction of queries that surface a given in-scope edition in the top 10, and the average number of distinct in-scope official/event editions in a query's top 10. Also break these out by intent family and by geography.

**Rationale:** Union recall measures coverage; per-query figures measure efficiency. The original text was compatible with union recall but did not say so clearly and did not require the efficiency view.

---

## A7. Pool URL adjudication across providers

**Where:** "Comparison and scoring" (precision/relevance@10) and "Acceptance and verification".

**Add:** Before judging precision or relevance, pool result URLs across all three providers and deduplicate them (normalize enough to collapse trivial duplicates such as scheme or trailing slash, and record the normalization rule). Judge each unique URL once against the recorded rubric. Score every provider against that shared judgment pool. Keep the adjudication log reviewable. Unjudged URLs are never credited as relevant.

**Rationale:** 58 queries × 3 providers × 10 results is up to 1,740 raw hits, with heavy overlap. Judging each provider's list separately wastes effort and can assign the same URL two different labels.

---

## A8. Set a hard spending cap

**Where:** "Dependencies, cost and security", the sentence "Stop before exceeding available credits or an approved spending limit; report partial results rather than silently charging."

**Replace** with:

- Immediately before the run, confirm each provider's current free tier or remaining credit and current pricing from official sources. Do not rely on balances recorded in earlier project documents.
- Hard cap: **US$5 total across all three providers**, including retries, unless Raj approves a higher amount in writing.
- Stop at the cap and report partial results rather than silently charging.
- Do not purchase credits or enable a new paid plan without separate approval.

**Rationale:** 174 planned calls (58 × 3), plus a small retry allowance, should be inexpensive, but a numeric cap is the only enforceable stop.

---

## Resulting query budget if A1–A8 are approved

**58 queries per provider** (still in the modest 40–60 range):

- 4 English intents × 13 geographies × 1 time mode = 52
- 3 French intents × 2 Québec scopes × 1 time mode = 6

The exact strings and the generation rule are in the appendix of `002-search-provider-benchmark.v2.md`. This count is a recommendation to cover Canadian regions, a U.S. fallback, inclusive programs, and French Québec pages under equal conditions; it was not specified in the handoff.

## Deferred and out of scope for this run

These are not part of Amendment A and remain possible later rounds, each requiring its own proposal and approval:

- A provider-native query mode (for example Exa's recommended natural-language style).
- A second full live run, or repeating the live comparison on a later date.

Everything else in the current 002 proposal is unchanged: frozen benchmark checksums before the first call; no benchmark names, domains, person names, or event URLs in queries; saved raw responses and offline rescoring; rotating provider order by query; a separate new-discovery log that does not alter v2 mid-run; live/replay and Canada/U.S. reporting splits; v1 as a separately reported continuity check; no commit, push, deployment, or purchase authorization.
