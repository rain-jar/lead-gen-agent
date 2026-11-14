"""Independent offline v2 candidate scoring; never imported by discovery."""
from __future__ import annotations

import calendar
import csv
import json
import sys
import unicodedata
from collections import defaultdict
from datetime import date, timedelta
from pathlib import Path

try:
    from scripts.score_search_provider_benchmark import build_source_maps, normalize_url
except ModuleNotFoundError:
    from score_search_provider_benchmark import build_source_maps, normalize_url

ROOT = Path(__file__).resolve().parents[1]


def fold(value: str | None) -> str:
    return unicodedata.normalize("NFKD", value or "").encode("ascii", "ignore").decode().casefold()


def add_months(day: date, months: int) -> date:
    year, month = divmod(day.year * 12 + day.month - 1 + months, 12)
    month += 1
    return date(year, month, min(day.day, calendar.monthrange(year, month)[1]))


def replay_window_status(opportunity: dict) -> str:
    ref = date.fromisoformat(opportunity["reference_date"])
    start = date.fromisoformat(opportunity["event_date"])
    end = date.fromisoformat(opportunity["event_end_date"]) if opportunity.get("event_end_date") else start
    if start < ref:
        return "past"
    if start < ref + timedelta(days=7):
        return "too_soon"
    if end > add_months(ref, 6):
        return "too_far"
    return "in_window"


def window_at(opportunity: dict, ref: date) -> str:
    """Benchmark edition's own window status at a run's reference date."""
    return replay_window_status({**opportunity, "reference_date": ref.isoformat()})


def wrong_value(record: dict, city: str, year: int) -> bool:
    return bool((record.get("city") and fold(record["city"]) != fold(city)) or (record.get("edition_year") and record["edition_year"] != year))


def edition_outcome(candidates: list[dict], excluded: list[dict], city: str, year: int, expected_status: str) -> dict:
    """A2b retention. A correct past/too-soon exclusion (approved 2026-11-14) is not penalized."""
    wrong = [c for c in candidates if wrong_value(c, city, year)]
    kept = bool(candidates) and not wrong
    correctly_excluded = (not candidates and bool(excluded) and expected_status in ("past", "too_soon")
                          and all(e.get("exclude_reason") == expected_status and not wrong_value(e, city, year) for e in excluded))
    return {"kept": kept, "correctly_excluded": correctly_excluded, "kept_or_correctly_excluded": kept or correctly_excluded, "wrong_records": len(wrong)}


def returned_by_search(raw_rows: list[dict], url_keys: dict, normalize=normalize_url) -> set:
    """A2a: edition keys whose known URLs came back from Exa or Serper, before any normalization."""
    keys = set()
    for row in raw_rows:
        if row.get("provider") not in ("exa", "serper") or row.get("http_status") != 200:
            continue
        for result in row.get("results", []):
            if result.get("url"):
                keys |= set(url_keys.get(normalize(result["url"]), set()))
    return keys


def _rows(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").split("\n") if line] if path.exists() else []


def score(run: Path, raw: Path | None = None) -> dict:
    benchmark = json.loads((ROOT / "docs/benchmark/v2/benchmark.json").read_text(encoding="utf-8"))
    pages, _, _ = build_source_maps(benchmark, True)
    labels = {}
    with (ROOT / "artifacts/search-provider/20261114T131952Z/judgments/same_site_first_pass.csv").open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            if row["label"] == "relevant_same_edition":
                labels[normalize_url(row["url"])] = row["adjudicated_edition_key"]
    url_keys = defaultdict(set)
    for url, keys in pages.items():
        url_keys[url] |= set(keys)
    for url, key in labels.items():
        url_keys[url].add(key)
    candidates = _rows(run / "candidates.jsonl")
    excluded = _rows(run / "excluded.jsonl")
    meta = json.loads((run / "run.json").read_text(encoding="utf-8")) if (run / "run.json").exists() else {}
    run_ref = date.fromisoformat(meta.get("reference_date", "2026-11-14"))
    raw = raw or (run / "raw.ndjson")
    returned = returned_by_search(_rows(raw), url_keys) if raw.exists() else None
    hits = {"union": defaultdict(dict), "exa": defaultdict(dict)}
    excluded_hits = {"union": defaultdict(dict), "exa": defaultdict(dict)}
    for bucket, records in ((hits, candidates), (excluded_hits, excluded)):
        for record in records:
            for source in record["sources"]:
                if source["provider"] not in ("exa", "serper"):
                    continue
                url = normalize_url(source["url"])
                for key in url_keys.get(url, set()):
                    identity = (record["dedupe_key"], tuple(sorted(s["canonical_url"] for s in record["sources"])))
                    bucket["union"][key][identity] = record
                    if source["provider"] == "exa":
                        bucket["exa"][key][identity] = record
    expected = [o for o in benchmark["opportunities"] if o["expected_discovery"] == "eligible"]
    criteria = ("a1a", "a1b") + (("a2a", "a2b", "kept_or_correctly_excluded") if returned is not None else ())
    counts = {view: defaultdict(lambda: {c: [0, 0] for c in criteria}) for view in hits}
    details = []
    for item in expected:
        key, split, country = item["edition_key"], item["split"], item["location"]["country"]
        city = item["location"]["city"]
        year = int(item["event_date"][:4])
        status_at_run = window_at(item, run_ref)
        row = {"edition_key": key, "split": split, "country": country, "expected_city": city, "expected_year": year, "reference_date": item["reference_date"], "benchmark_window_status": replay_window_status(item), "window_status_at_run_reference": status_at_run}
        if returned is not None:
            row["returned_by_search"] = key in returned
        for view in hits:
            related = list(hits[view].get(key, {}).values())
            related_excluded = list(excluded_hits[view].get(key, {}).values())
            outcome = edition_outcome(related, related_excluded, city, year, status_at_run)
            a1b = any(c.get("city") and fold(c["city"]) == fold(city) and c.get("edition_year") == year for c in related)
            row[view] = {"record_count": len(related), "cities": sorted({c["city"] or "unknown" for c in related}), "years": sorted({str(c["edition_year"] or "unknown") for c in related}), "windows": sorted({c["window_status"] for c in related}), "excluded_reasons": sorted({e.get("exclude_reason") for e in related_excluded}), "wrong_records": outcome["wrong_records"], "a1a": outcome["kept"], "a1b": a1b}
            if returned is not None:
                row[view].update({"a2a": key in returned, "a2b": key in returned and outcome["kept"], "kept_or_correctly_excluded": key in returned and outcome["kept_or_correctly_excluded"]})
            for group in ("overall", split, country.lower(), f"{split}_{country.lower()}"):
                for criterion in criteria:
                    counts[view][group][criterion][1] += 1
                    counts[view][group][criterion][0] += row[view][criterion]
        details.append(row)
    normalized = {view: dict(groups) for view, groups in counts.items()}
    union = normalized["union"]
    result = {"run_reference_date": run_ref.isoformat(), "counts": normalized, "details": details, "a1a_pass": union["overall"]["a1a"][0] >= 9 and union["live_ca"]["a1a"][0] >= 6, "candidate_count": len(candidates), "distinct_urls": len({s["canonical_url"] for c in candidates for s in c["sources"]})}
    if returned is not None:
        # Approved A2 restatement (2026-11-14): A2a search return and A2b retention, each >= 6/7 live Canada.
        result["a2_pass"] = union["live_ca"]["a2a"][0] >= 6 and union["live_ca"]["a2b"][0] >= 6
    return result


if __name__ == "__main__":
    result = score(Path(sys.argv[1]), Path(sys.argv[2]) if len(sys.argv) > 2 else None)
    print(json.dumps(result, ensure_ascii=False, indent=2))
