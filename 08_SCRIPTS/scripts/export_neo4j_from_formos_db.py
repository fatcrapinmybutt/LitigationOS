#!/usr/bin/env python3
"""
export_neo4j_from_formos_db.py

Exports SQLite FormOS DB content into Neo4j import-friendly CSVs:
- nodes_forms.csv
- nodes_documents.csv
- nodes_instructions.csv
- edges_has_doc.csv
- edges_has_instructions.csv

This is intentionally minimal; extend with specs, AKN templates, compliance profiles, stacks.
"""

from __future__ import annotations
import argparse, csv, sqlite3
from pathlib import Path

def safe_mkdir(p: Path) -> None:
    p.mkdir(parents=True, exist_ok=True)

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", required=True, help="Path to formos SQLite DB")
    ap.add_argument("--out", required=True, help="Output folder")
    args = ap.parse_args()

    db = Path(args.db)
    out = Path(args.out)
    safe_mkdir(out)

    con = sqlite3.connect(str(db))

    forms = con.execute("SELECT form_id, form_code_guess, title_guess, jurisdiction_guess, court_level_guess, family_guess, revision_guess, doctype_guess FROM forms").fetchall()
    docs = con.execute("SELECT doc_id, sha256, ext, mime, original_path, stored_object_path FROM documents").fetchall()
    instr = con.execute("SELECT instr_id, form_id, instruction_fulltext_path, instruction_sha256 FROM form_instructions").fetchall()

    with (out/"nodes_forms.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["form_id:ID(Form)", "form_code", "title", "jurisdiction", "court_level", "family", "revision", "doctype", ":LABEL"])
        for r in forms:
            w.writerow([*r, "Form"])

    with (out/"nodes_documents.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["doc_id:ID(Document)", "sha256", "ext", "mime", "original_path", "stored_object_path", ":LABEL"])
        for r in docs:
            w.writerow([*r, "Document"])

    with (out/"nodes_instructions.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["instr_id:ID(Instructions)", "form_id", "path", "sha256", ":LABEL"])
        for instr_id, form_id, path, sha in instr:
            w.writerow([instr_id, form_id, path, sha, "Instructions"])

    # edges
    with (out/"edges_has_instructions.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow([":START_ID(Form)", ":END_ID(Instructions)", ":TYPE"])
        for instr_id, form_id, *_ in instr:
            w.writerow([form_id, instr_id, "HAS_INSTRUCTIONS"])

    # form->doc
    fdoc = con.execute("SELECT form_id, doc_id FROM forms").fetchall()
    with (out/"edges_has_doc.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow([":START_ID(Form)", ":END_ID(Document)", ":TYPE"])
        for form_id, doc_id in fdoc:
            w.writerow([form_id, doc_id, "HAS_SOURCE_DOC"])

    con.close()
    print(f"OK: exported to {out}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
