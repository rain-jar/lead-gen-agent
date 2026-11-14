# Lead Discovery Replay Benchmark v1 (Frozen)

This is a static replay set for discovery and qualification. It has seven positive founder cases and three positive organizer cases, matching the composition the user approved on 2026-11-14, plus two negative cases. Benchmark v1 is frozen; ground-truth corrections require an approved new version.

## Replay dates

Each opportunity has its own `reference_date` and `event_date`. Eligibility is judged against that opportunity's reference date: the event must be at least 7 calendar days later and no more than 6 calendar months later. `checked_date` records when a supporting source was reviewed; it is separate from the simulated replay date. This design was approved by the user on 2026-11-14 because the cases span different event editions.

Fresh-live runs must be recorded separately using the actual request date. Static replay scores do not demonstrate current-world discovery quality.

## Case composition and known limitations

- Seven named pitching founders from one dated San Diego Startup Week finalist announcement.
- Three organizers: Startup San Diego, University of Toronto Entrepreneurship, and Innovation Factory (operator of the Synapse Life Science Competition).
- One negative case for an event inside the seven-day exclusion window.
- One negative case where an official page names a founder and finalist team but does not identify the individual presenter.

The founder positives currently come from one U.S. event edition, so they do not provide broad geography or event-category coverage. Organizer cases include Canada and the U.S. This is a small known-item set, not a sample of the full event population. The event-to-person evidence must be manually checked again before freezing, particularly the older replay case from November 2026.

## Provenance and freezing

Each case and opportunity links to public source evidence, a checked date, and an evidence note. Only public business/event facts are included. Do not add private contact information or secrets. Do not edit a frozen version in place. Any approved ground-truth correction creates a new version with a recorded reason and source evidence.

## Validation

Run `python3 scripts/validate_benchmark.py docs/benchmark/v1/benchmark.json` from the `fde_leadgen_codex_docs` directory. The validator checks JSON shape, unique IDs, references, source URL/date fields, required fields by case type, and the opportunity date window.
