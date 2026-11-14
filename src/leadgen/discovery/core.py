"""Pure discovery rules and bounded provider orchestration."""
from __future__ import annotations

import calendar
import re
import unicodedata
from dataclasses import dataclass
from datetime import date, timedelta
from urllib.parse import parse_qsl, unquote, urlencode, urlsplit, urlunsplit

from pydantic import BaseModel, Field


EN_CORE = ("startup pitch competition finalists", "startup accelerator demo day founders", "university entrepreneurship pitch showcase", "entrepreneurship competition finalists")
EN_EARLY = ("call for applications startup pitch competition", "demo day founders pitch night")
FR = ("concours de pitch startup", "demo day entrepreneurs", "concours entrepreneuriat finalistes", "finale concours de pitch étudiant", "appel de candidatures concours startup")
CA_SCOPES = ("Canada", "Montreal", "Quebec City", "Toronto", "Ottawa", "Hamilton", "Waterloo", "Calgary", "Edmonton", "Saskatoon", "Vancouver", "Halifax")
FR_SCOPES = ("Montréal", "Ville de Québec", "Québec", "Sherbrooke", "Gatineau")
US_METROS = ("New York", "Los Angeles", "Chicago", "Dallas", "Houston", "Washington", "Miami", "Philadelphia", "Atlanta", "Boston")
# Frozen 2026-11-14 before amended A1a rescore. Only generic geography.
CA_CITIES = ("Montréal", "Ville de Québec", "Sherbrooke", "Gatineau", "Toronto", "Ottawa", "Hamilton", "Waterloo", "Calgary", "Edmonton", "Saskatoon", "Vancouver", "Halifax", "Victoria", "Winnipeg", "Regina", "London", "Kitchener", "Mississauga", "Brampton", "Laval", "Longueuil", "Kelowna", "Kingston", "Fredericton", "Moncton", "Charlottetown", "St. John's")
CA_PROVINCES = ("Québec", "Ontario", "Alberta", "British Columbia", "Saskatchewan", "Nova Scotia", "Manitoba", "New Brunswick", "Newfoundland", "Prince Edward Island")
CITY_ALIASES = {"montreal": "Montréal", "quebec city": "Ville de Québec", "ville de quebec": "Ville de Québec", "nyc": "New York"}
EVENT_WORDS = ("pitch", "demo day", "showcase", "competition", "concours", "finale", "finalists", "finalistes", "venture day", "startup prize", "open house")
MONTHS = {name.lower(): i for i, name in enumerate(calendar.month_name) if name}
MONTHS.update({name.lower(): i for i, name in enumerate(calendar.month_abbr) if name})
MONTHS["sept"] = 9
MONTHS.update({"janvier": 1, "février": 2, "fevrier": 2, "mars": 3, "avril": 4, "mai": 5, "juin": 6, "juillet": 7, "août": 8, "aout": 8, "septembre": 9, "octobre": 10, "novembre": 11, "décembre": 12, "decembre": 12})
MONTH_PATTERN = "|".join(sorted(map(re.escape, MONTHS), key=len, reverse=True))


def slug(value: str) -> str:
    plain = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "-", plain).strip("-")


def fold(value: str) -> str:
    return unicodedata.normalize("NFKD", value or "").encode("ascii", "ignore").decode().casefold()


def clean_event_name(title: str) -> str:
    """Choose the event-bearing segment, dropping common platform/site wrappers."""
    parts = [p.strip() for p in re.split(r"\s+[|·–-]\s+", title or "") if p.strip()]
    if not parts:
        return ""
    platforms = ("luma", "eventbrite", "meetup", "facebook", "linkedin")
    parts = [p for p in parts if fold(p) not in platforms] or parts
    def strength(part: str) -> tuple[int, int]:
        low = fold(part)
        return (sum(w in low for w in EVENT_WORDS) + int(bool(re.search(r"\b20\d{2}\b", part))), -len(part))
    return max(parts, key=strength)


def page_city(title: str, url: str, snippet: str) -> str | None:
    """Extract only page evidence; query scope is deliberately absent."""
    aliases = {fold(x): x for x in CA_CITIES + US_METROS}
    aliases.update(CITY_ALIASES)
    aliases["quebec city"] = "Ville de Québec"
    def matches(piece: str):
        plain = fold(piece)
        found_matches = []
        for alias, city in aliases.items():
            for found in re.finditer(r"(?<![a-z])" + re.escape(alias) + r"(?![a-z])", plain):
                found_matches.append((found.start(), -len(alias), city, found.end(), plain))
        return sorted(found_matches)
    for piece in (title, unquote(urlsplit(url).path).replace("-", " ")):
        found = matches(piece)
        if found:
            return found[0][2]
    province_names = {fold(x) for x in CA_PROVINCES} | {"qc", "on", "ab", "bc", "sk", "ns", "mb", "nb", "nl", "pe"}
    for start, _, city, end, plain in matches(snippet):
        before = plain[max(0, start - 45):start]
        after = plain[end:end + 45]
        if re.search(r"\b(?:university of|college of)\s+$", before):
            continue
        if re.search(r"\b(?:startup week winner from|winner from)\s+$", before):
            continue
        venue = re.search(r"\b(?:in|held in|takes place in|hosted in|located in|downtown|a|au|en)\s+$", before)
        province = re.match(r"\s*,\s*([a-z ]+)", after)
        if venue or (province and province.group(1).strip() in province_names):
            return city
    return None


def event_years(name: str, url: str, snippet: str) -> set[int]:
    """Ignore historical winner/champion and copyright clauses."""
    clean_snippet = event_snippet(snippet)
    text = f"{name} {unquote(urlsplit(url).path)} {clean_snippet}"
    return set(map(int, re.findall(r"(?<!\d)20\d{2}(?!\d)", text)))


# "champions?" is word-bounded so that "championship" (a format word) no longer drops a clause (2026-11-14).
PAST_CLAUSE = re.compile(r"[^.!?;\n]*(?:last year|previous year|past edition|champions?(?![a-z])|winner|copyright|©|all rights reserved)[^.!?;\n]*[.!?;\n]?", re.I)


def event_snippet(snippet: str) -> str:
    return PAST_CLAUSE.sub(" ", snippet or "")


def add_months(day: date, months: int) -> date:
    year, month = divmod(day.year * 12 + day.month - 1 + months, 12)
    month += 1
    return date(year, month, min(day.day, calendar.monthrange(year, month)[1]))


@dataclass(frozen=True)
class Query:
    id: str
    query: str
    scope: str
    language: str
    phase: str
    family: str


def generate_queries(reference_date: date, us: bool = False) -> list[Query]:
    years = sorted({(reference_date + timedelta(days=7)).year, add_months(reference_date, 6).year})
    year_text = " ".join(map(str, years))
    queries: list[Query] = []
    def add(scope: str, intent: str, lang: str, phase: str, family: str) -> None:
        time_text = f"upcoming {year_text}" if lang == "en" else f"à venir {year_text}"
        queries.append(Query(f"q-{len(queries)+1:03d}", f"{scope} {intent} {time_text}", scope, lang, phase, family))
    for scope in CA_SCOPES:
        for intent in EN_CORE:
            add(scope, intent, "en", "ca", "en_core")
    for scope in CA_SCOPES:
        for intent in EN_EARLY:
            add(scope, intent, "en", "ca", "en_early")
    for scope in FR_SCOPES:
        for intent in FR:
            add(scope, intent, "fr", "ca", "fr")
    if us:
        for intent in EN_CORE + EN_EARLY:
            add("United States", intent, "en", "us", "us_national")
        for scope in US_METROS:
            for intent in (EN_CORE[0], EN_CORE[2]):
                add(scope, intent, "en", "us", "us_metro")
    return queries


def canonical_url(url: str) -> str:
    parts = urlsplit(url.strip())
    if parts.scheme.lower() not in ("http", "https") or not parts.hostname:
        return ""
    host = parts.hostname.lower().removeprefix("www.")
    if parts.port:
        host += f":{parts.port}"
    path = unquote(parts.path).rstrip("/") or "/"
    query = sorted((k, v) for k, v in parse_qsl(parts.query, keep_blank_values=True) if not k.lower().startswith("utm_") and k.lower() not in {"fbclid", "gclid"})
    return urlunsplit((parts.scheme.lower(), host, path, urlencode(query), ""))


def page_kind(url: str, title: str, snippet: str) -> str:
    host = (urlsplit(url).hostname or "").lower()
    path = urlsplit(url).path.lower()
    text = f"{title} {snippet}".lower()
    if any(host.endswith(h) for h in ("facebook.com", "linkedin.com", "instagram.com", "x.com")):
        return "social"
    if any(host.endswith(h) for h in ("luma.com", "eventbrite.com", "meetup.com", "arclight.events")):
        return "listing_or_aggregator"
    if any(s in path for s in ("/news/", "/blog/", "/press/")):
        return "news"
    event = any(w in text or w in path for w in EVENT_WORDS)
    if any(w in text or w in path for w in ("accelerator", "incubator", "cohort", "program")) and not (event and re.search(r"20\d{2}", text + path)):
        return "program"
    if event and re.search(r"20\d{2}", text + path):
        return "event_edition"
    if event:
        return "event_series"
    if any(s in path for s in ("/events", "/calendar")):
        return "listing_or_aggregator"
    return "other"


@dataclass(frozen=True)
class ParsedDate:
    start: date | None = None
    end: date | None = None
    text: str | None = None
    confidence: str = "none"
    ambiguous: bool = False


# Fix 1-3 (approved 2026-11-14). Generic wording only; matched on accent-folded, case-folded text.
def _cues(words: str) -> re.Pattern:
    return re.compile(r"(?<![a-z])(?:" + words + r")(?![a-z])")


DEADLINE_CUES = _cues(r"deadlines?|entr(?:y|ies) (?:window|period|deadline)|entries|application period|apply|applications?|applicants?|register|registration|sign[- ]?up|submit|submissions?|nominations?|closes?|closing|due|as of|no later than|until|candidatures?|inscriptions?|inscrivez|date limite|soumettre|soumission|jusqu.?au|avant le")
POSTED_CUES = _cues(r"posted|published|updated|last modified|newsletter|publie|mis a jour|infolettre")
EVENT_CUES = _cues(r"date\s*:|when\s*:|quand\s*:|takes? place|taking place|join us|events?|finale|finals?|demo ?day|pitch(?:es|ing)?|showcase|competition|compete|summit|ceremony|gala|aura lieu|se tiendra|se deroulera|evenement|concours|vitrine|forum|conference|hackathon")
WEAK_EVENT_CUES = _cues(r"on|le")
IMMEDIATE_DEADLINE_CUES = _cues(r"before|by|avant")
RECAP_CUES = _cues(r"winners(?!\s+(?:will|to be|are announced|announced (?:at|on)))|congratulations|congrats|recap|took place|was held|were held|wrapped up|took home|laureats?|felicitations|s.est tenue?|s.est deroulee?|a eu lieu|retour sur")
WEEKDAYS = r"monday|tuesday|wednesday|thursday|friday|saturday|sunday|mon|tue|tues|wed|thu|thur|thurs|fri|sat|sun|lundi|mardi|mercredi|jeudi|vendredi|samedi|dimanche"
_MON = rf"({MONTH_PATTERN})\.?"
_DAY = r"(\d{1,2})(?:st|nd|rd|th|er)?(?!\d)"
_YEAR = r"(20\d{2})(?!\d)"
_DASH = r"\s*(?:-|–|—|to|through|until)\s*"
DATE_PATTERNS = (
    ("iso", re.compile(r"(?<!\d)(20\d{2})-(\d{2})-(\d{2})(?!\d)")),
    ("en_cross_year", re.compile(rf"(?<![a-z]){_MON}\s+{_DAY},?\s+{_YEAR}{_DASH}{_MON}\s+{_DAY},?\s+{_YEAR}", re.I)),
    ("en_cross_month", re.compile(rf"(?<![a-z]){_MON}\s+{_DAY}{_DASH}{_MON}\s+{_DAY}(?:,?\s+{_YEAR})?", re.I)),
    ("en", re.compile(rf"(?<![a-z]){_MON}\s+{_DAY}(?:\s*(?:-|–|—|to)\s*{_DAY})?(?:,?\s+{_YEAR})?", re.I)),
    ("fr_range", re.compile(rf"(?<!\d){_DAY}(?:\s+{_MON})?\s*(?:au|-|–|—)\s*{_DAY}\s+{_MON}(?:\s+{_YEAR})?", re.I)),
    ("fr", re.compile(rf"(?<!\d){_DAY}\s+{_MON}(?:\s+{_YEAR})?", re.I)),
)
YEAR_HEADINGS = re.compile(r"(?<!\d)(20\d{2})[ \t]+(?:schedule|competition|edition|agenda|calendar)(?![a-z])|(?<![a-z])(?:applications?|registrations?|nominations?)\s+(?:for|to)\s+the\s+(20\d{2})\s+(?:competition|edition|event|challenge|prize)(?![a-z])|(?<![a-z])(?:edition|concours|calendrier|programmation)\s+(20\d{2})(?!\d)", re.I)
PAST_LINES = re.compile(r"[^\n]*(?:recipients?|winners?|laur[eé]ats?|champions?|past edition|previous edition|last year|l.an dernier)[^\n]*", re.I)
SEASON_MONTHS = {"spring": (3, 6), "printemps": (3, 6), "summer": (6, 9), "été": (6, 9), "fall": (9, 12), "autumn": (9, 12), "automne": (9, 12), "winter": (1, 3), "hiver": (1, 3)}


@dataclass(frozen=True)
class DateMention:
    start: date | None
    end: date | None
    text: str
    pos: int
    has_year: bool
    role: str  # event / neutral / byline / deadline / posted


def _infer_year(month: int, day: int, ref: date) -> int | None:
    years = [y for y in range(ref.year - 1, ref.year + 3) if add_months(ref, -1) <= date(y, month, min(day, 28)) <= add_months(ref, 12)]
    return years[0] if len(years) == 1 else None


def _safe_date(year: int | None, month: int, day: int) -> date | None:
    if year is None:
        return None
    try:
        return date(year, month, day)
    except ValueError:
        return None


def _nearest(pattern: re.Pattern, before: str, after: str) -> int | None:
    distances = [len(before) - m.end() for m in pattern.finditer(before)] + [m.start() + 1 for m in pattern.finditer(after)]
    return min(distances) if distances else None


def _role(before: str, after: str) -> str | None:
    before, after = fold(before), fold(after)
    if POSTED_CUES.search(before[-40:]):
        return "posted"
    deadline = _nearest(DEADLINE_CUES, before, after)
    event = _nearest(EVENT_CUES, before, after)
    weak = _nearest(WEAK_EVENT_CUES, before[-12:], "")
    if IMMEDIATE_DEADLINE_CUES.search(before[-10:]):
        return "deadline"
    if deadline is not None and (event is None or deadline <= event):
        return "deadline"
    if event is not None or weak is not None:
        return "event"
    return None


def _label_line(lines: list[str], index: int, step: int) -> str | None:
    i = index + step
    while 0 <= i < len(lines) and not lines[i].strip():
        i += step
    if 0 <= i < len(lines) and len(lines[i].strip()) <= 40:
        return lines[i]
    return None


def _mention_role(text: str, start: int, end: int) -> str:
    line_start = text.rfind("\n", 0, start) + 1
    line_end = text.find("\n", end)
    line_end = len(text) if line_end == -1 else line_end
    window = re.sub(r"(?<![a-z])([ap])\.m\.", r"\1m", text[max(line_start, start - 60):start], flags=re.I)  # "11:59 p.m." is not a sentence end
    before = re.split(r"[.!?;](?:\s|$)|[|•●]", window)[-1]
    after = re.split(r"[.!?;](?:\s|$)", text[end:min(line_end, end + 30)])[0]
    before = re.sub(rf"(?:(?<![a-z])(?:{WEEKDAYS})\.?,?\s*)+$", "", before, flags=re.I)  # "by Friday, January 15"
    role = _role(before, after)
    if role:
        return role
    residue = re.sub(rf"(?<![a-z])(?:{WEEKDAYS})(?![a-z])", " ", fold(text[line_start:start] + " " + text[end:line_end]))
    if len(re.findall(r"[a-z]", residue)) <= 6:  # only a (nearly) bare date line borrows a neighbouring label
        lines = text.split("\n")
        index = text.count("\n", 0, start)
        for step in (1, -1):
            label = _label_line(lines, index, step)
            if label is not None and DEADLINE_CUES.search(fold(label)):
                return "deadline"  # a short timeline label that names a deadline describes that deadline
            role = _role(label, "") if label is not None else None
            if role:
                return role
        if not re.search(r"[a-z]", residue):
            return "byline"
    return "neutral"


def find_date_mentions(text: str, ref: date, allow_inference: bool = True) -> list[DateMention]:
    """Every explicit or inferable date phrase in the text, with its local context role."""
    text = text or ""
    found = []
    for kind, pattern in DATE_PATTERNS:
        for match in pattern.finditer(text):
            found.append((match.start(), -(match.end() - match.start()), kind, match))
    accepted, taken = [], []
    for start, _, kind, match in sorted(found, key=lambda x: (x[0], x[1])):
        if any(start < b and match.end() > a for a, b in taken):
            continue
        taken.append((start, match.end()))
        accepted.append((kind, match))
    past = [m.span() for m in PAST_CLAUSE.finditer(text)]  # winner/champion/last-year/copyright clauses never give dates
    explicit_years = [int(y) for y in re.findall(r"(?<!\d)20\d{2}(?!\d)", PAST_CLAUSE.sub(" ", text))]
    earliest = min(explicit_years) if explicit_years else None
    def infer(month: int, day: int) -> int | None:
        # Fix 2: never infer a year later than an explicit year already in the text.
        year = _infer_year(month, day, ref) if allow_inference else None
        return None if year is None or (earliest is not None and earliest < year) else year
    mentions = []
    for kind, match in accepted:
        if any(a <= match.start() < b for a, b in past):
            continue
        g = match.groups()
        if kind == "iso":
            first = last = _safe_date(int(g[0]), int(g[1]), int(g[2]))
            has_year = True
        elif kind == "en_cross_year":
            first, last, has_year = _safe_date(int(g[2]), MONTHS[g[0].lower()], int(g[1])), _safe_date(int(g[5]), MONTHS[g[3].lower()], int(g[4])), True
        elif kind in ("en_cross_month", "en", "fr_range", "fr"):
            if kind == "en_cross_month":
                m1, d1, m2, d2, year = MONTHS[g[0].lower()], int(g[1]), MONTHS[g[2].lower()], int(g[3]), g[4]
            elif kind == "en":
                m1, d1, year = MONTHS[g[0].lower()], int(g[1]), g[3]
                m2, d2 = (m1, int(g[2])) if g[2] else (None, None)
            elif kind == "fr_range":
                m2, d1, d2, year = MONTHS[g[3].lower()], int(g[0]), int(g[2]), g[4]
                m1 = MONTHS[g[1].lower()] if g[1] else m2
            else:
                m1, d1, year = MONTHS[g[1].lower()], int(g[0]), g[2]
                m2 = d2 = None
            has_year = bool(year)
            y1 = int(year) if year else infer(m1, d1)
            if y1 is not None and year and m2 is not None and m2 < m1:
                y1 -= 1  # "Dec 30 to Jan 2, 2027": the stated year belongs to the end.
            first = _safe_date(y1, m1, d1)
            last = _safe_date(y1 + (1 if m2 is not None and m2 < m1 else 0), m2, d2) if (m2 is not None and y1 is not None) else None
        role = _mention_role(text, match.start(), match.end())
        if kind == "iso" and (re.match(r"T\d{2}:", text[match.end():match.end() + 4]) or re.search(r"[·\[]\s*$", text[max(0, match.start() - 3):match.start()])):
            role = "posted"  # machine timestamps and platform metadata ("· 2026-10-05T00:00", "[2026-11-06 · Reshared")
        mentions.append(DateMention(first, last, match.group(), match.start(), has_year, role))
    return mentions


def is_recap(text: str) -> bool:
    """Fix 2: recap wording (winners, took place, félicitations...) means no year is inferred."""
    return bool(RECAP_CUES.search(fold(text)))


def _season_or_month(text: str, ref: date) -> ParsedDate:
    lower, upper = ref + timedelta(days=7), add_months(ref, 6)
    for match in re.finditer(rf"(?<![a-z])({MONTH_PATTERN})\.?\s+(20\d{{2}})(?!\d)|(?<![a-z])(spring|summer|fall|autumn|winter|printemps|été|automne|hiver)\s+(20\d{{2}})(?!\d)", text or "", re.I):
        if match.group(1):
            month, year = MONTHS[match.group(1).lower()], int(match.group(2))
            first, last = date(year, month, 1), date(year, month, calendar.monthrange(year, month)[1])
        else:
            a, b = SEASON_MONTHS[match.group(3).lower()]
            year = int(match.group(4))
            first, last = date(year, a, 1), date(year, b, calendar.monthrange(year, b)[1])
        if last >= lower and first <= upper:
            return ParsedDate(text=match.group(), confidence="season_or_month")
    return ParsedDate()


def parse_date(text: str, reference_date: date, raw_text: str | None = None) -> ParsedDate:
    """Fix 1: choose the event date, never a deadline or posted date.

    Past/too-soon is returned only when no remaining date reaches the window;
    a remaining later date without an event cue makes the result ambiguous.
    """
    text = text or ""
    ref = reference_date
    mentions = find_date_mentions(text, ref, not is_recap(raw_text if raw_text is not None else text))
    usable = [m for m in mentions if m.start and m.role not in ("deadline", "posted")]
    pool = [m for m in usable if m.role != "byline"] or usable
    if not pool:
        return _season_or_month(text, ref)
    lower = ref + timedelta(days=7)
    cued = [m for m in pool if m.role == "event"]
    def result(m: DateMention) -> ParsedDate:
        return ParsedDate(m.start, m.end, m.text, "explicit" if m.has_year else "inferred_year")
    if all(m.start < lower for m in pool):
        return result(max(cued or pool, key=lambda m: (m.start, m.pos)))
    if cued:
        later = [m for m in cued if m.start >= lower]
        if later:
            return result(min(later, key=lambda m: (m.start, m.pos)))
        return ParsedDate(confidence="ambiguous", ambiguous=True)
    if any(m.start < lower for m in pool):
        return ParsedDate(confidence="ambiguous", ambiguous=True)
    return result(min(pool, key=lambda m: (m.start, m.pos)))


def year_anchors(text: str, ref: date) -> set[int]:
    """Fix 3: years named by explicit event-relevant full dates or edition headings, never by winner/recipient lines."""
    clean = PAST_CLAUSE.sub(" ", PAST_LINES.sub(" ", text or ""))
    anchors = set()
    for m in find_date_mentions(clean, ref, allow_inference=False):
        if m.has_year and m.start and m.role in ("event", "neutral"):
            anchors.add(m.start.year)
            if m.end:
                anchors.add(m.end.year)
    anchors.update(int(g) for match in YEAR_HEADINGS.finditer(clean) for g in match.groups() if g)
    return anchors


def window_status(start: date | None, end: date | None, ref: date, confidence: str = "explicit") -> str:
    if not start:
        return "pending_date" if confidence == "season_or_month" else "unknown"
    lower, upper = ref + timedelta(days=7), add_months(ref, 6)
    if start < ref:
        return "past"
    if start < lower:
        return "too_soon"
    if start > upper or (end and end > upper):
        return "too_far"
    return "in_window"


class Source(BaseModel):
    url: str
    canonical_url: str
    title: str = ""
    snippet: str = ""
    provider: str = ""
    query_id: str = ""
    query_family: str = ""
    rank: int = 0
    retrieved_at: str = ""
    is_official_guess: bool = False
    access_hint: str = "public"


class CandidateEdition(BaseModel):
    dedupe_key: str
    event_name: str
    series_key: str
    edition_token: str | None = None
    edition_year: int | None = None
    edition_conflict: bool = False
    event_date: date | None = None
    event_end_date: date | None = None
    date_text: str | None = None
    date_confidence: str = "none"
    city: str | None = None
    region: str | None = None
    country: str | None = None
    geo_tier: str = "canada"
    page_kind: str = "other"
    window_status: str = "unknown"
    lineup_status: str = "unknown"
    expected_announce_date: date | None = None
    recheck_date: date | None = None
    discovery_confidence: str = "low"
    needs_alternate_source: bool = False
    unknown_reasons: list[str] = Field(default_factory=list)
    conflict_reasons: list[str] = Field(default_factory=list)
    resolution_flags: list[str] = Field(default_factory=list)
    sources: list[Source] = Field(default_factory=list)
    providers: set[str] = Field(default_factory=set)
    query_families: set[str] = Field(default_factory=set)
    reference_date: date
    run_id: str = ""


def edition_fields(names: list[str], url: str, snippets: list[str], ref: date, raw_text: str) -> tuple[ParsedDate, int | None, bool, list[str]]:
    """Event date (Fix 1-2) and edition year with explicit-date resolution (Fix 3) for one URL's text."""
    path = urlsplit(url).path
    parse_text = "\n".join(names) + "\n" + "\n".join(snippets) + "\n" + path
    parsed = parse_date(parse_text, ref, raw_text)
    years = set().union(*(event_years(n, url, x) for n in names for x in snippets)) if names and snippets else set()
    if len(years) <= 1:
        return parsed, (parsed.start.year if parsed.start else next(iter(years), None)), False, []
    anchors = year_anchors(parse_text, ref)
    if len(anchors) == 1 and anchors <= years and (parsed.start is None or parsed.start.year in anchors):
        return parsed, next(iter(anchors)), False, ["year_resolved_by_explicit_date"]
    return parsed, None, True, []


def make_candidate(title: str, url: str, city: str, phase: str, ref: date, snippet: str = "", provider: str = "", query_id: str = "", family: str = "", retrieved_at: str = "", rank: int = 0, run_id: str = "") -> CandidateEdition:
    canonical = canonical_url(url)
    name = clean_event_name(title or "").strip() or urlsplit(url).path.rsplit("/", 1)[-1].replace("-", " ")
    parsed, year, conflict, flags = edition_fields([name], url, [snippet or ""], ref, f"{title or ''}\n{snippet or ''}")
    token = str(year) if year else None
    found_city = page_city(title, url, snippet)
    city_slug = slug(found_city) if found_city else "unknown"
    series = slug(re.sub(r"\b20\d{2}\b", "", name)) + "|" + city_slug
    key = series + "|" + (token or "unknown")
    kind = page_kind(url, name, event_snippet(snippet))
    status = window_status(parsed.start, parsed.end, ref, parsed.confidence)
    host = urlsplit(url).hostname or ""
    alternate = kind == "social" or any(h in host for h in ("meetup.com", "facebook.com", "linkedin.com"))
    pending = bool(re.search(r"apply|applications?|deadline|candidatures?", f"{title} {snippet}", re.I))
    announced = bool(re.search(r"finalists|finalistes|winners|lauréats|meet the teams", f"{title} {snippet}", re.I)) and bool(year) and not conflict
    lineup = "announced" if announced else "pending" if pending else "unknown"
    official = kind not in ("listing_or_aggregator", "social")
    confidence = "low" if conflict else "high" if kind == "event_edition" and official and status == "in_window" else "medium" if kind == "event_edition" and (status == "pending_date" or not official) else "low"
    source = Source(url=url, canonical_url=canonical, title=title or "", snippet=snippet or "", provider=provider, query_id=query_id, query_family=family, rank=rank, retrieved_at=retrieved_at, is_official_guess=official, access_hint="alternate_needed" if alternate else "public")
    unknowns = (["city_unknown"] if not found_city else []) + (["year_unknown"] if not year else []) + ((["date_ambiguous"] if parsed.ambiguous else ["date_unknown"]) if status == "unknown" else [])
    return CandidateEdition(dedupe_key=key, event_name=name, series_key=series, edition_token=token, edition_year=year, edition_conflict=conflict, event_date=parsed.start, event_end_date=parsed.end, date_text=parsed.text, date_confidence=parsed.confidence, city=found_city, country="US" if found_city in US_METROS else "CA" if found_city in CA_CITIES else None, geo_tier="us_fallback" if phase == "us" else "canada", page_kind=kind, window_status=status, lineup_status=lineup, discovery_confidence=confidence, needs_alternate_source=alternate, unknown_reasons=unknowns, conflict_reasons=["year_conflict"] if conflict else [], resolution_flags=flags, sources=[source], providers={provider} if provider else set(), query_families={family} if family else set(), reference_date=ref, run_id=run_id)


NAME_STOPWORDS = {"the", "a", "an", "of", "and", "for", "to", "in", "at", "on", "with", "by", "from", "your", "our", "de", "la", "le", "les", "des", "du", "d", "l", "et", "en", "au", "aux", "pour", "sur", "s"}
CITY_TOKENS = {t for c in CA_CITIES + US_METROS + tuple(CITY_ALIASES) for t in slug(c).split("-")}


def name_tokens(name: str) -> set[str]:
    """Meaningful event-name tokens: no stopwords, city words, years or digits."""
    return {t for t in slug(re.sub(r"\b20\d{2}\b", " ", name or "")).split("-") if len(t) > 1 and not t.isdigit() and t not in NAME_STOPWORDS and t not in CITY_TOKENS}


def merge_candidates(items: list[CandidateEdition]) -> list[CandidateEdition]:
    def source_url(x: CandidateEdition) -> str:
        return x.sources[0].canonical_url if x.sources else ""

    def host(x: CandidateEdition) -> str:
        return urlsplit(source_url(x)).hostname or ""

    def aggregate(group: list[CandidateEdition], same_url: bool = False) -> CandidateEdition:
        ordered = sorted(group, key=lambda x: (source_url(x), slug(x.event_name), x.sources[0].provider if x.sources else "", x.sources[0].query_id if x.sources else ""))
        result = ordered[0].copy(deep=True)
        sources = sorted({(s.canonical_url, s.provider, s.query_id, s.rank): s for x in ordered for s in x.sources}.values(), key=lambda s: (not s.is_official_guess, s.canonical_url, s.provider, s.query_id, s.rank))
        cities = {fold(x.city) for x in ordered if x.city}
        years = {x.edition_year for x in ordered if x.edition_year is not None}
        dates = {(x.event_date, x.event_end_date) for x in ordered if x.event_date}
        reasons = set().union(*(set(x.conflict_reasons) for x in ordered))
        flags = set().union(*(set(x.resolution_flags) for x in ordered))
        combined = None
        if same_url and len(ordered) > 1 and (len(years) > 1 or any(x.edition_conflict for x in ordered) or len(dates) > 1):
            # Same page, several excerpts: judge dates and years on all excerpts together (Fix 1 and 3).
            names = sorted({x.event_name for x in ordered})
            snippets = sorted({s.snippet for s in sources if s.snippet})
            raw = "\n".join(sorted({s.title for s in sources}) + snippets)
            combined = edition_fields(names, source_url(ordered[0]), snippets, result.reference_date, raw)
        if len(cities) > 1:
            reasons.add("city_conflict")
        year_value = next(iter(years), None)
        if len(years) > 1 or any(x.edition_conflict for x in ordered):
            if combined and not combined[2] and combined[1] is not None:
                year_value = combined[1]
                reasons.discard("year_conflict")
                flags.update(combined[3])
            else:
                reasons.add("year_conflict")
        date_resolved = False
        if len(dates) > 1:
            parsed = combined[0] if combined else None
            if parsed and parsed.start and not parsed.ambiguous and (year_value is None or "year_conflict" in reasons or parsed.start.year == year_value):
                dates = {(parsed.start, parsed.end)}
                result.event_date, result.event_end_date, result.date_text, result.date_confidence = parsed.start, parsed.end, parsed.text, parsed.confidence
                result.window_status = window_status(parsed.start, parsed.end, result.reference_date, parsed.confidence)
                reasons.discard("date_conflict")
                date_resolved = True
            else:
                reasons.add("date_conflict")
        result.city = next((x.city for x in ordered if x.city), None) if "city_conflict" not in reasons else None
        result.country = "US" if result.city in US_METROS else "CA" if result.city in CA_CITIES else None
        result.edition_year = year_value if "year_conflict" not in reasons else None
        result.edition_token = str(result.edition_year) if result.edition_year else None
        result.edition_conflict = "year_conflict" in reasons
        if "date_conflict" in reasons:
            result.event_date = result.event_end_date = None
            result.date_confidence = "none"
            result.window_status = "unknown"
        elif dates and not date_resolved:
            result.event_date, result.event_end_date = next(iter(dates))
            dated = next(x for x in ordered if x.event_date == result.event_date and x.event_end_date == result.event_end_date)
            result.date_text, result.date_confidence, result.window_status = dated.date_text, dated.date_confidence, dated.window_status
        result.conflict_reasons = sorted(reasons)
        result.resolution_flags = sorted(flags)
        result.sources = sources
        result.providers = set().union(*(x.providers for x in ordered))
        result.query_families = set().union(*(x.query_families for x in ordered))
        result.needs_alternate_source = any(x.needs_alternate_source for x in ordered)
        ambiguous = result.window_status == "unknown" and "date_conflict" not in reasons and any("date_ambiguous" in x.unknown_reasons for x in ordered)
        base = set().union(*(set(x.unknown_reasons) for x in ordered)) - {"city_unknown", "year_unknown", "date_unknown", "date_ambiguous"}
        result.unknown_reasons = sorted(base | ({"city_unknown"} if result.city is None else set()) | ({"year_unknown"} if result.edition_year is None else set()) | (({"date_ambiguous"} if ambiguous else {"date_unknown"}) if result.window_status == "unknown" else set()))
        result.series_key = slug(re.sub(r"\b20\d{2}\b", "", result.event_name)) + "|" + (slug(result.city) if result.city else "unknown")
        result.dedupe_key = result.series_key + "|" + (result.edition_token or "unknown")
        return result

    # Stage 1: every canonical URL yields exactly one record, even with conflicting snippets.
    by_url: dict[str, list[CandidateEdition]] = {}
    for item in items:
        by_url.setdefault(source_url(item), []).append(item)
    url_records = [aggregate(group, same_url=True) for _, group in sorted(by_url.items())]

    def same_site_name(a: CandidateEdition, b: CandidateEdition) -> bool:
        if host(a) != host(b):
            return False
        aa, bb = set(slug(a.event_name).split("-")), set(slug(b.event_name).split("-"))
        return bool(aa and bb) and len(aa & bb) / len(aa | bb) >= 0.8

    def same_site_dated(a: CandidateEdition, b: CandidateEdition) -> bool:
        # Fix 4, same-site form: identical full event date and >= 2 shared meaningful name tokens.
        return (host(a) == host(b) and a.event_date is not None and (a.event_date, a.event_end_date) == (b.event_date, b.event_end_date)
                and len(name_tokens(a.event_name) & name_tokens(b.event_name)) >= 2)

    # Stage 2: join compatible same-site pages only with a unique target.
    ordered = sorted(url_records, key=lambda x: (x.city is None, source_url(x)))
    merged: list[CandidateEdition] = []
    for item in ordered:
        possible = [g for g in merged if not g.conflict_reasons and not item.conflict_reasons and g.edition_year == item.edition_year and (g.city is None or item.city is None or fold(g.city) == fold(item.city)) and (same_site_name(g, item) or same_site_dated(g, item))]
        if len(possible) == 1:
            target = possible[0]
            merged.remove(target)
            merged.append(aggregate([target, item]))
        else:
            merged.append(item)

    # Stage 3 (Fix 4): join records from different sites only when city and full event date are
    # known and equal, neither record is conflicted, and names share >= 2 meaningful tokens.
    def linkable(a: CandidateEdition, b: CandidateEdition) -> bool:
        return (host(a) != host(b) and a.city is not None and b.city is not None and fold(a.city) == fold(b.city)
                and a.event_date is not None and (a.event_date, a.event_end_date) == (b.event_date, b.event_end_date)
                and not a.conflict_reasons and not b.conflict_reasons
                and (a.edition_year is None or b.edition_year is None or a.edition_year == b.edition_year)
                and len(name_tokens(a.event_name) & name_tokens(b.event_name)) >= 2)

    records = sorted(merged, key=lambda x: (source_url(x), x.dedupe_key))
    parent = list(range(len(records)))
    def find(i: int) -> int:
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i
    buckets: dict[tuple, list[int]] = {}
    for i, x in enumerate(records):
        if x.city and x.event_date and not x.conflict_reasons:
            buckets.setdefault((fold(x.city), x.event_date, x.event_end_date), []).append(i)
    for members in buckets.values():
        for n, i in enumerate(members):
            for j in members[n + 1:]:
                if linkable(records[i], records[j]):
                    a, b = find(i), find(j)
                    parent[max(a, b)] = min(a, b)
    groups: dict[int, list[CandidateEdition]] = {}
    for i, x in enumerate(records):
        groups.setdefault(find(i), []).append(x)
    final = [group[0] if len(group) == 1 else aggregate(group) for group in groups.values()]
    return sorted(final, key=lambda x: (x.dedupe_key, source_url(x)))


def recheck_date(reason: str, ref: date, expected: date | None, event: date | None) -> date:
    if reason == "enters_window_later" and event:
        return add_months(event, -6)
    return expected + timedelta(days=1) if expected else ref + timedelta(days=7)


class TransientSearchError(Exception):
    pass


class Runner:
    def __init__(self, search, cap: float = 1.25, prices: dict[str, float] | None = None):
        self.search = search
        self.cap = cap
        self.prices = prices or {"exa": 0.007, "serper": 0.001}
        self.reserved = 0.0
        self.attempts = {"exa": 0, "serper": 0}
        self.fallbacks = {"F1": 0, "F2": 0}
        self.status = "running"

    def _call(self, provider: str, q: Query):
        for attempt in (1, 2):
            price = self.prices[provider]
            if self.reserved + price > self.cap + 1e-9:
                self.status = "stopped_at_cap"
                return None
            self.reserved = round(self.reserved + price, 6)
            self.attempts[provider] += 1
            try:
                return self.search(provider, q)
            except TransientSearchError:
                if attempt == 2:
                    return None
        return None

    def search_query(self, q: Query) -> list[dict]:
        exa = self._call("exa", q)
        if self.status == "stopped_at_cap":
            return []
        eventlike = any(page_kind(r.get("url", ""), r.get("title", ""), r.get("snippet") or "") in ("event_edition", "event_series", "listing_or_aggregator") for r in (exa or []))
        reason = "F1" if exa is None else "F2" if not eventlike else None
        if reason:
            self.fallbacks[reason] += 1
            serper = self._call("serper", q)
            return (exa or []) + (serper or [])
        return exa or []
