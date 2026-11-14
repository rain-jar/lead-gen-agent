# 003 — Benchmark v2 (coverage expansion)

- Status: Complete. The user approved freezing v2 and rules R1–R3 on 2026-11-14, and v2 is frozen. Adoption for Slice 2 is not yet approved and belongs to the Slice 2 proposal.
- Proposal depth and reason: Standard. This changes evaluation ground truth, which later provider comparisons depend on. It adds data and validator checks but changes no product behavior.
- Source requirements / milestone: `docs/PROJECT.md` §6 (Evaluation Plan) and §8 (open question on benchmark coverage), `docs/STATUS.md`, `docs/work/001-benchmark-setup.md`, and the frozen `docs/benchmark/v1/`.
- Numbering note: this record is 003 because `STATUS.md` reserves 002 for the Search Provider Benchmark. STATUS.md and PROJECT.md have **not** been edited; reconciling them is left to the repository agent.

## Proposal

### Outcome
A broader, versioned, evidence-backed known-item benchmark (v2). It should make Slice 2 known-event recall meaningful across Canadian geographies and event types while leaving v1 frozen and unchanged.

### Scope
- Add `docs/benchmark/v2/benchmark.json` (frozen 2026-11-14) and `docs/benchmark/v2/README.md`.
- Extend `scripts/validate_benchmark.py` with optional v2 fields and checks that run when `schema_version >= 2`. v1 must still validate unchanged.
- v2 composition:
  - 18 opportunity records, 14 of them eligible editions (12 Canada, 2 U.S.; 8 live, 6 replay).
  - 17 verified founders from 6 editions (max edition share 3/17 = 18%).
  - 8 verified live organizers.
  - 12 negative/ambiguous cases covering all 9 PROJECT.md failure categories.

### Non-goals
- No provider adapters, query families, provider runs, application code, persistence, or paid services.
- No edits to frozen v1, and no edits to `PROJECT.md` or `STATUS.md` until approved.
- No claim of population recall.

### Recommended approach and why
- Keep the v1 JSON + Pydantic approach and add fields only. This keeps the diff reviewable and v1 compatible.
- Use an explicit `split` (live/replay) and `edition_key` so the same edition can be scored in both views without double counting. This enforces event-edition integrity (PROJECT.md D10).
- Make the coverage rules machine-checked rather than relying on reviewer memory:
  - edition share cap of 30%;
  - at least 5 founder editions;
  - at least 3 verified organizers;
  - all 9 failure categories present;
  - live reference date = benchmark date, and replay reference dates are earlier;
  - verified organizers carry contact and audience evidence;
  - verified founders carry newer-founder evidence;
  - duplicates point to their canonical case.
- The validator keeps the v1-style Pydantic API (`validator`, `Config`, `min_items`), so it runs under Pydantic 1 or 2 like the existing script.

### Ground-truth rules applied (approved by the user, 2026-11-14)
- **R1 Presenter:** a finalist entry naming exactly one person, on an official page stating that the finalists pitch or take the stage, names the presenter. Entries naming several people without a designation are `presenter_unknown` (consistent with the v1 Cornell case).
- **R2 Newer founder:** finalist status in a founder competition satisfies newer-founder fit (PROJECT.md example), unless primary evidence shows the venture is established (e.g., a completed institutional Series A). In that case it is `established_founder`.
- **R3 Replay reference date** = the date of the dated public announcement naming the edition, so the event was +7 days to +6 months ahead on that date.

### Future fit / reversal effort
- v2 is frozen, so any change requires a new version (v2.1, v3, ...) and reruns. Per the agreed evaluation protocol, new sets are added roughly weekly and never edit frozen ones.
- The live split ages. A live run on a date other than 2026-11-14 needs either an approximate-results disclaimer or a refreshed live split in a new version.

### Acceptance criteria
1. v1 artifact unchanged (SHA-256 `bb6621d6e9406864ab49d83182a35c8f165c7ea46f4746f9fd08dfb996d1032a`) and still passes the updated validator.
2. v2 passes the validator. Every opportunity and case has an HTTPS source URL, a `checked_date` and an evidence note.
3. At least 5 founder editions, no edition above 30% of verified founders, at least 3 verified organizers with public contact routes, and all 9 negative categories present.
4. The live vs replay split is explicit per opportunity. Canada-first coverage and its shortfalls are documented in the README.
5. Representative malformed variants are rejected by the validator.
6. The user explicitly approves the R1–R3 rules and the freeze of v2. Using v2 in Slice 2 is decided separately in the Slice 2 proposal.

### Verification
- `python3 scripts/validate_benchmark.py docs/benchmark/v1/benchmark.json`
- `python3 scripts/validate_benchmark.py docs/benchmark/v2/benchmark.json`
- Malformed-variant checks: edition cap breach, missing category, non-HTTPS URL, missing `checked_date`, empty sources, live reference-date mismatch, bad `duplicate_of`, organizer without contact, duplicate `edition_key` in a split, verified founder without a person, eligible event outside the window.
- Manual second pass on edition identity, dates, and duplicates before freeze.

## Additional Analysis

### Current findings / affected components
- v1 has 4 eligible editions. All 7 founder positives come from one U.S. edition, and there are 2 negatives (see 001 Results).
- v1's `description` says "This candidate is not frozen" while `status` is `frozen`. This is cosmetic; it is left untouched because v1 is frozen.
- As of 2026-11-14, Canadian live-window events with **named presenters** were not publicly available on the checked official pages. Examples: UBC published a company-only lineup, NEXT AI selects finalists after Nov 24, Startup TNT lists its Top 5 only on LinkedIn, and U of T and Arena finalists come later. Canadian founder positives are therefore replay cases.

### Interfaces / contracts affected
- Benchmark JSON contract: additive optional fields (documented in the v2 README).
- Validator: the founder `person_name` requirement moved from a field validator to the relationship check, so the v2 company-only `presenter_unknown` negative is allowed. v1 behavior is unchanged: v1 still passes, and a missing person on any v1 founder still fails.

### Alternatives considered
- **Edit v1 in place:** rejected, because v1 is frozen.
- **Live-only v2:** not feasible. Too few Canadian live editions publish named presenters by mid-November.
- **Replay-only v2:** loses current-world organizer and timing checks.
- **More founders per edition:** breaks the concentration goal.

### Dependencies
- Python 3.10+ and Pydantic, both already used.
- Case sourcing used web search/fetch only, with no paid APIs. Some sites blocked automated fetches (QueerTech, CNW via curl, which succeeded via a different fetcher, and LinkedIn), so those cases were excluded or sourced elsewhere.

### Risks / costs / deferred work
- Rules R1–R3 (approved 2026-11-14) decide 12 of the 17 founder labels. If R1 is ever revoked, the MRU, SOAR, CSP and Hen Hatch positives would become `presenter_unknown` in a new version, leaving 5 positives from 2 editions.
- Some newer-founder evidence is weak (SOAR, CSP-02/03, San Diego). Venture age was not checked.
- Live founder positives are U.S.-only (3). The next additive set (about early December, per the evaluation protocol in the v2 README) should add Canadian live cases once finalists publish:
  - NEXT AI Montréal after Nov 24;
  - Startup TNT if posted officially;
  - Total Mom Pitch, which plans a Top 5 announcement on Dec 8.
- Replay cases test the retrievability of still-live pages, not historical index state.
- Pages can change or disappear. Freeze soon after approval and keep checked dates.

### Revisit triggers
- A cited source changes or contradicts a label.
- The user revokes R1, R2 or R3.
- Slice 2 shows the live/replay split or the query-to-edition matching is unfair to a provider.

## Security Impact
Not material to this slice. Only public business/event information and necessary names are stored. Contact routes are official forms or published program addresses, and named-staff emails are referenced by page rather than copied. The artifact contains no secrets.

## Evaluation
- **Benchmark/version:** `lead-discovery-v2` `2.0.0`, schema_version 2, status `frozen` (frozen_date 2026-11-14).
- **Baseline:** v1 (frozen) for comparison of coverage. No provider baseline yet.
- **Metrics/scoring rules:** see the v2 README. They cover known-event recall@10 and evidence-page recall@10 (by split, country and type), precision@10, trap exposure and duplicate rate, new discoveries, latency and cost.
- **Pass thresholds:** none for provider selection in this slice.
- **Affected evaluation stages:** discovery now; retrieval, extraction and qualification reuse the same cases later.
- **Replay/live checks:** explicit `split` per opportunity; live reference date 2026-11-14.
- **Case-level evidence location:** `docs/benchmark/v2/benchmark.json` (sources per record).

## Approval

- **User approval / date / proposal revision or scope:**
  - On 2026-11-14 the user asked for a stronger benchmark slice and said to go ahead and try. That authorized drafting.
  - On 2026-11-14 the user explicitly approved the three labelling rules (R1 presenter, R2 newer-founder, R3 replay reference date) and said to freeze this benchmark. Scope: freeze `lead-discovery-v2` `2.0.0` as drafted, with R1–R3 recorded.
- **Conditions / agreed protocol:** On 2026-11-14 the user agreed to the evaluation protocol in the v2 README:
  - add a new set roughly weekly as an additive version;
  - treat each new set as held-out (scored once, never tuned against), after which it may join the tuning pool;
  - judge improvement by the held-out recall trend across several weeks.
- **Not approved:**
  - using v2 in Slice 2 (Search Provider Benchmark), which still needs its own proposal and approval;
  - edits to PROJECT.md/STATUS.md;
  - any commit or push.
- **Separately authorized external actions:** None.
- **Material amendments / renewed approval:** The record was renumbered from 002 to 003 to keep 002 for the Search Provider Benchmark.

## Results

### Actual changes and files (prepared outside the repository; not yet copied into it)
- `docs/benchmark/v2/benchmark.json`: frozen 2026-11-14 (`status: frozen`, `frozen_date`, and `ground_truth_rules` R1–R3 added at freeze; cases unchanged from the reviewed draft). **Frozen SHA-256 `d7efe922893222b8e60e9847d548190098baedc66f2fb7c1a89402561c9c7c81`.**
- `scripts/validate_benchmark.py`: now also accepts the optional v2 fields `frozen_date` and `ground_truth_rules`. For a frozen v2 benchmark it requires `frozen_date`, requires `frozen_date` to be on or after `created_date`, and rejects any rule approved after the freeze. It also rejects `frozen_date` on a non-frozen set. Tested on 3 malformed variants; all 3 were rejected.
- `docs/benchmark/v2/README.md`
- `scripts/validate_benchmark.py`: v2 checks added; v1-compatible.

### Acceptance criteria results / observed evidence
- v1 output: `Valid lead-discovery-replay-v1 1.0.0: 5 opportunities, 12 cases (frozen)`. The v1 SHA-256 is unchanged.
- v2 output: `Valid lead-discovery-v2 2.0.0: 18 opportunities, 37 cases (frozen)`, with 14 eligible (live 8, replay 6; CA 12, US 2), 17 verified founders from 6 editions (max share 3/17), 8 verified organizers, and 12 negative/ambiguous cases.
- All 11 malformed variants listed under Verification were rejected with the expected error.
- Criterion 6 is met: the user approved R1–R3 and the freeze on 2026-11-14.

### Checks not run / uncertainty
- No second independent manual audit pass was done before the freeze; one researcher checked all sources on 2026-11-14.
- The validator was run under Python 3.13 with Pydantic 2.14 only, not with Pydantic 1.
- Venture age was not checked for finalist-only positives.

### Deviations / residual risks / follow-ups
- Live Canadian founder positives: 0 (shortfall explained above).
- Founder geographies are limited to Calgary, Saskatoon, Montréal, Hamilton, Delaware and San Diego.

### Canonical documents updated
- `docs/PROJECT.md`: no. The repository agent should record frozen v2, rules R1–R3 and the evaluation protocol, and close the §8 coverage question. Whether Slice 2 uses v2 is still unapproved.
- `docs/STATUS.md`: no. The repository agent should record this record (003, complete) and keep 002 for the Search Provider Benchmark, which still needs approval.
- Other: v2 README.
