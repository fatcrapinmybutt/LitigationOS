# Validation Rules — Authority Validator Reference

## Rule Categories

### Category 1: Format Validation Rules

```yaml
RULE-FMT-001:
  name: Statute Format Check
  type: format
  description: MCL citations must follow MCL § [chapter].[section] format
  pattern: "MCL §? ?\\d+\\.\\d+"
  examples_valid:
    - "MCL § 722.23"
    - "MCL 722.23"
    - "MCL § 722.23(a)"
  examples_invalid:
    - "Michigan Compiled Laws 722.23"
    - "M.C.L. § 722.23"
    - "MCL sec. 722.23"
  severity: HIGH
  auto_fixable: true

RULE-FMT-002:
  name: Court Rule Format Check
  type: format
  description: MCR citations must follow MCR [chapter].[rule] format
  pattern: "MCR \\d+\\.\\d+"
  examples_valid:
    - "MCR 2.116(C)(10)"
    - "MCR 3.210"
    - "MCR 7.212(C)(7)"
  examples_invalid:
    - "Michigan Court Rule 2.116"
    - "M.C.R. 2.116(C)(10)"
    - "Court Rule 2.116"
  severity: HIGH
  auto_fixable: true

RULE-FMT-003:
  name: Evidence Rule Format Check
  type: format
  description: MRE citations must follow MRE [rule] format
  pattern: "MRE \\d+"
  examples_valid:
    - "MRE 801"
    - "MRE 403"
    - "MRE 804(b)(1)"
  examples_invalid:
    - "Michigan Rule of Evidence 801"
    - "FRE 801"  # Federal rule — wrong jurisdiction
    - "Evidence Rule 801"
  severity: HIGH
  auto_fixable: true

RULE-FMT-004:
  name: Michigan Case Citation Format
  type: format
  description: >
    Michigan case citations require volume, reporter, page, pinpoint,
    parallel NW2d citation, and year
  pattern: "[Name] v [Name], \\d+ Mich( App)? \\d+, \\d+; \\d+ NW2d \\d+ \\(\\d{4}\\)"
  examples_valid:
    - "Smith v Jones, 500 Mich 123, 130; 900 NW2d 456 (2023)"
    - "Smith v Jones, 340 Mich App 123, 130; 900 NW2d 456 (2023)"
  examples_invalid:
    - "Smith v Jones, 500 Mich 123 (2023)"         # missing pinpoint and NW2d
    - "Smith v. Jones, 500 Mich 123, 130 (2023)"   # period after v (Michigan omits)
    - "Smith v Jones, 900 NW2d 456 (2023)"          # missing official reporter
  severity: CRITICAL
  auto_fixable: false

RULE-FMT-005:
  name: Unpublished Opinion Disclosure
  type: format
  description: Unpublished COA opinions must be identified as such per MCR 7.215(C)(1)
  required_text: "unpublished"
  examples_valid:
    - "Smith v Jones, unpublished per curiam opinion of the Court of Appeals, issued January 15, 2024 (Docket No. 365432)"
  examples_invalid:
    - "Smith v Jones, Mich App, Docket No. 365432 (2024)"  # not identified as unpublished
  severity: CRITICAL
  auto_fixable: false
```

### Category 2: Existence Validation Rules

```yaml
RULE-EXT-001:
  name: Statute Existence
  type: existence
  description: Verify MCL section exists in current compiled laws
  method: Cross-reference against MCL table of contents and section index
  severity: CRITICAL
  notes: LLM-generated statutes are a known risk — ALWAYS verify

RULE-EXT-002:
  name: Case Existence
  type: existence
  description: Verify case exists at cited reporter volume and page
  method: Cross-reference against reporter indices
  severity: CRITICAL
  notes: >
    This is the #1 AI-assisted litigation risk. LLMs generate
    plausible but non-existent cases. EVERY case citation must be
    verified against actual reporter volumes.

RULE-EXT-003:
  name: Rule Existence
  type: existence
  description: Verify MCR/MRE rule exists and has cited subrule
  method: Cross-reference against current court rules
  severity: HIGH
  notes: Rules are occasionally renumbered or consolidated

RULE-EXT-004:
  name: Pinpoint Existence
  type: existence
  description: Verify pinpoint page contains the cited proposition
  method: Review cited page for matching legal proposition
  severity: HIGH
  notes: Correct case but wrong page is a common LLM error
```

### Category 3: Currency Validation Rules

```yaml
RULE-CUR-001:
  name: Statute Currency
  type: currency
  description: Verify statute has not been amended or repealed since citation
  check_against: Latest legislative session acts
  severity: CRITICAL
  notes: MCL 722.23 was last amended by 2023 PA 43 — verify current text

RULE-CUR-002:
  name: Case Currency — Overruled
  type: currency
  description: Verify case has not been overruled by higher court
  check_against: Subsequent appellate history
  severity: CRITICAL
  notes: Citing overruled authority is sanctionable under MCR 1.109(E)

RULE-CUR-003:
  name: Case Currency — Distinguished
  type: currency
  description: Check if case has been distinguished on relevant grounds
  check_against: Citing references in subsequent cases
  severity: MEDIUM
  notes: Distinguished cases are still valid but may be weakened

RULE-CUR-004:
  name: Rule Currency
  type: currency
  description: Verify court rule has not been amended by administrative order
  check_against: Michigan Supreme Court administrative orders
  severity: HIGH
  notes: COVID-era administrative orders modified many MCR provisions

RULE-CUR-005:
  name: Local Rule Currency
  type: currency
  description: Verify 14th Circuit local rules are current
  check_against: 14th Circuit administrative orders and website
  severity: MEDIUM
  notes: Local rules change more frequently than MCR
```

### Category 4: Chain Completeness Rules

```yaml
RULE-CHN-001:
  name: Primary Authority Required
  type: chain
  description: Every legal proposition must cite at least one primary authority
  severity: CRITICAL

RULE-CHN-002:
  name: Binding vs Persuasive
  type: chain
  description: Primary authority should be binding in the 14th Circuit
  binding_hierarchy:
    - Michigan Supreme Court (binding on all Michigan courts)
    - Michigan Court of Appeals published (binding unless conflicting panels)
    - Michigan Court of Appeals unpublished (persuasive only)
    - Federal courts (persuasive on state law questions)
    - Other state courts (persuasive only)
  severity: HIGH

RULE-CHN-003:
  name: Pinpoint Required
  type: chain
  description: Case citations must include pinpoint page reference
  severity: MEDIUM

RULE-CHN-004:
  name: Parenthetical Recommended
  type: chain
  description: Supporting authorities should include parenthetical explanations
  severity: LOW

RULE-CHN-005:
  name: Multiple Authority Preferred
  type: chain
  description: Strong propositions should cite 2+ supporting authorities
  severity: LOW
```

### Category 5: Lane-Specific Rules

```yaml
RULE-LANE-A-001:
  name: Best Interest Factor Authority
  type: lane_specific
  lane: A
  description: >
    Each of the 12 best-interest factors (MCL 722.23(a)-(l)) addressed
    in a filing must cite the factor statute AND at least one case
    interpreting that specific factor.
  severity: HIGH

RULE-LANE-B-001:
  name: Housing Code Authority
  type: lane_specific
  lane: B
  description: >
    Housing code violation claims must cite both the specific MCL
    provision violated AND the local housing code provision if applicable.
  severity: HIGH

RULE-LANE-C-001:
  name: Cross-Lane Authority Consistency
  type: lane_specific
  lane: C
  description: >
    Authority cited in convergence filings must be consistent with
    authority cited in Lane A and Lane B filings. No contradictory
    authority positions across lanes.
  severity: CRITICAL
```
