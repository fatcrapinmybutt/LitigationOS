#!/usr/bin/env python3
"""Phase 4: Brain database write — evidence registry, contradictions, legal theories, timeline events."""

import sqlite3
import sys
import os

# Set UTF-8 encoding
os.environ['PYTHONIOENCODING'] = 'utf-8'

def main():
    # Connect to brain database
    conn = sqlite3.connect(r"C:\Users\andre\LitigationOS\00_SYSTEM\brains\shadyoaks_brain.db")
    conn.execute("PRAGMA busy_timeout=60000")
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA cache_size=-32000")
    cursor = conn.cursor()

    print("=" * 80)
    print("PHASE 4: BRAIN DATABASE WRITE")
    print("=" * 80)

    try:
        # 1. INSERT INTO evidence_registry
        print("\n[1] Inserting evidence_registry rows...")
        # Columns: id, exhibit_id, description, file_path, evidence_type, date_of_evidence, actors_involved, legal_theory, bates_number, status, notes
        evidence_data = [
            ('EVR-LARA-001', 'LARA License #1201891 confirmation - Bryon Fields as licensee for dissolved LLC', r'I:\LITIGOS_DEDUP\2026-04-08\49144664_ADVERSARY_CHRONOLOGIES_2\ADVERSARY_CHRONOLOGIES_2.md', 'MD', '2026-03-16', 'Bryon Fields, Shady Oaks', 'RICO, fraud, void license', '', 'VERIFIED', 'LARA License: #1201891 (Licensee: Bryon Fields)'),
            ('EVR-LLC-001', 'LLC dissolution + MCL 450.4802 void acts + MCR 2.612(C)(1)(d) void judgment', r'I:\LITIGOS_DEDUP\2026-04-08\3d9465c6_ENCYCLOPEDIA_MASTER_1\ENCYCLOPEDIA_MASTER_1.txt', 'TXT', '2025-04-15', 'Shady Oaks MHP LLC, Legal Counsel', 'MCL 450.4802, MCR 2.612(C)(1)(d), void judgment', '', 'VERIFIED', 'Shady Oaks MHP LLC, a legally dissolved entity. Under MCR 2.612(C)(1)(d), a judgment obtained through a dissolved and unauthorized entity is void.'),
            ('EVR-BROWN-001', 'Jeremy Brown proposed order MCR 2.119(G)(3) — NOT a forgery. Brown received it, made zero objections at time, then falsely characterized as fabricated.', r'I:\LITIGOS_DEDUP\2026-04-08\3d9465c6_ENCYCLOPEDIA_MASTER_1\ENCYCLOPEDIA_MASTER_1.txt', 'TXT', '2025-07-09', 'Jeremy Brown P77427, Andrew Pigors, Judge', 'MCR 1.109(E)(5), defamation, malicious prosecution, abuse of process', '', 'VERIFIED', 'Proposed order legally submitted on July 9, 2025 pursuant to MCR 2.119(G)(3). Circulated to all parties including counsel Jeremy Brown, who lodged no objection, then falsely characterized as forged.'),
            ('EVR-BROWN-002', 'Check fraud — MDHHS payment + $1,300.26 check altered/omitted from rent ledger to procure eviction judgment', r'I:\LITIGOS_DEDUP\2026-04-08\3d9465c6_ENCYCLOPEDIA_MASTER_1\ENCYCLOPEDIA_MASTER_1.txt', 'TXT', '2025-04-15', 'Jeremy Brown, Shady Oaks HOA', 'MCL 600.2918, fraud, forgery, MCR 2.612(C)(1)(c)', '', 'VERIFIED', 'Altered or omitted both the MDHHS payment and the $1,300.26 check. Used to procure an eviction judgment under fraudulent financial pretenses.'),
            ('EVR-BROWN-003', 'Zego/payment portal — pre-2025 payment history WIPED. Removes proof of timely rent payments.', r'I:\LITIGOS_DEDUP\2026-04-08\3d9465c6_ENCYCLOPEDIA_MASTER_1\ENCYCLOPEDIA_MASTER_1.txt', 'TXT', '2025-07-14', 'Shady Oaks HOA, Jeremy Brown', 'spoliation, evidence destruction, MCR 2.302(E)', '', 'VERIFIED', 'The payment portal pre-2025 payment history wiped or deleted, removing key proof of timely rent payments.'),
            ('EVR-EGLE-001', 'EGLE Violation Notice VN-017235 — sewage violation at Shady Oaks MHP', r'I:\LITIGOS_DEDUP\2026-04-08\05d1ddb3_Correspondence_ Shady Oaks Park MHP VN-017235\Correspondence_ Shady Oaks Park MHP VN-017235.pdf', 'PDF', '2025-06-15', 'EGLE, Shady Oaks MHP', 'MCL 554.139, habitability, regulatory violation', '', 'VERIFIED', 'EGLE sewage violation notice VN-017235'),
            ('EVR-ENTITY-001', 'Full entity shell chain: Cricklewood -> Shady Oaks -> Homes of America (dissolved) -> Partridge Equity -> Alden Global', r'I:\LITIGOS_DEDUP\2026-04-08\49144664_ADVERSARY_CHRONOLOGIES_2\ADVERSARY_CHRONOLOGIES_2.md', 'MD', '2026-03-16', 'Cricklewood LLC, Shady Oaks, Alden Global', 'RICO, MCL 450.4802, fraud', '', 'VERIFIED', 'Entity shell game: Cricklewood -> Shady Oaks -> Homes of America (dissolved) -> Partridge Equity -> Alden Global'),
        ]
        
        cursor.executemany(
            """INSERT OR REPLACE INTO evidence_registry 
            (exhibit_id, description, file_path, evidence_type, date_of_evidence, actors_involved, legal_theory, bates_number, status, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            evidence_data
        )
        conn.commit()
        print(f"[OK] Inserted {len(evidence_data)} evidence_registry rows")

        # 2. INSERT INTO contradictions
        print("\n[2] Inserting contradictions rows...")
        # Columns: id, actor, statement_a, source_a, statement_b, source_b, significance, impeachment_value
        contradiction_data = [
            ('Jeremy Brown P77427', 'Brown accused Andrew of forging a judge signature on a fake order (July 2025)', 'Brown defamatory mischaracterization (post-July 2025)', 'The document was a proposed order legally submitted under MCR 2.119(G)(3). Brown received it and made ZERO objections at time of circulation.', 'ENCYCLOPEDIA_MASTER_1.txt - MCR 2.119(G)(3) compliance documentation', 'fraud_on_court_malicious_prosecution', 10),
            ('Shady Oaks / HOA / Brown', 'HOA claimed rent was unpaid to procure eviction judgment', 'Eviction complaint / rent ledger presented to court', 'Zego/payment portal pre-2025 history WIPED — removes proof of timely payments. MDHHS payment + $1,300.26 check altered/omitted from ledger.', 'ENCYCLOPEDIA_MASTER_1.txt - payment portal deletion + check fraud', 'fraud_spoliation_eviction_procurement', 10),
        ]
        
        cursor.executemany(
            """INSERT OR REPLACE INTO contradictions
            (actor, statement_a, source_a, statement_b, source_b, significance, impeachment_value)
            VALUES (?, ?, ?, ?, ?, ?, ?)""",
            contradiction_data
        )
        conn.commit()
        print(f"[OK] Inserted {len(contradiction_data)} contradictions rows")

        # 3. INSERT INTO legal_theories
        print("\n[3] Inserting legal_theories rows...")
        # Columns: id, count_number, theory_name, authority, elements, evidence_summary, status, layer_ref
        theory_data = [
            (14, 'Malicious False Accusation of Forgery (Defamation)', 'MCL 600.2918; MCR 1.109(E)(5); MRPC 3.3; MRPC 8.4(c)', 'False accusation; malice; damages; no prosecution filed', 'Jeremy Brown P77427 falsely accused Andrew of forging judges signature. Document was MCR 2.119(G)(3) proposed order. Brown received it, objected to nothing, then defamed Andrew. Never filed charges. Accusation abandoned = malicious prosecution + defamation.', 'VERIFIED', 'C14_defamation_malicious_prosecution'),
            (15, 'Spoliation — Zego Payment Portal History Wiped', 'MCR 2.302(E); MCL 600.2918; adverse inference doctrine', 'Evidence destruction; adverse inference warranted', 'Pre-2025 Zego payment portal history deleted — destroys proof of timely rent payment. Entitles Andrew to adverse inference instruction at trial.', 'VERIFIED', 'C15_spoliation'),
            (16, 'Check Fraud / Ledger Tampering to Procure Eviction', 'MCL 600.2907; MCL 750.249; MCR 2.612(C)(1)(c)', 'Check fraud; ledger falsification; fraud on court', 'MDHHS payment + $1,300.26 check altered/omitted from rent ledger presented to court. Used to manufacture unpaid rent narrative and procure fraudulent eviction judgment.', 'VERIFIED', 'C16_fraud_on_court'),
        ]
        
        cursor.executemany(
            """INSERT OR REPLACE INTO legal_theories
            (count_number, theory_name, authority, elements, evidence_summary, status, layer_ref)
            VALUES (?, ?, ?, ?, ?, ?, ?)""",
            theory_data
        )
        conn.commit()
        print(f"[OK] Inserted {len(theory_data)} legal_theories rows")

        # 4. INSERT INTO timeline_events
        print("\n[4] Inserting timeline_events rows...")
        # Columns: id, event_date, event_type, actor, target, description, legal_significance, evidence_refs, lane, severity
        timeline_data = [
            ('2025-07-09', 'Proposed Order Submission', 'Andrew Pigors', 'Circuit Court / all parties including Jeremy Brown', 'Submitted proposed order under MCR 2.119(G)(3) to stay eviction enforcement', 'Lawful proposed order — Brown received it, made ZERO objections. Later falsely characterized as forged.', 'ENCYCLOPEDIA_MASTER_1.txt', 'B', 10),
            ('2025-07-14', 'Evidence Spoliation', 'Shady Oaks/HOA/Brown', 'Evidence of Andrew timely rent payments', 'Zego payment portal pre-2025 history deleted/wiped', 'Spoliation — destroys proof of payment, adverse inference warranted', 'ENCYCLOPEDIA_MASTER_1.txt', 'B', 10),
            ('2024-03-26', 'Entity Shell Game', 'Cricklewood MHP LLC / Shady Oaks / HOA', 'Andrew Pigors Lot 17', 'Entity shell game: Cricklewood coerced lease signing, later transferred to Homes of America (dissolved), eviction executed by wrong entity', 'Entity fraud — eviction by dissolved entity = void under MCL 450.4802', 'ADVERSARY_CHRONOLOGIES_2.md', 'B', 10),
        ]
        
        cursor.executemany(
            """INSERT OR REPLACE INTO timeline_events
            (event_date, event_type, actor, target, description, legal_significance, evidence_refs, lane, severity)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            timeline_data
        )
        conn.commit()
        print(f"[OK] Inserted {len(timeline_data)} timeline_events rows")

        # 5. Verify by counting rows
        print("\n" + "=" * 80)
        print("VERIFICATION: Row Counts")
        print("=" * 80)

        cursor.execute("SELECT COUNT(*) FROM evidence_registry")
        count_evidence = cursor.fetchone()[0]
        print(f"evidence_registry: {count_evidence} rows")

        cursor.execute("SELECT COUNT(*) FROM contradictions")
        count_contradictions = cursor.fetchone()[0]
        print(f"contradictions: {count_contradictions} rows")

        cursor.execute("SELECT COUNT(*) FROM legal_theories")
        count_theories = cursor.fetchone()[0]
        print(f"legal_theories: {count_theories} rows")

        cursor.execute("SELECT COUNT(*) FROM timeline_events")
        count_timeline = cursor.fetchone()[0]
        print(f"timeline_events: {count_timeline} rows")

        print("\n" + "=" * 80)
        print("PHASE 4 BRAIN WRITE COMPLETE")
        print("=" * 80)

        conn.close()

    except Exception as e:
        print(f"\n[ERROR] {e}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        conn.close()
        sys.exit(1)

if __name__ == "__main__":
    main()

