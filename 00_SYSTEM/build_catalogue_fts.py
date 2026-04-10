"""Build FTS5 index across all catalogue tables for unified search."""
import sqlite3

DB = r"C:\Users\andre\LitigationOS\litigation_context.db"

def main():
    conn = sqlite3.connect(DB)
    conn.execute("PRAGMA busy_timeout=60000")
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA cache_size=-32000")

    conn.execute("DROP TABLE IF EXISTS catalogue_fts")
    conn.execute("""CREATE VIRTUAL TABLE catalogue_fts USING fts5(
        source_table, item_id, searchable_text, category
    )""")

    inserts = []

    def add_rows(table, query, category):
        for r in conn.execute(query).fetchall():
            item_id = str(r[0])
            text = " ".join(str(x) for x in r if x is not None)
            inserts.append((table, item_id, text, category))

    # Each table with actual column names
    add_rows("court_abbreviations",
             "SELECT abbreviation, full_name, tier, notes FROM court_abbreviations",
             "courts")
    add_rows("case_type_codes",
             "SELECT code, label, court_type, description FROM case_type_codes",
             "case_types")
    add_rows("best_interest_factors",
             "SELECT factor_letter, mcl_subsection, description, strategic_note FROM best_interest_factors",
             "custody")
    add_rows("constitutional_provisions",
             "SELECT provision, source, concept, description, relevance FROM constitutional_provisions",
             "constitutional")
    add_rows("foc_duties",
             "SELECT mcl_section, duty, description, critical_note FROM foc_duties",
             "foc")
    add_rows("judicial_accountability",
             "SELECT mechanism, authority, description, process_steps FROM judicial_accountability",
             "judicial")
    add_rows("appellate_pathways",
             "SELECT route_name, from_court, to_court, authority, standard, notes FROM appellate_pathways",
             "appellate")
    add_rows("legal_statutes",
             "SELECT citation, title, subject, description FROM legal_statutes",
             "statutes")
    add_rows("michigan_case_law",
             "SELECT case_name, citation, holding FROM michigan_case_law",
             "case_law")

    conn.executemany(
        "INSERT INTO catalogue_fts(source_table, item_id, searchable_text, category) VALUES (?,?,?,?)",
        inserts,
    )
    conn.commit()

    cnt = conn.execute("SELECT COUNT(*) FROM catalogue_fts").fetchone()[0]
    print(f"catalogue_fts: {cnt} entries indexed")

    # Test searches
    tests = [
        "custody OR parenting",
        "disqualification OR bias",
        "appeal OR appellate",
        "due process",
        "FOC OR friend",
        "PPO OR protection",
    ]
    for q in tests:
        results = conn.execute(
            "SELECT source_table, item_id FROM catalogue_fts WHERE catalogue_fts MATCH ? LIMIT 5",
            (q,),
        ).fetchall()
        hits = [f"{r[0]}/{r[1]}" for r in results]
        print(f'  "{q}": {len(results)} hits -> {hits}')

    conn.close()
    print("\n=== FTS5 CATALOGUE INDEX COMPLETE ===")


if __name__ == "__main__":
    main()
