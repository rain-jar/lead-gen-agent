# Lead Generation MVP — Project Definition

- Last updated: 2026-11-14
- State: Stages 1–4 covered for the current milestone; Stage 5 implementation not started
- Canonical principle: approved product/system direction does not imply blanket approval to implement roadmap slices

## 1. Problem and Evidence

### Product / problem
A Montréal public-speaking coach needs a lower-effort way to discover timely, high-quality prospects who have a concrete near-term reason to improve their public speaking.

The current workflow is largely manual: Google, LinkedIn, Eventbrite, referrals, networking, and related research. It consumes meaningful time and produces inconsistent lead discovery.

### Primary user
Initial user: a Montréal-based public-speaking coach.

### Demand evidence
- The coach has explicitly said he is interested in finding good-quality leads in a more automated fashion.
- Manual lead discovery takes meaningful time.
- A third party previously proposed an AI-based solution at approximately $2,000, but the cost was impractical.

This establishes a real workflow, explicit demand, and a strong cost constraint.

### Desired outcome and success metrics
Long-term product behavior: provide a fresh weekly digest of strong, timely leads.

Current milestone target: prove one complete fresh discovery run can produce:
- 7 verified founder leads;
- 3 verified organizer leads;
- at least 6 of 10 verified leads judged genuinely outreach-worthy by the coach, when 10 verified leads are available.

Primary quality metric:

`outreach_worthy_rate = useful_verified_leads / verified_leads_reviewed`

Initial target: `>= 60%`.

Long-term aspiration: increase the outreach-worthy rate toward 100% without weakening verification criteria.

Keep technical validity and customer usefulness separate:
- **Verified lead completion** — did the system satisfy the evidence/eligibility rules and produce the target mix?
- **Coach usefulness** — would the coach actually consider contacting the lead?

No reliable baseline for current manual research time has been measured yet. Do not invent one.

---

## 2. Vision and Current Scope

### Testable MVP hypothesis
A bounded, evidence-driven discovery pipeline can independently find timely, verifiable prospects without the user supplying event names or URLs, and can produce a useful shortlist at very low operating cost.

Evidence supporting the hypothesis:
- one fresh run discovers up to 7 verified founders + 3 verified organizers under the agreed rules;
- no weak leads are added merely to hit 10;
- at least 60% of reviewed verified leads are marked useful when 10 are available;
- failures can be attributed to discovery, retrieval, extraction, qualification, ranking, or final usefulness rather than remaining opaque;
- actual run cost and latency are recorded.

Evidence challenging the hypothesis includes persistent inability to surface known eligible opportunities under a reasonable search budget, systematically poor qualification precision, or low coach usefulness despite technically valid leads.

### Narrow MVP segment
The first validation segment is intentionally narrow:
- newer founders preparing to pitch or publicly present at a specific upcoming opportunity;
- organizers of pitch events, demo days, showcases, entrepreneurship programs, or similar opportunities serving newer founders.

This is a validation segment, not the permanent product market.

### Architecture intent
The system should avoid coupling the core pipeline to this one coach or one ICP. Where practical, customer-specific discovery/qualification rules should live in a profile/configuration or clean domain boundary.

Target reusable shape:

`Request → Discover → Gather evidence → Extract → Qualify → Rank → Present → Review`

Do **not** build a generic lead-generation platform now. Design for reasonable configurability, not speculative abstraction.

### Current milestone
Prove one end-to-end discovery run can produce the target shortlist with traceable evidence and measurable usefulness.

Weekly repeatability is a later milestone after one-run feasibility is proven.

### MVP geography
1. Search Canada first, including Montréal.
2. Use the United States only to fill shortfalls in either lead pool.
3. Tech and non-tech sectors are eligible.

### Opportunity date window
Qualifying event/opportunity date must be:
- at least 7 calendar days after the discovery request date;
- no more than 6 calendar months after the request date.

User-facing phrase “Top leads for this week” means “run discovery fresh now and produce the current digest.” It does not restrict event dates to the next seven days.

“Up-to-date” means discovery is executed fresh at request time against currently available sources.

### Founder verification rule
A founder is **Verified** only when:
1. an official source names the actual person as pitching/presenting/participating in a qualifying role at a specific upcoming event edition; and
2. evidence supports fit with the newer-founder audience, e.g. student founder, early-stage venture, accelerator participant, competition finalist, or participant in a program for newer entrepreneurs.

A company-only lineup may support discovery of an event but does not verify an individual presenter.

### Organizer verification rule
An organizer is **Verified** only when official evidence establishes:
- who operates/runs the event or program;
- the program supports newer founders;
- an in-window upcoming event date;
- a public organizer contact route.

A promising upcoming organizer/event with unresolved required fields may appear as **Provisional**, but Provisional rows do not count toward the 3 verified-organizer target.

### Event-edition integrity
Evidence across multiple pages must refer to the same event edition. Never combine a presenter from one edition with the date/contact/organizer of another.

Create an internal opportunity/event entity before final lead qualification so evidence can be attached to a specific edition.

### Desired output
For each lead, when supported:
- name;
- lead type (Founder / Organizer);
- venture/company/organization;
- why selected;
- associated event/opportunity;
- event date;
- location;
- sector;
- public contact route;
- verification status;
- source links/evidence;
- review state.

CSV export is sufficient for the pilot; a lightweight visual results view is also in scope.

### Failure behavior
Never weaken criteria or fabricate records to reach 10. If fewer than 10 verified leads exist, return fewer and explain the shortfall.

### MVP non-goals
Unless separately approved:
- CRM integration;
- automated email/LinkedIn outreach;
- outreach sequencing;
- scheduled recurring jobs;
- feedback-driven retraining/reranking;
- vector database;
- graph database;
- generic agent framework;
- unrestricted autonomous browser agent;
- complex/distributed job queues;
- enterprise multi-tenancy;
- advanced authentication system;
- generalized multi-industry UI;
- large design system.

### Budget / cost posture
Extremely low-cost MVP. Prefer free-tier usage where it does not compromise credible evaluation. Track actual API cost per benchmark/run where practical. Purchasing/upgrading services requires explicit approval.

Known context:
- approximately $4 of Brave Search API credit is available;
- Exa, Brave, and Serper are the initial search candidates;
- TinyFetch is the intended default retrieval layer;
- Firecrawl is the advanced fallback.

Exact monthly operating budget and production SLA are not yet fixed because current milestone is one-run validation.

---

## 3. Experience

### Core user journey
1. User opens the app.
2. User requests a fresh “Top leads for this week” digest.
3. System executes fresh bounded discovery.
4. System returns ranked, reviewable results.
5. User inspects reasons/evidence/contact routes.
6. User marks each lead Useful or Not useful.
7. User may export the result set to CSV.

### Result actions / CTAs
MVP-level actions may include:
- View source/evidence;
- Contact via public route when available;
- Mark Useful / Not useful;
- Export CSV.

No automated outreach in the MVP.

### Review state
Each lead can be marked:
- Useful;
- Not useful.

This review state provides the primary customer-quality metric.

A future V2 may allow a user to trigger a new run after reviewing all leads, potentially using feedback to influence later discovery/ranking. That behavior is deferred and not approved for MVP implementation.

### Required user states
When relevant, the app should support:
- loading/discovery-in-progress;
- successful result set;
- fewer-than-10 result shortfall with explanation;
- retrieval/search/provider failure;
- empty result state;
- export success/failure;
- review-state persistence once that slice is implemented.

### Frontend scope
A lightweight web UI is approved in principle. Exact frontend framework is unresolved and should be selected just in time when the UI slice requires it.

---

## 4. System and Constraints

### Approved conceptual architecture

`Request`
→ `Discovery`
→ `Evidence Retrieval`
→ `Extraction`
→ `Qualification`
→ `Ranking / Digest Assembly`
→ `Presentation`
→ `Human Review`

The stages should remain separable enough that quality/failure can be diagnosed at each boundary.

### Backend
Approved:
- Python
- FastAPI
- Pydantic for structured contracts/models

### Discovery strategy
Discovery is bounded and domain-specific, not generic “find interesting founders” web search.

Current opportunity categories include:
- startup pitch competitions;
- demo days;
- accelerator demo days;
- founder showcases;
- entrepreneurship competitions;
- university entrepreneurship events;
- startup finals;
- venture showcases;
- incubator/accelerator events;
- comparable founder presentation opportunities.

These categories should inform query families. Query strategy should remain inspectable and reproducible.

Illustrative query shapes only (not frozen benchmark queries):
- `"startup pitch competition" Canada <year>`
- `"demo day" founders Montreal`
- `"pitch finalists" accelerator Canada`
- `"entrepreneurship showcase" upcoming founders`

### Search provider abstraction
Approved architecture intent: small provider boundary conceptually equivalent to:

`SearchProvider.search(query, options) -> normalized ranked search results`

Normalize only fields downstream logic needs. Do not over-generalize provider APIs.

### Search provider decision
Final provider is **unresolved pending benchmark evidence**.

Initial providers to compare fairly:
- Exa — current favorite/hypothesis;
- Brave Search API — existing credits and low-cost independent index;
- Serper — Google-backed challenger, useful for obscure/site-specific discovery.

The benchmark, not preference or vendor marketing, decides primary/fallback selection.

### Retrieval/extraction technology
Approved intended hierarchy:

1. **TinyFetch default** for ordinary/dynamic page retrieval because of favorable cost and sufficient retrieval capability at MVP scale.
2. **Firecrawl advanced fallback** where evidence shows it is justified, including difficult JS behavior, PDF parsing, structured schema extraction, crawling, browser interaction, or cases TinyFetch cannot retrieve reliably.

Do not route all pages through Firecrawl merely because it is more feature-rich. Optimize the combined tradeoff of capability, reliability, and cost.

Do not benchmark TinyFetch vs Firecrawl prematurely unless retrieval failures make that comparison consequential.

### Extraction strategy
Hybrid approach:
- deterministic parsing/code for structurally obvious facts;
- LLM interpretation where semantic judgment is genuinely useful.

Potential LLM tasks:
- determine whether a named person is actually presenting;
- interpret whether a program serves newer founders;
- extract evidence from irregular prose;
- resolve ambiguous contextual relationships.

LLM outputs must be structured/validated. An LLM assertion alone is not evidence; source material must remain traceable.

### Qualification strategy
Prefer deterministic enforcement for strict rules, including:
- date window;
- geography order;
- required fields;
- event-edition matching;
- Verified/Provisional/Rejected state rules;
- duplicate handling;
- founder/organizer target counts;
- evidence requirements.

Use LLM judgment only for semantic interpretation that deterministic rules cannot reliably perform.

### Ranking
Only sufficiently qualified candidates enter final ranking.

Initial ranking may consider:
- timing;
- ICP fit;
- evidence strength;
- contactability;
- opportunity relevance.

Keep ranking explainable. No ML ranking system is required for the MVP.

### Opportunity/event model
Exact schema is not yet approved, but the domain model must preserve event-edition identity. Likely concepts include:
- event/program name;
- edition/year;
- event date;
- geography/location;
- organizer;
- official source URLs;
- presenter evidence;
- program/audience evidence.

Lead records should reference the relevant opportunity/event.

### LLM/model
Exact model/provider is unresolved. Keep a model/provider boundary. Select a specific model only when an approved slice requires it and record rationale/cost.

### Persistence
A small persistence layer will eventually be needed for:
- discovery runs;
- lead records;
- evidence;
- review state.

Exact database is unresolved and should be selected just in time when persistence becomes necessary.

### Hosting / auth / deployment
Unresolved and deferred until a slice requires them. Do not prematurely select production hosting, auth strategy, or deployment architecture.

### Privacy / data posture
Operate primarily on publicly available business/event information.
- Do not seek private contact information.
- Publicly published business contact routes are acceptable.
- Minimize collected personal information.
- Keep secrets in environment/approved secret management and out of source/logs/examples.

### Main technical risk
Top-of-funnel discovery remains the highest-risk unknown. The first implementation work therefore validates the benchmark and search-provider performance before investing in the full application.

---

## 5. Decisions and Assumptions

| ID | Decision or assumption | State | Rationale / future fit | Switching cost | Revisit trigger |
| --- | --- | --- | --- | --- | --- |
| D01 | Initial user is a Montréal public-speaking coach | Approved | Gives a real user/workflow for validation | Low | New pilot/customer |
| D02 | MVP lead segment = newer founders preparing for pitches + relevant organizers | Approved | Crisp, time-sensitive, verifiable test segment | Low–Medium | MVP succeeds or evidence shows segment is too sparse |
| D03 | Narrow validation scope must not deeply hard-code the core pipeline | Approved | Supports future reuse without building generic platform now | Medium | Core boundaries prove artificial/expensive |
| D04 | First milestone = prove one fresh end-to-end run before weekly repeatability | Approved | Smallest credible product proof | Low | First run succeeds |
| D05 | Target = 7 verified founders + 3 verified organizers | Approved | Concrete pilot target | Low | User/pilot requirement changes |
| D06 | Initial coach-quality threshold = >=60% Useful among reviewed verified leads | Approved | Measures commercial usefulness separately from technical validity | Low | Pilot feedback suggests different threshold |
| D07 | Canada first, U.S. fallback; tech and non-tech eligible | Approved | Matches user context while preserving enough supply | Low | Discovery supply proves insufficient |
| D08 | Qualifying opportunity window = +7 days through +6 months | Approved | Provides actionable lead time | Low | User changes outreach timing |
| D09 | No padding weak leads to reach 10 | Approved | Protects quality/integrity | Low | None expected |
| D10 | Same-event-edition evidence integrity is mandatory | Approved | Prevents false joins across years/editions | Medium | None; core correctness rule |
| D11 | Basic UX = fresh digest → review → Useful/Not useful → CSV | Approved | Sufficient for pilot | Low | User needs richer workflow |
| D12 | Backend = Python + FastAPI + Pydantic | Approved | Simple, testable, appropriate for data/LLM pipeline | Medium | Material technical limitation |
| D13 | Core pipeline stages remain separable for diagnostics | Approved | Needed for credible evaluation and debugging | Medium | Proven unnecessary complexity |
| D14 | Search provider is abstracted behind a small adapter | Approved | Allows fair provider comparison/replacement | Low–Medium | One provider becomes fixed for strong reason |
| D15 | Search benchmark candidates = Exa, Brave, Serper | Approved for evaluation | Current cost/quality candidates; winner not preselected | Low | Provider unavailable/pricing materially changes |
| D16 | Final primary/fallback search provider | Unresolved | Must be selected from benchmark evidence | — | Slice 2 results |
| D17 | TinyFetch default retrieval; Firecrawl advanced fallback | Approved intent | Optimizes capability/reliability/cost | Low–Medium | Measured extraction failures/cost change |
| D18 | Hybrid deterministic + LLM extraction/qualification | Approved | Strict rules stay deterministic; semantic ambiguity uses LLM | Medium | Evaluation shows another split is superior |
| D19 | Exact LLM/model | Unresolved | Not needed yet | — | First slice requiring LLM |
| D20 | Exact frontend framework | Unresolved | UI not needed for early benchmark slices | — | UI slice begins |
| D21 | Exact database | Unresolved | Persistence not needed for early benchmark slices | — | Persistence becomes necessary |
| D22 | Hosting/auth/deployment | Deferred | Premature for one-run validation | — | Pilot UI/deployment slice |
| D23 | Recurring scheduling | Deferred | Weekly repeatability comes after one-run proof | Low | End-to-end validation succeeds |
| D24 | Feedback-driven rerun/learning | Deferred V2 | Useful but not required for MVP proof | Medium | Review loop produces sufficient data |

---

## 6. Evaluation Plan

Evaluation must be agreed/frozen before significant discovery tuning. Benchmark and scoring stay independent of implementation.

### Benchmark purpose
Normal product runs receive **no event seed list**.

Evaluation uses a separate, versioned ground-truth/seed set.

Therefore:
- no seed list as product input;
- yes seed list as evaluation ground truth.

### Benchmark categories
At minimum:

#### A. Known eligible opportunities/events
Known upcoming or replayable event editions that fit the discovery scope.

Question: can search surface the relevant event/source?

#### B. Known eligible people
Actual presenters/founders associated with known eligible event editions.

Question: after event discovery, can retrieval/extraction locate the correct person and evidence?

#### C. Negative / ambiguous cases
Examples that should not become Verified, such as:
- past edition;
- company named but actual presenter unknown;
- event outside date window;
- speaker but not pitching/presenting;
- established founder outside intended audience;
- mismatched edition evidence;
- organizer without qualifying upcoming event;
- insufficient evidence;
- duplicates.

### Search provider benchmark
Compare Exa, Brave, and Serper under comparable conditions:
- same benchmark version;
- same query families;
- same query count/equivalent budget;
- same geography/date constraints;
- same result cutoff where practical.

Measure at minimum:
- known-event recall@K;
- useful newly discovered candidates (after verification);
- precision/relevance at a fixed cutoff where practical;
- latency;
- estimated/actual API cost.

Document any provider differences that make direct comparison imperfect.

Frozen benchmark v2 (`docs/benchmark/v2/`, work record 003) expands the known-item set to 14 eligible editions, including 12 Canadian editions. It has separate live and historical replay splits. Slice 2 must choose its benchmark version in its own proposal and report the two splits separately; replay retrieval is not evidence of present-day discovery. V1 remains frozen for continuity.

For Slice 2, the revised 58-query comparison set is frozen in `docs/benchmark/search-provider/queries-v1.tsv` (work record 002), with a US$5 total spending cap. This freezes the evaluation queries, not the eventual product query strategy. Provider implementation and API calls remain a separate approval step.

The approved v2 ground-truth rules are: R1, a single named finalist on an official page saying finalists pitch or present counts as the presenter; R2, founder-competition finalist status supports newer-founder fit absent contrary primary evidence of an established venture; and R3, a replay reference date is the dated public announcement of that edition. These rules and their exact wording are recorded in the frozen v2 artifact.

For ongoing evaluation, add a separately versioned set roughly weekly as qualifying events publish. Score each new set once as held out before using it for tuning, and judge performance by the held-out trend across several weeks. Never edit a frozen set in place. This protocol can add live Canadian founder positives when public evidence becomes available; v2 itself contains none.

### Stage diagnostics
Evaluate separately:
1. **Search/discovery** — did search surface the relevant event/source?
2. **Evidence retrieval** — once discovered, did retrieval obtain the page containing required evidence?
3. **Extraction** — were the correct person/event/date/company/organizer/contact/evidence fields extracted?
4. **Qualification** — did the system correctly classify Verified / Provisional / Rejected?
5. **Ranking/output** — did a qualifying lead survive ranking and appear in the digest?
6. **User usefulness** — did the coach mark it Useful?

Preserve case-level failure reasons.

### New discoveries
The full population is unknown, so known-item recall is limited. Newly discovered candidates may be legitimate successes if independently verified. Record them separately; do not silently add them to the benchmark mid-run.

### Replay vs live checks
Where practical:
- save dated queries/settings/ranked results for replay/comparison;
- run fresh live searches separately to assess current performance.

Do not equate replay performance with live discovery quality.

### Ground-truth governance
- Version the benchmark.
- Freeze a version before tuning against it.
- Evidence-back every case.
- Record provenance/date.
- Ground-truth corrections require explicit documented approval.
- Do not silently alter cases after seeing model/provider failures.

### End-to-end milestone acceptance
For the current milestone, success ultimately requires:
- a fresh live run;
- up to 7 Verified founders + 3 Verified organizers under the agreed rules;
- no padded weak leads;
- >=60% Useful among reviewed verified leads when 10 verified leads are available;
- stage-level failure visibility;
- recorded latency and API cost.

---

## 7. High-Level Implementation Roadmap

These slices define the planned build path. They are **not blanket implementation approval**. Each requires its own work record/proposal and explicit approval.

### Slice 1 — Benchmark Setup
- Create versioned benchmark artifact.
- Include known eligible events, known eligible people, and negative/ambiguous cases.
- Define case schema, scoring rules, metrics, leakage prevention, and validation checks.
- Freeze v1 before tuning.

### Slice 2 — Search Provider Benchmark
- Implement minimum common search adapter.
- Add Exa, Brave, and Serper adapters.
- Run equal-condition benchmark.
- Measure recall/relevance, useful new discoveries, latency, and cost.
- Select primary/fallback search provider based on evidence.

### Slice 3 — Opportunity Discovery
- Implement bounded query-family generation.
- Discover candidate events/opportunities.
- Normalize/deduplicate event editions.
- Enforce Canada-first/U.S.-fallback search sequencing.

### Slice 4 — Evidence Retrieval
- Fetch candidate pages.
- Use TinyFetch by default.
- Escalate to Firecrawl only when justified.
- Preserve source URLs and event-edition evidence relationships.

### Slice 5 — Structured Extraction
- Extract people, ventures, organizers, dates, locations, sectors, contacts, and evidence.
- Produce validated structured records.
- Preserve source traceability.

### Slice 6 — Qualification
- Implement Founder and Organizer rules.
- Implement Verified / Provisional / Rejected states.
- Enforce event-edition integrity, date/geography rules, required evidence, and deduplication.

### Slice 7 — Ranking and Digest Assembly
- Rank qualified candidates using explainable factors.
- Assemble 7 Founder + 3 Organizer target when enough verified candidates exist.
- Never pad weak results.

### Slice 8 — User-Facing Results
- Build lightweight web UI.
- Trigger fresh digest.
- Show reasons, evidence, event/contact information, and status.
- Add CSV export.

### Slice 9 — Review State
- Add Useful / Not useful review control.
- Persist review state.
- Compute outreach-worthy rate.
- Do not implement automatic learning from feedback yet.

### Slice 10 — End-to-End Validation
- Run frozen benchmark and fresh live discovery.
- Measure target completion, usefulness, stage failures, latency, and cost.
- Produce release-readiness assessment for pilot.

### Slice 11 — Pilot Hardening
Only after core behavior works:
- focused retries/backoff;
- error handling;
- logging/observability;
- rate-limit handling;
- minimal deployment/operational safeguards;
- repeated-run readiness.

Do not add speculative infrastructure beyond observed needs.

---

## 8. Open Questions and Deferred Work

| Question / deferred item | Why deferred | Evidence / trigger needed |
| --- | --- | --- |
| Benchmark coverage beyond v2 | V2 adds Canadian editions and a weekly held-out protocol, but has no live Canadian founder positives as of its 2026-11-14 freeze | Revisit as named presenters publish and held-out trend accumulates |
| Slice 2 query families and K/budget | Frozen in work record 002: 58 queries per provider, top 10, US$5 total cap | Revisit only with Raj's approval before a revised comparison |
| Final search provider + fallback | Empirical decision | Slice 2 benchmark results |
| Exact LLM/model | Not needed for benchmark setup/search provider test | First extraction/semantic qualification slice |
| Exact frontend framework | UI not needed yet | Slice 8 proposal |
| Exact database | Persistence not needed yet | First slice requiring durable state |
| Hosting/environment | Premature for validation | UI/pilot deployment proposal |
| Authentication | Single-user pilot may not require it initially | Deployment/user-access requirements |
| Exact ranking weights | Need qualified data first | Slice 7 evidence |
| TinyFetch vs broader Firecrawl usage | Only consequential if default retrieval fails materially | Slice 4 failure evidence |
| Weekly scheduler | Repeatability not yet proven | Successful Slice 10 |
| Feedback-driven rerun/learning | V2 | Sufficient review data + explicit proposal |
| Manual research-time baseline | Not measured | User measurement if ROI analysis becomes necessary |

---

## 9. Security and Data Constraints

- Use only public web/business/event information for lead discovery unless explicitly approved otherwise.
- Do not discover or infer private contact information.
- Do not store unnecessary personal data.
- Validate external/LLM data at trust boundaries.
- Keep all API keys and secrets out of source, logs, benchmark artifacts, and examples.
- Search/retrieval providers are external trust boundaries; sanitize/validate their outputs before use.
- Any later security-related change must include the Security Impact section required by `AGENTS.md`.

---

## 10. Definition of Done for Current Milestone

The milestone is not complete merely because code exists.

Completion requires observed evidence that:
1. benchmark/evaluation framework is versioned and independently maintained;
2. search provider choice is evidence-based;
3. discovery can run without user-supplied event seeds;
4. evidence remains tied to correct event editions;
5. qualification rules are enforced and traceable;
6. a fresh live run returns only legitimately qualifying leads, up to the 7/3 target;
7. no weak leads are padded into the result set;
8. coach review produces a measurable usefulness rate;
9. stage-level failures, latency, and cost are recorded;
10. relevant automated/manual checks pass and residual uncertainty is documented.
