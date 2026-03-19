# Audit Checklist — Skill Auditor Reference

## Master Audit Checklist

This checklist is applied to every skill in the litigation fleet.
Each item has a check type, severity, and pass/fail criteria.

---

## Section 1: File Structure Checks

```yaml
CHECK-FS-001:
  name: SKILL.md Exists
  type: file_structure
  severity: CRITICAL
  check: File named exactly "SKILL.md" (ALL CAPS) exists in skill root
  pass: File exists with correct case
  fail: File missing or wrong case (e.g., skill.md, Skill.md)
  auto_fixable: false
  notes: ALL CAPS is a hard requirement of writing-skills standard

CHECK-FS-002:
  name: gotchas.md Exists
  type: file_structure
  severity: HIGH
  check: File named "gotchas.md" exists in skill root
  pass: File exists
  fail: File missing
  auto_fixable: false

CHECK-FS-003:
  name: references/ Directory Exists
  type: file_structure
  severity: MEDIUM
  check: Directory named "references/" exists in skill root
  pass: Directory exists and contains at least 2 files
  fail: Directory missing or empty
  auto_fixable: false

CHECK-FS-004:
  name: Reference File Minimum Length
  type: file_structure
  severity: LOW
  check: Each file in references/ has at least 50 lines
  pass: All reference files >= 50 lines
  fail: Any reference file < 50 lines
  auto_fixable: false
  notes: Short reference files indicate insufficient depth

CHECK-FS-005:
  name: No Extraneous Files
  type: file_structure
  severity: LOW
  check: No unexpected files in skill directory
  expected_files:
    - SKILL.md
    - gotchas.md
    - references/ (directory)
    - references/*.md (reference files)
  pass: Only expected files present
  fail: Unexpected files found (temp files, backups, etc.)
```

## Section 2: Metadata Checks

```yaml
CHECK-MD-001:
  name: Name Field Matches Directory
  type: metadata
  severity: CRITICAL
  check: >
    "name:" field in SKILL.md metadata matches the directory name
    exactly (kebab-case)
  pass: name field == directory name
  fail: Mismatch between name field and directory
  example_pass: "name: litigation-authority-validator" in dir litigation-authority-validator/
  example_fail: "name: authority_validator" in dir litigation-authority-validator/

CHECK-MD-002:
  name: Name is Kebab-Case
  type: metadata
  severity: CRITICAL
  check: Name field uses kebab-case (lowercase, hyphens only)
  pattern: "^[a-z][a-z0-9]*(-[a-z0-9]+)*$"
  pass: Matches kebab-case pattern
  fail: Contains underscores, uppercase, spaces, or special chars

CHECK-MD-003:
  name: Description Starts with "Use when..."
  type: metadata
  severity: HIGH
  check: Description field begins with "Use when"
  pass: Description starts with "Use when" (case-insensitive first word)
  fail: Description starts with anything else
  rationale: >
    "Use when..." format ensures descriptions are actionable and
    tell the routing system when to invoke this skill

CHECK-MD-004:
  name: Category is "discipline"
  type: metadata
  severity: HIGH
  check: Category field is exactly "discipline"
  pass: category == "discipline"
  fail: Any other value
  notes: All litigation fleet skills use "discipline" category

CHECK-MD-005:
  name: Triggers Minimum Count
  type: metadata
  severity: HIGH
  check: metadata.triggers list has at least 3 entries
  pass: len(triggers) >= 3
  fail: len(triggers) < 3
  notes: Fewer than 3 triggers = insufficient discoverability

CHECK-MD-006:
  name: Version Follows Semver
  type: metadata
  severity: LOW
  check: Version field matches semver pattern (MAJOR.MINOR.PATCH)
  pattern: "^\\d+\\.\\d+\\.\\d+$"
  pass: Matches semver pattern
  fail: Non-semver version string

CHECK-MD-007:
  name: Lane Assignments Present
  type: metadata
  severity: HIGH
  check: Metadata includes lane assignments (A, B, C)
  pass: At least one lane referenced
  fail: No lane information
  notes: >
    Every skill must know which lanes it operates on
    for proper routing and convergence tracking

CHECK-MD-008:
  name: Court/Case Metadata
  type: metadata
  severity: HIGH
  check: Metadata includes court and case information
  required_fields:
    - court (14th Judicial Circuit, Muskegon County)
    - case (Pigors v Watson)
  pass: Both fields present
  fail: Either field missing
```

## Section 3: Content Quality Checks

```yaml
CHECK-CQ-001:
  name: SKILL.md Line Count
  type: content_quality
  severity: MEDIUM
  check: SKILL.md has fewer than 500 lines
  pass: line_count < 500
  fail: line_count >= 500
  notes: >
    Skills exceeding 500 lines should be split or
    content moved to references/

CHECK-CQ-002:
  name: Decision Tree Present
  type: content_quality
  severity: HIGH
  check: SKILL.md contains a decision tree section
  detection: Look for "Decision Tree" heading or tree-like structure
  pass: Decision tree found
  fail: No decision tree
  notes: Decision trees are required for routing and execution logic

CHECK-CQ-003:
  name: Output Contract Present
  type: content_quality
  severity: HIGH
  check: SKILL.md contains an output contract section
  detection: Look for "Output Contract" heading or YAML schema
  pass: Output contract found with typed fields
  fail: No output contract or untyped contract

CHECK-CQ-004:
  name: Anti-Rationalization Table
  type: content_quality
  severity: CRITICAL
  check: gotchas.md contains anti-rationalization table with 5+ rows
  detection: Look for table with Excuse/Reality/Consequence columns
  pass: Table found with >= 5 data rows (not counting header)
  fail: Table missing, wrong format, or < 5 rows
  notes: >
    This is the skill's immune system against rationalized failures.
    CRITICAL because weak tables lead to unchecked error propagation.

CHECK-CQ-005:
  name: Lane-Specific Content
  type: content_quality
  severity: MEDIUM
  check: SKILL.md contains lane-specific sections or notes
  detection: Look for Lane A / Lane B / Lane C references
  pass: Lane-specific content present
  fail: Generic content without lane differentiation
```

## Section 4: Cross-Reference Checks

```yaml
CHECK-XR-001:
  name: Dependencies Exist
  type: cross_reference
  severity: CRITICAL
  check: Every skill listed in "dependencies" exists in the fleet
  method: >
    For each dependency name, verify a directory with that name
    exists in the skills directory with a valid SKILL.md
  pass: All dependencies resolve
  fail: Any dependency points to non-existent skill

CHECK-XR-002:
  name: Integration Points Exist
  type: cross_reference
  severity: HIGH
  check: Every skill mentioned in "Integration Points" exists
  method: Extract skill names from integration section, verify each
  pass: All mentioned skills exist
  fail: Any mentioned skill doesn't exist

CHECK-XR-003:
  name: No Circular Dependencies
  type: cross_reference
  severity: CRITICAL
  check: Dependency graph has no cycles
  method: Build directed graph from all dependencies, check for cycles
  pass: No cycles found
  fail: Cycle detected (list the cycle path)

CHECK-XR-004:
  name: Bidirectional References
  type: cross_reference
  severity: MEDIUM
  check: >
    If skill A lists skill B in integration points,
    skill B should reference skill A
  pass: All integration references are bidirectional
  fail: One-directional references found
  notes: One-directional references suggest incomplete integration
```

## Section 5: Trigger Coverage Checks

```yaml
CHECK-TC-001:
  name: No Duplicate Triggers
  type: trigger_coverage
  severity: MEDIUM
  check: No trigger keyword is exactly duplicated within a skill
  pass: All triggers within each skill are unique
  fail: Duplicate triggers found

CHECK-TC-002:
  name: Trigger Overlap Analysis
  type: trigger_coverage
  severity: MEDIUM
  check: >
    Identify triggers shared between multiple skills.
    Overlap is acceptable if skills handle different aspects.
  pass: All overlaps have disambiguation rules
  fail: Ambiguous overlaps with no resolution strategy

CHECK-TC-003:
  name: Coverage Gap Detection
  type: trigger_coverage
  severity: HIGH
  check: >
    Common litigation tasks map to at least one skill's triggers.
    Check against standard litigation task taxonomy.
  standard_tasks:
    - citation checking → litigation-authority-validator
    - brief writing → litigation-appellate-strategist
    - filing preparation → litigation-filing-packager
    - evidence management → litigation-brain-spec
    - quality assurance → litigation-convergence-orchestrator
    - pipeline execution → litigation-pipeline-commander
    - fleet management → litigation-skill-auditor
  pass: All standard tasks covered
  fail: Any standard task has no trigger path
```

---

## Audit Execution Protocol

```
1. ENUMERATE: List all skills from fleet manifest
2. FOR EACH skill:
   a. Run all Section 1 (File Structure) checks
   b. Run all Section 2 (Metadata) checks
   c. Run all Section 3 (Content Quality) checks
   d. Run all Section 4 (Cross-Reference) checks (needs fleet context)
3. Run all Section 5 (Trigger Coverage) checks (fleet-wide)
4. SCORE each skill using compliance formula
5. GENERATE audit report
6. UPDATE fleet manifest with new scores
```
