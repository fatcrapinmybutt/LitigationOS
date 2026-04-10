"""
Phase 37: Generate FOIA letters — MCSO, MDHHS, 60th District Court
Phase 38: Generate litigation hold letters to all HOA entities
"""
from pathlib import Path
from datetime import datetime

OUT_DIR = Path(r"C:\Users\andre\LitigationOS\05_FILINGS\LANE_B_HOUSING\FOIA")
HOLD_DIR = Path(r"C:\Users\andre\LitigationOS\05_FILINGS\LANE_B_HOUSING\LITIGATION_HOLD")
OUT_DIR.mkdir(parents=True, exist_ok=True)
HOLD_DIR.mkdir(parents=True, exist_ok=True)

today = datetime.now().strftime("%B %d, %Y")
today_short = datetime.now().strftime("%Y-%m-%d")
sender = "Andrew James Pigors\n1977 Whitehall Rd, Lot 17\nNorth Muskegon, MI 49445\n(231) 903-5690\nandrewjpigors@gmail.com"

# ══════════════════════════════════════════════════
# FOIA 1: MCSO — Deputy Schmidt Report
# ══════════════════════════════════════════════════
foia_mcso_1 = f"""{sender}

{today}

Muskegon County Sheriff's Office
Records Division
990 Terrace Street
Muskegon, MI 49442

        RE: FREEDOM OF INFORMATION ACT REQUEST — MCL 15.231 et seq.
            Re: Call for Service — July 17, 2025 — 1977 Whitehall Rd, Lot 17, North Muskegon

To the FOIA Coordinator:

Pursuant to the Michigan Freedom of Information Act, MCL 15.231 et seq., I hereby request copies
of the following public records:

1. All incident reports, supplemental reports, and case documentation generated in connection
   with a call for service placed by Andrew James Pigors on or about July 17, 2025, regarding
   an incident at 1977 Whitehall Rd, Lot 17, North Muskegon, MI 49445;

2. All body camera footage and dash camera footage captured by any responding deputy on
   July 17, 2025 at the above address;

3. All dispatch audio recordings (Computer Aided Dispatch / CAD) for the above call;

4. All CAD log entries for the above call, including time of dispatch, unit assigned, time of
   arrival, and disposition;

5. The name and badge number of all deputies who responded to the above call (Deputy Douglas
   Schmidt believed to be the primary responder — confirm or identify);

6. Any report or supplement completed by or signed by Deputy Douglas Schmidt or any other
   deputy regarding the incident at Lot 17, 1977 Whitehall Rd, North Muskegon, MI on July 17, 2025.

The purpose of this request is to obtain records documenting my call to law enforcement when I
observed, via my own security cameras, agents of Homes of America LLC / Shady Oaks Park MHP LLC
drilling the lock on my door without lawful authorization.

I am willing to pay reasonable copying costs, not to exceed $10.00 without prior notification.
If any portion of this request is denied, please identify the specific exemption(s) relied upon
and provide the portions not exempt.

Please respond within the statutory 5-business-day acknowledgment period and 15-business-day
production period under MCL 15.235.

                                        Respectfully,
                                        /s/ Andrew James Pigors
                                        Andrew James Pigors
"""

# ══════════════════════════════════════════════════
# FOIA 2: MCSO — HOA False Police Report
# ══════════════════════════════════════════════════
foia_mcso_2 = f"""{sender}

{today}

Muskegon County Sheriff's Office
Records Division
990 Terrace Street
Muskegon, MI 49442

        RE: FREEDOM OF INFORMATION ACT REQUEST — MCL 15.231 et seq.
            Re: All MCSO Reports Filed by or on Behalf of Shady Oaks / Homes of America LLC
                Regarding 1977 Whitehall Rd, Lot 17, North Muskegon, MI — 2025 to Present

To the FOIA Coordinator:

Pursuant to the Michigan Freedom of Information Act, MCL 15.231 et seq., I hereby request copies
of the following public records:

1. All incident reports, complaints, and supplemental reports filed by or on behalf of:
   - Shady Oaks Park MHP LLC
   - Homes of America LLC
   - Cassandra VanDam
   - Nicole Browley
   - Shelly Przybylek
   - Any officer, agent, or employee of the above entities
   relating to 1977 Whitehall Rd, Lot 17, North Muskegon, MI 49445, from January 1, 2025
   to present;

2. Any incident report alleging that Andrew James Pigors damaged, destroyed, or tampered with
   any lock, door, or property at 1977 Whitehall Rd, Lot 17, at any time;

3. Any incident report filed after July 17, 2025, relating to Lot 17 or the parties identified above;

4. All communications between MCSO and any representative of Homes of America LLC or Shady Oaks
   Park MHP LLC, from January 1, 2025 to present.

Background: I have evidence that HOA filed a false police report claiming that I returned to
Lot 17 and damaged locks that HOA had installed after drilling through my original lock on
July 17, 2025. My security camera footage disproves this false allegation. I am requesting these
records to identify the false report and document the false reporting offense.

I am willing to pay reasonable copying costs, not to exceed $10.00 without prior notification.
Please respond within the statutory 5-business-day acknowledgment and 15-business-day production
period under MCL 15.235.

                                        Respectfully,
                                        /s/ Andrew James Pigors
                                        Andrew James Pigors
"""

# ══════════════════════════════════════════════════
# FOIA 3: MDHHS — DHS Payment Records
# ══════════════════════════════════════════════════
foia_mdhhs = f"""{sender}

{today}

Michigan Department of Health and Human Services
FOIA Coordinator
P.O. Box 30195
Lansing, MI 48909

        RE: FREEDOM OF INFORMATION ACT REQUEST — MCL 15.231 et seq.
            Re: DHS Rental Assistance Payment to Homes of America LLC — $1,962.45
            Beneficiary: Andrew James Pigors, 1977 Whitehall Rd, Lot 17, North Muskegon, MI 49445

To the FOIA Coordinator:

Pursuant to the Michigan Freedom of Information Act, MCL 15.231 et seq., I hereby request copies
of the following public records regarding rental assistance payments made on my behalf:

1. All MDHHS / DHS records reflecting any rental assistance payment issued to Homes of America
   LLC, Shady Oaks Park MHP LLC, or any associated entity, on behalf of Andrew James Pigors
   (beneficiary), for the tenancy at 1977 Whitehall Rd, Lot 17, North Muskegon, MI 49445,
   from January 1, 2022 through present;

2. Specifically, records reflecting a payment of $1,962.45 that was disbursed to HOA on
   Plaintiff's behalf and was NOT credited to Plaintiff's account by HOA;

3. Check or warrant numbers, payee names, disbursement dates, and endorsement records for
   any payment made to HOA under programs including but not limited to:
   - Emergency Rental Assistance (ERA)
   - State Emergency Relief (SER)
   - COVID-19 rental assistance
   - Any other MDHHS rental support program;

4. Any documentation showing when payment was processed and to what payee account it was directed;

5. Any returned or undelivered payments.

The requested records are needed because HOA collected $1,962.45 in government rental assistance
issued to it on my behalf, then refused to credit that payment to my account and used the
non-credit to support fraudulent eviction proceedings against me.

I am willing to pay reasonable copying costs, not to exceed $20.00 without prior notification.
Please respond within the 5-business-day acknowledgment and 15-business-day production period.

                                        Respectfully,
                                        /s/ Andrew James Pigors
                                        Andrew James Pigors
"""

# ══════════════════════════════════════════════════
# FOIA 4: 60th District Court — Hearing Transcript
# ══════════════════════════════════════════════════
foia_60th = f"""{sender}

{today}

60th District Court
990 Terrace Street
Muskegon, MI 49442
Attn: Court Clerk / Records Department

        RE: REQUEST FOR TRANSCRIPT AND COURT RECORDS
            Case No. 2025-061626-LT (Eviction)
            Case No. 24058913LT (Prior Consent Order)

Dear Court Clerk:

I hereby request the following court records pursuant to MCR 8.108 and the Michigan Constitution:

1. Full verbatim transcript of all hearings conducted in Case No. 2025-061626-LT, including
   but not limited to:
   - All pretrial hearings
   - The hearing at which a writ of eviction and/or lot return was authorized
   - Any hearing at which HOA presented proof of ownership of the mobile home at Lot 17;

2. All documents submitted by Homes of America LLC, Shady Oaks Park MHP LLC, or their counsel
   to support the writ of eviction and lot return, including any deed, title, or bill of sale
   purporting to establish HOA's ownership of the mobile home at Lot 17;

3. The complete writ of eviction and writ of lot return entered in Case No. 2025-061626-LT,
   and all underlying orders;

4. All documents submitted by either party in Case No. 24058913LT, including the
   Consent Order and any payments records;

5. Full verbatim transcript of all hearings in Case No. 24058913LT.

I am prepared to pay reasonable transcript fees. Please provide an itemized cost estimate.

The records are requested for the purpose of identifying material misrepresentations made to
the Court by HOA counsel regarding ownership of my mobile home.

                                        Respectfully,
                                        /s/ Andrew James Pigors
                                        Andrew James Pigors
"""

# ══════════════════════════════════════════════════
# LITIGATION HOLD LETTER — All HOA Entities
# ══════════════════════════════════════════════════
hold_letter = f"""{sender}

{today}

VIA CERTIFIED MAIL — RETURN RECEIPT REQUESTED

TO:
Homes of America LLC                    Shady Oaks Park MHP LLC
c/o Registered Agent                    c/o Registered Agent
[ADDRESS — confirm LARA registration]  [ADDRESS — NJ registration]

Alden Global Capital LLC                Partridge Equity Group
590 Madison Avenue                      [ADDRESS — confirm]
New York, NY                            [City, State]

Cricklewood MHP LLC
[ADDRESS — confirm LARA registration]

Also served on:
Jeremy Brown, P77427 (HOA Counsel — if still active)
[Law firm address]

        RE: LITIGATION HOLD NOTICE — PRESERVATION DEMAND
            Re: 1977 Whitehall Rd, Lot 17, North Muskegon, MI 49445
            Andrew James Pigors v. All Parties Named Below

Ladies and Gentlemen:

                           NOTICE OF ANTICIPATED LITIGATION
                           DEMAND TO PRESERVE ALL EVIDENCE

You are hereby notified that Andrew James Pigors intends to pursue legal action against you, your
entities, your agents, and your employees in connection with the following matters:

1. Fraudulent eviction proceedings — Case Nos. 2025-061626-LT and 2025-002760-CZ
2. Slander of title — Cassandra VanDam's public statements about Plaintiff's home
3. Spoliation of financial records — ledger destruction (XLS/CSV null-wiped)
4. Post-eviction destruction of personal property
5. False police report filed after the eviction
6. Coercive conduct — February 13, 2025 email demanding surrender of title for $750
7. Financial fraud — DHS $1,962.45 not credited; $1,300.26 check omitted; Zego ledger wiped
8. Federal RICO violations — 18 USC §1961 et seq.

                        YOU ARE REQUIRED TO PRESERVE THE FOLLOWING:

IMMEDIATELY, and without destruction, modification, or alteration, you must preserve and
retain all documents, records, electronically stored information (ESI), and tangible items
related to the above matters, including but not limited to:

A. FINANCIAL RECORDS
   1. All rent ledgers, financial records, and accounting documents for Lot 17, from 2019 to present
   2. All versions of any ledger or financial statement for Shady Oaks Park MHP LLC / Lot 17
   3. All records of payments received from or on behalf of Andrew Pigors
   4. All records from Zego payment portal related to Lot 17
   5. DHS / MDHHS rental assistance payment records for Lot 17
   6. Bank records showing HOA receipt and deposit of DHS $1,962.45 payment
   7. All records of the $1,300.26 payment identified in Plaintiff's records but absent from HOA ledger
   8. All water/sewer billing records for Lot 17

B. COMMUNICATIONS
   1. All emails, text messages, social media messages, and voicemails involving:
      - Andrew James Pigors
      - Lot 17, 1977 Whitehall Rd, North Muskegon
      - The eviction proceedings (any case number)
      - Cassandra VanDam's communications with Carmyn Hanna
   2. All communications with Jeremy Brown (P77427) and any other counsel
   3. All communications with the 60th District Court and 14th Circuit Court
   4. All communications with Muskegon County Sheriff's Office
   5. All communications regarding ownership of the mobile home at Lot 17
   6. All communications with LARA regarding License #1201891

C. TITLE AND OWNERSHIP DOCUMENTS
   1. Any deed, bill of sale, title, or other document purportedly establishing HOA's ownership
      of the mobile home at Lot 17
   2. All documents related to HOA's acquisition of the Shady Oaks mobile home park
   3. All documents related to the corporate structure of:
      - Homes of America LLC
      - Shady Oaks Park MHP LLC
      - Cricklewood MHP LLC
      - Partridge Equity Group
      - Alden Global Capital LLC
   4. LARA registration and licensing documents for all entities operating at Shady Oaks

D. SECURITY AND ACCESS RECORDS
   1. All security camera footage from Shady Oaks MHC for the period July 1–August 31, 2025
   2. All work orders, instructions, or authorizations for the lock-drilling activity at Lot 17
      on or about July 17, 2025
   3. All records related to Nicole Browley's presence at Lot 17 on July 17, 2025
   4. All police reports filed by HOA regarding Lot 17 — 2025 to present

E. COURT RECORDS AND SUBMISSIONS
   1. All documents submitted by HOA to any court in the eviction proceedings
   2. All draft orders prepared by Jeremy Brown in Cases 2025-002760-CZ and 2025-061626-LT
   3. Any document alleging that Andrew Pigors falsified a judicial signature

F. PERSONNEL AND AGENCY RECORDS
   1. All employment and agency records for Cassandra VanDam, Nicole Browley, and Shelly Przybylek
   2. All instructions given to those individuals regarding Lot 17 and Andrew Pigors

                              CONSEQUENCES OF FAILURE TO PRESERVE

Failure to preserve the evidence identified above may constitute spoliation of evidence.
Under Michigan law, the adverse inference rule applies when a party destroys evidence relevant to
litigation: Toth v Ords, 319 Mich App 673 (2017). Courts may instruct juries that destroyed
evidence would have been unfavorable to the party who destroyed it.

You are further warned that:
- Destruction of the financial ledger records (the digital versions of which show evidence of
  deliberate null-byte wiping) has already been documented;
- Destruction of any additional records after receipt of this letter will be reported to the
  Court and to the Attorney General;
- Federal obstruction provisions (18 USC §1503, §1512) apply to destruction of evidence in
  anticipation of federal proceedings.

                              REQUEST FOR INSURANCE IDENTIFICATION

Pursuant to MCR 2.313(G), please identify all liability insurance policies that may cover
any claims arising from the above matters, including the name of the insurer, policy number,
limits of coverage, and contact information for the insurer's claims department.

This letter constitutes formal notice of anticipated litigation. Please direct all future
communications to:

Andrew James Pigors (Pro Se)
1977 Whitehall Rd, Lot 17
North Muskegon, MI 49445
andrewjpigors@gmail.com

                                        Respectfully,
                                        /s/ Andrew James Pigors
                                        Andrew James Pigors, Pro Se
Date: {today}
"""

# Write FOIA letters
foia_files = {
    f"FOIA_MCSO_Schmidt_Report_{today_short}.md": foia_mcso_1,
    f"FOIA_MCSO_False_Police_Report_{today_short}.md": foia_mcso_2,
    f"FOIA_MDHHS_DHS_Payment_{today_short}.md": foia_mdhhs,
    f"FOIA_60thDistrict_Transcripts_{today_short}.md": foia_60th,
}

for fname, content in foia_files.items():
    fpath = OUT_DIR / fname
    fpath.write_text(content, encoding='utf-8')
    print(f"FOIA: {fpath}")

# Write litigation hold
hold_path = HOLD_DIR / f"LITIGATION_HOLD_ALL_HOA_ENTITIES_{today_short}.md"
hold_path.write_text(hold_letter, encoding='utf-8')
print(f"HOLD: {hold_path}")

print(f"\nFOIA dir: {OUT_DIR}")
print(f"Hold dir: {HOLD_DIR}")
print(f"Total files written: {len(foia_files) + 1}")
