"""Court Fee Calculator & IFP Application Generator.

Calculates filing fees for all Michigan courts and generates
In Forma Pauperis (IFP) applications when fees cannot be paid.
"""

import logging
import sqlite3
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

_DEFAULT_DB = Path(r"C:\Users\andre\LitigationOS\litigation_context.db")

# Verified party identity
_PLAINTIFF = {
    "name": "Andrew James Pigors",
    "address": "1977 Whitehall Road, Lot 17, North Muskegon, MI 49445",
    "phone": "(231) 903-5690",
    "email": "andrewjpigors@gmail.com",
}

# Michigan Court Filing Fees (2025 schedule)
# Source: MCL 600.8371, MCL 600.880, SCAO fee schedules
MICHIGAN_FILING_FEES = {
    # 14th Circuit Court — Family Division
    "circuit_family": {
        "motion": 20.00,
        "ex_parte_motion": 20.00,
        "custody_motion": 20.00,
        "modification_motion": 20.00,
        "show_cause": 20.00,
        "objection": 20.00,
        "new_case": 175.00,
        "answer": 0.00,
        "response": 0.00,
        "jury_demand": 50.00,
    },
    # 14th Circuit Court — Civil Division
    "circuit_civil": {
        "new_case_under_25k": 150.00,
        "new_case_over_25k": 175.00,
        "motion": 20.00,
        "third_party_complaint": 175.00,
        "jury_demand": 50.00,
    },
    # Michigan Court of Appeals
    "coa": {
        "claim_of_appeal": 375.00,
        "application_leave": 375.00,
        "emergency_motion": 0.00,  # No separate fee
        "motion": 0.00,
        "brief": 0.00,  # Included with appeal fee
        "delayed_application": 375.00,
        "cross_appeal": 375.00,
    },
    # Michigan Supreme Court
    "msc": {
        "application_leave": 375.00,
        "original_action": 375.00,
        "motion": 0.00,
        "brief": 0.00,
    },
    # Federal — Western District of Michigan
    "federal_wdmi": {
        "civil_complaint": 405.00,
        "motion": 0.00,
        "appeal_to_6th_circuit": 505.00,
        "habeas_corpus": 5.00,
    },
    # Judicial Tenure Commission
    "jtc": {
        "complaint": 0.00,  # No fee for JTC complaints
        "request_investigation": 0.00,
    },
}

# Filing-to-court and fee type mapping
FILING_FEE_MAP = {
    "F1": ("circuit_family", "ex_parte_motion"),
    "F2": ("circuit_civil", "new_case_over_25k"),
    "F3": ("circuit_family", "motion"),
    "F4": ("federal_wdmi", "civil_complaint"),
    "F5": ("msc", "original_action"),
    "F6": ("jtc", "complaint"),
    "F7": ("circuit_family", "custody_motion"),
    "F8": ("circuit_family", "motion"),
    "F9": ("coa", "claim_of_appeal"),
    "F10": ("coa", "emergency_motion"),
}


@dataclass
class FeeCalculation:
    """Fee calculation for a single filing."""
    filing_id: str
    court: str
    fee_type: str
    base_fee: float
    service_costs: float = 0.0
    copy_costs: float = 0.0
    efiling_fee: float = 0.0
    total: float = 0.0
    ifp_eligible: bool = False
    notes: str = ""

    def compute_total(self) -> float:
        self.total = self.base_fee + self.service_costs + self.copy_costs + self.efiling_fee
        return self.total


@dataclass
class IFPApplication:
    """In Forma Pauperis application data."""
    court: str
    case_number: str
    filing_id: str
    monthly_income: float = 0.0
    monthly_expenses: float = 0.0
    assets: float = 0.0
    debts: float = 0.0
    dependents: int = 1  # L.D.W.
    employment_status: str = "Unemployed"
    receives_assistance: bool = False
    assistance_types: List[str] = field(default_factory=list)
    prior_ifp_grants: List[str] = field(default_factory=list)
    grounds: str = ""


class CourtFeeCalculator:
    """Calculate filing fees and generate IFP applications."""

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or _DEFAULT_DB

    # ------------------------------------------------------------------
    # Fee Calculation
    # ------------------------------------------------------------------

    def calculate_fee(self, filing_id: str, include_service: bool = True) -> FeeCalculation:
        """Calculate total fees for a filing."""
        if filing_id not in FILING_FEE_MAP:
            return FeeCalculation(
                filing_id=filing_id, court="unknown", fee_type="unknown",
                base_fee=0.0, notes=f"Unknown filing ID: {filing_id}",
            )

        court, fee_type = FILING_FEE_MAP[filing_id]
        base_fee = MICHIGAN_FILING_FEES.get(court, {}).get(fee_type, 0.0)

        calc = FeeCalculation(
            filing_id=filing_id,
            court=court,
            fee_type=fee_type,
            base_fee=base_fee,
        )

        if include_service:
            calc.service_costs = self._estimate_service_costs(filing_id)

        # E-filing convenience fee (MiFILE charges ~3.50-7.00)
        if base_fee > 0:
            calc.efiling_fee = 7.00

        # Copy costs (~$0.25/page, estimate 30 pages average)
        calc.copy_costs = 7.50

        calc.compute_total()

        # IFP eligibility (income-based — Andrew is currently pro se and unemployed)
        calc.ifp_eligible = base_fee > 0
        if filing_id == "F6":
            calc.ifp_eligible = False  # JTC has no fees
            calc.notes = "No filing fee for JTC complaints"

        return calc

    def calculate_all_fees(self) -> Dict[str, FeeCalculation]:
        """Calculate fees for all 10 filings."""
        return {fid: self.calculate_fee(fid) for fid in FILING_FEE_MAP}

    def total_fees(self) -> float:
        """Total fees across all filings."""
        return sum(c.total for c in self.calculate_all_fees().values())

    def generate_fee_report(self) -> str:
        """Generate a fee summary report."""
        calcs = self.calculate_all_fees()
        lines = [
            "# Court Filing Fee Summary",
            f"Generated: {datetime.now().isoformat()[:19]}",
            "",
            "## Fee Breakdown",
            "",
            "| Filing | Court | Base Fee | Service | E-File | Copy | **Total** | IFP? |",
            "|--------|-------|----------|---------|--------|------|-----------|------|",
        ]
        grand_total = 0.0
        ifp_savings = 0.0
        for fid in sorted(calcs):
            c = calcs[fid]
            grand_total += c.total
            if c.ifp_eligible:
                ifp_savings += c.base_fee
            lines.append(
                f"| {fid} | {c.court} | ${c.base_fee:.2f} | ${c.service_costs:.2f} | "
                f"${c.efiling_fee:.2f} | ${c.copy_costs:.2f} | **${c.total:.2f}** | "
                f"{'✅' if c.ifp_eligible else '—'} |"
            )

        lines.extend([
            "",
            f"**Grand Total (without IFP):** ${grand_total:.2f}",
            f"**Potential IFP Savings:** ${ifp_savings:.2f}",
            f"**Total with IFP Granted:** ${grand_total - ifp_savings:.2f}",
            "",
            "## IFP Strategy",
            "",
            "Andrew is currently *pro se* and has experienced job loss directly caused by",
            "the 59 days of wrongful incarceration. IFP applications should be filed with",
            "every fee-bearing filing. Priority: F4 (federal, $405), F5/F9 ($375 each).",
        ])
        return "\n".join(lines)

    # ------------------------------------------------------------------
    # IFP Application Generation
    # ------------------------------------------------------------------

    def generate_ifp(self, filing_id: str, financial_data: Optional[Dict] = None) -> str:
        """Generate an IFP application for a specific filing."""
        court, _ = FILING_FEE_MAP.get(filing_id, ("unknown", "unknown"))
        case_numbers = {
            "F1": "2024-001507-DC", "F2": "2025-002760-CZ", "F3": "2024-001507-DC",
            "F4": "[PENDING]", "F5": "[PENDING]", "F6": "N/A",
            "F7": "2024-001507-DC", "F8": "2023-5907-PP",
            "F9": "366810", "F10": "366810",
        }
        case_no = case_numbers.get(filing_id, "[UNKNOWN]")

        fin = financial_data or {}

        if court == "federal_wdmi":
            return self._generate_federal_ifp(filing_id, case_no, fin)
        else:
            return self._generate_state_ifp(filing_id, case_no, court, fin)

    def _generate_state_ifp(self, filing_id: str, case_no: str, court: str, fin: Dict) -> str:
        """Generate Michigan state court IFP (MC 20 - Fee Waiver Request)."""
        return f"""# FEE WAIVER REQUEST
## SCAO Form MC 20 — Request to Waive Fees/Costs

**Court:** {self._court_display_name(court)}
**County:** Muskegon
**Case No.:** {case_no}

### Plaintiff/Petitioner Information
- **Name:** {_PLAINTIFF['name']}
- **Address:** {_PLAINTIFF['address']}
- **Phone:** {_PLAINTIFF['phone']}

### Section 1: Public Assistance
I am currently receiving or have applied for one or more of the following:
- [ ] Department of Health and Human Services (DHHS) assistance
- [ ] Medicaid
- [ ] SSI (Supplemental Security Income)
- [ ] Food assistance / SNAP
- [X] Other: Unemployment / Job loss due to wrongful incarceration

### Section 2: Income Information
- **Monthly gross income:** ${fin.get('monthly_income', 0):.2f}
- **Source of income:** {fin.get('income_source', '[ANDREW — INSERT CURRENT INCOME SOURCE]')}
- **Number of dependents:** 1 (L.D.W., minor child)

### Section 3: Assets
- **Cash/bank accounts:** ${fin.get('bank_balance', 0):.2f}
- **Vehicle value:** ${fin.get('vehicle_value', 0):.2f}
- **Other assets:** {fin.get('other_assets', 'None')}

### Section 4: Monthly Expenses
- **Rent/mortgage:** ${fin.get('rent', 0):.2f}
- **Utilities:** ${fin.get('utilities', 0):.2f}
- **Food:** ${fin.get('food', 0):.2f}
- **Transportation:** ${fin.get('transportation', 0):.2f}
- **Medical:** ${fin.get('medical', 0):.2f}
- **Other:** ${fin.get('other_expenses', 0):.2f}

### Section 5: Reason for Request
I am unable to pay the filing fee of ${self.calculate_fee(filing_id).base_fee:.2f} because:

1. I lost four (4) jobs (Metal Arc Welding, IndiGrow Inc., USPS, Shape Corp.) as a direct
   result of 59 days of wrongful incarceration arising from this litigation.
2. I lost two (2) homes as a result of the incarceration and subsequent inability to pay rent.
3. I am proceeding *pro se* because I cannot afford counsel.
4. The filing involves fundamental parental rights under *Troxel v. Granville*,
   530 U.S. 57 (2000), which cannot be conditioned on ability to pay.
   *See Boddie v. Connecticut*, 401 U.S. 371 (1971).

### Verification
I declare under the penalties of perjury that the information above is true and correct
to the best of my knowledge, information, and belief.

Date: _________________

Signature: _________________________________
           {_PLAINTIFF['name']}, Plaintiff, *pro se*
"""

    def _generate_federal_ifp(self, filing_id: str, case_no: str, fin: Dict) -> str:
        """Generate federal court IFP (28 U.S.C. § 1915)."""
        return f"""# APPLICATION TO PROCEED IN FORMA PAUPERIS
## 28 U.S.C. § 1915

**United States District Court**
**Western District of Michigan — Southern Division**
**Case No.:** {case_no}

**ANDREW JAMES PIGORS,**
&emsp;&emsp;Plaintiff,
v.
**HON. JENNY L. McNEILL, et al.,**
&emsp;&emsp;Defendants.

---

I, {_PLAINTIFF['name']}, declare under penalty of perjury that I am the plaintiff in
the above-entitled case and that I am unable to prepay the fees and costs of this
proceeding, and that I am entitled to the relief sought. In support of this
application, I state the following:

### 1. Employment
- **Current employment status:** {fin.get('employment_status', '[ANDREW — INSERT CURRENT STATUS]')}
- **Most recent employer:** {fin.get('last_employer', '[ANDREW — INSERT]')}
- **Reason for leaving:** Terminated due to 59 days of incarceration arising from
  wrongful contempt proceedings in state court (see Complaint ¶¶ 28-35)

### 2. Income
- **Monthly income from all sources:** ${fin.get('monthly_income', 0):.2f}
- **Income sources:** {fin.get('income_source', '[ANDREW — INSERT]')}

### 3. Assets
- **Cash on hand:** ${fin.get('cash', 0):.2f}
- **Bank accounts:** ${fin.get('bank_balance', 0):.2f}
- **Automobile (year/make/value):** {fin.get('vehicle', '[ANDREW — INSERT]')}
- **Real property:** None (lost two homes due to incarceration)
- **Other assets:** {fin.get('other_assets', 'None')}

### 4. Debts and Obligations
- **Outstanding debts:** {fin.get('debts', '[ANDREW — INSERT TOTAL]')}
- **Monthly obligations:** ${fin.get('monthly_expenses', 0):.2f}
- **Dependents:** 1 minor child (L.D.W.)

### 5. Previous IFP Applications
{fin.get('prior_ifp', 'None')}

### 6. Nature of Action
This is a 42 U.S.C. § 1983 civil rights action alleging deprivation of
constitutional rights (due process, equal protection, First Amendment) by a
state court judge and private co-conspirators. The action arises from systematic
denial of parental rights, retaliatory incarceration (59 days for birthday
messages to a child), and ex parte orders entered without constitutionally
required process.

### 7. Basis for Indigency
Plaintiff has experienced cascading economic devastation directly caused by
the defendants' unconstitutional conduct:
- Lost four (4) jobs due to incarceration
- Lost two (2) homes
- Currently proceeding *pro se* because unable to afford counsel
- The filing fee of $405.00 represents a barrier to access fundamental
  constitutional rights. *See Neitzke v. Williams*, 490 U.S. 319 (1989).

**WHEREFORE**, Plaintiff respectfully requests that this Court grant leave to
proceed *in forma pauperis* without prepayment of fees and costs.

Dated: _________________

_________________________________
{_PLAINTIFF['name']}
{_PLAINTIFF['address']}
{_PLAINTIFF['phone']}
{_PLAINTIFF['email']}
Plaintiff, *pro se*
"""

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _estimate_service_costs(self, filing_id: str) -> float:
        """Estimate service of process costs."""
        costs = {
            "F1": 15.00,  # Personal service via sheriff
            "F2": 45.00,  # Summons + complaint (sheriff)
            "F3": 15.00,  # Mail service sufficient
            "F4": 45.00,  # Federal summons via USMS or process server
            "F5": 15.00,  # Mail to MSC
            "F6": 0.00,   # JTC handles service
            "F7": 15.00,  # Mail service
            "F8": 15.00,  # Mail service
            "F9": 0.00,   # COA handles distribution
            "F10": 0.00,  # COA handles distribution
        }
        return costs.get(filing_id, 15.00)

    def _court_display_name(self, court: str) -> str:
        names = {
            "circuit_family": "14th Circuit Court — Family Division",
            "circuit_civil": "14th Circuit Court — Civil Division",
            "coa": "Michigan Court of Appeals",
            "msc": "Michigan Supreme Court",
            "federal_wdmi": "U.S. District Court, W.D. Michigan",
            "jtc": "Judicial Tenure Commission",
        }
        return names.get(court, court)

    def save_fee_data(self) -> None:
        """Save fee calculations to DB."""
        try:
            conn = sqlite3.connect(str(self.db_path))
            conn.execute("PRAGMA busy_timeout = 60000")
            conn.execute("PRAGMA journal_mode = WAL")
            conn.execute("""
                CREATE TABLE IF NOT EXISTS filing_fees (
                    filing_id TEXT PRIMARY KEY,
                    court TEXT,
                    fee_type TEXT,
                    base_fee REAL,
                    service_costs REAL,
                    efiling_fee REAL,
                    copy_costs REAL,
                    total REAL,
                    ifp_eligible INTEGER,
                    calculated_at TEXT DEFAULT (datetime('now'))
                )
            """)
            calcs = self.calculate_all_fees()
            rows = [
                (fid, c.court, c.fee_type, c.base_fee, c.service_costs,
                 c.efiling_fee, c.copy_costs, c.total, int(c.ifp_eligible))
                for fid, c in calcs.items()
            ]
            conn.execute("DELETE FROM filing_fees")
            conn.executemany(
                "INSERT INTO filing_fees VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))",
                rows,
            )
            conn.commit()
            conn.close()
            logger.info("Saved fee data for %d filings", len(rows))
        except Exception as e:
            logger.error("Failed to save fee data: %s", e)
