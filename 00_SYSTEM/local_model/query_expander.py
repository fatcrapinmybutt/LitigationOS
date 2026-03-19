"""
THE MANBEARPIG — Query Expansion Engine (EPOCH v4.0)
====================================================
Legal thesaurus + co-occurrence mining for query enrichment.
Expands user queries with Michigan family-law synonyms, authority
citations, and DB-mined co-occurring terms before retrieval.
"""

import sqlite3
import re
import time
import sys
from collections import Counter

DB_PATH = r"C:\Users\andre\LitigationOS\litigation_context.db"


class QueryExpander:
    """Expand queries using a Michigan legal thesaurus and DB co-occurrence."""

    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self.thesaurus = self._build_thesaurus()
        # Normalised lookup: lowercase key → list of expansions
        self._lookup = {}
        for key, synonyms in self.thesaurus.items():
            self._lookup[key.lower()] = synonyms
            # Also index each synonym back to the group
            for syn in synonyms:
                norm = syn.lower()
                if norm not in self._lookup:
                    self._lookup[norm] = synonyms

    # ------------------------------------------------------------------
    # Thesaurus
    # ------------------------------------------------------------------

    @staticmethod
    def _build_thesaurus() -> dict:
        """Comprehensive Michigan family-law thesaurus (50+ entries)."""
        return {
            # --- Custody & Parenting ---
            "custody": ["parenting time", "custodial environment", "best interest",
                        "MCL 722.23", "physical custody", "legal custody",
                        "joint custody", "sole custody", "custody determination"],
            "best interest": ["best interest factors", "MCL 722.23", "child welfare",
                              "best interest of the child", "factor analysis"],
            "parenting time": ["visitation", "parenting schedule", "MCL 722.27a",
                               "overnights", "holiday schedule", "makeup parenting time"],
            "established custodial environment": ["ECE", "MCL 722.27(1)(c)",
                                                  "custodial stability", "clear and convincing evidence"],
            "change of circumstances": ["Vodvarka", "Vodvarka v Grasher",
                                        "proper cause", "modification threshold"],
            # --- Alienation ---
            "alienation": ["parental alienation", "factor j", "MCL 722.23(j)",
                           "Lombardo", "willingness to facilitate",
                           "interference with parenting", "alienating conduct"],
            "parental alienation": ["alienation", "factor j", "MCL 722.23(j)",
                                    "Lombardo v Lombardo", "willingness to facilitate",
                                    "gatekeeping", "obstruction of relationship"],
            "factor j": ["MCL 722.23(j)", "willingness to facilitate",
                         "parental alienation", "Lombardo"],
            # --- Judicial Conduct ---
            "disqualification": ["recusal", "bias", "prejudice", "MCR 2.003",
                                 "judicial misconduct", "actual bias",
                                 "appearance of impropriety"],
            "recusal": ["disqualification", "MCR 2.003", "bias", "prejudice",
                        "judicial disqualification", "motion to disqualify"],
            "judicial misconduct": ["canon violation", "JTC", "Judicial Tenure Commission",
                                    "MCR 9.104", "MCR 9.205", "benchbook violation"],
            "bias": ["prejudice", "impartiality", "MCR 2.003(C)(1)",
                     "actual bias", "appearance of bias", "judicial bias"],
            # --- Discovery ---
            "discovery": ["interrogatories", "deposition", "subpoena",
                          "MCR 2.302", "production of documents", "MCR 2.310",
                          "request for admissions", "MCR 2.312"],
            "interrogatories": ["discovery", "MCR 2.309", "written questions",
                                "answers to interrogatories"],
            "deposition": ["discovery", "MCR 2.306", "deposition transcript",
                           "oral examination", "deposition upon written questions"],
            "subpoena": ["MCR 2.506", "subpoena duces tecum", "compulsory process",
                         "witness subpoena"],
            "motion to compel": ["MCR 2.313", "discovery enforcement",
                                 "compel discovery", "sanctions for non-compliance"],
            # --- Contempt ---
            "contempt": ["contempt of court", "civil contempt", "MCL 600.1701",
                         "MCR 3.606", "sanctions", "criminal contempt",
                         "show cause", "purge condition"],
            "sanctions": ["contempt", "MCR 2.313(B)", "attorney fees",
                          "discovery sanctions", "MCR 2.114"],
            # --- Appeals ---
            "appeal": ["appellate", "claim of appeal", "MCR 7.204", "COA",
                        "brief on appeal", "MCR 7.212", "Court of Appeals",
                        "appeal of right", "MCR 7.203"],
            "appellate": ["appeal", "COA", "MCR 7.204", "MCR 7.205",
                          "appellant", "appellee", "appellate brief"],
            "claim of appeal": ["MCR 7.204", "notice of appeal",
                                "appeal of right", "21-day deadline"],
            "brief on appeal": ["MCR 7.212", "appellate brief",
                                "statement of questions presented",
                                "statement of facts", "argument section"],
            "standard of review": ["de novo", "abuse of discretion",
                                   "clear error", "great weight of evidence",
                                   "clearly erroneous"],
            # --- PPO ---
            "PPO": ["personal protection order", "MCL 600.2950",
                     "restraining order", "no contact", "ex parte PPO",
                     "domestic relationship PPO"],
            "personal protection order": ["PPO", "MCL 600.2950",
                                          "restraining order", "MCL 600.2950a",
                                          "stalking PPO"],
            # --- Due Process ---
            "due process": ["14th Amendment", "fundamental rights", "Troxel",
                            "procedural due process", "substantive due process",
                            "Troxel v Granville", "parental liberty interest"],
            "fundamental rights": ["due process", "14th Amendment",
                                   "parental rights", "Troxel v Granville",
                                   "liberty interest"],
            # --- Evidence ---
            "evidence": ["MRE", "admissibility", "exhibit", "testimony",
                         "hearsay", "relevance", "MRE 401", "MRE 402"],
            "hearsay": ["MRE 801", "MRE 802", "MRE 803", "MRE 804",
                        "out of court statement", "hearsay exception",
                        "excited utterance", "present sense impression"],
            "admissibility": ["MRE 402", "MRE 403", "relevance",
                              "probative value", "prejudicial effect",
                              "foundation", "authentication"],
            "impeachment": ["MRE 607", "MRE 608", "MRE 609",
                            "prior inconsistent statement", "credibility",
                            "contradiction", "bias of witness"],
            # --- Motions ---
            "summary disposition": ["MCR 2.116", "C(7)", "C(8)", "C(10)",
                                    "no genuine issue", "failure to state a claim"],
            "motion": ["MCR 2.119", "brief in support", "motion hearing",
                       "response to motion", "reply brief"],
            "motion for reconsideration": ["MCR 2.119(F)", "21 days",
                                           "palpable error", "reconsideration"],
            # --- Service & Filing ---
            "service of process": ["MCR 2.105", "personal service",
                                   "substitute service", "MCR 2.107",
                                   "proof of service", "certificate of service"],
            "filing": ["e-filing", "MiFILE", "TrueFiling",
                       "proof of filing", "time-stamped"],
            # --- FOC ---
            "friend of court": ["FOC", "MCL 552.501", "FOC recommendation",
                                "FOC referee", "objection to FOC",
                                "de novo hearing"],
            "FOC": ["friend of court", "MCL 552.501", "FOC recommendation",
                    "MCL 552.507", "FOC referee hearing"],
            # --- GAL ---
            "guardian ad litem": ["GAL", "MCR 3.915", "MCL 722.24",
                                  "child representative", "best interest attorney"],
            "GAL": ["guardian ad litem", "MCR 3.915", "MCL 722.24",
                    "child advocate"],
            # --- Superintending Control ---
            "superintending control": ["MCR 3.302", "MCL 600.1701",
                                       "extraordinary writ", "mandamus",
                                       "complaint for superintending control"],
            "mandamus": ["superintending control", "MCR 3.302",
                         "writ of mandamus", "ministerial duty"],
            # --- Child Support ---
            "child support": ["MCL 552.605", "Michigan Child Support Formula",
                              "MCSF", "support obligation", "income shares model"],
            "support": ["child support", "spousal support", "alimony",
                        "MCL 552.605", "support modification"],
            # --- Domestic Violence ---
            "domestic violence": ["DV", "MCL 750.81", "assault",
                                  "domestic assault", "MCL 400.1501",
                                  "VAWA", "safety planning"],
            # --- Separation ---
            "separation": ["parent-child separation", "329+ days",
                           "deprivation of parenting", "no contact period"],
            # --- Miscellaneous Michigan ---
            "SCAO": ["State Court Administrative Office",
                     "SCAO form", "administrative order"],
            "MCR": ["Michigan Court Rules", "court rule",
                    "procedural rule"],
            "MCL": ["Michigan Compiled Laws", "statute",
                    "statutory authority"],
            "MRE": ["Michigan Rules of Evidence", "evidence rule",
                    "evidentiary rule"],
            # --- Procedural ---
            "hearing": ["evidentiary hearing", "motion hearing",
                        "oral argument", "scheduling conference",
                        "status conference"],
            "trial": ["bench trial", "evidentiary hearing",
                      "trial court", "finder of fact"],
            "order": ["court order", "ex parte order", "stipulated order",
                      "consent order", "proposed order"],
            "objection": ["MCR 2.119", "objection to recommendation",
                          "FOC objection", "de novo hearing request"],
        }

    # ------------------------------------------------------------------
    # Expansion
    # ------------------------------------------------------------------

    def expand(self, query: str) -> str:
        """Expand query with thesaurus matches.

        Tokenises the query, finds matching thesaurus keys, appends
        unique expansions.  Returns the enriched query string.
        """
        original_tokens = re.findall(r"[\w'.]+", query.lower())
        expansions = set()

        # Single-word matches
        for token in original_tokens:
            if token in self._lookup:
                for syn in self._lookup[token]:
                    expansions.add(syn.lower())

        # Bigram / trigram matches (e.g. "best interest", "friend of court")
        text_lower = query.lower()
        for key in self.thesaurus:
            if key.lower() in text_lower:
                for syn in self.thesaurus[key]:
                    expansions.add(syn.lower())

        # Remove tokens already present in original query
        original_set = set(original_tokens)
        new_terms = [e for e in expansions if not all(w in original_set for w in e.split())]

        if not new_terms:
            return query

        return query + " " + " ".join(sorted(set(new_terms)))

    def expand_with_context(self, query: str, top_k: int = 5) -> str:
        """Expand query with thesaurus AND DB co-occurrence mining.

        1. First applies thesaurus expansion.
        2. Then finds terms that frequently co-occur near query terms
           in evidence_quotes.
        """
        expanded = self.expand(query)

        # Mine co-occurring terms from evidence_quotes
        co_terms = self._mine_cooccurrence(query, top_k=top_k)
        if co_terms:
            expanded = expanded + " " + " ".join(co_terms)

        return expanded

    def _mine_cooccurrence(self, query: str, top_k: int = 5) -> list:
        """Find terms that frequently appear near query terms in evidence_quotes."""
        tokens = re.findall(r"\w+", query.lower())
        if not tokens:
            return []

        co_counter = Counter()
        try:
            conn = sqlite3.connect(self.db_path, timeout=10)
            conn.execute("PRAGMA query_only=ON")

            # Use FTS5 to find matching evidence, then extract neighbouring terms
            safe_tokens = []
            for t in tokens:
                cleaned = "".join(ch for ch in t if ch.isalnum())
                if cleaned and len(cleaned) > 2:
                    safe_tokens.append(f'"{cleaned}"')
            if not safe_tokens:
                conn.close()
                return []

            fts_query = " OR ".join(safe_tokens)
            try:
                rows = conn.execute(
                    "SELECT quote_text FROM evidence_quotes_fts "
                    "WHERE evidence_quotes_fts MATCH ? LIMIT 200",
                    (fts_query,),
                ).fetchall()
            except Exception:
                # Fallback: LIKE search
                like_clause = " OR ".join(f"quote_text LIKE '%{t}%'" for t in tokens[:3])
                rows = conn.execute(
                    f"SELECT quote_text FROM evidence_quotes WHERE {like_clause} LIMIT 200"
                ).fetchall()

            conn.close()

            # Count terms in matched documents
            stop_words = {
                "the", "and", "for", "that", "this", "with", "was", "are",
                "not", "but", "have", "has", "had", "been", "from", "they",
                "will", "would", "could", "should", "their", "there", "what",
                "which", "when", "where", "who", "how", "can", "does", "did",
                "its", "you", "your", "she", "her", "his", "him",
                "our", "out", "all", "also", "than", "then", "into",
                "about", "were", "being", "other", "some", "more",
            }
            query_set = set(tokens)

            for (text,) in rows:
                if not text:
                    continue
                words = re.findall(r"\w+", text.lower())
                for w in words:
                    if len(w) > 3 and w not in stop_words and w not in query_set:
                        co_counter[w] += 1

        except Exception as exc:
            print(f"[QueryExpander] Co-occurrence mining error: {exc}")
            return []

        # Return top_k most frequent co-occurring terms
        return [term for term, _ in co_counter.most_common(top_k)]

    # ------------------------------------------------------------------
    # Utility
    # ------------------------------------------------------------------

    def get_synonyms(self, term: str) -> list:
        """Return all synonyms/expansions for a given term."""
        norm = term.lower().strip()
        # Direct lookup
        if norm in self._lookup:
            return list(self._lookup[norm])
        # Substring match in thesaurus keys
        matches = []
        for key, syns in self.thesaurus.items():
            if norm in key.lower() or key.lower() in norm:
                matches.extend(syns)
        return list(set(matches)) if matches else []

    # ------------------------------------------------------------------
    # Self-test
    # ------------------------------------------------------------------

    def self_test(self):
        """Expand test queries, show before/after."""
        test_queries = [
            "custody best interest",
            "judicial bias disqualification",
            "parental alienation factor j",
            "discovery interrogatories",
            "appeal brief COA",
            "PPO domestic violence",
            "contempt sanctions",
            "due process fundamental rights",
        ]

        print("\n" + "=" * 70)
        print("  QUERY EXPANDER — SELF TEST")
        print("=" * 70)
        print(f"  Thesaurus entries: {len(self.thesaurus)}")
        print(f"  Lookup keys:      {len(self._lookup)}")
        print("=" * 70)

        for q in test_queries:
            expanded = self.expand(q)
            print(f"\n  ORIGINAL : {q}")
            print(f"  EXPANDED : {expanded[:200]}{'...' if len(expanded) > 200 else ''}")
            # Show token count growth
            orig_count = len(q.split())
            exp_count = len(expanded.split())
            print(f"  TOKENS   : {orig_count} → {exp_count} (+{exp_count - orig_count})")

        # Test get_synonyms
        print(f"\n{'─' * 60}")
        print("  SYNONYM LOOKUPS:")
        for term in ["custody", "PPO", "hearsay", "MCR 2.003"]:
            syns = self.get_synonyms(term)
            print(f"    {term:20s} → {syns[:5]}")

        # Test context expansion (if DB available)
        print(f"\n{'─' * 60}")
        print("  CONTEXT EXPANSION (with DB co-occurrence):")
        try:
            ctx = self.expand_with_context("custody alienation", top_k=5)
            print(f"    INPUT  : custody alienation")
            print(f"    OUTPUT : {ctx[:200]}{'...' if len(ctx) > 200 else ''}")
        except Exception as exc:
            print(f"    DB unavailable: {exc}")

        print("\n" + "=" * 70)
        print("  SELF TEST COMPLETE")
        print("=" * 70)


# ------------------------------------------------------------------
# CLI entry point
# ------------------------------------------------------------------
if __name__ == "__main__":
    qe = QueryExpander()
    if "--test" in sys.argv or len(sys.argv) == 1:
        qe.self_test()
    else:
        query = " ".join(sys.argv[1:])
        print(f"Original:  {query}")
        print(f"Expanded:  {qe.expand(query)}")
        print(f"Synonyms:  {qe.get_synonyms(query)}")
