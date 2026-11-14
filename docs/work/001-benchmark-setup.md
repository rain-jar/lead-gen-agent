# 001 — Benchmark Setup

- Status: Complete
- Proposal depth and reason: Standard — the benchmark will govern later search comparisons and must remain independent of the implementation; the work creates data, schema, and validation but does not change product behavior.
- Source requirements / milestone: `docs/PROJECT.md`, `docs/STATUS.md`, and the clean restart handoff dated 2026-11-14.

## Proposal

### Outcome
Create a small, auditable, versioned replay benchmark and validator that can be frozen before search-provider or query tuning. Keep future fresh-live run records separate from this static benchmark.

### Scope
- Define a machine-readable case schema and document its meaning and ground-truth rules.
- Create a manually verifiable v1 set containing eligible event editions, named presenter/founder cases linked to those editions, and negative or ambiguous cases covering the failure modes in `PROJECT.md`. Include Canada and the U.S., Montréal, and varied opportunity categories where credible cases can be verified.
- The handoff sets no numeric benchmark size. Choose a small, manually reviewable case set that provides useful category and geography coverage; report its actual size and coverage before freezing. Do not treat the product output target of 7 founders plus 3 organizers as a benchmark case-count requirement.
- Do not force a case to meet a count when strong public evidence is unavailable. Surface material coverage gaps before freezing.
- Include event-edition identity, expected result at each applicable stage, evidence/source URLs, evidence notes, provenance/check date, and negative/ambiguous reason. Store only public business/event information and necessary names.
- Add schema validation and consistency checks for stable unique IDs, valid references, dates, expected labels, evidence URLs, and required fields by case type.
- Define provider comparison conditions and metrics for Slice 2 before any provider or query tuning.
- Freeze the reviewed artifact as benchmark v1; corrections after freeze require a documented new version and explicit approval.

### Non-goals
- No production discovery pipeline, provider adapters, query tuning, UI, persistence service, or paid service use.
- No live lead target guarantee. This benchmark measures a known subset and cannot establish recall over the unknown full population.
- No importing previous experimental results as ground truth without independently checking every selected case.

### Recommended approach and why
Use JSON for the benchmark artifact and a small Pydantic schema/validator. JSON is easy to review in diffs, handles nested evidence and event-person relationships, and can be strictly validated with the already approved backend model library. YAML is more forgiving to edit but has implicit typing and parser variability; CSV is awkward for linked editions and multiple evidence records. Keep data and validation separate from production query generation.

### Proposed case model
Use a shared stable `case_id`, `case_type`, `expected_judgment`, `sources[]` (URL, source type, checked date, evidence note), and optional `reason` for all cases. Event/person records reference a stable `opportunity_id` so evidence cannot silently join across editions.

An opportunity record should include event/program name, edition label, event date or explicit date status, city/region/country, category, official source evidence, and expected discovery eligibility. A person record should include the actual public name, venture when supported, referenced opportunity edition, expected presenter/founder eligibility, and evidence supporting both the role and newer-founder fit. Negative/ambiguous cases should identify the failure rule and expected non-Verified outcome. Do not collect private contact details for benchmark purposes.

The final schema may use shared records plus references rather than duplicating event facts in each case; it must preserve the edition-specific relationship and support stage-level scoring.

### Ground-truth process
For each case, inspect the cited public source directly and record the date checked and the fact it supports. For people, verify both the named person’s qualifying role and newer-founder fit. For organizers, verify the operator, target audience, in-window date, and public contact route where the organizer case is intended to be eligible. Exclude unsupported cases or label them ambiguous with the exact unresolved criterion. A second pass checks edition identity, duplicates, geography, date window, and source sufficiency before freeze.

Past events may be used in the static replay benchmark only when their edition facts remain independently verifiable; their expected date-window result is evaluated relative to the recorded benchmark reference date. Fresh-live evaluation uses separate run artifacts and the current request date. This avoids treating a now-past event as currently actionable while preserving a stable replay case.

### Versioning and leakage prevention
Store v1 under a canonical benchmark directory with an explicit version and `reference_date`; freeze by recording the reviewed artifact revision/checksum in the work record. Never edit frozen v1 in place. A correction creates v2 (or a clearly documented patch version before tuning begins), preserves the prior artifact, explains the evidence and reason, and requires explicit approval.

Keep benchmark data out of production query generation and provider-specific tuning configuration. During Slice 2, all providers receive the same predeclared query families, query count/equivalent budget, geography sequence, date constraints, and result cutoff. Save dated query and result records. Newly found candidates are recorded separately, manually verified, and are not added to the frozen ground truth during a comparison.

### Slice 2 metrics and fixed comparison plan
- **Known-event recall@10:** eligible benchmark opportunity editions surfaced in a provider’s top 10 results across the same predeclared query set, divided by eligible editions in scope. Report per geography/category and overall; deduplicate results to event edition before scoring. Also report per-query recall where the query-to-case mapping is defined in advance.
- **Precision/relevance@10:** manually judge each unique result in the fixed top-10 cutoff using a recorded relevance rubric; report relevant unique editions divided by judged unique editions. Unknown results remain uncredited until checked.
- **Useful new discoveries:** count unique, independently verified qualifying event editions absent from v1, separately from known-item metrics. Record evidence and do not alter v1 mid-run.
- **Latency:** record wall-clock duration per query and total provider run, including failures; report median and total.
- **Cost:** record actual charge when provider reporting supports it, otherwise a dated estimate using documented request/result pricing. Never imply an estimate is an actual charge.
- **Equal conditions:** same frozen benchmark version, query family and query count, result cutoff, geography/date rules, and equivalent request budget; record unavoidable API/provider setting differences. Run order should be rotated or otherwise recorded to expose time-sensitive index effects.

The exact query families, per-provider request budget, and operational cutoff must be frozen in the Slice 2 proposal before running the comparison; Slice 1 documents metric definitions and leakage rules without using benchmark failures to tune queries.

### Future fit / reversal effort
Stage labels and edition references let later retrieval, extraction, and qualification evaluations share the same independently maintained cases. Changing the schema before freeze is inexpensive; after provider tuning begins, changing case meaning requires versioning and rerunning comparisons.

### Acceptance criteria
1. A canonical, machine-readable v1 candidate artifact and schema documentation exist.
2. Each case has a stable unique ID, explicit expected judgment, provenance/check date, and sufficient evidence to audit that judgment.
3. Eligible event cases identify one specific edition and geography/date; person cases link to that edition and support both actual role and newer-founder fit.
4. Negative/ambiguous cases cover past/out-of-window editions, unidentified presenter, non-qualifying role or founder fit, mismatched editions, incomplete organizer evidence, insufficient evidence, and duplicates, to the extent verifiable examples are available.
5. Replay reference date and future fresh-live separation are explicit.
6. Validation catches malformed records, missing required evidence, broken references, duplicate IDs, and key edition/date inconsistencies.
7. Slice 2 metrics, result cutoff, comparison constraints, cost/latency recording, and new-discovery handling are documented before provider tuning.
8. v1 is reviewed and explicitly frozen; any unavailable source, count shortfall, or ambiguity is recorded rather than hidden.
9. No provider implementation, production query generation, or unrelated application code is added.

### Verification
- Run focused schema/validator checks on valid cases and representative malformed/inconsistent cases.
- Manually revisit every source and expected judgment, including event-edition identity and reference-date logic.
- Check benchmark cases are not embedded in production query generation or provider tuning code.
- Review the complete diff and record actual counts, case coverage, checks run/not run, unresolved ambiguity, and freeze identifier.

## Additional Analysis

### Current findings / affected components
The workspace currently contains only the documentation package; there is no application code, repository configuration, or Git metadata to extend. `PROJECT.md` and `STATUS.md` already record Stages 1–4 as covered, Stage 5 as not started, the current milestone, and the proposed next slice. No product contradiction was found between those documents and the handoff. This proposal adds detail to the existing Slice 1 record.

### Alternatives considered
- **CSV:** simple for flat rows, but poorly represents multiple sources and event-to-person edition references.
- **YAML:** readable, but implicit typing and parser differences make strict validation less predictable.
- **JSON (recommended):** portable, diffable, and straightforward to validate with Pydantic.
- **JSONL:** useful for streaming very large datasets; unnecessary for a small manually reviewed v1.

### Dependencies
- No paid service or API credentials are needed for benchmark construction.
- Public sources can be inspected manually. If web search is used to locate cases, record its role as case sourcing only; it must not become provider benchmark tuning.
- No implementation commands are configured in this documentation-only workspace.

### Risks / costs / deferred work
- **Stale events:** keep a fixed replay reference date and separate fresh-live run data.
- **Leakage/overfitting:** freeze cases and query families before provider comparison; keep ground truth outside production query generation.
- **Ambiguous ground truth:** exclude unsupported positives or mark them ambiguous with a specific reason.
- **Category/geography imbalance:** deliberately sample multiple opportunity types and Canada/U.S.; disclose actual distribution.
- **Small/incomplete set:** report known-item recall as limited evidence, not population recall; credit new discoveries separately after verification.
- **Source changes:** record check dates and preserve enough citation detail to recheck; version corrections rather than silently editing frozen cases.
- **Case set feasibility:** a small set may have uneven coverage; disclose its size and composition and do not lower evidence standards to reach an arbitrary count.

### Revisit triggers
- A cited source disappears or evidence disproves a ground-truth label.
- Slice 2 identifies a material coverage gap, ambiguous scoring rule, or unfair provider comparison.
- Later stage evaluation needs an additional field that cannot be represented without changing case meaning.

## Security Impact
Not material to this slice. Benchmark artifacts use public business/event information, avoid private contact data, and contain no secrets. Any external search used for case sourcing is a trust boundary; validate facts against cited primary/official sources before inclusion.

## Evaluation
- Benchmark/version: frozen `lead-discovery-replay-v1` (`1.0.0`), with per-opportunity replay reference dates.
- Baseline: none; v1 establishes the known-item baseline for later provider comparison.
- Metrics/scoring rules: known-event recall@10, manually judged precision/relevance@10, independently verified new discoveries, latency, and actual or explicitly estimated cost.
- Pass thresholds: no provider winner threshold in Slice 1; Slice 2 must interpret results against the frozen case set and disclose limitations.
- Affected evaluation stages: discovery immediately; data model supports retrieval, extraction, and qualification diagnostics later.
- Replay/live checks: static v1 replay cases; separate fresh-live run artifacts.
- Case-level evidence location: proposed benchmark artifact and linked sources, to be chosen within the canonical repository after its location is established.

## Approval

- User approval / date / proposal revision or scope: Approved by user on 2026-11-14 to begin Slice 1 under the revised proposal. User approved a v1 target composition of 7 eligible founder cases and 3 eligible organizer cases, plus negative/ambiguous cases. User also approved historical replay cases and one fixed reference date per opportunity. These are benchmark design choices, distinct from product run requirements.
- Conditions: None.
- Separately authorized external actions: None.
- Material amendments / renewed approval: None.

## Results
### Actual changes and files
- Added and froze `docs/benchmark/v1/benchmark.json` with 7 founder positives, 3 organizer positives, and 2 negative cases. SHA-256: `bb6621d6e9406864ab49d83182a35c8f165c7ea46f4746f9fd08dfb996d1032a`.
- Added `docs/benchmark/v1/README.md` documenting per-opportunity replay dates, scope, provenance, and limitations.
- Added `scripts/validate_benchmark.py` using Pydantic to validate record shape, required fields, sources, IDs, references, and per-opportunity date-window consistency.
- Updated `docs/PROJECT.md` and `docs/STATUS.md` with the frozen v1 state, current milestone, and coverage limitation.

### Acceptance criteria results / observed evidence
- Ran `python3 scripts/validate_benchmark.py docs/benchmark/v1/benchmark.json` after freezing: passed. Output: `Valid lead-discovery-replay-v1 1.0.0: 5 opportunities, 12 cases (frozen)`.
- Seven founder cases use the dated San Diego Startup Week Founders Fight Club announcement. It was posted October 28, identifies each named founder as pitching, and gives the event date as November 6, 2026. The reference date is October 28, so the event is nine days ahead.
- Organizer positives cover Startup San Diego, University of Toronto Entrepreneurship (March 4, 2027), and Innovation Factory, which runs the Synapse Life Science Competition (March 24, 2027). Their event dates, qualifying startup audiences, operator identity, and public contact routes are recorded in the artifact.
- Negative cases cover a named pitcher at an event only four days after its November 14 reference date, and a Cornell finalist founder whose individual presenter role is not established by the cited official page.
- The founder positives currently all come from one U.S. event edition. This is a narrow replay sample and is disclosed in the benchmark README; it does not establish broad discovery recall.
- Sources inspected: [San Diego Startup Week finalist announcement](https://startupsd.org/news/founders-fight-club-finalists-sdsw2026/), [Startup San Diego contact page](https://startupsd.org/contact/), [U of T Desjardins Startup Prize](https://entrepreneurs.utoronto.ca/for-entrepreneurs/desjardins-startup-prize-2027/), [Synapse Life Science Competition](https://synapselifescience.com/apply/), [McMaster Startup Survivor](https://theforge.mcmaster.ca/pitchcompetition/), [Cornell Mark Mobius Pitch Competition](https://business.cornell.edu/centers/ccem/conference/pitch-competition/).

### Evaluation results
- No provider benchmark run. Benchmark ground truth v1 is frozen and ready for the separately approved provider-comparison slice.

### Checks not run / uncertainty
- The validator's schema and relationship checks passed. A separate edge-case test suite for malformed/inconsistent samples has not been run.
- The case-level manual source audit has been completed. The benchmark is small and the founder positives share one event edition; report known-event recall as limited evidence.
- No provider benchmark or fresh-live discovery run has been performed.
- The founder set is concentrated in one event edition; broader geography/category coverage may require adding cases in a separately approved benchmark revision.

### Deviations / residual risks / follow-ups
- The user's size approval governs the frozen positive-case composition. Case evidence and event-edition integrity remain mandatory.
- Historical replay reference dates differ by opportunity, as approved by the user. Fresh-live evaluation remains separate.
- Do not edit frozen v1 in place. A ground-truth correction requires approval and a new version. Revisit wider founder case diversity if Slice 2 results show the current event coverage unfairly affects provider comparison.

### Canonical documents updated
- `docs/PROJECT.md`: yes — records the frozen v1 composition and coverage limitation.
- `docs/STATUS.md`: yes — records Slice 1 complete and the frozen artifact state.
- Other: `docs/benchmark/v1/README.md`, `docs/benchmark/v1/benchmark.json`, `scripts/validate_benchmark.py`.
