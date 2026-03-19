#!/usr/bin/env python3
"""
MBP LitigationOS 2026 — Impeachment Brief Generator
=====================================================
Engine for generating cross-examination outlines, impeachment briefs,
and credibility-attack packages from the litigation_context.db.

Pigors v. Watson | Consolidated Case Matrix
"""

import sqlite3
import json
import re
from collections import defaultdict, Counter
from datetime import datetime


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

DEFAULT_DB_PATH = r"C:\Users\andre\LitigationOS\litigation_context.db"

SEVERITY_RANK = {"CRITICAL": 3, "HIGH": 2, "MEDIUM": 1}

ITEM_TYPE_RANK = {
    "TESTIMONY_VS_DOCUMENT": 5,
    "CROSS_SPEAKER_CONTRADICTION": 4,
    "PRIOR_INCONSISTENT_STATEMENT": 3,
    "TIMELINE_CONTRADICTION": 2,
    "TIMELINE_SEQUENCE_ANOMALY": 2,
    "CREDIBILITY_FORENSIC": 3,
    "JUDICIAL_BENCHBOOK_DEVIATION": 4,
    "BENCHBOOK_VIOLATION": 4,
    "JUDICIAL_PPO_WEAPONIZATION": 4,
    "JUDICIAL_EX_PARTE_VIOLATION": 5,
    "JUDICIAL_PROCEDURAL_MISCONDUCT": 4,
    "JUDICIAL_DUE_PROCESS_VIOLATION": 5,
    "JUDICIAL_MCJC_CANON_VIOLATION": 4,
    "JUDICIAL_MCR_2003_DISQUALIFICATION": 5,
    "JUDICIAL_CREDIBILITY_FAILURE": 3,
}

# MCL 722.23 Best Interest Factors (a)-(l) keyword mapping
BIF_KEYWORDS = {
    "a": ["love", "affection", "emotional ties", "bond"],
    "b": ["capacity", "provide", "food", "clothing", "medical", "needs"],
    "c": ["permanence", "stability", "family unit", "custodial environment"],
    "d": ["moral fitness", "moral", "fitness"],
    "e": ["mental health", "physical health", "health"],
    "f": ["school", "education", "community", "school record"],
    "g": ["preference", "child's preference", "reasonable preference"],
    "h": ["domestic violence", "violence", "abuse"],
    "i": ["facilitate", "relationship", "parent-child", "willingness"],
    "j": ["alienation", "alienate", "disparage", "undermine", "factor j"],
    "k": ["domestic violence history", "threat", "coercion"],
    "l": ["other factor", "relevant factor"],
}

MRE_IMPEACHMENT_RULES = {
    "607": "MRE 607 — Who May Impeach a Witness",
    "608": "MRE 608 — Character for Truthfulness",
    "609": "MRE 609 — Impeachment by Criminal Conviction",
    "613": "MRE 613 — Prior Inconsistent Statements",
    "801": "MRE 801(d)(1) — Prior Statement by Witness",
}


# ---------------------------------------------------------------------------
# ImpeachmentGenerator
# ---------------------------------------------------------------------------

class ImpeachmentGenerator:
    """Generates cross-examination outlines and impeachment briefs from DB."""

    def __init__(self, db_path: str = DEFAULT_DB_PATH):
        self.db_path = db_path
        self._conn = None

    # -- connection management ------------------------------------------------

    def _get_conn(self) -> sqlite3.Connection:
        """Return a live connection, reconnecting with retry if needed."""
        if self._conn is not None:
            try:
                self._conn.execute("SELECT 1")
                return self._conn
            except Exception:
                self._conn = None

        last_err = None
        for attempt in range(3):
            try:
                conn = sqlite3.connect(self.db_path, timeout=10)
                conn.row_factory = sqlite3.Row
                conn.execute("PRAGMA journal_mode=WAL")
                self._conn = conn
                return self._conn
            except Exception as exc:
                last_err = exc
                import time
                time.sleep(2 ** attempt)
        raise ConnectionError(
            f"Failed to connect to {self.db_path} after 3 attempts: {last_err}"
        )

    def close(self):
        if self._conn:
            try:
                self._conn.close()
            except Exception:
                pass
            self._conn = None

    # -- low-level queries ----------------------------------------------------

    def _query(self, sql: str, params: tuple = ()) -> list:
        """Execute a parameterized query and return list of Row objects."""
        try:
            cur = self._get_conn().execute(sql, params)
            return cur.fetchall()
        except Exception as exc:
            # One retry with fresh connection
            self._conn = None
            try:
                cur = self._get_conn().execute(sql, params)
                return cur.fetchall()
            except Exception:
                print(f"[IMPEACH-ERR] Query failed: {exc}")
                return []

    def _fetch_impeachment_items(self, speaker: str) -> list:
        """Fetch all impeachment items for a speaker (case-insensitive)."""
        return self._query(
            """
            SELECT id, item_type, speaker, transcript_doc_id, transcript_page,
                   statement, contradicting_source, contradicting_doc_id,
                   contradicting_text, legal_hook, severity
            FROM impeachment_items
            WHERE LOWER(speaker) = LOWER(?)
            ORDER BY severity DESC, id
            """,
            (speaker,),
        )

    def _fetch_evidence_for_speaker(self, speaker: str, limit: int = 200) -> list:
        """Fetch supporting evidence quotes for a speaker."""
        return self._query(
            """
            SELECT id, evidence_category, quote_text, speaker,
                   legal_significance, source_type
            FROM evidence_quotes
            WHERE LOWER(speaker) = LOWER(?)
            LIMIT ?
            """,
            (speaker, limit),
        )

    def _fetch_mre_rule(self, rule_number: str) -> dict:
        """Fetch an MRE rule by number from auth_rules."""
        rows = self._query(
            """
            SELECT id, rule_number, title, full_text, summary
            FROM auth_rules
            WHERE rule_type = 'MRE' AND rule_number = ?
            """,
            (rule_number,),
        )
        if rows:
            r = rows[0]
            return {
                "id": r["id"],
                "rule_number": r["rule_number"],
                "title": r["title"],
                "full_text": r["full_text"],
                "summary": r["summary"],
            }
        return {}

    def _search_auth_rules_fts(self, query_text: str, limit: int = 5) -> list:
        """Full-text search against auth_rules_fts."""
        safe_q = re.sub(r"[^\w\s]", "", query_text)
        try:
            return self._query(
                """
                SELECT ar.id, ar.rule_number, ar.title, ar.summary
                FROM auth_rules_fts fts
                JOIN auth_rules ar ON fts.rowid = ar.rowid
                WHERE auth_rules_fts MATCH ?
                LIMIT ?
                """,
                (safe_q, limit),
            )
        except Exception:
            return []

    # -- scoring --------------------------------------------------------------

    @staticmethod
    def _score_item(row) -> float:
        """Score an impeachment item for strength/impact."""
        score = 0.0
        severity = row["severity"] or "MEDIUM"
        score += SEVERITY_RANK.get(severity, 1) * 10

        item_type = row["item_type"] or ""
        score += ITEM_TYPE_RANK.get(item_type, 1) * 5

        # Bonus for having contradicting source
        if row["contradicting_source"]:
            score += 5
        if row["contradicting_text"]:
            score += 3

        # Bonus if legal_hook references BIF
        hook = (row["legal_hook"] or "").lower()
        if "722.23" in hook or "best interest" in hook:
            score += 15

        # Bonus for MRE 613 (prior inconsistent) — strongest impeachment
        if "613" in hook:
            score += 8

        return score

    # -- BIF mapping ----------------------------------------------------------

    def map_to_bif_factors(self, items: list) -> dict:
        """Map impeachment items to MCL 722.23 best interest factors (a)-(l).

        Returns dict keyed by factor letter with list of matching item ids.
        """
        mapping = {letter: [] for letter in BIF_KEYWORDS}

        for item in items:
            text_blob = " ".join(
                str(item.get(k, "") or "")
                for k in ("statement", "contradicting_text", "legal_hook")
            ).lower()

            for letter, keywords in BIF_KEYWORDS.items():
                if any(kw in text_blob for kw in keywords):
                    item_id = item.get("id") or item.get("item_id")
                    mapping[letter].append(item_id)

        # Strip empty factors
        return {k: v for k, v in mapping.items() if v}

    # -- primary methods ------------------------------------------------------

    def get_speaker_stats(self) -> dict:
        """Return dict of all speakers with impeachment counts and breakdown."""
        rows = self._query(
            """
            SELECT speaker,
                   COUNT(*) AS total,
                   SUM(CASE WHEN severity = 'CRITICAL' THEN 1 ELSE 0 END) AS critical,
                   SUM(CASE WHEN severity = 'HIGH' THEN 1 ELSE 0 END) AS high,
                   SUM(CASE WHEN severity = 'MEDIUM' THEN 1 ELSE 0 END) AS medium
            FROM impeachment_items
            GROUP BY speaker
            ORDER BY COUNT(*) DESC
            """
        )
        stats = {}
        for r in rows:
            speaker = r["speaker"] or "(None)"
            items_sample = self._query(
                """
                SELECT id, item_type, severity, legal_hook
                FROM impeachment_items
                WHERE speaker IS ? AND severity = 'CRITICAL'
                ORDER BY id LIMIT 3
                """,
                (r["speaker"],),
            )
            stats[speaker] = {
                "total": r["total"],
                "critical": r["critical"],
                "high": r["high"],
                "medium": r["medium"],
                "top_items": [dict(i) for i in items_sample],
            }
        return stats

    def find_strongest_impeachment(self, speaker: str, top_n: int = 10) -> list:
        """Return the N strongest impeachment items for a speaker, scored."""
        items = self._fetch_impeachment_items(speaker)
        if not items:
            return []

        scored = []
        for row in items:
            score = self._score_item(row)
            d = dict(row)
            d["impeachment_score"] = score
            scored.append(d)

        scored.sort(key=lambda x: x["impeachment_score"], reverse=True)
        return scored[:top_n]

    def generate_cross_exam_outline(self, speaker: str) -> dict:
        """Generate a structured cross-examination outline for a speaker.

        Groups impeachment items by legal_hook, orders by severity,
        and attaches applicable MRE rules.
        """
        items = self._fetch_impeachment_items(speaker)
        if not items:
            return {"speaker": speaker, "total_items": 0, "groups": []}

        # Group by legal_hook
        groups = defaultdict(list)
        for row in items:
            hook = row["legal_hook"] or "Unclassified"
            groups[hook].append(dict(row))

        # Load MRE impeachment rules
        mre_rules = {}
        for rn in ("607", "608", "609", "613", "801"):
            rule_data = self._fetch_mre_rule(rn)
            if rule_data:
                mre_rules[rn] = rule_data

        # Build outline groups sorted by count (most contradictions first)
        outline_groups = []
        for hook, hook_items in sorted(
            groups.items(), key=lambda kv: len(kv[1]), reverse=True
        ):
            # Score each item
            for it in hook_items:
                it["impeachment_score"] = self._score_item(
                    type("R", (), {
                        "__getitem__": lambda s, k, _d=it: _d.get(k)
                    })()
                )
            hook_items.sort(key=lambda x: x["impeachment_score"], reverse=True)

            # Determine applicable MRE rules for this hook
            applicable_mre = []
            hook_lower = hook.lower()
            if "613" in hook_lower or "inconsistent" in hook_lower:
                applicable_mre.append("MRE 613 — Prior Inconsistent Statements")
            if "801" in hook_lower or "hearsay" in hook_lower:
                applicable_mre.append("MRE 801(d)(1) — Prior Statement by Witness")
            if "608" in hook_lower or "character" in hook_lower or "truthful" in hook_lower:
                applicable_mre.append("MRE 608 — Character for Truthfulness")
            if "609" in hook_lower or "conviction" in hook_lower:
                applicable_mre.append("MRE 609 — Impeachment by Criminal Conviction")
            # MRE 607 always applies — any party may impeach any witness
            if not applicable_mre:
                applicable_mre.append("MRE 607 — Who May Impeach a Witness")
            if "MRE 607 — Who May Impeach a Witness" not in applicable_mre:
                applicable_mre.insert(0, "MRE 607 — Who May Impeach a Witness")

            outline_groups.append({
                "legal_hook": hook,
                "item_count": len(hook_items),
                "applicable_mre": applicable_mre,
                "items": [
                    {
                        "id": it["id"],
                        "item_type": it["item_type"],
                        "severity": it["severity"],
                        "statement": (it["statement"] or "")[:500],
                        "contradicting_text": (it["contradicting_text"] or "")[:500],
                        "contradicting_source": it["contradicting_source"],
                        "score": it["impeachment_score"],
                    }
                    for it in hook_items[:20]  # cap per group for readability
                ],
            })

        return {
            "speaker": speaker,
            "generated_at": datetime.now().isoformat(),
            "total_items": len(items),
            "groups": outline_groups,
            "mre_rules_reference": {
                k: {"rule_number": v.get("rule_number"), "title": v.get("title")}
                for k, v in mre_rules.items()
            },
        }

    def generate_impeachment_brief_section(self, speaker: str) -> str:
        """Generate a court-ready IRAC impeachment brief section."""
        strongest = self.find_strongest_impeachment(speaker, top_n=15)
        if not strongest:
            return f"No impeachment items found for speaker: {speaker}"

        total_rows = self._query(
            "SELECT COUNT(*) AS cnt FROM impeachment_items WHERE LOWER(speaker)=LOWER(?)",
            (speaker,),
        )
        total_count = total_rows[0]["cnt"] if total_rows else 0

        critical_count = sum(1 for i in strongest if i.get("severity") == "CRITICAL")
        high_count = sum(1 for i in strongest if i.get("severity") == "HIGH")

        # Map to BIF factors
        bif_map = self.map_to_bif_factors(strongest)
        bif_str = ", ".join(
            f"Factor ({letter})" for letter in sorted(bif_map.keys())
        ) if bif_map else "multiple factors"

        # Fetch supporting evidence
        evidence = self._fetch_evidence_for_speaker(speaker, limit=10)

        lines = []
        lines.append("=" * 72)
        lines.append("IMPEACHMENT ANALYSIS — IRAC FORMAT")
        lines.append(f"Re: {speaker}")
        lines.append(f"Generated: {datetime.now().strftime('%B %d, %Y')}")
        lines.append("=" * 72)
        lines.append("")

        # ISSUE
        lines.append("I.  ISSUE")
        lines.append("-" * 40)
        lines.append(
            f"    Whether the testimony and representations of {speaker} are "
            f"credible, given {total_count} documented contradictions, "
            f"inconsistencies, and impeachable statements in the record."
        )
        lines.append("")

        # RULE
        lines.append("II. RULE")
        lines.append("-" * 40)
        lines.append(
            "    Under Michigan law, the credibility of a witness may be "
            "attacked by any party, including the party calling the witness. "
            "MRE 607."
        )
        lines.append("")
        lines.append(
            "    A witness who has made a prior statement inconsistent with "
            "their testimony may be impeached by extrinsic evidence of that "
            "statement. MRE 613(b)."
        )
        lines.append("")
        lines.append(
            "    A statement is not hearsay if the declarant testifies and is "
            "subject to cross-examination concerning the statement, and the "
            "statement is inconsistent with the declarant's testimony. "
            "MRE 801(d)(1)(A)."
        )
        lines.append("")
        lines.append(
            "    The court must evaluate the best interest of the child under "
            "the factors enumerated in MCL 722.23(a)-(l). The credibility of "
            "witnesses directly affects the court's findings on " + bif_str + "."
        )
        lines.append("")

        # APPLICATION
        lines.append("III. APPLICATION")
        lines.append("-" * 40)
        lines.append(
            f"    The record contains {total_count} impeachment items for "
            f"{speaker}, of which {critical_count} are CRITICAL severity "
            f"and {high_count} are HIGH severity. The strongest "
            f"contradictions are set forth below:"
        )
        lines.append("")

        for idx, item in enumerate(strongest, 1):
            lines.append(f"    {idx}. [{item.get('severity', 'N/A')}] "
                         f"({item.get('item_type', 'N/A')})")
            stmt = (item.get("statement") or "")[:300].replace("\n", " ").strip()
            lines.append(f"       STATEMENT: \"{stmt}\"")
            contra = (item.get("contradicting_text") or "")[:300].replace("\n", " ").strip()
            if contra:
                lines.append(f"       CONTRADICTED BY: \"{contra}\"")
            if item.get("contradicting_source"):
                lines.append(f"       SOURCE: {item['contradicting_source']}")
            if item.get("legal_hook"):
                lines.append(f"       LEGAL HOOK: {item['legal_hook']}")
            lines.append(f"       IMPEACHMENT SCORE: {item.get('impeachment_score', 0):.1f}")
            lines.append("")

        if evidence:
            lines.append("    Supporting Evidence Quotes:")
            for eq in evidence[:5]:
                qt = (eq["quote_text"] or "")[:200].replace("\n", " ").strip()
                lines.append(f"    - [{eq['evidence_category']}] \"{qt}\"")
            lines.append("")

        if bif_map:
            lines.append("    Best Interest Factor Mapping (MCL 722.23):")
            for letter in sorted(bif_map.keys()):
                count = len(bif_map[letter])
                lines.append(f"    - Factor ({letter}): {count} impeachment items")
            lines.append("")

        # CONCLUSION
        lines.append("IV. CONCLUSION")
        lines.append("-" * 40)
        if critical_count >= 3 or total_count >= 50:
            weight_recommendation = "no"
        else:
            weight_recommendation = "significantly reduced"
        lines.append(
            f"    Based on {total_count} documented contradictions — including "
            f"{critical_count} at CRITICAL severity — the testimony and "
            f"representations of {speaker} should be given {weight_recommendation} "
            f"weight by this Court. The pattern of inconsistency is pervasive "
            f"and directly undermines findings on {bif_str} under MCL 722.23."
        )
        lines.append("")
        lines.append(
            "    Respectfully submitted,\n"
            "    Andrew Pigors, Plaintiff (pro se)\n"
            f"    Date: {datetime.now().strftime('%B %d, %Y')}"
        )
        lines.append("")

        return "\n".join(lines)

    def export_impeachment_package(self, speaker: str, format: str = "dict") -> object:
        """Export complete impeachment package for a speaker.

        Args:
            speaker: Name of the speaker.
            format: 'dict' returns Python dict; 'json' returns JSON string;
                    'brief' returns the IRAC brief text.
        """
        outline = self.generate_cross_exam_outline(speaker)
        strongest = self.find_strongest_impeachment(speaker, top_n=15)
        bif_map = self.map_to_bif_factors(strongest)

        package = {
            "speaker": speaker,
            "generated_at": datetime.now().isoformat(),
            "cross_exam_outline": outline,
            "strongest_items": strongest,
            "bif_factor_mapping": bif_map,
            "speaker_stats": self.get_speaker_stats().get(speaker, {}),
        }

        if format == "json":
            return json.dumps(package, indent=2, default=str)
        elif format == "brief":
            return self.generate_impeachment_brief_section(speaker)
        return package


# ---------------------------------------------------------------------------
# Smoke test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("=" * 72)
    print("MBP LitigationOS — Impeachment Generator Smoke Test")
    print("=" * 72)
    print()

    gen = ImpeachmentGenerator()

    # 1. Speaker stats
    print("[1] Speaker Stats")
    print("-" * 50)
    try:
        stats = gen.get_speaker_stats()
        for speaker, info in stats.items():
            print(
                f"  {speaker:25s} | total={info['total']:5d} | "
                f"CRIT={info['critical']:4d} | HIGH={info['high']:5d} | "
                f"MED={info['medium']:4d}"
            )
    except Exception as exc:
        print(f"  [ERROR] {exc}")
    print()

    # 2. Strongest impeachment for Tiffany Watson
    print("[2] Top 5 Strongest — Tiffany Watson")
    print("-" * 50)
    try:
        top = gen.find_strongest_impeachment("Tiffany Watson", top_n=5)
        for item in top:
            stmt = (item.get("statement") or "")[:80].replace("\n", " ")
            print(
                f"  Score={item['impeachment_score']:5.1f} | "
                f"{item['severity']:8s} | {item['item_type']}"
            )
            print(f"    stmt: {stmt}...")
    except Exception as exc:
        print(f"  [ERROR] {exc}")
    print()

    # 3. Cross-exam outline summary for Judge McNeill
    print("[3] Cross-Exam Outline Summary — Judge McNeill")
    print("-" * 50)
    try:
        outline = gen.generate_cross_exam_outline("Judge McNeill")
        print(f"  Total items: {outline['total_items']}")
        print(f"  Groups: {len(outline['groups'])}")
        for g in outline["groups"][:5]:
            print(
                f"    [{g['item_count']:3d}] {g['legal_hook'][:60]}"
            )
            print(f"         MRE: {', '.join(g['applicable_mre'][:2])}")
    except Exception as exc:
        print(f"  [ERROR] {exc}")
    print()

    # 4. BIF mapping for Emily Watson
    print("[4] BIF Factor Mapping — Emily Watson")
    print("-" * 50)
    try:
        items = gen.find_strongest_impeachment("Emily Watson", top_n=20)
        bif = gen.map_to_bif_factors(items)
        for letter, ids in sorted(bif.items()):
            print(f"  Factor ({letter}): {len(ids)} items")
    except Exception as exc:
        print(f"  [ERROR] {exc}")
    print()

    # 5. Brief section excerpt for Tiffany Watson
    print("[5] IRAC Brief Excerpt — Tiffany Watson")
    print("-" * 50)
    try:
        brief = gen.generate_impeachment_brief_section("Tiffany Watson")
        # Print first 40 lines
        for line in brief.split("\n")[:40]:
            print(f"  {line}")
        print("  ... [truncated for smoke test]")
    except Exception as exc:
        print(f"  [ERROR] {exc}")
    print()

    gen.close()
    print("Smoke test complete.")
