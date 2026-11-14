# 004 — Amendment: Lead mix: founder-first, organizer fill

- Status: **Applied to canonical docs on 2026-11-14**, under Raj's explicit approval of the 004 amendment and one Slice 2 documentation commit. No product mix implementation or push is authorized by this amendment alone.
- Proposal depth and reason: Standard — this changes an approved product target (D05) and the weekly digest assembly rule, and it records evidence that later slices must respect. It does not implement pipeline behavior.
- Source requirements / milestone: `docs/PROJECT.md` §§1–2, 4–7, 10 (especially D05, D09, D23, Slice 7, and the 7/3 acceptance language); `docs/STATUS.md`; founder-reachability spikes in `artifacts/search-provider/20261114T131952Z/judgments/founder_reachability_spike.md` and `founder_reachability_replay.md`.
- Applies to: the fixed weekly target of 7 verified founders + 3 verified organizers, and to later Discovery / Evidence Retrieval / Extraction / Presentation design. It does not change frozen benchmarks v1 or v2.

If this amendment is applied, replace the fixed 7+3 mix in canonical product docs **before** any dependent slice is implemented. Do not treat discussion of this amendment as implementation approval, and do not start Slice 3 until its own proposal is approved.

---

## L1. Founder-first list assembly, organizers fill the gap

**Where:** `docs/PROJECT.md` current milestone target (§1), MVP hypothesis (§2), organizer verification wording that refers to “the 3 verified-organizer target,” qualification “founder/organizer target counts,” D05, end-to-end acceptance (§6), Slice 7 assembly rule, Definition of Done item 6; `docs/STATUS.md` milestone line, Stage 2 coverage, and Current Reality target.

**Replace** the fixed weekly target “7 verified founders + 3 verified organizers” with this assembly rule:

- Each weekly digest has **10 slots**.
- **Verified founders fill first, up to 7.**
- **At least 2 organizer slots are always reserved.** Default minimum is **2**, and the minimum is configurable. Reserved means those slots are not filled with extra founders; it does not invent organizers when none are verified.
- **Verified organizers fill the remaining slots,** including any unused founder slots and the reserved organizer slots.
- **Never pad.** If fewer than 10 verified leads exist, the list is shorter and the report states the shortfall and the founder/organizer split. Provisional rows still do not count toward verified slots.

Worked examples (assuming the default minimum of 2 organizer slots):

| Available verified founders | Available verified organizers | Digest |
| --- | ---: | --- |
| 7+ | 3+ | 7 founders + 3 organizers |
| 7+ | 2 | 7 founders + 2 organizers (9 rows; do not pad) |
| 7+ | 1 | 7 founders + 1 organizer (8 rows) |
| 4 | 10 | 4 founders + 6 organizers |
| 0 | 10 | 10 organizers |
| 9 | 1 | 7 founders + 1 organizer (8 rows; the reserved organizer slot stays empty) |

**Where the rule lives in the pipeline:** implement it as **deterministic code in Presentation / digest assembly (Slice 7)**. Qualification and Ranking do not change their validity decisions. Qualification still decides Verified / Provisional / Rejected; Ranking still ranks qualified candidates. Only the final list-building step applies the mix. The qualification bullet that currently lists “founder/organizer target counts” among strict qualification rules should be corrected so target-count assembly is not treated as a qualification rule.

**Rationale:** Live in-window events often have no named presenters yet, while organizer contact routes are usually public immediately. Founders remain the preferred lead type when they are verified; organizers keep the digest useful in weeks when names have not been published. The no-padding rule (D09) is unchanged.

D05 should be updated to this rule (or superseded by a new approved decision that points here). The coach-quality metric is unchanged: `>=60%` Useful among reviewed verified leads when 10 verified leads are available.

---

## L2. Watch list for events with no lineup yet

**Where:** new product behavior to record in `docs/PROJECT.md` (opportunity/event model, Failure / user states if needed, and a note under D23). Implementation belongs to later approved slices, not this amendment.

**Add:**

- When an otherwise qualifying event is found but the current edition has not named presenters, keep it on a **watch list** with an expected-announce date and/or a recheck date.
- Recheck weekly once a repeating digest exists.
- The **organizer** of a pending-lineup event may be a verified organizer lead in the current week, if organizer rules are met.
- **Founders** from that event are added only in a later week, after official same-edition evidence names them.
- For the current milestone (one fresh run), the watch list is an **output of the run** (pending events plus recheck dates). An automated weekly scheduler remains deferred under D23 unless Raj later approves it.

**Rationale:** The live reachability spike found named presenters on 1 of 10 upcoming events; the replay spike found them on 5 of 10 past or already-announced editions, usually on a later official finalists/winners/news page. Founder supply is mostly a timing problem. Two clicks were enough when names existed.

---

## L3. Weekly founder/organizer metric and review trigger

**Where:** `docs/PROJECT.md` success metrics / evaluation, and the operating notes in `docs/STATUS.md` once weekly runs exist.

**Add:** each digest run must log:

- the founder/organizer split actually delivered;
- the count of pending-lineup watch-list events;
- whether the list was short of 10, and why.

**Review trigger:** if verified founders stay under about **2 per week for 3–4 consecutive weekly runs**, revisit the founder channel (query strategy, watch-list yield, or the mix rule itself) rather than silently lowering verification criteria.

**Rationale:** This is the observable test of whether the founder path is producing enough names once rechecks are in place.

---

## L4. Evidence findings to carry into Slices 4–5 (and the Slice 3 proposal)

These are design constraints from the 2026-11-14 reachability spikes (10 live events, 7 Canada / 3 US; 10 past/announced Canadian editions). They are not a license to start those slices.

- **Live vs past:** 1/10 live events named presenters within two official clicks; 5/10 past or already-announced editions did. Organizer contact routes were available on 9/10 events in both spikes.
- **Follow the organizer’s later official finalists, winners, or news pages,** then stop. Names often appear there, not on the apply page search returns.
- **Maximum official-site link depth of 2 is sufficient** when names exist (depth 0 or 1 in most yes cases; one official list was at depth 2).
- **Company-only pages are incomplete,** even after the event. They do not verify individual founders. Do not trust titles such as “Meet the Founders” or “Winner’s Circle”; those were company-only in the replay set (Startup World Cup Ottawa, Startupfest, and Desjardins 2026).
- **Strict same-edition-year matching remains mandatory (D10).** Observed traps: The Arena’s page still showing 2026 names next to the 2027 event; McMaster’s program page still saying the pitch is “at the end of August”; Startupfest 2026 pages carrying a 2027 header; a 2023 session URL in results.
- **Plan for bot-blocked, login-walled, and LinkedIn-only surfaces.** Official names that appear only off-site (for example LinkedIn) are **not counted** unless Raj later changes that policy. Do not discover or store private contact information.
- **PDFs are low priority.** HTML event and news pages were the surface that mattered; no replay case required a PDF to reach names.
- **Incubators and programs are not direct founder sources.** Use them only to find their dated demo days or equivalent pitch events.

---

## L5. Open question: student teams

**Default until Raj decides otherwise:** student capstone or class pitch teams **do not count as verified founders** unless official evidence shows they are pitching a venture (not only a course project).

The replay spike included Waterloo Capstone Design 2026 (12 teams) and the QVI Problem Pitch (4 teams). Those names should not be treated as founder leads under this default. Events such as Enactus, where students pitch ventures, can still qualify under the existing newer-founder rule.

---

## Canonical documents Codex must update upon approval to apply this amendment

Update these to the L1–L5 rule. Do not rewrite frozen benchmark data or completed historical results.

| Document | What to change |
| --- | --- |
| `docs/PROJECT.md` | §1 milestone target (7 founders; 3 organizers; “6 of 10” stays, because the quality metric still applies when 10 verified leads are available). §2 hypothesis bullet “up to 7 verified founders + 3 verified organizers.” Organizer verification sentence that refers to “the 3 verified-organizer target.” §4 qualification “founder/organizer target counts” (move assembly to Presentation / Slice 7). D05 (and, if useful, a new decision row for the watch list and weekly metric; note under D23 that watch-list output is in scope later, while an automated scheduler stays deferred). §6 end-to-end acceptance “up to 7 Verified founders + 3 Verified organizers.” Slice 7 “Assemble 7 Founder + 3 Organizer target…”. §8 add the student-team default. §10 Definition of Done item 6 (“up to the 7/3 target”). Failure behavior / D09 already match “never pad” and need only wording alignment. |
| `docs/STATUS.md` | Milestone line; Stage 2 “7/3 target”; Current Reality “Target: 7 Verified founders + 3 Verified organizers when available.” Also refresh Slice 2 status and next action if the provider decision is recorded in the same authorized edit. |
| `README.md` | Only if its “Current position” still describes the old fixed mix or a stale Slice 2 next action. |

**Do not change** frozen `docs/benchmark/v1/` or `v2/` (their “7 founders” / “17 founders” figures are case counts, not the product mix). `docs/work/001-benchmark-setup.md` may get a one-line pointer that the product mix was later amended here; do not recast v1’s case counts as a product target.

Related Slice 2 close-out edits (`002` results, D16 provider choice) are separate; see the companion Codex prompt. They may be applied in the same authorized documentation pass if Raj approves that scope.

---

## Security Impact

Not material to this amendment. The off-site-names and private-contact rules above restate existing privacy constraints; they do not add collection of private contact information.

## Approval

- User approval / date / proposal revision or scope: Substance approved by Raj in conversation on 2026-11-14 (America/Toronto), including founder-first fill, organizer gap-fill, a reserved organizer minimum, the watch list, the weekly split metric, and the reachability findings. Canonical-document application and any implementation remain separately authorized.
- Conditions: Student-team default as in L5 unless Raj overrides. Default reserved organizer slots = 2, configurable.
- Separately authorized external actions (commit/push/deploy/purchase/etc.): None.
- Material amendments / renewed approval: None yet.

## Results (after canonical docs are updated)

### Actual changes and files
- Pending.

### Canonical documents updated
- `docs/PROJECT.md`: founder-first 10-slot rule, watch list, weekly metrics/review trigger, D05/D23, Slice 7, and milestone acceptance updated; reachability and student-team constraints carried forward.
- `docs/STATUS.md`: milestone and current reality aligned.
- Other: `README.md` pointer aligned; frozen benchmarks untouched.
