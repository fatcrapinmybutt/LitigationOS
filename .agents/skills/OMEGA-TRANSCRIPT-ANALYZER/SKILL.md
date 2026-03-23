---
name: OMEGA-TRANSCRIPT-ANALYZER
description: >-
  Hearing transcript analysis engine that extracts judicial conduct patterns,
  testimony timelines, objection tracking, ruling bias detection, and witness
  credibility signals from court transcripts. Critical for McNeill bias
  documentation, COA appeal grounds, and JTC complaint evidence.
category: discipline
version: "1.0.0"
triggers:
  - transcript
  - hearing
  - testimony
  - objection
  - ruling
  - bias detection
  - judicial conduct
  - witness
  - cross examination
  - court record
lanes:
  - "A: Watson/Custody (2024-001507-DC)"
  - "D: PPO (2023-5907-PP)"
  - "E: Judicial Misconduct/JTC"
  - "F: Appellate (COA 366810)"
court: "14th Judicial Circuit, Michigan COA"
case: Pigors v Watson
metadata:
  tier: 3 (Analysis)
  layer: Layer 3 — Analysis
  fused_skills: 8
  author: andrew-pigors + copilot-omega
  jurisdiction: Michigan
---

# 🎙️ OMEGA-TRANSCRIPT-ANALYZER 🎙️

> **LAYER 3 — Analysis: Hearing Transcript Intelligence Engine**
> **Pipeline:** Raw Transcript → Parse → Extract → Annotate → Score → Report
> **Case:** Pigors v Watson · Focus: McNeill bias patterns, COA record, JTC evidence
> **Iron Law:** Every finding links to page:line in transcript. No fabrication.

```
╔══════════════════════════════════════════════════════════════════════════╗
║                   OMEGA-TRANSCRIPT-ANALYZER v1.0                        ║
║               8 Skills → 6 Modules → 1 Analysis Engine                  ║
║                                                                         ║
║  T1  Transcript Parser ──────┐                                          ║
║  T2  Speaker Identification ─┤→ T4 Ruling Analysis ──→ T6 Bias Report  ║
║  T3  Testimony Extraction ───┘       ↓                      ↓           ║
║       ↓                     T5 Objection Tracker ──→ SCORED TRANSCRIPT  ║
║  Timeline Events                     ↑                                   ║
║       ↓                     Pattern Detection ─────→ JTC Evidence Pack  ║
║  Credibility Signals                                                     ║
╚══════════════════════════════════════════════════════════════════════════╝
```

---

## Forged from 8 Individual Skills

| # | Source Skill | Absorbed Capability |
|---|-------------|---------------------|
| 1 | `litigation-timeline-forensics` | Chronological event extraction from transcripts |
| 2 | `litigation-impeachment-engine` | Contradiction detection across testimony |
| 3 | `litigation-judicial-analyst` | Judicial behavior pattern analysis |
| 4 | `litigation-voir-dire-specialist` | Witness credibility assessment |
| 5 | `litigation-witness-preparation` | Cross-exam question generation |
| 6 | `litigation-deposition-strategist` | Deposition transcript analysis |
| 7 | `criminal-evidence-scanner` | Evidence extraction from recorded proceedings |
| 8 | `litigation-record-builder` | Appellate record construction from transcripts |

---

## ═══════════════════════════════════════════════════════════════
## MODULE T1: TRANSCRIPT PARSER
## ═══════════════════════════════════════════════════════════════

### Transcript Format Detection

Michigan court transcripts follow these formats:
```
Format A (Standard):
  1    THE COURT: Please be seated.
  2    MR. PIGORS: Your Honor, I'd like to—
  3    THE COURT: I'm going to stop you there.

Format B (Certified):
  Q.  (By Mr. Pigors) Can you explain—
  A.  I don't recall.
  THE COURT: Objection sustained.

Format C (Audio Transcription):
  [14:32:15] JUDGE McNEILL: The motion is denied.
  [14:32:22] ANDREW PIGORS: But Your Honor—
  [14:32:24] JUDGE McNEILL: I've made my ruling.
```

### T1 Parser Output

```python
@dataclass
class TranscriptLine:
    page: int
    line: int
    timestamp: str | None
    speaker: str              # THE COURT, MR. PIGORS, MS. WATSON, etc.
    speaker_role: str         # JUDGE, PLAINTIFF, DEFENDANT, ATTORNEY, WITNESS, CLERK
    content: str              # The actual words spoken
    annotations: list[str]    # [OBJECTION], [RULING], [SIDEBAR], etc.
    
@dataclass
class ParsedTranscript:
    case_number: str
    hearing_date: str
    hearing_type: str         # Motion hearing, Status conference, Trial, etc.
    judge: str
    parties_present: list[str]
    total_pages: int
    lines: list[TranscriptLine]
```

---

## ═══════════════════════════════════════════════════════════════
## MODULE T2: SPEAKER IDENTIFICATION
## ═══════════════════════════════════════════════════════════════

### Known Speakers (Pigors v Watson)

| Speaker Pattern | Normalized | Role |
|----------------|-----------|------|
| THE COURT / JUDGE McNEILL | Hon. Jenny L. McNeill | JUDGE |
| MR. PIGORS / ANDREW PIGORS | Andrew James Pigors | PLAINTIFF |
| MS. WATSON / EMILY WATSON | Emily A. Watson | DEFENDANT |
| MS. BARNES / JENNIFER BARNES | Jennifer Barnes (P55406) | DEF_ATTORNEY |
| THE CLERK / COURT CLERK | Court Clerk | CLERK |
| MS. RUSCO / PAMELA RUSCO | Pamela Rusco | FOC |

### Speaking Time Analysis

```python
def calculate_speaking_time(transcript: ParsedTranscript) -> dict:
    """Track how much time each party gets — asymmetry = bias signal."""
    word_counts = defaultdict(int)
    interruptions = defaultdict(int)
    
    for line in transcript.lines:
        word_counts[line.speaker_role] += len(line.content.split())
    
    # Flag: Judge gives defendant 3x more speaking time than plaintiff
    plaintiff_words = word_counts.get('PLAINTIFF', 0)
    defendant_words = word_counts.get('DEFENDANT', 0) + word_counts.get('DEF_ATTORNEY', 0)
    
    if defendant_words > plaintiff_words * 2:
        return BiasSignal(
            type="SPEAKING_TIME_ASYMMETRY",
            severity="HIGH",
            detail=f"Defendant side: {defendant_words} words vs Plaintiff: {plaintiff_words} words",
            ratio=defendant_words / max(plaintiff_words, 1)
        )
```

---

## ═══════════════════════════════════════════════════════════════
## MODULE T3: TESTIMONY EXTRACTION
## ═══════════════════════════════════════════════════════════════

### Extract Categories

| Category | What to Extract | Use Case |
|----------|----------------|----------|
| Admissions | Party admits unfavorable facts | Impeachment, motion support |
| Denials | Party denies known facts | Contradiction detection |
| Factual Claims | Statements about events, dates, actions | Timeline construction |
| Expert Opinions | Expert witness conclusions | Daubert challenges |
| Hearsay | Out-of-court statements offered for truth | MRE 801-807 analysis |
| Character Evidence | Statements about character/reputation | MRE 404 analysis |

### Testimony Database Schema

```sql
CREATE TABLE transcript_testimony (
    id INTEGER PRIMARY KEY,
    transcript_id TEXT,
    page INTEGER,
    line_start INTEGER,
    line_end INTEGER,
    speaker TEXT,
    speaker_role TEXT,
    category TEXT,     -- admission, denial, factual_claim, expert, hearsay, character
    content TEXT,
    contradicts TEXT,  -- NULL or reference to contradicting testimony
    exhibits TEXT,     -- referenced exhibits
    lane TEXT,         -- A, B, D, E, F
    impeachment_value REAL,  -- 0.0 to 1.0
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## ═══════════════════════════════════════════════════════════════
## MODULE T4: RULING ANALYSIS
## ═══════════════════════════════════════════════════════════════

### Ruling Classification

```python
@dataclass
class Ruling:
    page: int
    line: int
    type: str         # GRANTED, DENIED, SUSTAINED, OVERRULED, RESERVED, TAKEN_UNDER_ADVISEMENT
    subject: str      # What was ruled on
    beneficiary: str  # PLAINTIFF or DEFENDANT
    reasoning: str    # Judge's stated reason (if any)
    no_reasoning: bool  # True if judge ruled without explanation
    
def analyze_ruling_pattern(rulings: list[Ruling]) -> BiasReport:
    """Detect systematic bias in rulings."""
    plaintiff_wins = sum(1 for r in rulings if r.beneficiary == 'PLAINTIFF')
    defendant_wins = sum(1 for r in rulings if r.beneficiary == 'DEFENDANT')
    
    no_reason_plaintiff = sum(1 for r in rulings 
        if r.beneficiary == 'DEFENDANT' and r.no_reasoning)
    
    return BiasReport(
        total_rulings=len(rulings),
        plaintiff_favorable=plaintiff_wins,
        defendant_favorable=defendant_wins,
        ratio=defendant_wins / max(plaintiff_wins, 1),
        rulings_without_reasoning=no_reason_plaintiff,
        bias_indicators=detect_bias_patterns(rulings)
    )
```

### Bias Indicators (McNeill-Specific)

| Indicator | Detection | Severity |
|-----------|-----------|----------|
| Asymmetric denial rate | >70% of plaintiff motions denied | HIGH |
| No reasoning given | Judge rules without stating basis | HIGH |
| Cutting off plaintiff | Interrupts before argument complete | MEDIUM |
| Ex parte indicators | References to info not in record | CRITICAL |
| Hostile tone markers | "I'm going to stop you", "That's enough" | MEDIUM |
| Time pressure | Rushing plaintiff's presentation | MEDIUM |
| Deference to defendant | "Ms. Barnes, would you like to respond?" vs cutting off Pigors | HIGH |

---

## ═══════════════════════════════════════════════════════════════
## MODULE T5: OBJECTION TRACKER
## ═══════════════════════════════════════════════════════════════

### Objection Analysis

```python
@dataclass
class Objection:
    page: int
    line: int
    objector: str         # Who objected
    objection_type: str   # Relevance, hearsay, foundation, etc.
    ruling: str           # SUSTAINED, OVERRULED
    prejudicial: bool     # Was it prejudicial to plaintiff?

def track_objections(transcript: ParsedTranscript) -> ObjectionReport:
    objections = extract_objections(transcript)
    
    # Sustained when defendant objects vs when plaintiff objects
    def_obj_sustained = sum(1 for o in objections 
        if o.objector == 'DEFENDANT' and o.ruling == 'SUSTAINED')
    plt_obj_sustained = sum(1 for o in objections 
        if o.objector == 'PLAINTIFF' and o.ruling == 'SUSTAINED')
    
    # Asymmetry = bias signal
    return ObjectionReport(
        total=len(objections),
        defendant_sustained=def_obj_sustained,
        plaintiff_sustained=plt_obj_sustained,
        asymmetry_ratio=def_obj_sustained / max(plt_obj_sustained, 1),
        bias_detected=def_obj_sustained > plt_obj_sustained * 2
    )
```

---

## ═══════════════════════════════════════════════════════════════
## MODULE T6: BIAS REPORT GENERATOR
## ═══════════════════════════════════════════════════════════════

### Composite Bias Score

```python
def generate_bias_report(transcript: ParsedTranscript) -> BiasReport:
    """
    Generate comprehensive judicial bias report from transcript.
    Used for: MCR 2.003 disqualification, JTC complaint, COA appeal.
    
    NOTE: This produces DOCUMENTED INCIDENT COUNTS, not synthetic percentages.
    """
    speaking = calculate_speaking_time(transcript)
    rulings = analyze_ruling_pattern(extract_rulings(transcript))
    objections = track_objections(transcript)
    interruptions = count_interruptions(transcript)
    
    indicators = []
    
    if rulings.ratio > 2.0:
        indicators.append(f"Ruling asymmetry: {rulings.defendant_favorable} defendant-favorable "
                         f"vs {rulings.plaintiff_favorable} plaintiff-favorable")
    
    if objections.bias_detected:
        indicators.append(f"Objection asymmetry: {objections.defendant_sustained} defendant "
                         f"objections sustained vs {objections.plaintiff_sustained} plaintiff")
    
    if speaking.ratio > 2.0:
        indicators.append(f"Speaking time asymmetry: defendant side {speaking.defendant_words} "
                         f"words vs plaintiff {speaking.plaintiff_words} words")
    
    if interruptions['PLAINTIFF'] > interruptions['DEFENDANT'] * 2:
        indicators.append(f"Interruption asymmetry: plaintiff interrupted "
                         f"{interruptions['PLAINTIFF']} times vs defendant {interruptions['DEFENDANT']}")
    
    return BiasReport(
        transcript_id=transcript.case_number,
        hearing_date=transcript.hearing_date,
        judge=transcript.judge,
        total_indicators=len(indicators),
        indicators=indicators,
        # NO synthetic score — only documented incident counts
        ruling_count=rulings.total_rulings,
        plaintiff_favorable_count=rulings.plaintiff_favorable,
        defendant_favorable_count=rulings.defendant_favorable,
        use_for_mcr_2003=len(indicators) >= 3,
        use_for_jtc=any("CRITICAL" in i for i in indicators),
        use_for_coa=len(indicators) >= 2
    )
```

### Output Destinations

| Output | Use Case | Lane |
|--------|----------|------|
| Bias Report → MCR 2.003 Motion | Disqualification motion support | A, E |
| Bias Report → JTC Complaint | Judicial misconduct evidence | E |
| Bias Report → COA Brief | Appeal grounds (judicial error) | F |
| Testimony Extracts → Evidence DB | evidence_quotes table entries | ALL |
| Timeline Events → Chronology | case_timeline table entries | ALL |
| Contradictions → Impeachment | Cross-exam ammunition | A, D |

---

## ═══════════════════════════════════════════════════════════════
## GLOBAL RULES
## ═══════════════════════════════════════════════════════════════

### ANTI-HALLUCINATION FOR TRANSCRIPTS

```
□ Every finding MUST cite page:line from the actual transcript
□ NEVER fabricate quotes — if unsure, mark [VERIFY AGAINST TRANSCRIPT]
□ NEVER generate synthetic bias percentages — use incident COUNTS only
□ NEVER assume what was said off-record
□ Distinguish: SAID (direct quote) vs PARAPHRASED vs INFERRED
□ Speaker attribution must be verified — don't guess who said what
```

### TRANSCRIPT SOURCES (known locations)

```
Primary: I:\02_EVIDENCE\Primary\05_EVIDENCE\
Secondary: J:\COURT_TRANSCRIPTS\ (if exists)
DB: SELECT * FROM documents WHERE doc_type = 'transcript'
ChatGPT exports may contain transcript discussions — NOT the transcripts themselves
```

---

*OMEGA-TRANSCRIPT-ANALYZER v1.0 — 8 skills forged into one analysis engine.*
*Every judicial bias finding links to page:line. No fabrication. No synthetic scores.*
