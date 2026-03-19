# Convergence Engine Protocol

## Philosophy

**Convergence** reduces DNEW to zero (gap-closing).
**Emergence** surfaces non-obvious legal strategies, contradictions, and authority chains
that no single document contains (synthesis).

When citation networks, evidence atoms, and rule graphs reach critical mass,
the system stops just filling gaps and starts discovering connections invisible in any single source.

## Convergence Cycle

Execute cycles until DNEW = empty AND quality >= 95:

```
CYCLE N:
  1. litigation_self_test()        → PASS/FAIL (stack health)
  2. litigation_self_audit()       → quality score 0-100
  3. litigation_convergence_status()
     → DNEW: [new sources, new rules, new evidence]
     → BLOCKERS: [missing auth, corrupt PDF, unindexed dirs]
     → NEXT_PATCH: highest-leverage fix
  4. Execute NEXT_PATCH
  5. Re-audit → measure delta reduction

  IF DNEW = empty AND quality >= 95:
    → CONVERGED. Switch to EMERGENCE mode.
  ELSE:
    → CYCLE N+1
```

## Emergence Signals

After convergence, watch for:

1. **Cross-Graph Pattern Discovery** — Search matches nodes across multiple knowledge graphs; intersection reveals invisible patterns
2. **Authority Chain Completion** — Complete trace: FACT → PROPOSITION → AUTHORITY → ELEMENTS → EVIDENCE ATOMS → QUOTE REFS
3. **Contradiction Surface Mapping** — Records from different sources conflict (order vs transcript, party vs sworn testimony)
4. **Novel Strategy Synthesis** — Cross-referencing reveals untried combinations (authority + facts not yet briefed)

## Error Recovery

**Circuit Breaker:** 5 consecutive failures → OPEN → 60s cooldown → HALF_OPEN → test
- Check: `litigation_health(action="status")`
- Reset: `litigation_health(action="reset")`

See [quality-metrics.md](quality-metrics.md) for scoring details.
