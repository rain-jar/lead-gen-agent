"""Run discovery offline from saved responses; live search follows the A1 gate."""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import Counter
from datetime import date
from pathlib import Path

from .core import CandidateEdition, make_candidate, merge_candidates, recheck_date


def watch_items(candidates: list[CandidateEdition], reference_date: date, run_id: str) -> list[dict]:
    by_edition: dict[str, dict] = {}
    for item in candidates:
        reasons = set(item.unknown_reasons)
        if item.needs_alternate_source:
            reasons.add("alternate_source_needed")
        if item.window_status == "too_far":
            reasons.add("enters_window_later")
        elif item.window_status == "pending_date":
            reasons.add("date_pending")
        elif item.window_status == "unknown" and "date_ambiguous" not in reasons:
            reasons.add("date_unknown")
        if item.lineup_status == "pending":
            reasons.add("lineup_pending")
        if not reasons:
            continue
        key = item.dedupe_key
        row = by_edition.setdefault(key, {"dedupe_key": key, "reasons": set(), "expected_announce_date": None, "recheck_date": None, "last_seen_run_id": run_id, "primary_source_urls": set()})
        row["reasons"].update(reasons)
        row["primary_source_urls"].update(s.url for s in item.sources[:1])
        expected = item.expected_announce_date
        if expected:
            row["expected_announce_date"] = expected.isoformat()
        dates = [recheck_date(reason, reference_date, expected, item.event_date) for reason in reasons]
        if dates:
            next_date = min(dates).isoformat()
            row["recheck_date"] = min(row["recheck_date"], next_date) if row["recheck_date"] else next_date
    return [{**row, "reasons": sorted(row["reasons"]), "primary_source_urls": sorted(row["primary_source_urls"])} for _, row in sorted(by_edition.items())]


def process(raw_path: Path, out: Path, reference_date: date, run_id: str, providers: tuple[str, ...] = ("exa", "serper")) -> dict:
    out.mkdir(parents=True, exist_ok=True)
    # A JSON string may contain Unicode line separators; only LF delimits NDJSON.
    raw = [json.loads(line) for line in raw_path.read_text(encoding="utf-8").split("\n") if line]
    items = []
    for row in raw:
        if row.get("provider") not in providers or row.get("http_status") != 200:
            continue
        scope = row.get("scope", "")
        phase = "us" if scope == "United States" else "ca"
        for result in row.get("results", []):
            if not result.get("url"):
                continue
            items.append(make_candidate(result.get("title") or "", result["url"], scope, phase, reference_date, result.get("snippet") or "", row["provider"], row.get("query_id", ""), row.get("query_family", "replay"), row.get("timestamp", ""), result.get("rank", 0), run_id))
    merged = merge_candidates(items)
    candidates, excluded = [], []
    for item in merged:
        reason = None
        if item.page_kind == "program":
            reason = "program_without_dated_event"
        elif item.page_kind == "other":
            reason = "non_event"
        elif item.window_status in ("past", "too_soon"):
            reason = item.window_status
        if reason:
            excluded.append({**json.loads(item.json()), "providers": sorted(item.providers), "query_families": sorted(item.query_families), "exclude_reason": reason})
            continue
        candidates.append(item)
    watch = watch_items(candidates, reference_date, run_id)
    def write(name: str, rows: list) -> None:
        def stable(row):
            if not isinstance(row, CandidateEdition):
                return row
            value = json.loads(row.json())
            value["providers"] = sorted(row.providers)
            value["query_families"] = sorted(row.query_families)
            return value
        (out / name).write_text("".join(json.dumps(stable(x), ensure_ascii=False, sort_keys=True) + "\n" for x in rows), encoding="utf-8")
    write("candidates.jsonl", candidates)
    write("watchlist.jsonl", watch)
    write("excluded.jsonl", excluded)
    meta = {"run_id": run_id, "mode": "replay", "reference_date": reference_date.isoformat(), "raw_sha256": hashlib.sha256(raw_path.read_bytes()).hexdigest(), "providers": list(providers), "candidate_count": len(candidates), "distinct_urls": len({s.canonical_url for x in candidates for s in x.sources}), "excluded_count": len(excluded), "watch_count": len(watch), "watch_reason_memberships": sum(len(x["reasons"]) for x in watch), "window_status": dict(Counter(x.window_status for x in candidates)), "lineup_status": dict(Counter(x.lineup_status for x in candidates)), "page_kind": dict(Counter(x.page_kind for x in candidates)), "watch_reason": dict(Counter(reason for x in watch for reason in x["reasons"])), "reserved_usd": 0.0}
    (out / "run.json").write_text(json.dumps(meta, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return meta


def main() -> None:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--replay", type=Path, help="Saved raw.ndjson from a prior run")
    mode.add_argument("--live-eval", action="store_true", help="One bounded Canada and US evaluation run")
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--reference-date", type=date.fromisoformat, default=date.today())
    parser.add_argument("--providers", choices=("union", "exa"), default="union")
    args = parser.parse_args()
    if args.live_eval:
        from .live import LiveRun
        meta = LiveRun(args.out, args.reference_date).run()
    else:
        meta = process(args.replay, args.out, args.reference_date, args.out.name, ("exa",) if args.providers == "exa" else ("exa", "serper"))
    print(json.dumps({"run_id": meta["run_id"], "candidates": meta["candidate_count"], "excluded": meta["excluded_count"], "watch": meta["watch_count"]}))


if __name__ == "__main__":
    main()
