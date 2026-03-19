"""
Discovery Engine — LitigationOS 2026
Generates discovery requests (interrogatories, RFPs, RFAs), responses, motions
to compel, and privilege logs for Pigors v. Watson consolidated litigation.
Indexes evidence_file_index (153,661 rows), documents (18,012 rows),
scanned_pdf_triage (390 rows).
"""

import json
import os
import sqlite3
import sys
from datetime import datetime
from typing import Any, Dict, List, Optional

DB_PATH = os.environ.get("LITIGATION_DB_PATH", r"C:\Users\andre\LitigationOS\litigation_context.db")


def _get_db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH, timeout=30)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA query_only=ON")
    conn.row_factory = sqlite3.Row
    return conn


class DiscoveryEngine:
    """Generates discovery requests, responses, and motions to compel."""

    def get_file_index(self, limit: int = 200) -> List[Dict[str, Any]]:
        """Query evidence_file_index table (153,661 rows)."""
        conn = _get_db()
        try:
            rows = conn.execute(
                "SELECT * FROM evidence_file_index ORDER BY rowid DESC LIMIT ?",
                (limit,),
            ).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    def get_documents(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Query documents table (18,012 rows)."""
        conn = _get_db()
        try:
            rows = conn.execute(
                "SELECT * FROM documents ORDER BY rowid DESC LIMIT ?",
                (limit,),
            ).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    def get_scanned_pdfs(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Query scanned_pdf_triage table (390 rows)."""
        conn = _get_db()
        try:
            rows = conn.execute(
                "SELECT * FROM scanned_pdf_triage ORDER BY rowid DESC LIMIT ?",
                (limit,),
            ).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    def search_documents(self, query: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Search pages_fts for document content."""
        conn = _get_db()
        try:
            rows = conn.execute(
                """SELECT p.*
                   FROM pages p
                   JOIN pages_fts fts ON p.rowid = fts.rowid
                   WHERE pages_fts MATCH ?
                   ORDER BY rank
                   LIMIT ?""",
                (query, limit),
            ).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    def generate_discovery_request(
        self, request_type: str, topics: List[str]
    ) -> Dict[str, Any]:
        """Generate interrogatories, RFPs, or RFAs per MCR 2.309/2.310/2.312."""
        request_type = request_type.upper()
        now = datetime.now().strftime("%B %d, %Y")

        # Get relevant evidence for each topic
        conn = _get_db()
        try:
            topic_evidence = {}
            for topic in topics:
                try:
                    rows = conn.execute(
                        """SELECT eq.quote_text, eq.legal_significance
                           FROM evidence_quotes eq
                           JOIN evidence_quotes_fts fts ON eq.rowid = fts.rowid
                           WHERE evidence_quotes_fts MATCH ?
                           ORDER BY rank LIMIT 5""",
                        (topic,),
                    ).fetchall()
                    topic_evidence[topic] = [dict(r) for r in rows]
                except sqlite3.OperationalError:
                    topic_evidence[topic] = []
        finally:
            conn.close()

        if request_type in ("INTERROGATORY", "INTERROGATORIES"):
            items = []
            for i, topic in enumerate(topics, 1):
                items.append({
                    "number": i,
                    "text": (
                        f"State in detail all facts known to you, or which you can "
                        f"ascertain through reasonable inquiry, regarding {topic}, "
                        f"including but not limited to: (a) all relevant dates; "
                        f"(b) all persons with knowledge; (c) all documents relating "
                        f"thereto; and (d) the substance of any communications."
                    ),
                })
            authority = "MCR 2.309 — Interrogatories"
            limit_note = "MCR 2.309(A)(2) limits interrogatories to 35 including subparts."

        elif request_type in ("RFP", "REQUEST FOR PRODUCTION", "RFPS"):
            items = []
            for i, topic in enumerate(topics, 1):
                items.append({
                    "number": i,
                    "text": (
                        f"Produce all documents and electronically stored information "
                        f"in your possession, custody, or control relating to {topic}, "
                        f"including but not limited to: correspondence, emails, text "
                        f"messages, photographs, recordings, reports, notes, memoranda, "
                        f"and any other tangible items."
                    ),
                })
            authority = "MCR 2.310 — Request for Production of Documents"
            limit_note = "No numeric limit under MCR; must be relevant per MCR 2.302(B)."

        elif request_type in ("RFA", "REQUEST FOR ADMISSION", "RFAS"):
            items = []
            for i, topic in enumerate(topics, 1):
                items.append({
                    "number": i,
                    "text": (
                        f"Admit that {topic}. If you cannot admit or deny this "
                        f"request in its entirety, please state in detail the "
                        f"reasons why and what portion, if any, you can admit."
                    ),
                })
            authority = "MCR 2.312 — Request for Admission"
            limit_note = (
                "MCR 2.312(A) — deemed admitted if not answered within 28 days. "
                "Costs of proving denied matters recoverable under MCR 2.312(D)."
            )
        else:
            return {
                "error": f"Unknown request type: {request_type}",
                "valid_types": ["INTERROGATORIES", "RFP", "RFA"],
            }

        return {
            "document_type": f"PLAINTIFF'S {request_type}",
            "case_caption": "PIGORS v. WATSON, Case No. 2024-001507-DC",
            "court": "14th Circuit Court, Muskegon County, Michigan",
            "date": now,
            "authority": authority,
            "limit_note": limit_note,
            "definitions": {
                "document": (
                    "As used herein, 'document' includes all writings, drawings, "
                    "graphs, charts, photographs, recordings, electronically stored "
                    "information, and other data compilations, per MCR 2.310(A)."
                ),
                "you": "Defendant Tiffany Watson and any agents or representatives.",
                "relating_to": "Concerning, referring to, reflecting, or pertaining to.",
            },
            "requests": items,
            "request_count": len(items),
            "topic_evidence": topic_evidence,
            "instructions": (
                "Responses due within 28 days of service per MCR 2.309(B)/2.310(B)/2.312(B). "
                "Objections must state grounds with particularity."
            ),
        }

    def generate_discovery_response(self, request_text: str) -> Dict[str, Any]:
        """Draft discovery response with appropriate objections."""
        conn = _get_db()
        try:
            # Search for relevant evidence to support response
            keywords = [w for w in request_text.split() if len(w) > 4][:5]
            supporting_evidence = []
            for kw in keywords:
                try:
                    rows = conn.execute(
                        """SELECT eq.quote_text, eq.legal_significance, eq.evidence_category
                           FROM evidence_quotes eq
                           JOIN evidence_quotes_fts fts ON eq.rowid = fts.rowid
                           WHERE evidence_quotes_fts MATCH ?
                           ORDER BY rank LIMIT 5""",
                        (kw,),
                    ).fetchall()
                    supporting_evidence.extend(dict(r) for r in rows)
                except sqlite3.OperationalError:
                    pass

            common_objections = [
                {
                    "objection": "Overbroad and unduly burdensome",
                    "authority": "MCR 2.302(C) — protective order for undue burden",
                },
                {
                    "objection": "Vague and ambiguous",
                    "authority": "MCR 2.302(B)(1) — relevance standard",
                },
                {
                    "objection": "Attorney-client privilege / work product",
                    "authority": "MRE 501; MCR 2.302(B)(3) — work product protection",
                },
                {
                    "objection": "Not reasonably calculated to lead to admissible evidence",
                    "authority": "MCR 2.302(B)(1) — scope of discovery",
                },
            ]

            return {
                "request_analyzed": request_text[:500],
                "response_template": {
                    "preamble": (
                        "Plaintiff Andrew Pigors responds to Defendant's discovery "
                        "request as follows, subject to the following general objections:"
                    ),
                    "general_objections": [
                        "Plaintiff objects to any request that seeks information "
                        "protected by attorney-client privilege or work product doctrine.",
                        "Plaintiff objects to any request that is overbroad, unduly "
                        "burdensome, or not proportional to the needs of the case.",
                    ],
                    "specific_response": (
                        "Subject to and without waiving the foregoing objections, "
                        "Plaintiff responds as follows: [DRAFT RESPONSE HERE]"
                    ),
                },
                "applicable_objections": common_objections,
                "supporting_evidence": supporting_evidence[:15],
                "authority": {
                    "response_timing": "MCR 2.309(B) — 28 days to respond",
                    "objection_requirements": "MCR 2.309(B)(4) — state grounds with particularity",
                    "privilege_log": "MCR 2.302(B)(5) — privilege log required for withheld docs",
                },
            }
        finally:
            conn.close()

    def generate_motion_to_compel(self, discovery_type: str) -> Dict[str, Any]:
        """Generate motion to compel with MCR 2.313 authority."""
        conn = _get_db()
        try:
            # Get relevant authority
            authority = []
            try:
                rows = conn.execute(
                    """SELECT rule_number, title, full_text
                       FROM auth_rules
                       WHERE rule_number LIKE '%2.313%'
                       LIMIT 10"""
                ).fetchall()
                authority = [dict(r) for r in rows]
            except sqlite3.OperationalError:
                pass

            # If no specific rule found, search broadly
            if not authority:
                try:
                    rows = conn.execute(
                        """SELECT ar.*
                           FROM auth_rules ar
                           JOIN auth_rules_fts fts ON ar.rowid = fts.rowid
                           WHERE auth_rules_fts MATCH 'compel OR discovery OR sanction'
                           ORDER BY rank LIMIT 10"""
                    ).fetchall()
                    authority = [dict(r) for r in rows]
                except sqlite3.OperationalError:
                    pass

            return {
                "document_type": "MOTION TO COMPEL DISCOVERY",
                "case_caption": "PIGORS v. WATSON, Case No. 2024-001507-DC",
                "court": "14th Circuit Court, Muskegon County, Michigan",
                "judge": "Hon. Jenny L. McNeill",
                "discovery_type": discovery_type,
                "date": datetime.now().strftime("%B %d, %Y"),
                "irac_structure": {
                    "issue": (
                        f"Whether Defendant should be compelled to respond to "
                        f"Plaintiff's {discovery_type} pursuant to MCR 2.313."
                    ),
                    "rule": {
                        "primary": (
                            "MCR 2.313(A)(1) — A party may apply for an order "
                            "compelling discovery when a party fails to answer "
                            "interrogatories or respond to a request for production."
                        ),
                        "sanctions": (
                            "MCR 2.313(A)(5) — The court shall require the party "
                            "whose conduct necessitated the motion to pay reasonable "
                            "expenses including attorney fees, unless the court finds "
                            "that the opposition was substantially justified."
                        ),
                        "good_faith_conference": (
                            "MCR 2.313(A)(4) — Motion must include certification that "
                            "movant has in good faith conferred or attempted to confer "
                            "with the party not making disclosure in an effort to secure "
                            "disclosure without court action."
                        ),
                    },
                    "application": (
                        "Plaintiff served discovery requests on Defendant. Defendant "
                        "has [failed to respond / provided inadequate responses / "
                        "asserted improper objections]. Plaintiff conferred in good "
                        "faith with Defendant to resolve the dispute without court "
                        "intervention, but Defendant [refused / failed to respond]."
                    ),
                    "conclusion": (
                        "Plaintiff respectfully requests that this Court: "
                        "(1) enter an order compelling Defendant to provide full and "
                        "complete responses within 14 days; (2) award Plaintiff "
                        "reasonable expenses under MCR 2.313(A)(5); and (3) grant "
                        "such other relief as the Court deems just and proper."
                    ),
                },
                "required_components": [
                    "Caption per MCR 2.113",
                    "Good faith conference certification — MCR 2.313(A)(4)",
                    "Statement of discovery requests served",
                    "Statement of deficient responses or non-response",
                    "IRAC argument",
                    "Proposed order",
                    "Certificate of service",
                ],
                "authority_from_db": authority[:5],
            }
        finally:
            conn.close()

    def generate_privilege_log(self) -> Dict[str, Any]:
        """List of potentially privileged documents per MCR 2.302(B)(5)."""
        conn = _get_db()
        try:
            # Search for attorney-client communications or work product
            privileged_candidates = []
            privilege_keywords = [
                "attorney", "counsel", "legal advice", "privileged",
                "work product", "litigation strategy", "confidential",
            ]
            for kw in privilege_keywords:
                try:
                    rows = conn.execute(
                        """SELECT file_path, file_name
                           FROM documents
                           WHERE file_path LIKE ? OR file_name LIKE ?
                           LIMIT 20""",
                        (f"%{kw}%", f"%{kw}%"),
                    ).fetchall()
                    privileged_candidates.extend(dict(r) for r in rows)
                except sqlite3.OperationalError:
                    pass

            # Deduplicate
            seen = set()
            unique = []
            for doc in privileged_candidates:
                key = doc.get("file_path", "") or doc.get("file_name", "")
                if key not in seen:
                    seen.add(key)
                    unique.append(doc)

            return {
                "title": "PRIVILEGE LOG",
                "authority": (
                    "MCR 2.302(B)(5) — When a party withholds information otherwise "
                    "discoverable by claiming privilege, the party shall make the claim "
                    "expressly and describe the nature of the documents or things not "
                    "produced in a manner that will enable other parties to assess the "
                    "applicability of the privilege."
                ),
                "privilege_types": {
                    "attorney_client": (
                        "Communications between client and attorney for purpose of "
                        "obtaining legal advice. MRE 501."
                    ),
                    "work_product": (
                        "Documents prepared in anticipation of litigation. "
                        "MCR 2.302(B)(3)."
                    ),
                    "mental_impressions": (
                        "Attorney mental impressions, conclusions, opinions — "
                        "absolute protection. MCR 2.302(B)(3)(a)."
                    ),
                },
                "log_format": {
                    "required_fields": [
                        "Document date",
                        "Document type/description",
                        "Author/sender",
                        "Recipient(s)",
                        "Privilege asserted",
                        "Basis for privilege",
                    ],
                },
                "potentially_privileged_documents": unique[:50],
                "document_count": len(unique),
                "note": (
                    "Review each document individually. Pro se litigant work product "
                    "is protected under MCR 2.302(B)(3). ChatGPT legal research "
                    "conversations may qualify as work product if prepared in "
                    "anticipation of litigation."
                ),
            }
        finally:
            conn.close()

    def assess_document_completeness(self, topic: str) -> Dict[str, Any]:
        """Assess what documents we have vs. likely missing for a topic."""
        conn = _get_db()
        try:
            # Search file index for topic-related documents
            topic_docs = []
            try:
                rows = conn.execute(
                    """SELECT * FROM evidence_file_index
                       WHERE file_path LIKE ? OR file_name LIKE ?
                       LIMIT 100""",
                    (f"%{topic}%", f"%{topic}%"),
                ).fetchall()
                topic_docs = [dict(r) for r in rows]
            except sqlite3.OperationalError:
                pass

            # Search pages for topic content
            page_hits = []
            try:
                rows = conn.execute(
                    """SELECT p.document_id, COUNT(*) as page_count
                       FROM pages p
                       JOIN pages_fts fts ON p.rowid = fts.rowid
                       WHERE pages_fts MATCH ?
                       GROUP BY p.document_id
                       ORDER BY page_count DESC
                       LIMIT 30""",
                    (topic,),
                ).fetchall()
                page_hits = [dict(r) for r in rows]
            except sqlite3.OperationalError:
                pass

            # Search evidence quotes
            evidence_hits = []
            try:
                rows = conn.execute(
                    """SELECT eq.evidence_category, COUNT(*) as cnt
                       FROM evidence_quotes eq
                       JOIN evidence_quotes_fts fts ON eq.rowid = fts.rowid
                       WHERE evidence_quotes_fts MATCH ?
                       GROUP BY eq.evidence_category
                       ORDER BY cnt DESC""",
                    (topic,),
                ).fetchall()
                evidence_hits = [dict(r) for r in rows]
            except sqlite3.OperationalError:
                pass

            # Check for gap tickets on this topic
            gaps = []
            try:
                rows = conn.execute(
                    """SELECT * FROM gap_tickets
                       WHERE description LIKE ?
                       LIMIT 20""",
                    (f"%{topic}%",),
                ).fetchall()
                gaps = [dict(r) for r in rows]
            except sqlite3.OperationalError:
                pass

            # Standard document categories expected in family litigation
            expected_categories = [
                "Financial records (tax returns, pay stubs, bank statements)",
                "Communication records (texts, emails, social media)",
                "School records",
                "Medical records",
                "Court orders and filings",
                "FOC reports and recommendations",
                "Witness statements / affidavits",
                "Photographs / videos",
                "Police reports",
                "Housing records",
            ]

            return {
                "topic": topic,
                "documents_found": len(topic_docs),
                "documents_sample": topic_docs[:20],
                "page_content_hits": page_hits,
                "evidence_by_category": evidence_hits,
                "known_gaps": gaps,
                "expected_document_categories": expected_categories,
                "completeness_assessment": {
                    "has_documents": len(topic_docs) > 0,
                    "has_page_content": len(page_hits) > 0,
                    "has_evidence_quotes": len(evidence_hits) > 0,
                    "has_known_gaps": len(gaps) > 0,
                },
                "recommendation": (
                    "Review expected categories against documents found. "
                    "Issue targeted discovery requests for any missing categories "
                    "using generate_discovery_request()."
                ),
            }
        finally:
            conn.close()

    def get_statistics(self) -> Dict[str, Any]:
        """Total files, documents, and categories."""
        conn = _get_db()
        try:
            file_count = conn.execute(
                "SELECT COUNT(*) as cnt FROM evidence_file_index"
            ).fetchone()["cnt"]

            doc_count = conn.execute(
                "SELECT COUNT(*) as cnt FROM documents"
            ).fetchone()["cnt"]

            pdf_count = conn.execute(
                "SELECT COUNT(*) as cnt FROM scanned_pdf_triage"
            ).fetchone()["cnt"]

            page_count = conn.execute(
                "SELECT COUNT(*) as cnt FROM pages"
            ).fetchone()["cnt"]

            # Column info
            file_cols = conn.execute(
                "PRAGMA table_info(evidence_file_index)"
            ).fetchall()
            doc_cols = conn.execute("PRAGMA table_info(documents)").fetchall()
            pdf_cols = conn.execute("PRAGMA table_info(scanned_pdf_triage)").fetchall()

            return {
                "evidence_file_index_count": file_count,
                "documents_count": doc_count,
                "scanned_pdf_triage_count": pdf_count,
                "pages_count": page_count,
                "total_indexed_items": file_count + doc_count + pdf_count,
                "evidence_file_index_columns": [c["name"] for c in file_cols],
                "documents_columns": [c["name"] for c in doc_cols],
                "scanned_pdf_triage_columns": [c["name"] for c in pdf_cols],
            }
        finally:
            conn.close()


def self_test() -> Dict[str, Any]:
    """Run self-test to verify database connectivity and table access."""
    results = {"status": "ok", "tests": {}}
    de = DiscoveryEngine()

    try:
        stats = de.get_statistics()
        results["tests"]["statistics"] = {
            "passed": stats["evidence_file_index_count"] > 0,
            "files": stats["evidence_file_index_count"],
            "documents": stats["documents_count"],
            "scanned_pdfs": stats["scanned_pdf_triage_count"],
        }
    except Exception as e:
        results["tests"]["statistics"] = {"passed": False, "error": str(e)}

    try:
        files = de.get_file_index(limit=5)
        results["tests"]["get_file_index"] = {
            "passed": isinstance(files, list),
            "count": len(files),
        }
    except Exception as e:
        results["tests"]["get_file_index"] = {"passed": False, "error": str(e)}

    try:
        docs = de.get_documents(limit=5)
        results["tests"]["get_documents"] = {
            "passed": isinstance(docs, list),
            "count": len(docs),
        }
    except Exception as e:
        results["tests"]["get_documents"] = {"passed": False, "error": str(e)}

    try:
        search = de.search_documents("custody", limit=5)
        results["tests"]["search_documents"] = {
            "passed": isinstance(search, list),
            "count": len(search),
        }
    except Exception as e:
        results["tests"]["search_documents"] = {"passed": False, "error": str(e)}

    try:
        req = de.generate_discovery_request("INTERROGATORIES", ["custody", "parenting time"])
        results["tests"]["generate_request"] = {
            "passed": "requests" in req and len(req["requests"]) == 2,
        }
    except Exception as e:
        results["tests"]["generate_request"] = {"passed": False, "error": str(e)}

    results["status"] = (
        "ok" if all(t.get("passed") for t in results["tests"].values()) else "degraded"
    )
    return results


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        print(json.dumps(self_test(), indent=2, default=str))
    elif len(sys.argv) > 1 and sys.argv[1] == "stats":
        de = DiscoveryEngine()
        print(json.dumps(de.get_statistics(), indent=2, default=str))
    elif len(sys.argv) > 1 and sys.argv[1] == "search" and len(sys.argv) > 2:
        de = DiscoveryEngine()
        print(json.dumps(de.search_documents(sys.argv[2]), indent=2, default=str))
    elif len(sys.argv) > 1 and sys.argv[1] == "request" and len(sys.argv) > 3:
        de = DiscoveryEngine()
        print(json.dumps(
            de.generate_discovery_request(sys.argv[2], sys.argv[3:]),
            indent=2, default=str,
        ))
    elif len(sys.argv) > 1 and sys.argv[1] == "compel" and len(sys.argv) > 2:
        de = DiscoveryEngine()
        print(json.dumps(de.generate_motion_to_compel(sys.argv[2]), indent=2, default=str))
    elif len(sys.argv) > 1 and sys.argv[1] == "completeness" and len(sys.argv) > 2:
        de = DiscoveryEngine()
        print(json.dumps(de.assess_document_completeness(sys.argv[2]), indent=2, default=str))
    else:
        print(
            "Usage: python discovery_engine.py "
            "[test|stats|search <query>|request <type> <topics...>|compel <type>|completeness <topic>]"
        )
