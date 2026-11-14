"""Focused checks for the frozen Slice 2 request and offline scoring contracts."""

import json
import sys
import tempfile
import unittest
from pathlib import Path
from urllib.parse import parse_qs, urlsplit


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from search_provider_benchmark import PROVIDERS, QUERY_SHA256, V2_SHA256, compact_results, load_queries, request_for  # noqa: E402
from score_search_provider_benchmark import normalize_url, score  # noqa: E402


class SearchProviderBenchmarkTests(unittest.TestCase):
    def test_frozen_queries_and_request_parameters(self):
        queries = load_queries()
        self.assertEqual(len(queries), 58)
        english, french = queries[0], queries[8]
        exa = json.loads(request_for("exa", english, "test-key").data)
        self.assertEqual(exa, {"query": english["query"], "numResults": 10, "userLocation": "CA"})
        brave = parse_qs(urlsplit(request_for("brave", french, "test-key").full_url).query)
        self.assertEqual([brave[k][0] for k in ("country", "search_lang", "count")], ["CA", "fr", "10"])
        serper = json.loads(request_for("serper", french, "test-key").data)
        self.assertEqual([serper[k] for k in ("gl", "hl", "num")], ["ca", "fr", 10])

    def test_empty_results_and_url_normalization(self):
        self.assertEqual(compact_results("exa", {"results": []}), [])
        self.assertEqual(compact_results("brave", {"web": {"results": []}}), [])
        self.assertEqual(compact_results("serper", {"organic": []}), [])
        self.assertEqual(normalize_url("http://WWW.Example.COM/a/?utm_source=x#f"), "example.com/a")

    def test_pooled_url_dedup_and_reproducible_offline_score(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)
            meta = {"status": "fixture", "query_sha256": QUERY_SHA256, "benchmark_v2_sha256": V2_SHA256,
                    "attempts": {p: int(p != "serper") for p in PROVIDERS},
                    "successes": {p: int(p != "serper") for p in PROVIDERS},
                    "reserved_list_price_usd": {p: 0 for p in PROVIDERS}, "exa_response_cost_usd": 0}
            (path / "run.json").write_text(json.dumps(meta))
            url = "https://luma.com/lt0uuj20"
            records = []
            for provider, found_url in (("exa", url), ("brave", url + "/?utm_source=test")):
                records.append({"query_id": "q-001", "query": "fixture", "scope": "Canada", "language": "en",
                                "provider": provider, "attempt": 1, "timestamp": "fixture", "http_status": 200,
                                "error": None, "latency_seconds": 0.1,
                                "results": [{"rank": 1, "title": "NEXT AI", "url": found_url, "snippet": None}], "response": {}})
            (path / "raw.ndjson").write_text("\n".join(json.dumps(r) for r in records) + "\n")
            first = score(path)
            second = score(path)
            self.assertEqual(first, second)
            self.assertEqual(first["pooled_unique_urls"], 1)
            self.assertEqual(first["union_recall_at_10"]["exa"]["live_ca"]["hits"], 1)
            self.assertEqual(first["union_recall_at_10"]["brave"]["live_ca"]["hits"], 1)
            self.assertEqual(first["union_recall_at_10"]["serper"]["live_ca"]["hits"], 0)


if __name__ == "__main__":
    unittest.main()
