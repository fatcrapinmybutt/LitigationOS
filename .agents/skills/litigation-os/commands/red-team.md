# Red Team Workflow Command

## When to Use

- Stress-testing ANY filing before submission to court
- Simulating opposing counsel's response to your arguments
- Identifying weaknesses in evidence, authority, or procedure
- Pre-filing adversarial review (MANDATORY in MODE:FILE_READY)

## Quick Start

```
# Red team a specific filing
/red-team filing "Motion to Modify Parenting Time"

# Red team a legal theory
/red-team theory "IIED claim against Amy Watson"

# Red team all pending filings
/red-team --all --lane A

# Simulate opposing counsel
/red-team --persona "defense-counsel" --filing B3

# Simulate judge perspective
/red-team --persona "judge-mcneill" --filing A12
```

## Attack Vector Taxonomy

### I. Procedural Attacks
1. **Jurisdiction defect** — Court lacks subject matter or personal jurisdiction
2. **Venue improper** — Wrong county or division
3. **Service defect** — Improper method, timing, or proof
4. **Statute of limitations** — Claim time-barred
5. **Standing defect** — Plaintiff lacks injury-in-fact
6. **Capacity defect** — Wrong party name or legal capacity
7. **Failure to exhaust** — Administrative remedies not exhausted
8. **Res judicata / Collateral estoppel** — Prior adjudication bars claim

### II. Substantive Attacks
9. **Element failure** — One or more elements unsupported by evidence
10. **Authority weakness** — Cited authority distinguishable or overruled
11. **Evidence gap** — Key fact asserted without evidence support
12. **Contradicted fact** — Your assertion contradicted by record evidence
13. **Hearsay exposure** — Key evidence inadmissible without exception
14. **Privilege claim** — Evidence subject to privilege objection
15. **Weight vs admissibility** — Evidence admissible but weak

### III. Strategic Attacks
16. **Remedy mismatch** — Relief requested not available for the claim
17. **Proportionality** — Requested relief disproportionate to harm shown
18. **Credibility** — Key witness impeachable
19. **Alternative explanation** — Facts support opposing interpretation
20. **Policy argument** — Ruling would create bad precedent
21. **Equitable defense** — Unclean hands, laches, estoppel

### IV. Formatting/Compliance
22. **Page limit exceeded** — MCR page limits violated
23. **Required section missing** — TOC, TOA, certificate of service
24. **Citation format error** — Non-standard citations
25. **Caption error** — Wrong case number, parties, or court

## Scoring

Each filing receives a Red Team Score (0-100):

| Score | Meaning |
|-------|---------|
| 90-100 | **BATTLE-READY** — File it. Minor nits only. |
| 75-89 | **STRONG** — Address flagged items, then file. |
| 50-74 | **VULNERABLE** — Significant weaknesses. Revise. |
| < 50 | **EXPOSED** — Major structural problems. Rebuild. |

## Output Contract

```
[VR] RED_TEAM_REPORT
  Score: 87/100 (STRONG)
  Attack Vectors Found: 4
  Critical: 0
  Major: 1 — Element 3 of IIED (severity) needs additional evidence
  Minor: 3 — Citation format (2), missing TOA entry (1)
  Mitigations Applied: 2
  Remaining Actions: Fix severity evidence + TOA
```

Dispatches to: **litigation-red-team**

## Cross-References

- [Fleet Dispatch](../references/fleet/dispatch-matrix.md)
- [Case Lanes](../references/case-lanes/README.md) — Lane-specific attack vectors
