# Claim Viability Scoring — Framework and Methodology

> Systematic scoring protocol for ranking claim viability
> Context: Pigors v Watson | Michigan | 14th Judicial Circuit

---

## Scoring Overview

Every candidate cause of action receives a composite viability score from 0-100. The score drives filing priority decisions and resource allocation.

**Composite Formula:**
```
Composite Score = (Element Coverage × 0.30) 
               + (Evidence Strength × 0.25) 
               + (SOL Compliance × 0.15) 
               + (Defense Resilience × 0.15) 
               + (Remedy Value × 0.15)
```

---

## Factor 1: Element Coverage (30% weight)

### Scoring Methodology:
For each element of the cause of action, assess whether the available facts satisfy it.

| Element Status | Score per Element |
|---------------|------------------|
| **STRONG** — Facts clearly establish element; direct evidence exists | 100 |
| **ARGUABLE** — Facts support element but reasonable minds could differ | 60 |
| **WEAK** — Some factual basis but significant gaps exist | 30 |
| **MISSING** — No facts support this element | 0 |

### Calculation:
```
Element Coverage = (Sum of all element scores) / (Number of elements × 100) × 100
```

### Example — Fraud (6 elements):
| Element | Status | Score |
|---------|--------|-------|
| Material representation | STRONG | 100 |
| Falsity | STRONG | 100 |
| Knowledge/recklessness | ARGUABLE | 60 |
| Intent to induce reliance | STRONG | 100 |
| Actual reliance | STRONG | 100 |
| Damages | STRONG | 100 |

**Element Coverage = (100+100+60+100+100+100) / 600 × 100 = 93%**

### Special Rules:
- If ANY element is MISSING (score 0), the claim cannot survive summary judgment — cap the overall composite at 35 regardless of other factors
- If the claim has a heightened burden (clear and convincing for fraud), downgrade each ARGUABLE element to score 40 instead of 60

---

## Factor 2: Evidence Strength (25% weight)

### Scoring Methodology:
Assess the quality and quantity of evidence supporting each element.

| Evidence Quality | Score |
|-----------------|-------|
| **Documentary proof** — Signed contract, official record, photograph with metadata | 95-100 |
| **Written communications** — Emails, texts, letters between parties | 80-90 |
| **Third-party records** — Inspection reports, government records, bank statements | 75-85 |
| **Disinterested witness testimony** — Neighbor, inspector, bystander | 65-75 |
| **Interested witness testimony** — Plaintiff's own testimony (credible) | 50-65 |
| **Circumstantial evidence** — Inference chains, pattern evidence | 35-50 |
| **Plaintiff's testimony alone** — No corroboration | 25-40 |
| **No evidence currently available** — Element relies on future discovery | 10-20 |

### Calculation:
```
Evidence Strength = Average evidence score across all elements
```

### Corroboration Bonus:
When multiple independent evidence sources support the same element, add +10 to that element's evidence score (cap at 100).

### Michigan-Specific Considerations:
- **Fraud requires clear and convincing evidence** — discount evidence scores by 15% for fraud claims
- **IIED requires extreme and outrageous conduct** — unless evidence is overwhelming (90+), discount by 20%
- **Defamation per se presumes damages** — evidence score for damages element is automatically 80+

---

## Factor 3: SOL Compliance (15% weight)

### Binary Scoring (with nuance):

| SOL Status | Score |
|-----------|-------|
| **Clearly within SOL** — More than 1 year remaining | 100 |
| **Within SOL but tight** — Less than 1 year remaining | 90 |
| **Within SOL but very tight** — Less than 6 months remaining | 75 |
| **Arguable** — Discovery rule or tolling may apply | 50 |
| **Likely expired** — Tolling argument is weak | 20 |
| **Clearly expired** — No tolling argument available | 0 |

### SOL Calculation Protocol:
1. Identify the accrual date (when the claim arose)
2. Apply the specific SOL period for this cause of action
3. Check for discovery rule applicability (MCL 600.5855)
4. Check for tolling (MCL 600.5851 — infancy, insanity)
5. Check for continuing violations doctrine
6. Check for equitable tolling (active concealment)
7. Check for saving provision (MCL 600.5856 — 6-month refile)

### Filing Urgency Flags:
| Flag | Condition | Action Required |
|------|----------|----------------|
| 🔴 URGENT | SOL expires within 30 days | File immediately, amend later |
| 🟡 CAUTION | SOL expires within 6 months | Prioritize this claim in filing |
| 🟢 SAFE | SOL has 1+ year remaining | Normal priority |

---

## Factor 4: Defense Resilience (15% weight)

### Scoring Methodology:
Anticipate defenses and assess how well the claim withstands them.

| Defense Vulnerability | Score |
|---------------------|-------|
| **No significant defenses apparent** | 90-100 |
| **Defenses exist but are weak** | 70-85 |
| **Moderate defenses — reasonable arguments both ways** | 45-65 |
| **Strong defenses — plaintiff's position is uphill** | 20-40 |
| **Overwhelming defenses — claim likely fails** | 0-20 |

### Common Defense Assessment (Michigan):

#### Fraud Claims:
| Defense | Strength Assessment |
|---------|-------------------|
| Puffery / opinion | WEAK if statement was specific and factual |
| No reliance (plaintiff should have investigated) | MODERATE — depends on relationship |
| No damages | WEAK if out-of-pocket losses documented |
| SOL expired | Check discovery rule |

#### Negligence Claims:
| Defense | Strength Assessment |
|---------|-------------------|
| No duty | STRONG if no recognized legal relationship |
| Comparative negligence | MODERATE — reduces damages, doesn't eliminate if <51% |
| Assumption of risk | WEAK in landlord-tenant (unequal bargaining power) |
| Governmental immunity | STRONG if defendant is government entity |

#### Contract Claims:
| Defense | Strength Assessment |
|---------|-------------------|
| Plaintiff's breach | MODERATE — depends on materiality and timing |
| Waiver clause | WEAK if waiving statutory right (MCL 554.139 cannot be waived) |
| Force majeure | WEAK unless truly unforeseeable |
| Statute of frauds | Check if written agreement exists |

#### MCPA Claims:
| Defense | Strength Assessment |
|---------|-------------------|
| Regulatory exemption | MODERATE — check if transaction is specifically regulated |
| No "trade or commerce" | WEAK if defendant is in business of the transaction |
| De minimis harm | WEAK — MCPA has $250 floor |

---

## Factor 5: Remedy Value (15% weight)

### Scoring Methodology:
Assess the monetary and equitable value of available remedies.

| Remedy Value | Score | Description |
|-------------|-------|-------------|
| **Exceptional** | 90-100 | Treble damages + attorney fees + injunction; total potential > $100K |
| **High** | 70-85 | Significant compensatory + statutory enhancements; $50K-$100K |
| **Moderate** | 50-65 | Solid compensatory damages; $25K-$50K |
| **Low-Moderate** | 30-45 | Modest damages or primarily equitable relief; $10K-$25K |
| **Low** | 10-25 | Small damages, nominal recovery likely; < $10K |
| **Nominal** | 0-10 | Technical violation, minimal actual harm |

### Remedy Multiplier Impact:
| Claim | Base Damages | Multiplier | Enhanced Value |
|-------|-------------|-----------|---------------|
| MCPA (knowing) | $5,000 | 3x + fees | $15,000 + fees |
| Security Deposit | $2,000 | 2x + fees | $4,000 + fees |
| Forcible eviction | $10,000 | 3x | $30,000 |
| § 1983 | $20,000 | + fees (§ 1988) | $20,000 + fees |

### Fee-Shifting Premium:
Claims with attorney fee provisions receive +15 to remedy value score because:
1. Fee-shifting increases settlement pressure on defendant
2. Even if plaintiff is pro se, courts may award "reasonable" fees
3. Threat of fee exposure motivates serious settlement discussion

---

## Composite Score → Filing Priority

| Composite Score | Priority | Action |
|----------------|----------|--------|
| **85-100** | 🔴 CRITICAL | File as lead count. Strongest claim drives the case. |
| **70-84** | 🟠 HIGH | File as primary supporting count. Strong standalone claim. |
| **55-69** | 🟡 MEDIUM | File as secondary count. Adds damages and discovery rights. |
| **40-54** | 🔵 LOW | Consider filing. May be useful for leverage or discovery. |
| **25-39** | ⚪ DEFER | Do not file now. Investigate further. May develop with discovery. |
| **0-24** | ❌ REJECT | Do not file. Document reason for rejection. |

---

## Example Scorecard Output

```
═══════════════════════════════════════════════════════════
CLAIM VIABILITY SCORECARD — Pigors v Watson
═══════════════════════════════════════════════════════════

CLAIM: Michigan Consumer Protection Act (MCL 445.903)
  Element Coverage:    92/100 (3/3 elements STRONG)    × 0.30 = 27.6
  Evidence Strength:   85/100 (texts + lease + photos)  × 0.25 = 21.3
  SOL Compliance:     100/100 (well within 6 years)     × 0.15 = 15.0
  Defense Resilience:  75/100 (regulatory exemption weak)× 0.15 = 11.3
  Remedy Value:        95/100 (treble + fees)            × 0.15 = 14.3
  ─────────────────────────────────────────────────────
  COMPOSITE SCORE:     89.5/100
  PRIORITY:            🔴 CRITICAL
  RECOMMENDATION:      File as Count I or II. Lead with this.

CLAIM: Fraud (Common Law)
  Element Coverage:    83/100 (5 STRONG, 1 ARGUABLE)    × 0.30 = 24.9
  Evidence Strength:   72/100 (discount for C&C burden)  × 0.25 = 18.0
  SOL Compliance:     100/100 (discovery rule extends)   × 0.15 = 15.0
  Defense Resilience:  65/100 (puffery defense possible)  × 0.15 =  9.8
  Remedy Value:        65/100 (compensatory only)         × 0.15 =  9.8
  ─────────────────────────────────────────────────────
  COMPOSITE SCORE:     77.5/100
  PRIORITY:            🟠 HIGH
  RECOMMENDATION:      File as supporting count. Strong but harder to prove.

═══════════════════════════════════════════════════════════
```

---

## Cost-Benefit Analysis

For pro se litigants, also consider:

| Factor | Assessment |
|--------|-----------|
| **Filing complexity** | How difficult is this count to draft correctly? |
| **Discovery burden** | How much discovery is needed to prove this claim? |
| **Motion practice risk** | How likely is a dispositive motion against this claim? |
| **Settlement leverage** | Does this claim create pressure independent of trial value? |
| **Judicial reception** | How do Michigan circuit courts typically treat this claim? |

A claim may score well on viability but poorly on cost-benefit for a pro se litigant if it requires extensive expert testimony, complex discovery, or specialized legal knowledge to prosecute.
