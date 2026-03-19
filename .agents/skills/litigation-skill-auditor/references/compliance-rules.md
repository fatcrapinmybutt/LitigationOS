# Compliance Rules — Skill Auditor Reference

## Writing-Skills Standard — Compliance Rules

This document defines the authoritative compliance rules for the
litigation skill fleet. Every skill must comply with these rules.
The litigation-skill-auditor enforces these rules during audits.

---

## Rule Category 1: Structural Compliance

```yaml
COMP-STRUCT-001:
  rule: "SKILL.md filename must be ALL CAPS"
  severity: CRITICAL
  rationale: >
    The writing-skills standard specifies ALL CAPS for the primary
    skill definition file. This is not a convention — it's a hard
    requirement for skill discovery and loading.
  check_method: Verify filename is exactly "SKILL.md" (case-sensitive)
  remediation: Rename file to "SKILL.md"
  common_violations:
    - "skill.md" (all lowercase)
    - "Skill.md" (title case)
    - "SKILL.MD" (extension uppercase — may cause issues on case-sensitive systems)

COMP-STRUCT-002:
  rule: "gotchas.md must exist in skill root"
  severity: HIGH
  rationale: >
    Gotchas documentation prevents common failure modes and provides
    the anti-rationalization framework that keeps agents honest.
  check_method: Verify file exists at {skill_dir}/gotchas.md
  remediation: Create gotchas.md with required sections

COMP-STRUCT-003:
  rule: "references/ directory must exist with 2+ files"
  severity: MEDIUM
  rationale: >
    Reference files provide depth that SKILL.md cannot (due to 500-line
    limit). At least 2 reference files ensure adequate supporting detail.
  check_method: Verify directory exists and contains >= 2 .md files
  remediation: Create references/ directory and populate with relevant files

COMP-STRUCT-004:
  rule: "No non-standard files in skill directory"
  severity: LOW
  rationale: >
    Extraneous files (temp files, backups, drafts) clutter the skill
    directory and may confuse skill loading systems.
  allowed_files:
    - SKILL.md
    - gotchas.md
    - references/*.md
  check_method: List all files, flag any not in allowed list
  remediation: Remove or relocate extraneous files
```

---

## Rule Category 2: Metadata Compliance

```yaml
COMP-META-001:
  rule: "name field must match directory name exactly"
  severity: CRITICAL
  rationale: >
    The name field is the canonical identifier for the skill. It MUST
    match the directory name for skill discovery, dependency resolution,
    and cross-reference integrity. A mismatch breaks the entire fleet.
  check_method: Compare name field value to directory basename
  remediation: Update name field or rename directory

COMP-META-002:
  rule: "name must be kebab-case"
  severity: CRITICAL
  rationale: >
    Kebab-case (lowercase, hyphen-separated) is the standard naming
    convention for skills. It ensures URL-safe, filesystem-safe,
    and consistent identifiers across the fleet.
  pattern: "^[a-z][a-z0-9]*(-[a-z0-9]+)*$"
  check_method: Regex match against name field
  remediation: Convert name to kebab-case
  examples:
    valid: "litigation-authority-validator"
    invalid:
      - "litigation_authority_validator" (underscores)
      - "LitigationAuthorityValidator" (PascalCase)
      - "LITIGATION-AUTHORITY-VALIDATOR" (uppercase)

COMP-META-003:
  rule: "description must start with 'Use when...'"
  severity: HIGH
  rationale: >
    The "Use when..." prefix ensures descriptions are action-oriented
    and tell the skill routing system WHEN to invoke this skill.
    Descriptions that start with "This skill..." or "A tool for..."
    are passive and don't help with routing decisions.
  check_method: Verify description text starts with "Use when"
  remediation: Rewrite description to start with "Use when..."
  examples:
    valid: "Use when verifying MCR/MCL/MRE citations..."
    invalid:
      - "This skill validates citations..." (passive)
      - "Citation validation tool" (noun phrase)
      - "Validates citations and authority chains" (no routing context)

COMP-META-004:
  rule: "category must be 'discipline'"
  severity: HIGH
  rationale: >
    All litigation fleet skills use the "discipline" category to
    distinguish them from other skill types (utility, integration, etc.)
  check_method: Verify category field equals "discipline"
  remediation: Set category to "discipline"

COMP-META-005:
  rule: "triggers must have 3+ keywords"
  severity: HIGH
  rationale: >
    Triggers are how the routing system discovers skills. Fewer than
    3 triggers creates coverage gaps — users who describe the same
    need in different words won't reach the skill.
  check_method: Count items in triggers list
  remediation: Add triggers covering common phrasings of the skill's purpose

COMP-META-006:
  rule: "version must follow semver (MAJOR.MINOR.PATCH)"
  severity: LOW
  rationale: >
    Semantic versioning enables dependency management and compatibility
    checking across the fleet.
  pattern: "^\\d+\\.\\d+\\.\\d+$"
  check_method: Regex match against version field
  remediation: Convert to semver format

COMP-META-007:
  rule: "lane assignments must be present"
  severity: HIGH
  rationale: >
    Lane assignments tell the convergence system which skills apply
    to which case lanes. Without lane assignments, convergence cannot
    compute per-lane quality scores.
  check_method: Verify lanes field exists and contains valid values
  valid_values: [A, B, C]
  remediation: Add lane assignments based on skill's scope

COMP-META-008:
  rule: "court and case metadata must be present"
  severity: HIGH
  rationale: >
    Court and case metadata ensures skills are correctly scoped to
    Pigors v Watson in the 14th Judicial Circuit. Without this,
    skills could produce generic output inappropriate for this case.
  required_fields:
    - court: "14th Judicial Circuit, Muskegon County"
    - case: "Pigors v Watson"
  check_method: Verify both fields present with correct values
  remediation: Add court and case metadata
```

---

## Rule Category 3: Content Quality Compliance

```yaml
COMP-CONTENT-001:
  rule: "SKILL.md must be under 500 lines"
  severity: MEDIUM
  rationale: >
    The 500-line limit prevents skills from becoming monolithic.
    Detailed content belongs in references/ files. The SKILL.md
    should contain the decision tree, output contract, and essential
    protocol — not encyclopedic reference material.
  check_method: Count lines in SKILL.md
  remediation: Move detailed content to references/ files

COMP-CONTENT-002:
  rule: "Decision tree must be present in SKILL.md"
  severity: HIGH
  rationale: >
    Decision trees define the skill's execution logic. Without one,
    the skill is a passive reference document, not an actionable
    agent capability.
  check_method: Search for decision tree structure (headings, tree formatting)
  remediation: Add decision tree section

COMP-CONTENT-003:
  rule: "Output contract must be present in SKILL.md"
  severity: HIGH
  rationale: >
    Output contracts define what the skill produces and in what format.
    Without an output contract, downstream skills cannot consume this
    skill's output reliably.
  check_method: Search for output contract section with typed schema
  remediation: Add output contract with YAML schema

COMP-CONTENT-004:
  rule: "Anti-rationalization table must have 5+ rows"
  severity: CRITICAL
  rationale: >
    Anti-rationalization tables are the skill's immune system against
    the tendency of both humans and LLMs to explain away errors.
    Each row represents a documented failure mode with its rationalization
    pattern. Fewer than 5 rows means the skill hasn't been adequately
    threat-modeled.
  check_method: >
    Parse gotchas.md, find table with Excuse/Reality columns,
    count data rows (excluding header)
  remediation: >
    Identify the skill's top 5+ failure modes, document the
    rationalization pattern for each, and add to table

COMP-CONTENT-005:
  rule: "Lane-specific content must be present"
  severity: MEDIUM
  rationale: >
    Generic skills that don't differentiate between lanes produce
    generic output. Lane-specific sections ensure the skill's output
    is tailored to Lane A (custody), Lane B (housing), or Lane C
    (convergence) contexts.
  check_method: Search for lane-specific sections or references
  remediation: Add lane-specific content for each assigned lane
```

---

## Rule Category 4: Cross-Reference Compliance

```yaml
COMP-XREF-001:
  rule: "All dependencies must resolve to existing skills"
  severity: CRITICAL
  rationale: >
    A dependency on a non-existent skill means the skill expects
    functionality that doesn't exist. This causes runtime failures
    when the skill tries to invoke or consume from the dependency.
  check_method: >
    For each dependency name, verify directory exists in
    skills/ with valid SKILL.md
  remediation: Remove invalid dependencies or create missing skills

COMP-XREF-002:
  rule: "No circular dependencies"
  severity: CRITICAL
  rationale: >
    Circular dependencies (A→B→C→A) cause infinite loops in
    pipeline execution and make initialization order impossible.
  check_method: Build directed dependency graph, run cycle detection
  remediation: Break the cycle by removing the weakest dependency link

COMP-XREF-003:
  rule: "Integration references should be bidirectional"
  severity: MEDIUM
  rationale: >
    If skill A claims integration with skill B, skill B should
    acknowledge the integration with skill A. One-directional
    references indicate incomplete integration design.
  check_method: >
    Extract integration references from all skills, verify
    each reference has a corresponding reverse reference
  remediation: Add missing reverse references
```

---

## Severity Enforcement Policy

```
CRITICAL violations:
  - Must be fixed before skill is considered operational
  - Blocks any filing that depends on this skill
  - Auditor marks skill as "non-compliant"
  - Remediation deadline: IMMEDIATE (within 4 hours)

HIGH violations:
  - Must be fixed before next convergence cycle
  - Does not block filing but degrades quality score
  - Auditor marks skill as "degraded"
  - Remediation deadline: 24 hours

MEDIUM violations:
  - Should be fixed within 48 hours
  - Does not affect operational status
  - Auditor notes in audit report
  - Remediation deadline: 48 hours

LOW violations:
  - Fix when convenient
  - Does not affect any operational metric
  - Auditor notes as suggestion
  - Remediation deadline: Next scheduled maintenance
```
