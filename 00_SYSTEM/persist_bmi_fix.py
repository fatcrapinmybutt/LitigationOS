"""Fix BMI persistence with correct schema."""
import sqlite3, datetime

DB = r"C:\Users\andre\LitigationOS\litigation_context.db"

def main():
    conn = sqlite3.connect(DB, timeout=60)
    conn.execute("PRAGMA busy_timeout=60000")
    conn.execute("PRAGMA journal_mode=WAL")
    
    data = [
        ("MARRIAGE", "Jenny McNeill", "Cavan Berry", "Spouse — same residential address 4084 Oak Hollow Ct Norton Shores. Both NIU Law (1996/1998). Consecutively barred.", "MCNEILLEXPARTE harvest", "CONFIRMED", "Kyle McNeill Berry (~24) same address confirms familial unit."),
        ("OFFICE_NEXUS", "Cavan Berry", "Pamela Rusco", "Same office address 990 Terrace St. Berry=Attorney Magistrate 60th District. Rusco=FOC. Supervisory/collegial nexus.", "MCNEILLEXPARTE harvest", "CONFIRMED", "Single building houses FOC + 60th District + Berry office."),
        ("POTENTIAL_FAMILY", "Ronald Berry", "Cavan Berry", "Shared surname + both Norton Shores (~24K pop). Shannon Patrick Berry also in area. If related within 3rd degree: MCR 2.003(C)(1)(b) MANDATORY DISQUALIFICATION.", "MCNEILLEXPARTE harvest", "HIGH", "Never disclosed by McNeill. Requires genealogical verification."),
        ("EX_PARTE_BIAS", "Jenny McNeill", "Emily Watson", "52 ex parte orders. 100% favored Watson. 0% favored Pigors. 26.8% ex parte rate vs 5% national norm (5-6X elevated).", "MCNEILLEXPARTE harvest statistical analysis", "CONFIRMED", "Constitutional due process violation. Pattern too extreme for coincidence."),
        ("EVIDENCE_TAMPERING", "Jenny McNeill", "Court Staff", "'Yes, I had my staff listen to it' — personal acquisition of disputed evidence outside noticed hearing. Canon 3A(6) direct violation.", "Hearing transcript / MCNEILLEXPARTE analysis", "CONFIRMED", "Ex parte evidence acquisition. Instructed email to secretary not Clerk."),
        ("UNAUTHENTICATED_EVIDENCE", "Emily Watson", "Jenny McNeill", "Aug 5 2025: Emily submitted USB recording admitted WITHOUT MRE 901(A) authentication. NOT verified for MCL 750.539d. Five ex parte orders based on unverified evidence.", "MCNEILLEXPARTE harvest", "CONFIRMED", "Andrew's lawful recording REJECTED while Emily's unauthenticated recording ACCEPTED."),
        ("HOSTILE_STATEMENTS", "Jenny McNeill", "Andrew Pigors", "Called Andrew 'a liar' and 'crazy' on record. Acknowledged causing harm then weaponized it: 'concerns regarding mental health from job loss, homelessness and family loss'", "Court orders / hearing transcripts", "CONFIRMED", "7+ muting incidents. Told Andrew to 'shut my mouth'. Systematic suppression."),
        ("FILING_BOND_ABUSE", "Jenny McNeill", "Andrew Pigors", "$250 bond imposed for filing motions WITHOUT MCR 2.625 vexatious litigant finding. No statutory authority. Effective access-to-courts bar.", "Court orders", "CONFIRMED", "Canon 3A(4) + 1st Amendment violation."),
        ("DISQUALIFICATION_ERROR", "Jenny McNeill", "Kenneth Hoopes", "Sept 25 2024: Andrew filed disqualification motion. McNeill denied it herself without referring to Chief Judge per MCR 2.003(D)(1). PROCEDURAL ERROR PRESERVED.", "Motion records", "CONFIRMED", "But Chief Judge Hoopes = former law partner = also conflicted."),
        ("ENFORCEMENT_ASYMMETRY", "Jenny McNeill", "Emily Watson", "27+ Emily parenting time violations: ZERO enforcement. Andrew 6 motions July 16 2024: sanctioned as 'frivolous harassment'. Canon 3B violation.", "Docket records / motions", "CONFIRMED", "Pattern proves systematic favoritism, not case-by-case discretion."),
        ("CONSPIRACY_CHAIN", "Ladas", "Full Cartel", "Ladas(founder)->Ladas-Hoopes(daughter,60th Judge)->Hoopes(spouse,Chief Judge)->McNeill(former partner)->Berry(spouse,atty)->990 Terrace(FOC/60th)->Rusco(FOC). Single chain controls ALL courts Andrew faces.", "MCNEILLEXPARTE harvest / public records", "CONFIRMED", "435 Whitehall Rd = former Ladas Hoopes & McNeill law firm."),
        ("CANON_VIOLATIONS", "Jenny McNeill", "Judicial Tenure Commission", "1,127 MCJC violations: Canon 3A(1)=560, Canon 3A(6)=169, Canon 3C=167, Canon 3A(5)=108. McNeill = 62.2% of ALL case violations.", "MCNEILLEXPARTE statistical analysis", "CONFIRMED", "Sufficient for JTC complaint. Filing readiness COMPLETE."),
        ("NO_BEST_INTEREST", "Jenny McNeill", "L.D.W.", "MCL 722.27a REQUIRES written best interest findings in all custody mods. McNeill issued ZERO findings despite multiple orders. Canon 3A(1) violation.", "Court orders review", "CONFIRMED", "Critical appellate issue — abuse of discretion standard."),
        ("ZERO_14DAY_HEARINGS", "Jenny McNeill", "Andrew Pigors", "MCR 3.207(C)(5) MANDATES hearing on ex parte custody order within 14 days. McNeill conducted ZERO hearings within mandated window.", "Docket records", "CONFIRMED", "Systematic due process deprivation. Every ex parte order should have had a hearing."),
        ("AUG_8_PREMEDITATION", "Albert Watson", "Emily Watson", "Aug 7 NSPD NS2505044: Albert told police 'They want this documented so Emily can go tomorrow to get an Ex Parte order for full custody'. Aug 8: FIVE ex parte orders issued.", "NSPD report NS2505044", "CONFIRMED", "Direct evidence of premeditated custody grab. Conspiracy between family members."),
    ]
    
    inserted = 0
    for row in data:
        try:
            conn.execute(
                "INSERT INTO berry_mcneill_intelligence (connection_type, person_a, person_b, relationship, evidence_source, confidence, notes) VALUES (?,?,?,?,?,?,?)",
                row
            )
            inserted += 1
        except Exception as e:
            print(f"  [WARN] {e}")
    
    conn.commit()
    
    total = conn.execute("SELECT count(*) FROM berry_mcneill_intelligence").fetchone()[0]
    print(f"Inserted {inserted} rows. Total BMI: {total}")
    conn.close()

if __name__ == "__main__":
    main()
