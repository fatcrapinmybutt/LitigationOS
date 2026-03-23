#!/usr/bin/env python3
"""Court Feed Scraper — Check Michigan court feeds for updates.

Standalone tool that checks RSS/Atom feeds and scrape targets seeded
in court_feed_sources, scores relevance against Pigors v. Watson
case terms, and stores results in court_feed_entries.

Usage:
    python court_feed_scraper.py --check              # Check all active feeds
    python court_feed_scraper.py --check --days 7     # Show recent entries
    python court_feed_scraper.py --recent              # Recent entries (7 days)
    python court_feed_scraper.py --recent --days 14
    python court_feed_scraper.py --sources             # List configured sources
    python court_feed_scraper.py --track-rules         # Track MCR rule amendments
    python court_feed_scraper.py --score-opinion TEXT  # Score opinion text for relevance
    python court_feed_scraper.py --check-forms         # Check SCAO form versions
    python court_feed_scraper.py --update-citations    # Check citation freshness
    python court_feed_scraper.py --digest              # Generate weekly legal digest
    python court_feed_scraper.py --digest --days 14    # Custom digest window
    python court_feed_scraper.py --help
"""
import argparse
import datetime
import re
import sqlite3
import sys
import os
import xml.etree.ElementTree as ET

import json
import hashlib

try:
    import urllib.request
    import urllib.error
    HAS_URLLIB = True
except ImportError:
    HAS_URLLIB = False

DB_PATH = r"C:\Users\andre\LitigationOS\litigation_context.db"
COURT_FORMS_DB = r"C:\Users\andre\LitigationOS\court_forms.db"
REPORTS_DIR = r"C:\Users\andre\LitigationOS\05_REPORTS"

# Relevance keywords — weighted for Pigors v. Watson case lanes
RELEVANCE_KEYWORDS = {
    # Lane A — Custody / Family
    "custody": 3.0,
    "parenting time": 3.0,
    "parenting-time": 3.0,
    "child custody": 3.0,
    "best interest": 2.5,
    "friend of the court": 2.0,
    "FOC": 2.0,
    "domestic relations": 2.0,
    "family division": 2.0,
    # Lane B — Housing
    "eviction": 2.0,
    "landlord": 1.5,
    "tenant": 1.5,
    "housing": 1.5,
    "property": 1.5,
    # Lane D — PPO
    "personal protection": 3.0,
    "PPO": 3.0,
    "stalking": 2.0,
    "contempt": 2.5,
    # Lane E — Judicial Misconduct
    "judicial misconduct": 4.0,
    "judicial tenure": 4.0,
    "JTC": 4.0,
    "disqualification": 3.0,
    "MCR 2.003": 4.0,
    "recusal": 3.0,
    "due process": 2.5,
    "ex parte": 3.0,
    # Lane F — Appellate
    "court of appeals": 2.0,
    "supreme court": 2.0,
    "COA": 2.0,
    "MSC": 2.0,
    "appellate": 2.0,
    # General legal
    "MCR": 1.5,
    "court rule": 1.5,
    "amendment": 1.0,
    "administrative order": 1.5,
    "SCAO": 1.5,
    # Muskegon / 14th Circuit
    "muskegon": 3.0,
    "14th circuit": 3.0,
    "McNeill": 5.0,
}


def get_db():
    """Open DB with WAL + busy_timeout."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA busy_timeout = 60000")
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA cache_size = -32000")
    conn.execute("PRAGMA temp_store = MEMORY")
    conn.execute("PRAGMA synchronous = NORMAL")
    return conn


def score_relevance(title: str, content: str = "") -> float:
    """Score relevance of a feed entry against case-specific keywords.

    Returns a float 0.0 – 10.0 (capped).
    """
    text = f"{title} {content}".lower()
    score = 0.0
    for keyword, weight in RELEVANCE_KEYWORDS.items():
        pattern = re.escape(keyword.lower())
        matches = len(re.findall(pattern, text))
        if matches:
            score += weight * min(matches, 3)  # cap per-keyword contribution
    return min(round(score, 2), 10.0)


def parse_rss(url: str, timeout: int = 30) -> list[dict]:
    """Parse an RSS or Atom feed from *url*.

    Returns a list of dicts with keys: title, content, url, published_date.
    On network error returns an empty list (this tool runs offline-safe).
    """
    if not HAS_URLLIB:
        return []

    try:
        req = urllib.request.Request(url, headers={"User-Agent": "LitigationOS/2.0 CourtFeedScraper"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = resp.read()
    except (urllib.error.URLError, OSError, TimeoutError) as exc:
        print(f"  [WARN] Could not fetch {url}: {exc}")
        return []

    entries = []
    try:
        root = ET.fromstring(data)
    except ET.ParseError:
        print(f"  [WARN] Could not parse XML from {url}")
        return []

    # RSS 2.0
    for item in root.iter("item"):
        entries.append({
            "title": _text(item, "title"),
            "content": _text(item, "description"),
            "url": _text(item, "link"),
            "published_date": _text(item, "pubDate"),
        })

    # Atom
    ns = {"atom": "http://www.w3.org/2005/Atom"}
    for entry in root.iter("{http://www.w3.org/2005/Atom}entry"):
        link_el = entry.find("atom:link", ns)
        link_href = link_el.get("href", "") if link_el is not None else ""
        entries.append({
            "title": _text(entry, "{http://www.w3.org/2005/Atom}title"),
            "content": _text(entry, "{http://www.w3.org/2005/Atom}summary")
                        or _text(entry, "{http://www.w3.org/2005/Atom}content"),
            "url": link_href,
            "published_date": _text(entry, "{http://www.w3.org/2005/Atom}published")
                              or _text(entry, "{http://www.w3.org/2005/Atom}updated"),
        })

    return entries


def _text(parent, tag: str) -> str:
    el = parent.find(tag)
    return (el.text or "").strip() if el is not None else ""


def check_feeds(verbose: bool = True) -> int:
    """Check all active feed sources and store new entries. Returns count of new entries."""
    conn = get_db()
    sources = conn.execute(
        "SELECT * FROM court_feed_sources WHERE active = 1"
    ).fetchall()

    if not sources:
        print("No active feed sources configured.")
        conn.close()
        return 0

    total_new = 0
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()

    for src in sources:
        if verbose:
            print(f"Checking: {src['source_name']} ({src['feed_type']})")

        if src["feed_type"] == "rss":
            entries = parse_rss(src["source_url"])
        else:
            # Scrape and API sources are stubs — they log a placeholder
            if verbose:
                print(f"  [STUB] {src['feed_type']} scraper not yet implemented for {src['source_name']}")
            entries = []

        new_count = 0
        for e in entries:
            # Deduplicate by URL within this source
            exists = conn.execute(
                "SELECT 1 FROM court_feed_entries WHERE source_id = ? AND url = ?",
                (src["id"], e["url"]),
            ).fetchone()
            if exists:
                continue

            rel_score = score_relevance(e["title"], e["content"])
            case_num = _extract_case_number(f"{e['title']} {e['content']}")
            tags = _auto_tag(e["title"], e["content"])

            conn.execute(
                """INSERT INTO court_feed_entries
                   (source_id, title, content, url, published_date, relevance_score, case_number, tags)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    src["id"],
                    e["title"],
                    e["content"][:2000] if e["content"] else None,
                    e["url"],
                    e["published_date"],
                    rel_score,
                    case_num,
                    tags,
                ),
            )
            new_count += 1

        # Update last_checked
        conn.execute(
            "UPDATE court_feed_sources SET last_checked = ? WHERE id = ?",
            (now, src["id"]),
        )
        conn.commit()

        if verbose:
            print(f"  → {new_count} new entries (from {len(entries)} fetched)")
        total_new += new_count

    conn.close()
    return total_new


def _extract_case_number(text: str) -> str | None:
    """Try to pull a Michigan-style case number from text."""
    patterns = [
        r"\d{4}-\d{4,6}-[A-Z]{2,3}",  # 2024-001507-DC
        r"No\.\s*(\d+)",               # No. 366810
        r"Case\s+#?\s*(\S+)",
    ]
    for pat in patterns:
        m = re.search(pat, text)
        if m:
            return m.group(0)
    return None


def _auto_tag(title: str, content: str) -> str:
    """Return comma-separated tags based on keyword hits."""
    text = f"{title} {content}".lower()
    tags = set()
    tag_map = {
        "custody": "custody",
        "parenting": "parenting-time",
        "PPO": "ppo",
        "personal protection": "ppo",
        "contempt": "contempt",
        "appellate": "appellate",
        "court of appeals": "appellate",
        "supreme court": "supreme-court",
        "MCR": "court-rules",
        "court rule": "court-rules",
        "administrative order": "admin-order",
        "SCAO": "scao",
        "judicial": "judicial",
        "misconduct": "misconduct",
        "eviction": "housing",
        "muskegon": "local",
    }
    for keyword, tag in tag_map.items():
        if keyword.lower() in text:
            tags.add(tag)
    return ",".join(sorted(tags)) if tags else ""


def get_recent(days: int = 7, min_relevance: float = 0.0) -> list[dict]:
    """Return recent feed entries from the last *days* days."""
    conn = get_db()
    cutoff = (
        datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=days)
    ).isoformat()

    rows = conn.execute(
        """SELECT e.*, s.source_name
           FROM court_feed_entries e
           JOIN court_feed_sources s ON e.source_id = s.id
           WHERE e.created_at >= ? AND e.relevance_score >= ?
           ORDER BY e.relevance_score DESC, e.created_at DESC
           LIMIT 100""",
        (cutoff, min_relevance),
    ).fetchall()

    conn.close()
    return [dict(r) for r in rows]


def list_sources():
    """Print configured sources."""
    conn = get_db()
    rows = conn.execute("SELECT * FROM court_feed_sources ORDER BY active DESC, id").fetchall()
    conn.close()

    print(f"\n{'ID':>3}  {'Active':>6}  {'Type':<7}  {'Freq':<8}  {'Source Name'}")
    print("-" * 70)
    for r in rows:
        status = "  YES" if r["active"] else "   NO"
        print(f"{r['id']:>3}  {status:>6}  {r['feed_type']:<7}  {r['frequency']:<8}  {r['source_name']}")
    print(f"\nTotal: {len(rows)} sources")


# ─── Case lane definitions for opinion scoring ───────────────────────────────

LANE_KEYWORDS = {
    "A": {
        "name": "Custody / Family",
        "keywords": {
            "custody": 4, "parenting time": 4, "parenting-time": 4,
            "child custody": 4, "best interest": 3, "best interests": 3,
            "friend of the court": 3, "FOC": 3, "domestic relations": 2,
            "family division": 2, "parental rights": 3, "visitation": 3,
            "child support": 2, "guardian ad litem": 2, "MCL 722.23": 4,
            "parental alienation": 4, "custodial interference": 4,
        },
    },
    "B": {
        "name": "Housing / Shady Oaks",
        "keywords": {
            "eviction": 3, "landlord": 2, "tenant": 2, "housing": 2,
            "property": 2, "title": 2, "habitability": 3, "lockout": 3,
            "utility shutoff": 3, "water shutoff": 3, "sewage": 2,
        },
    },
    "D": {
        "name": "PPO / Protection Orders",
        "keywords": {
            "personal protection": 4, "PPO": 4, "stalking": 3,
            "contempt": 3, "protection order": 4, "MCL 600.2950": 4,
            "domestic violence": 3, "restraining order": 3,
        },
    },
    "E": {
        "name": "Judicial Misconduct",
        "keywords": {
            "judicial misconduct": 5, "judicial tenure": 5, "JTC": 5,
            "disqualification": 4, "MCR 2.003": 5, "recusal": 4,
            "due process": 3, "ex parte": 4, "bias": 3, "prejudice": 3,
            "judicial discipline": 4, "canon": 3,
        },
    },
    "F": {
        "name": "Appellate",
        "keywords": {
            "court of appeals": 3, "supreme court": 3, "COA": 3,
            "MSC": 3, "appellate": 3, "MCR 7.203": 4, "MCR 7.305": 4,
            "MCR 7.215": 3, "leave to appeal": 3, "de novo": 2,
            "abuse of discretion": 3, "clearly erroneous": 3,
        },
    },
}

# MCR rules relevant to Pigors v. Watson
TRACKED_RULES = [
    "MCR 2.003", "MCR 2.107", "MCR 2.119", "MCR 2.612",
    "MCR 3.206", "MCR 3.211", "MCR 3.606", "MCR 3.708",
    "MCR 7.203", "MCR 7.205", "MCR 7.215", "MCR 7.305",
    "MCR 8.119",
]

RULE_AMENDMENT_URLS = [
    "https://courts.michigan.gov/courts/michigansupremecourt/rules/court-rules-admin-matters",
    "https://courts.michigan.gov/courts/michigansupremecourt/rules/proposed-adopted",
]


# ─── Feature 1: Rule Amendment Tracker ────────────────────────────────────────

def track_rule_changes(verbose: bool = True) -> int:
    """Monitor MCR amendments from courts.michigan.gov.

    Fetches rule amendment pages, extracts rule references, checks if any
    tracked rules (MCR 2.003, 3.606, 7.203, etc.) are mentioned, and stores
    new changes in the rule_changes table.

    Returns count of new rule changes found.
    """
    conn = get_db()
    _ensure_rule_changes_table(conn)

    if verbose:
        print("=== Tracking MCR Rule Amendments ===\n")

    total_new = 0
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()

    for url in RULE_AMENDMENT_URLS:
        if verbose:
            print(f"Checking: {url}")

        html = _fetch_page(url)
        if not html:
            if verbose:
                print("  [WARN] Could not fetch page")
            continue

        changes = _extract_rule_changes(html, url)
        if verbose:
            print(f"  Found {len(changes)} rule references")

        for change in changes:
            # Dedup by rule_number + description hash
            desc_hash = hashlib.sha256(
                (change["rule_number"] + change["description"]).encode()
            ).hexdigest()[:16]

            exists = conn.execute(
                """SELECT 1 FROM rule_changes
                   WHERE rule_number = ? AND description LIKE ?""",
                (change["rule_number"], f"%{desc_hash}%"),
            ).fetchone()

            if exists:
                continue

            # Assess impact on our case lanes
            impact = _assess_rule_impact(change["rule_number"], change["description"])

            conn.execute(
                """INSERT INTO rule_changes
                   (rule_number, change_type, effective_date, description,
                    impact_assessment, source_url)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (
                    change["rule_number"],
                    change.get("change_type", "amendment"),
                    change.get("effective_date"),
                    f"{change['description']} [hash:{desc_hash}]",
                    impact,
                    url,
                ),
            )
            total_new += 1

            if verbose and change["rule_number"] in TRACKED_RULES:
                print(f"  ⚠ RELEVANT: {change['rule_number']} — {impact}")

    conn.commit()

    # Also show existing tracked rule changes
    if verbose:
        tracked = conn.execute(
            """SELECT rule_number, change_type, effective_date,
                      substr(description, 1, 80) as desc_short,
                      impact_assessment
               FROM rule_changes
               WHERE rule_number IN ({})
               ORDER BY created_at DESC LIMIT 20""".format(
                ",".join("?" for _ in TRACKED_RULES)
            ),
            TRACKED_RULES,
        ).fetchall()

        if tracked:
            print(f"\n--- Tracked Rule Changes ({len(tracked)}) ---")
            for r in tracked:
                flag = "🔴" if "HIGH" in (r["impact_assessment"] or "") else "🟡"
                print(f"  {flag} {r['rule_number']:<12} {r['change_type']:<12} "
                      f"{r['effective_date'] or 'N/A':<12} {r['desc_short']}")
        else:
            print("\nNo tracked rule changes recorded yet.")

    conn.close()
    if verbose:
        print(f"\n=== Done: {total_new} new rule changes recorded ===")
    return total_new


def _ensure_rule_changes_table(conn):
    """Ensure rule_changes table exists with correct schema."""
    conn.execute("""
        CREATE TABLE IF NOT EXISTS rule_changes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            rule_number TEXT,
            change_type TEXT,
            effective_date TEXT,
            description TEXT,
            impact_assessment TEXT,
            source_url TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        )
    """)
    conn.commit()


def _fetch_page(url: str, timeout: int = 30) -> str:
    """Fetch a web page as text. Returns empty string on failure."""
    if not HAS_URLLIB:
        return ""
    try:
        req = urllib.request.Request(
            url, headers={"User-Agent": "LitigationOS/2.0 CourtFeedScraper"}
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read().decode("utf-8", errors="replace")
    except (urllib.error.URLError, OSError, TimeoutError):
        return ""


def _extract_rule_changes(html: str, source_url: str) -> list[dict]:
    """Extract rule change references from HTML page content."""
    changes = []
    # Match patterns like "MCR X.XXX" or "MCR X.XXX(X)"
    rule_pattern = re.compile(
        r"(MCR\s+\d+\.\d{3}(?:\([A-Za-z0-9]+\))?)", re.IGNORECASE
    )
    # Look for date patterns near rule references
    date_pattern = re.compile(
        r"(?:effective|eff\.?|dated?)\s+(\w+\s+\d{1,2},?\s+\d{4})", re.IGNORECASE
    )
    # Amendment type patterns
    type_pattern = re.compile(
        r"(amend(?:ed|ment)?|adopt(?:ed|ion)?|rescind(?:ed)?|proposed|modified)",
        re.IGNORECASE,
    )

    # Strip HTML tags for text analysis
    text = re.sub(r"<[^>]+>", " ", html)
    text = re.sub(r"\s+", " ", text)

    # Split into chunks around rule references
    for match in rule_pattern.finditer(text):
        rule_num = match.group(1).upper().replace("MCR ", "MCR ")
        # Normalize to "MCR X.XXX"
        rule_num = re.sub(r"\s+", " ", rule_num).strip()

        # Get context (200 chars around the match)
        start = max(0, match.start() - 100)
        end = min(len(text), match.end() + 200)
        context = text[start:end]

        # Extract effective date if nearby
        date_match = date_pattern.search(context)
        eff_date = date_match.group(1) if date_match else None

        # Extract change type
        type_match = type_pattern.search(context)
        change_type = type_match.group(1).lower() if type_match else "amendment"

        changes.append({
            "rule_number": rule_num,
            "change_type": change_type,
            "effective_date": eff_date,
            "description": context.strip()[:500],
        })

    # Deduplicate by rule number within this batch
    seen = set()
    unique = []
    for c in changes:
        key = c["rule_number"]
        if key not in seen:
            seen.add(key)
            unique.append(c)

    return unique


def _assess_rule_impact(rule_number: str, description: str) -> str:
    """Assess the impact of a rule change on our case lanes."""
    impacts = []
    rule_upper = rule_number.upper()
    desc_lower = description.lower()

    lane_rule_map = {
        "Lane A (Custody)": ["MCR 3.206", "MCR 3.211", "MCR 3.708"],
        "Lane B (Housing)": [],
        "Lane D (PPO)": ["MCR 3.606", "MCR 3.708"],
        "Lane E (Misconduct)": ["MCR 2.003", "MCR 2.107", "MCR 2.119"],
        "Lane F (Appellate)": ["MCR 7.203", "MCR 7.205", "MCR 7.215", "MCR 7.305"],
    }

    for lane, rules in lane_rule_map.items():
        for r in rules:
            if r in rule_upper:
                impacts.append(lane)
                break

    if not impacts:
        return "LOW — No direct case lane impact"

    severity = "HIGH" if len(impacts) >= 2 or any(
        k in desc_lower for k in ["rescind", "amend", "modify", "repeal"]
    ) else "MEDIUM"

    return f"{severity} — Affects: {', '.join(impacts)}"


# ─── Feature 2: Opinion Relevance Scorer ──────────────────────────────────────

def score_opinion(text: str) -> dict:
    """Score a COA/MSC opinion for relevance to our 6 case lanes.

    Returns dict with:
        - score: 0-100 overall relevance
        - matched_lanes: list of dicts with lane, score, matched_keywords
        - tier: 'high' (70+), 'medium' (40-69), 'low' (0-39)
    """
    text_lower = text.lower()
    lane_scores = {}

    for lane_id, lane_def in LANE_KEYWORDS.items():
        lane_score = 0.0
        matched = []

        for keyword, weight in lane_def["keywords"].items():
            count = len(re.findall(re.escape(keyword.lower()), text_lower))
            if count > 0:
                contribution = weight * min(count, 5)  # Cap per-keyword
                lane_score += contribution
                matched.append({"keyword": keyword, "count": count, "weight": weight})

        lane_scores[lane_id] = {
            "lane": lane_id,
            "lane_name": lane_def["name"],
            "raw_score": round(lane_score, 2),
            "matched_keywords": matched,
        }

    # Normalize: highest possible per-lane ~ 50 (10 keywords × 5 weight)
    # Overall score = weighted combo of lane scores, capped at 100
    raw_total = sum(ls["raw_score"] for ls in lane_scores.values())
    overall = min(100, round(raw_total * 1.5, 1))  # Scale factor

    # Assign per-lane normalized scores (0-100)
    for ls in lane_scores.values():
        ls["score"] = min(100, round(ls["raw_score"] * 3, 1))

    matched_lanes = sorted(
        [ls for ls in lane_scores.values() if ls["score"] > 0],
        key=lambda x: x["score"],
        reverse=True,
    )

    if overall >= 70:
        tier = "high"
    elif overall >= 40:
        tier = "medium"
    else:
        tier = "low"

    return {
        "score": overall,
        "tier": tier,
        "matched_lanes": matched_lanes,
    }


# ─── Feature 3: Form Version Tracker ─────────────────────────────────────────

SCAO_FORMS_URL = "https://courts.michigan.gov/administration/scao/forms"


def check_form_versions(verbose: bool = True) -> list[dict]:
    """Check SCAO court forms for version updates.

    Queries court_forms.db for current forms, fetches SCAO website,
    and flags forms that may be outdated.

    Returns list of dicts for forms with potential updates.
    """
    if verbose:
        print("=== Checking SCAO Form Versions ===\n")

    if not os.path.exists(COURT_FORMS_DB):
        if verbose:
            print(f"ERROR: court_forms.db not found at {COURT_FORMS_DB}")
        return []

    # Get current forms from our DB
    forms_conn = sqlite3.connect(COURT_FORMS_DB)
    forms_conn.row_factory = sqlite3.Row
    forms = forms_conn.execute(
        """SELECT form_number, form_name, url, last_verified
           FROM court_forms
           ORDER BY form_number"""
    ).fetchall()
    forms_conn.close()

    if verbose:
        print(f"Found {len(forms)} forms in court_forms.db")

    # Fetch SCAO page for comparison
    scao_html = _fetch_page(SCAO_FORMS_URL)
    scao_text = re.sub(r"<[^>]+>", " ", scao_html).lower() if scao_html else ""

    results = []
    now_str = datetime.datetime.now().strftime("%Y-%m-%d")
    stale_cutoff = (
        datetime.datetime.now() - datetime.timedelta(days=180)
    ).strftime("%Y-%m-%d")

    for form in forms:
        form_num = form["form_number"] or ""
        form_name = form["form_name"] or ""
        last_verified = form["last_verified"] or ""
        status = "current"
        notes = []

        # Check 1: Is the form referenced on the SCAO page?
        if scao_text and form_num.lower() not in scao_text:
            # Form number not found — might have been replaced
            status = "check_needed"
            notes.append("Form number not found on SCAO page — may be superseded")

        # Check 2: Stale verification date (>180 days)
        if not last_verified or last_verified < stale_cutoff:
            if status == "current":
                status = "stale"
            notes.append(
                f"Last verified: {last_verified or 'never'} (>180 days)"
            )

        # Check 3: URL reachability (lightweight HEAD check)
        form_url = form["url"] or ""
        if form_url and HAS_URLLIB:
            try:
                req = urllib.request.Request(
                    form_url, method="HEAD",
                    headers={"User-Agent": "LitigationOS/2.0 FormChecker"},
                )
                with urllib.request.urlopen(req, timeout=10) as resp:
                    if resp.status >= 400:
                        status = "broken_url"
                        notes.append(f"URL returned HTTP {resp.status}")
            except (urllib.error.URLError, OSError, TimeoutError):
                status = "unreachable"
                notes.append("Form URL unreachable — may have moved")

        result = {
            "form_number": form_num,
            "form_name": form_name,
            "url": form_url,
            "last_verified": last_verified,
            "status": status,
            "notes": "; ".join(notes) if notes else "OK",
            "checked_date": now_str,
        }
        results.append(result)

    # Summary
    flagged = [r for r in results if r["status"] != "current"]
    if verbose:
        if flagged:
            print(f"\n⚠ {len(flagged)} forms need attention:\n")
            for r in flagged:
                icon = {"stale": "🟡", "check_needed": "🔴",
                        "broken_url": "🔴", "unreachable": "🟠"}.get(
                    r["status"], "❓"
                )
                print(f"  {icon} {r['form_number']:<15} {r['status']:<15} {r['notes']}")
        else:
            print("\n✅ All forms appear current.")

        print(f"\n=== Done: {len(results)} forms checked, {len(flagged)} flagged ===")

    return results


# ─── Feature 4: Citation Chain Updater ────────────────────────────────────────

def _ensure_citation_freshness_table(conn):
    """Create or recreate the citation_freshness table."""
    conn.execute("DROP TABLE IF EXISTS citation_freshness")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS citation_freshness (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            authority_id TEXT,
            citation TEXT,
            status TEXT DEFAULT 'current',
            checked_date TEXT,
            notes TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        )
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_citation_freshness_status
        ON citation_freshness(status)
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_citation_freshness_authority
        ON citation_freshness(authority_id)
    """)
    conn.commit()


MICHIGAN_CASELAW_SEARCH = "https://courts.michigan.gov/opinions-orders/search"


def update_citations(verbose: bool = True) -> dict:
    """Check if authorities in authority_master_index are still good law.

    Queries authority_master_index for citations, performs basic freshness
    checks (pattern matching for overruled/modified indicators, date-based
    staleness), and stores results in citation_freshness table.

    Returns dict with counts: {current, modified, overruled, superseded, unknown}.
    """
    conn = get_db()
    _ensure_citation_freshness_table(conn)

    if verbose:
        print("=== Updating Citation Freshness ===\n")

    # Get all authorities
    authorities = conn.execute(
        """SELECT id, authority_type, identifier, title, full_text, category, lanes
           FROM authority_master_index
           ORDER BY id"""
    ).fetchall()

    if not authorities:
        if verbose:
            print("No authorities found in authority_master_index.")
        conn.close()
        return {"current": 0, "modified": 0, "overruled": 0, "superseded": 0, "unknown": 0}

    if verbose:
        print(f"Checking {len(authorities)} authorities...\n")

    counts = {"current": 0, "modified": 0, "overruled": 0, "superseded": 0, "unknown": 0}
    now_str = datetime.datetime.now().strftime("%Y-%m-%d")

    for auth in authorities:
        auth_id = str(auth["id"])
        identifier = auth["identifier"] or ""
        title = auth["title"] or ""
        full_text = auth["full_text"] or ""
        combined = f"{identifier} {title} {full_text}".lower()

        status = "current"
        notes_parts = []

        # Check 1: Overruled indicators in the text itself
        overruled_patterns = [
            r"overruled\s+by", r"overruled\s+in", r"no longer\s+good\s+law",
            r"abrogated\s+by", r"reversed\s+by",
        ]
        for pat in overruled_patterns:
            if re.search(pat, combined):
                status = "overruled"
                notes_parts.append(f"Text contains overruled indicator: {pat}")
                break

        # Check 2: Modified/superseded indicators
        if status == "current":
            modified_patterns = [
                r"modified\s+by", r"amended\s+by", r"distinguished\s+in",
                r"limited\s+by", r"clarified\s+in",
            ]
            for pat in modified_patterns:
                if re.search(pat, combined):
                    status = "modified"
                    notes_parts.append(f"Text contains modification indicator: {pat}")
                    break

        # Check 3: Superseded indicators
        if status == "current":
            superseded_patterns = [
                r"superseded\s+by", r"replaced\s+by", r"repealed",
            ]
            for pat in superseded_patterns:
                if re.search(pat, combined):
                    status = "superseded"
                    notes_parts.append(f"Text contains superseded indicator: {pat}")
                    break

        # Check 4: Statute vs case law freshness heuristic
        if status == "current":
            # MCL references — check for recent amendments mentioned
            if re.search(r"MCL\s+\d+\.\d+", identifier):
                notes_parts.append("Statute — verify current version on legislature.mi.gov")
            # MCR references — check against our tracked rules
            elif re.search(r"MCR\s+\d+\.\d+", identifier):
                rule_changes = conn.execute(
                    "SELECT COUNT(*) FROM rule_changes WHERE rule_number LIKE ?",
                    (f"%{identifier}%",),
                ).fetchone()
                if rule_changes and rule_changes[0] > 0:
                    status = "modified"
                    notes_parts.append(
                        f"Rule has {rule_changes[0]} recorded change(s) in rule_changes table"
                    )

        if not notes_parts:
            notes_parts.append("No negative indicators found — presumed current")

        counts[status] += 1

        conn.execute(
            """INSERT INTO citation_freshness
               (authority_id, citation, status, checked_date, notes)
               VALUES (?, ?, ?, ?, ?)""",
            (auth_id, identifier, status, now_str, "; ".join(notes_parts)),
        )

    conn.commit()

    if verbose:
        print(f"  Current:    {counts['current']}")
        print(f"  Modified:   {counts['modified']}")
        print(f"  Overruled:  {counts['overruled']}")
        print(f"  Superseded: {counts['superseded']}")
        print(f"  Unknown:    {counts['unknown']}")

        # Show flagged citations
        flagged = conn.execute(
            """SELECT citation, status, notes
               FROM citation_freshness
               WHERE status != 'current'
               ORDER BY status, citation
               LIMIT 30"""
        ).fetchall()

        if flagged:
            print(f"\n--- Flagged Citations ({len(flagged)}) ---")
            for f in flagged:
                icon = {"overruled": "🔴", "modified": "🟡", "superseded": "🟠"}.get(
                    f["status"], "❓"
                )
                print(f"  {icon} [{f['status']:<11}] {f['citation']:<30} {f['notes'][:60]}")

    conn.close()
    if verbose:
        print(f"\n=== Done: {sum(counts.values())} citations checked ===")
    return counts


# ─── Feature 5: Weekly Digest Generator ───────────────────────────────────────

def generate_digest(days: int = 7, verbose: bool = True) -> str:
    """Generate a weekly legal digest in Markdown.

    Compiles feed entries, rule changes, and citation updates from the past
    N days, grouped by relevance tier (high/medium/low).

    Writes to 05_REPORTS/WEEKLY_LEGAL_DIGEST.md and returns the path.
    """
    conn = get_db()
    now = datetime.datetime.now(datetime.timezone.utc)
    cutoff = (now - datetime.timedelta(days=days)).isoformat()
    date_str = now.strftime("%Y-%m-%d")

    if verbose:
        print(f"=== Generating Legal Digest (last {days} days) ===\n")

    # Section 1: Feed entries grouped by relevance
    entries = conn.execute(
        """SELECT e.*, s.source_name
           FROM court_feed_entries e
           JOIN court_feed_sources s ON e.source_id = s.id
           WHERE e.created_at >= ?
           ORDER BY e.relevance_score DESC, e.created_at DESC
           LIMIT 200""",
        (cutoff,),
    ).fetchall()

    high = [e for e in entries if e["relevance_score"] >= 5.0]
    medium = [e for e in entries if 2.0 <= e["relevance_score"] < 5.0]
    low = [e for e in entries if e["relevance_score"] < 2.0]

    # Section 2: Rule changes
    rule_changes = conn.execute(
        """SELECT * FROM rule_changes
           WHERE created_at >= ?
           ORDER BY created_at DESC""",
        (cutoff,),
    ).fetchall()

    # Section 3: Citation freshness (if checked recently)
    citation_flags = conn.execute(
        """SELECT * FROM citation_freshness
           WHERE status != 'current' AND checked_date >= ?
           ORDER BY status, citation""",
        ((now - datetime.timedelta(days=days)).strftime("%Y-%m-%d"),),
    ).fetchall()

    # Section 4: Form checks (run inline)
    form_results = check_form_versions(verbose=False)
    flagged_forms = [f for f in form_results if f["status"] != "current"]

    # Build markdown
    lines = [
        f"# Weekly Legal Digest — {date_str}",
        f"",
        f"> Auto-generated by LitigationOS Court Feed Scraper",
        f"> Period: {days} days ending {date_str}",
        f"> Case: Pigors v. Watson (2024-001507-DC)",
        f"",
        f"## Summary",
        f"",
        f"| Category | Count |",
        f"|----------|-------|",
        f"| High-relevance entries | {len(high)} |",
        f"| Medium-relevance entries | {len(medium)} |",
        f"| Low-relevance entries | {len(low)} |",
        f"| Rule changes | {len(rule_changes)} |",
        f"| Flagged citations | {len(citation_flags)} |",
        f"| Flagged forms | {len(flagged_forms)} |",
        f"",
    ]

    # High relevance
    lines.append("## 🔴 High Relevance Entries\n")
    if high:
        for e in high[:20]:
            lines.append(f"### [{e['relevance_score']:.1f}] {e['title']}")
            lines.append(f"- **Source:** {e['source_name']}")
            lines.append(f"- **Date:** {e['published_date'] or 'N/A'}")
            if e["case_number"]:
                lines.append(f"- **Case:** {e['case_number']}")
            if e["tags"]:
                lines.append(f"- **Tags:** {e['tags']}")
            if e["url"]:
                lines.append(f"- **URL:** {e['url']}")
            if e["content"]:
                lines.append(f"- {e['content'][:300]}")
            lines.append("")
    else:
        lines.append("_No high-relevance entries this period._\n")

    # Medium relevance
    lines.append("## 🟡 Medium Relevance Entries\n")
    if medium:
        for e in medium[:15]:
            lines.append(
                f"- **[{e['relevance_score']:.1f}]** {e['title'][:80]} "
                f"— {e['source_name']} ({e['published_date'] or 'N/A'})"
            )
        lines.append("")
    else:
        lines.append("_No medium-relevance entries this period._\n")

    # Low relevance (condensed)
    lines.append("## 🟢 Low Relevance Entries\n")
    if low:
        lines.append(f"_{len(low)} low-relevance entries. Top 10:_\n")
        for e in low[:10]:
            lines.append(f"- [{e['relevance_score']:.1f}] {e['title'][:80]}")
        lines.append("")
    else:
        lines.append("_No low-relevance entries this period._\n")

    # Rule changes section
    lines.append("## ⚖️ Rule Changes\n")
    if rule_changes:
        for rc in rule_changes:
            flag = "⚠️" if rc["rule_number"] in TRACKED_RULES else "📋"
            lines.append(
                f"- {flag} **{rc['rule_number']}** ({rc['change_type']}) "
                f"— {rc['description'][:100]}"
            )
            if rc["impact_assessment"]:
                lines.append(f"  - Impact: {rc['impact_assessment']}")
        lines.append("")
    else:
        lines.append("_No rule changes this period._\n")

    # Citation freshness section
    lines.append("## 📚 Citation Freshness Flags\n")
    if citation_flags:
        lines.append("| Citation | Status | Notes |")
        lines.append("|----------|--------|-------|")
        for cf in citation_flags[:20]:
            lines.append(
                f"| {cf['citation']} | {cf['status']} | {cf['notes'][:60]} |"
            )
        lines.append("")
    else:
        lines.append("_No citation issues flagged this period._\n")

    # Form updates section
    lines.append("## 📋 Form Version Status\n")
    if flagged_forms:
        lines.append("| Form | Status | Notes |")
        lines.append("|------|--------|-------|")
        for ff in flagged_forms:
            lines.append(
                f"| {ff['form_number']} | {ff['status']} | {ff['notes'][:60]} |"
            )
        lines.append("")
    else:
        lines.append("_All forms appear current._\n")

    # Footer
    lines.extend([
        "---",
        f"_Generated: {now.isoformat()} by court_feed_scraper.py_",
        f"_Database: {DB_PATH}_",
    ])

    content = "\n".join(lines)

    # Write to file
    os.makedirs(REPORTS_DIR, exist_ok=True)
    output_path = os.path.join(REPORTS_DIR, "WEEKLY_LEGAL_DIGEST.md")
    with open(output_path, "w", encoding="utf-8") as fh:
        fh.write(content)

    conn.close()

    if verbose:
        print(f"Digest written to: {output_path}")
        print(f"  High:   {len(high)} entries")
        print(f"  Medium: {len(medium)} entries")
        print(f"  Low:    {len(low)} entries")
        print(f"  Rules:  {len(rule_changes)} changes")
        print(f"  Citations: {len(citation_flags)} flagged")
        print(f"  Forms:  {len(flagged_forms)} flagged")
        print(f"\n=== Digest complete ===")

    return output_path


def main():
    sys.stdout = open(sys.stdout.fileno(), mode="w", encoding="utf-8", errors="replace")

    parser = argparse.ArgumentParser(
        description="LitigationOS Court Feed Scraper — check Michigan court feeds",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --check                  Check all active feeds for new entries
  %(prog)s --recent --days 14       Show recent entries from last 14 days
  %(prog)s --track-rules            Track MCR rule amendments
  %(prog)s --score-opinion "text"   Score opinion text for case relevance
  %(prog)s --check-forms            Check SCAO form versions for updates
  %(prog)s --update-citations       Check citation freshness in authority_master_index
  %(prog)s --digest                 Generate weekly legal digest (7 days)
  %(prog)s --digest --days 30       Generate digest for last 30 days
"""
    )
    parser.add_argument("--check", action="store_true", help="Check all active feeds for new entries")
    parser.add_argument("--recent", action="store_true", help="Show recent entries")
    parser.add_argument("--sources", action="store_true", help="List configured sources")
    parser.add_argument("--track-rules", action="store_true", help="Track MCR rule amendments from courts.michigan.gov")
    parser.add_argument("--score-opinion", type=str, metavar="TEXT", help="Score opinion/case text for relevance to case lanes")
    parser.add_argument("--check-forms", action="store_true", help="Check SCAO court form versions for updates")
    parser.add_argument("--update-citations", action="store_true", help="Check citation freshness in authority_master_index")
    parser.add_argument("--digest", action="store_true", help="Generate weekly legal digest markdown report")
    parser.add_argument("--days", type=int, default=7, help="Number of days to look back (default: 7)")
    parser.add_argument("--min-relevance", type=float, default=0.0, help="Minimum relevance score filter")
    args = parser.parse_args()

    if not os.path.exists(DB_PATH):
        print(f"ERROR: Database not found at {DB_PATH}")
        print("Run temp_court_feed.py first to create tables and seed sources.")
        sys.exit(1)

    if args.sources:
        list_sources()
        return

    if args.track_rules:
        track_rule_changes(verbose=True)
        return

    if args.score_opinion:
        result = score_opinion(args.score_opinion)
        print(f"=== Opinion Relevance Score ===\n")
        print(f"Overall Score: {result['score']}/100  (Tier: {result['tier'].upper()})")
        print(f"\nMatched Lanes:")
        if result["matched_lanes"]:
            for lane in result["matched_lanes"]:
                print(f"  Lane {lane['lane']} ({lane['lane_name']}): {lane['score']}/100")
                if lane["matched_keywords"]:
                    kws = ", ".join(
                        f"{k['keyword']}({k['count']}×{k['weight']})"
                        for k in lane["matched_keywords"][:5]
                    )
                    print(f"    Keywords: {kws}")
        else:
            print("  No lane matches found.")
        return

    if args.check_forms:
        check_form_versions(verbose=True)
        return

    if args.update_citations:
        update_citations(verbose=True)
        return

    if args.digest:
        generate_digest(days=args.days, verbose=True)
        return

    if args.check:
        print("=== Checking Court Feeds ===\n")
        new = check_feeds(verbose=True)
        print(f"\n=== Done: {new} new entries ingested ===")

        if args.days:
            entries = get_recent(days=args.days, min_relevance=args.min_relevance)
            if entries:
                print(f"\n--- Recent entries (last {args.days} days) ---")
                for e in entries[:20]:
                    score_bar = "*" * int(e["relevance_score"])
                    print(f"  [{e['relevance_score']:>5.1f}] {score_bar:<10} {e['title'][:70]}")
                    if e.get("case_number"):
                        print(f"         Case: {e['case_number']}")
            else:
                print(f"\nNo entries in the last {args.days} days.")
        return

    if args.recent:
        entries = get_recent(days=args.days, min_relevance=args.min_relevance)
        if entries:
            print(f"=== Recent Court Feed Entries (last {args.days} days) ===\n")
            for e in entries[:30]:
                print(f"  [{e['relevance_score']:>5.1f}]  {e['title'][:70]}")
                print(f"           Source: {e.get('source_name', '?')}  |  {e.get('published_date', 'N/A')}")
                if e.get("tags"):
                    print(f"           Tags: {e['tags']}")
                print()
            print(f"Total: {len(entries)} entries")
        else:
            print(f"No entries in the last {args.days} days with relevance >= {args.min_relevance}.")
        return

    # Default: show help
    parser.print_help()


if __name__ == "__main__":
    main()
