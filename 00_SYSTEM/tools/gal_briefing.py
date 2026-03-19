#!/usr/bin/env python3
"""
Tool #109 — Guardian Ad Litem Briefing Package
===================================================
🆕 NOVEL TOOL — If court appoints a GAL, have the
briefing ready BEFORE the first meeting

Generates a professional, fact-based briefing for a GAL:
- Case overview (neutral presentation)
- Key evidence (pre-organized)
- Timeline of events
- Andrew's proposed parenting plan
- Questions Andrew wants the GAL to investigate

GALs are the judge's eyes and ears. Making a good
impression with organized materials = huge advantage.
"""
import sys, json, sqlite3
from pathlib import Path
from datetime import datetime

sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')

REPO = Path(r"C:\Users\andre\LitigationOS")
DB_PATH = REPO / "litigation_context.db"
REPORTS_DIR = REPO / "00_SYSTEM" / "reports"

def main():
    print("=" * 70)
    print("GUARDIAN AD LITEM BRIEFING PACKAGE — Tool #109")
    print("=" * 70)
    
    conn = sqlite3.connect(str(DB_PATH), timeout=60)
    conn.execute("PRAGMA busy_timeout=60000")
    conn.execute("PRAGMA journal_mode=WAL")
    
    # Get evidence counts
    counts = {}
    for table in ['evidence_quotes', 'judicial_violations', 'detected_contradictions']:
        try:
            r = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()
            counts[table] = r[0] if r else 0
        except:
            counts[table] = 0
    
    conn.close()
    
    lines = [
        "# 👨‍⚖️ GUARDIAN AD LITEM BRIEFING PACKAGE",
        f"*Prepared by: Andrew James Pigors (Pro Se Plaintiff)*",
        f"*Case: Pigors v. Watson, No. 2024-001507-DC*",
        f"*14th Circuit Court, Family Division, Muskegon County*",
        f"*Date: {datetime.now().strftime('%B %d, %Y')}*\n",
        "---\n",
        
        "## I. CASE OVERVIEW\n",
        "This is a custody/parenting time matter involving one minor child,",
        "L.D.W. (DOB: November 9, 2022). The father, Andrew Pigors, has been",
        "denied all parenting time since approximately [date]. The mother,",
        "Emily Watson, obtained a Personal Protection Order (2023-5907-PP)",
        "based on an allegation that Mr. Pigors threw a drinking straw near",
        "the child. No medical evidence, police report, or CPS investigation",
        "corroborated this allegation.\n",
        
        "## II. KEY FACTS FOR INVESTIGATION\n",
        "The following facts are supported by documentary evidence:\n",
        "### A. Parenting Time Denial",
        "- Father's parenting time has been completely suspended",
        "- No finding of clear and convincing evidence of harm per MCL 722.27a(3)",
        "- Father has consistently requested contact; mother has consistently denied/ignored",
        "",
        "### B. Best Interest Factors (MCL 722.23)",
        "| Factor | Father | Mother |",
        "|--------|--------|--------|",
        "| (a) Love/affection/emotional ties | Strong bond documented | Primary caretaker |",
        "| (b) Capacity for love/affection | Consistent requests for contact | Blocking contact |",
        "| (c) Capacity for food/clothing/medical | Employed, stable housing | Employed, stable housing |",
        "| (d) Home permanence | 1977 Whitehall Rd, N. Muskegon | 2160 Garland Dr, Norton Shores |",
        "| (e) Moral fitness | No criminal record | [Evidence of deception in filings] |",
        "| (f) Mental/physical health | Good | Good |",
        "| (g) Home/school/community | Stable | Stable |",
        "| (h) Child's preference | N/A — child under 4 | N/A |",
        "| (i) Willingness to facilitate | **100% — requests contact** | **Blocking all contact** |",
        "| (j) Domestic violence | No substantiated incidents | PPO based on straw allegation |",
        "| (k) Other factors | Pro se — fighting for child | Boyfriend (non-attorney) involved |",
        "| (l) Other factors | Documented 262K+ communications | — |",
        "",
        "### C. Evidence Available for Review\n",
        f"- {counts.get('evidence_quotes', 0):,} documented evidence items",
        f"- {counts.get('detected_contradictions', 0):,} documented contradictions in opposing party statements",
        "- Text message records",
        "- Email communications",
        "- Court filing records",
        "- ChatGPT/AI conversation exports (262K+ items)\n",
        
        "## III. WHAT WE ASK THE GAL TO INVESTIGATE\n",
        "1. **Interview L.D.W.** — Observe child's comfort level discussing father",
        "2. **Interview both parents** — Assess bonding, attachment, stability",
        "3. **Review the PPO basis** — Is a thrown straw sufficient for no-contact?",
        "4. **Assess Ronald Berry's role** — Non-attorney making legal decisions about L.D.W.",
        "5. **Evaluate communication patterns** — Who is facilitating vs. blocking?",
        "6. **Review mother's statements** — Compare filings to documented evidence",
        "7. **Observe both homes** — Standard home visits",
        "8. **Talk to L.D.W.'s providers** — Daycare, medical (with consent)\n",
        
        "## IV. PROPOSED PARENTING PLAN\n",
        "Andrew proposes the following, consistent with MCL 722.27a:\n",
        "### Immediate (Emergency)",
        "- Supervised parenting time 2x/week, 2 hours each",
        "- Gradually increase as comfort established",
        "- Professional supervisor if court prefers\n",
        "### Short-term (30-90 days)",
        "- Unsupervised parenting time every other weekend",
        "- One midweek evening (4 hours)",
        "- Phone/video calls on non-parenting days\n",
        "### Long-term",
        "- Standard parenting time per Muskegon County guidelines",
        "- Shared holidays per standard schedule",
        "- Joint legal custody (already ordered)\n",
        
        "## V. SUPPORTING DOCUMENTS\n",
        "The following are available for GAL review:",
        "- [ ] Complete text message record (Andrew-Emily)",
        "- [ ] Complete email correspondence",
        "- [ ] All court filings in both cases",
        "- [ ] Evidence of parenting time requests/denials",
        "- [ ] ChatGPT conversation exports",
        "- [ ] Financial records",
        "- [ ] Character references\n",
        
        "## VI. CONTACT INFORMATION\n",
        "**Andrew James Pigors**",
        "1977 Whitehall Road, Lot 17",
        "North Muskegon, MI 49445",
        "(231) 903-5690",
        "andrewjpigors@gmail.com\n",
        
        "*I am available for interviews at the GAL's convenience.*",
        "*All documents referenced herein are available upon request.*\n",
        
        "---",
        f"*GAL Briefing Package — Tool #109 — {sum(counts.values()):,} evidence items referenced*",
    ]
    
    md_path = REPORTS_DIR / "GAL_BRIEFING.md"
    md_path.write_text('\n'.join(lines), encoding='utf-8')
    
    json_path = REPORTS_DIR / "gal_briefing.json"
    json_path.write_text(json.dumps({
        'generated': datetime.now().isoformat(),
        'tool': 'GAL Briefing Package (#109)',
        'evidence_counts': counts,
        'best_interest_factors': 12,
        'investigation_requests': 8,
    }, indent=2), encoding='utf-8')
    
    print(f"\n✅ GAL Briefing Package generated")
    print(f"   Evidence referenced: {sum(counts.values()):,} items")
    print(f"   12 best interest factors + 8 investigation requests")
    print(f"   Reports: GAL_BRIEFING.md + gal_briefing.json")

if __name__ == '__main__':
    main()
