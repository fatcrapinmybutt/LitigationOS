# LEGAL RISK HEATMAP
*Generated: 2026-03-18 21:02*

## 🔥 Critical Findings

- **F4 (Federal §1983) has highest expected value at ~$300K+ likely**
- **F7 (Fraud on Court) creates biggest cascade — enables F1, F2, F5**
- **Emily Watson faces CRITICAL exposure on 4 filings (F1, F4, F5, F7)**
- **McNeill faces CRITICAL exposure on F6 (JTC) and F8 (MSC)**
- **Berry faces HIGH exposure on F4 (federal) and F10 (AGC)**
- **F6 (JTC) is zero-cost with 75% success probability — highest ROI**
- **Filing F3 first is optimal — it enables F5 and F7 with no dependencies**

## 📊 Party Exposure Matrix

| Party | CRITICAL | HIGH | MODERATE | LOW |
|-------|----------|------|----------|-----|
| Emily Watson | 4 | 1 | 4 | 1 |
| Ronald Berry | 1 | 1 | 1 | 7 |
| Jennifer Barnes | 0 | 0 | 0 | 10 |
| Judge McNeill | 2 | 2 | 0 | 6 |
| Andrew Pigors | 0 | 0 | 5 | 5 |

## 💰 Expected Value Ranking

| Filing | P(Success) | Cost | EV (Likely) | ROI |
|--------|-----------|------|-------------|-----|
| F4 (42 USC §1983 Federal) | 60% | $400 | $317,600 | 794.0x |
| F7 (Fraud on Court/Void Order) | 60% | $175 | $95,825 | 547.6x |
| F9 (COA Appeal) | 65% | $375 | $58,125 | 155.0x |
| F5 (Emergency Parenting Time) | 65% | $175 | $51,825 | 296.1x |
| F1 (Emergency Custody/TRO) | 45% | $175 | $44,825 | 256.1x |
| F3 (MCR 2.003 Disqualificatio) | 70% | $175 | $38,325 | 219.0x |
| F6 (JTC Complaint) | 75% | $0 | $30,000 | 30000.0x |
| F8 (MSC Superintending Contro) | 50% | $100 | $27,400 | 274.0x |
| F10 (Attorney Grievance) | 70% | $0 | $14,000 | 14000.0x |
| F2 (PPO Termination) | 55% | $175 | $11,925 | 68.1x |

## 🔗 Cascading Failure Map

### F3 (MCR 2.003 Disqualification)
- **Depends on:** Nothing (independent)
- **Enables:** Nothing (terminal)
- **Cascade depth:** 4 filings affected
- **If fails:** If recusal denied, McNeill rules on all subsequent motions — file COA mandamus immediately
- **Mitigation:** File simultaneously with F9 COA appeal as backup

### F7 (Fraud on Court/Void Orders)
- **Depends on:** F3
- **Enables:** Nothing (terminal)
- **Cascade depth:** 3 filings affected
- **If fails:** If fraud not found, all existing orders remain valid — appeal immediately
- **Mitigation:** Build overwhelming evidence package; fraud on court has NO time bar (MCR 2.612(C)(3))

### F6 (JTC Complaint)
- **Depends on:** Nothing (independent)
- **Enables:** Nothing (terminal)
- **Cascade depth:** 2 filings affected
- **If fails:** JTC investigation is independent — even dismissal doesn't affect other filings
- **Mitigation:** JTC complaint strengthens disqualification motion regardless of JTC outcome

### F9 (COA Appeal)
- **Depends on:** Nothing (independent)
- **Enables:** Nothing (terminal)
- **Cascade depth:** 2 filings affected
- **If fails:** COA affirmance means binding precedent against you — carefully choose which issues to appeal
- **Mitigation:** Only appeal STRONGEST issues; weak issues get bad precedent

### F4 (42 USC §1983 Federal)
- **Depends on:** Nothing (independent)
- **Enables:** Nothing (terminal)
- **Cascade depth:** 1 filings affected
- **If fails:** Federal abstention sends case back to state court — but creates federal record of claims
- **Mitigation:** Plead Younger abstention exception (bad faith prosecution); file in state simultaneously

### F5 (Emergency Parenting Time)
- **Depends on:** F3
- **Enables:** Nothing (terminal)
- **Cascade depth:** 1 filings affected
- **If fails:** Denied parenting time continues — but denial creates additional due process claims
- **Mitigation:** Each denial = additional §1983 claim; document EVERY denial with specificity

### F8 (MSC Superintending Control)
- **Depends on:** F6, F9
- **Enables:** Nothing (terminal)
- **Cascade depth:** 1 filings affected
- **If fails:** MSC denial is final for state extraordinary relief — federal court remains
- **Mitigation:** MSC rarely grants superintending control — but filing creates record; federal §1983 is primary path

### F10 (Attorney Grievance)
- **Depends on:** Nothing (independent)
- **Enables:** Nothing (terminal)
- **Cascade depth:** 1 filings affected
- **If fails:** AGC may take no action — but complaint is on record for §1983 evidence
- **Mitigation:** AGC complaint demonstrates good faith and exhaustion of remedies

### F1 (Emergency Custody/TRO)
- **Depends on:** F3, F4, F5, F7
- **Enables:** Nothing (terminal)
- **Cascade depth:** 0 filings affected
- **If fails:** Emergency custody denied — but creates appellate record; file for regular custody modification
- **Mitigation:** Emergency requires 'immediate danger' — standard custody modification has lower bar

### F2 (PPO Termination)
- **Depends on:** F7
- **Enables:** Nothing (terminal)
- **Cascade depth:** 0 filings affected
- **If fails:** PPO remains — but void if underlying orders void (fruit of poisonous tree)
- **Mitigation:** PPO termination tied to fraud finding; if F7 succeeds, PPO falls automatically
