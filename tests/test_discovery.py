"""Approved Slice 3 verification: pure rules and bounded provider orchestration."""
import sys
import json
import random
import tempfile
import unittest
from datetime import date
from pathlib import Path
from urllib.parse import urlsplit
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from leadgen.discovery import core


class DiscoveryTests(unittest.TestCase):
    def test_queries_and_leakage(self):
        queries = core.generate_queries(date(2026, 11, 14), us=True)
        self.assertEqual((len(queries), sum(q.phase == "ca" for q in queries)), (123, 97))
        self.assertTrue(all(q.phase == "ca" for q in queries[:97]))
        self.assertEqual(queries, core.generate_queries(date(2026, 11, 14), us=True))
        joined = " ".join(q.query for q in queries).lower()
        benchmark = json.loads((Path(__file__).resolve().parents[1] / "docs/benchmark/v2/benchmark.json").read_text())
        for opportunity in benchmark["opportunities"]:
            self.assertNotIn(opportunity["name"].casefold(), joined)
            for source in opportunity["sources"]:
                host = urlsplit(source["url"]).hostname
                if host:
                    self.assertNotIn(host.casefold(), joined)

    def test_discovery_code_has_no_benchmark_names_or_hosts(self):
        root = Path(__file__).resolve().parents[1]
        code = " ".join(p.read_text(encoding="utf-8") for p in sorted((root / "src").rglob("*.py"))).casefold()
        benchmark = json.loads((root / "docs/benchmark/v2/benchmark.json").read_text())
        for opportunity in benchmark["opportunities"]:
            self.assertNotIn(opportunity["name"].casefold(), code)
            for source in opportunity["sources"]:
                host = (urlsplit(source["url"]).hostname or "").casefold().removeprefix("www.")
                platforms = ("luma.com", "eventbrite.com", "meetup.com", "linkedin.com", "facebook.com", "instagram.com", "x.com")
                if host and not host.endswith(platforms):  # generic platforms are page-kind rules, not leakage
                    self.assertNotIn(host, code)

    def test_url_and_kind(self):
        self.assertEqual(core.canonical_url("HTTPS://WWW.Example.com/x/?utm_source=a&gclid=b#top"), "https://example.com/x")
        self.assertEqual(core.page_kind("https://example.com/accelerator", "Accelerator program", ""), "program")
        self.assertEqual(core.page_kind("https://luma.com/abc", "2027 pitch final", ""), "listing_or_aggregator")
        self.assertEqual(core.page_kind("https://example.com/2027-pitch-final", "2027 pitch final", ""), "event_edition")

    def test_dates_window(self):
        ref = date(2026, 11, 14)
        for phrase in ("December 2, 2026", "2 décembre 2026", "2026-12-02"):
            self.assertEqual(core.parse_date(phrase, ref).start, date(2026, 12, 2))
        self.assertEqual(core.window_status(date(2026, 11, 20), None, ref), "too_soon")
        self.assertEqual(core.window_status(date(2026, 11, 21), None, ref), "in_window")
        self.assertEqual(core.window_status(date(2027, 5, 14), None, ref), "in_window")
        self.assertEqual(core.window_status(date(2027, 5, 15), None, ref), "too_far")
        self.assertEqual(core.window_status(date(2027, 5, 14), date(2027, 5, 15), ref), "too_far")
        self.assertEqual(core.parse_date("Spring 2027", ref).confidence, "season_or_month")

    def test_edition_and_merge(self):
        a = core.make_candidate("Toronto Pitch Final 2027", "https://example.com/pitch-2027", "Toronto", "ca", date(2026, 11, 14))
        b = core.make_candidate("Toronto Pitch Final 2027", "https://example.com/pitch-2027?utm_source=x", "Toronto", "ca", date(2026, 11, 14))
        c = core.make_candidate("Montréal Pitch Final 2027", "https://example.com/pitch-2027", "Toronto", "ca", date(2026, 11, 14))
        d = core.make_candidate("Toronto Pitch Final 2026", "https://example.com/pitch-2026", "Toronto", "ca", date(2026, 11, 14))
        self.assertEqual(len(core.merge_candidates([a, b])), 1)
        self.assertEqual(len(core.merge_candidates([a, c, d])), 2)
        conflicted = next(x for x in core.merge_candidates([a, c, d]) if "city_conflict" in x.conflict_reasons)
        self.assertIsNone(conflicted.city)

    def test_fallback_and_cap(self):
        q = core.Query("q1", "x pitch 2027", "Toronto", "en", "ca", "core")
        calls = []
        def search(provider, query):
            calls.append(provider)
            if provider == "exa":
                return []
            return [{"rank": 1, "title": "Pitch Final 2027", "url": "https://example.com/final-2027", "snippet": ""}]
        runner = core.Runner(search, cap=0.008)
        runner.search_query(q)
        self.assertEqual(calls, ["exa", "serper"])
        self.assertEqual(runner.fallbacks["F2"], 1)
        runner.search_query(q)
        self.assertEqual(calls, ["exa", "serper"])
        self.assertEqual(runner.status, "stopped_at_cap")
        def fails(provider, query):
            if provider == "exa":
                raise core.TransientSearchError("timeout")
            return []
        runner = core.Runner(fails, cap=0.03)
        runner.search_query(q)
        self.assertEqual(runner.fallbacks["F1"], 1)
        self.assertEqual(runner.attempts["exa"], 2)

    def test_watch_dates(self):
        ref = date(2026, 11, 14)
        self.assertEqual(core.recheck_date("lineup_pending", ref, date(2026, 12, 1), None), date(2026, 12, 2))
        self.assertEqual(core.recheck_date("date_pending", ref, None, None), date(2026, 11, 21))
        self.assertEqual(core.recheck_date("enters_window_later", ref, None, date(2027, 7, 7)), date(2027, 1, 7))

    def test_page_city_beats_query_and_accent_folds(self):
        item = core.make_candidate("La finale des créateurs 2027 · Luma", "https://luma.com/finale-2027", "Toronto", "ca", date(2026, 11, 14), "Montréal, Québec")
        self.assertEqual(item.city, "Montréal")
        self.assertEqual(core.fold("Montreal"), core.fold("Montréal"))
        self.assertNotIn("luma", item.event_name.lower())

    def test_site_name_and_past_champion_do_not_name_event_year(self):
        item = core.make_candidate("Cedar Institute | Spring Pitch Final", "https://example.org/spring-pitch", "Ottawa", "ca", date(2026, 11, 14), "Last year's 2026 champion returns. Copyright 2027.")
        self.assertEqual(item.event_name, "Spring Pitch Final")
        self.assertIsNone(item.edition_year)
        self.assertIsNone(item.city)
        self.assertIn("city_unknown", item.unknown_reasons)

    def test_canonical_url_merges_and_conflicts_split(self):
        ref = date(2026, 11, 14)
        a = core.make_candidate("Maple Pitch 2027", "https://www.example.org/final/?utm_x=1", "Ottawa", "ca", ref, "Ottawa")
        b = core.make_candidate("Maple Pitch 2027", "https://example.org/final", "Montreal", "ca", ref, "Ottawa")
        c = core.make_candidate("Maple Pitch 2026", "https://example.org/final", "Ottawa", "ca", ref, "Ottawa")
        merged = core.merge_candidates([a, b, c])
        self.assertEqual(len(merged), 1)
        self.assertTrue(merged[0].edition_conflict)
        self.assertIsNone(merged[0].edition_year)
        self.assertIn("year_conflict", merged[0].conflict_reasons)

    def test_url_merge_order_independent(self):
        ref = date(2026, 11, 14)
        items = [
            core.make_candidate("Maple Pitch 2027", "https://example.org/final", "Canada", "ca", ref, "Held in Ottawa"),
            core.make_candidate("Maple Pitch 2026", "https://example.org/final?utm_source=a", "Canada", "ca", ref, "Last year's champion"),
            core.make_candidate("Maple Pitch", "https://example.org/final/", "Canada", "ca", ref, "University of Calgary team"),
        ]
        baseline = [x.dict() for x in core.merge_candidates(items)]
        for seed in range(5):
            shuffled = items[:]
            random.Random(seed).shuffle(shuffled)
            self.assertEqual([x.dict() for x in core.merge_candidates(shuffled)], baseline)

    def test_snippet_affiliation_is_not_city_but_venue_is(self):
        ref = date(2026, 11, 14)
        affiliation = core.make_candidate("Maple Pitch", "https://example.org/final", "Canada", "ca", ref, "University of Calgary team competes")
        venue = core.make_candidate("Maple Pitch", "https://example.org/final", "Canada", "ca", ref, "Hosted in Ottawa on Friday")
        self.assertIsNone(affiliation.city)
        self.assertEqual(venue.city, "Ottawa")

    def test_full_raw_title_used_for_city(self):
        item = core.make_candidate("University of Toronto | Maple Pitch Final", "https://example.org/final", "Canada", "ca", date(2026, 11, 14))
        self.assertEqual(item.event_name, "Maple Pitch Final")
        self.assertEqual(item.city, "Toronto")

    def test_watch_one_row_per_edition(self):
        from leadgen.discovery.__main__ import watch_items
        item = core.make_candidate("Maple Pitch 2027", "https://example.org/final-2027", "Ottawa", "ca", date(2026, 11, 14), "Applications open in Ottawa")
        rows = watch_items([item], date(2026, 11, 14), "test")
        self.assertEqual(len(rows), 1)
        self.assertGreaterEqual(len(rows[0]["reasons"]), 2)

    def test_replay_window_uses_edition_reference(self):
        from scripts.score_discovery import replay_window_status
        opportunity = {"split": "replay", "reference_date": "2026-02-27", "event_date": "2026-04-01", "event_end_date": None}
        self.assertEqual(replay_window_status(opportunity), "in_window")

    def test_live_probe_reserves_price_and_redacts_keys(self):
        from leadgen.discovery.live import LiveRun
        with tempfile.TemporaryDirectory() as temp:
            with patch("leadgen.discovery.live.load_keys", return_value={"EXA_API_KEY": "synthetic-secret", "SERPER_API_KEY": "synthetic-other"}), patch("leadgen.discovery.live.call", return_value=(200, {"results": [{"title": "Maple Pitch 2027", "url": "https://example.org/final", "highlights": ["Held in Ottawa"]}], "costDollars": {"total": 0.007}}, None, 0.01)):
                run = LiveRun(Path(temp) / "run", date(2026, 11, 14))
                run._query(core.Query("q-001", "Canada pitch final upcoming 2026 2027", "Canada", "en", "ca", "en_core"), probe=True)
                run.raw.close()
                self.assertTrue(run.snippet_enabled)
                self.assertEqual(run.reserved, 0.007)
                self.assertNotIn("synthetic-secret", (run.out / "raw.ndjson").read_text())

    def test_live_stops_repeated_network_failure(self):
        from leadgen.discovery.live import LiveRun
        with tempfile.TemporaryDirectory() as temp:
            with patch("leadgen.discovery.live.load_keys", return_value={"EXA_API_KEY": "synthetic-secret", "SERPER_API_KEY": "synthetic-other"}), patch("leadgen.discovery.live.call", return_value=(None, None, "network_error", 0.01)), patch("leadgen.discovery.live.time.sleep"):
                run = LiveRun(Path(temp) / "run", date(2026, 11, 14))
                run._query(core.Query("q-001", "Canada pitch final upcoming 2026 2027", "Canada", "en", "ca", "en_core"), probe=True)
                run.raw.close()
                self.assertEqual(run.status, "stopped_network_unavailable")
                self.assertEqual(sum(run.attempts.values()), 4)

    def test_ndjson_unicode_separator_is_not_a_record_boundary(self):
        from leadgen.discovery.__main__ import process
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            raw = root / "raw.ndjson"
            row = {"provider": "exa", "http_status": 200, "scope": "Canada", "results": [{"title": "Maple Pitch 2027\u2028Hosted in Ottawa", "url": "https://example.org/final-2027", "rank": 1, "snippet": ""}]}
            raw.write_text(json.dumps(row, ensure_ascii=False) + "\n", encoding="utf-8")
            meta = process(raw, root / "out", date(2026, 11, 14), "test")
            self.assertEqual(meta["candidate_count"], 1)


class DateSelectionTests(unittest.TestCase):
    """Fixes 1-4 (approved 2026-11-14). All text is synthetic."""

    REF = date(2026, 11, 14)

    def test_event_cue_beats_byline_and_deadline(self):
        text = "# Maple Showcase\n\n October 2, 2026 \n\nApplications close Sunday, October 10, 2026.\n\n● Date: Tuesday, December 8, 2026\n● Time: 4 PM"
        parsed = core.parse_date(text, self.REF)
        self.assertEqual((parsed.start, parsed.ambiguous), (date(2026, 12, 8), False))
        item = core.make_candidate("Maple Showcase 2026", "https://example.org/maple-showcase", "Canada", "ca", self.REF, text)
        self.assertEqual((item.event_date, item.window_status), (date(2026, 12, 8), "in_window"))

    def test_deadline_or_posted_date_alone_is_not_the_event_date(self):
        for text in ("Apply by December 9, 2026 to pitch your venture.", "Posted December 9, 2026.", "Date limite : 9 décembre 2026", "Inscriptions jusqu'au 9 décembre 2026"):
            parsed = core.parse_date(text, self.REF)
            self.assertIsNone(parsed.start, text)
        item = core.make_candidate("Maple Pitch 2026", "https://example.org/apply", "Canada", "ca", self.REF, "Applications close December 9, 2026.")
        self.assertEqual(item.window_status, "unknown")

    def test_french_event_cue(self):
        parsed = core.parse_date("Date limite : 3 novembre 2026. La finale aura lieu le 4 février 2027 à Gatineau.", self.REF)
        self.assertEqual(parsed.start, date(2027, 2, 4))

    def test_timeline_labels_on_adjacent_lines(self):
        text = "Key dates\n\nNovember 2, 2026\n\n#### Applications open\n\nJanuary 20, 2027\n\n#### Applications close\n\nMarch 3, 2027\n\n#### Final pitch night"
        self.assertEqual(core.parse_date(text, self.REF).start, date(2027, 3, 3))

    def test_past_only_when_no_remaining_date_reaches_the_window(self):
        past = core.make_candidate("Maple Forum 2026", "https://example.org/forum", "Canada", "ca", self.REF, "Maple Forum on October 1, 2026.")
        self.assertEqual(past.window_status, "past")
        mixed = core.make_candidate("Maple Forum 2026", "https://example.org/forum", "Canada", "ca", self.REF, "Maple Forum on October 1, 2026 | Next stop: March 3, 2027")
        self.assertEqual((mixed.window_status, mixed.event_date), ("unknown", None))
        self.assertIn("date_ambiguous", mixed.unknown_reasons)
        self.assertNotIn("date_unknown", mixed.unknown_reasons)
        from leadgen.discovery.__main__ import watch_items
        reasons = watch_items([mixed], self.REF, "test")[0]["reasons"]
        self.assertIn("date_ambiguous", reasons)
        self.assertNotIn("date_unknown", reasons)

    def test_ranges(self):
        parsed = core.parse_date("The bracket runs from March 1 to April 6, 2027.", self.REF)
        self.assertEqual((parsed.start, parsed.end), (date(2027, 3, 1), date(2027, 4, 6)))
        parsed = core.parse_date("Semaine de l'entrepreneuriat du 1er au 5 mars 2027", self.REF)
        self.assertEqual((parsed.start, parsed.end), (date(2027, 3, 1), date(2027, 3, 5)))
        parsed = core.parse_date("Registration window: October 1, 2026 - January 2, 2027", self.REF)
        self.assertEqual((parsed.start, parsed.end), (None, None))

    def test_recap_or_earlier_year_blocks_year_inference(self):
        self.assertEqual(core.parse_date("Maple pitch day April 4 at the hub.", self.REF).start, date(2027, 4, 4))
        for text in ("Congratulations to our winners! The pitch day took place April 4.", "Winter 2024 cohort update: pitch day April 4 at the hub.", "Maple Faceoff 2026: finals May 12 at the hub.", "Félicitations aux lauréats de la finale du 4 avril."):
            parsed = core.parse_date(text, self.REF)
            self.assertIsNone(parsed.start, text)
            self.assertNotEqual(core.window_status(parsed.start, parsed.end, self.REF, parsed.confidence), "pending_date", text)
        item = core.make_candidate("Maple Faceoff 2026", "https://example.org/faceoff", "Canada", "ca", self.REF, "Finals May 12 at the hub.")
        self.assertIsNone(item.event_date)
        self.assertNotEqual(item.edition_year, 2027)

    def test_season_or_month_must_overlap_window(self):
        self.assertEqual(core.window_status(*self._pd("Spring 2027")), "pending_date")
        self.assertEqual(core.window_status(*self._pd("Spring 2026")), "unknown")
        self.assertEqual(core.window_status(*self._pd("février 2027")), "pending_date")

    def _pd(self, text):
        parsed = core.parse_date(text, self.REF)
        return parsed.start, parsed.end, self.REF, parsed.confidence

    def test_year_resolved_by_explicit_dates_and_headings(self):
        text = "Hosted since 2019. The bracket runs from March 1 to April 6, 2027.\n\n## Applications for the 2027 competition are now open\n\n## 2027 Schedule\n\nRound one March 1-11"
        item = core.make_candidate("Maple Bracket Pitch Competition", "https://example.org/bracket", "Canada", "ca", self.REF, text)
        self.assertEqual(item.edition_year, 2027)
        self.assertIn("year_resolved_by_explicit_date", item.resolution_flags)
        self.assertNotIn("year_conflict", item.conflict_reasons)
        self.assertEqual(item.window_status, "in_window")

    def test_recipient_lines_never_resolve_a_year(self):
        text = "Ten finalists pitch during Maple Week (March 1–5, 2027).\n\n### 2026 Competition Recipients\n\n- First place: Acme"
        resolved = core.make_candidate("Maple Prize", "https://example.org/prize", "Canada", "ca", self.REF, text)
        self.assertEqual(resolved.edition_year, 2027)
        conflicted = core.make_candidate("Maple Prize", "https://example.org/prize", "Canada", "ca", self.REF, text + "\n\nThe 2026 final was held on May 3, 2026.")
        self.assertIsNone(conflicted.edition_year)
        self.assertIn("year_conflict", conflicted.conflict_reasons)

    def test_same_url_sources_resolve_from_combined_text(self):
        a = core.make_candidate("Maple Bracket", "https://example.org/bracket", "Canada", "ca", self.REF, "Round two March 15-18. The bracket runs from March 1 to April 6, 2027.", "exa", "q-1")
        b = core.make_candidate("Maple Bracket", "https://example.org/bracket/", "Canada", "ca", self.REF, "Round three April 1, 2027. 2027 Schedule. Since 2020.", "exa", "q-2")
        merged = core.merge_candidates([a, b])
        self.assertEqual(len(merged), 1)
        self.assertEqual((merged[0].edition_year, merged[0].event_date, merged[0].window_status), (2027, date(2027, 3, 1), "in_window"))

    def test_cross_site_merge_requires_city_date_tokens_and_no_conflict(self):
        snippet_a = "Summit Finale: November 30, 2026. 100 Main St, Ottawa, ON"
        snippet_b = "The Maple Pitch Summit Finale will be held in Ottawa. Finale: November 30, 2026"
        a = core.make_candidate("Maple Pitch Summit Finale | Hub Events", "https://hub.example.org/event/maple-finale", "Canada", "ca", self.REF, snippet_a)
        b = core.make_candidate("Ottawa Summit — Maple Pitch", "https://maplepitch.example.com/summits/ottawa", "Canada", "ca", self.REF, snippet_b)
        merged = core.merge_candidates([a, b])
        self.assertEqual(len(merged), 1)
        self.assertEqual({s.canonical_url for s in merged[0].sources}, {a.sources[0].canonical_url, b.sources[0].canonical_url})
        other_date = core.make_candidate("Ottawa Summit — Maple Pitch", "https://maplepitch.example.com/summits/ottawa", "Canada", "ca", self.REF, snippet_b.replace("30", "29"))
        no_city = core.make_candidate("Summit — Maple Pitch", "https://maplepitch.example.com/summits/x", "Canada", "ca", self.REF, "Finale: November 30, 2026")
        one_token = core.make_candidate("Ottawa Pitch Night", "https://other.example.net/night", "Canada", "ca", self.REF, "Held in Ottawa. Finale: November 30, 2026")
        conflicted = core.make_candidate("Ottawa Summit — Maple Pitch", "https://maplepitch.example.com/summits/ottawa", "Canada", "ca", self.REF, snippet_b + " The 2025 finale was held on November 30, 2025.")
        for other in (other_date, no_city, one_token, conflicted):
            self.assertEqual(len(core.merge_candidates([a, other])), 2, other.event_name)

    def test_cross_site_merge_is_order_independent(self):
        items = [
            core.make_candidate("Maple Pitch Summit Finale | Hub", "https://hub.example.org/e/1", "Canada", "ca", self.REF, "Finale: November 30, 2026. Held in Ottawa."),
            core.make_candidate("Maple Pitch Summit", "https://maplepitch.example.com/ottawa", "Canada", "ca", self.REF, "Finale: November 30, 2026. Held in Ottawa."),
            core.make_candidate("Maple Pitch Summit Finale Recap", "https://news.example.net/maple", "Canada", "ca", self.REF, "Finale: November 30, 2026. Held in Ottawa."),
            core.make_candidate("Cedar Demo Day", "https://cedar.example.org/demo", "Canada", "ca", self.REF, "Demo day: November 30, 2026. Held in Ottawa."),
        ]
        baseline = [x.dict() for x in core.merge_candidates(items)]
        self.assertEqual(len(baseline), 2)
        for seed in range(6):
            shuffled = items[:]
            random.Random(seed).shuffle(shuffled)
            self.assertEqual([x.dict() for x in core.merge_candidates(shuffled)], baseline)

    def test_immediate_deadline_and_announcement_wording(self):
        text = "Submit your pitch here, before November 24th.\nFinalists will pitch live at our December 2 open house. The winner will be announced on stage; winners will be invited back."
        self.assertEqual(core.parse_date(text, self.REF).start, date(2026, 12, 2))

    def test_same_site_pages_with_same_date_merge(self):
        a = core.make_candidate("12 teams to present at the Maple Demo Showcase", "https://maple.example.org/news/teams", "Canada", "ca", self.REF, "On Tuesday, December 8, 2026, 12 teams will take the stage.")
        b = core.make_candidate("Demo Showcase - Applications open", "https://maple.example.org/files/apply.pdf", "Canada", "ca", self.REF, "Applications close October 1, 2026.\nDate: Tuesday, December 8, 2026")
        merged = core.merge_candidates([a, b])
        self.assertEqual(len(merged), 1)
        c = core.make_candidate("Demo Showcase - Applications open", "https://other.example.net/apply", "Canada", "ca", self.REF, "Date: Tuesday, December 8, 2026")
        self.assertEqual(len(core.merge_candidates([a, c])), 2)

    def test_metadata_timestamps_and_same_line_headings(self):
        self.assertIsNone(core.parse_date("# Maple pitch night | Example Org · Social · 2026-10-05T00:00:00+00:00", self.REF).start)
        self.assertIsNone(core.parse_date("- [2026-11-06 · Reshared · 70 reactions] Maple demo day", self.REF).start)
        self.assertEqual(core.parse_date("Maple demo day: 2026-12-04", self.REF).start, date(2026, 12, 4))
        self.assertEqual(core.year_anchors("Entry closes November 18, 2026\n\nCompetition entry window.", self.REF), set())

    def test_championship_format_word_keeps_its_date_and_winner_lines_give_none(self):
        parsed = core.parse_date("Modelled after a championship bracket, the pitch competition runs from March 1 to April 6, 2027.", self.REF)
        self.assertEqual(parsed.start, date(2027, 3, 1))
        self.assertIsNone(core.parse_date("Our 2025 champion was crowned on December 3, 2026.", self.REF).start)

    def test_timeline_label_naming_a_deadline_wins(self):
        text = "Timeline\n\nOctober 13 – November 18, 2026\n\nCompetition entry window.\n\nMarch 4, 2027\n\nPitch competition and winner selection."
        self.assertEqual(core.parse_date(text, self.REF).start, date(2027, 3, 4))

    def test_list_item_labels_and_clock_abbreviations(self):
        text = "- Application deadline: February 7, 2027, at 11:59 p.m. ET\n- Finalist notification: February 22, 2027\n- Competition finale: March 19, 2027"
        self.assertEqual(core.parse_date(text, self.REF).start, date(2027, 3, 19))
        self.assertIsNone(core.parse_date("Open now · Applications close 11:59 p.m. CST Friday, January 29, 2027\n\n#### Maple Pitch Competition", self.REF).start)

    def test_after_context_stops_at_sentence_end_and_weekday_is_transparent(self):
        self.assertEqual(core.parse_date("Maple pitch day is December 15, 2026. Applications close November 30, 2026.", self.REF).start, date(2026, 12, 15))
        self.assertIsNone(core.parse_date("Final decisions by Friday, January 15, 2027", self.REF).start)


class ScorerTests(unittest.TestCase):
    """A2a/A2b restatement and the precision sample (approved 2026-11-14)."""

    def test_kept_or_correctly_excluded(self):
        from scripts.score_discovery import edition_outcome
        ok = {"city": None, "edition_year": 2027, "window_status": "in_window"}
        wrong = {"city": "Elsewhere", "edition_year": 2027, "window_status": "in_window"}
        past = {"city": None, "edition_year": 2026, "window_status": "past", "exclude_reason": "past"}
        self.assertEqual(edition_outcome([ok], [], "Ottawa", 2027, "in_window"), {"kept": True, "correctly_excluded": False, "kept_or_correctly_excluded": True, "wrong_records": 0})
        self.assertFalse(edition_outcome([ok, wrong], [], "Ottawa", 2027, "in_window")["kept"])
        self.assertTrue(edition_outcome([], [past], "Ottawa", 2026, "past")["kept_or_correctly_excluded"])
        self.assertFalse(edition_outcome([], [past], "Ottawa", 2026, "in_window")["kept_or_correctly_excluded"])
        self.assertFalse(edition_outcome([], [dict(past, edition_year=2025)], "Ottawa", 2026, "past")["kept_or_correctly_excluded"])

    def test_returned_by_search(self):
        from scripts.score_discovery import returned_by_search
        rows = [{"provider": "exa", "http_status": 200, "results": [{"url": "https://Example.org/a/"}]}, {"provider": "brave", "http_status": 200, "results": [{"url": "https://example.org/b"}]}]
        keys = returned_by_search(rows, {"https://example.org/a": {"e1"}, "https://example.org/b": {"e2"}}, lambda u: u.lower().rstrip("/"))
        self.assertEqual(keys, {"e1"})

    def test_precision_sample_is_seeded_and_in_window_only(self):
        from scripts.precision_sample import sample_in_window
        rows = [{"dedupe_key": f"k{i}", "window_status": "in_window" if i % 3 else "unknown"} for i in range(60)]
        first = sample_in_window(rows, 25, 7)
        self.assertEqual(first, sample_in_window(list(reversed(rows)), 25, 7))
        self.assertEqual(len(first), 25)
        self.assertTrue(all(r["window_status"] == "in_window" for r in first))


if __name__ == "__main__":
    unittest.main()
