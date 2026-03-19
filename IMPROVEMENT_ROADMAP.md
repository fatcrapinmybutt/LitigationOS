# LitigationOS Agent Ecosystem - IMPROVEMENT ROADMAP
**Created:** 2026-03-16 14:17:33**
**Based on:** Comprehensive Agent & Skill Ecosystem Audit

---

## 🎯 IMMEDIATE ACTIONS (This Week)

### 1. [CRITICAL] Resolve Dual copilot-instructions.md Files
**Files:** 
- C:\Users\andre\LitigationOS\copilot-instructions.md (34.83 KB)
- C:\Users\andre\LitigationOS\.github\copilot-instructions.md (33.46 KB)

**Status:** Nearly identical, creating context window overflow risk

**Steps:**
1. \diff\ the two files to confirm they're duplicates
2. Determine which is the canonical source
3. Delete or archive the duplicate
4. Add Git reference from deleted location to canonical source
5. Split merged copilot-instructions.md into domain-specific files:
   - agent-instructions.md (agent setup/config)
   - skill-instructions.md (skill development/usage)
   - protocol-instructions.md (EAGAIN, shell management)
   - memory-instructions.md (SQLite, memory config)

**Time estimate:** 1-2 hours
**Owner:** DevOps/Config

---

### 2. [CRITICAL] Audit Massive Skill Library
**Scope:** 1,158 skill folders across two locations

**Steps:**
1. Generate skill usage report:
   \\\powershell
   # Count which skills are actually referenced in agents/configs
   Get-ChildItem -Path ".\.agents" -Filter "*.agent.md" -Recurse | 
     Select-String -Pattern "skills/" | 
     Group-Object { [regex]::Match(, 'skills/([^/]+)').Groups[1].Value } |
     Sort-Object Count -Descending |
     Export-Csv skill_usage.csv
   \\\
2. Identify unused skills (count = 0)
3. Create archive folder: 00_SYSTEM/skills_archive/
4. Move unused skills to archive with metadata README
5. Document decision in SKILL_AUDIT_FOLLOW_UP.md

**Time estimate:** 4-8 hours
**Owner:** Engineering Lead

---

### 3. [CRITICAL] Review Lost Agents from Backup
**Finding:** backup_20260304_212018 contains 54 agents vs. 33 active
**Difference:** 21 agents were consolidated/removed

**Steps:**
1. \diff\ .agents directory vs. backup_20260304_212018/.copilot/agents
2. Identify the 21 removed agents
3. Create impact analysis for each:
   - Was it intentionally deprecated?
   - Do any agents still reference it?
   - Does it contain functionality in current agents?
4. Document findings in BACKUP_AGENT_AUDIT.md
5. Selectively restore if features were lost

**Time estimate:** 2-4 hours
**Owner:** Tech Lead

---

## 📊 HIGH PRIORITY TASKS (Next 1-2 Weeks)

### 4. Clean Trivial SKILL.md Files
**Files to delete/flesh out:**
- C:\Users\andre\LitigationOS\.agents\skills\cc-skill-continuous-learning\SKILL.md (202 bytes)
- C:\Users\andre\LitigationOS\.agents\skills\cc-skill-strategic-compact\SKILL.md (198 bytes)
- C:\Users\andre\LitigationOS\.agents\skills\ffuf-claude-skill\SKILL.md (490 bytes)
- C:\Users\andre\LitigationOS\skills\agents\cc-skill-continuous-learning\SKILL.md (202 bytes)
- C:\Users\andre\LitigationOS\skills\agents\cc-skill-strategic-compact\SKILL.md (198 bytes)
- C:\Users\andre\LitigationOS\skills\agents\ffuf-claude-skill\SKILL.md (490 bytes)
- C:\Users\andre\LitigationOS\skills\my-issues\SKILL.md (340 bytes)

**Steps:**
1. Review each file
2. If duplicate across both locations, keep only one
3. If no content, delete or add proper SKILL.md template
4. Document cleanup in CLEANUP_LOG.md

**Time estimate:** 0.5 hours
**Owner:** Engineering

---

### 5. Archive Old Session Data
**File:** C:\Users\andre\LitigationOS\.copilot\session-store.db (19 MB)

**Steps:**
1. Backup current database
2. Export useful session history (if any) to JSON
3. Truncate database to clear old sessions
4. Archive to 00_SYSTEM/backups/session-store-archive-<date>.db
5. Monitor if new sessions grow similarly

**Time estimate:** 1 hour
**Owner:** DevOps

---

### 6. Validate OMEGA Agent Duplication
**Files:**
- OMEGA-AGENT-ARCHITECT.md (41 KB) — Full implementation
- OMEGA-ARCHITECT-AGENT.md (1.67 KB) — Stub
- OMEGA-ENGINEER-AGENT.md (1.44 KB) — Stub
- OMEGA-LITIGATOR-AGENT.md (2.09 KB) — Stub
- OMEGA-SENTINEL-AGENT.md (1.72 KB) — Stub

**Steps:**
1. Confirm stub agents properly reference parent implementation
2. Verify no divergent functionality in stubs
3. Add version control comments explaining relationship
4. Document in OMEGA_ARCHITECTURE.md
5. Consider consolidation if redundant

**Time estimate:** 1-2 hours
**Owner:** Engineering

---

## 📈 MEDIUM PRIORITY TASKS (Next Month)

### 7. Expand AGENTS.md Documentation
**Current status:** 1.61 KB (minimal)
**Goal:** Comprehensive agent capability matrix

**Content to add:**
- Agent purpose/description
- Skills each agent depends on
- Input/output specifications
- Version/maintenance status
- Cross-references to instruction files
- Performance/cost characteristics

**Template:**
\\\markdown
## Agent: [name]
- **Purpose:** What does this agent do?
- **Size:** X KB
- **Skills:** [list dependencies]
- **Use cases:** [scenarios]
- **Status:** Active/Deprecated/Experimental
- **Last updated:** Date
- **Owner:** Team/person
\\\

**Time estimate:** 2-4 hours
**Owner:** Tech Writer + Engineer

---

### 8. Split Instruction Files by Domain
**Current:** Monolithic copilot-instructions.md (34 KB)
**Target:** Domain-specific files each <15 KB

**Structure:**
\\\
.github/instructions/
  ├── agent-instructions.md (setup/activation)
  ├── skill-instructions.md (development/usage)
  ├── protocol-instructions.md (EAGAIN, shell limits)
  ├── memory-instructions.md (SQLite, memory mgmt)
  ├── error-handling-instructions.md (debugging)
  └── INDEX.md (master navigation)
\\\

**Time estimate:** 2-3 hours
**Owner:** Tech Lead

---

### 9. Add Usage Metrics to Agents
**Goal:** Identify dead/unused agents

**Steps:**
1. Add telemetry to agent invocation (if not present)
2. Log agent usage to metrics database
3. Generate monthly usage report
4. Tag agents as "high-use", "medium-use", "low-use", "unused"
5. Plan deprecation for unused agents after 3 months

**Time estimate:** 4-6 hours
**Owner:** Engineering

---

## 📋 LOWER PRIORITY (Next Quarter)

### 10. Consolidate Duplicate Skills Across Locations
**Finding:** .agents/skills/ and /skills/ contain overlapping skill definitions

**Example duplicates:**
- cc-skill-continuous-learning (in both)
- cc-skill-strategic-compact (in both)
- ffuf-claude-skill (in both)
- agents subfolder exists in both

**Steps:**
1. Full diff of both skill directories
2. Consolidate duplicates (keep 1, reference other)
3. Add symlinks or documented duplicates
4. Update .skill-lock.json to reflect consolidation
5. Document rationale for kept vs. removed

**Time estimate:** 4-6 hours
**Owner:** Engineering

---

## 📊 SUCCESS METRICS

After completing these improvements, you should see:

| Metric | Current | Target | Impact |
|--------|---------|--------|--------|
| Duplicate instruction files | 2 | 1 | -30 KB memory, better UX |
| Trivial skill files | 7 | 0 | -2 KB, cleaner filesystem |
| Unused skills (archived) | 1,158 | ~900-1,000 | 20-30% reduction, clarity |
| Legacy agents reviewed | 54 unknown | Categorized | Recover lost functionality |
| Skill duplication | High | Low | Reduced confusion |
| Copilot-instructions.md size | 34 KB | <15 KB each | Avoid context overflow |
| AGENTS.md completeness | 1.6 KB | 15+ KB | Better documentation |
| session-store.db size | 19 MB | <5 MB | Better performance |

---

## 🚀 ROLLOUT TIMELINE

**Week 1 (Critical):**
- Resolve dual copilot-instructions.md
- Begin skill library audit
- Review backup agents

**Week 2-3 (High Priority):**
- Complete skill audit
- Clean trivial files
- Archive session data
- Validate OMEGA structure

**Month 2-3 (Medium):**
- Expand documentation
- Split instruction files
- Add usage metrics
- Consolidate duplicates

---

## 📞 QUESTIONS TO ANSWER

1. **Are 945 + 213 = 1,158 skills intentional?**
   - Is there a reason for dual locations?
   - Should they be merged?

2. **Why were 21 agents removed from active set?**
   - Were features consolidated?
   - Should any be restored?

3. **What's the purpose of OMEGA stub agents?**
   - Are they proxies/wrappers?
   - Can they be consolidated?

4. **Is session-store.db growth expected?**
   - Should we rotate/archive periodically?
   - Is there a retention policy?

---

## 🔗 RELATED DOCUMENTS

- Full audit report: LITIGATION_OS_AGENT_SKILL_AUDIT_REPORT.md
- Agent definitions: .agents/*.agent.md
- Backup inventory: 00_SYSTEM/backups/
- Configuration: config/
- Instructions: .github/instructions/

