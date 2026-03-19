# Gotchas — litigation-skill-auditor

## Anti-Rationalization Table

| # | Excuse (The Lie) | Reality (The Truth) | Consequence |
|---|-----------------|---------------------|-------------|
| 1 | "The skill works fine in practice — compliance with writing-skills format is just bureaucracy." | Format compliance IS functional compliance. The writing-skills standard ensures skills are machine-parseable, discoverable by triggers, and interoperable through standardized output contracts. A "working" skill that doesn't follow the standard is a ticking time bomb. | Non-compliant skills break trigger routing, output contract validation, and cross-reference resolution. In a 25-skill fleet, one non-compliant skill can cascade failures to every skill that references it. |
| 2 | "We don't need 5 anti-rationalization rows — 2 or 3 covers the main risks." | Anti-rationalization tables exist because humans (and LLMs) rationalize failures in predictable patterns. Each row represents a documented failure mode. Fewer than 5 rows means you haven't thought hard enough about how this skill can fail. The number 5 is a MINIMUM, not a target. | Skills with weak anti-rationalization tables produce agents that rationalize their way past errors. In litigation, a rationalized error becomes a court filing defect. The table is the skill's immune system — weaken it and infections get through. |
| 3 | "Cross-reference integrity doesn't matter — skills are independent modules." | Skills in this fleet are deeply interconnected. litigation-authority-validator feeds into litigation-filing-packager which depends on litigation-brain-spec. A broken cross-reference means a skill expects integration that doesn't exist, leading to silent failures during pipeline execution. | Broken cross-references cause Phase 7 (Merge) failures in the OMEGA pipeline, convergence score miscalculations, and filing packages with missing components. In Pigors v Watson, a broken reference between Lane A and Lane C skills caused a 3-day delay. |
| 4 | "Trigger coverage gaps are fine — users can just invoke skills directly." | Direct invocation requires the user to know which skill to call. The entire point of triggers is automatic routing — when a user says "check my citations," the system routes to litigation-authority-validator without the user knowing that skill's name. Coverage gaps = dead zones where requests go unhandled. | In active litigation, attorneys type natural language requests. If "validate my authority section" doesn't trigger litigation-authority-validator because "authority section" isn't in the trigger list, the request either fails silently or routes to the wrong skill. Both outcomes risk filing errors. |
| 5 | "The fleet manifest is just documentation — it doesn't affect anything operational." | The fleet manifest is the source of truth for skill discovery, dependency resolution, and compliance tracking. Without an accurate manifest, the system cannot verify that all 25 skills are operational, that dependencies are satisfied, or that coverage is complete. | An outdated manifest means the system reports "all skills healthy" when degraded skills exist. During a filing deadline, discovering that a critical skill has been non-compliant for weeks — because the manifest wasn't updated — is catastrophic. |
| 6 | "Auditing after every skill edit is overkill — monthly audits are sufficient." | Skills are edited frequently during active litigation. A monthly audit means up to 30 days of undetected non-compliance. In Pigors v Watson, with three active lanes and court deadlines, a month of skill drift can corrupt dozens of filings. | Monthly audits create a false sense of security. By the time the audit runs, non-compliant skills have produced non-compliant outputs that fed into other skills, pipelines, and convergence cycles. Audit-on-edit catches problems at the source. |
| 7 | "The auditor itself doesn't need to follow writing-skills standard — it's meta-level." | The auditor is a skill like any other. If it doesn't follow the standard it enforces, it's hypocritical and likely contains the same defects it's supposed to detect. Meta-tools that exempt themselves from their own rules always degrade over time. | A non-compliant auditor produces unreliable audit results. Other skills can't integrate with it properly, its triggers don't work in the routing system, and its output contract can't be consumed by litigation-convergence-orchestrator. Practice what you preach. |

---

## Common Failure Modes

### 1. Audit Scope Creep
- **What happens**: Auditor starts modifying skills instead of just auditing them
- **How to prevent**: Strict read-only audit protocol — auditor reports findings, skill owners fix them
- **Lane risk**: HIGH — unauthorized modifications can break skills during active litigation

### 2. False Compliance
- **What happens**: Skill passes checklist but substantive content is weak or wrong
- **How to prevent**: Checklist includes content quality checks, not just structural presence
- **Lane risk**: MEDIUM — structural compliance without substantive quality is hollow

### 3. Manifest Drift
- **What happens**: Fleet manifest doesn't match actual filesystem state
- **How to prevent**: Manifest refresh is triggered by every audit; includes filesystem scan
- **Lane risk**: HIGH — stale manifests cause skill discovery failures

### 4. Circular Dependency Blindness
- **What happens**: Circular dependencies introduced gradually (A→B→C→A) not detected
- **How to prevent**: Full dependency graph analysis at every cross-reference audit
- **Lane risk**: CRITICAL — circular dependencies cause infinite loops in pipeline execution

### 5. Trigger Collision
- **What happens**: Same trigger keyword maps to multiple skills with no disambiguation
- **How to prevent**: Trigger coverage audit detects overlaps; overlaps require explicit resolution rules
- **Lane risk**: MEDIUM — ambiguous routing delays litigation tasks

---

## Meta-Auditor Specific Gotchas

### Self-Audit Paradox
The auditor cannot fully audit itself — this is a known limitation. Mitigation:
- The auditor's own compliance is verified by manual review quarterly
- The auditor runs its checklist against its own SKILL.md as a basic self-test
- Any modifications to the auditor require sign-off from two skill authors

### Audit Fatigue
Running too many audits with too many findings causes teams to ignore results:
- Prioritize CRITICAL and HIGH findings
- Batch LOW findings for periodic cleanup
- Track finding resolution rate — declining resolution = audit fatigue

### Version Drift
Skills update independently. The auditor must handle version mismatches:
- Audit against the LATEST writing-skills standard
- Flag skills more than 2 minor versions behind
- Major version changes require full re-audit of all dependent skills

---

## Integration Gotchas

- **litigation-convergence-orchestrator** consumes audit results to adjust quality scores — audit report format must match expected schema
- **litigation-pipeline-commander** may skip phases for non-compliant skills — auditor findings directly affect pipeline execution
- **ALL SKILLS** in the fleet are audit targets — the auditor must not have favorites or blind spots
- Fleet manifest is consumed by external tools (LitigationOS Desktop) — manifest format is a public contract
- Audit scheduling interacts with convergence cycle scheduling — avoid running both simultaneously on the same skill
