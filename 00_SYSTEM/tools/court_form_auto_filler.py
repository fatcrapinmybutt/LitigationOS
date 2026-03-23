#!/usr/bin/env python3
"""
Tool #270 — Court Form Auto-Filler
====================================
Generates pre-filled Michigan SCAO court forms as text documents ready for
printing/signing.  Forms are written to GENERATED_FILINGS/court_forms/.

Forms generated:
  MC 264  — Motion to Disqualify Judge
  CC 379  — Motion Regarding PPO
  CC 385  — Order on Motion Regarding PPO
  MC 230  — Ex Parte / TRO (Housing)
  MC 231  — Motion for Emergency Relief
  FOC 10  — Uniform Child Support Order (reference)
  MC 01   — Case Inventory Addendum
"""
import sys, os, json, sqlite3, textwrap
from datetime import datetime

sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'litigation_context.db')
REPORTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'reports')
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'GENERATED_FILINGS')
FORMS_DIR = os.path.join(OUTPUT_DIR, 'court_forms')


def s(v):
    return (v or "").lower()


def safe_query(conn, sql, params=()):
    try:
        return conn.execute(sql, params).fetchall()
    except Exception:
        return []


# ── Verified party information (NEVER fabricate) ──────────────────────────
PLAINTIFF = {
    'name': 'Andrew James Pigors',
    'role': 'Plaintiff, Pro Se',
    'address': '1977 Whitehall Road, Lot 17',
    'city_state_zip': 'North Muskegon, MI 49445',
    'phone': '(231) 903-5690',
    'email': 'andrewjpigors@gmail.com',
}
DEFENDANT = {
    'name': 'Emily A. Watson',
    'role': 'Defendant',
    'address': '2160 Garland Drive',
    'city_state_zip': 'Norton Shores, MI 49441',
}
JUDGE = 'Hon. Jenny L. McNeill'
COURT = '14th Judicial Circuit'
COUNTY = 'Muskegon'
DIVISION = 'Family Division'

CASES = {
    'custody': '2024-001507-DC',
    'ppo': '2023-5907-PP',
    'housing': '2025-002760-CZ',
}


def _sig_block():
    return textwrap.dedent(f"""\
    Date: _______________          ________________________________
                                   {PLAINTIFF['name']}, Pro Se Plaintiff
                                   {PLAINTIFF['address']}
                                   {PLAINTIFF['city_state_zip']}
                                   {PLAINTIFF['phone']}""")


def _header(case_number, form_number, form_title):
    return textwrap.dedent(f"""\
    {'=' * 72}
    {form_number} — {form_title}
    {'=' * 72}

    STATE OF MICHIGAN                           FILE NO. {case_number}
    {COURT}
    COUNTY OF {COUNTY.upper()}                          {DIVISION}

    {form_title.upper()}

    Case Name: PIGORS v WATSON
    Judge: {JUDGE}
    """)


# ── Form generators ──────────────────────────────────────────────────────

def gen_mc264(conn):
    """MC 264 — Motion/Stipulation to Disqualify Judge."""
    grounds = []
    rows = safe_query(conn,
        "SELECT strengths, gaps FROM filing_readiness WHERE vehicle_name LIKE '%disqualif%' OR vehicle_name LIKE '%F3%' LIMIT 5")
    for r in rows:
        if r['strengths']:
            grounds.append(str(r['strengths']))
    claim_rows = safe_query(conn,
        "SELECT proposition FROM claims WHERE proposition LIKE '%disqualif%' OR proposition LIKE '%bias%' OR proposition LIKE '%canon%' LIMIT 10")
    for r in claim_rows:
        if r['proposition']:
            grounds.append(str(r['proposition'])[:200])

    grounds_text = "\n   ".join(grounds[:8]) if grounds else "[VERIFY — confirm specific disqualification grounds]"

    txt = _header(CASES['custody'], 'MC 264', 'Motion to Disqualify Judge')
    txt += textwrap.dedent(f"""\
    1. I, {PLAINTIFF['name']}, move to disqualify the {JUDGE}
       from further proceedings in the above-captioned case.

    2. Grounds for Disqualification:

       {grounds_text}

       Applicable Court Rules:
       [ ] MCR 2.003(C)(1)(a) — Personal bias or prejudice concerning a party
       [ ] MCR 2.003(C)(1)(b) — Personal knowledge of disputed evidentiary facts
       [ ] MCR 2.003(C)(1)(c) — Attorney previously associated in the matter
       [ ] MCR 2.003(C)(1)(d) — Financial interest in the matter
       [ ] MCR 2.003(C)(1)(e) — Related to a party or attorney within third degree

    3. Supporting Facts:
       See attached Exhibit Binder with supporting evidence of judicial bias,
       ex parte communications, and Canon violations.

    4. This motion is timely filed within 14 days of discovery of grounds
       per MCR 2.003(D)(1).

    5. I request that this case be reassigned to a different judge pursuant to
       MCR 2.003(E).

    WHEREFORE, Plaintiff respectfully requests that this Court grant the
    motion and disqualify {JUDGE} from further proceedings.

    {_sig_block()}
    """)
    return ('MC_264', 'Motion to Disqualify Judge', CASES['custody'], 'F3', txt)


def gen_cc379(conn):
    """CC 379 — Motion Regarding Personal Protection Order."""
    txt = _header(CASES['ppo'], 'CC 379', 'Motion Regarding Personal Protection Order')
    txt += textwrap.dedent(f"""\
    1. On or about _____________ [VERIFY date], a Personal Protection Order
       was entered in Case No. {CASES['ppo']}.

    2. I, {PLAINTIFF['name']}, move this Court to:
       [ ] Modify the Personal Protection Order
       [ ] Terminate the Personal Protection Order
       [ ] Extend the Personal Protection Order
       [ ] Other: _________________________________________

    3. The reasons for this motion are:
       a. The PPO was based on false allegations by {DEFENDANT['name']}.
       b. There is no factual or legal basis for the continuation of the PPO.
       c. The PPO has been used as a tool for parental alienation and to
          deny Plaintiff parenting time with L.D.W.
       d. Evidence demonstrates that Plaintiff poses no threat to Defendant
          or L.D.W.

    4. Supporting Evidence:
       See attached Exhibit Binder documenting:
       - False allegations made by {DEFENDANT['name']}
       - Parenting time denied as a result of the PPO
       - Evidence of PPO misuse for custody leverage

    5. This motion is supported by the attached brief, exhibits, and
       affidavit of {PLAINTIFF['name']}.

    WHEREFORE, Plaintiff respectfully requests that this Court grant the
    motion and modify/terminate the Personal Protection Order.

    {_sig_block()}
    """)
    return ('CC_379', 'Motion Regarding Personal Protection Order', CASES['ppo'], 'F2', txt)


def gen_cc385(conn):
    """CC 385 — Order on Motion Regarding PPO (Proposed)."""
    txt = _header(CASES['ppo'], 'CC 385', 'Order on Motion Regarding Personal Protection Order')
    txt += textwrap.dedent(f"""\
                          PROPOSED ORDER

    At a session of said Court held in the Courthouse in the
    City of Muskegon, County of Muskegon, State of Michigan

    on _______________

    PRESENT: {JUDGE}

    This matter having come before the Court on Plaintiff's Motion
    Regarding Personal Protection Order, and the Court having reviewed
    the motion, exhibits, and supporting documents,

    IT IS HEREBY ORDERED:

    [ ] The Personal Protection Order in Case No. {CASES['ppo']}
        is MODIFIED as follows:
        _______________________________________________________________
        _______________________________________________________________

    [ ] The Personal Protection Order in Case No. {CASES['ppo']}
        is TERMINATED effective immediately.

    [ ] The Personal Protection Order in Case No. {CASES['ppo']}
        is EXTENDED for a period of _________.

    [ ] Plaintiff's motion is DENIED.

    [ ] Other: ________________________________________________________


    Date: _______________          ________________________________
                                   {JUDGE}
                                   {COURT}, {COUNTY} County
    """)
    return ('CC_385', 'Order on Motion Regarding PPO', CASES['ppo'], 'F2', txt)


def gen_mc230(conn):
    """MC 230 — Ex Parte Application / Motion for TRO (Housing)."""
    txt = _header(CASES['housing'], 'MC 230',
                  'Ex Parte Application and Motion for Temporary Restraining Order')
    txt += textwrap.dedent(f"""\
    1. I, {PLAINTIFF['name']}, respectfully request this Court issue a
       Temporary Restraining Order in Case No. {CASES['housing']}.

    2. Nature of the Case:
       This is a housing/habitability action concerning the property at
       1977 Whitehall Road, Lot 17, North Muskegon, MI 49445
       (Shady Oaks Mobile Home Park).

    3. Irreparable Harm Will Occur Without Immediate Relief:
       a. Unsafe living conditions including sewer/septic negligence
       b. Property management has failed to address documented hazards
       c. Health and safety risks to Plaintiff and L.D.W.
       d. Continued deterioration of the premises

    4. Specific Relief Requested:
       [ ] Order Defendant(s) to cease and desist from: _______________
       [ ] Order Defendant(s) to repair: ______________________________
       [ ] Order Defendant(s) to maintain habitable conditions
       [ ] Temporary restraint from eviction/retaliation
       [ ] Other: _____________________________________________________

    5. Efforts to Resolve Without Court Intervention:
       [VERIFY — document prior complaints to landlord/property manager]

    6. This application is made ex parte because:
       Immediate and irreparable injury, loss, or damage will result
       before the adverse party can be heard in opposition.

    Supporting documents are attached as exhibits.

    {_sig_block()}
    """)
    return ('MC_230', 'Ex Parte Application / Motion for TRO', CASES['housing'], 'F9', txt)


def gen_mc231(conn):
    """MC 231 — Motion for Emergency Relief (Custody)."""
    # Pull parenting-time denial data if available
    pt_rows = safe_query(conn,
        "SELECT description FROM actor_violations WHERE description LIKE '%parenting%' OR description LIKE '%withhold%' LIMIT 5")
    pt_evidence = []
    for r in pt_rows:
        if r['description']:
            pt_evidence.append(str(r['description'])[:200])

    pt_text = "\n       ".join(pt_evidence[:5]) if pt_evidence else "[VERIFY — confirm specific parenting time denial incidents]"

    txt = _header(CASES['custody'], 'MC 231', 'Motion for Emergency Relief')
    txt += textwrap.dedent(f"""\
    1. I, {PLAINTIFF['name']}, move this Court for emergency relief in
       the above-captioned custody matter.

    2. Emergency Circumstances:
       a. {DEFENDANT['name']} has systematically denied Plaintiff parenting
          time with L.D.W. in violation of court orders.
       b. The child's welfare requires immediate court intervention.
       c. Delay in granting relief will cause irreparable harm to the
          parent-child relationship between Plaintiff and L.D.W.

    3. Specific Facts Supporting Emergency:
       {pt_text}

    4. Relief Requested:
       [ ] Immediate establishment/enforcement of parenting time schedule
       [ ] Temporary change of custody pending hearing
       [ ] Order to show cause why {DEFENDANT['name']} should not be held
           in contempt for parenting time denial
       [ ] Appointment of Guardian Ad Litem
       [ ] Other: _____________________________________________________

    5. Efforts to Resolve:
       Plaintiff has attempted to resolve parenting time disputes through
       the Friend of the Court (Pamela Rusco, 990 Terrace St, Muskegon,
       MI 49442) without success.

    6. Best Interest of the Child:
       Emergency relief serves the best interest of L.D.W. by preserving
       the parent-child relationship with Plaintiff per MCL 722.23.

    WHEREFORE, Plaintiff respectfully requests that this Court grant
    emergency relief as outlined above.

    {_sig_block()}
    """)
    return ('MC_231', 'Motion for Emergency Relief', CASES['custody'], 'F1', txt)


def gen_foc10(conn):
    """FOC 10 — Uniform Child Support Order (Reference Template)."""
    txt = _header(CASES['custody'], 'FOC 10',
                  'Uniform Child Support Order — REFERENCE ONLY')
    txt += textwrap.dedent(f"""\
    ╔══════════════════════════════════════════════════════════════════╗
    ║  NOTE: This is a REFERENCE TEMPLATE only.                       ║
    ║  The actual FOC 10 must be obtained from the Friend of the      ║
    ║  Court and completed with current financial information.        ║
    ║  Contact: Pamela Rusco, 990 Terrace St, Muskegon, MI 49442    ║
    ╚══════════════════════════════════════════════════════════════════╝

    UNIFORM CHILD SUPPORT ORDER

    Plaintiff: {PLAINTIFF['name']}
    Defendant: {DEFENDANT['name']}
    Child(ren): L.D.W.  (initials per MCR 8.119(H))

    Case No. {CASES['custody']}
    Court: {COURT}, {COUNTY} County

    IT IS ORDERED:

    1. Child Support:
       Payer:    [VERIFY]
       Payee:    [VERIFY]
       Amount:   $_______ per [  ] week  [  ] month
       Effective: _______________

    2. Medical Support:
       [ ] Plaintiff shall maintain health insurance
       [ ] Defendant shall maintain health insurance
       Uninsured medical expenses divided: ____% / ____%

    3. Child Care:
       Child care expenses divided: ____% / ____%

    4. Income Information (as of order date):
       Plaintiff income: $_______ per [  ] week  [  ] month  [  ] year
       Defendant income: $_______ per [  ] week  [  ] month  [  ] year

    [VERIFY — All financial figures must be verified by FOC before filing]

    {_sig_block()}
    """)
    return ('FOC_10', 'Uniform Child Support Order (Reference)', CASES['custody'], 'F1', txt)


def gen_mc01(conn):
    """MC 01 — Case Inventory Addendum."""
    # Pull all related case numbers
    txt = _header(CASES['custody'], 'MC 01', 'Case Inventory Addendum')
    txt += textwrap.dedent(f"""\
    CASE INVENTORY ADDENDUM

    The following related cases involve the same parties or subject matter:

    ┌─────┬───────────────────┬────────────────────────────────────────┐
    │  #  │ Case Number       │ Description                            │
    ├─────┼───────────────────┼────────────────────────────────────────┤
    │  1  │ {CASES['custody']:<19}│ Custody / Parenting Time               │
    │  2  │ {CASES['ppo']:<19}│ Personal Protection Order              │
    │  3  │ {CASES['housing']:<19}│ Housing / Habitability (Shady Oaks)    │
    │  4  │ [VERIFY]          │ COA Appeal (if filed)                  │
    │  5  │ [VERIFY]          │ MSC Application (if filed)             │
    └─────┴───────────────────┴────────────────────────────────────────┘

    Court:      {COURT}, {COUNTY} County
    Judge:      {JUDGE}
    Division:   {DIVISION}

    Plaintiff:  {PLAINTIFF['name']}
                {PLAINTIFF['address']}
                {PLAINTIFF['city_state_zip']}
                {PLAINTIFF['phone']}

    Defendant:  {DEFENDANT['name']}
                {DEFENDANT['address']}
                {DEFENDANT['city_state_zip']}

    I certify that the information provided above is true and complete
    to the best of my knowledge.

    {_sig_block()}
    """)
    return ('MC_01', 'Case Inventory Addendum', CASES['custody'], 'ALL', txt)


# ── Main ──────────────────────────────────────────────────────────────────

def main():
    print("=" * 60)
    print("Tool #270 — Court Form Auto-Filler")
    print("=" * 60)

    os.makedirs(FORMS_DIR, exist_ok=True)
    os.makedirs(REPORTS_DIR, exist_ok=True)

    conn = sqlite3.connect(DB_PATH, timeout=120)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=60000")
    conn.execute("PRAGMA cache_size=-32000")
    conn.row_factory = sqlite3.Row

    # Create tracking table
    conn.execute("""\
        CREATE TABLE IF NOT EXISTS generated_court_forms (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            form_number TEXT,
            form_title TEXT,
            filing_id TEXT,
            case_number TEXT,
            output_path TEXT,
            fields_filled INTEGER,
            fields_blank INTEGER,
            generated_date TEXT
        )""")
    conn.commit()

    generators = [gen_mc264, gen_cc379, gen_cc385, gen_mc230, gen_mc231, gen_foc10, gen_mc01]
    results = []
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    for gen_fn in generators:
        form_num, title, case_num, filing_id, txt = gen_fn(conn)
        fname = f"{form_num}_{filing_id}.txt"
        fpath = os.path.join(FORMS_DIR, fname)
        with open(fpath, 'w', encoding='utf-8') as f:
            f.write(txt)

        # Count filled vs blank fields
        filled = txt.count(PLAINTIFF['name']) + txt.count(DEFENDANT['name']) + txt.count(case_num)
        blanks = txt.count('[VERIFY') + txt.count('___')

        conn.execute("""\
            INSERT INTO generated_court_forms
            (form_number, form_title, filing_id, case_number, output_path, fields_filled, fields_blank, generated_date)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (form_num, title, filing_id, case_num, fpath, filled, blanks, now))

        results.append({
            'form_number': form_num,
            'form_title': title,
            'filing_id': filing_id,
            'case_number': case_num,
            'output_path': fpath,
            'fields_filled': filled,
            'fields_blank': blanks,
        })
        print(f"  [OK] {form_num} — {title} → {fname}")

    conn.commit()

    # ── Write reports ─────────────────────────────────────────────────
    report_json = {
        'tool': 'court_form_auto_filler',
        'tool_number': 270,
        'generated': now,
        'forms_dir': FORMS_DIR,
        'forms': results,
        'total_forms': len(results),
    }
    json_path = os.path.join(REPORTS_DIR, 'court_form_auto_filler.json')
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(report_json, f, indent=2)

    md_lines = [
        "# Court Form Auto-Filler Report",
        f"**Generated:** {now}",
        f"**Forms Directory:** `{FORMS_DIR}`",
        "",
        "## Generated Forms",
        "",
        "| Form | Title | Case | Filing | Filled | Blank |",
        "|------|-------|------|--------|--------|-------|",
    ]
    for r in results:
        md_lines.append(
            f"| {r['form_number']} | {r['form_title']} | {r['case_number']} "
            f"| {r['filing_id']} | {r['fields_filled']} | {r['fields_blank']} |")
    md_lines += [
        "",
        "## Notes",
        "- All forms use VERIFIED party information — never fabricated.",
        "- Fields marked `[VERIFY]` require Andrew's confirmation before filing.",
        "- Signature lines left blank for wet signature.",
        "- Forms are text-based approximations of SCAO forms — verify format against official versions.",
    ]
    md_path = os.path.join(REPORTS_DIR, 'COURT_FORM_AUTO_FILLER.md')
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(md_lines))

    conn.close()

    print(f"\n  Total forms generated: {len(results)}")
    print(f"  Reports: {json_path}")
    print(f"           {md_path}")
    print("  Done.")


if __name__ == '__main__':
    main()
