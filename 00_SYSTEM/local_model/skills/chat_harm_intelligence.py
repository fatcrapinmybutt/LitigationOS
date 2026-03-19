"""
Skill: chat_harm_intelligence
Provides deep analysis of 26,409 extracted harms from Andrew's 51,868 ChatGPT messages.
Categories: PARENTAL_ALIENATION, EX_PARTE_ABUSE, JUDICIAL_BIAS, FALSE_IMPRISONMENT,
PPO_WEAPONIZATION, FINANCIAL_HARM, EMOTIONAL_PSYCHOLOGICAL, CONSPIRACY_COORDINATION,
HOUSING_HARM, WATSON_FAMILY_INTIMIDATION, ATTORNEY_MISCONDUCT, PROCEDURAL_VIOLATIONS,
CHILD_WELFARE

Adversaries: Emily Watson (3,949), Shady Oaks (4,580), Judge McNeill (1,530),
Housing Entity (1,343), FOC (1,181), Watson Family (758), Albert Watson (305),
Lori Watson (280), Ron Berry (280), Homes of America (211), Alden Global (199),
Mandi Martini (80), Cody Watson (65), Pamela Rusco (61), HealthWest (43)
"""
import sqlite3
import json

SKILL_NAME = "chat_harm_intelligence"
SKILL_VERSION = "1.0.0"

DB_PATH = r"C:\Users\andre\LitigationOS\litigation_context.db"

def get_conn():
    return sqlite3.connect(DB_PATH)

def harm_search(query: str, adversary: str = None, category: str = None, 
                min_severity: int = 5, limit: int = 50) -> dict:
    """Search extracted harms by keyword, adversary, and/or category."""
    conn = get_conn()
    cur = conn.cursor()
    
    conditions = ["severity >= ?"]
    params = [min_severity]
    
    if adversary:
        conditions.append("adversary LIKE ?")
        params.append(f"%{adversary}%")
    
    if category:
        conditions.append("category = ?")
        params.append(category)
    
    where = " AND ".join(conditions)
    
    if query:
        # Use FTS if available
        try:
            cur.execute(f"""
                SELECT eh.id, eh.category, eh.adversary, eh.date_ref, 
                       eh.description, eh.severity, eh.constitutional_violation,
                       eh.filing_stacks
                FROM extracted_harms eh
                JOIN extracted_harms_fts fts ON eh.rowid = fts.rowid
                WHERE fts.extracted_harms_fts MATCH ? AND {where}
                ORDER BY eh.severity DESC
                LIMIT ?
            """, [query] + params + [limit])
        except:
            conditions.append("(andrew_quote LIKE ? OR description LIKE ?)")
            params.extend([f"%{query}%", f"%{query}%"])
            where = " AND ".join(conditions)
            cur.execute(f"""
                SELECT id, category, adversary, date_ref, description, 
                       severity, constitutional_violation, filing_stacks
                FROM extracted_harms WHERE {where}
                ORDER BY severity DESC LIMIT ?
            """, params + [limit])
    else:
        cur.execute(f"""
            SELECT id, category, adversary, date_ref, description, 
                   severity, constitutional_violation, filing_stacks
            FROM extracted_harms WHERE {where}
            ORDER BY severity DESC LIMIT ?
        """, params + [limit])
    
    results = []
    for row in cur.fetchall():
        results.append({
            "id": row[0], "category": row[1], "adversary": row[2],
            "date_ref": row[3], "description": row[4], "severity": row[5],
            "constitutional_violation": row[6], "filing_stacks": row[7]
        })
    
    conn.close()
    return {"count": len(results), "results": results}


def adversary_profile(adversary_name: str) -> dict:
    """Get comprehensive adversary harm profile."""
    conn = get_conn()
    cur = conn.cursor()
    
    # Get summary
    cur.execute("SELECT * FROM adversary_harm_summary WHERE adversary LIKE ?",
                (f"%{adversary_name}%",))
    summary = cur.fetchone()
    
    # Get harm breakdown
    cur.execute("""
        SELECT category, COUNT(*) as cnt, AVG(severity) as avg_sev,
               MAX(severity) as max_sev
        FROM extracted_harms WHERE adversary LIKE ?
        GROUP BY category ORDER BY cnt DESC
    """, (f"%{adversary_name}%",))
    categories = [{"category": r[0], "count": r[1], "avg_severity": round(r[2], 1), 
                   "max_severity": r[3]} for r in cur.fetchall()]
    
    # Get top harms
    cur.execute("""
        SELECT date_ref, category, substr(andrew_quote, 1, 300), 
               severity, constitutional_violation
        FROM extracted_harms WHERE adversary LIKE ?
        ORDER BY severity DESC LIMIT 20
    """, (f"%{adversary_name}%",))
    top_harms = [{"date": r[0], "category": r[1], "quote": r[2],
                  "severity": r[3], "violation": r[4]} for r in cur.fetchall()]
    
    conn.close()
    return {
        "adversary": adversary_name,
        "summary": summary,
        "harm_categories": categories,
        "top_harms": top_harms,
        "total_harms": sum(c["count"] for c in categories)
    }


def harm_to_filing_map(category: str = None, adversary: str = None) -> dict:
    """Map harms to appropriate filing stacks."""
    conn = get_conn()
    cur = conn.cursor()
    
    conditions = []
    params = []
    if category:
        conditions.append("category = ?")
        params.append(category)
    if adversary:
        conditions.append("adversary LIKE ?")
        params.append(f"%{adversary}%")
    
    where = " AND ".join(conditions) if conditions else "1=1"
    
    cur.execute(f"""
        SELECT filing_stacks, category, COUNT(*) as cnt
        FROM extracted_harms WHERE {where}
        GROUP BY filing_stacks, category
        ORDER BY cnt DESC
    """, params)
    
    mapping = {}
    for row in cur.fetchall():
        stacks = row[0] or ""
        for s in stacks.split(","):
            s = s.strip()
            if s:
                if s not in mapping:
                    mapping[s] = []
                mapping[s].append({"category": row[1], "count": row[2]})
    
    conn.close()
    return {"filing_stack_mapping": mapping}


def chat_evidence_extract(keywords: list, limit: int = 100) -> dict:
    """Extract Andrew's own words as evidence from chat messages."""
    conn = get_conn()
    cur = conn.cursor()
    
    results = []
    for kw in keywords:
        cur.execute("""
            SELECT date_ref, adversary, category, substr(andrew_quote, 1, 500),
                   severity, conversation_title
            FROM extracted_harms
            WHERE andrew_quote LIKE ?
            ORDER BY severity DESC LIMIT ?
        """, (f"%{kw}%", limit // len(keywords) if keywords else limit))
        
        for r in cur.fetchall():
            results.append({
                "keyword": kw, "date": r[0], "adversary": r[1],
                "category": r[2], "quote": r[3], "severity": r[4],
                "conversation": r[5]
            })
    
    conn.close()
    return {"keyword_count": len(keywords), "results": results}


def harm_statistics() -> dict:
    """Get comprehensive harm statistics."""
    conn = get_conn()
    cur = conn.cursor()
    
    stats = {}
    
    cur.execute("SELECT COUNT(*) FROM extracted_harms")
    stats["total_harms"] = cur.fetchone()[0]
    
    cur.execute("SELECT category, COUNT(*) FROM extracted_harms GROUP BY category ORDER BY COUNT(*) DESC")
    stats["by_category"] = {r[0]: r[1] for r in cur.fetchall()}
    
    cur.execute("SELECT adversary, COUNT(*) FROM extracted_harms GROUP BY adversary ORDER BY COUNT(*) DESC")
    stats["by_adversary"] = {r[0]: r[1] for r in cur.fetchall()}
    
    cur.execute("SELECT severity, COUNT(*) FROM extracted_harms GROUP BY severity ORDER BY severity DESC")
    stats["by_severity"] = {r[0]: r[1] for r in cur.fetchall()}
    
    cur.execute("SELECT AVG(severity) FROM extracted_harms")
    stats["avg_severity"] = round(cur.fetchone()[0], 2)
    
    conn.close()
    return stats


# JSON-RPC method registry
METHODS = {
    "harm_search": harm_search,
    "adversary_profile": adversary_profile,
    "harm_to_filing_map": harm_to_filing_map,
    "chat_evidence_extract": chat_evidence_extract,
    "harm_statistics": harm_statistics,
}

def handle_request(method: str, params: dict = None) -> dict:
    if method not in METHODS:
        return {"error": f"Unknown method: {method}"}
    try:
        return METHODS[method](**(params or {}))
    except Exception as e:
        return {"error": str(e)}
