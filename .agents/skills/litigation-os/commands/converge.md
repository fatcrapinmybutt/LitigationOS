# Convergence Workflow Command

## When to Use

- Running convergence cycles to close knowledge gaps
- Measuring system quality and readiness
- Triggering emergence (cross-graph pattern discovery)
- Pre-filing quality assurance

## Quick Start

```
# Full convergence cycle
/converge                     → Run cycle until DNEW=empty, quality>=95

# Quality check only
/converge --audit             → Score only, no patches

# Targeted convergence
/converge --lane A            → Converge Lane A (custody) only
/converge --phase gaps        → Focus on gap tickets only

# Emergence mode
/converge --emerge            → Post-convergence pattern discovery
```

## Convergence Cycle Protocol

```
CYCLE N:
  1. HEALTH CHECK     → litigation_self_test()
  2. QUALITY AUDIT    → litigation_self_audit() → score 0-100
  3. STATUS CHECK     → litigation_convergence_status()
     → DNEW: [new sources, new rules, new evidence]
     → BLOCKERS: [missing auth, corrupt PDF, unindexed dirs]
     → NEXT_PATCH: highest-leverage fix
  4. EXECUTE PATCH    → Apply NEXT_PATCH
  5. RE-AUDIT         → Measure delta reduction

  IF DNEW = empty AND quality >= 95:
    → CONVERGED. Switch to EMERGENCE mode.
  ELSE:
    → CYCLE N+1
```

## Quality Thresholds

| Score | Status | Action |
|-------|--------|--------|
| 95-100 | **CONVERGED** | Switch to emergence |
| 80-94 | **GOOD** | Continue cycles |
| 60-79 | **NEEDS WORK** | Focus on blockers |
| < 60 | **CRITICAL** | Major repair needed |

## Emergence Signals

After convergence (quality >= 95), watch for:

1. **Cross-Graph Pattern** — Nodes match across multiple knowledge graphs
2. **Authority Chain Completion** — Full trace: FACT → PROPOSITION → AUTHORITY → ELEMENTS → EVIDENCE → QUOTES
3. **Contradiction Surface** — Records from different sources conflict
4. **Novel Strategy** — Untried authority + facts combinations

Dispatches to: **litigation-convergence-orchestrator**

## Blocker Resolution

| Blocker Type | Resolution |
|-------------|------------|
| Missing authority | → **litigation-authority-validator** |
| Corrupt PDF | → Skip + log + **litigation-evidence-harvester** for alternatives |
| Unindexed directory | → **litigation-pipeline-commander** Phase 9 |
| FTS desync | → `litigation_self_test()` rebuild |
| Circuit breaker OPEN | → Wait 60s or `litigation_health(action="reset")` |

## Cross-References

- [Convergence Engine](../references/convergence/README.md)
- [Quality Metrics](../references/convergence/quality-metrics.md)
- [Fleet Dispatch](../references/fleet/dispatch-matrix.md)
