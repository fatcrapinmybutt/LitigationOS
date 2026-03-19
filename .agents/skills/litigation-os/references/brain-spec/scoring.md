# Scoring Formula & 50-Brain LEXOS Map

## Scoring Formula (from brain_builder.py)

```python
score = (citations * 3.0 + keywords * 1.5 + dollars + dates) * length_factor
```

| Component | Weight | How Counted |
|-----------|--------|-------------|
| `citations` | 3.0 | Count of UNIQUE MCL/MCR/MRE/case cites |
| `keywords` | 1.5 | Count of UNIQUE violation/person keyword matches |
| `dollars` | 1.0 | Count of dollar amount mentions |
| `dates` | 1.0 | Count of date mentions (ISO, US format) |
| `length_factor` | multiplier | `min(1.0, char_count / 500)` |

**Final evidence score** = base_score × posture_weight (SWORN=5x, RECORD=4x, etc.)

## Classification Regex Patterns

```python
MCL_PATTERN  = r'MCL\s+\d+[\.\d]*'
MCR_PATTERN  = r'MCR\s+\d+[\.\d]*'
MRE_PATTERN  = r'MRE\s+\d+[\.\d]*'
CASE_PATTERN = r'\b\d+\s+(Mich|NW2d|US)\b'

PERSON_NAMES = [
    'Pigors', 'Watson', 'McNeill', 'Rusco', 'HealthWest',
    'Emily', 'Albert', 'Lori', 'Cody', 'Hoopes'
]

VIOLATION_KEYWORDS = [
    'contempt', 'ex parte', 'bias', 'fraud', 'perjury',
    'alienation', 'due process', 'discrimination', 'retaliation'
]

MEEK_LANE_SIGNALS = {
    'MEEK1': ['habitability', 'landlord', 'tenant', 'lease', 'MCL 554'],
    'MEEK2': ['custody', 'parenting', 'FOC', 'child', 'MCL 722', 'MCR 3.206', 'MCR 3.207', 'MCR 3.210'],
    'MEEK3': ['PPO', 'contempt', 'MCL 600.2950', 'MCR 3.606', 'MCR 3.707', 'MCR 3.708'],
    'MEEK4': ['bias', 'JTC', 'disqualification', 'MCR 2.003', 'Canon', 'superintending'],
    'MEEK5': ['appeal', 'COA', 'MSC', 'MCR 7.205', 'MCR 7.305', 'stay', 'interlocutory']
}
```

## 50 LEXOS Brain Nuclei

| Brain # | Domain | Key Signals |
|---------|--------|-------------|
| 1 | MCL (Compiled Laws) | Statute numbers, MCL pattern |
| 2 | MCR (Court Rules) | Rule numbers, MCR pattern |
| 3 | MRE (Evidence Rules) | Evidence rules, MRE pattern |
| 4 | Case Law | Michigan case citations |
| 5 | Constitution | Constitutional provisions |
| 6 | Benchbooks | MJI references |
| 7 | SCAO Forms | Form numbers, SCAO |
| 8 | Local Rules | Administrative orders, local |
| 9 | Andrew Pigors | Plaintiff references |
| 10 | Emily Watson | Defendant references |
| 11 | Albert Watson | Father of defendant |
| 12 | Lori Watson | Mother of defendant |
| 13 | Cody Watson | Brother of defendant |
| 14 | Jenny McNeill | Judge references |
| 15 | David/Pamela Rusco | Attorney + FOC |
| 16 | FOC Office | Friend of Court |
| 17 | HealthWest | Mental health evaluator |
| 18 | Alienation | Parental alienation patterns |
| 19 | Custody | Custody law + factors |
| 20 | PPO | Protection orders |
| 21 | Judicial Misconduct | Bias, Canon violations |
| 22 | Fraud/Perjury | False statements |
| 23 | Contempt | Civil + criminal contempt |
| 24 | Landlord-Tenant | Housing law (Shady Oaks) |
| 25 | Due Process | Constitutional rights |
| 26 | Hearings | Hearing transcripts |
| 27 | Orders | Court orders |
| 28 | Motions | Filed motions |
| 29 | Discovery | Discovery requests/responses |
| 30 | Evidence/Exhibits | Evidence items |
| 31 | Best Interest | MCL 722.23 twelve factors |
| 32 | Financial | Income, expenses, support |
| 33 | Timelines | Chronological events |
| 34 | Credibility | Witness credibility analysis |
| 35 | Patterns | Recurring conduct patterns |
| 36 | Contradictions | Statement vs record conflicts |
| 37 | Damages | Harm quantification |
| 38 | Service | Proof of service |
| 39 | Filing Status | Filing readiness |
| 40 | Compliance | MCR compliance audit |
| 41 | Emergency Relief | Emergency motions |
| 42 | Appellate Strategy | Appeal paths |
| 43 | Standards of Review | De novo, abuse, clear error |
| 44 | Remedies | Available relief types |
| 45 | Federal Claims | §1983, constitutional |
| 46 | Tort Claims | Civil tort actions |
| 47 | Criminal Referrals | Perjury, fraud referrals |
| 48 | Administrative | JTC, grievance, LARA |
| 49 | Shady Oaks | Housing-specific evidence |
| 50 | Case Numbers | Case number references |

## Brain Constraints

- **500KB max** per brain nucleus (per lexos_config.json)
- **SHA1 dedup** within each brain (no duplicate entries)
- **TF-IDF index** rebuilt after each feed cycle
- **Trim rule**: When brain exceeds 500KB, remove lowest-scored entries first
