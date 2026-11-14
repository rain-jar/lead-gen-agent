"""Validate a replay benchmark JSON artifact and its internal references.

Schema version 1 (benchmark v1) is validated exactly as before. Artifacts that
declare ``schema_version >= 2`` also get the v2 coverage and integrity checks
(live/replay split, edition concentration, negative-category coverage, contact
routes, duplicates). New fields are optional so v1 still validates unchanged.
"""

from __future__ import annotations

import calendar
import json
import sys
from collections import Counter
from datetime import date, timedelta
from pathlib import Path
from urllib.parse import urlparse

from pydantic import BaseModel, Field, ValidationError, validator


# ---- v2 policy constants (benchmark-design rules, not product logic) ----
MAX_EDITION_SHARE = 0.30  # max share of verified founder cases from one edition
MIN_FOUNDER_EDITIONS = 5  # min distinct editions contributing verified founders
MIN_VERIFIED_ORGANIZERS = 3
REQUIRED_FAILURE_CATEGORIES = {
    "past_edition",
    "presenter_unknown",
    "outside_date_window",
    "non_pitching_role",
    "established_founder",
    "mismatched_edition",
    "organizer_no_upcoming_event",
    "insufficient_evidence",
    "duplicate",
}
SPLITS = {"live", "replay"}
OPPORTUNITY_TYPES = {
    "university_competition",
    "accelerator_or_incubator_demo_day",
    "regional_or_national_pitch_final",
    "social_or_non_tech_competition",
    "founder_showcase",
    "festival_pitch_competition",
}
SECTORS = {"tech", "non-tech", "mixed", "unspecified"}


class StrictModel(BaseModel):
    class Config:
        extra = "forbid"


class Location(StrictModel):
    city: str = Field(min_length=1)
    region: str = Field(min_length=1)
    country: str = Field(min_length=2, max_length=2)

    @validator("country")
    def uppercase_country(cls, value: str) -> str:
        if value != value.upper():
            raise ValueError("country must be an uppercase ISO-style two-letter code")
        return value


class Source(StrictModel):
    url: str = Field(min_length=1)
    source_type: str = Field(min_length=1)
    checked_date: date
    evidence_note: str = Field(min_length=1)

    @validator("url")
    def public_https_url(cls, value: str) -> str:
        parsed = urlparse(value)
        if parsed.scheme != "https" or not parsed.hostname:
            raise ValueError("source URL must be an absolute HTTPS URL")
        return value


class ContactRoute(StrictModel):
    url: str = Field(min_length=1)
    kind: str = Field(min_length=1)

    @validator("url")
    def public_https_url(cls, value: str) -> str:
        parsed = urlparse(value)
        if parsed.scheme != "https" or not parsed.hostname:
            raise ValueError("contact route URL must be an absolute HTTPS URL")
        return value


class Opportunity(StrictModel):
    opportunity_id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    edition: str = Field(min_length=1)
    split: str | None = None  # v2
    edition_key: str | None = None  # v2
    reference_date: date
    event_date: date
    event_end_date: date | None = None  # v2
    location: Location
    category: str = Field(min_length=1)
    opportunity_type: str | None = None  # v2
    sector: str | None = None  # v2
    operator: str | None = None  # v2
    expected_discovery: str
    sources: list[Source] = Field(min_items=1)
    notes: str | None = None  # v2

    @validator("expected_discovery")
    def valid_discovery_judgment(cls, value: str) -> str:
        if value not in {"eligible", "ineligible", "ambiguous"}:
            raise ValueError("expected_discovery must be eligible, ineligible, or ambiguous")
        return value


class Case(StrictModel):
    case_id: str = Field(min_length=1)
    case_type: str
    opportunity_id: str = Field(min_length=1)
    expected_judgment: str
    person_name: str | None = None
    venture: str | None = None
    organization_name: str | None = None
    sector: str | None = None  # v2
    failure_category: str | None = None  # v2
    duplicate_of: str | None = None  # v2
    newer_founder_evidence: str | None = None  # v2
    audience_evidence: str | None = None  # v2
    contact_route: ContactRoute | None = None  # v2
    reason: str | None = None
    sources: list[Source] = Field(min_items=1)

    @validator("case_type")
    def valid_case_type(cls, value: str) -> str:
        if value not in {"founder", "organizer"}:
            raise ValueError("case_type must be founder or organizer")
        return value

    @validator("expected_judgment")
    def valid_expected_judgment(cls, value: str) -> str:
        if value not in {"verified", "provisional", "rejected"}:
            raise ValueError("expected_judgment must be verified, provisional, or rejected")
        return value

    @validator("reason")
    def rejected_cases_need_reason(cls, value: str | None, values: dict) -> str | None:
        if values.get("expected_judgment") == "rejected" and not value:
            raise ValueError("rejected cases must explain the rejection")
        return value

    @validator("organization_name")
    def organizer_requires_organization(cls, value: str | None, values: dict) -> str | None:
        if values.get("case_type") == "organizer" and not value:
            raise ValueError("organizer cases require organization_name")
        return value


class GroundTruthRule(StrictModel):
    rule_id: str = Field(min_length=1)
    statement: str = Field(min_length=1)
    approved_by: str = Field(min_length=1)
    approved_date: date


class Benchmark(StrictModel):
    benchmark_id: str = Field(min_length=1)
    version: str = Field(min_length=1)
    schema_version: int = 1
    status: str
    frozen_date: date | None = None  # v2
    created_date: date
    benchmark_date: date | None = None  # v2: live-split reference date
    ground_truth_rules: list[GroundTruthRule] | None = None  # v2
    description: str = Field(min_length=1)
    opportunities: list[Opportunity] = Field(min_items=1)
    cases: list[Case] = Field(min_items=1)

    @validator("status")
    def valid_status(cls, value: str) -> str:
        if value not in {"draft", "frozen"}:
            raise ValueError("status must be draft or frozen")
        return value


def add_calendar_months(value: date, months: int) -> date:
    month_index = value.month - 1 + months
    year = value.year + month_index // 12
    month = month_index % 12 + 1
    day = min(value.day, calendar.monthrange(year, month)[1])
    return date(year, month, day)


def in_window(reference: date, event: date) -> bool:
    return reference + timedelta(days=7) <= event <= add_calendar_months(reference, 6)


def validate_relationships(benchmark: Benchmark) -> list[str]:
    """Checks shared by every schema version (unchanged v1 behaviour)."""
    errors: list[str] = []
    opportunities = {item.opportunity_id: item for item in benchmark.opportunities}
    if len(opportunities) != len(benchmark.opportunities):
        errors.append("opportunity_id values must be unique")

    case_ids = [item.case_id for item in benchmark.cases]
    if len(set(case_ids)) != len(case_ids):
        errors.append("case_id values must be unique")

    for opportunity in benchmark.opportunities:
        is_in_window = in_window(opportunity.reference_date, opportunity.event_date)
        if opportunity.expected_discovery == "eligible" and not is_in_window:
            errors.append(
                f"{opportunity.opportunity_id}: marked eligible, but event date is outside "
                "the reference date +7 day to +6 month window"
            )
        if opportunity.expected_discovery == "ineligible" and is_in_window:
            errors.append(
                f"{opportunity.opportunity_id}: marked ineligible, but event date is inside "
                "the reference date +7 day to +6 month window"
            )

    for case in benchmark.cases:
        if case.opportunity_id not in opportunities:
            errors.append(f"{case.case_id}: references missing opportunity {case.opportunity_id}")
        # v1 rule: founder cases need a person, except an explicit v2 company-only
        # presenter_unknown negative (the failure being tested is the missing person).
        if case.case_type == "founder" and not case.person_name:
            company_only = (
                benchmark.schema_version >= 2
                and case.failure_category == "presenter_unknown"
                and case.expected_judgment != "verified"
                and bool(case.venture)
            )
            if not company_only:
                errors.append(f"{case.case_id}: founder cases require person_name")
        if case.case_type == "founder" and case.expected_judgment == "verified":
            if not case.venture:
                errors.append(f"{case.case_id}: verified founder case requires venture")
        if case.case_type == "organizer" and case.expected_judgment == "verified":
            opportunity = opportunities.get(case.opportunity_id)
            if opportunity and opportunity.expected_discovery != "eligible":
                errors.append(f"{case.case_id}: verified organizer references ineligible opportunity")
    return errors


def validate_v2_rules(benchmark: Benchmark) -> list[str]:
    """Additional coverage and integrity checks for schema_version >= 2."""
    errors: list[str] = []
    opportunities = {item.opportunity_id: item for item in benchmark.opportunities}
    cases = {item.case_id: item for item in benchmark.cases}
    bdate = benchmark.benchmark_date
    if bdate is None:
        errors.append("schema v2 requires benchmark_date")
    if benchmark.status == "frozen":
        if benchmark.frozen_date is None:
            errors.append("frozen v2 benchmark requires frozen_date")
        elif benchmark.frozen_date < benchmark.created_date:
            errors.append("frozen_date precedes created_date")
        for rule in benchmark.ground_truth_rules or []:
            if benchmark.frozen_date and rule.approved_date > benchmark.frozen_date:
                errors.append(f"rule {rule.rule_id} approved after the freeze date")
    elif benchmark.frozen_date is not None:
        errors.append("frozen_date is only allowed when status is frozen")

    # Opportunity-level fields, split semantics, edition keys.
    keys_per_split: Counter = Counter()
    edition_dates: dict[str, set] = {}
    for opp in benchmark.opportunities:
        oid = opp.opportunity_id
        for field in ("split", "edition_key", "opportunity_type", "sector"):
            if not getattr(opp, field):
                errors.append(f"{oid}: v2 requires {field}")
        if opp.split and opp.split not in SPLITS:
            errors.append(f"{oid}: split must be one of {sorted(SPLITS)}")
        if opp.opportunity_type and opp.opportunity_type not in OPPORTUNITY_TYPES:
            errors.append(f"{oid}: unknown opportunity_type {opp.opportunity_type}")
        if opp.sector and opp.sector not in SECTORS:
            errors.append(f"{oid}: unknown sector {opp.sector}")
        if bdate and opp.split == "live" and opp.reference_date != bdate:
            errors.append(f"{oid}: live opportunities must use reference_date == benchmark_date")
        if bdate and opp.split == "replay" and opp.reference_date >= bdate:
            errors.append(f"{oid}: replay reference_date must be before benchmark_date")
        if opp.event_end_date:
            if opp.event_end_date < opp.event_date:
                errors.append(f"{oid}: event_end_date precedes event_date")
            if opp.expected_discovery == "eligible" and not in_window(opp.reference_date, opp.event_end_date):
                errors.append(f"{oid}: eligible multi-day event must end inside the window")
        if opp.expected_discovery == "eligible" and not opp.operator:
            errors.append(f"{oid}: eligible opportunity requires operator")
        if opp.edition_key and opp.split:
            keys_per_split[(opp.split, opp.edition_key)] += 1
            edition_dates.setdefault(opp.edition_key, set()).add(opp.event_date)
    for (split, key), count in keys_per_split.items():
        if count > 1:
            errors.append(f"edition_key {key} appears {count} times in split {split} (dedupe editions)")
    for key, dates in edition_dates.items():
        if len(dates) > 1:
            errors.append(f"edition_key {key} has conflicting event dates across records")

    # Sources: every opportunity and case needs URL + checked date not after benchmark date.
    created = benchmark.created_date
    for label, items in (("opportunity", benchmark.opportunities), ("case", benchmark.cases)):
        for item in items:
            ident = getattr(item, "opportunity_id", None) if label == "opportunity" else item.case_id
            for source in item.sources:
                if source.checked_date > created:
                    errors.append(f"{ident}: source checked_date is after created_date")

    # Case-level rules.
    for case in benchmark.cases:
        cid = case.case_id
        opp = opportunities.get(case.opportunity_id)
        if case.failure_category and case.failure_category not in REQUIRED_FAILURE_CATEGORIES:
            errors.append(f"{cid}: unknown failure_category {case.failure_category}")
        if case.expected_judgment == "verified":
            if case.failure_category or case.duplicate_of:
                errors.append(f"{cid}: verified cases cannot carry failure_category or duplicate_of")
            if opp and opp.expected_discovery != "eligible":
                errors.append(f"{cid}: verified case references a non-eligible opportunity")
            if case.case_type == "founder" and not case.newer_founder_evidence:
                errors.append(f"{cid}: verified founder requires newer_founder_evidence")
            if case.case_type == "organizer":
                if not case.contact_route:
                    errors.append(f"{cid}: verified organizer requires contact_route")
                if not case.audience_evidence:
                    errors.append(f"{cid}: verified organizer requires audience_evidence")
        else:
            if not case.failure_category:
                errors.append(f"{cid}: non-verified cases require failure_category")
            if not case.reason:
                errors.append(f"{cid}: non-verified cases require reason")
        if case.failure_category == "duplicate":
            target = cases.get(case.duplicate_of or "")
            if not target:
                errors.append(f"{cid}: duplicate case must reference an existing duplicate_of case")
            elif target.case_type != case.case_type or target.opportunity_id != case.opportunity_id:
                errors.append(f"{cid}: duplicate_of must point to the same case type and opportunity")
            elif target.expected_judgment != "verified":
                errors.append(f"{cid}: duplicate_of must point to the canonical verified case")
        elif case.duplicate_of:
            errors.append(f"{cid}: duplicate_of is only allowed for failure_category duplicate")

    # Coverage rules.
    verified_founders = [
        c for c in benchmark.cases if c.case_type == "founder" and c.expected_judgment == "verified"
    ]
    per_edition = Counter(
        opportunities[c.opportunity_id].edition_key for c in verified_founders if c.opportunity_id in opportunities
    )
    if verified_founders:
        top_key, top_count = per_edition.most_common(1)[0]
        share = top_count / len(verified_founders)
        if share > MAX_EDITION_SHARE:
            errors.append(
                f"edition {top_key} supplies {share:.0%} of verified founders (cap {MAX_EDITION_SHARE:.0%})"
            )
    if len(per_edition) < MIN_FOUNDER_EDITIONS:
        errors.append(f"verified founders come from {len(per_edition)} editions (minimum {MIN_FOUNDER_EDITIONS})")
    verified_orgs = [c for c in benchmark.cases if c.case_type == "organizer" and c.expected_judgment == "verified"]
    if len(verified_orgs) < MIN_VERIFIED_ORGANIZERS:
        errors.append(f"only {len(verified_orgs)} verified organizers (minimum {MIN_VERIFIED_ORGANIZERS})")
    present = {c.failure_category for c in benchmark.cases if c.failure_category}
    missing = REQUIRED_FAILURE_CATEGORIES - present
    if missing:
        errors.append(f"missing negative/ambiguous categories: {sorted(missing)}")
    return errors


def summarize(benchmark: Benchmark) -> str:
    opps = {o.opportunity_id: o for o in benchmark.opportunities}
    vf = [c for c in benchmark.cases if c.case_type == "founder" and c.expected_judgment == "verified"]
    vo = [c for c in benchmark.cases if c.case_type == "organizer" and c.expected_judgment == "verified"]
    neg = [c for c in benchmark.cases if c.expected_judgment != "verified"]
    per_edition = Counter(opps[c.opportunity_id].edition_key for c in vf)
    top = per_edition.most_common(1)[0] if per_edition else ("-", 0)
    eligible = [o for o in benchmark.opportunities if o.expected_discovery == "eligible"]
    by_split = Counter(o.split for o in eligible)
    by_country = Counter(o.location.country for o in eligible)
    return (
        f"  eligible opportunities: {len(eligible)} (split {dict(by_split)}, country {dict(by_country)})\n"
        f"  verified founders: {len(vf)} from {len(per_edition)} editions; "
        f"max edition share {top[1]}/{len(vf)} ({top[0]})\n"
        f"  verified organizers: {len(vo)}; negative/ambiguous cases: {len(neg)}"
    )


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: python3 scripts/validate_benchmark.py <benchmark.json>", file=sys.stderr)
        return 2

    path = Path(sys.argv[1])
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        benchmark = Benchmark.parse_obj(payload)
    except (OSError, json.JSONDecodeError, ValidationError) as exc:
        print(f"Invalid benchmark: {exc}", file=sys.stderr)
        return 1

    errors = validate_relationships(benchmark)
    if benchmark.schema_version >= 2:
        errors += validate_v2_rules(benchmark)
    if errors:
        print("Benchmark consistency errors:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    print(
        f"Valid {benchmark.benchmark_id} {benchmark.version}: "
        f"{len(benchmark.opportunities)} opportunities, {len(benchmark.cases)} cases "
        f"({benchmark.status})"
    )
    if benchmark.schema_version >= 2:
        print(summarize(benchmark))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
