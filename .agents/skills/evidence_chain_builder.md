# Evidence Chain Builder v13.0.0

## LitigationOS Skill Module — Cross-Lane Document Chain Construction

---

## Purpose and Scope

The Evidence Chain Builder constructs linked evidence chains that connect documents across case lanes into coherent narratives. Each chain follows the pattern:

**Source Document → Supporting Document → Corroborating Document → Conclusion**

Evidence chains are the backbone of litigation strategy. They transform scattered documents into legally compelling arguments by establishing:
- Temporal relationships (what happened when)
- Causal relationships (what caused what)
- Corroborative strength (how many independent sources confirm a fact)
- Legal sufficiency (whether the chain meets the burden of proof)

---

## Input Requirements

| Field | Type | Description |
|-------|------|-------------|
| `lane` | `str` | Primary case lane (A–G) or `"ALL"` for cross-lane |
| `documents` | `List[DocumentRef]` | Documents available for chain building |
| `claim` | `str` | Legal claim or factual assertion the chain should support |
| `chain_type` | `str` | One of: `"chronological"`, `"causal"`, `"corroborative"`, `"impeachment"` |
| `min_strength` | `float` | Minimum chain strength score (default: `0.60`) |
| `max_chain_length` | `int` | Maximum links in a chain (default: `8`) |

### DocumentRef Schema
```json
{
  "doc_id": "DOC-2024-1847",
  "path": "Lane_A\\orders\\2024-03-15_custody_order.pdf",
  "lane": "A",
  "classification": "REAL_COURT_FILE",
  "doc_type": "ORDER",
  "date": "2024-03-15",
  "parties": ["Parent A", "Parent B"],
  "extracted_text_summary": "...",
  "key_facts": ["custody modified", "parenting time reduced"]
}
```

---

## Processing Methodology

### Step 1: Fact Extraction

Extract discrete facts from each document:

```
Fact Schema:
{
  "fact_id": "F-001",
  "source_doc": "DOC-2024-1847",
  "statement": "Court reduced Father's parenting time from 50/50 to every-other-weekend",
  "date": "2024-03-15",
  "actors": ["Judge Smith", "Father", "Mother"],
  "fact_type": "court_action",       # court_action | party_statement | third_party_observation | physical_evidence
  "reliability": 0.95                # Based on source classification
}
```

**Fact Types & Reliability Baseline:**
| Source Type | Baseline Reliability |
|-------------|---------------------|
| Court order (filed, stamped) | 0.95 |
| Court transcript | 0.90 |
| Attorney filing (verified) | 0.85 |
| Party declaration/affidavit | 0.70 |
| Third-party correspondence | 0.65 |
| Informal communication (text, email) | 0.50 |
| AI-generated draft | 0.10 (not admissible) |

### Step 2: Relationship Discovery

Identify relationships between facts:

**Temporal Relationships:**
```
- PRECEDES:    Fact A occurred before Fact B
- FOLLOWS:     Fact A occurred after Fact B
- CONCURRENT:  Fact A and Fact B occurred within the same time window
- RESPONDS_TO: Fact B is a direct response to Fact A
```

**Causal Relationships:**
```
- CAUSED_BY:       Fact B was caused by Fact A
- RESULTED_IN:     Fact A resulted in Fact B
- ENABLED:         Fact A enabled Fact B to occur
- CONTRADICTS:     Fact A contradicts Fact B
```

**Corroborative Relationships:**
```
- CONFIRMS:        Fact B independently confirms Fact A
- PARTIALLY_CONFIRMS: Fact B confirms part of Fact A
- CONSISTENT_WITH: Fact B is consistent with (but does not prove) Fact A
```

### Step 3: Chain Assembly

Build chains using the four-link pattern:

```
CHAIN PATTERN:
  [1] SOURCE DOCUMENT      — The primary document establishing the core fact
  [2] SUPPORTING DOCUMENT  — A document that adds context or detail to the core fact
  [3] CORROBORATING DOCUMENT — An independent document that confirms the core fact
  [4] CONCLUSION           — The legal or factual conclusion the chain supports

Chain Strength = (
    source_reliability × 0.30 +
    support_relevance × 0.20 +
    corroboration_independence × 0.30 +
    conclusion_legal_sufficiency × 0.20
)
```

**Chain Assembly Algorithm:**
1. For each claim, identify candidate source documents (highest reliability, most directly relevant).
2. For each source, find supporting documents (same lane or cross-lane) that add context.
3. For each source+support pair, find corroborating documents from **independent** sources.
4. Score the chain and formulate the conclusion.
5. Rank all candidate chains by strength; return chains above `min_strength`.

### Step 4: Cross-Lane Linking

When documents from different lanes contribute to the same chain:

```
Cross-Lane Link:
{
  "link_type": "CROSS_LANE",
  "from_lane": "A",
  "to_lane": "E",
  "from_doc": "DOC-2024-1847",
  "to_doc": "DOC-2024-2201",
  "relationship": "CAUSED_BY",
  "explanation": "Custody order (Lane A) was issued after ex parte contact (Lane E)"
}
```

### Step 5: Chain Validation

Each chain is validated for:
1. **Temporal consistency** — No backward time jumps (unless documenting backdating).
2. **Source independence** — Corroborating document must be from a different source than the source document.
3. **Admissibility** — All documents in the chain must be classified as `REAL_COURT_FILE` or verified attorney work product.
4. **Legal sufficiency** — Chain conclusion must reference applicable law.
5. **No circular reasoning** — Document A cannot support Document B if B is already supporting A.

---

## Output Format

```json
{
  "builder": "evidence_chain_builder_v13",
  "claim": "Court denied Father due process by modifying custody without proper hearing",
  "chains": [
    {
      "chain_id": "EC-001",
      "chain_type": "causal",
      "strength": 0.88,
      "links": [
        {
          "position": 1,
          "role": "SOURCE",
          "doc_id": "DOC-2024-1847",
          "lane": "A",
          "fact": "Court modified custody from 50/50 to every-other-weekend",
          "date": "2024-03-15",
          "reliability": 0.95
        },
        {
          "position": 2,
          "role": "SUPPORTING",
          "doc_id": "DOC-2024-1790",
          "lane": "D",
          "fact": "No motion for change of custody was filed prior to order",
          "date": "2024-03-10",
          "reliability": 0.90
        },
        {
          "position": 3,
          "role": "CORROBORATING",
          "doc_id": "DOC-2024-1820",
          "lane": "E",
          "fact": "Docket shows no hearing was scheduled before the order date",
          "date": "2024-03-14",
          "reliability": 0.95
        },
        {
          "position": 4,
          "role": "CONCLUSION",
          "statement": "Custody was modified without a pending motion or scheduled hearing, violating due process under the 14th Amendment and MCR 3.210(C)",
          "legal_basis": ["U.S. Const. Amend. XIV", "MCR 3.210(C)", "MCL 722.27(1)(c)"],
          "strength": 0.88
        }
      ],
      "cross_lane_links": [
        {
          "from_lane": "A",
          "to_lane": "E",
          "relationship": "CAUSED_BY"
        }
      ]
    }
  ],
  "weak_chains": [],
  "gaps": [
    {
      "description": "No transcript of March 15 proceeding found — may strengthen or weaken chain",
      "suggested_action": "Subpoena court reporter transcript for 2024-03-15"
    }
  ]
}
```

---

## Integration Points

| Skill | Integration |
|-------|-------------|
| `case_lane_router` | Documents must be routed before chain building |
| `pdf_court_file_classifier` | Only `REAL_COURT_FILE` documents enter chains |
| `convergence_dedup_engine` | Canonical documents only; no duplicates in chains |
| `timeline_anomaly_detector` | Anomalies feed into chain gap analysis |
| `judicial_pattern_analyzer` | Judicial misconduct evidence feeds Lane E chains |
| `witness_credibility_scorer` | Witness reliability scores inform fact reliability |
| `harm_quantifier` | Harm metrics provide data for conclusion strength |
| `evidence_chains` (engine) | Engine module executes chain assembly logic |
| `evidence_linker_batch` (engine) | Batch linker processes multiple chains in parallel |

---

## Michigan-Specific Legal References

- **MCL 722.23** — Best interest factors (chain conclusions for Lane A)
- **MCL 722.27(1)(c)** — Requirements for custody modification (proper cause/change of circumstances)
- **MCR 3.210(C)** — Hearing requirements for custody proceedings
- **MRE 801–807** — Hearsay rules affecting document admissibility in chains
- **MRE 901** — Authentication requirements for evidence
- **MRE 403** — Relevance balancing (chain must not be unfairly prejudicial)
- **MCR 2.119(A)(2)** — Motion requirements that chains may reference

---

## Chain Types

### Chronological Chain
Links documents in temporal sequence to show a pattern over time.
Use for: Establishing pattern of behavior, escalation, delay tactics.

### Causal Chain
Links documents showing cause-and-effect relationships.
Use for: Proving harm, demonstrating judicial error, establishing liability.

### Corroborative Chain
Links independent sources confirming the same fact.
Use for: Meeting burden of proof, overcoming credibility challenges.

### Impeachment Chain
Links documents showing contradictions in a party's or witness's statements.
Use for: Challenging credibility, exposing false statements, supporting sanctions motions.
