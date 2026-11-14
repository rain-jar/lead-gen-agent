"""One bounded live discovery evaluation using Exa then Serper fallback."""
from __future__ import annotations

import csv
import hashlib
import json
import ssl
import statistics
import time
from dataclasses import replace
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from .core import Query, add_months, generate_queries, make_candidate, page_kind
from .__main__ import process

ROOT = Path(__file__).resolve().parents[3]
PRICES = {"exa": 0.007, "serper": 0.001}
RUN_CAP = 1.25
SLICE_CAP = 4.0


def load_keys() -> dict[str, str]:
    values = {}
    for line in (ROOT / ".env").read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        name, value = line.split("=", 1)
        if name in ("EXA_API_KEY", "SERPER_API_KEY"):
            values[name] = value.strip().strip("\"'")
    if not all(values.get(name) for name in ("EXA_API_KEY", "SERPER_API_KEY")):
        raise ValueError("Exa or Serper key missing from ignored .env")
    return values


def request_for(provider: str, query: Query, key: str, highlights: bool) -> Request:
    country = "US" if query.phase == "us" else "CA"
    if provider == "exa":
        body = {"query": query.query, "numResults": 10, "userLocation": country}
        if highlights:
            body["contents"] = {"highlights": True}
        return Request("https://api.exa.ai/search", data=json.dumps(body).encode(), headers={"Content-Type": "application/json", "x-api-key": key}, method="POST")
    body = {"q": query.query, "gl": country.lower(), "hl": query.language, "num": 10}
    return Request("https://google.serper.dev/search", data=json.dumps(body).encode(), headers={"Content-Type": "application/json", "X-API-KEY": key}, method="POST")


def call(request: Request) -> tuple[int | None, dict | None, str | None, float]:
    started = time.monotonic()
    ca_file = Path("/etc/ssl/cert.pem")
    context = ssl.create_default_context(cafile=str(ca_file) if ca_file.is_file() else None)
    try:
        with urlopen(request, timeout=35, context=context) as response:
            payload = json.load(response)
            return response.status, payload if isinstance(payload, dict) else None, None if isinstance(payload, dict) else "invalid_json", time.monotonic() - started
    except HTTPError as error:
        return error.code, None, "http_error", time.monotonic() - started
    except URLError as error:
        return None, None, "tls_verification_error" if isinstance(error.reason, ssl.SSLCertVerificationError) else "network_error", time.monotonic() - started
    except (TimeoutError, OSError):
        return None, None, "network_error", time.monotonic() - started
    except (ValueError, UnicodeDecodeError):
        return None, None, "invalid_json", time.monotonic() - started


def compact(provider: str, payload: dict | None) -> list[dict]:
    if not payload:
        return []
    source = payload.get("results", []) if provider == "exa" else payload.get("organic", [])
    results = []
    for rank, item in enumerate(source[:10], 1):
        if not isinstance(item, dict):
            continue
        url = item.get("url") if provider == "exa" else item.get("link")
        if not url:
            continue
        highlights = item.get("highlights") or []
        snippet = " ".join(str(h) for h in highlights) if provider == "exa" else item.get("snippet")
        results.append({"rank": rank, "title": item.get("title") or "", "url": url, "snippet": snippet or None})
    return results


class LiveRun:
    def __init__(self, out: Path, reference_date: date):
        self.out, self.ref = out, reference_date
        self.keys = load_keys()
        self.out.mkdir(parents=True, exist_ok=False)
        self.raw = (out / "raw.ndjson").open("w", encoding="utf-8")
        self.reserved = 0.0
        self.attempts = {"exa": 0, "serper": 0}
        self.successes = {"exa": 0, "serper": 0}
        self.fallbacks = {"F1": 0, "F2": 0}
        self.latencies = {"exa": [], "serper": []}
        self.exa_reported = 0.0
        self.status = "running"
        self.snippet_enabled = False
        self.probe_cost = None
        self.probe_latency = None
        self.records = []
        self.network_failures = 0

    def _save_progress(self) -> None:
        progress = {"status": self.status, "reference_date": self.ref.isoformat(), "attempts": self.attempts, "successes": self.successes, "fallbacks": self.fallbacks, "reserved_usd": self.reserved, "exa_reported_cost_usd": round(self.exa_reported, 6), "snippet_probe_cost_usd": self.probe_cost, "snippet_enabled": self.snippet_enabled, "run_cap_usd": RUN_CAP, "slice_cap_usd": SLICE_CAP}
        (self.out / "run.json").write_text(json.dumps(progress, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    def _attempt(self, provider: str, query: Query, highlights: bool) -> tuple[list[dict] | None, dict | None]:
        for attempt in (1, 2):
            price = PRICES[provider]
            if self.reserved + price > RUN_CAP + 1e-9 or self.reserved + price > SLICE_CAP + 1e-9:
                self.status = "stopped_at_cap"
                return None, None
            self.reserved = round(self.reserved + price, 6)
            self.attempts[provider] += 1
            key = self.keys["EXA_API_KEY" if provider == "exa" else "SERPER_API_KEY"]
            status, payload, error, latency = call(request_for(provider, query, key, highlights))
            self.latencies[provider].append(latency)
            success = status == 200 and payload is not None
            self.network_failures = 0 if success else self.network_failures + 1 if error == "network_error" else 0
            if self.network_failures >= 4:
                self.status = "stopped_network_unavailable"
            if success:
                self.successes[provider] += 1
                if provider == "exa":
                    reported = (payload.get("costDollars") or {}).get("total")
                    if isinstance(reported, (int, float)):
                        self.exa_reported += reported
            results = compact(provider, payload) if success else []
            record = {"query_id": query.id, "query": query.query, "scope": query.scope, "language": query.language, "query_family": query.family, "provider": provider, "attempt": attempt, "timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds"), "http_status": status, "error": error, "latency_seconds": round(latency, 3), "results": results, "response": payload if success else None}
            serialized = json.dumps(record, ensure_ascii=False)
            for secret in self.keys.values():
                serialized = serialized.replace(secret, "[REDACTED]")
            self.raw.write(serialized + "\n")
            self.raw.flush()
            self.records.append(record)
            self._save_progress()
            if self.status == "stopped_network_unavailable":
                return None, None
            if success:
                return results, payload
            if status in (400, 401, 402, 403) or error == "tls_verification_error":
                self.status = f"stopped_provider_error_{provider}_{status or error}"
                return None, None
            transient = status == 429 or (status is not None and 500 <= status < 600) or error == "network_error"
            if not transient or attempt == 2:
                return None, None
            time.sleep(1)
        return None, None

    def _query(self, query: Query, probe: bool = False) -> None:
        exa, payload = self._attempt("exa", query, self.snippet_enabled or probe)
        if probe:
            total = (payload.get("costDollars") or {}).get("total") if payload else None
            self.probe_cost = total if isinstance(total, (int, float)) else None
            self.probe_latency = self.latencies["exa"][-1] if self.latencies["exa"] else None
            self.snippet_enabled = self.probe_cost is not None and self.probe_cost - PRICES["exa"] <= 0.007 + 1e-9
            self._save_progress()
            # The price probe is the first real query; its response is kept in the run.
        if self.status != "running":
            return
        if exa is None:
            reason = "F1"
        elif not any(page_kind(r["url"], r["title"], r.get("snippet") or "") in ("event_edition", "event_series", "listing_or_aggregator") for r in exa):
            reason = "F2"
        else:
            reason = None
        if reason:
            self.fallbacks[reason] += 1
            self._attempt("serper", query, False)

    def _second_hops(self) -> list[Query]:
        names = set()
        for record in self.records:
            if record["provider"] not in ("exa", "serper") or record["http_status"] != 200 or record["scope"] == "United States":
                continue
            for result in record["results"]:
                item = make_candidate(result["title"], result["url"], record["scope"], "ca", self.ref, result.get("snippet") or "")
                if item.page_kind in ("program", "event_series") and item.event_date is None and len(item.event_name) >= 8:
                    names.add(item.event_name)
        years = sorted({(self.ref + timedelta(days=7)).year, add_months(self.ref, 6).year})
        year_text = " ".join(map(str, years))
        return [Query(f"q-hop-{i:03d}", f"{name} demo day OR pitch finale {year_text}", "Canada", "en", "ca", "second_hop") for i, name in enumerate(sorted(names)[:15], 1)]

    def run(self) -> dict:
        base = generate_queries(self.ref, us=True)
        canada = [q for q in base if q.phase == "ca"]
        usa = [q for q in base if q.phase == "us"]
        queries = []
        for i, query in enumerate(canada):
            queries.append(query)
            self._query(query, probe=i == 0)
            if self.status != "running":
                break
        if self.status == "running":
            for query in self._second_hops():
                queries.append(query)
                self._query(query)
                if self.status != "running":
                    break
        if self.status == "running":
            for query in usa:
                queries.append(query)
                self._query(query)
                if self.status != "running":
                    break
        self.raw.close()
        with (self.out / "queries.tsv").open("w", newline="", encoding="utf-8") as handle:
            writer = csv.writer(handle, delimiter="\t")
            writer.writerow(("id", "language", "scope", "family", "query"))
            for q in queries:
                writer.writerow((q.id, q.language, q.scope, q.family, q.query))
        discovery_meta = process(self.out / "raw.ndjson", self.out, self.ref, self.out.name)
        meta = {**discovery_meta, "mode": "live_evaluation", "status": "complete" if self.status == "running" else self.status, "query_sha256": hashlib.sha256((self.out / "queries.tsv").read_bytes()).hexdigest(), "queries": len(queries), "attempts": self.attempts, "successes": self.successes, "fallbacks": self.fallbacks, "reserved_usd": self.reserved, "exa_reported_cost_usd": round(self.exa_reported, 6), "serper_list_price_usd": round(self.attempts["serper"] * PRICES["serper"], 6), "snippet_probe_cost_usd": self.probe_cost, "snippet_enabled": self.snippet_enabled, "latency_seconds": {p: {"total": round(sum(v), 3), "median": round(statistics.median(v), 3) if v else None} for p, v in self.latencies.items()}, "run_cap_usd": RUN_CAP, "slice_cap_usd": SLICE_CAP}
        (self.out / "run.json").write_text(json.dumps(meta, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return meta
