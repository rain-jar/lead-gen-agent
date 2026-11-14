"""Run the frozen Slice 2 query set against Exa, Brave, and Serper.

Only public search responses are saved. API keys are read from the repository's
ignored .env file and are never written to a run artifact.
"""

from __future__ import annotations

import csv
import hashlib
import json
import ssl
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[1]
QUERIES = ROOT / "docs/benchmark/search-provider/queries-v1.tsv"
BENCHMARK_V2 = ROOT / "docs/benchmark/v2/benchmark.json"
QUERY_SHA256 = "7cc841763f57a56850194a706702ea1d670a43fc7fdcb4813cafd445ded78c1f"
V2_SHA256 = "d7efe922893222b8e60e9847d548190098baedc66f2fb7c1a89402561c9c7c81"
CAP_USD = 5.0
PROVIDERS = ("exa", "brave", "serper")
# Published search prices checked 2026-11-14. Reserve the full list price per
# attempt for cap enforcement, even if the account has free credits.
UNIT_PRICE_USD = {"exa": 0.007, "brave": 0.005, "serper": 0.001}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_queries() -> list[dict[str, str]]:
    if sha256(QUERIES) != QUERY_SHA256 or sha256(BENCHMARK_V2) != V2_SHA256:
        raise ValueError("Frozen query or v2 benchmark checksum changed; stop before API calls")
    with QUERIES.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle, delimiter="\t"))
    if len(rows) != 58 or [r["id"] for r in rows] != [f"q-{n:03d}" for n in range(1, 59)]:
        raise ValueError("Frozen query IDs/count are invalid")
    if len({r["query"] for r in rows}) != 58:
        raise ValueError("Frozen queries are not unique")
    return rows


def load_keys() -> dict[str, str]:
    """Read only the three approved keys from the local .env; never print them."""
    values: dict[str, str] = {}
    for raw_line in (ROOT / ".env").read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        name, value = line.split("=", 1)
        name = name.strip()
        if name in {"EXA_API_KEY", "BRAVE_API_KEY", "SERPER_API_KEY"}:
            value = value.strip()
            if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
                value = value[1:-1]
            values[name] = value
    if any(not values.get(name) for name in ("EXA_API_KEY", "BRAVE_API_KEY", "SERPER_API_KEY")):
        raise ValueError("A required API key is missing from .env")
    return values


def request_for(provider: str, row: dict[str, str], key: str) -> Request:
    ca = row["scope"] != "United States"
    country = "CA" if ca else "US"
    language = row["language"]
    query = row["query"]
    if provider == "exa":
        # Plain /search only: ten metadata-only results, no contents or synthesis.
        body = {"query": query, "numResults": 10, "userLocation": country}
        return Request(
            "https://api.exa.ai/search",
            data=json.dumps(body).encode("utf-8"),
            headers={"Content-Type": "application/json", "x-api-key": key},
            method="POST",
        )
    if provider == "brave":
        params = urlencode({"q": query, "country": country, "search_lang": language, "count": 10})
        return Request(
            "https://api.search.brave.com/res/v1/web/search?" + params,
            headers={"Accept": "application/json", "x-subscription-token": key},
        )
    if provider == "serper":
        body = {"q": query, "gl": country.lower(), "hl": language, "num": 10}
        return Request(
            "https://google.serper.dev/search",
            data=json.dumps(body).encode("utf-8"),
            headers={"Content-Type": "application/json", "X-API-KEY": key},
            method="POST",
        )
    raise ValueError("Unknown provider")


def compact_results(provider: str, payload: dict) -> list[dict]:
    if provider == "exa":
        source = payload.get("results", [])
        return [
            {"rank": i, "title": item.get("title"), "url": item.get("url"), "snippet": None}
            for i, item in enumerate(source[:10], 1)
            if isinstance(item, dict) and item.get("url")
        ]
    if provider == "brave":
        source = (payload.get("web") or {}).get("results", [])
        return [
            {"rank": i, "title": item.get("title"), "url": item.get("url"), "snippet": item.get("description")}
            for i, item in enumerate(source[:10], 1)
            if isinstance(item, dict) and item.get("url")
        ]
    source = payload.get("organic", [])
    return [
        {"rank": i, "title": item.get("title"), "url": item.get("link"), "snippet": item.get("snippet")}
        for i, item in enumerate(source[:10], 1)
        if isinstance(item, dict) and item.get("link")
    ]


def call_provider(request: Request) -> tuple[int | None, dict | None, str | None, float]:
    started = time.monotonic()
    # python.org's macOS Python may lack a configured default CA bundle. Use
    # the operating system's CA file when present; never disable verification.
    system_ca = Path("/etc/ssl/cert.pem")
    context = ssl.create_default_context(cafile=str(system_ca) if system_ca.is_file() else None)
    try:
        with urlopen(request, timeout=35, context=context) as response:
            status = response.status
            payload = json.load(response)
            if not isinstance(payload, dict):
                return status, None, "non_object_response", time.monotonic() - started
            return status, payload, None, time.monotonic() - started
    except HTTPError as error:
        # Never save error bodies: providers may echo request headers or tokens.
        return error.code, None, "http_error", time.monotonic() - started
    except URLError as error:
        if isinstance(error.reason, ssl.SSLCertVerificationError):
            return None, None, "tls_verification_error", time.monotonic() - started
        return None, None, "network_error", time.monotonic() - started
    except (TimeoutError, OSError):
        return None, None, "network_error", time.monotonic() - started
    except (ValueError, UnicodeDecodeError):
        return None, None, "invalid_json", time.monotonic() - started


def timestamp() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def write_meta(path: Path, meta: dict) -> None:
    path.write_text(json.dumps(meta, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def run() -> Path:
    queries = load_queries()
    keys = load_keys()
    key_by_provider = {"exa": keys["EXA_API_KEY"], "brave": keys["BRAVE_API_KEY"], "serper": keys["SERPER_API_KEY"]}
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out = ROOT / "artifacts/search-provider" / run_id
    out.mkdir(parents=True, exist_ok=False)
    meta = {
        "run_id": run_id,
        "started_at": timestamp(),
        "status": "running",
        "query_sha256": QUERY_SHA256,
        "benchmark_v2_sha256": V2_SHA256,
        "cap_usd": CAP_USD,
        "price_checked_date": "2026-11-14",
        "unit_price_usd": UNIT_PRICE_USD,
        "attempts": {p: 0 for p in PROVIDERS},
        "successes": {p: 0 for p in PROVIDERS},
        "reserved_list_price_usd": {p: 0.0 for p in PROVIDERS},
        "exa_response_cost_usd": 0.0,
        "warnings": ["Free-credit balances and Brave/Serper actual billing are not available from search responses."],
    }
    write_meta(out / "run.json", meta)
    reserved_total = 0.0
    abort = False
    with (out / "raw.ndjson").open("w", encoding="utf-8") as raw:
        for query_index, row in enumerate(queries):
            order = PROVIDERS[query_index % 3 :] + PROVIDERS[: query_index % 3]
            for provider in order:
                for attempt in (1, 2):
                    reserve = UNIT_PRICE_USD[provider]
                    if reserved_total + reserve > CAP_USD + 1e-9:
                        meta["status"] = "stopped_at_cap"
                        abort = True
                        break
                    reserved_total += reserve
                    meta["attempts"][provider] += 1
                    meta["reserved_list_price_usd"][provider] = round(meta["reserved_list_price_usd"][provider] + reserve, 6)
                    status, payload, error, latency = call_provider(request_for(provider, row, key_by_provider[provider]))
                    success = status == 200 and payload is not None
                    if success:
                        meta["successes"][provider] += 1
                        if provider == "exa":
                            reported = (payload.get("costDollars") or {}).get("total")
                            if isinstance(reported, (int, float)) and reported >= 0:
                                meta["exa_response_cost_usd"] = round(meta["exa_response_cost_usd"] + reported, 6)
                    record = {
                        "query_id": row["id"], "query": row["query"], "scope": row["scope"],
                        "language": row["language"], "provider": provider, "attempt": attempt,
                        "timestamp": timestamp(), "http_status": status, "error": error,
                        "latency_seconds": round(latency, 3), "results": compact_results(provider, payload) if success else [],
                        "response": payload if success else None,
                    }
                    serialized = json.dumps(record, ensure_ascii=False)
                    for secret in keys.values():
                        serialized = serialized.replace(secret, "[REDACTED]")
                    raw.write(serialized + "\n")
                    raw.flush()
                    write_meta(out / "run.json", meta)
                    print(f"{row['id']} {provider} attempt={attempt} status={status or error} results={len(record['results'])}", flush=True)
                    if success:
                        break
                    if status in (400, 401, 402, 403) or error == "tls_verification_error":
                        meta["status"] = f"stopped_provider_error_{provider}_{status}"
                        abort = True
                        break
                    transient = status == 429 or (status is not None and 500 <= status <= 599) or error == "network_error"
                    if attempt == 1 and transient:
                        time.sleep(1)
                        continue
                    break
                if abort:
                    break
            if abort:
                break
    if not abort:
        meta["status"] = "complete"
    meta["finished_at"] = timestamp()
    meta["reserved_total_usd"] = round(reserved_total, 6)
    write_meta(out / "run.json", meta)
    print(f"Run directory: {out}")
    print(f"Status: {meta['status']}; reserved list-price total: ${reserved_total:.3f}")
    return out


if __name__ == "__main__":
    run()
