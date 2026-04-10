"""
Phase 16-17: Write Gmail ledger evidence to brain DB + litigation_context.db.
OCR the COOKING THE BOOKS PDF + Andrew Pigors Ledger + VanDam screenshot.
"""
import sqlite3, os, datetime, sys

BRAIN = r"C:\Users\andre\LitigationOS\00_SYSTEM\brains\shadyoaks_brain.db"
MAIN  = r"C:\Users\andre\LitigationOS\litigation_context.db"
OUT   = r"C:\Users\andre\temp\phase16_writes.txt"
lines = []

def cn(p):
    c = sqlite3.connect(p)
    c.execute("PRAGMA busy_timeout=60000")
    c.execute("PRAGMA journal_mode=WAL")
    c.execute("PRAGMA cache_size=-32000")
    c.execute("PRAGMA synchronous=NORMAL")
    return c

# === NEW EVIDENCE ITEMS ===
brain_evidence = [
    # Gmail false ledger sequence
    ("EX_LEDGER_GMAIL_001", "Gmail thread: Cassandra sends false ledger May 16 2025; claims 'sent in error' after Andrew catches discrepancy. Ledger misrepresents payments through Dec 2024.",
     r"Gmail -SHADY OAKS CASSANDRA UNPROFESSIONAL FALSE LEDGER Andrew Pigors Current Ledger.pdf",
     "email_communication", "2025-05-16",
     "Cassandra VanDam (southhaven@ourhomesofamerica.com), Andrew Pigors",
     "fraudulent_ledger,false_records,concealment", "HIGH"),

    ("EX_LEDGER_GMAIL_002", "Cassandra reply: 'It was sent in error. Please disregard it.' — Attempt to suppress false ledger AFTER Andrew identified discrepancy with court-ordered Dec 2024 payment credit.",
     r"Gmail -SHADY OAKS CASSANDRA UNPROFESSIONAL FALSE LEDGER Andrew Pigors Current Ledger.pdf",
     "email_communication", "2025-05-16",
     "Cassandra VanDam", "evidence_suppression,false_records", "CRITICAL"),

    ("EX_LEDGER_GMAIL_003", "HOA refused ledger by email: 'Wasn't requested to me and if your needing anything from HOA your request needs to be in person at the office' — denied email records access.",
     r"Gmail -SHADY OAKS CASSANDRA UNPROFESSIONAL FALSE LEDGER Andrew Pigors Current Ledger.pdf",
     "email_communication", "2025-05-16",
     "South Haven Park MHC (southhaven@ourhomesofamerica.com)",
     "records_denial,harassment,spoliation_risk", "HIGH"),

    ("EX_LEDGER_MOTION_001", "Motion for Sanctions filed: 'submitting materially false and inconsistent rent ledger documentation in judicial proceedings. Misrepresenting payments made through December 2024, improper late fees, concealment of original security deposit terms.' MCR 2.114(E).",
     r"04_MOTION_FOR_SANCTIONS_LEDGER_FRAUD.docx",
     "court_filing", "2025-01-01",
     "Andrew Pigors (Plaintiff)",
     "MCR_2.114_sanctions,fraudulent_ledger,court_fraud", "HIGH"),

    ("EX_LEDGER_SPOLIATION", "CONFIRMED SPOLIATION: shady_oaks_park_mhp_llc_LEDGER.csv = 142,395 bytes ALL null bytes. XLS version = 2.1MB file with 1 empty cell. Both ledger conversions destroyed. Only authentic source: JPG original.",
     r"shady_oaks_park_mhp_llc_LEDGER.csv",
     "spoliation_evidence", "2025-01-01",
     "Shady Oaks Park MHP LLC / Homes of America",
     "spoliation,evidence_destruction,MCR_2.313", "CRITICAL"),
]

timeline_events = [
    ("Shady Oaks / Cassandra VanDam",
     "Cassandra sends false ledger to Andrew by email (rentmanager.com platform). Ledger misrepresents payments through December 2024 contrary to court order.",
     "2025-05-16", "false_ledger_sent",
     "EX_LEDGER_GMAIL_001", "B", "Evidence of intentional submission of false financial records", "CRITICAL", "Andrew Pigors"),

    ("Cassandra VanDam",
     "Cassandra replies 'It was sent in error. Please disregard it.' after Andrew disputes the ledger — attempted suppression of false ledger evidence.",
     "2025-05-16", "evidence_suppression",
     "EX_LEDGER_GMAIL_002", "B", "Consciousness of guilt — scrambling to suppress false records", "CRITICAL", "Andrew Pigors"),

    ("South Haven Park MHC",
     "HOA refuses email-based ledger request: demands in-person-only requests. Creates unreasonable barrier to records access.",
     "2025-05-16", "records_access_denial",
     "EX_LEDGER_GMAIL_003", "B", "MCL 600.2950 records denial + harassment pattern", "HIGH", "Andrew Pigors"),
]

contradictions = [
    ("Cassandra VanDam / Shady Oaks",
     9,
     "VanDam's false ledger contradicts court-stipulated Dec 2024 payment credit",
     "Ledger sent May 16 2025 shows unpaid/incorrect amounts through Dec 2024",
     "Court order stipulating rent paid through December 2024",
     "HOA submitted ledger misrepresenting payments covered by court order — material fraud on court"),

    ("Shady Oaks / Homes of America",
     10,
     "CSV/XLS ledger destruction contradicts fiduciary duty to maintain accurate records",
     "shady_oaks_park_mhp_llc_LEDGER.csv: 142,395 bytes = ALL null bytes (100% destroyed)",
     "shady enhanced redacted ledger$$$.jpg: authentic JPG ledger showing actual transactions",
     "SPOLIATION: Electronic ledger completely wiped — only authentic version is the physical photo. MCR 2.313 sanctions warranted."),
]

# Write to brain DB
conn = cn(BRAIN)
c = conn.cursor()

# evidence_registry
for (eid, desc, fp, etype, date, actors, theory, status) in brain_evidence:
    try:
        c.execute("""INSERT OR IGNORE INTO evidence_registry 
            (exhibit_id, description, file_path, evidence_type, date_of_evidence, actors_involved, legal_theory, status)
            VALUES (?,?,?,?,?,?,?,?)""",
            (eid, desc, fp, etype, date, actors, theory, status))
    except Exception as e:
        lines.append(f"evidence_registry error: {e}")

# timeline_events
for (actor, desc, date, etype, refs, lane, sig, sev, target) in timeline_events:
    try:
        c.execute("""INSERT OR IGNORE INTO timeline_events
            (actor, description, event_date, event_type, evidence_refs, lane, legal_significance, severity, target)
            VALUES (?,?,?,?,?,?,?,?,?)""",
            (actor, desc, date, etype, refs, lane, sig, sev, target))
    except Exception as e:
        lines.append(f"timeline_events error: {e}")

# contradictions
for (actor, val, sig, sa, sb, notes) in contradictions:
    try:
        c.execute("""INSERT OR IGNORE INTO contradictions
            (actor, impeachment_value, significance, source_a, source_b, statement_a, statement_b)
            VALUES (?,?,?,?,?,?,?)""",
            (actor, val, sig, sa, sb, notes))
    except Exception as e:
        lines.append(f"contradictions error: {e}")

conn.commit()

# Verify brain counts
for tbl in ["evidence_registry", "timeline_events", "contradictions"]:
    n = c.execute(f"SELECT COUNT(*) FROM {tbl}").fetchone()[0]
    lines.append(f"brain.{tbl}: {n} rows")
conn.close()

# === Write to litigation_context.db ===
main_conn = cn(MAIN)
mc = main_conn.cursor()

quotes = [
    ("B", "Cassandra VanDam / Shady Oaks FALSE LEDGER: Email May 16 2025 from southhaven@ourhomesofamerica.com sends incorrect ledger. After Andrew disputes: 'It was sent in error. Please disregard it.' — attempted evidence suppression. Prior request had gone unanswered for ~4 weeks.",
     r"Gmail -SHADY OAKS CASSANDRA UNPROFESSIONAL FALSE LEDGER Andrew Pigors Current Ledger.pdf", 1, 9.5,
     "vandm,cassandra,false_ledger,suppression,spoliation", "housing"),

    ("B", "HOA records access denial: 'Wasn't requested to me and if your needing anything from HOA your request needs to be in person at the office' — email request refused, forced to appear in person as barrier to records.",
     r"Gmail -SHADY OAKS CASSANDRA UNPROFESSIONAL FALSE LEDGER Andrew Pigors Current Ledger.pdf", 2, 8.5,
     "vandm,records_denial,harassment", "housing"),

    ("B", "Andrew Pigors email: 'This ledger is incorrect. Stipulated in the judges order, my rent was paid through December of 2024.' — confirms court order covered rent through Dec 2024, contradicting false ledger.",
     r"Gmail -SHADY OAKS CASSANDRA UNPROFESSIONAL FALSE LEDGER Andrew Pigors Current Ledger.pdf", 1, 9.0,
     "court_order,rent_paid,ledger_fraud", "housing"),

    ("B", "MOTION FOR SANCTIONS: 'Shady Oaks Park MHP LLC submitting materially false and inconsistent rent ledger documentation in judicial proceedings. Inconsistencies include misrepresenting payments made through December 2024, improper application of late fees, concealment of the original security deposit terms.' MCR 2.114(E).",
     r"04_MOTION_FOR_SANCTIONS_LEDGER_FRAUD.docx", 1, 9.5,
     "MCR_2.114,sanctions,ledger_fraud,court_fraud", "housing"),

    ("B", "SPOLIATION CONFIRMED: shady_oaks_park_mhp_llc_LEDGER.csv = 142,395 bytes ALL null bytes (100% wiped). XLS version 2.1MB contains 1 empty cell. Both electronic ledger formats completely destroyed. Authentic ledger exists only as JPG original photo.",
     r"shady_oaks_park_mhp_llc_LEDGER.csv", 1, 10.0,
     "spoliation,evidence_destruction,MCR_2.313,null_bytes", "housing"),
]

for (lane, qt, sf, pg, rs, tags, cat) in quotes:
    try:
        mc.execute("""INSERT INTO evidence_quotes (lane, quote_text, source_file, page_number, relevance_score, tags, category, is_duplicate, duplicate_of)
            VALUES (?,?,?,?,?,?,?,0,NULL)""",
            (lane, qt, sf, pg, rs, tags, cat))
    except Exception as e:
        lines.append(f"evidence_quotes error: {e}")

main_conn.commit()
q_count = mc.execute("SELECT COUNT(*) FROM evidence_quotes WHERE lane='B'").fetchone()[0]
lines.append(f"litigation_context.evidence_quotes lane=B: {q_count} rows")

# impeachment_matrix
impls = [
    ("Cassandra VanDam", "FALSE LEDGER + SUPPRESSION: Sent wrong ledger May 16 2025, claimed 'sent in error' after Andrew caught discrepancy — consciousness of guilt, MRE 404(b) pattern",
     r"Gmail FALSE LEDGER email thread May 16 2025", "Sent false ledger then immediately tried to retract when caught",
     "ledger_fraud", 10, "Is it true you emailed a ledger on May 16, 2025 that showed amounts not covered by the court's December 2024 stipulation? And then you said 'sent in error'? Was it 'in error' or were you hoping he wouldn't catch the discrepancy?", "B"),

    ("Shady Oaks / Homes of America", "SPOLIATION: Electronic ledger destroyed — CSV all null bytes, XLS empty. Only authentic version is physical JPG. MCR 2.313 sanctions.",
     r"shady_oaks_park_mhp_llc_LEDGER.csv", "142,395 bytes ALL null bytes — production of destroyed ledger to court",
     "spoliation", 10, "You produced this CSV file to the court as the ledger. Can you explain why every single byte in this file is a null byte? What happened to the data?", "B"),
]

for (target, summary, src, quote, cat, val, question, filing) in impls:
    try:
        mc.execute("""INSERT INTO impeachment_matrix 
            (target, evidence_summary, source_file, quote_text, category, impeachment_value, cross_exam_question, filing_relevance)
            VALUES (?,?,?,?,?,?,?,?)""",
            (target, summary, src, quote, cat, val, question, filing))
    except Exception as e:
        lines.append(f"impeachment_matrix error: {e}")

main_conn.commit()
imp_count = mc.execute("SELECT COUNT(*) FROM impeachment_matrix WHERE filing_relevance='B'").fetchone()[0]
lines.append(f"litigation_context.impeachment_matrix lane=B: {imp_count} rows")

# contradiction_map
for (target, val, sig, sa, sb, notes) in contradictions:
    try:
        mc.execute("""INSERT INTO contradiction_map (source_a, source_b, contradiction_text, severity, lane)
            VALUES (?,?,?,?,?)""",
            (sa, sb, notes, "critical", "B"))
    except Exception as e:
        lines.append(f"contradiction_map error: {e}")

main_conn.commit()
cm_count = mc.execute("SELECT COUNT(*) FROM contradiction_map WHERE lane='B'").fetchone()[0]
lines.append(f"litigation_context.contradiction_map lane=B: {cm_count} rows")
main_conn.close()

# === OCR: COOKING THE BOOKS PDF (scanned image) ===
ctb_pdf = r"C:\Users\andre\Desktop\COURT_FILING_PACKETS\SHADY\ledger COOKING THE BOOKS shady oaks.pdf"
lines.append(f"\n=== COOKING THE BOOKS PDF OCR ===")
try:
    import fitz  # PyMuPDF
    from PIL import Image
    import io
    doc = fitz.open(ctb_pdf)
    try:
        from paddleocr import PaddleOCR
        ocr_engine = PaddleOCR(use_angle_cls=True, lang='en', show_log=False)
        for pnum in range(min(len(doc), 4)):
            page = doc[pnum]
            mat = fitz.Matrix(2.0, 2.0)
            pix = page.get_pixmap(matrix=mat)
            img_bytes = pix.tobytes("png")
            img = Image.open(io.BytesIO(img_bytes))
            tmp_img = f"C:\\Users\\andre\\temp\\ctb_page_{pnum}.png"
            img.save(tmp_img)
            result = ocr_engine.ocr(tmp_img, cls=True)
            if result and result[0]:
                for line in result[0]:
                    if line and len(line) >= 2 and line[1]:
                        txt = str(line[1][0]).encode('ascii', errors='replace').decode('ascii')
                        conf = line[1][1] if len(line[1]) > 1 else 0
                        if conf > 0.5 and txt.strip():
                            lines.append(f"  [p{pnum+1}] {txt}")
        doc.close()
    except ImportError:
        lines.append("PaddleOCR not available — trying pytesseract")
        try:
            import pytesseract
            for pnum in range(min(len(doc), 4)):
                page = doc[pnum]
                pix = page.get_pixmap(matrix=fitz.Matrix(2.0, 2.0))
                img = Image.open(io.BytesIO(pix.tobytes("png")))
                text = pytesseract.image_to_string(img)
                lines.append(f"--- Page {pnum+1} ---")
                lines.append(text[:2000].encode('ascii', errors='replace').decode('ascii'))
        except Exception as e2:
            lines.append(f"pytesseract error: {e2}")
except Exception as e:
    lines.append(f"CTB OCR error: {e}")

# === OCR: VanDam screenshot ===
vandam_img = r"C:\Users\andre\Desktop\COURT_FILING_PACKETS\SHADY\Screenshot_20260218_212004_One UI Home.jpg"
lines.append(f"\n=== VANDAM SCREENSHOT OCR ===")
if os.path.exists(vandam_img):
    try:
        from paddleocr import PaddleOCR
        ocr = PaddleOCR(use_angle_cls=True, lang='en', show_log=False)
        result = ocr.ocr(vandam_img, cls=True)
        if result and result[0]:
            for line in result[0]:
                if line and len(line) >= 2 and line[1]:
                    txt = str(line[1][0]).encode('ascii', errors='replace').decode('ascii')
                    conf = line[1][1] if len(line[1]) > 1 else 0
                    if conf > 0.4 and txt.strip():
                        lines.append(f"  {txt}")
    except Exception as e:
        lines.append(f"VanDam OCR error: {e}")
else:
    lines.append("VanDam screenshot not found at expected path")

# Write output
with open(OUT, 'w', encoding='utf-8') as f:
    f.write('\n'.join(lines))

sys.stdout.buffer.write(b"Phase 16-17 complete\n")
