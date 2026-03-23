---
name: OMEGA-DISCOVERY
description: >-
  Discovery warfare engine covering interrogatories, requests for production,
  requests for admission, privilege log generation, redaction protocols,
  document retention policies, discovery abuse detection, and protective orders.
  Michigan-specific MCR 2.301-2.314 compliance. Includes deposition strategy
  and subpoena coordination.
category: discipline
version: "1.0.0"
triggers:
  - discovery
  - interrogatory
  - interrogatories
  - request for production
  - RFP
  - request for admission
  - RFA
  - privilege log
  - redaction
  - protective order
  - deposition
  - discovery abuse
  - compel discovery
  - sanctions
  - document retention
lanes:
  - "A: Watson/Custody (2024-001507-DC)"
  - "B: Shady Oaks/Housing (2025-002760-CZ)"
  - "D: PPO (2023-5907-PP)"
  - "E: Judicial Misconduct/JTC"
court: "14th Judicial Circuit, Muskegon County"
case: Pigors v Watson
metadata:
  tier: 2-3 (Knowledge → Analysis)
  layer: Layer 2-3 — Knowledge and Analysis
  fused_skills: 9
  author: andrew-pigors + copilot-omega
  jurisdiction: Michigan
---

# ⚔️ OMEGA-DISCOVERY ⚔️

> **LAYER 2-3 — Knowledge + Analysis: Discovery Warfare Engine**
> **Pipeline:** Discovery Plan → Draft → Serve → Track Responses → Compel → Sanction
> **Case:** Pigors v Watson · MCR 2.301-2.314 · Pro Se Discovery Rights
> **Iron Law:** Every discovery request targets specific evidence gaps. No fishing.

```
╔══════════════════════════════════════════════════════════════════════════╗
║                       OMEGA-DISCOVERY v1.0                              ║
║               9 Skills → 7 Modules → 1 Discovery Engine                 ║
║                                                                         ║
║  D1  Discovery Planning ─────┐                                          ║
║  D2  Interrogatory Drafting ─┤→ D5 Response Analysis ──→ D7 Sanctions  ║
║  D3  RFP/RFA Drafting ───────┘       ↓                      ↓          ║
║  D4  Privilege Log Generator → D6 Motion to Compel ──→ EVIDENCE GAINED ║
║                                      ↑                                   ║
║  Subpoena Coordination ─────────────┘                                   ║
╚══════════════════════════════════════════════════════════════════════════╝
```

---

## Forged from 9 Individual Skills

| # | Source Skill | Absorbed Capability |
|---|-------------|---------------------|
| 1 | `litigation-discovery-warfare` | Strategic discovery planning |
| 2 | `litigation-interrogatory-specialist` | Interrogatory drafting & analysis |
| 3 | `litigation-mandatory-disclosure-specialist` | MCR 2.302 initial disclosures |
| 4 | `litigation-deposition-strategist` | Deposition planning & transcript analysis |
| 5 | `litigation-protective-order-specialist` | Protective order drafting |
| 6 | `litigation-subpoena-engine` | Subpoena generation & tracking |
| 7 | `litigation-sanctions-engine` | Discovery sanction motions |
| 8 | `litigation-evidence-harvester` | Evidence gap → discovery request mapping |
| 9 | `litigation-motion-practice` | Motion to compel drafting (MCR 2.313) |

---

## ═══════════════════════════════════════════════════════════════
## MODULE D1: DISCOVERY PLANNING
## ═══════════════════════════════════════════════════════════════

### Evidence Gap → Discovery Request Mapping

```python
def plan_discovery(lane: str) -> DiscoveryPlan:
    """Map evidence gaps to specific discovery requests."""
    
    # Query evidence gaps from DB
    gaps = query_db("""
        SELECT claim_id, claim_type, gap_description, gap_severity
        FROM claims c
        LEFT JOIN evidence_quotes eq ON c.claim_id = eq.claim_id
        WHERE c.vehicle_name LIKE ? AND eq.atom_id IS NULL
    """, lane_filter(lane))
    
    requests = []
    for gap in gaps:
        if gap.gap_severity == 'critical':
            # Critical gaps get interrogatories + RFP + RFA
            requests.append(Interrogatory(targeting=gap))
            requests.append(RFP(targeting=gap))
            requests.append(RFA(targeting=gap))
        elif gap.gap_severity == 'high':
            # High gaps get RFP + RFA
            requests.append(RFP(targeting=gap))
            requests.append(RFA(targeting=gap))
        else:
            # Standard gaps get RFP only
            requests.append(RFP(targeting=gap))
    
    return DiscoveryPlan(
        lane=lane,
        total_gaps=len(gaps),
        requests=requests,
        deadline=calculate_discovery_deadline(),
        service_method='MCR 2.107 (mail to last known address)'
    )
```

### Michigan Discovery Rules Reference

| Rule | Subject | Key Provisions |
|------|---------|---------------|
| MCR 2.301 | General Discovery | Scope: any nonprivileged matter relevant to claims/defenses |
| MCR 2.302 | Mandatory Disclosure | Initial disclosures required within 14 days |
| MCR 2.303 | Depositions | Oral examination, 7-hour limit per deponent |
| MCR 2.307 | Interrogatories | Max 20 interrogatories (including subparts) per MCR |
| MCR 2.310 | Request for Production | Documents, ESI, tangible things, property inspection |
| MCR 2.312 | Request for Admission | Deemed admitted if not responded within 28 days |
| MCR 2.313 | Motion to Compel | Failure to respond → court order + sanctions |
| MCR 2.314 | Discovery Sanctions | Progressive: costs → adverse inference → default |

---

## ═══════════════════════════════════════════════════════════════
## MODULE D2: INTERROGATORY DRAFTING
## ═══════════════════════════════════════════════════════════════

### Interrogatory Templates by Lane

**Lane A (Custody) — Target: Emily A. Watson**

```
INTERROGATORY NO. [X]: State with specificity each and every occasion 
between [START_DATE] and [END_DATE] on which you denied or interfered 
with the Plaintiff's court-ordered parenting time with L.D.W., including:
  (a) the date and time of each denial;
  (b) the stated reason for each denial;
  (c) any communication (text, email, phone) related to each denial;
  (d) whether L.D.W. was present during each denial;
  (e) any third party present or involved.
```

**Lane B (Shady Oaks) — Target: Homes of America LLC / Cricklewood MHP**

```
INTERROGATORY NO. [X]: Identify all persons with authority to approve 
or deny maintenance requests at Shady Oaks Mobile Home Park for Lot 17 
between January 2023 and December 2025, including:
  (a) their full name and title;
  (b) their employer;
  (c) the scope of their authority.
```

### Interrogatory Rules

```
MICHIGAN LIMITS:
- Max 20 interrogatories per set (MCR 2.307(A))
- Subparts count toward the 20 limit
- Must be answered within 28 days (MCR 2.307(B))
- Answers must be under oath
- Objections must state specific grounds
- "General objections" are insufficient
```

---

## ═══════════════════════════════════════════════════════════════
## MODULE D3: RFP / RFA DRAFTING
## ═══════════════════════════════════════════════════════════════

### Request for Production Templates

```
REQUEST FOR PRODUCTION NO. [X]: Produce all text messages, emails, 
social media messages, and other electronic communications between you 
and Ronald Berry regarding the Plaintiff, L.D.W., or any custody, 
parenting time, or court proceedings in Case No. 2024-001507-DC, 
from [START_DATE] to present.
```

### Request for Admission Templates

```
REQUEST FOR ADMISSION NO. [X]: Admit that on [DATE], you did not 
make L.D.W. available for the Plaintiff's court-ordered parenting 
time as specified in the [ORDER_DATE] Order of the Court.
```

### RFA Strategic Use

```
RFAs are WEAPONS, not just discovery:
- If admitted → fact established without trial testimony
- If denied → impeachment ammunition if proven true at trial
- If not responded within 28 days → DEEMED ADMITTED (MCR 2.312(B))

STRATEGY: Serve RFAs on every key fact Emily might dodge.
28-day clock starts on service. If no response → file notice of 
deemed admissions. Game over for those facts.
```

---

## ═══════════════════════════════════════════════════════════════
## MODULE D4: PRIVILEGE LOG GENERATOR
## ═══════════════════════════════════════════════════════════════

### Privilege Log Format

```
| # | Document | Date | Author | Recipient | Privilege | Basis |
|---|----------|------|--------|-----------|-----------|-------|
| 1 | Email re: custody | 03/15/2024 | Barnes | Watson | Attorney-Client | MCR 2.302(B)(1) |
| 2 | Therapy notes | 04/01/2024 | Dr. Smith | Watson | Psychotherapist | MCL 333.18237 |
```

### Privilege Categories (Michigan)

| Privilege | Rule | Scope |
|-----------|------|-------|
| Attorney-Client | MRE 501 | Communications for legal advice |
| Work Product | MCR 2.302(B)(3) | Materials prepared in anticipation of litigation |
| Psychotherapist | MCL 333.18237 | Therapy/counseling communications |
| Spousal | MRE 501 | Marital communications (limited in family cases) |
| Medical | MCL 600.2157 | Medical records (waivable) |

### Challenging Opponent's Privilege Claims

```python
def challenge_privilege(log_entry: PrivilegeLogEntry) -> str | None:
    """
    Barnes WITHDREW as counsel — does attorney-client privilege survive?
    YES for communications during representation.
    NO for communications after withdrawal if Watson has no new counsel.
    """
    if log_entry.privilege == 'Attorney-Client':
        if log_entry.date > BARNES_WITHDRAWAL_DATE:
            return ("CHALLENGE: Attorney-client privilege cannot apply to "
                    "communications after Barnes withdrew. Watson is now pro se. "
                    "No attorney = no attorney-client privilege for new communications.")
    
    if log_entry.privilege == 'Work Product':
        if log_entry.author not in ['Jennifer Barnes', 'Barnes Law Firm']:
            return ("CHALLENGE: Work product doctrine requires preparation by "
                    "or for an attorney. Non-attorney work product claims fail.")
    
    return None
```

---

## ═══════════════════════════════════════════════════════════════
## MODULE D5: RESPONSE ANALYSIS
## ═══════════════════════════════════════════════════════════════

### Response Classification

| Response Type | Meaning | Action |
|--------------|---------|--------|
| Complete answer | Party responded fully | Extract facts → evidence DB |
| Partial answer | Evasive or incomplete | Motion to compel the remainder |
| Objection only | Refused to answer | Evaluate objection validity → compel if invalid |
| No response (28 days) | Deemed admitted (RFA) or waived (interrogatory) | File notice + motion for sanctions |
| Late response | After deadline without extension | Challenge untimeliness |

### Evasion Detection

```python
EVASION_PATTERNS = [
    "I do not recall",           # If contradicted by documents → impeachment
    "To the best of my knowledge",  # Hedge language
    "I am not aware of",        # Passive denial
    "See attached",              # Without identifying what's attached
    "Objection, overly broad",  # Without answering the non-objectionable part
    "This request is harassing", # Emotional objection = not a legal ground
]
```

---

## ═══════════════════════════════════════════════════════════════
## MODULE D6: MOTION TO COMPEL
## ═══════════════════════════════════════════════════════════════

### MCR 2.313 Motion to Compel Template

```
MOTION TO COMPEL DISCOVERY RESPONSES

Plaintiff Andrew James Pigors moves this Court for an Order compelling 
Defendant Emily A. Watson to fully respond to Plaintiff's [First Set of 
Interrogatories / Requests for Production / Requests for Admission] 
served on [SERVICE_DATE], pursuant to MCR 2.313(A).

STATEMENT OF FACTS:
1. On [SERVICE_DATE], Plaintiff served [DISCOVERY_TYPE] on Defendant.
2. Responses were due by [DUE_DATE] per MCR 2.307(B) / 2.310(B) / 2.312(B).
3. As of the date of this motion, Defendant has [not responded / 
   provided incomplete responses / asserted improper objections].
4. Plaintiff's counsel [N/A — pro se] conferred with Defendant regarding 
   this dispute on [CONF_DATE] per MCR 2.313(B)(1), but the dispute 
   remains unresolved.

ARGUMENT:
[Specific failures + why objections are invalid + prejudice to Plaintiff]

RELIEF REQUESTED:
1. Order compelling complete responses within 14 days.
2. Award Plaintiff reasonable expenses per MCR 2.313(A)(4).
3. Such other relief as this Court deems just.
```

---

## ═══════════════════════════════════════════════════════════════
## MODULE D7: DISCOVERY SANCTIONS
## ═══════════════════════════════════════════════════════════════

### Sanctions Escalation Ladder (MCR 2.314)

```
Level 1: Order compelling compliance + expenses
Level 2: Facts taken as established (adverse inference)
Level 3: Prohibit disobedient party from supporting claims/defenses
Level 4: Strike pleadings
Level 5: Default judgment / dismissal
Level 6: Contempt of court
```

### When to Escalate

```python
def recommend_sanction_level(history: list[DiscoveryViolation]) -> int:
    if len(history) == 0:
        return 0  # No violation yet
    elif len(history) == 1 and history[0].type == 'late_response':
        return 1  # First offense, minor
    elif any(v.type == 'no_response' for v in history):
        return 2  # Complete refusal → adverse inference
    elif len(history) >= 3:
        return 3  # Pattern of abuse → prohibit claims
    elif any(v.type == 'destruction' for v in history):
        return 5  # Spoliation → default judgment
    return 1
```

---

## ═══════════════════════════════════════════════════════════════
## GLOBAL RULES
## ═══════════════════════════════════════════════════════════════

### PRO SE DISCOVERY RIGHTS

```
Andrew is pro se. He has the SAME discovery rights as any attorney.
MCR 2.301(A) — "Parties may obtain discovery regarding any matter, 
not privileged, which is relevant to the subject matter involved 
in the pending action."

No court may deny discovery requests solely because a party is pro se.
If McNeill restricts Andrew's discovery rights → appeal ground (Lane F)
and JTC evidence (Lane E).
```

### DISCOVERY TRACKING TABLE

```sql
CREATE TABLE discovery_tracker (
    id INTEGER PRIMARY KEY,
    lane TEXT,
    type TEXT,          -- interrogatory, rfp, rfa, subpoena
    set_number INTEGER,
    request_number INTEGER,
    target TEXT,        -- Emily A. Watson, Homes of America LLC, etc.
    served_date TEXT,
    due_date TEXT,
    response_date TEXT,
    response_status TEXT, -- complete, partial, objection, no_response, deemed_admitted
    compel_filed TEXT,
    sanctions_level INTEGER DEFAULT 0,
    evidence_gained TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

*OMEGA-DISCOVERY v1.0 — 9 skills forged into one discovery warfare engine.*
*Every request targets a specific evidence gap. Every non-response triggers escalation.*
