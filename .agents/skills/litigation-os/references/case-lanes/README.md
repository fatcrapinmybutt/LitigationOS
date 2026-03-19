# Case Lanes — Three-Lane Separation Model

## Iron Rule

**Watson/custody (Lane A) and Shady Oaks/housing (Lane B) are SEPARATE cases.**
They converge ONLY in Lane C when pursuing claims against Muskegon County and judges
whose misconduct spans both cases.

## Lane Overview

| Lane | Cases | Judge | Adversaries | MEEK | Actions |
|------|-------|-------|-------------|------|---------|
| **A: Custody/PPO** | 2024-001507-DC, 2023-5907-PP | McNeill | Watson family (6), Rusco (2) | 2, 3 | A1-A35 |
| **B: Housing** | 2025-002760-CZ | Hoopes | Shady Oaks, Homes of America, Alden Global | 1 | B1-B14 |
| **C: Convergence** | NEW consolidated | N/A | Muskegon County, 14th Circuit, Judges | 4, 5 | C1-C7 |

## Convergence Rules

- ✅ CAN cite McNeill custody misconduct to show county pattern (Lane C only)
- ✅ CAN aggregate damages across both lanes for federal §1983 (Lane C only)
- ✅ CAN reference both lanes when showing systemic judicial misconduct
- ❌ CANNOT mix Watson custody evidence into Shady Oaks filings
- ❌ CANNOT cite housing conditions in custody motions
- ❌ CANNOT merge case numbers or filing lanes
- ❌ CANNOT file Lane A exhibits with Lane B motions

## Lane Details

- [Lane A: Watson / Custody / PPO](lane-a-custody.md) — 35 legal actions
- [Lane B: Shady Oaks / Housing Harms](lane-b-housing.md) — 14 legal actions
- [Lane C: Convergence / County / Judges](lane-c-convergence.md) — 7 legal actions

## Evidence-to-Action Scoring

For each action across all 3 lanes:
1. Query atom stores — lane-filtered (only atoms from matching MEEK lane)
2. Score evidence strength: `(fact_atoms × 3 + citation_atoms × 2 + person_atoms × 1) × posture_weight`
3. Score authority backing: citations available ÷ citations needed
4. Score adversary vulnerability: contradiction_atoms targeting that adversary
5. Composite readiness: evidence × authority × vulnerability → 0-100

Lane C actions get bonus scoring from BOTH Lane A + Lane B evidence.
