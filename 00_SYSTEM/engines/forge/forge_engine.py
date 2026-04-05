"""
FORGE — Filing Operations & Readiness Generation Engine
═══════════════════════════════════════════════════════════

Takes evidence + authorities + templates → produces court-ready filing packets.
Each packet: lead document + affidavit + exhibits + proposed order + service cert.

Part of the PANTHEON Engine Suite for LitigationOS.
"""

import sys
import os
import json
import sqlite3
import hashlib
import logging
from datetime import datetime, date
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# Shared module integration(with fallback for standalone execution)
try:
    _SYSTEM_DIR = Path(__file__).resolve().parent.parent.parent  # engines/forge/ → 00_SYSTEM/
    if str(_SYSTEM_DIR) not in sys.path:
        sys.path.insert(0, str(_SYSTEM_DIR))
    from shared import get_db_path, get_root
    _HAS_SHARED = True
except ImportError:
    _HAS_SHARED = False
    logger.debug("shared module not available, using standalone fallback paths")

if _HAS_SHARED:
    DB_PATH = str(get_db_path("litigation"))
    FILINGS_DIR = get_root() / "01_FILINGS"
    TEMPLATES_DIR = Path(__file__).resolve().parent / "templates"
else:
    DB_PATH = str(Path(__file__).resolve().parents[3] / "litigation_context.db")  # fallback
    FILINGS_DIR = Path(r"C:\Users\andre\LitigationOS\01_FILINGS")
    TEMPLATES_DIR = Path(r"C:\Users\andre\LitigationOS\00_SYSTEM\engines\forge\templates")

# Michigan court info
COURTS = {
    "A": {"name": "14th Circuit Court, Family Division", "case": "2024-001507-DC", "judge": "Hon. Jenny L. McNeill"},
    "B": {"name": "14th Circuit Court, Civil Division", "case": "2025-002760-CZ", "judge": "Hon. Kenneth Hoopes"},
    "D": {"name": "14th Circuit Court", "case": "2023-5907-PP", "judge": "Hon. Jenny L. McNeill"},
    "E": {"name": "Judicial Tenure Commission", "case": "JTC Complaint", "judge": "N/A"},
    "F": {"name": "Michigan Court of Appeals", "case": "COA 366810", "judge": "Panel TBD"},
}

PARTY_INFO = {
    "plaintiff": {"name": "Andrew James Pigors", "address": "1977 Whitehall Road, Lot 17, North Muskegon, MI 49445",
                   "phone": "(231) 903-5690", "email": "andrewjpigors@gmail.com"},
    "defendant": {"name": "Emily A. Watson", "address": "2160 Garland Drive, Norton Shores, MI 49441"},
    "child": "L.D.W.",
    "foc": {"name": "Pamela Rusco", "address": "990 Terrace St, Muskegon, MI 49442"},
}

# Filing packet components
PACKET_COMPONENTS = {
    "motion": ["lead_motion", "brief_in_support", "affidavit", "exhibit_index", "exhibits",
                "proposed_order", "proof_of_service", "certificate_of_service"],
    "response": ["lead_response", "brief_in_opposition", "affidavit", "exhibit_index", "exhibits",
                  "proof_of_service"],
    "petition": ["lead_petition", "supporting_brief", "affidavit", "exhibit_index", "exhibits",
                  "proposed_order", "proof_of_service"],
    "complaint": ["lead_complaint", "affidavit", "exhibit_index", "exhibits", "summons"],
    "appeal": ["claim_of_appeal", "jurisdictional_checklist", "designation_record",
                "docketing_statement", "proof_of_service"],
    "emergency": ["lead_motion", "brief_in_support", "affidavit_emergency", "exhibit_index",
                   "exhibits", "proposed_order", "ex_parte_motion", "proof_of_service"],
}


def get_db():
    """Get DB connection with required PRAGMAs."""
    conn = sqlite3.connect(DB_PATH, timeout=60)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA busy_timeout = 60000")
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA cache_size = -32000")
    return conn


def init_tables(conn):
    """Create FORGE tables."""
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS forge_packets (
            packet_id TEXT PRIMARY KEY,
            lane TEXT NOT NULL,
            filing_type TEXT NOT NULL,
            title TEXT NOT NULL,
            status TEXT DEFAULT 'draft',
            components_json TEXT,
            completeness_pct REAL DEFAULT 0,
            output_dir TEXT,
            created_at TEXT DEFAULT (datetime('now')),
            updated_at TEXT DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS forge_exhibits (
            exhibit_id TEXT PRIMARY KEY,
            packet_id TEXT,
            exhibit_label TEXT,
            bates_start TEXT,
            bates_end TEXT,
            source_path TEXT,
            description TEXT,
            authenticated INTEGER DEFAULT 0,
            created_at TEXT DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS forge_checklists (
            checklist_id TEXT PRIMARY KEY,
            packet_id TEXT,
            requirement TEXT NOT NULL,
            mcr_reference TEXT,
            satisfied INTEGER DEFAULT 0,
            notes TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS forge_service (
            service_id TEXT PRIMARY KEY,
            packet_id TEXT,
            served_party TEXT,
            method TEXT,
            address TEXT,
            date_served TEXT,
            proof_path TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        );
        CREATE INDEX IF NOT EXISTS idx_forge_packets_lane ON forge_packets(lane);
        CREATE INDEX IF NOT EXISTS idx_forge_exhibits_packet ON forge_exhibits(packet_id);
    """)


class ForgeEngine:
    """Court-ready filing packet assembly engine."""

    def __init__(self):
        self.conn = get_db()
        init_tables(self.conn)
        self.bates_counter = self._get_next_bates()

    def _get_next_bates(self) -> int:
        """Get the next available Bates number."""
        row = self.conn.execute(
            "SELECT MAX(CAST(REPLACE(bates_end, 'PIGORS-', '') AS INTEGER)) FROM forge_exhibits"
        ).fetchone()
        return (row[0] or 0) + 1

    def _bates_stamp(self, count: int = 1) -> tuple:
        """Generate Bates stamp range."""
        start = f"PIGORS-{self.bates_counter:06d}"
        end = f"PIGORS-{self.bates_counter + count - 1:06d}"
        self.bates_counter += count
        return start, end

    def create_packet(self, lane: str, filing_type: str, title: str) -> str:
        """Create a new filing packet scaffold."""
        packet_id = f"{lane}-{filing_type}-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        components = PACKET_COMPONENTS.get(filing_type, PACKET_COMPONENTS["motion"])
        component_status = {c: "missing" for c in components}

        output_dir = FILINGS_DIR / f"{lane}_{filing_type}_{datetime.now().strftime('%Y%m%d')}"
        output_dir.mkdir(parents=True, exist_ok=True)

        self.conn.execute(
            "INSERT INTO forge_packets (packet_id, lane, filing_type, title, components_json, output_dir) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (packet_id, lane, filing_type, title, json.dumps(component_status), str(output_dir))
        )
        self._generate_checklist(packet_id, lane, filing_type)
        self.conn.commit()
        return packet_id

    def _generate_checklist(self, packet_id: str, lane: str, filing_type: str):
        """Generate MCR compliance checklist for the packet."""
        requirements = [
            ("Caption format per MCR 2.113", "MCR 2.113(C)", 0),
            ("Case number on all pages", "MCR 2.113(C)(2)", 0),
            ("Parties correctly identified", "MCR 2.113(C)(1)", 0),
            ("Proper court designation", "MCR 2.113(C)(1)", 0),
            ("Signed by filing party", "MCR 2.114", 0),
            ("Certificate of service attached", "MCR 2.107", 0),
            ("Proof of service on all parties", "MCR 2.107(C)", 0),
            ("Child identified by initials only", "MCR 8.119(H)", 0),
            ("No confidential info exposed", "MCR 8.119", 0),
            ("Filing fee addressed", "MCL 600.880", 0),
        ]

        if filing_type == "motion":
            requirements.extend([
                ("Brief in support attached or filed separately", "MCR 2.119(A)(2)", 0),
                ("Proposed order attached", "MCR 2.602(B)", 0),
                ("Notice of hearing date", "MCR 2.119(C)", 0),
            ])
        elif filing_type == "emergency":
            requirements.extend([
                ("Ex parte motion with specific grounds", "MCR 2.119(B)", 0),
                ("Affidavit showing irreparable harm", "MCR 3.207", 0),
                ("Good cause for emergency relief shown", "MCR 3.207(A)", 0),
            ])
        elif filing_type == "appeal":
            requirements.extend([
                ("Claim of appeal timely filed", "MCR 7.204(A)", 0),
                ("Jurisdictional checklist complete", "MCR 7.204(E)", 0),
                ("Transcript ordered or waived", "MCR 7.210(A)", 0),
                ("Docketing statement filed", "MCR 7.204(E)", 0),
            ])

        for req_text, mcr_ref, satisfied in requirements:
            cid = hashlib.md5(f"{packet_id}:{req_text}".encode()).hexdigest()[:12]
            self.conn.execute(
                "INSERT OR IGNORE INTO forge_checklists "
                "(checklist_id, packet_id, requirement, mcr_reference, satisfied) "
                "VALUES (?, ?, ?, ?, ?)",
                (cid, packet_id, req_text, mcr_ref, satisfied)
            )

    def add_exhibit(self, packet_id: str, source_path: str, description: str, pages: int = 1) -> str:
        """Add an exhibit to a packet with Bates stamps."""
        bates_start, bates_end = self._bates_stamp(pages)
        # Auto-label: Exhibit A, B, C...
        count = self.conn.execute(
            "SELECT COUNT(*) FROM forge_exhibits WHERE packet_id = ?", (packet_id,)
        ).fetchone()[0]
        label = f"Exhibit {chr(65 + count)}" if count < 26 else f"Exhibit {count + 1}"

        exhibit_id = f"{packet_id}-{label.replace(' ', '-').lower()}"
        self.conn.execute(
            "INSERT OR REPLACE INTO forge_exhibits "
            "(exhibit_id, packet_id, exhibit_label, bates_start, bates_end, source_path, description) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (exhibit_id, packet_id, label, bates_start, bates_end, source_path, description)
        )
        self.conn.commit()
        return exhibit_id

    def generate_caption(self, lane: str) -> str:
        """Generate a properly formatted Michigan court caption."""
        court = COURTS.get(lane, COURTS["A"])
        p = PARTY_INFO["plaintiff"]
        d = PARTY_INFO["defendant"]

        return f"""STATE OF MICHIGAN
IN THE {court['name'].upper()}
COUNTY OF MUSKEGON

{p['name'].upper()},
    Plaintiff,

v                                           Case No. {court['case']}
                                            {court['judge']}
{d['name'].upper()},
    Defendant.
{'_' * 40}/"""

    def generate_verification(self) -> str:
        """Generate verification/signature block."""
        p = PARTY_INFO["plaintiff"]
        return f"""
Respectfully submitted,

Date: {date.today().strftime('%B %d, %Y')}

___________________________
{p['name']}
{p['address']}
{p['phone']}
{p['email']}
In Propria Persona"""

    def generate_certificate_of_service(self, packet_id: str) -> str:
        """Generate certificate of service."""
        d = PARTY_INFO["defendant"]
        return f"""CERTIFICATE OF SERVICE

I, {PARTY_INFO['plaintiff']['name']}, hereby certify that on {date.today().strftime('%B %d, %Y')},
I served a true copy of the foregoing document(s) upon the following party(ies) by
first-class U.S. Mail, postage prepaid, addressed to:

    {d['name']}
    {d['address']}

    {PARTY_INFO['foc']['name']}
    Friend of the Court
    {PARTY_INFO['foc']['address']}

___________________________
{PARTY_INFO['plaintiff']['name']}"""

    def generate_exhibit_index(self, packet_id: str) -> str:
        """Generate exhibit index for a packet."""
        exhibits = self.conn.execute(
            "SELECT exhibit_label, bates_start, bates_end, description "
            "FROM forge_exhibits WHERE packet_id = ? ORDER BY exhibit_label",
            (packet_id,)
        ).fetchall()

        if not exhibits:
            return "No exhibits attached."

        lines = ["EXHIBIT INDEX", "=" * 60, ""]
        lines.append(f"{'Label':<15} {'Bates Range':<25} {'Description'}")
        lines.append("-" * 80)
        for ex in exhibits:
            lines.append(f"{ex[0]:<15} {ex[1]}-{ex[2]:<15} {ex[3]}")
        return "\n".join(lines)

    def validate_packet(self, packet_id: str) -> dict:
        """Validate a packet against its MCR checklist."""
        checklist = self.conn.execute(
            "SELECT requirement, mcr_reference, satisfied FROM forge_checklists WHERE packet_id = ?",
            (packet_id,)
        ).fetchall()

        total = len(checklist)
        satisfied = sum(1 for c in checklist if c[2])
        missing = [{"requirement": c[0], "mcr": c[1]} for c in checklist if not c[2]]

        return {
            "packet_id": packet_id,
            "completeness": round(satisfied / total * 100, 1) if total else 0,
            "satisfied": satisfied,
            "total": total,
            "missing": missing,
        }

    def assemble(self, lane: str, filing_type: str, title: str, exhibit_paths: list = None) -> dict:
        """Full assembly pipeline: create packet, add exhibits, generate boilerplate."""
        packet_id = self.create_packet(lane, filing_type, title)

        if exhibit_paths:
            for path in exhibit_paths:
                p = Path(path)
                if p.exists():
                    self.add_exhibit(packet_id, str(p), p.stem.replace("_", " ").title())

        caption = self.generate_caption(lane)
        verification = self.generate_verification()
        cert_service = self.generate_certificate_of_service(packet_id)
        exhibit_index = self.generate_exhibit_index(packet_id)
        validation = self.validate_packet(packet_id)

        # Write assembled components to output directory
        packet = self.conn.execute(
            "SELECT output_dir FROM forge_packets WHERE packet_id = ?", (packet_id,)
        ).fetchone()
        output_dir = Path(packet[0])

        (output_dir / "00_CAPTION.md").write_text(caption, encoding="utf-8")
        (output_dir / "98_VERIFICATION.md").write_text(verification, encoding="utf-8")
        (output_dir / "99_CERTIFICATE_OF_SERVICE.md").write_text(cert_service, encoding="utf-8")
        (output_dir / "97_EXHIBIT_INDEX.md").write_text(exhibit_index, encoding="utf-8")
        (output_dir / "VALIDATION_REPORT.json").write_text(
            json.dumps(validation, indent=2), encoding="utf-8"
        )

        self.conn.execute(
            "UPDATE forge_packets SET completeness_pct = ?, status = 'assembled', updated_at = datetime('now') "
            "WHERE packet_id = ?",
            (validation["completeness"], packet_id)
        )
        self.conn.commit()

        return {
            "packet_id": packet_id,
            "output_dir": str(output_dir),
            "components_written": 4,
            "exhibits": len(exhibit_paths or []),
            "validation": validation,
        }

    def status(self) -> dict:
        """Get status of all packets."""
        row = self.conn.execute("""
            SELECT
                (SELECT COUNT(*) FROM forge_packets) as total_packets,
                (SELECT COUNT(*) FROM forge_packets WHERE status = 'assembled') as assembled,
                (SELECT COUNT(*) FROM forge_packets WHERE status = 'draft') as drafts,
                (SELECT COUNT(*) FROM forge_exhibits) as total_exhibits,
                (SELECT COUNT(*) FROM forge_checklists WHERE satisfied = 1) as checks_passed,
                (SELECT COUNT(*) FROM forge_checklists) as total_checks
        """).fetchone()
        return dict(row)

    def list_packets(self, lane: str = None) -> list:
        """List all packets, optionally filtered by lane."""
        query = "SELECT packet_id, lane, filing_type, title, status, completeness_pct FROM forge_packets"
        params = ()
        if lane:
            query += " WHERE lane = ?"
            params = (lane,)
        query += " ORDER BY created_at DESC"
        return [dict(r) for r in self.conn.execute(query, params).fetchall()]

    def close(self):
        self.conn.close()


def main():
    """CLI interface."""
    if len(sys.argv) < 2:
        print("""
╔══════════════════════════════════════════════════════════╗
║          FORGE ⚒️  — Filing Assembly Engine               ║
╠══════════════════════════════════════════════════════════╣
║                                                          ║
║  Commands:                                               ║
║    assemble <lane> <type> <title> [--exhibits p1,p2]    ║
║    validate <packet_id>                                  ║
║    exhibits <packet_id>                                  ║
║    checklist <packet_id>                                 ║
║    list [--lane A|B|D|E|F]                              ║
║    caption <lane>                                        ║
║    status                                                ║
║                                                          ║
║  Types: motion, response, petition, complaint,           ║
║         appeal, emergency                                ║
║                                                          ║
║  Lanes: A(custody) B(housing) D(PPO) E(JTC) F(appeal)  ║
╚══════════════════════════════════════════════════════════╝""")
        return

    cmd = sys.argv[1]
    engine = ForgeEngine()

    try:
        if cmd == "assemble" and len(sys.argv) >= 5:
            lane, ftype, title = sys.argv[2], sys.argv[3], sys.argv[4]
            exhibits = []
            if "--exhibits" in sys.argv:
                idx = sys.argv.index("--exhibits")
                if idx + 1 < len(sys.argv):
                    exhibits = sys.argv[idx + 1].split(",")
            result = engine.assemble(lane, ftype, title, exhibits)
            print(json.dumps(result, indent=2))

        elif cmd == "validate" and len(sys.argv) >= 3:
            result = engine.validate_packet(sys.argv[2])
            print(json.dumps(result, indent=2))

        elif cmd == "exhibits" and len(sys.argv) >= 3:
            print(engine.generate_exhibit_index(sys.argv[2]))

        elif cmd == "caption" and len(sys.argv) >= 3:
            print(engine.generate_caption(sys.argv[2]))

        elif cmd == "list":
            lane = None
            if "--lane" in sys.argv:
                idx = sys.argv.index("--lane")
                if idx + 1 < len(sys.argv):
                    lane = sys.argv[idx + 1]
            packets = engine.list_packets(lane)
            for p in packets:
                status_icon = "✅" if p["status"] == "assembled" else "📝"
                print(f"  {status_icon} [{p['lane']}] {p['packet_id']}: {p['title']} ({p['completeness_pct']}%)")

        elif cmd == "status":
            s = engine.status()
            print(f"""
╔══════════════════════════════════════╗
║        FORGE STATUS DASHBOARD        ║
╠══════════════════════════════════════╣
║  Packets:    {s['total_packets']:>4}                   ║
║  Assembled:  {s['assembled']:>4}                   ║
║  Drafts:     {s['drafts']:>4}                   ║
║  Exhibits:   {s['total_exhibits']:>4}                   ║
║  Checks:     {s['checks_passed']}/{s['total_checks']} passed           ║
╚══════════════════════════════════════╝""")
        else:
            print(f"Unknown command: {cmd}")
    finally:
        engine.close()


if __name__ == "__main__":
    main()
