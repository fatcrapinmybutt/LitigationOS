#!/usr/bin/env python
"""
court_feed.py — Michigan Court Feed Fetcher & Authority Ingestor

Fetches daily opinions/orders from Michigan Supreme Court and Court of Appeals,
scores them for relevance to Pigors v. Watson, and ingests high-relevance
authorities into mbp_brain.db.

Usage:
    python -I scripts/court_feed.py              # Fetch + score
    python -I scripts/court_feed.py --process    # Fetch + score + create nodes
    python -I scripts/court_feed.py --status     # Show feed stats
    python -I scripts/court_feed.py --since 7    # Only last N days
    python -I scripts/court_feed.py --min-score 0.5  # Min score for processing
"""

import argparse
import hashlib
import json
import logging
import os
import re
import sqlite3
import sys
import time
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from html.parser import HTMLParser
from pathlib import Path
from typing import Optional

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
REPO_ROOT = Path(__file__).resolve().parent.parent
MBP_BRAIN_DB = REPO_ROOT / "mbp_brain.db"
LIT_CONTEXT_DB = REPO_ROOT / "litigation_context.db"
LOG_DIR = REPO_ROOT / "logs"
LOG_FILE = LOG_DIR / "court_feed.log"

USER_AGENT = "LitigationOS/5.0 Court Feed Fetcher"
REQUEST_TIMEOUT = 30
RATE_LIMIT_SECONDS = 2

# ---------------------------------------------------------------------------
# Feed sources (tried in order; first success wins per court)
#
# Primary: CourtListener public search API (100 req/day unauthenticated)
#   court=mich       → Michigan Supreme Court
#   court=michctapp  → Michigan Court of Appeals
# Fallback: Michigan Courts HTML pages (JS-rendered, limited extraction)
# ---------------------------------------------------------------------------
FEED_SOURCES = {
    "MSC": [
        {
            "url": (
                "https://www.courtlistener.com/api/rest/v4/search/"
                "?court=mich&type=o&order_by=dateFiled+desc&format=json"
            ),
            "kind": "courtlistener",
            "label": "CourtListener MSC",
        },
        {
            "url": "https://www.courts.michigan.gov/courts/supreme-court/opinions/2024-2025-term-opinions/",
            "kind": "html_scrape",
            "label": "MI Courts MSC HTML",
        },
        {
            "url": "https://www.courts.michigan.gov/courts/supreme-court/opinions/",
            "kind": "html_scrape",
            "label": "MI Courts MSC Opinions Page",
        },
    ],
    "COA": [
        {
            "url": (
                "https://www.courtlistener.com/api/rest/v4/search/"
                "?court=michctapp&type=o&order_by=dateFiled+desc&format=json"
            ),
            "kind": "courtlistener",
            "label": "CourtListener COA",
        },
        {
            "url": "https://www.courts.michigan.gov/case-search/",
            "kind": "html_scrape",
            "label": "MI Courts Case Search HTML",
        },
    ],
}

# ---------------------------------------------------------------------------
# Relevance keyword tiers
# ---------------------------------------------------------------------------
HIGH_KEYWORDS: list[tuple[str, float]] = [
    (r"\bMCR\s*2\.003\b", 0.95),
    (r"\bMCL\s*722\.23\b", 0.90),
    (r"\bMCL\s*722\.27a?\b", 0.88),
    (r"\bex\s*parte\b", 0.85),
    (r"\bparental\s+alienation\b", 0.92),
    (r"\bpersonal\s+protection\s+order\b", 0.85),
    (r"\bPPO\b", 0.82),
    (r"\bcontempt\b", 0.80),
    (r"\bshow\s+cause\b", 0.80),
    (r"\bsuperintending\s+control\b", 0.90),
    (r"\bmandamus\b", 0.88),
    (r"\b42\s*U\.?S\.?C\.?\s*(?:§|sec(?:tion)?\.?\s*)?\s*1983\b", 0.92),
    (r"\bcivil\s+rights\b", 0.82),
    (r"\bqualified\s+immunity\b", 0.85),
    (r"\bdisqualification\b", 0.82),
    (r"\brecusal\b", 0.82),
    (r"\bhabeas\s+corpus\b", 0.85),
]

MEDIUM_KEYWORDS: list[tuple[str, float]] = [
    (r"\bfamily\s+law\b", 0.55),
    (r"\bcustody\b", 0.60),
    (r"\bdivorce\b", 0.45),
    (r"\bdue\s+process\b", 0.65),
    (r"\bequal\s+protection\b", 0.60),
    (r"\bjudicial\s+conduct\b", 0.65),
    (r"\bcanon\b", 0.50),
    (r"\bfriend\s+of\s+(the\s+)?court\b", 0.60),
    (r"\bFOC\b", 0.55),
    (r"\bchild\s+custody\b", 0.65),
    (r"\bparenting\s+time\b", 0.70),
    (r"\bbest\s+interest\b", 0.65),
    (r"\bestablished\s+custodial\b", 0.70),
    (r"\bMCR\s*[237]\.\d+\b", 0.50),
    (r"\bMCL\s*\d+\.\d+\b", 0.45),
]

LOW_KEYWORDS: list[tuple[str, float]] = [
    (r"\bcivil\s+procedure\b", 0.25),
    (r"\bevidence\s+rule\b", 0.20),
    (r"\bMRE\s*\d+\b", 0.25),
    (r"\bappeal\b", 0.20),
    (r"\bsummary\s+disposition\b", 0.30),
]

# Pre-compile all patterns
_HIGH_COMPILED = [(re.compile(p, re.IGNORECASE), s) for p, s in HIGH_KEYWORDS]
_MEDIUM_COMPILED = [(re.compile(p, re.IGNORECASE), s) for p, s in MEDIUM_KEYWORDS]
_LOW_COMPILED = [(re.compile(p, re.IGNORECASE), s) for p, s in LOW_KEYWORDS]

# Patterns for extracting MCR/MCL cites from text
_MCR_CITE = re.compile(r"\bMCR\s*(\d+\.\d+(?:\([A-Za-z0-9]+\))*)", re.IGNORECASE)
_MCL_CITE = re.compile(r"\bMCL\s*(\d+\.\d+[a-z]?)", re.IGNORECASE)

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

def setup_logging() -> logging.Logger:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger("court_feed")
    logger.setLevel(logging.DEBUG)
    fmt = logging.Formatter(
        "%(asctime)s | %(levelname)-7s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    fh = logging.FileHandler(str(LOG_FILE), encoding="utf-8")
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(fmt)
    logger.addHandler(fh)

    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.INFO)
    ch.setFormatter(fmt)
    logger.addHandler(ch)
    return logger


log = setup_logging()

# ---------------------------------------------------------------------------
# HTML text extractor (stdlib only)
# ---------------------------------------------------------------------------

class _HTMLTextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self._parts: list[str] = []

    def handle_data(self, data: str) -> None:
        self._parts.append(data)

    def get_text(self) -> str:
        return " ".join(self._parts)


def strip_html(html: str) -> str:
    ext = _HTMLTextExtractor()
    ext.feed(html)
    return ext.get_text()

# ---------------------------------------------------------------------------
# Database helpers
# ---------------------------------------------------------------------------

def get_mbp_conn() -> sqlite3.Connection:
    if not MBP_BRAIN_DB.exists():
        raise FileNotFoundError(f"mbp_brain.db not found at {MBP_BRAIN_DB}")
    conn = sqlite3.connect(str(MBP_BRAIN_DB))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA busy_timeout = 60000")
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA cache_size = -32000")
    conn.execute("PRAGMA synchronous = NORMAL")
    return conn


def get_litctx_conn() -> sqlite3.Connection:
    if not LIT_CONTEXT_DB.exists():
        raise FileNotFoundError(f"litigation_context.db not found at {LIT_CONTEXT_DB}")
    conn = sqlite3.connect(f"file:{LIT_CONTEXT_DB}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    conn.text_factory = lambda b: b.decode("utf-8", errors="replace")
    return conn

# ---------------------------------------------------------------------------
# Network helpers
# ---------------------------------------------------------------------------

def _fetch_url(url: str, retries: int = 1) -> Optional[bytes]:
    """Fetch a URL with retry and rate limiting. Returns raw bytes or None."""
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    for attempt in range(1 + retries):
        try:
            with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as resp:
                data = resp.read()
                log.debug("Fetched %d bytes from %s", len(data), url)
                return data
        except urllib.error.HTTPError as exc:
            log.warning("HTTP %d from %s (attempt %d)", exc.code, url, attempt + 1)
        except urllib.error.URLError as exc:
            log.warning("URL error from %s: %s (attempt %d)", url, exc.reason, attempt + 1)
        except OSError as exc:
            log.warning("Network error from %s: %s (attempt %d)", url, exc, attempt + 1)
        if attempt < retries:
            time.sleep(RATE_LIMIT_SECONDS)
    return None

# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

class FeedItem:
    __slots__ = (
        "title", "citation", "url", "date_str", "court",
        "case_number", "summary", "raw_text",
    )

    def __init__(
        self,
        title: str = "",
        citation: str = "",
        url: str = "",
        date_str: str = "",
        court: str = "",
        case_number: str = "",
        summary: str = "",
        raw_text: str = "",
    ) -> None:
        self.title = title.strip()
        self.citation = citation.strip()
        self.url = url.strip()
        self.date_str = date_str.strip()
        self.court = court.strip()
        self.case_number = case_number.strip()
        self.summary = summary.strip()
        self.raw_text = raw_text.strip()

    @property
    def searchable_text(self) -> str:
        return " ".join(filter(None, [
            self.title, self.citation, self.summary, self.raw_text,
        ]))

    @property
    def stable_id(self) -> str:
        key = self.url or self.citation or self.title
        return hashlib.sha256(key.encode("utf-8", errors="replace")).hexdigest()[:16]

    def __repr__(self) -> str:
        return f"FeedItem(court={self.court!r}, title={self.title[:60]!r})"

# ---------------------------------------------------------------------------
# Parsers (one per feed kind)
# ---------------------------------------------------------------------------

def _parse_courtlistener(data: bytes, court: str) -> list[FeedItem]:
    """Parse CourtListener v4 search API JSON response."""
    items: list[FeedItem] = []
    try:
        payload = json.loads(data)
    except (json.JSONDecodeError, ValueError) as exc:
        log.warning("JSON parse error for %s CourtListener: %s", court, exc)
        return items

    results = []
    if isinstance(payload, dict):
        results = payload.get("results", [])
    elif isinstance(payload, list):
        results = payload

    for rec in results:
        if not isinstance(rec, dict):
            continue

        case_name = str(rec.get("caseName") or rec.get("case_name") or "")
        citation_str = str(rec.get("citation") or "")
        if not citation_str:
            cites = rec.get("citations", [])
            if isinstance(cites, list) and cites:
                first = cites[0] if isinstance(cites[0], str) else str(cites[0])
                citation_str = first

        abs_url = str(rec.get("absolute_url") or "")
        if abs_url and not abs_url.startswith("http"):
            abs_url = "https://www.courtlistener.com" + abs_url

        date_filed = str(rec.get("dateFiled") or rec.get("date_filed") or "")
        docket_number = str(rec.get("docketNumber") or rec.get("docket_number") or "")

        snippet = strip_html(str(rec.get("snippet") or ""))
        court_name = str(rec.get("court") or rec.get("court_id") or court)

        detected_court = court
        if "supreme" in court_name.lower() or court_name in ("mich", "Mich."):
            detected_court = "MSC"
        elif "appeal" in court_name.lower() or court_name in ("michctapp",):
            detected_court = "COA"

        if not case_name and not citation_str:
            continue

        items.append(FeedItem(
            title=case_name,
            citation=citation_str,
            url=abs_url,
            date_str=date_filed,
            court=detected_court,
            case_number=docket_number,
            summary=snippet,
            raw_text=json.dumps(rec, ensure_ascii=False, default=str),
        ))

    log.debug("CourtListener returned %d results for %s", len(items), court)
    return items


def _parse_json_api(data: bytes, court: str) -> list[FeedItem]:
    """Parse a generic JSON API response (fallback for future APIs)."""
    items: list[FeedItem] = []
    try:
        payload = json.loads(data)
    except (json.JSONDecodeError, ValueError) as exc:
        log.warning("JSON parse error for %s API: %s", court, exc)
        return items

    records = []
    if isinstance(payload, list):
        records = payload
    elif isinstance(payload, dict):
        for key in ("Results", "results", "Items", "items", "Opinions", "opinions", "data"):
            if key in payload and isinstance(payload[key], list):
                records = payload[key]
                break
        if not records and any(k in payload for k in ("Title", "title", "CaseNumber")):
            records = [payload]

    for rec in records:
        if not isinstance(rec, dict):
            continue
        title = str(rec.get("Title") or rec.get("title") or rec.get("CaseName") or "")
        citation = str(rec.get("Citation") or rec.get("citation") or "")
        url = str(rec.get("Url") or rec.get("url") or rec.get("DocumentUrl") or "")
        if url and not url.startswith("http"):
            url = "https://www.courts.michigan.gov" + url
        date_str = str(rec.get("Date") or rec.get("date") or rec.get("OpinionDate") or
                       rec.get("ReleaseDate") or "")
        case_number = str(rec.get("CaseNumber") or rec.get("caseNumber") or
                         rec.get("DocketNumber") or "")
        summary = strip_html(str(rec.get("Summary") or rec.get("summary") or
                                  rec.get("Description") or ""))

        if not title and not citation:
            continue

        items.append(FeedItem(
            title=title, citation=citation, url=url,
            date_str=date_str, court=court, case_number=case_number,
            summary=summary,
            raw_text=json.dumps(rec, ensure_ascii=False, default=str),
        ))
    return items


def _parse_rss(data: bytes, court: str) -> list[FeedItem]:
    """Parse an RSS/Atom XML feed."""
    items: list[FeedItem] = []
    try:
        root = ET.fromstring(data)
    except ET.ParseError as exc:
        log.warning("XML parse error for %s RSS: %s", court, exc)
        return items

    ns = {"atom": "http://www.w3.org/2005/Atom"}

    # RSS 2.0 <channel><item>
    for item_el in root.iter("item"):
        title = (item_el.findtext("title") or "").strip()
        link = (item_el.findtext("link") or "").strip()
        pub_date = (item_el.findtext("pubDate") or "").strip()
        desc = strip_html(item_el.findtext("description") or "")

        citation_match = re.search(
            r"(\d+\s+Mich(?:\s+App)?\s+\d+|\d+\s+NW\s*\.?\s*2d\s+\d+)",
            title + " " + desc, re.IGNORECASE,
        )
        citation = citation_match.group(0) if citation_match else ""
        detected_court = court
        if "supreme" in title.lower() or "MSC" in title:
            detected_court = "MSC"
        elif "appeals" in title.lower() or "COA" in title:
            detected_court = "COA"

        if not title:
            continue
        items.append(FeedItem(
            title=title, citation=citation, url=link,
            date_str=pub_date, court=detected_court,
            summary=desc, raw_text=desc,
        ))

    # Atom <entry>
    for entry in root.iter("{http://www.w3.org/2005/Atom}entry"):
        title = (entry.findtext("{http://www.w3.org/2005/Atom}title") or "").strip()
        link_el = entry.find("{http://www.w3.org/2005/Atom}link")
        link = (link_el.get("href", "") if link_el is not None else "").strip()
        updated = (entry.findtext("{http://www.w3.org/2005/Atom}updated") or "").strip()
        summary = strip_html(
            entry.findtext("{http://www.w3.org/2005/Atom}summary") or
            entry.findtext("{http://www.w3.org/2005/Atom}content") or ""
        )
        if not title:
            continue
        items.append(FeedItem(
            title=title, citation="", url=link,
            date_str=updated, court=court,
            summary=summary, raw_text=summary,
        ))

    return items


def _parse_sitemap(data: bytes, court: str) -> list[FeedItem]:
    """Parse a sitemap XML for opinion URLs."""
    items: list[FeedItem] = []
    try:
        root = ET.fromstring(data)
    except ET.ParseError as exc:
        log.warning("Sitemap XML parse error: %s", exc)
        return items

    ns = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    for url_el in root.iter("{http://www.sitemaps.org/schemas/sitemap/0.9}url"):
        loc = (url_el.findtext("{http://www.sitemaps.org/schemas/sitemap/0.9}loc") or "").strip()
        lastmod = (url_el.findtext("{http://www.sitemaps.org/schemas/sitemap/0.9}lastmod") or "").strip()
        if not loc or "opinion" not in loc.lower():
            continue
        slug = loc.rstrip("/").split("/")[-1]
        title = slug.replace("-", " ").title()
        items.append(FeedItem(
            title=title, url=loc, date_str=lastmod, court=court,
        ))
    return items


def _parse_opinions_html(data: bytes, court: str) -> list[FeedItem]:
    """Fallback: scrape the opinions-orders HTML page for links."""
    items: list[FeedItem] = []
    try:
        text = data.decode("utf-8", errors="replace")
    except Exception:
        return items

    link_pattern = re.compile(
        r'<a[^>]+href=["\']([^"\']*opinion[^"\']*)["\'][^>]*>(.*?)</a>',
        re.IGNORECASE | re.DOTALL,
    )
    date_pattern = re.compile(r"(\d{1,2}/\d{1,2}/\d{4}|\d{4}-\d{2}-\d{2})")

    for match in link_pattern.finditer(text):
        href = match.group(1).strip()
        link_text = strip_html(match.group(2)).strip()
        if not link_text or len(link_text) < 5:
            continue
        if not href.startswith("http"):
            href = "https://www.courts.michigan.gov" + href

        date_match = date_pattern.search(link_text)
        date_str = date_match.group(0) if date_match else ""

        detected_court = court
        if "supreme" in link_text.lower():
            detected_court = "MSC"
        elif "appeal" in link_text.lower():
            detected_court = "COA"

        items.append(FeedItem(
            title=link_text, url=href, date_str=date_str, court=detected_court,
        ))
    return items

# ---------------------------------------------------------------------------
# Fetching orchestrator
# ---------------------------------------------------------------------------

def fetch_feed_items(since_days: Optional[int] = None) -> list[FeedItem]:
    """Fetch from all configured sources, dedup, and return items."""
    all_items: list[FeedItem] = []
    seen_ids: set[str] = set()

    for court, sources in FEED_SOURCES.items():
        court_items: list[FeedItem] = []
        for src in sources:
            log.info("Trying %s: %s", src["label"], src["url"])
            raw = _fetch_url(src["url"])
            if raw is None:
                log.info("  -> No response, trying next source")
                time.sleep(RATE_LIMIT_SECONDS)
                continue

            kind = src["kind"]
            if kind == "courtlistener":
                court_items = _parse_courtlistener(raw, court)
            elif kind == "json_api":
                court_items = _parse_json_api(raw, court)
            elif kind == "rss":
                court_items = _parse_rss(raw, court)
            elif kind == "sitemap_xml":
                court_items = _parse_sitemap(raw, court)
            else:
                court_items = _parse_opinions_html(raw, court)

            if court_items:
                log.info("  -> Got %d items from %s", len(court_items), src["label"])
                break
            log.info("  -> 0 items parsed, trying next source")
            time.sleep(RATE_LIMIT_SECONDS)

        if not court_items:
            log.info("Trying HTML scrape fallback for %s", court)
            raw = _fetch_url("https://www.courts.michigan.gov/opinions-orders/")
            if raw:
                court_items = _parse_opinions_html(raw, court)
                log.info("  -> Scraped %d items from opinions-orders page", len(court_items))
            time.sleep(RATE_LIMIT_SECONDS)

        for item in court_items:
            sid = item.stable_id
            if sid not in seen_ids:
                seen_ids.add(sid)
                all_items.append(item)

    if since_days is not None and since_days > 0:
        cutoff = datetime.now(timezone.utc) - timedelta(days=since_days)
        filtered: list[FeedItem] = []
        for item in all_items:
            if not item.date_str:
                filtered.append(item)
                continue
            item_date = _parse_date(item.date_str)
            if item_date is None or item_date >= cutoff:
                filtered.append(item)
        log.info("Filtered to %d items within last %d days (from %d total)",
                 len(filtered), since_days, len(all_items))
        all_items = filtered

    log.info("Total unique items fetched: %d", len(all_items))
    return all_items


def _parse_date(date_str: str) -> Optional[datetime]:
    """Best-effort date parsing from various formats."""
    for fmt in (
        "%Y-%m-%dT%H:%M:%S%z",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d",
        "%m/%d/%Y",
        "%B %d, %Y",
        "%b %d, %Y",
        "%a, %d %b %Y %H:%M:%S %z",
        "%a, %d %b %Y %H:%M:%S %Z",
        "%d %b %Y",
    ):
        try:
            dt = datetime.strptime(date_str.strip(), fmt)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
        except ValueError:
            continue
    return None

# ---------------------------------------------------------------------------
# Relevance scoring
# ---------------------------------------------------------------------------

class ScoreResult:
    __slots__ = ("score", "matches")

    def __init__(self, score: float, matches: list[str]) -> None:
        self.score = score
        self.matches = matches


def score_relevance(item: FeedItem) -> ScoreResult:
    """Score a feed item for relevance to Pigors v. Watson."""
    text = item.searchable_text
    if not text:
        return ScoreResult(0.10, [])

    matched: list[tuple[str, float]] = []

    for pat, weight in _HIGH_COMPILED:
        if pat.search(text):
            matched.append((pat.pattern, weight))

    for pat, weight in _MEDIUM_COMPILED:
        if pat.search(text):
            matched.append((pat.pattern, weight))

    for pat, weight in _LOW_COMPILED:
        if pat.search(text):
            matched.append((pat.pattern, weight))

    if not matched:
        return ScoreResult(0.10, ["michigan_court_opinion"])

    max_score = max(w for _, w in matched)
    bonus = min(0.05 * (len(matched) - 1), 0.10)
    final_score = min(round(max_score + bonus, 3), 1.0)

    match_labels = [p for p, _ in matched]
    return ScoreResult(final_score, match_labels)

# ---------------------------------------------------------------------------
# Storage: court_feed table
# ---------------------------------------------------------------------------

def store_feed_items(items: list[FeedItem]) -> tuple[int, int]:
    """Insert items into court_feed. Returns (inserted, skipped)."""
    conn = get_mbp_conn()
    inserted = 0
    skipped = 0
    now = datetime.now(timezone.utc).isoformat()

    try:
        for item in items:
            result = score_relevance(item)
            try:
                conn.execute(
                    """INSERT INTO court_feed
                       (source, title, url, citation, relevance_score, is_processed, fetched_at)
                       VALUES (?, ?, ?, ?, ?, 0, ?)
                       ON CONFLICT(url) DO UPDATE SET
                           relevance_score = MAX(excluded.relevance_score, court_feed.relevance_score),
                           fetched_at = excluded.fetched_at
                       """,
                    (
                        item.court,
                        item.title[:500],
                        item.url or f"no-url-{item.stable_id}",
                        item.citation[:200],
                        result.score,
                        now,
                    ),
                )
                if conn.total_changes:
                    inserted += 1
            except sqlite3.IntegrityError:
                skipped += 1

            if result.score >= 0.8:
                _alert_high_relevance(item, result)

        conn.commit()

        actual = conn.execute("SELECT COUNT(*) FROM court_feed WHERE fetched_at = ?", (now,)).fetchone()[0]
        log.info("Stored %d items (%d skipped as duplicates, %d confirmed in DB)",
                 inserted, skipped, actual)
    finally:
        conn.close()

    return inserted, skipped


def _ensure_url_unique_index(conn: sqlite3.Connection) -> None:
    """Create unique index on url if it doesn't exist."""
    indexes = {
        row[1]
        for row in conn.execute("PRAGMA index_list(court_feed)").fetchall()
    }
    if "idx_court_feed_url" not in indexes:
        try:
            conn.execute(
                "CREATE UNIQUE INDEX IF NOT EXISTS idx_court_feed_url ON court_feed(url)"
            )
            conn.commit()
            log.debug("Created unique index idx_court_feed_url")
        except sqlite3.OperationalError as exc:
            log.warning("Could not create unique index on url: %s", exc)


def _alert_high_relevance(item: FeedItem, result: ScoreResult) -> None:
    matches_str = ", ".join(result.matches[:5])
    log.info("")
    log.info("=" * 70)
    log.info("  HIGH RELEVANCE: %s", item.citation or item.title[:80])
    log.info("  %s (score: %.2f)", item.title[:100], result.score)
    log.info("  Matches: %s", matches_str)
    if item.url:
        log.info("  URL: %s", item.url)
    log.info("=" * 70)
    log.info("")

# ---------------------------------------------------------------------------
# Processing: create authority nodes + edges
# ---------------------------------------------------------------------------

def process_feed_items(min_score: float = 0.4) -> tuple[int, int]:
    """
    Process unprocessed court_feed items above min_score.
    Creates nodes + edges in mbp_brain.db.
    Returns (nodes_created, edges_created).
    """
    conn = get_mbp_conn()
    _ensure_url_unique_index(conn)
    nodes_created = 0
    edges_created = 0
    now = datetime.now(timezone.utc).isoformat()

    try:
        rows = conn.execute(
            """SELECT id, source, title, url, citation, relevance_score
               FROM court_feed
               WHERE is_processed = 0 AND relevance_score >= ?
               ORDER BY relevance_score DESC""",
            (min_score,),
        ).fetchall()

        if not rows:
            log.info("No unprocessed items with score >= %.2f", min_score)
            return 0, 0

        log.info("Processing %d items (min_score=%.2f)", len(rows), min_score)

        rule_numbers = _load_tracked_rules()

        for row in rows:
            feed_id = row["id"]
            court = row["source"] or "UNKNOWN"
            title = row["title"] or ""
            url = row["url"] or ""
            citation = row["citation"] or ""
            rel_score = row["relevance_score"] or 0.0

            node_id = f"cf-{feed_id}"
            label = citation if citation else title[:120]
            node_type = "CaseLaw" if citation else "CourtOrder"
            binding = "mandatory" if court == "MSC" else "persuasive"
            description = f"{title} (fetched from Michigan Courts)"

            metadata = json.dumps({
                "url": url,
                "court": court,
                "citation": citation,
                "relevance_score": rel_score,
                "feed_id": feed_id,
                "fetched_via": "court_feed.py",
            }, ensure_ascii=False)

            try:
                conn.execute(
                    """INSERT INTO nodes
                       (id, node_type, layer, label, description,
                        confidence, binding_strength, source_table, metadata, created_at)
                       VALUES (?, ?, 'AUTHORITY', ?, ?, ?, ?, 'court_feed', ?, ?)
                       ON CONFLICT(id) DO UPDATE SET
                           confidence = MAX(excluded.confidence, nodes.confidence),
                           metadata = excluded.metadata""",
                    (node_id, node_type, label, description,
                     rel_score, binding, metadata, now),
                )
                nodes_created += 1
            except sqlite3.Error as exc:
                log.warning("Failed to insert node %s: %s", node_id, exc)
                continue

            search_text = f"{title} {citation}"
            edges_created += _create_citation_edges(
                conn, node_id, search_text, rule_numbers, now
            )

            conn.execute(
                "UPDATE court_feed SET is_processed = 1, processed_at = ? WHERE id = ?",
                (now, feed_id),
            )

        conn.commit()

        verify_nodes = conn.execute(
            "SELECT COUNT(*) FROM nodes WHERE source_table = 'court_feed' AND created_at = ?",
            (now,),
        ).fetchone()[0]
        log.info("Verified: %d nodes in DB from this run", verify_nodes)

        conn.execute(
            """INSERT INTO brain_ops
               (operation, input_params, output_summary, nodes_touched, edges_traversed, created_at)
               VALUES ('court_feed_process', ?, ?, ?, ?, ?)""",
            (
                json.dumps({"min_score": min_score, "items": len(rows)}),
                f"Created {nodes_created} nodes, {edges_created} edges",
                nodes_created,
                edges_created,
                now,
            ),
        )
        conn.commit()

    finally:
        conn.close()

    log.info("Processing complete: %d nodes, %d edges created", nodes_created, edges_created)
    return nodes_created, edges_created


def _load_tracked_rules() -> set[str]:
    """Load rule numbers from michigan_rules_extracted for edge matching."""
    rules: set[str] = set()
    try:
        lconn = get_litctx_conn()
        rows = lconn.execute(
            "SELECT DISTINCT rule_number FROM michigan_rules_extracted WHERE rule_number IS NOT NULL"
        ).fetchall()
        for row in rows:
            val = row["rule_number"]
            if val:
                rules.add(val.strip())
        lconn.close()
        log.debug("Loaded %d tracked rules from litigation_context.db", len(rules))
    except Exception as exc:
        log.warning("Could not load tracked rules: %s", exc)
    return rules


def _create_citation_edges(
    conn: sqlite3.Connection,
    node_id: str,
    text: str,
    rule_numbers: set[str],
    now: str,
) -> int:
    """Create CITES edges from a node to rules it references."""
    edges = 0

    for match in _MCR_CITE.finditer(text):
        rule_num = f"MCR {match.group(1)}"
        if rule_num in rule_numbers or match.group(1) in rule_numbers:
            target_id = f"rule-{rule_num.replace(' ', '-').replace('.', '_')}"
            edges += _insert_edge(conn, node_id, target_id, "CITES", 0.8, rule_num, now)

    for match in _MCL_CITE.finditer(text):
        rule_num = f"MCL {match.group(1)}"
        if rule_num in rule_numbers or match.group(1) in rule_numbers:
            target_id = f"rule-{rule_num.replace(' ', '-').replace('.', '_')}"
            edges += _insert_edge(conn, node_id, target_id, "CITES", 0.7, rule_num, now)

    return edges


def _insert_edge(
    conn: sqlite3.Connection,
    source_id: str,
    target_id: str,
    edge_type: str,
    weight: float,
    evidence_text: str,
    now: str,
) -> int:
    """Insert an edge, return 1 on success, 0 on failure/duplicate."""
    try:
        existing = conn.execute(
            "SELECT 1 FROM edges WHERE source_id = ? AND target_id = ? AND edge_type = ?",
            (source_id, target_id, edge_type),
        ).fetchone()
        if existing:
            return 0
        conn.execute(
            """INSERT INTO edges
               (source_id, target_id, edge_type, weight, evidence, source_table, created_at)
               VALUES (?, ?, ?, ?, ?, 'court_feed', ?)""",
            (source_id, target_id, edge_type, weight, evidence_text, now),
        )
        return 1
    except sqlite3.Error as exc:
        log.warning("Edge insert failed %s->%s: %s", source_id, target_id, exc)
        return 0

# ---------------------------------------------------------------------------
# Status report
# ---------------------------------------------------------------------------

def show_status() -> None:
    """Print current feed stats."""
    conn = get_mbp_conn()
    try:
        row = conn.execute("""
            SELECT
                (SELECT COUNT(*) FROM court_feed) AS total,
                (SELECT COUNT(*) FROM court_feed WHERE is_processed = 1) AS processed,
                (SELECT COUNT(*) FROM court_feed WHERE is_processed = 0) AS pending,
                (SELECT COUNT(*) FROM court_feed WHERE relevance_score >= 0.8) AS high_rel,
                (SELECT COUNT(*) FROM court_feed WHERE relevance_score >= 0.4 AND relevance_score < 0.8) AS med_rel,
                (SELECT COUNT(*) FROM court_feed WHERE relevance_score < 0.4) AS low_rel,
                (SELECT COUNT(*) FROM nodes WHERE source_table = 'court_feed') AS feed_nodes,
                (SELECT COUNT(*) FROM edges WHERE source_table = 'court_feed') AS feed_edges,
                (SELECT MIN(fetched_at) FROM court_feed) AS first_fetch,
                (SELECT MAX(fetched_at) FROM court_feed) AS last_fetch
        """).fetchone()

        print("\n" + "=" * 60)
        print("  MICHIGAN COURT FEED STATUS")
        print("=" * 60)
        print(f"  Total items:        {row['total']:>6}")
        print(f"  Processed:          {row['processed']:>6}")
        print(f"  Pending:            {row['pending']:>6}")
        print("-" * 60)
        print(f"  HIGH relevance:     {row['high_rel']:>6}  (>= 0.8)")
        print(f"  MEDIUM relevance:   {row['med_rel']:>6}  (0.4 - 0.8)")
        print(f"  LOW relevance:      {row['low_rel']:>6}  (< 0.4)")
        print("-" * 60)
        print(f"  Authority nodes:    {row['feed_nodes']:>6}")
        print(f"  Citation edges:     {row['feed_edges']:>6}")
        print("-" * 60)
        print(f"  First fetch:  {row['first_fetch'] or 'never'}")
        print(f"  Last fetch:   {row['last_fetch'] or 'never'}")
        print("=" * 60)

        high_items = conn.execute(
            """SELECT source, title, citation, relevance_score, url
               FROM court_feed
               WHERE relevance_score >= 0.8
               ORDER BY relevance_score DESC
               LIMIT 10"""
        ).fetchall()

        if high_items:
            print("\n  TOP HIGH-RELEVANCE ITEMS:")
            print("-" * 60)
            for hi in high_items:
                label = hi["citation"] or hi["title"][:60]
                print(f"  [{hi['source']}] {label} (score: {hi['relevance_score']:.2f})")
                if hi["url"]:
                    print(f"         {hi['url']}")
            print()

    finally:
        conn.close()

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Michigan Court Feed Fetcher for LitigationOS",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--process", action="store_true",
        help="Fetch, score, AND create authority nodes in mbp_brain.db",
    )
    parser.add_argument(
        "--status", action="store_true",
        help="Show current feed statistics and exit",
    )
    parser.add_argument(
        "--since", type=int, default=None, metavar="DAYS",
        help="Only fetch items from the last N days",
    )
    parser.add_argument(
        "--min-score", type=float, default=0.4, metavar="SCORE",
        help="Minimum relevance score for processing (default: 0.4)",
    )
    args = parser.parse_args()

    log.info("court_feed.py started (process=%s, since=%s, min_score=%.2f)",
             args.process, args.since, args.min_score)

    if not MBP_BRAIN_DB.exists():
        log.error("mbp_brain.db not found at %s", MBP_BRAIN_DB)
        return 1

    conn = get_mbp_conn()
    _ensure_url_unique_index(conn)
    conn.close()

    if args.status:
        show_status()
        return 0

    items = fetch_feed_items(since_days=args.since)

    if not items:
        log.info("No items fetched from any source. Network may be unavailable.")
        show_status()
        return 0

    for item in items:
        result = score_relevance(item)
        log.debug("  %s | score=%.2f | %s",
                   item.court, result.score, (item.citation or item.title)[:60])

    scores = [score_relevance(i).score for i in items]
    high_count = sum(1 for s in scores if s >= 0.8)
    med_count = sum(1 for s in scores if 0.4 <= s < 0.8)
    low_count = sum(1 for s in scores if s < 0.4)
    log.info("Relevance distribution: HIGH=%d, MEDIUM=%d, LOW=%d", high_count, med_count, low_count)

    inserted, skipped = store_feed_items(items)

    if args.process:
        nodes, edges = process_feed_items(min_score=args.min_score)
        log.info("Processing results: %d nodes, %d edges", nodes, edges)

    show_status()
    log.info("court_feed.py finished successfully")
    return 0


if __name__ == "__main__":
    sys.exit(main())
