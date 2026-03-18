# Affidavit Narrative Agent

## Name
`affidavit-narrative-agent`

## Description
Expert in building comprehensive, Michigan-compliant affidavits from LitigationOS databases. Constructs chronological narratives spanning custody disputes, housing violations, judicial misconduct, and civil rights violations. Analyzes all available evidence to identify viable legal claims with element analysis, strength scoring, and venue recommendations.

## Trigger Phrases
Use this agent when the user needs:
- "Build an affidavit from case data"
- "Generate a chronological narrative of the case"
- "Create a master affidavit for litigation"
- "Analyze legal claims against defendants"
- "Prepare JTC complaint affidavit"
- "Draft §1983 civil rights affidavit"
- "Build custody affidavit with timeline"
- "Create housing/habitability affidavit"
- "Evaluate claim strength and SOL deadlines"
- "Generate comprehensive case narrative from databases"

## Capabilities

### 1. Data Reading (Multi-Database Integration)
- Reads ALL LitigationOS databases:
  - `case_analysis.db` (analysis results)
  - `lane_A_custody.db` (custody/domestic)
  - `lane_B_housing.db` (housing/PPO)
  - `lane_C_convergence.db` (civil rights convergence)
  - `master_index.db` (3.3GB master index)
  - `consolidation_plan.db` (strategic consolidation)
- Extracts timeline events, factual findings, legal citations, evidence references
- Tracks entity mentions (people, places, dates)
- Cross-references evidence across all sources

### 2. Chronological Narrative Construction
- Collects and sorts ALL dated events chronologically
- Deduplicates and reconciles conflicting dates
- Groups events into 11 narrative chapters:
  1. Background (relationship, child, initial situation)
  2. Custody Dispute Origins
  3. PPO/Protection Order Events
  4. FOC Actions and Recommendations
  5. Judge McNeill's Rulings and Conduct
  6. Housing/Shady Oaks Issues
  7. Judge Hoopes' Rulings
  8. Watson Family Actions
  9. Civil Rights Violations
  10. Harm to Child and Father
  11. Current Status and Ongoing Issues
- Tracks evidence support for each event
- Identifies legal significance and claim support

### 3. Michigan-Compliant Affidavit Generation
Produces affidavits per MCR 2.119(B), MCR 2.112:
- **Master Affidavit**: Comprehensive 50+ page chronological account
- **Custody Affidavit**: Lane A specific (chapters 1, 2, 4, 5, 8, 10)
- **Housing Affidavit**: Lane B specific (chapters 6, 7)
- **JTC Complaint Affidavit**: Judicial misconduct (chapters 5, 7)
- **§1983 Affidavit**: Civil rights violations (chapters 4, 5, 7, 9)
- **Emergency Affidavit**: Short form for ex parte motions

### Affidavit Format Standards
- Proper Michigan heading (STATE OF MICHIGAN, COUNTY OF MUSKEGON)
- First-person narrative ("I, Andrew J. Pigors...")
- Numbered paragraphs (each = ONE fact)
- Exhibit references integrated
- Knowledge basis documented (personal knowledge vs. document review)
- Proper signature block with notary section

### 4. Comprehensive Claim Analysis
Evaluates all potential legal claims against:

#### Against Emily Watson
- Custody interference / manipulation
- False allegations
- PPO abuse of process
- Perjury
- Fraud upon the court
- Intentional infliction of emotional distress (IIED)
- Defamation
- Civil conspiracy

#### Against Watson Family Members
- Civil conspiracy
- Tortious interference with parental relationship
- IIED
- Aiding and abetting

#### Against Judge McNeill / Judge Hoopes
- Judicial misconduct (JTC)
- Due process violations (§1983)
- Bias/prejudice indicators
- Michigan Court Rules violations
- Ex parte communications

#### Against Friend of Court (FOC)
- Failure to properly investigate
- Bias in recommendations
- Due process violations
- §1983 (acting under color of state law)

#### Against Shady Oaks / Housing
- Breach of implied warranty of habitability (MCL 554.139)
- Negligence
- Health/safety code violations
- Constructive eviction

### Claim Analysis Features
For each claim, provides:
- **Claim Type & Defendant**: Specific identification
- **Legal Basis**: Statute/common law citation
- **Elements**: Complete element analysis with met/unmet status
- **Supporting Evidence**: Exhibit references
- **Strength Score**: 0-100 rating
- **Statute of Limitations**: With deadline calculation
- **Recommended Venue**: Circuit, COA, Federal, JTC
- **Risks**: Potential weaknesses and defenses
- **Filing Priority**: Strategic order (1=highest)

## CLI Commands

```bash
# Build full chronological narrative
python affidavit_agent.py narrative

# Generate affidavits
python affidavit_agent.py affidavit --master       # Master chronological affidavit
python affidavit_agent.py affidavit --custody      # Custody-specific
python affidavit_agent.py affidavit --housing      # Housing-specific
python affidavit_agent.py affidavit --jtc          # JTC complaint
python affidavit_agent.py affidavit --1983         # Civil rights (§1983)
python affidavit_agent.py affidavit --emergency    # Emergency motion
python affidavit_agent.py affidavit --case 2024-001507-DC  # With case number

# Analyze claims
python affidavit_agent.py claims                   # All claims
python affidavit_agent.py claims --against watson  # Watson family only
python affidavit_agent.py claims --against judge   # Judges only
python affidavit_agent.py claims --against foc     # FOC only
python affidavit_agent.py claims --against housing # Housing only

# Generate reports
python affidavit_agent.py report                   # Full status report
python affidavit_agent.py all                      # Everything (narrative + affidavits + claims)
```

## Output Structure

```
C:\Users\andre\LitigationOS\07_COURT_DOCUMENTS\
├── narratives\
│   ├── master_chronology.txt          # Complete chronological narrative
│   ├── affidavit_master.txt           # Master affidavit
│   └── affidavit_emergency.txt        # Emergency affidavit
├── lane_A_custody\
│   └── affidavits\
│       └── affidavit_custody.txt      # Custody-specific affidavit
├── lane_B_housing\
│   └── affidavits\
│       └── affidavit_housing.txt      # Housing-specific affidavit
├── lane_C_convergence\
│   └── affidavits\
│       ├── affidavit_jtc.txt          # JTC complaint affidavit
│       └── affidavit_1983.txt         # §1983 affidavit
└── analysis\
    ├── claims_report.txt              # Detailed claim analysis
    └── agent_report.txt               # Agent status report
```

## Key Players (Context)

### Parties
- **Andrew J. Pigors**: Plaintiff/Father, pro se
- **Emily Watson**: Defendant/Mother (custody case)
- **Watson Family**: Emily's family members (coordinated involvement)

### Judicial Officers
- **Judge McNeill**: 14th Circuit, custody case 2024-001507-DC
- **Judge Hoopes**: 14th Circuit, housing/PPO case 2023-5907-PP

### Entities
- **Friend of Court (FOC)**: Muskegon County FOC
- **Shady Oaks**: Housing complex (habitability issues)

### Cases
- **2024-001507-DC**: Custody/Domestic, Judge McNeill
- **2023-5907-PP**: Housing/PPO, Judge Hoopes
- **2025-002760-CZ**: Civil Rights/Convergence

## Technical Architecture

### Classes
1. **AffidavitDataReader**: Multi-database reader with event/evidence extraction
2. **ChronologicalNarrativeBuilder**: Timeline sorting, deduplication, chapter assignment
3. **AffidavitWriter**: Michigan-compliant affidavit generation
4. **ClaimAnalyzer**: Legal claim identification, element analysis, strength scoring

### Data Models
- `TimelineEvent`: Dated events with actors, evidence, legal significance
- `Evidence`: Exhibit tracking with relevance and claim support
- `LegalClaim`: Complete claim structure with elements, SOL, venue, risks
- `AffidavitParagraph`: Numbered paragraph with exhibits and knowledge basis

### Features
- **Enum-based claim types**: Type-safe claim categorization
- **Court venue routing**: Proper venue recommendations (Circuit, COA, Federal, JTC)
- **SOL tracking**: Statute of limitations with deadline calculation
- **Element analysis**: Per-claim element tracking with met/unmet status
- **Risk assessment**: Identifies weaknesses and defensive strategies
- **Strategic prioritization**: Filing order recommendations

## Use Cases

### 1. Trial Preparation
```bash
python affidavit_agent.py affidavit --custody --case 2024-001507-DC
```
Generates comprehensive custody affidavit with all timeline events, evidence references, and proper Michigan format for trial motions.

### 2. JTC Complaint
```bash
python affidavit_agent.py affidavit --jtc
python affidavit_agent.py claims --against judge
```
Builds judicial misconduct affidavit focused on Judge McNeill/Hoopes conduct, with claim analysis showing JTC-specific elements.

### 3. Civil Rights Filing
```bash
python affidavit_agent.py affidavit --1983
python affidavit_agent.py claims --against foc
```
Creates §1983 affidavit targeting FOC due process violations, with federal venue analysis and immunity considerations.

### 4. Strategic Planning
```bash
python affidavit_agent.py claims
```
Analyzes all potential claims with strength scores, SOL deadlines, venue recommendations, and filing priority order.

### 5. Discovery Support
```bash
python affidavit_agent.py narrative
```
Builds master chronology identifying evidence gaps and supporting targeted discovery requests.

## Integration Points

### LocalAI (Optional)
- Enhanced narrative generation with AI summarization
- Intelligent entity extraction
- Legal issue identification
- Falls back to rule-based processing if unavailable

### LitigationOS Databases
- Reads from 6 core databases
- Cross-references evidence across sources
- Maintains data provenance tracking

### Court Document Pipeline
- Outputs to lane-specific directories
- Ready for exhibit attachment
- Court-filing ready format

## Limitations & Risks

### Evidence Dependency
- Quality depends on database completeness
- Requires manual exhibit attachment
- Cannot verify factual accuracy

### Legal Disclaimer
⚠️ **NOT LEGAL ADVICE**
- This agent assists with document preparation
- Does not provide legal advice or strategy
- User must verify all facts and legal citations
- Consult attorney for legal guidance

### Claim Strength Caveats
- Strength scores are preliminary assessments
- Element analysis requires evidence population
- SOL deadlines must be independently verified
- Venue recommendations subject to jurisdictional research

### Judicial Immunity
- §1983 claims against judges face near-absolute immunity
- JTC complaints have low success rate
- Strategic value may exceed win probability

## Best Practices

### 1. Evidence Review First
Before generating affidavits:
1. Review database completeness
2. Ensure timeline accuracy
3. Verify exhibit references
4. Cross-check dates and names

### 2. Iterative Generation
Start with master narrative, then generate specific affidavits to ensure consistency across all documents.

### 3. Manual Enhancement
After generation:
- Add specific exhibit numbers
- Fill in knowledge basis details
- Enhance legal significance descriptions
- Add personal observations not in databases

### 4. Strategic Claim Selection
Use claim analysis to:
- Identify strongest claims first
- Monitor SOL deadlines
- Plan multi-stage filing strategy
- Assess risk/reward tradeoffs

### 5. Court-Specific Formatting
Before filing:
- Add case caption
- Insert proper case number
- Verify local court rules
- Add certificate of service
- Attach exhibits with proper tabs

## Future Enhancements

### Planned Features
- [ ] PDF generation with proper formatting
- [ ] Exhibit auto-attachment from file system
- [ ] Interactive claim builder with evidence mapping
- [ ] SOL deadline calendar integration
- [ ] Multi-affidavit comparison/consistency checker
- [ ] Court-specific format templates (Federal, COA, Circuit)

### Integration Opportunities
- Michigan eCourts filing integration
- Westlaw/Lexis citation verification
- OCR evidence extraction
- Deposition transcript integration

## Examples

### Example 1: Master Affidavit Generation
```bash
cd C:\Users\andre\LitigationOS\00_SYSTEM
python affidavit_agent.py affidavit --master --case 2025-002760-CZ
```

**Output**: 50+ page chronological affidavit in `07_COURT_DOCUMENTS\narratives\affidavit_master.txt`

### Example 2: Claim Analysis for Strategy Session
```bash
python affidavit_agent.py claims > my_claims.txt
```

**Result**: Comprehensive report showing:
- 15+ potential claims identified
- Grouped by defendant
- Strength scores (20-55 range)
- Priority filing order
- Venue recommendations

### Example 3: Emergency Motion Support
```bash
python affidavit_agent.py affidavit --emergency --case 2024-001507-DC
```

**Output**: Short-form affidavit focused on recent critical events, ready for ex parte filing.

## Agent Metadata

- **Version**: 1.0
- **Author**: LitigationOS
- **Created**: 2025
- **Language**: Python 3.8+
- **Dependencies**: sqlite3, dataclasses, pathlib
- **Optional**: LocalAI for enhanced generation
- **Location**: `C:\Users\andre\LitigationOS\00_SYSTEM\affidavit_agent.py`

## Support

For issues or enhancements:
1. Review database connectivity
2. Check output directory permissions
3. Verify Python 3.8+ installation
4. Ensure database files exist at expected paths

---

**Remember**: This agent is a *tool* for document preparation. Always verify facts, check legal citations, and consult counsel before filing any court documents.
