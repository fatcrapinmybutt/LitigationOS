"""
MBP LitigationOS 2026 — Entity Resolution Engine
==================================================
Resolves entity mentions (names, aliases, roles) to canonical forms
across all litigation lanes. TF-IDF character n-gram fuzzy matching
with exact-match fast path. Zero external API calls.
"""

import sqlite3
import json
import os
import re
import time
import logging
import collections

try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False

logger = logging.getLogger("LitigationOS.EntityResolver")

_DIR = os.path.dirname(os.path.abspath(__file__))
_CACHE_DIR = os.path.join(_DIR, "cache")


class EntityResolver:
    """Resolves entity mentions to canonical names across the litigation record."""

    def __init__(self, db_path: str = r"C:\Users\andre\LitigationOS\litigation_context.db"):
        self.db_path = db_path
        self.canonical_map = self._build_canonical_map()
        # Reverse lookup: lowered alias -> canonical
        self._alias_to_canonical: dict[str, str] = {}
        for canonical, aliases in self.canonical_map.items():
            self._alias_to_canonical[canonical.lower()] = canonical
            for alias in aliases:
                self._alias_to_canonical[alias.lower()] = canonical
        # Sorted by length descending for greedy matching
        self._all_mentions_sorted = sorted(
            self._alias_to_canonical.keys(), key=len, reverse=True
        )
        # TF-IDF vectorizer for fuzzy matching (char 3-grams)
        self._vectorizer = None
        self._tfidf_matrix = None
        self._tfidf_labels: list[str] = []
        self._build_tfidf_index()
        # Entity occurrence index (lazy-loaded)
        self._entity_index: dict[str, list] | None = None
        self._index_path = os.path.join(_CACHE_DIR, "entity_index.json")
        logger.info(
            "EntityResolver initialized: %d canonical entities, %d aliases",
            len(self.canonical_map),
            len(self._alias_to_canonical),
        )

    # ------------------------------------------------------------------
    # Canonical entity map
    # ------------------------------------------------------------------
    def _build_canonical_map(self) -> dict[str, list[str]]:
        """Returns dict of canonical entity -> known aliases."""
        return {
            # --- Parties ---
            "Andrew Pigors": [
                "Andrew", "Pigors", "Plaintiff", "Appellant", "Father",
                "Dad", "Mr. Pigors", "Andrew M. Pigors", "Andrew Pigors",
                "Plaintiff-Appellant", "Plaintiff/Appellant",
            ],
            "Tiffany Watson": [
                "Watson", "Tiffany", "Defendant", "Appellee", "Mother",
                "Mom", "Tiffany Pigors", "Ms. Watson", "Tiffany M. Watson",
                "Defendant-Appellee", "Defendant/Appellee",
                "Tiffany M. Pigors",
            ],
            # --- Judges ---
            "Judge McNeill": [
                "McNeill", "Hon. Jenny L. McNeill", "Judge Jenny McNeill",
                "the Court", "Her Honor", "Jenny McNeill", "Hon. McNeill",
                "Judge Jenny L. McNeill", "J. McNeill",
            ],
            # --- GAL / Professionals ---
            "Emily Watson": [
                "Emily", "Emily Watson", "GAL", "Guardian ad Litem",
                "guardian", "the Guardian",
            ],
            # --- FOC ---
            "Friend of the Court": [
                "FOC", "Friend of Court", "friend of the court",
                "Friend of the Court Office", "FOC Office",
                "FOC Referee", "FOC referee",
            ],
            # --- Courts ---
            "Michigan Court of Appeals": [
                "COA", "Court of Appeals", "appellate court",
                "Michigan COA", "MCOA",
            ],
            "Michigan Supreme Court": [
                "MSC", "Supreme Court", "MI Supreme Court",
            ],
            "14th Circuit Court": [
                "circuit court", "trial court", "lower court",
                "14th Circuit", "Muskegon County Circuit Court",
                "14th Circuit Court, Muskegon County",
            ],
            "US District Court Western Michigan": [
                "USDC", "federal court", "Western District",
                "USDC Western District", "W.D. Mich.",
            ],
            # --- Attorneys ---
            "Tiffany Watson Attorney": [
                "opposing counsel", "defense counsel",
                "Defendant's attorney", "Watson's attorney",
            ],
            # --- State Agencies ---
            "DHHS": [
                "Department of Health and Human Services",
                "Michigan DHHS", "MDHHS", "CPS",
                "Child Protective Services",
            ],
            "SCAO": [
                "State Court Administrative Office",
                "State Court Admin Office",
            ],
            "Judicial Tenure Commission": [
                "JTC", "Tenure Commission",
                "Michigan Judicial Tenure Commission",
            ],
            # --- Children ---
            "Minor Child A": [
                "the child", "the minor child", "the children",
                "minor child", "Child A",
            ],
            # --- Law Enforcement ---
            "Muskegon County Sheriff": [
                "Sheriff", "Sheriff's Office",
                "Muskegon Sheriff", "MCSO",
            ],
            "Muskegon Police": [
                "MPD", "Muskegon Police Department",
                "police", "law enforcement",
            ],
            # --- Housing ---
            "Shady Oaks": [
                "Shady Oaks Apartments", "Shady Oaks Housing",
                "Shady Oaks management", "the landlord",
            ],
            # --- Custody Evaluator ---
            "Custody Evaluator": [
                "evaluator", "custody evaluation",
                "the evaluator", "psych eval",
            ],
            # --- Mediator ---
            "Mediator": [
                "mediator", "mediation", "the mediator",
            ],
            # --- Court Reporter ---
            "Court Reporter": [
                "court reporter", "reporter", "transcript reporter",
            ],
            # --- Court Clerk ---
            "Muskegon County Clerk": [
                "county clerk", "clerk of court",
                "Clerk's Office", "the clerk",
            ],
            # --- Prosecutor ---
            "Muskegon County Prosecutor": [
                "prosecutor", "PA", "prosecuting attorney",
                "Muskegon Prosecutor",
            ],
            # --- Case Lanes ---
            "Lane A Watson Custody": [
                "Lane A", "custody case", "2024-001507-DC",
            ],
            "Lane D PPO": [
                "Lane D", "PPO case", "2023-5907-PP",
                "protection order case",
            ],
            "Lane F Appellate": [
                "Lane F", "COA 366810", "appeal case",
                "appellate case", "Docket 366810",
            ],
        }

    # ------------------------------------------------------------------
    # TF-IDF fuzzy matching index
    # ------------------------------------------------------------------
    def _build_tfidf_index(self) -> None:
        """Build TF-IDF character 3-gram index over all known entity names."""
        if not HAS_SKLEARN:
            logger.warning("sklearn not available — fuzzy matching disabled")
            return
        all_names: list[str] = []
        labels: list[str] = []
        for canonical, aliases in self.canonical_map.items():
            for name in [canonical] + aliases:
                all_names.append(name.lower())
                labels.append(canonical)
        self._vectorizer = TfidfVectorizer(
            analyzer="char", ngram_range=(3, 3)
        )
        self._tfidf_matrix = self._vectorizer.fit_transform(all_names)
        self._tfidf_labels = labels

    def _fuzzy_resolve(self, mention: str, threshold: float = 0.35) -> tuple[str, float]:
        """Resolve via TF-IDF cosine similarity. Returns (canonical, score)."""
        if not HAS_SKLEARN or self._vectorizer is None:
            return ("", 0.0)
        vec = self._vectorizer.transform([mention.lower()])
        scores = cosine_similarity(vec, self._tfidf_matrix).flatten()
        best_idx = scores.argmax()
        best_score = float(scores[best_idx])
        if best_score >= threshold:
            return (self._tfidf_labels[best_idx], best_score)
        return ("", 0.0)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def resolve(self, text: str) -> list[dict]:
        """Find all entity mentions in text. Returns list of match dicts."""
        results: list[dict] = []
        text_lower = text.lower()
        seen_spans: list[tuple[int, int]] = []

        for alias in self._all_mentions_sorted:
            # Skip very short aliases that cause false positives
            if len(alias) <= 2:
                continue
            pattern = re.compile(r"\b" + re.escape(alias) + r"\b", re.IGNORECASE)
            for m in pattern.finditer(text):
                start, end = m.start(), m.end()
                # Skip if overlapping with an already-matched span
                if any(s <= start < e or s < end <= e for s, e in seen_spans):
                    continue
                seen_spans.append((start, end))
                canonical = self._alias_to_canonical[alias]
                results.append({
                    "mention": m.group(),
                    "canonical": canonical,
                    "start": start,
                    "end": end,
                    "confidence": 1.0,
                })
        # Sort by position
        results.sort(key=lambda r: r["start"])
        return results

    def resolve_entity(self, mention: str) -> str:
        """Resolve a single mention to canonical form (exact then fuzzy)."""
        # Exact match
        key = mention.lower().strip()
        if key in self._alias_to_canonical:
            return self._alias_to_canonical[key]
        # Fuzzy match
        canonical, score = self._fuzzy_resolve(mention)
        if canonical:
            return canonical
        return mention  # return as-is if unresolvable

    def get_entity_profile(self, canonical_name: str) -> dict:
        """Query DB for all information about an entity."""
        profile: dict = {
            "canonical_name": canonical_name,
            "aliases": self.canonical_map.get(canonical_name, []),
            "evidence_quotes": [],
            "docket_events": [],
            "vehicles": [],
            "impeachment_items": [],
            "judicial_violations": [],
            "claims": [],
        }
        aliases = [canonical_name] + self.canonical_map.get(canonical_name, [])
        like_clauses = " OR ".join(
            "quote_text LIKE ?" for _ in aliases
        )
        params = [f"%{a}%" for a in aliases]

        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()

            # Evidence quotes
            try:
                cur.execute(
                    f"SELECT quote_text, speaker, legal_significance, evidence_category "
                    f"FROM evidence_quotes WHERE {like_clauses} LIMIT 50",
                    params,
                )
                profile["evidence_quotes"] = [dict(r) for r in cur.fetchall()]
            except Exception:
                pass

            # Docket events
            docket_like = " OR ".join("summary LIKE ?" for _ in aliases)
            try:
                cur.execute(
                    f"SELECT event_date_iso, title, event_type, summary "
                    f"FROM docket_events WHERE {docket_like} LIMIT 50",
                    [f"%{a}%" for a in aliases],
                )
                profile["docket_events"] = [dict(r) for r in cur.fetchall()]
            except Exception:
                pass

            # Vehicles
            vehicle_like = " OR ".join("title LIKE ?" for _ in aliases)
            try:
                cur.execute(
                    f"SELECT case_lane, title, forum, vehicle_type, status "
                    f"FROM vehicles WHERE {vehicle_like} LIMIT 50",
                    [f"%{a}%" for a in aliases],
                )
                profile["vehicles"] = [dict(r) for r in cur.fetchall()]
            except Exception:
                pass

            # Impeachment items
            imp_like = " OR ".join("speaker LIKE ? OR statement LIKE ?" for _ in aliases)
            try:
                cur.execute(
                    f"SELECT speaker, statement, contradicting_text, legal_hook "
                    f"FROM impeachment_items WHERE {imp_like} LIMIT 50",
                    [p for a in aliases for p in (f"%{a}%", f"%{a}%")],
                )
                profile["impeachment_items"] = [dict(r) for r in cur.fetchall()]
            except Exception:
                pass

            # Judicial violations (if entity is a judge)
            jv_like = " OR ".join("judge_name LIKE ?" for _ in aliases)
            try:
                cur.execute(
                    f"SELECT judge_name, canon_number, violation_description, severity "
                    f"FROM judicial_violations WHERE {jv_like} LIMIT 50",
                    [f"%{a}%" for a in aliases],
                )
                profile["judicial_violations"] = [dict(r) for r in cur.fetchall()]
            except Exception:
                pass

            # Claims
            claims_like = " OR ".join("proposition LIKE ?" for _ in aliases)
            try:
                cur.execute(
                    f"SELECT classification, actor, proposition, status "
                    f"FROM claims WHERE {claims_like} LIMIT 50",
                    [f"%{a}%" for a in aliases],
                )
                profile["claims"] = [dict(r) for r in cur.fetchall()]
            except Exception:
                pass

            conn.close()
        except Exception as exc:
            logger.error("DB error in get_entity_profile: %s", exc)

        return profile

    def find_cooccurrences(
        self, entity_a: str, entity_b: str, limit: int = 50
    ) -> list:
        """Find documents/quotes where both entities appear together."""
        results: list[dict] = []
        aliases_a = [entity_a] + self.canonical_map.get(entity_a, [])
        aliases_b = [entity_b] + self.canonical_map.get(entity_b, [])

        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()

            # Search evidence_quotes
            for aa in aliases_a:
                for ab in aliases_b:
                    try:
                        cur.execute(
                            "SELECT quote_text, speaker, legal_significance "
                            "FROM evidence_quotes "
                            "WHERE quote_text LIKE ? AND quote_text LIKE ? "
                            "LIMIT ?",
                            (f"%{aa}%", f"%{ab}%", limit),
                        )
                        for row in cur.fetchall():
                            entry = dict(row)
                            entry["source"] = "evidence_quotes"
                            if entry not in results:
                                results.append(entry)
                    except Exception:
                        pass
                    if len(results) >= limit:
                        break
                if len(results) >= limit:
                    break

            # Search md_sections
            if len(results) < limit:
                for aa in aliases_a[:3]:
                    for ab in aliases_b[:3]:
                        try:
                            cur.execute(
                                "SELECT section_title, content, source_file "
                                "FROM md_sections "
                                "WHERE content LIKE ? AND content LIKE ? "
                                "LIMIT ?",
                                (f"%{aa}%", f"%{ab}%", limit - len(results)),
                            )
                            for row in cur.fetchall():
                                entry = dict(row)
                                entry["source"] = "md_sections"
                                results.append(entry)
                        except Exception:
                            pass
                        if len(results) >= limit:
                            break
                    if len(results) >= limit:
                        break

            conn.close()
        except Exception as exc:
            logger.error("DB error in find_cooccurrences: %s", exc)

        return results[:limit]

    def build_entity_index(self) -> dict[str, list]:
        """Scan evidence_quotes and md_sections to build entity occurrence index."""
        index: dict[str, list] = collections.defaultdict(list)
        t0 = time.time()

        try:
            conn = sqlite3.connect(self.db_path)
            cur = conn.cursor()

            # evidence_quotes
            try:
                cur.execute(
                    "SELECT rowid, quote_text FROM evidence_quotes"
                )
                for rowid, text in cur.fetchall():
                    if not text:
                        continue
                    text_lower = text.lower()
                    for alias, canonical in self._alias_to_canonical.items():
                        if len(alias) > 2 and alias in text_lower:
                            doc_ref = f"evidence_quotes:{rowid}"
                            if doc_ref not in index[canonical]:
                                index[canonical].append(doc_ref)
            except Exception as exc:
                logger.warning("Skipping evidence_quotes scan: %s", exc)

            # md_sections
            try:
                cur.execute(
                    "SELECT rowid, content FROM md_sections"
                )
                for rowid, text in cur.fetchall():
                    if not text:
                        continue
                    text_lower = text.lower()
                    for alias, canonical in self._alias_to_canonical.items():
                        if len(alias) > 2 and alias in text_lower:
                            doc_ref = f"md_sections:{rowid}"
                            if doc_ref not in index[canonical]:
                                index[canonical].append(doc_ref)
            except Exception as exc:
                logger.warning("Skipping md_sections scan: %s", exc)

            conn.close()
        except Exception as exc:
            logger.error("DB error in build_entity_index: %s", exc)

        self._entity_index = dict(index)
        elapsed = time.time() - t0
        logger.info(
            "Entity index built in %.2fs: %d entities, %d total refs",
            elapsed,
            len(self._entity_index),
            sum(len(v) for v in self._entity_index.values()),
        )

        # Cache to disk
        try:
            os.makedirs(_CACHE_DIR, exist_ok=True)
            with open(self._index_path, "w", encoding="utf-8") as f:
                json.dump(self._entity_index, f, indent=2)
            logger.info("Entity index cached to %s", self._index_path)
        except Exception as exc:
            logger.warning("Failed to cache entity index: %s", exc)

        return self._entity_index

    def get_entity_stats(self) -> dict:
        """Returns mention counts for each canonical entity across the DB."""
        # Load cached index if available
        if self._entity_index is None:
            if os.path.exists(self._index_path):
                try:
                    with open(self._index_path, "r", encoding="utf-8") as f:
                        self._entity_index = json.load(f)
                except Exception:
                    self._entity_index = {}
            else:
                self._entity_index = {}

        stats: dict[str, dict] = {}
        for canonical in self.canonical_map:
            refs = self._entity_index.get(canonical, [])
            eq_count = sum(1 for r in refs if r.startswith("evidence_quotes:"))
            md_count = sum(1 for r in refs if r.startswith("md_sections:"))
            stats[canonical] = {
                "total_refs": len(refs),
                "evidence_quotes": eq_count,
                "md_sections": md_count,
                "alias_count": len(self.canonical_map[canonical]),
            }
        return stats

    # ------------------------------------------------------------------
    # Self-test
    # ------------------------------------------------------------------
    def self_test(self) -> None:
        """Resolve test strings, show entity profiles."""
        print("=" * 70)
        print("  MBP LitigationOS — Entity Resolver Self-Test")
        print("=" * 70)

        # --- Test resolve_entity (exact) ---
        test_mentions = [
            "Andrew", "Watson", "McNeill", "FOC", "COA", "MSC",
            "Tiffany Pigors", "Her Honor", "the Court", "GAL",
            "CPS", "JTC", "USDC", "Sheriff", "Shady Oaks",
            "Lane A", "Plaintiff-Appellant", "Mom",
        ]
        print("\n[1] resolve_entity (exact + fuzzy):")
        for mention in test_mentions:
            resolved = self.resolve_entity(mention)
            tag = "exact" if mention.lower() in self._alias_to_canonical else "fuzzy"
            print(f"    {mention:30s} -> {resolved}  [{tag}]")

        # --- Test fuzzy matching ---
        fuzzy_tests = [
            "Andew Pigor",   # typo
            "Tifany Watsn",  # typo
            "Judge McNeil",  # close
            "Muskegn Sheriff",
        ]
        print("\n[2] Fuzzy resolution (typos):")
        for mention in fuzzy_tests:
            canonical, score = self._fuzzy_resolve(mention)
            print(f"    {mention:30s} -> {canonical or '???':30s}  (score={score:.3f})")

        # --- Test resolve (full text) ---
        sample_text = (
            "On January 15, 2025, Andrew Pigors filed a motion with the "
            "14th Circuit Court. Judge McNeill denied the motion without "
            "hearing. The FOC recommended supervised parenting time. "
            "Tiffany Watson objected through her attorney. The GAL filed "
            "a supplemental report. Andrew appealed to the Court of Appeals."
        )
        print("\n[3] resolve (full text scan):")
        mentions = self.resolve(sample_text)
        for m in mentions:
            print(
                f"    [{m['start']:3d}-{m['end']:3d}] "
                f"{m['mention']:35s} -> {m['canonical']}"
            )
        print(f"    Total mentions found: {len(mentions)}")

        # --- Test entity profile ---
        print("\n[4] get_entity_profile('Judge McNeill'):")
        profile = self.get_entity_profile("Judge McNeill")
        for key, val in profile.items():
            if isinstance(val, list):
                print(f"    {key}: {len(val)} items")
            else:
                print(f"    {key}: {val}")

        # --- Test entity stats ---
        print("\n[5] get_entity_stats (from cache/index):")
        stats = self.get_entity_stats()
        for entity, s in sorted(
            stats.items(), key=lambda x: x[1]["total_refs"], reverse=True
        )[:10]:
            print(
                f"    {entity:40s}  refs={s['total_refs']:5d}  "
                f"eq={s['evidence_quotes']:4d}  md={s['md_sections']:4d}"
            )

        # --- Summary ---
        print("\n" + "=" * 70)
        print(f"  Canonical entities : {len(self.canonical_map)}")
        print(f"  Total aliases      : {len(self._alias_to_canonical)}")
        print(f"  sklearn available  : {HAS_SKLEARN}")
        print("=" * 70)


# ------------------------------------------------------------------
# CLI entry point
# ------------------------------------------------------------------
if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    )
    resolver = EntityResolver()
    resolver.self_test()
