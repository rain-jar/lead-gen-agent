"""Seeded precision sample of in-window candidates for human judgment (approved 2026-11-14).

Writes a CSV for Raj to judge. Advisory labels, if an advisory CSV exists, are merged in
as clearly marked advisory columns; they are never treated as ground truth.
"""
from __future__ import annotations

import argparse
import csv
import json
import random
from collections import Counter
from pathlib import Path

FIELDS = ("sample_index", "dedupe_key", "event_name", "city", "country", "geo_tier", "event_date", "event_end_date", "date_text", "date_confidence", "page_kind", "lineup_status", "primary_url", "primary_title", "snippet_excerpt")
ADVISORY = ("advisory_real_in_window_event", "advisory_in_canada", "advisory_error_type", "advisory_note")
JUDGE = ("raj_real_in_window_event", "raj_notes")


def sample_in_window(rows: list[dict], n: int, seed: int) -> list[dict]:
    pool = sorted((r for r in rows if r.get("window_status") == "in_window"), key=lambda r: (r["dedupe_key"], json.dumps(r.get("sources", []), sort_keys=True)))
    picked = random.Random(seed).sample(pool, min(n, len(pool)))
    return sorted(picked, key=lambda r: r["dedupe_key"])


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("run", type=Path)
    parser.add_argument("--n", type=int, default=25)
    parser.add_argument("--seed", type=int, default=20261114)
    parser.add_argument("--advisory", type=Path, help="Optional CSV keyed by dedupe_key with advisory_* columns")
    args = parser.parse_args()
    rows = [json.loads(line) for line in (args.run / "candidates.jsonl").read_text(encoding="utf-8").split("\n") if line]
    sample = sample_in_window(rows, args.n, args.seed)
    advisory = {}
    if args.advisory and args.advisory.exists():
        with args.advisory.open(newline="", encoding="utf-8") as handle:
            advisory = {r["dedupe_key"]: r for r in csv.DictReader(handle)}
    out = args.run / "precision_sample.csv"
    with out.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS + ADVISORY + JUDGE)
        writer.writeheader()
        for i, r in enumerate(sample, 1):
            source = r["sources"][0] if r.get("sources") else {}
            snippet = " ".join((source.get("snippet") or "").split())[:400]
            row = {"sample_index": i, "dedupe_key": r["dedupe_key"], "event_name": r["event_name"], "city": r.get("city") or "", "country": r.get("country") or "", "geo_tier": r.get("geo_tier"), "event_date": r.get("event_date") or "", "event_end_date": r.get("event_end_date") or "", "date_text": r.get("date_text") or "", "date_confidence": r.get("date_confidence"), "page_kind": r.get("page_kind"), "lineup_status": r.get("lineup_status"), "primary_url": source.get("url", ""), "primary_title": source.get("title", ""), "snippet_excerpt": snippet}
            row.update({k: advisory.get(r["dedupe_key"], {}).get(k, "") for k in ADVISORY})
            row.update({k: "" for k in JUDGE})
            writer.writerow(row)
    labelled = [advisory[r["dedupe_key"]] for r in sample if r["dedupe_key"] in advisory]
    real = [a for a in labelled if a.get("advisory_real_in_window_event") == "yes"]
    canada = [a for a in labelled if a.get("advisory_in_canada") == "yes"]
    summary = {"csv": str(out), "seed": args.seed, "in_window_pool": sum(r.get("window_status") == "in_window" for r in rows), "sampled": len(sample), "sample_geo_tier": dict(Counter(r.get("geo_tier") for r in sample)),
               "advisory_labelled": len(labelled), "advisory_real_all": len(real), "advisory_canada_located": len(canada), "advisory_real_canada": sum(a.get("advisory_in_canada") == "yes" for a in real),
               "advisory_errors": dict(Counter(a.get("advisory_error_type") for a in labelled if a.get("advisory_error_type") not in ("", "none")))}
    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
