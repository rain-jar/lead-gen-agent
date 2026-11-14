"""Score saved Slice 2 responses offline; leave relevance judgments to Raj."""

from __future__ import annotations

import csv
import json
import statistics
import sys
from collections import defaultdict
from pathlib import Path
from urllib.parse import parse_qsl, unquote, urlencode, urlsplit

from search_provider_benchmark import BENCHMARK_V2, PROVIDERS, QUERIES, ROOT, load_queries, sha256


TRACKING_PARAMS = {"fbclid", "gclid", "mc_cid", "mc_eid"}


def normalize_url(url: str) -> str:
    """Collapse scheme, host case, www, trailing slash, fragment and tracking tags."""
    parts = urlsplit(url.strip())
    if not parts.hostname:
        return ""
    host = parts.hostname.lower().removeprefix("www.")
    if parts.port:
        host += f":{parts.port}"
    path = unquote(parts.path).rstrip("/") or "/"
    query = sorted(
        (k, v) for k, v in parse_qsl(parts.query, keep_blank_values=True)
        if not k.lower().startswith("utm_") and k.lower() not in TRACKING_PARAMS
    )
    return host + path + ("?" + urlencode(query) if query else "")


def source_is_event_or_official(source: dict) -> bool:
    kind = source.get("source_type", "").lower()
    return any(word in kind for word in ("official", "organizer", "event listing", "venue"))


def eligible_editions(benchmark: dict) -> list[dict]:
    return [o for o in benchmark["opportunities"] if o["expected_discovery"] == "eligible"]


def build_source_maps(benchmark: dict, v2: bool) -> tuple[dict[str, set[str]], dict[str, set[str]], dict[str, set[str]]]:
    """Map exact cited pages to eligible editions and verified people evidence."""
    opportunities = {o["opportunity_id"]: o for o in eligible_editions(benchmark)}
    event_pages: dict[str, set[str]] = defaultdict(set)
    evidence_pages: dict[str, set[str]] = defaultdict(set)
    hosts: dict[str, set[str]] = defaultdict(set)
    for opportunity in opportunities.values():
        edition = opportunity.get("edition_key") if v2 else opportunity["opportunity_id"]
        for source in opportunity["sources"]:
            if source_is_event_or_official(source):
                key = normalize_url(source["url"])
                event_pages[key].add(edition)
                hosts[key.split("/", 1)[0]].add(edition)
    for case in benchmark["cases"]:
        if case["expected_judgment"] != "verified" or case["opportunity_id"] not in opportunities:
            continue
        edition = opportunities[case["opportunity_id"]].get("edition_key") if v2 else case["opportunity_id"]
        for source in case["sources"]:
            if source_is_event_or_official(source):
                key = normalize_url(source["url"])
                event_pages[key].add(edition)
                evidence_pages[key].add(case["case_id"])
                hosts[key.split("/", 1)[0]].add(edition)
    return event_pages, evidence_pages, hosts


def load_responses(path: Path) -> tuple[list[dict], dict[tuple[str, str], dict]]:
    raw = [json.loads(line) for line in (path / "raw.ndjson").read_text(encoding="utf-8").splitlines() if line]
    successes: dict[tuple[str, str], dict] = {}
    for record in raw:
        if record["http_status"] == 200:
            successes[(record["provider"], record["query_id"])] = record
    return raw, successes


def safe_csv(path: Path, fieldnames: list[str], rows: list[dict]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            # Search-result titles are untrusted input. Prevent spreadsheet
            # formula execution when the judgment CSV is opened in Excel.
            safe = {key: ("'" + value if isinstance(value, str) and value.lstrip().startswith(("=", "+", "-", "@")) else value)
                    for key, value in row.items()}
            writer.writerow(safe)


def score(path: Path) -> dict:
    queries = load_queries()  # rechecks both frozen checksums
    meta = json.loads((path / "run.json").read_text(encoding="utf-8"))
    if meta["query_sha256"] != sha256(QUERIES) or meta["benchmark_v2_sha256"] != sha256(BENCHMARK_V2):
        raise ValueError("Run used a different query or benchmark checksum")
    benchmark = json.loads(BENCHMARK_V2.read_text(encoding="utf-8"))
    v1 = json.loads((ROOT / "docs/benchmark/v1/benchmark.json").read_text(encoding="utf-8"))
    raw, responses = load_responses(path)
    event_pages, evidence_pages, hosts = build_source_maps(benchmark, True)
    v1_pages, _, _ = build_source_maps(v1, False)
    trap_pages: dict[str, set[str]] = defaultdict(set)
    trap_opportunities = [o for o in benchmark["opportunities"] if o["expected_discovery"] != "eligible"]
    for opportunity in trap_opportunities:
        for source in opportunity["sources"]:
            trap_pages[normalize_url(source["url"])].add(opportunity["opportunity_id"])
    editions = eligible_editions(benchmark)
    lookup = {(o["split"], o["edition_key"]): o for o in editions}
    query_by_id = {q["id"]: q for q in queries}
    hits: dict[tuple[str, str], set[str]] = defaultdict(set)
    evidence_hits: dict[str, set[str]] = defaultdict(set)
    v1_hits: dict[str, set[str]] = defaultdict(set)
    per_query_editions: dict[tuple[str, str], set[tuple[str, str]]] = defaultdict(set)
    query_edition_urls: dict[tuple[str, str, str], set[str]] = defaultdict(set)
    trap_hits: dict[str, set[str]] = defaultdict(set)
    pooled: dict[str, dict] = {}
    possible: list[dict] = []
    for (provider, query_id), record in responses.items():
        for result in record["results"][:10]:
            url = result["url"]
            key = normalize_url(url)
            if not key:
                continue
            item = pooled.setdefault(key, {"normalized_url": key, "example_url": url, "title": result.get("title") or "", "providers": set(), "query_ids": set(), "exact_edition_keys": set()})
            item["providers"].add(provider)
            item["query_ids"].add(query_id)
            item["exact_edition_keys"].update(event_pages.get(key, set()))
            for edition_key in event_pages.get(key, set()):
                for split, ek in lookup:
                    if ek == edition_key:
                        hits[(split, edition_key)].add(provider)
                        per_query_editions[(provider, query_id)].add((split, edition_key))
                        query_edition_urls[(provider, query_id, edition_key)].add(key)
            for opportunity_id in trap_pages.get(key, set()):
                trap_hits[provider].add(opportunity_id)
            for case_id in evidence_pages.get(key, set()):
                evidence_hits[case_id].add(provider)
            for opportunity_id in v1_pages.get(key, set()):
                v1_hits[opportunity_id].add(provider)
            if key not in event_pages:
                host = key.split("/", 1)[0]
                if host in hosts:
                    possible.append({"provider": provider, "query_id": query_id, "url": url, "possible_edition_keys": "; ".join(sorted(hosts[host])), "review_status": "unjudged"})

    pool_rows = [
        {
            "normalized_url": key,
            "example_url": item["example_url"],
            "title": item["title"],
            "providers": "; ".join(sorted(item["providers"])),
            "query_ids": "; ".join(sorted(item["query_ids"])),
            "exact_edition_keys": "; ".join(sorted(item["exact_edition_keys"])),
            "judgment": "",
            "adjudicated_edition_key": "",
            "notes": "",
        }
        for key, item in sorted(pooled.items())
    ]
    safe_csv(path / "pooled_unique_urls.csv", list(pool_rows[0]) if pool_rows else ["normalized_url", "example_url", "title", "providers", "query_ids", "exact_edition_keys", "judgment", "adjudicated_edition_key", "notes"], pool_rows)
    safe_csv(path / "possible_same_site_hits.csv", ["provider", "query_id", "url", "possible_edition_keys", "review_status"], possible)

    matrix = []
    for (split, edition_key), opportunity in lookup.items():
        row = {"split": split, "country": opportunity["location"]["country"], "edition_key": edition_key, "opportunity": opportunity["name"]}
        for provider in PROVIDERS:
            qids = [qid for (p, qid), found in per_query_editions.items() if p == provider and (split, edition_key) in found]
            row[provider] = "; ".join(sorted(qids))
        matrix.append(row)
    safe_csv(path / "edition_hits.csv", ["split", "country", "edition_key", "opportunity", *PROVIDERS], matrix)

    scopes = {"live_ca": [o for o in editions if o["split"] == "live" and o["location"]["country"] == "CA"],
              "live": [o for o in editions if o["split"] == "live"],
              "replay": [o for o in editions if o["split"] == "replay"],
              "canada": [o for o in editions if o["location"]["country"] == "CA"],
              "us": [o for o in editions if o["location"]["country"] == "US"],
              "overall": editions}
    union = {}
    per_query = {}
    for provider in PROVIDERS:
        union[provider] = {}
        per_query[provider] = {}
        for name, subset in scopes.items():
            identities = {(o["split"], o["edition_key"]) for o in subset}
            found = sum(provider in hits.get(identity, set()) for identity in identities)
            union[provider][name] = {"hits": found, "denominator": len(identities), "recall": round(found / len(identities), 4) if identities else None}
            counts = [len(per_query_editions.get((provider, q["id"]), set()) & identities) for q in queries]
            per_query[provider][name] = {"mean_distinct_official_editions_per_query": round(statistics.mean(counts), 4),
                                         "edition_query_hit_fraction": round(sum(counts) / (len(queries) * len(identities)), 4) if identities else None}
    by_query = []
    for q in queries:
        place = q["scope"] if q["language"] == "en" else ("Montréal" if q["scope"] == "Montreal" else "Ville de Québec")
        intent = q["query"].removeprefix(place + " ")
        intent = intent.removesuffix(" upcoming 2026 2027").removesuffix(" à venir 2026 2027")
        for provider in PROVIDERS:
            found = per_query_editions.get((provider, q["id"]), set())
            by_query.append({"provider": provider, "query_id": q["id"], "scope": q["scope"], "language": q["language"],
                             "intent": intent, "eligible_edition_hits": len(found), "query_succeeded": (provider, q["id"]) in responses})
    safe_csv(path / "per_query_hits.csv", list(by_query[0]), by_query)
    grouped: dict[tuple[str, str, str], list[int]] = defaultdict(list)
    for row in by_query:
        grouped[(row["provider"], "intent", row["intent"])].append(row["eligible_edition_hits"])
        grouped[(row["provider"], "geography", row["scope"])].append(row["eligible_edition_hits"])
    group_rows = [{"provider": provider, "dimension": dimension, "group": group, "queries": len(counts),
                   "mean_eligible_editions_per_query": round(statistics.mean(counts), 4)}
                  for (provider, dimension, group), counts in sorted(grouped.items())]
    safe_csv(path / "query_group_summary.csv", list(group_rows[0]), group_rows)

    verified_cases = [c for c in benchmark["cases"] if c["expected_judgment"] == "verified"]
    evidence_recall = {provider: {"hits": sum(provider in evidence_hits.get(c["case_id"], set()) for c in verified_cases), "denominator": len(verified_cases)} for provider in PROVIDERS}
    v1_eligible = eligible_editions(v1)
    continuity = {provider: {"hits": sum(provider in v1_hits.get(o["opportunity_id"], set()) for o in v1_eligible), "denominator": len(v1_eligible)} for provider in PROVIDERS}
    latency = {}
    for provider in PROVIDERS:
        times = [r["latency_seconds"] for r in raw if r["provider"] == provider]
        latency[provider] = {"median_seconds": round(statistics.median(times), 3) if times else None,
                             "total_seconds": round(sum(times), 3)}
    serper_credits_used = sum(r["response"].get("credits", 0) for r in raw if r["provider"] == "serper" and isinstance(r.get("response"), dict) and isinstance(r["response"].get("credits"), (int, float)))
    metrics = {"scoring_basis": "Exact normalized cited official/event URLs only; lower bound pending manual adjudication of other pages.",
               "run_status": meta["status"], "query_sha256": meta["query_sha256"], "benchmark_v2_sha256": meta["benchmark_v2_sha256"],
               "union_recall_at_10": union, "per_query_recall_at_10": per_query,
               "evidence_page_recall_at_10": evidence_recall, "v1_continuity_recall_at_10": continuity,
               "requests": {p: {"attempts": meta["attempts"][p], "successes": meta["successes"][p]} for p in PROVIDERS},
               "latency": latency, "reserved_list_price_usd": meta["reserved_list_price_usd"],
               "exa_response_cost_usd": meta["exa_response_cost_usd"],
               "serper_response_credits_used": serper_credits_used,
               "trap_exposure_exact": {p: {"hits": len(trap_hits[p]), "denominator": len(trap_opportunities)} for p in PROVIDERS},
               "duplicate_edition_query_instances_exact": {p: sum(len(urls) > 1 for (provider, _, _), urls in query_edition_urls.items() if provider == p) for p in PROVIDERS},
               "pooled_unique_urls": len(pool_rows), "possible_same_site_hits": len(possible),
               "precision_and_new_discoveries": "Pending Raj's pooled-URL judgments and independent verification."}
    (path / "metrics.json").write_text(json.dumps(metrics, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    write_report(path, matrix, metrics, group_rows)
    return metrics


def write_report(path: Path, matrix: list[dict], metrics: dict, group_rows: list[dict]) -> None:
    lines = ["# Slice 2 offline search scoring", "", f"Run: `{path.name}`. Status: `{metrics['run_status']}`.", "",
             "Scores below are **confirmed exact cited-page hits**, a lower bound until the pooled URLs are manually judged. No provider recommendation is made.", "",
             "## Eligible edition × provider", "",
             "| Split | Country | Edition | Exa | Brave | Serper |", "| --- | --- | --- | --- | --- | --- |"]
    for row in matrix:
        label = row["opportunity"].replace("|", "\\|")
        cells = [row[p] or "—" for p in PROVIDERS]
        lines.append(f"| {row['split']} | {row['country']} | {label} | {cells[0]} | {cells[1]} | {cells[2]} |")
    lines += ["", "## Union recall@10, confirmed lower bound", "", "| Scope | Denominator | Exa | Brave | Serper |", "| --- | ---: | ---: | ---: | ---: |"]
    for scope in ("live_ca", "live", "replay", "canada", "us", "overall"):
        vals = [metrics["union_recall_at_10"][p][scope] for p in PROVIDERS]
        lines.append(f"| {scope} | {vals[0]['denominator']} | " + " | ".join(f"{v['hits']}/{v['denominator']} ({v['recall']:.1%})" for v in vals) + " |")
    lines += ["", "## Per-query recall@10", "", "For each scope, edition-query hit fraction = confirmed edition appearances divided by (58 queries × eligible editions). Mean hits/query counts distinct eligible editions in each query’s top 10. `per_query_hits.csv` gives every query and supports intent/geography breakdowns.", "",
              "| Scope | Provider | Edition-query hit fraction | Mean hits/query |", "| --- | --- | ---: | ---: |"]
    for scope in ("live_ca", "live", "replay", "overall"):
        for provider in PROVIDERS:
            val = metrics["per_query_recall_at_10"][provider][scope]
            lines.append(f"| {scope} | {provider} | {val['edition_query_hit_fraction']:.1%} | {val['mean_distinct_official_editions_per_query']:.3f} |")
    lines += ["", "### By intent and geography", "", "These are mean distinct confirmed eligible editions per query. The full counts are in `query_group_summary.csv`.", "",
              "| Dimension | Group | Exa | Brave | Serper |", "| --- | --- | ---: | ---: | ---: |"]
    group_lookup = {(r["provider"], r["dimension"], r["group"]): r["mean_eligible_editions_per_query"] for r in group_rows}
    for dimension, group in sorted({(r["dimension"], r["group"]) for r in group_rows}):
        values = [group_lookup.get((p, dimension, group), 0.0) for p in PROVIDERS]
        lines.append(f"| {dimension} | {group} | {values[0]:.3f} | {values[1]:.3f} | {values[2]:.3f} |")
    lines += ["", "## Requests, latency and cost", "", "| Provider | Attempts | Successes | Median latency | Total latency | List-price reservation | Response-reported cost |",
              "| --- | ---: | ---: | ---: | ---: | ---: | ---: |"]
    for provider in PROVIDERS:
        req = metrics["requests"][provider]
        lat = metrics["latency"][provider]
        actual = f"${metrics['exa_response_cost_usd']:.3f}" if provider == "exa" else "Unavailable from API"
        lines.append(f"| {provider} | {req['attempts']} | {req['successes']} | {lat['median_seconds']}s | {lat['total_seconds']}s | ${metrics['reserved_list_price_usd'][provider]:.3f} | {actual} |")
    lines += ["", f"Serper responses report {metrics['serper_response_credits_used']} credits used (one per successful query here), but no dollar charge or remaining balance. Brave responses do not provide billable cost or free-credit balance. Their list-price reservation is an upper-bound usage estimate, not an observed charge. Exa's response field is itself an estimated dollar cost. The US$5 cap was enforced against reserved list price for every attempt, including retries.",
              "", "## Exact-source trap exposure and duplicates", "",
              "| Provider | Ineligible/ambiguous opportunities surfaced | Query-edition instances with 2+ cited URLs |", "| --- | ---: | ---: |"]
    for provider in PROVIDERS:
        trap = metrics["trap_exposure_exact"][provider]
        lines.append(f"| {provider} | {trap['hits']}/{trap['denominator']} | {metrics['duplicate_edition_query_instances_exact'][provider]} |")
    lines += ["", "These are exact cited-source diagnostics; manual judging may find additional traps or duplicates.",
              "", "## V1 continuity check (separate)", "",
              "| Provider | Exact eligible editions found |", "| --- | ---: |"]
    for provider in PROVIDERS:
        value = metrics["v1_continuity_recall_at_10"][provider]
        lines.append(f"| {provider} | {value['hits']}/{value['denominator']} |")
    lines += ["", "V1 uses the same saved responses; no extra queries were issued and its scores are not pooled with v2.",
              "", "## Manual judging handoff", "",
              f"`pooled_unique_urls.csv` contains {metrics['pooled_unique_urls']} unique normalized URLs with provider/query provenance and blank judgment columns. Set `judgment` to `relevant_edition`, `irrelevant`, or `unjudged`; for a relevant page, set `adjudicated_edition_key` and explain any non-exact match in `notes`. `possible_same_site_hits.csv` contains {metrics['possible_same_site_hits']} same-site candidates that cannot be credited without review. Precision, new discoveries and any provider recommendation remain pending.",
              "", "One edition changes live recall by 12.5 percentage points (8 live editions) and live Canadian recall by about 14.3 points (7 editions). A one- or two-edition gap is inconclusive.", ""]
    (path / "report.md").write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("Usage: python3 scripts/score_search_provider_benchmark.py RUN_DIR")
    score(Path(sys.argv[1]).resolve())
