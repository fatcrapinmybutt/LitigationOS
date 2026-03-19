#!/usr/bin/env python3
"""
_mega_ingest.py — Ingest ALL legal reference materials into litigation_context.db.
LitigationOS · Andrew Pigors
"""
import csv
import hashlib
import json
import os
import re
import sqlite3
import sys
import time
import traceback
from datetime import datetime

DB_PATH = r"C:\Users\andre\litigation_context.db"

# Force UTF-8 stdout on Windows
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# ── helpers ──────────────────────────────────────────────────────────
def md5(text: str) -> str:
    return hashlib.md5(text.encode("utf-8", errors="replace")).hexdigest()[:16]

def connect_db():
    conn = sqlite3.connect(DB_PATH, timeout=120)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA cache_size=-65536")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.execute("PRAGMA temp_store=MEMORY")
    return conn

def safe_json(val):
    """Serialize non-string values to JSON for storage."""
    if val is None:
        return None
    if isinstance(val, (dict, list)):
        return json.dumps(val, ensure_ascii=False)
    return str(val)

RESULTS = {}

# ═══════════════════════════════════════════════════════════════════
# 1. michigan-court-rules.pages.jsonl → rules_text
# ═══════════════════════════════════════════════════════════════════
def ingest_michigan_court_rules_pages():
    label = "michigan-court-rules.pages.jsonl → rules_text"
    print(f"\n{'='*60}\n[1] {label}\n{'='*60}")
    fpath = r"C:\Users\andre\LitigationOS\03_LEGAL_AUTHORITIES\court_rules\michigan-court-rules.pages.jsonl"
    try:
        conn = connect_db()
        # rules_text schema: id INTEGER PK, rule TEXT, chapter TEXT, context TEXT, source_doc TEXT
        rows = []
        with open(fpath, "r", encoding="utf-8", errors="replace") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                rec = json.loads(line)
                page = rec.get("page", 0)
                text = rec.get("text", "")
                doc_path = rec.get("doc_path", "")
                sha = rec.get("doc_sha256", "")
                # Use page as a pseudo-rule identifier
                rule_id = f"MCR-PAGE-{page}"
                chapter = ""
                # Try to extract chapter from text
                ch_match = re.search(r"Chapter\s+(\d+)", text[:200])
                if ch_match:
                    chapter = f"Chapter {ch_match.group(1)}"
                rows.append((rule_id, chapter, text, f"{doc_path}|sha256:{sha[:16]}"))

        # INSERT OR IGNORE (rule is the natural key here)
        inserted = 0
        for r in rows:
            try:
                conn.execute(
                    "INSERT OR IGNORE INTO rules_text (rule, chapter, context, source_doc) VALUES (?,?,?,?)",
                    r,
                )
                inserted += conn.total_changes  # approximate
            except sqlite3.IntegrityError:
                pass
        conn.commit()
        # Count actual rows
        count = conn.execute("SELECT COUNT(*) FROM rules_text WHERE rule LIKE 'MCR-PAGE-%'").fetchone()[0]
        conn.close()
        print(f"  ✓ Parsed {len(rows)} page records; ~{count} MCR-PAGE rows in rules_text")
        RESULTS[label] = f"{len(rows)} parsed, {count} MCR-PAGE rows"
    except Exception as e:
        print(f"  ✗ FAILED: {e}")
        traceback.print_exc()
        RESULTS[label] = f"FAILED: {e}"


# ═══════════════════════════════════════════════════════════════════
# 2. rules_authority_shards.jsonl → authority_shards
# ═══════════════════════════════════════════════════════════════════
def ingest_authority_shards():
    label = "rules_authority_shards.jsonl → authority_shards"
    print(f"\n{'='*60}\n[2] {label}\n{'='*60}")
    fpath = r"C:\Users\andre\LitigationOS\08_APPS\desktop\backend\evidence\watson\authority_store\rules_authority_shards.jsonl"
    try:
        conn = connect_db()
        conn.execute("""
            CREATE TABLE IF NOT EXISTS authority_shards (
                authority_id   TEXT NOT NULL,
                authority_type TEXT,
                citation       TEXT,
                pinpoint       TEXT,
                chapter        INTEGER,
                context_excerpt TEXT,
                source_doc     TEXT,
                source_extraction TEXT,
                _row_hash      TEXT UNIQUE
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_ashards_auth_id ON authority_shards(authority_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_ashards_citation ON authority_shards(citation)")

        rows = []
        with open(fpath, "r", encoding="utf-8", errors="replace") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                rec = json.loads(line)
                row_hash = md5(
                    f"{rec.get('authority_id','')}|{rec.get('context_excerpt','')[:100]}"
                )
                rows.append((
                    rec.get("authority_id", ""),
                    rec.get("authority_type", ""),
                    rec.get("citation", ""),
                    rec.get("pinpoint", ""),
                    rec.get("chapter", 0),
                    rec.get("context_excerpt", ""),
                    rec.get("source_doc", ""),
                    safe_json(rec.get("source_extraction")),
                    row_hash,
                ))

        conn.executemany(
            """INSERT OR IGNORE INTO authority_shards
               (authority_id, authority_type, citation, pinpoint, chapter,
                context_excerpt, source_doc, source_extraction, _row_hash)
               VALUES (?,?,?,?,?,?,?,?,?)""",
            rows,
        )
        conn.commit()
        count = conn.execute("SELECT COUNT(*) FROM authority_shards").fetchone()[0]
        conn.close()
        print(f"  ✓ Parsed {len(rows)} shards; {count} total rows in authority_shards")
        RESULTS[label] = f"{len(rows)} parsed, {count} in table"
    except Exception as e:
        print(f"  ✗ FAILED: {e}")
        traceback.print_exc()
        RESULTS[label] = f"FAILED: {e}"


# ═══════════════════════════════════════════════════════════════════
# 3. authorities_index.jsonl → authorities_index
# ═══════════════════════════════════════════════════════════════════
def ingest_authorities_index():
    label = "authorities_index.jsonl → authorities_index"
    print(f"\n{'='*60}\n[3] {label}\n{'='*60}")
    fpath = r"C:\Users\andre\LitigationOS\08_APPS\desktop\backend\evidence\watson\authority_store\authorities_index.jsonl"
    try:
        conn = connect_db()
        conn.execute("""
            CREATE TABLE IF NOT EXISTS authorities_index (
                id          TEXT,
                kind        TEXT,
                source_url  TEXT,
                meta        TEXT,
                _row_hash   TEXT UNIQUE
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_authidx_id ON authorities_index(id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_authidx_kind ON authorities_index(kind)")

        rows = []
        with open(fpath, "r", encoding="utf-8", errors="replace") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                rec = json.loads(line)
                row_hash = md5(f"{rec.get('id','')}|{rec.get('kind','')}|{rec.get('source_url','')}")
                rows.append((
                    rec.get("id", ""),
                    rec.get("kind", ""),
                    rec.get("source_url", ""),
                    safe_json(rec.get("meta")),
                    row_hash,
                ))

        conn.executemany(
            "INSERT OR IGNORE INTO authorities_index (id, kind, source_url, meta, _row_hash) VALUES (?,?,?,?,?)",
            rows,
        )
        conn.commit()
        count = conn.execute("SELECT COUNT(*) FROM authorities_index").fetchone()[0]
        conn.close()
        print(f"  ✓ Parsed {len(rows)} index entries; {count} total rows")
        RESULTS[label] = f"{len(rows)} parsed, {count} in table"
    except Exception as e:
        print(f"  ✗ FAILED: {e}")
        traceback.print_exc()
        RESULTS[label] = f"FAILED: {e}"


# ═══════════════════════════════════════════════════════════════════
# 4. nodes_authorities.csv → authorities_nodes
# ═══════════════════════════════════════════════════════════════════
def ingest_authorities_nodes():
    label = "nodes_authorities.csv → authorities_nodes"
    print(f"\n{'='*60}\n[4] {label}\n{'='*60}")
    fpath = r"C:\Users\andre\LitigationOS\08_APPS\desktop\backend\evidence\watson\authority_store\nodes_authorities.csv"
    try:
        conn = connect_db()
        # CSV header: id:ID,label,group,:LABEL,tokens
        conn.execute("""
            CREATE TABLE IF NOT EXISTS authorities_nodes (
                node_id     TEXT UNIQUE,
                label       TEXT,
                node_group  TEXT,
                node_label  TEXT,
                tokens      TEXT
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_authnodes_id ON authorities_nodes(node_id)")

        rows = []
        with open(fpath, "r", encoding="utf-8", errors="replace") as f:
            reader = csv.reader(f)
            header = next(reader)  # skip header
            for row in reader:
                if len(row) < 5:
                    row += [""] * (5 - len(row))
                rows.append((row[0], row[1], row[2], row[3], row[4]))

        conn.executemany(
            "INSERT OR IGNORE INTO authorities_nodes (node_id, label, node_group, node_label, tokens) VALUES (?,?,?,?,?)",
            rows,
        )
        conn.commit()
        count = conn.execute("SELECT COUNT(*) FROM authorities_nodes").fetchone()[0]
        conn.close()
        print(f"  ✓ Parsed {len(rows)} nodes; {count} total rows in authorities_nodes")
        RESULTS[label] = f"{len(rows)} parsed, {count} in table"
    except Exception as e:
        print(f"  ✗ FAILED: {e}")
        traceback.print_exc()
        RESULTS[label] = f"FAILED: {e}"


# ═══════════════════════════════════════════════════════════════════
# 5. authorities_edges.csv → authorities_edges
# ═══════════════════════════════════════════════════════════════════
def ingest_authorities_edges():
    label = "authorities_edges.csv → authorities_edges"
    print(f"\n{'='*60}\n[5] {label}\n{'='*60}")
    fpath = r"C:\Users\andre\LitigationOS\08_APPS\desktop\backend\evidence\watson\authority_store\authorities_edges.csv"
    try:
        conn = connect_db()
        # CSV header: src,dst,relation,weight,notes
        conn.execute("""
            CREATE TABLE IF NOT EXISTS authorities_edges (
                src       TEXT NOT NULL,
                dst       TEXT NOT NULL,
                relation  TEXT,
                weight    REAL,
                notes     TEXT,
                _row_hash TEXT UNIQUE
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_authedges_src ON authorities_edges(src)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_authedges_dst ON authorities_edges(dst)")

        rows = []
        with open(fpath, "r", encoding="utf-8", errors="replace") as f:
            reader = csv.reader(f)
            header = next(reader)
            for row in reader:
                if len(row) < 5:
                    row += [""] * (5 - len(row))
                row_hash = md5(f"{row[0]}|{row[1]}|{row[2]}")
                weight = 0.0
                try:
                    weight = float(row[3])
                except (ValueError, IndexError):
                    pass
                rows.append((row[0], row[1], row[2], weight, row[4], row_hash))

        conn.executemany(
            "INSERT OR IGNORE INTO authorities_edges (src, dst, relation, weight, notes, _row_hash) VALUES (?,?,?,?,?,?)",
            rows,
        )
        conn.commit()
        count = conn.execute("SELECT COUNT(*) FROM authorities_edges").fetchone()[0]
        conn.close()
        print(f"  ✓ Parsed {len(rows)} edges; {count} total rows in authorities_edges")
        RESULTS[label] = f"{len(rows)} parsed, {count} in table"
    except Exception as e:
        print(f"  ✗ FAILED: {e}")
        traceback.print_exc()
        RESULTS[label] = f"FAILED: {e}"


# ═══════════════════════════════════════════════════════════════════
# 6. LEGAL_AUTHORITY_REFERENCE_COMPREHENSIVE.md → legal_reference_docs
# ═══════════════════════════════════════════════════════════════════
def ingest_legal_reference_md():
    label = "LEGAL_AUTHORITY_REFERENCE_COMPREHENSIVE.md → legal_reference_docs"
    print(f"\n{'='*60}\n[6] {label}\n{'='*60}")
    fpath = r"C:\Users\andre\Scans\LEGAL_AUTHORITY_REFERENCE_COMPREHENSIVE.md"
    try:
        conn = connect_db()
        conn.execute("""
            CREATE TABLE IF NOT EXISTS legal_reference_docs (
                section_id    TEXT UNIQUE,
                heading_level INTEGER,
                heading       TEXT,
                body          TEXT,
                source_file   TEXT
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_lrd_heading ON legal_reference_docs(heading)")

        with open(fpath, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()

        # Parse markdown sections by headings
        lines = content.split("\n")
        sections = []
        current_heading = ""
        current_level = 0
        current_body_lines = []

        def flush_section():
            if current_heading:
                body = "\n".join(current_body_lines).strip()
                sec_id = md5(f"{current_heading}|{body[:100]}")
                sections.append((sec_id, current_level, current_heading, body, os.path.basename(fpath)))

        for line in lines:
            heading_match = re.match(r"^(#{1,6})\s+(.*)", line)
            if heading_match:
                flush_section()
                current_level = len(heading_match.group(1))
                current_heading = heading_match.group(2).strip()
                current_body_lines = []
            else:
                current_body_lines.append(line)

        flush_section()  # last section

        conn.executemany(
            "INSERT OR IGNORE INTO legal_reference_docs (section_id, heading_level, heading, body, source_file) VALUES (?,?,?,?,?)",
            sections,
        )
        conn.commit()
        count = conn.execute("SELECT COUNT(*) FROM legal_reference_docs").fetchone()[0]
        conn.close()
        print(f"  ✓ Parsed {len(sections)} sections; {count} total rows in legal_reference_docs")
        RESULTS[label] = f"{len(sections)} parsed, {count} in table"
    except Exception as e:
        print(f"  ✗ FAILED: {e}")
        traceback.print_exc()
        RESULTS[label] = f"FAILED: {e}"


# ═══════════════════════════════════════════════════════════════════
# 7. TONS OF COURT RULES AND LAWS.json → court_rule_graphs
#    (malformed JSON — extract id/label node pairs via regex)
# ═══════════════════════════════════════════════════════════════════
def ingest_court_rule_graphs():
    label = "TONS OF COURT RULES AND LAWS.json → court_rule_graphs"
    print(f"\n{'='*60}\n[7] {label}\n{'='*60}")
    fpath = r"C:\Users\andre\LitigationOS\08_APPS\desktop\backend\evidence\watson\court_rule_graphs\TONS OF COURT RULES AND LAWS.json"
    try:
        conn = connect_db()
        conn.execute("""
            CREATE TABLE IF NOT EXISTS court_rule_graphs (
                node_id   TEXT,
                label     TEXT,
                source_file TEXT,
                _row_hash TEXT UNIQUE
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_crg_node ON court_rule_graphs(node_id)")

        with open(fpath, "r", encoding="utf-8", errors="replace") as f:
            lines = f.readlines()

        # Extract id/label pairs from the malformed JSON
        nodes = []
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            id_match = re.search(r'"id":\s*"([^"]*)"', line)
            if id_match:
                node_id = id_match.group(1)
                label_val = ""
                if i + 1 < len(lines):
                    label_match = re.search(r'"label":\s*"([^"]*)"', lines[i + 1].strip())
                    if label_match:
                        label_val = label_match.group(1)
                row_hash = md5(f"{node_id}|{label_val}")
                nodes.append((node_id, label_val, "TONS OF COURT RULES AND LAWS.json", row_hash))
            i += 1

        # Batch insert
        BATCH = 5000
        for start in range(0, len(nodes), BATCH):
            batch = nodes[start : start + BATCH]
            conn.executemany(
                "INSERT OR IGNORE INTO court_rule_graphs (node_id, label, source_file, _row_hash) VALUES (?,?,?,?)",
                batch,
            )
        conn.commit()
        count = conn.execute("SELECT COUNT(*) FROM court_rule_graphs").fetchone()[0]
        conn.close()
        print(f"  ✓ Extracted {len(nodes)} nodes; {count} total rows in court_rule_graphs")
        RESULTS[label] = f"{len(nodes)} extracted, {count} in table"
    except Exception as e:
        print(f"  ✗ FAILED: {e}")
        traceback.print_exc()
        RESULTS[label] = f"FAILED: {e}"


# ═══════════════════════════════════════════════════════════════════
# 8. CLAIMS.json → claims
# ═══════════════════════════════════════════════════════════════════
def ingest_claims():
    label = "CLAIMS.json → claims"
    print(f"\n{'='*60}\n[8] {label}\n{'='*60}")
    fpath = r"C:\Users\andre\LitigationOS\08_APPS\desktop\backend\evidence\watson\exparte_suspension_analysis_append\CLAIMS.json"
    try:
        conn = connect_db()
        conn.execute("""
            CREATE TABLE IF NOT EXISTS claims (
                claim_id        TEXT UNIQUE,
                issue_id        TEXT,
                doc             TEXT,
                line_no         INTEGER,
                classification  TEXT,
                actor           TEXT,
                proposition     TEXT,
                affirmative_counter_proposition TEXT,
                evidence_targets TEXT,
                status          TEXT,
                generated_at    TEXT,
                classifier_version TEXT
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_claims_issue ON claims(issue_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_claims_class ON claims(classification)")

        with open(fpath, "r", encoding="utf-8", errors="replace") as f:
            data = json.load(f)

        generated_at = data.get("generated_at", "")
        classifier_version = data.get("classifier_version", "")
        claims_list = data.get("claims", [])

        rows = []
        for c in claims_list:
            rows.append((
                c.get("claim_id", ""),
                c.get("issue_id", ""),
                c.get("doc", ""),
                c.get("line_no", 0),
                c.get("classification", ""),
                c.get("actor", ""),
                c.get("proposition", ""),
                c.get("affirmative_counter_proposition", ""),
                safe_json(c.get("evidence_targets")),
                c.get("status", ""),
                generated_at,
                classifier_version,
            ))

        conn.executemany(
            """INSERT OR IGNORE INTO claims
               (claim_id, issue_id, doc, line_no, classification, actor,
                proposition, affirmative_counter_proposition, evidence_targets,
                status, generated_at, classifier_version)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
            rows,
        )
        conn.commit()
        count = conn.execute("SELECT COUNT(*) FROM claims").fetchone()[0]
        conn.close()
        print(f"  ✓ Parsed {len(rows)} claims; {count} total rows in claims")
        RESULTS[label] = f"{len(rows)} parsed, {count} in table"
    except Exception as e:
        print(f"  ✗ FAILED: {e}")
        traceback.print_exc()
        RESULTS[label] = f"FAILED: {e}"


# ═══════════════════════════════════════════════════════════════════
# 9. CLAIMS_MATRIX.csv → claims_matrix
# ═══════════════════════════════════════════════════════════════════
def ingest_claims_matrix():
    label = "CLAIMS_MATRIX.csv → claims_matrix"
    print(f"\n{'='*60}\n[9] {label}\n{'='*60}")
    fpath = r"C:\Users\andre\LitigationOS\08_APPS\desktop\backend\evidence\watson\exparte_suspension_analysis_append\CLAIMS_MATRIX.csv"
    try:
        conn = connect_db()
        # CSV header: claim_id,issue_id,doc,line_no,classification,actor,status,proposition,affirmative_counter_proposition
        conn.execute("""
            CREATE TABLE IF NOT EXISTS claims_matrix (
                claim_id        TEXT,
                issue_id        TEXT,
                doc             TEXT,
                line_no         INTEGER,
                classification  TEXT,
                actor           TEXT,
                status          TEXT,
                proposition     TEXT,
                affirmative_counter_proposition TEXT,
                _row_hash       TEXT UNIQUE
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_cmatrix_claim ON claims_matrix(claim_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_cmatrix_issue ON claims_matrix(issue_id)")

        rows = []
        with open(fpath, "r", encoding="utf-8", errors="replace") as f:
            reader = csv.DictReader(f)
            for row in reader:
                line_no = 0
                try:
                    line_no = int(row.get("line_no", 0) or 0)
                except ValueError:
                    pass
                row_hash = md5(
                    f"{row.get('claim_id','')}|{row.get('proposition','')[:50]}"
                )
                rows.append((
                    row.get("claim_id", ""),
                    row.get("issue_id", ""),
                    row.get("doc", ""),
                    line_no,
                    row.get("classification", ""),
                    row.get("actor", ""),
                    row.get("status", ""),
                    row.get("proposition", ""),
                    row.get("affirmative_counter_proposition", ""),
                    row_hash,
                ))

        conn.executemany(
            """INSERT OR IGNORE INTO claims_matrix
               (claim_id, issue_id, doc, line_no, classification, actor,
                status, proposition, affirmative_counter_proposition, _row_hash)
               VALUES (?,?,?,?,?,?,?,?,?,?)""",
            rows,
        )
        conn.commit()
        count = conn.execute("SELECT COUNT(*) FROM claims_matrix").fetchone()[0]
        conn.close()
        print(f"  ✓ Parsed {len(rows)} matrix rows; {count} total rows in claims_matrix")
        RESULTS[label] = f"{len(rows)} parsed, {count} in table"
    except Exception as e:
        print(f"  ✗ FAILED: {e}")
        traceback.print_exc()
        RESULTS[label] = f"FAILED: {e}"


# ═══════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════
def main():
    start = time.time()
    print(f"╔══════════════════════════════════════════════════════════╗")
    print(f"║  LitigationOS · Mega Ingest Pipeline                   ║")
    print(f"║  DB: {DB_PATH}")
    print(f"║  Started: {datetime.now().isoformat()}")
    print(f"╚══════════════════════════════════════════════════════════╝")

    ingest_michigan_court_rules_pages()   # 1
    ingest_authority_shards()             # 2
    ingest_authorities_index()            # 3
    ingest_authorities_nodes()            # 4
    ingest_authorities_edges()            # 5
    ingest_legal_reference_md()           # 6
    ingest_court_rule_graphs()            # 7
    ingest_claims()                       # 8
    ingest_claims_matrix()                # 9

    elapsed = time.time() - start
    print(f"\n{'='*60}")
    print(f"  MEGA INGEST COMPLETE — {elapsed:.1f}s")
    print(f"{'='*60}")
    for k, v in RESULTS.items():
        status = "✓" if "FAILED" not in v else "✗"
        print(f"  {status} {k}")
        print(f"      {v}")

    # Final table counts
    print(f"\n{'='*60}")
    print(f"  FINAL TABLE ROW COUNTS (new tables)")
    print(f"{'='*60}")
    conn = connect_db()
    new_tables = [
        "authority_shards", "authorities_index", "authorities_nodes",
        "authorities_edges", "legal_reference_docs", "court_rule_graphs",
        "claims", "claims_matrix",
    ]
    for tbl in new_tables:
        try:
            cnt = conn.execute(f"SELECT COUNT(*) FROM {tbl}").fetchone()[0]
            print(f"  {tbl:30s} → {cnt:>8,} rows")
        except Exception as e:
            print(f"  {tbl:30s} → ERROR: {e}")

    # Also report rules_text MCR-PAGE count
    try:
        cnt = conn.execute("SELECT COUNT(*) FROM rules_text WHERE rule LIKE 'MCR-PAGE-%'").fetchone()[0]
        print(f"  {'rules_text (MCR-PAGE-*)':30s} → {cnt:>8,} rows")
    except:
        pass

    conn.close()
    print(f"\nDone.")


if __name__ == "__main__":
    main()
