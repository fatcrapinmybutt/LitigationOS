#!/usr/bin/env python3
"""
AFFIDAVIT AGENT
Builds comprehensive, chronological affidavits from LitigationOS databases.

Purpose:
    Constructs Michigan-compliant affidavits by reading ALL case data from:
    - Case analysis DBs
    - Lane databases (custody, housing, convergence)
    - Master index (3.3GB)
    - Consolidation plan
    
    Produces chronological narratives supporting:
    - Custody motions
    - Judicial misconduct complaints (JTC)
    - Civil rights claims (§1983)
    - Housing/habitability claims
    - Claims against Watson family

Author: LitigationOS
Date: 2025
"""

import sys
import os
import sqlite3
import json
import re
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple, Set
from dataclasses import dataclass, field, asdict
from collections import defaultdict
from enum import Enum

# Add pipeline to path for LocalAI
sys.path.insert(0, r'C:\Users\andre\LitigationOS\00_SYSTEM\pipeline')
try:
    from local_ai_engine import LocalAI
except ImportError:
    LocalAI = None
    print("WARNING: LocalAI not available, using fallback text generation")

# Import AuthorityLookup for real Michigan legal authority data
try:
    from authority_ingestion_engine import AuthorityLookup
    _adb = os.path.join(r'C:\Users\andre\LitigationOS\03_LEGAL_AUTHORITIES', 'authority_master.db')
    authority_lookup = AuthorityLookup(_adb) if os.path.exists(_adb) else None
except ImportError:
    authority_lookup = None


# ============================================================================
# DATA MODELS
# ============================================================================

class ClaimType(Enum):
    """Types of legal claims identified"""
    # Against Emily Watson
    CUSTODY_INTERFERENCE = "custody_interference"
    FALSE_ALLEGATIONS = "false_allegations"
    PPO_ABUSE = "ppo_abuse_of_process"
    PERJURY = "perjury"
    FRAUD_COURT = "fraud_upon_court"
    IIED = "intentional_infliction_emotional_distress"
    DEFAMATION = "defamation"
    CIVIL_CONSPIRACY = "civil_conspiracy"
    
    # Against Judges
    JUDICIAL_MISCONDUCT = "judicial_misconduct"
    DUE_PROCESS_VIOLATION = "due_process_violation"
    BIAS_PREJUDICE = "bias_prejudice"
    MCR_VIOLATION = "michigan_court_rules_violation"
    EX_PARTE_COMMUNICATION = "ex_parte_communication"
    
    # Against FOC
    FOC_FAILURE_INVESTIGATE = "foc_failure_to_investigate"
    FOC_BIAS = "foc_bias"
    FOC_DUE_PROCESS = "foc_due_process_violation"
    SECTION_1983 = "42_usc_1983"
    
    # Against Housing
    BREACH_HABITABILITY = "breach_habitability"
    NEGLIGENCE = "negligence"
    CODE_VIOLATIONS = "health_safety_code_violations"
    CONSTRUCTIVE_EVICTION = "constructive_eviction"
    
    # Family Members
    TORTIOUS_INTERFERENCE = "tortious_interference"
    AIDING_ABETTING = "aiding_and_abetting"


class CourtVenue(Enum):
    """Where claims should be filed"""
    MUSKEGON_CIRCUIT = "14th_circuit_muskegon"
    MICHIGAN_COA = "michigan_court_of_appeals"
    FEDERAL_DISTRICT = "western_district_michigan"
    JTC = "judicial_tenure_commission"
    SUPREME_COURT = "michigan_supreme_court"


@dataclass
class TimelineEvent:
    """A dated event in the case"""
    date: str  # ISO format or "circa YYYY-MM"
    event_type: str  # custody_hearing, ppo_filing, etc.
    description: str
    actors: List[str]  # People involved
    evidence_refs: List[str]  # Exhibit numbers
    legal_significance: str
    claims_supported: List[str]  # ClaimType values
    source_db: str
    exact_date: bool = True
    chapter: Optional[str] = None


@dataclass
class Evidence:
    """Evidence/exhibit reference"""
    exhibit_id: str  # A-001, B-042, etc.
    description: str
    source_file: Optional[str] = None
    date: Optional[str] = None
    author: Optional[str] = None
    category: str = "document"  # document, photo, recording, text, email
    relevance: str = ""
    claims_supported: List[str] = field(default_factory=list)


@dataclass
class ClaimElement:
    """Element of a legal claim"""
    element: str
    met: bool
    evidence: List[str]  # Exhibit IDs
    reasoning: str


@dataclass
class LegalClaim:
    """A potential legal claim"""
    claim_type: ClaimType
    defendant: str
    legal_basis: str  # Statute/common law
    elements: List[ClaimElement]
    supporting_evidence: List[str]  # Exhibit IDs
    strength_score: int  # 0-100
    statute_of_limitations: str
    sol_deadline: Optional[str]
    recommended_venue: CourtVenue
    risks: List[str]
    filing_priority: int  # 1=highest
    notes: str = ""


@dataclass
class AffidavitParagraph:
    """A single numbered paragraph in affidavit"""
    number: int
    text: str
    date: Optional[str] = None
    exhibits: List[str] = field(default_factory=list)
    knowledge_basis: str = "personal_knowledge"  # personal_knowledge, document_review, informed_belief
    claims_supported: List[str] = field(default_factory=list)


# ============================================================================
# PART 1: DATA READER
# ============================================================================

class AffidavitDataReader:
    """
    Reads ALL LitigationOS databases and extracts:
    - Timeline entries
    - Factual findings
    - Legal citations
    - Evidence references
    - Entity mentions
    """
    
    def __init__(self, base_path: str = r"C:\Users\andre\LitigationOS"):
        self.base_path = Path(base_path)
        self.databases = {
            'case_analysis': self.base_path / "00_SYSTEM" / "manifests" / "case_analysis.db",
            'lane_a': self.base_path / "06_CASE_DATABASES" / "lane_A_custody.db",
            'lane_b': self.base_path / "06_CASE_DATABASES" / "lane_B_housing.db",
            'lane_c': self.base_path / "06_CASE_DATABASES" / "lane_C_convergence.db",
            'master_index': self.base_path / "00_SYSTEM" / "pipeline" / "agents" / "master_index.db",
            'consolidation': self.base_path / "00_SYSTEM" / "manifests" / "consolidation_plan.db",
        }
        
        self.events: List[TimelineEvent] = []
        self.evidence: List[Evidence] = []
        self.entities = defaultdict(list)  # name -> mentions
        self.legal_issues = defaultdict(list)
        
    def read_all_databases(self) -> Dict[str, Any]:
        """Read all databases and compile results"""
        results = {
            'events': [],
            'evidence': [],
            'entities': {},
            'legal_issues': {},
            'raw_data': {}
        }
        
        for db_name, db_path in self.databases.items():
            if not db_path.exists():
                print(f"[!] Database not found: {db_path}")
                continue
            
            print(f"[*] Reading {db_name}...")
            try:
                data = self._read_database(db_path, db_name)
                results['raw_data'][db_name] = data
                
                # Extract structured data
                events = self._extract_events(data, db_name)
                evidence = self._extract_evidence(data, db_name)
                entities = self._extract_entities(data, db_name)
                
                results['events'].extend(events)
                results['evidence'].extend(evidence)
                
                for entity, mentions in entities.items():
                    if entity not in results['entities']:
                        results['entities'][entity] = []
                    results['entities'][entity].extend(mentions)
                    
            except Exception as e:
                print(f"[X] Error reading {db_name}: {e}")
                continue
        
        self.events = results['events']
        self.evidence = results['evidence']
        self.entities = results['entities']
        
        print(f"\n[+] Data read complete:")
        print(f"   - {len(results['events'])} events")
        print(f"   - {len(results['evidence'])} evidence items")
        print(f"   - {len(results['entities'])} entities")
        
        return results
    
    def _read_database(self, db_path: Path, db_name: str) -> Dict[str, Any]:
        """Read a single database"""
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        
        data = {'tables': {}}
        
        # Get all tables
        tables = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
        
        for table_row in tables:
            table_name = table_row['name']
            try:
                rows = conn.execute(f"SELECT * FROM {table_name}").fetchall()
                data['tables'][table_name] = [dict(row) for row in rows]
            except Exception as e:
                print(f"  Warning: Could not read table {table_name}: {e}")
        
        conn.close()
        return data
    
    def _extract_events(self, data: Dict, source: str) -> List[TimelineEvent]:
        """Extract timeline events from database"""
        events = []
        
        # Look for common event-like tables
        event_tables = [
            'events', 'timeline', 'hearings', 'filings', 
            'motions', 'orders', 'incidents', 'documents'
        ]
        
        for table_name, rows in data['tables'].items():
            if any(et in table_name.lower() for et in event_tables):
                for row in rows:
                    event = self._parse_event_row(row, source, table_name)
                    if event:
                        events.append(event)
        
        return events
    
    def _parse_event_row(self, row: Dict, source: str, table: str) -> Optional[TimelineEvent]:
        """Parse a database row into TimelineEvent"""
        # Try to find date field
        date_fields = ['date', 'event_date', 'filing_date', 'hearing_date', 'created_at', 'timestamp']
        date_value = None
        for field in date_fields:
            if field in row and row[field]:
                date_value = row[field]
                break
        
        if not date_value:
            return None
        
        # Try to find description
        desc_fields = ['description', 'event', 'title', 'summary', 'text', 'content']
        description = None
        for field in desc_fields:
            if field in row and row[field]:
                description = str(row[field])
                break
        
        if not description:
            description = f"Event from {table}"
        
        return TimelineEvent(
            date=str(date_value),
            event_type=table,
            description=description,
            actors=[],  # Will populate later
            evidence_refs=[],
            legal_significance="",
            claims_supported=[],
            source_db=source,
            exact_date=self._is_exact_date(date_value)
        )
    
    def _is_exact_date(self, date_str: str) -> bool:
        """Check if date is exact or approximate"""
        if not date_str:
            return False
        approx_markers = ['circa', 'about', 'approximately', '~']
        return not any(marker in str(date_str).lower() for marker in approx_markers)
    
    def _extract_evidence(self, data: Dict, source: str) -> List[Evidence]:
        """Extract evidence/exhibit references"""
        evidence = []
        
        evidence_tables = ['evidence', 'exhibits', 'documents', 'files', 'attachments']
        
        for table_name, rows in data['tables'].items():
            if any(et in table_name.lower() for et in evidence_tables):
                for row in rows:
                    ev = self._parse_evidence_row(row, source)
                    if ev:
                        evidence.append(ev)
        
        return evidence
    
    def _parse_evidence_row(self, row: Dict, source: str) -> Optional[Evidence]:
        """Parse database row into Evidence"""
        # Try to find exhibit ID
        id_fields = ['exhibit_id', 'id', 'doc_id', 'file_id']
        exhibit_id = None
        for field in id_fields:
            if field in row and row[field]:
                exhibit_id = str(row[field])
                break
        
        if not exhibit_id:
            return None
        
        # Description
        desc_fields = ['description', 'title', 'filename', 'name']
        description = "Document"
        for field in desc_fields:
            if field in row and row[field]:
                description = str(row[field])
                break
        
        return Evidence(
            exhibit_id=exhibit_id,
            description=description,
            source_file=row.get('file_path') or row.get('filepath'),
            date=row.get('date'),
            author=row.get('author'),
            category=row.get('category', 'document'),
            relevance=row.get('relevance', '')
        )
    
    def _extract_entities(self, data: Dict, source: str) -> Dict[str, List[str]]:
        """Extract entity mentions (people, places)"""
        entities = defaultdict(list)
        
        # Define key entities
        key_people = [
            'Andrew J. Pigors', 'Andrew Pigors', 'Emily Watson',
            'Judge McNeill', 'Judge Hoopes', 'Watson'
        ]
        
        key_places = ['Muskegon', 'Shady Oaks', '14th Circuit']
        
        # Search all text fields
        for table_name, rows in data['tables'].items():
            for row in rows:
                for field, value in row.items():
                    if isinstance(value, str):
                        # Check for entity mentions
                        for person in key_people:
                            if person.lower() in value.lower():
                                entities[person].append(f"{source}:{table_name}")
                        
                        for place in key_places:
                            if place.lower() in value.lower():
                                entities[place].append(f"{source}:{table_name}")
        
        return dict(entities)


# ============================================================================
# PART 2: CHRONOLOGICAL NARRATIVE BUILDER
# ============================================================================

class ChronologicalNarrativeBuilder:
    """
    Builds chronological narrative from timeline events.
    Groups into chapters, deduplicates, resolves conflicts.
    """
    
    CHAPTERS = {
        1: "Background (Relationship, Child, Initial Situation)",
        2: "Custody Dispute Origins",
        3: "PPO/Protection Order Events",
        4: "FOC Actions and Recommendations",
        5: "Judge McNeill's Rulings and Conduct",
        6: "Housing/Shady Oaks Issues",
        7: "Judge Hoopes' Rulings",
        8: "Watson Family Actions",
        9: "Civil Rights Violations",
        10: "Harm to Child and Father",
        11: "Current Status and Ongoing Issues"
    }
    
    def __init__(self, events: List[TimelineEvent]):
        self.events = events
        self.sorted_events: List[TimelineEvent] = []
        self.chapters: Dict[int, List[TimelineEvent]] = defaultdict(list)
    
    def build_narrative(self) -> Dict[int, List[TimelineEvent]]:
        """Build complete chronological narrative"""
        print("\n[*] Building chronological narrative...")
        
        # Sort events
        self.sorted_events = self._sort_events(self.events)
        
        # Deduplicate
        self.sorted_events = self._deduplicate_events(self.sorted_events)
        
        # Assign to chapters
        self._assign_chapters()
        
        print(f"[+] Narrative built: {len(self.sorted_events)} events in {len(self.chapters)} chapters")
        
        return self.chapters
    
    def _sort_events(self, events: List[TimelineEvent]) -> List[TimelineEvent]:
        """Sort events chronologically"""
        def parse_date(date_str: str) -> datetime:
            """Parse various date formats"""
            if not date_str:
                return datetime.min
            
            # Remove circa markers
            date_str = re.sub(r'(circa|about|approximately|~)\s*', '', date_str, flags=re.IGNORECASE)
            
            # Try ISO format
            try:
                return datetime.fromisoformat(date_str.split('T')[0])
            except:
                pass
            
            # Try common formats
            formats = [
                '%Y-%m-%d', '%m/%d/%Y', '%m/%d/%y',
                '%Y-%m', '%B %Y', '%b %Y', '%Y'
            ]
            
            for fmt in formats:
                try:
                    return datetime.strptime(date_str.strip(), fmt)
                except:
                    continue
            
            return datetime.min
        
        return sorted(events, key=lambda e: parse_date(e.date))
    
    def _deduplicate_events(self, events: List[TimelineEvent]) -> List[TimelineEvent]:
        """Remove duplicate events"""
        seen = set()
        unique = []
        
        for event in events:
            # Create signature
            sig = (event.date, event.description[:50])
            if sig not in seen:
                seen.add(sig)
                unique.append(event)
        
        return unique
    
    def _assign_chapters(self):
        """Assign events to narrative chapters"""
        for event in self.sorted_events:
            chapter = self._determine_chapter(event)
            event.chapter = self.CHAPTERS.get(chapter, "Other")
            self.chapters[chapter].append(event)
    
    def _determine_chapter(self, event: TimelineEvent) -> int:
        """Determine which chapter an event belongs to"""
        desc_lower = event.description.lower()
        event_type_lower = event.event_type.lower()
        
        # Keywords for each chapter
        if any(kw in desc_lower for kw in ['birth', 'relationship', 'met', 'dating', 'pregnancy']):
            return 1
        elif any(kw in desc_lower for kw in ['custody', 'parenting time', 'visitation']):
            if any(kw in desc_lower for kw in ['mcneill', 'judge', 'ruling', 'order']):
                return 5
            return 2
        elif any(kw in desc_lower for kw in ['ppo', 'protection order', 'restraining']):
            return 3
        elif any(kw in desc_lower for kw in ['foc', 'friend of court', 'referee']):
            return 4
        elif 'mcneill' in desc_lower:
            return 5
        elif any(kw in desc_lower for kw in ['housing', 'shady oaks', 'habitability', 'landlord']):
            return 6
        elif 'hoopes' in desc_lower:
            return 7
        elif any(kw in desc_lower for kw in ['watson', 'family', 'mother']):
            return 8
        elif any(kw in desc_lower for kw in ['civil rights', '1983', 'due process', 'constitutional']):
            return 9
        elif any(kw in desc_lower for kw in ['harm', 'child', 'emotional', 'psychological']):
            return 10
        else:
            return 11  # Current status
    
    def generate_narrative_text(self) -> str:
        """Generate human-readable narrative text"""
        output = []
        output.append("=" * 80)
        output.append("CHRONOLOGICAL NARRATIVE")
        output.append("Andrew J. Pigors v. Watson, et al.")
        output.append("=" * 80)
        output.append("")
        
        for chapter_num in sorted(self.chapters.keys()):
            output.append(f"\n{'=' * 80}")
            output.append(f"CHAPTER {chapter_num}: {self.CHAPTERS[chapter_num]}")
            output.append("=" * 80)
            output.append("")
            
            events = self.chapters[chapter_num]
            for event in events:
                output.append(f"📅 {event.date}" + (" (exact)" if event.exact_date else " (approximate)"))
                output.append(f"   {event.description}")
                
                if event.actors:
                    output.append(f"   Actors: {', '.join(event.actors)}")
                
                if event.evidence_refs:
                    output.append(f"   Evidence: {', '.join(event.evidence_refs)}")
                
                if event.legal_significance:
                    output.append(f"   Legal Significance: {event.legal_significance}")
                
                output.append("")
        
        return "\n".join(output)


# ============================================================================
# PART 3: AFFIDAVIT WRITER
# ============================================================================

class AffidavitWriter:
    """
    Generates Michigan-compliant affidavits per MCR 2.119(B), MCR 2.112
    """
    
    def __init__(self, narrative: ChronologicalNarrativeBuilder, evidence: List[Evidence]):
        self.narrative = narrative
        self.evidence = evidence
        self.affiant_name = "Andrew J. Pigors"
        self.affiant_address = "[Address]"
        self.affiant_phone = "[Phone]"
        self.county = "Muskegon"
    
    def generate_affidavit(
        self, 
        affidavit_type: str = "master",
        case_number: Optional[str] = None
    ) -> str:
        """
        Generate affidavit
        
        Types:
        - master: Comprehensive chronological
        - custody: Lane A specific
        - housing: Lane B specific
        - jtc: Judicial misconduct
        - 1983: Civil rights
        - emergency: Short form
        """
        
        paragraphs = self._build_paragraphs(affidavit_type)
        
        return self._format_affidavit(paragraphs, affidavit_type, case_number)
    
    def _build_paragraphs(self, affidavit_type: str) -> List[AffidavitParagraph]:
        """Build numbered paragraphs for affidavit"""
        paragraphs = []
        
        # Introductory paragraphs (always included)
        paragraphs.append(AffidavitParagraph(
            number=1,
            text=f"I am the Plaintiff in the above-captioned matter. I am over the age of 18 years and am competent to testify to the matters stated herein. I have personal knowledge of the facts stated in this Affidavit.",
            knowledge_basis="personal_knowledge"
        ))
        
        # Type-specific paragraphs
        if affidavit_type == "master":
            paragraphs.extend(self._build_master_paragraphs())
        elif affidavit_type == "custody":
            paragraphs.extend(self._build_custody_paragraphs())
        elif affidavit_type == "housing":
            paragraphs.extend(self._build_housing_paragraphs())
        elif affidavit_type == "jtc":
            paragraphs.extend(self._build_jtc_paragraphs())
        elif affidavit_type == "1983":
            paragraphs.extend(self._build_1983_paragraphs())
        elif affidavit_type == "emergency":
            paragraphs.extend(self._build_emergency_paragraphs())
        
        # Renumber
        for i, para in enumerate(paragraphs, 1):
            para.number = i
        
        return paragraphs
    
    def _build_master_paragraphs(self) -> List[AffidavitParagraph]:
        """Build paragraphs for master chronological affidavit"""
        paragraphs = []
        
        # Background chapter
        if 1 in self.narrative.chapters:
            for event in self.narrative.chapters[1]:
                paragraphs.append(AffidavitParagraph(
                    number=0,  # Will renumber
                    text=f"On or about {event.date}, {event.description}",
                    date=event.date,
                    exhibits=event.evidence_refs,
                    knowledge_basis="personal_knowledge"
                ))
        
        # All other chapters
        for chapter_num in sorted(self.narrative.chapters.keys()):
            if chapter_num == 1:
                continue  # Already did background
            
            # Chapter heading paragraph
            chapter_title = self.narrative.CHAPTERS[chapter_num]
            paragraphs.append(AffidavitParagraph(
                number=0,
                text=f"The following pertains to {chapter_title}:",
                knowledge_basis="personal_knowledge"
            ))
            
            # Events in chapter
            for event in self.narrative.chapters[chapter_num]:
                kb = "personal_knowledge" if event.exact_date else "document_review"
                paragraphs.append(AffidavitParagraph(
                    number=0,
                    text=f"On or about {event.date}, {event.description}",
                    date=event.date,
                    exhibits=event.evidence_refs,
                    knowledge_basis=kb,
                    claims_supported=event.claims_supported
                ))
        
        return paragraphs
    
    def _build_custody_paragraphs(self) -> List[AffidavitParagraph]:
        """Build custody-specific affidavit paragraphs"""
        paragraphs = []
        
        # Focus on chapters 1, 2, 4, 5, 8, 10
        custody_chapters = [1, 2, 4, 5, 8, 10]
        
        for chapter_num in custody_chapters:
            if chapter_num not in self.narrative.chapters:
                continue
            
            for event in self.narrative.chapters[chapter_num]:
                paragraphs.append(AffidavitParagraph(
                    number=0,
                    text=f"On or about {event.date}, {event.description}",
                    date=event.date,
                    exhibits=event.evidence_refs,
                    knowledge_basis="personal_knowledge"
                ))
        
        return paragraphs
    
    def _build_housing_paragraphs(self) -> List[AffidavitParagraph]:
        """Build housing-specific affidavit paragraphs"""
        paragraphs = []
        
        # Focus on chapters 6, 7
        if 6 in self.narrative.chapters:
            for event in self.narrative.chapters[6]:
                paragraphs.append(AffidavitParagraph(
                    number=0,
                    text=f"On or about {event.date}, {event.description}",
                    date=event.date,
                    exhibits=event.evidence_refs,
                    knowledge_basis="personal_knowledge"
                ))
        
        if 7 in self.narrative.chapters:
            for event in self.narrative.chapters[7]:
                paragraphs.append(AffidavitParagraph(
                    number=0,
                    text=f"On or about {event.date}, {event.description}",
                    date=event.date,
                    exhibits=event.evidence_refs,
                    knowledge_basis="personal_knowledge"
                ))
        
        return paragraphs
    
    def _build_jtc_paragraphs(self) -> List[AffidavitParagraph]:
        """Build JTC complaint affidavit paragraphs"""
        paragraphs = []
        
        # Focus on judicial conduct (chapters 5, 7)
        for chapter_num in [5, 7]:
            if chapter_num not in self.narrative.chapters:
                continue
            
            judge_name = "Judge McNeill" if chapter_num == 5 else "Judge Hoopes"
            
            for event in self.narrative.chapters[chapter_num]:
                # Only include events that show potential misconduct
                if any(kw in event.description.lower() for kw in 
                       ['denied', 'refused', 'ex parte', 'bias', 'prejudice', 'failed']):
                    paragraphs.append(AffidavitParagraph(
                        number=0,
                        text=f"On or about {event.date}, {judge_name} {event.description}",
                        date=event.date,
                        exhibits=event.evidence_refs,
                        knowledge_basis="document_review"
                    ))
        
        return paragraphs
    
    def _build_1983_paragraphs(self) -> List[AffidavitParagraph]:
        """Build §1983 civil rights affidavit paragraphs"""
        paragraphs = []
        
        # Focus on chapters 4, 5, 7, 9
        civil_rights_chapters = [4, 5, 7, 9]
        
        for chapter_num in civil_rights_chapters:
            if chapter_num not in self.narrative.chapters:
                continue
            
            for event in self.narrative.chapters[chapter_num]:
                # Focus on constitutional violations
                if any(kw in event.description.lower() for kw in 
                       ['due process', 'civil rights', 'constitutional', 'violation', '1983']):
                    paragraphs.append(AffidavitParagraph(
                        number=0,
                        text=f"On or about {event.date}, {event.description}",
                        date=event.date,
                        exhibits=event.evidence_refs,
                        knowledge_basis="personal_knowledge"
                    ))
        
        return paragraphs
    
    def _build_emergency_paragraphs(self) -> List[AffidavitParagraph]:
        """Build emergency motion affidavit (short form)"""
        paragraphs = []
        
        # Most recent critical events only
        recent_events = self.narrative.sorted_events[-10:]  # Last 10 events
        
        for event in recent_events:
            if any(kw in event.description.lower() for kw in 
                   ['emergency', 'urgent', 'immediate', 'harm', 'danger']):
                paragraphs.append(AffidavitParagraph(
                    number=0,
                    text=f"On or about {event.date}, {event.description}",
                    date=event.date,
                    exhibits=event.evidence_refs,
                    knowledge_basis="personal_knowledge"
                ))
        
        return paragraphs
    
    def _format_affidavit(
        self, 
        paragraphs: List[AffidavitParagraph],
        affidavit_type: str,
        case_number: Optional[str]
    ) -> str:
        """Format affidavit with Michigan heading and signature block"""
        
        output = []
        
        # Heading
        output.append("STATE OF MICHIGAN")
        output.append(f"COUNTY OF {self.county.upper()}")
        output.append("")
        
        if case_number:
            output.append(f"Case No. {case_number}")
            output.append("")
        
        output.append(f"AFFIDAVIT OF {self.affiant_name.upper()}")
        output.append("")
        
        output.append(f"I, {self.affiant_name}, being first duly sworn, depose and state as follows:")
        output.append("")
        
        # Paragraphs
        for para in paragraphs:
            para_text = f"{para.number}. {para.text}"
            
            # Add exhibit references
            if para.exhibits:
                exhibit_text = ", ".join(para.exhibits)
                para_text += f" A true and correct copy is attached as Exhibit {exhibit_text}."
            
            output.append(para_text)
            output.append("")
        
        # Closing
        output.append("FURTHER AFFIANT SAYETH NOT.")
        output.append("")
        output.append("")
        output.append("                                    ____________________________")
        output.append(f"                                    {self.affiant_name}")
        output.append(f"                                    {self.affiant_address}")
        output.append(f"                                    {self.affiant_phone}")
        output.append("")
        output.append("")
        output.append("Subscribed and sworn to before me")
        output.append("this ___ day of _________, 2026.")
        output.append("")
        output.append("")
        output.append("____________________________")
        output.append("Notary Public, State of Michigan")
        output.append(f"County of {self.county}")
        output.append("My Commission Expires: __________")
        
        return "\n".join(output)


# ============================================================================
# PART 4: CLAIM ANALYZER
# ============================================================================

class ClaimAnalyzer:
    """
    Analyzes evidence to determine viable legal claims.
    Evaluates elements, strength, SOL, venue.
    """
    
    def __init__(self, events: List[TimelineEvent], evidence: List[Evidence]):
        self.events = events
        self.evidence = evidence
        self.claims: List[LegalClaim] = []
    
    def analyze_all_claims(self) -> List[LegalClaim]:
        """Analyze all potential claims"""
        print("\n[*] Analyzing legal claims...")
        
        self.claims = []
        
        # Claims against Emily Watson
        self.claims.extend(self._analyze_watson_claims())
        
        # Claims against Watson family
        self.claims.extend(self._analyze_family_claims())
        
        # Claims against judges
        self.claims.extend(self._analyze_judge_claims())
        
        # Claims against FOC
        self.claims.extend(self._analyze_foc_claims())
        
        # Claims against housing
        self.claims.extend(self._analyze_housing_claims())
        
        # Sort by strength and priority
        self.claims.sort(key=lambda c: (c.filing_priority, -c.strength_score))
        
        print(f"[+] Analysis complete: {len(self.claims)} claims identified")
        
        return self.claims
    
    def _analyze_watson_claims(self) -> List[LegalClaim]:
        """Analyze claims against Emily Watson"""
        claims = []
        
        # Custody Interference
        claims.append(LegalClaim(
            claim_type=ClaimType.CUSTODY_INTERFERENCE,
            defendant="Emily Watson",
            legal_basis="Michigan common law; MCL 722.27",
            elements=[
                ClaimElement("Valid custody order or parenting time", True, [], "Court orders exist"),
                ClaimElement("Defendant intentionally interfered", False, [], "Need specific evidence"),
                ClaimElement("Harm to parental relationship", False, [], "Need documentation")
            ],
            supporting_evidence=[],
            strength_score=50,
            statute_of_limitations="3 years (tort)",
            sol_deadline=None,
            recommended_venue=CourtVenue.MUSKEGON_CIRCUIT,
            risks=["Need clear evidence of intentional interference", "Custody court may be exclusive venue"],
            filing_priority=2,
            notes="Evaluate in context of existing custody case"
        ))
        
        # PPO Abuse of Process
        claims.append(LegalClaim(
            claim_type=ClaimType.PPO_ABUSE,
            defendant="Emily Watson",
            legal_basis="Michigan common law - abuse of process",
            elements=[
                ClaimElement("Legal process was used", False, [], "Need PPO records"),
                ClaimElement("Ulterior motive", False, [], "Need evidence of motive"),
                ClaimElement("Harm resulted", False, [], "Need harm documentation")
            ],
            supporting_evidence=[],
            strength_score=40,
            statute_of_limitations="3 years",
            sol_deadline=None,
            recommended_venue=CourtVenue.MUSKEGON_CIRCUIT,
            risks=["Difficult to prove ulterior motive", "PPO may have been granted in good faith"],
            filing_priority=3
        ))
        
        # IIED
        claims.append(LegalClaim(
            claim_type=ClaimType.IIED,
            defendant="Emily Watson",
            legal_basis="Michigan common law - intentional infliction of emotional distress",
            elements=[
                ClaimElement("Extreme and outrageous conduct", False, [], "Need specific acts"),
                ClaimElement("Intentional or reckless", False, [], "Need evidence of intent"),
                ClaimElement("Severe emotional distress", False, [], "Need medical/counseling records"),
                ClaimElement("Causation", False, [], "Need causal link")
            ],
            supporting_evidence=[],
            strength_score=35,
            statute_of_limitations="3 years",
            sol_deadline=None,
            recommended_venue=CourtVenue.MUSKEGON_CIRCUIT,
            risks=["High bar for 'extreme and outrageous'", "Need strong medical evidence"],
            filing_priority=4
        ))
        
        return claims
    
    def _analyze_family_claims(self) -> List[LegalClaim]:
        """Analyze claims against Watson family members"""
        claims = []
        
        # Civil Conspiracy
        claims.append(LegalClaim(
            claim_type=ClaimType.CIVIL_CONSPIRACY,
            defendant="Watson Family Members",
            legal_basis="Michigan common law - civil conspiracy",
            elements=[
                ClaimElement("Agreement between parties", False, [], "Need evidence of coordination"),
                ClaimElement("Unlawful act or lawful act by unlawful means", False, [], "Need underlying tort"),
                ClaimElement("Harm resulted", False, [], "Need damages")
            ],
            supporting_evidence=[],
            strength_score=30,
            statute_of_limitations="3 years",
            sol_deadline=None,
            recommended_venue=CourtVenue.MUSKEGON_CIRCUIT,
            risks=["Hard to prove agreement", "Needs underlying tort"],
            filing_priority=5
        ))
        
        # Tortious Interference
        claims.append(LegalClaim(
            claim_type=ClaimType.TORTIOUS_INTERFERENCE,
            defendant="Watson Family Members",
            legal_basis="Michigan common law - tortious interference with parental relationship",
            elements=[
                ClaimElement("Valid parental relationship", True, [], "Established"),
                ClaimElement("Defendant knew of relationship", False, [], "Likely provable"),
                ClaimElement("Intentional interference", False, [], "Need specific acts"),
                ClaimElement("Harm resulted", False, [], "Need documentation")
            ],
            supporting_evidence=[],
            strength_score=35,
            statute_of_limitations="3 years",
            sol_deadline=None,
            recommended_venue=CourtVenue.MUSKEGON_CIRCUIT,
            risks=["Need specific acts by family members", "May be privileged if supporting Emily"],
            filing_priority=4
        ))
        
        return claims
    
    def _analyze_judge_claims(self) -> List[LegalClaim]:
        """Analyze claims against judges"""
        claims = []
        
        # Judge McNeill - Judicial Misconduct
        claims.append(LegalClaim(
            claim_type=ClaimType.JUDICIAL_MISCONDUCT,
            defendant="Judge McNeill",
            legal_basis="Michigan Judicial Tenure Commission rules",
            elements=[
                ClaimElement("Violation of Michigan Code of Judicial Conduct", False, [], "Need specific rule violations"),
                ClaimElement("Pattern of conduct or serious single act", False, [], "Need documentation"),
                ClaimElement("Harm to judicial integrity", False, [], "Arguable from record")
            ],
            supporting_evidence=[],
            strength_score=45,
            statute_of_limitations="N/A (JTC complaint)",
            sol_deadline="Within reasonable time of discovery",
            recommended_venue=CourtVenue.JTC,
            risks=["JTC rarely disciplines judges", "High bar for finding misconduct"],
            filing_priority=1,
            notes="File JTC complaint separate from civil action"
        ))
        
        # Judge McNeill - Due Process (§1983)
        claims.append(LegalClaim(
            claim_type=ClaimType.SECTION_1983,
            defendant="Judge McNeill",
            legal_basis="42 U.S.C. § 1983 - deprivation of due process",
            elements=[
                ClaimElement("Acting under color of state law", True, [], "Judge acting in official capacity"),
                ClaimElement("Deprivation of constitutional right", False, [], "Need due process violation"),
                ClaimElement("No absolute judicial immunity", False, [], "Immunity likely applies"),
                ClaimElement("Causation and harm", False, [], "Need damages")
            ],
            supporting_evidence=[],
            strength_score=20,
            statute_of_limitations="3 years",
            sol_deadline=None,
            recommended_venue=CourtVenue.FEDERAL_DISTRICT,
            risks=["Judicial immunity is nearly absolute", "Very difficult to overcome", "11th Amendment sovereign immunity"],
            filing_priority=7,
            notes="Low chance of success due to judicial immunity"
        ))
        
        # Judge Hoopes - Same analysis
        claims.append(LegalClaim(
            claim_type=ClaimType.JUDICIAL_MISCONDUCT,
            defendant="Judge Hoopes",
            legal_basis="Michigan Judicial Tenure Commission rules",
            elements=[
                ClaimElement("Violation of Michigan Code of Judicial Conduct", False, [], "Need specific rule violations"),
                ClaimElement("Pattern of conduct or serious single act", False, [], "Need documentation"),
                ClaimElement("Harm to judicial integrity", False, [], "Arguable from record")
            ],
            supporting_evidence=[],
            strength_score=40,
            statute_of_limitations="N/A (JTC complaint)",
            sol_deadline="Within reasonable time of discovery",
            recommended_venue=CourtVenue.JTC,
            risks=["JTC rarely disciplines judges", "High bar for finding misconduct"],
            filing_priority=2,
            notes="File JTC complaint separate from civil action"
        ))
        
        return claims
    
    def _analyze_foc_claims(self) -> List[LegalClaim]:
        """Analyze claims against Friend of Court"""
        claims = []
        
        # FOC - Due Process / §1983
        claims.append(LegalClaim(
            claim_type=ClaimType.SECTION_1983,
            defendant="Muskegon County Friend of Court",
            legal_basis="42 U.S.C. § 1983 - due process violation",
            elements=[
                ClaimElement("Acting under color of state law", True, [], "FOC is state agency"),
                ClaimElement("Deprivation of constitutional right", False, [], "Need due process violation"),
                ClaimElement("No qualified immunity defense", False, [], "May apply"),
                ClaimElement("Causation and harm", False, [], "Need damages")
            ],
            supporting_evidence=[],
            strength_score=40,
            statute_of_limitations="3 years",
            sol_deadline=None,
            recommended_venue=CourtVenue.FEDERAL_DISTRICT,
            risks=["Qualified immunity may apply", "Need clear constitutional violation", "11th Amendment issues"],
            filing_priority=3,
            notes="More viable than claims against judges"
        ))
        
        # FOC - Bias in Recommendations
        claims.append(LegalClaim(
            claim_type=ClaimType.FOC_BIAS,
            defendant="Muskegon County Friend of Court",
            legal_basis="MCL 552.505; due process",
            elements=[
                ClaimElement("FOC made biased recommendations", False, [], "Need evidence of bias"),
                ClaimElement("Recommendations affected custody decision", False, [], "Need causal link"),
                ClaimElement("Harm resulted", False, [], "Need damages")
            ],
            supporting_evidence=[],
            strength_score=35,
            statute_of_limitations="3 years",
            sol_deadline=None,
            recommended_venue=CourtVenue.MUSKEGON_CIRCUIT,
            risks=["FOC has discretion", "Hard to prove bias vs. professional judgment"],
            filing_priority=4
        ))
        
        return claims
    
    def _analyze_housing_claims(self) -> List[LegalClaim]:
        """Analyze housing/habitability claims"""
        claims = []
        
        # Breach of Implied Warranty of Habitability
        claims.append(LegalClaim(
            claim_type=ClaimType.BREACH_HABITABILITY,
            defendant="Shady Oaks / Landlord",
            legal_basis="MCL 554.139 - implied warranty of habitability",
            elements=[
                ClaimElement("Landlord-tenant relationship", False, [], "Need lease"),
                ClaimElement("Conditions violated habitability standards", False, [], "Need inspection reports"),
                ClaimElement("Landlord had notice", False, [], "Need complaint records"),
                ClaimElement("Landlord failed to remedy", False, [], "Need evidence of inaction"),
                ClaimElement("Harm/damages resulted", False, [], "Need documentation")
            ],
            supporting_evidence=[],
            strength_score=55,
            statute_of_limitations="6 years (contract)",
            sol_deadline=None,
            recommended_venue=CourtVenue.MUSKEGON_CIRCUIT,
            risks=["Need strong evidence of conditions", "Damages may be limited"],
            filing_priority=2,
            notes="Potentially strongest claim if evidence exists"
        ))
        
        # Negligence
        claims.append(LegalClaim(
            claim_type=ClaimType.NEGLIGENCE,
            defendant="Shady Oaks / Landlord",
            legal_basis="Michigan common law negligence",
            elements=[
                ClaimElement("Duty of care", True, [], "Landlord owes duty"),
                ClaimElement("Breach of duty", False, [], "Need evidence of negligence"),
                ClaimElement("Causation", False, [], "Need causal link"),
                ClaimElement("Damages", False, [], "Need harm documentation")
            ],
            supporting_evidence=[],
            strength_score=50,
            statute_of_limitations="3 years",
            sol_deadline=None,
            recommended_venue=CourtVenue.MUSKEGON_CIRCUIT,
            risks=["Need clear breach", "Comparative negligence may reduce recovery"],
            filing_priority=3
        ))
        
        return claims
    
    def generate_claims_report(self) -> str:
        """Generate detailed claims analysis report"""
        output = []
        output.append("=" * 80)
        output.append("LEGAL CLAIMS ANALYSIS")
        output.append("Andrew J. Pigors v. Watson, et al.")
        output.append("=" * 80)
        output.append("")
        
        # Group by defendant
        by_defendant = defaultdict(list)
        for claim in self.claims:
            by_defendant[claim.defendant].append(claim)
        
        for defendant, claims in by_defendant.items():
            output.append(f"\n{'=' * 80}")
            output.append(f"CLAIMS AGAINST: {defendant}")
            output.append("=" * 80)
            
            for claim in claims:
                output.append(f"\n{claim.claim_type.value.upper().replace('_', ' ')}")
                output.append(f"Legal Basis: {claim.legal_basis}")
                output.append(f"Strength: {claim.strength_score}/100")
                output.append(f"Priority: {claim.filing_priority}")
                output.append(f"Venue: {claim.recommended_venue.value}")
                output.append(f"SOL: {claim.statute_of_limitations}")
                if claim.sol_deadline:
                    output.append(f"Deadline: {claim.sol_deadline}")
                
                output.append("\nElements:")
                for elem in claim.elements:
                    status = "[+]" if elem.met else "[X]"
                    output.append(f"  {status} {elem.element}")
                    if elem.reasoning:
                        output.append(f"     {elem.reasoning}")
                
                if claim.risks:
                    output.append("\nRisks:")
                    for risk in claim.risks:
                        output.append(f"  [!] {risk}")
                
                if claim.notes:
                    output.append(f"\nNotes: {claim.notes}")
                
                output.append("")
        
        # Summary
        output.append("\n" + "=" * 80)
        output.append("SUMMARY")
        output.append("=" * 80)
        output.append(f"\nTotal Claims Identified: {len(self.claims)}")
        
        # By strength
        strong = len([c for c in self.claims if c.strength_score >= 60])
        moderate = len([c for c in self.claims if 40 <= c.strength_score < 60])
        weak = len([c for c in self.claims if c.strength_score < 40])
        
        output.append(f"  Strong (60+):   {strong}")
        output.append(f"  Moderate (40-59): {moderate}")
        output.append(f"  Weak (<40):     {weak}")
        
        # By venue
        output.append("\nBy Venue:")
        by_venue = defaultdict(int)
        for claim in self.claims:
            by_venue[claim.recommended_venue.value] += 1
        
        for venue, count in sorted(by_venue.items()):
            output.append(f"  {venue}: {count}")
        
        # Priority recommendations
        output.append("\nRecommended Filing Order:")
        priority_claims = sorted(self.claims, key=lambda c: c.filing_priority)[:5]
        for i, claim in enumerate(priority_claims, 1):
            output.append(f"  {i}. {claim.claim_type.value} vs {claim.defendant} (strength: {claim.strength_score})")
        
        return "\n".join(output)


# ============================================================================
# MAIN CLI
# ============================================================================

def main():
    """Main CLI entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Affidavit Agent - Build comprehensive affidavits from LitigationOS data"
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')
    
    # narrative command
    subparsers.add_parser('narrative', help='Build full chronological narrative')
    
    # affidavit command
    affidavit_parser = subparsers.add_parser('affidavit', help='Generate affidavit')
    affidavit_parser.add_argument('--master', action='store_true', help='Master affidavit')
    affidavit_parser.add_argument('--custody', action='store_true', help='Custody affidavit')
    affidavit_parser.add_argument('--housing', action='store_true', help='Housing affidavit')
    affidavit_parser.add_argument('--jtc', action='store_true', help='JTC complaint affidavit')
    affidavit_parser.add_argument('--1983', dest='civil_rights', action='store_true', help='§1983 affidavit')
    affidavit_parser.add_argument('--emergency', action='store_true', help='Emergency affidavit')
    affidavit_parser.add_argument('--case', help='Case number')
    
    # claims command
    claims_parser = subparsers.add_parser('claims', help='Analyze legal claims')
    claims_parser.add_argument('--against', choices=['watson', 'judge', 'foc', 'housing', 'all'], 
                               default='all', help='Filter by defendant')
    
    # report command
    subparsers.add_parser('report', help='Full status report')
    
    # all command
    subparsers.add_parser('all', help='Generate everything')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Initialize
    print(">> Affidavit Agent Starting...")
    print("=" * 80)
    
    # Read data
    reader = AffidavitDataReader()
    data = reader.read_all_databases()
    
    # Build narrative
    builder = ChronologicalNarrativeBuilder(reader.events)
    chapters = builder.build_narrative()
    
    # Create output directories
    base_output = Path(r"C:\Users\andre\LitigationOS\07_COURT_DOCUMENTS")
    (base_output / "narratives").mkdir(parents=True, exist_ok=True)
    (base_output / "lane_A_custody" / "affidavits").mkdir(parents=True, exist_ok=True)
    (base_output / "lane_B_housing" / "affidavits").mkdir(parents=True, exist_ok=True)
    (base_output / "lane_C_convergence" / "affidavits").mkdir(parents=True, exist_ok=True)
    (base_output / "analysis").mkdir(parents=True, exist_ok=True)
    
    # Execute command
    if args.command == 'narrative' or args.command == 'all':
        print("\n[*] Generating narrative...")
        narrative_text = builder.generate_narrative_text()
        output_path = base_output / "narratives" / "master_chronology.txt"
        output_path.write_text(narrative_text, encoding='utf-8')
        print(f"[+] Narrative saved: {output_path}")
    
    if args.command == 'affidavit' or args.command == 'all':
        writer = AffidavitWriter(builder, reader.evidence)
        
        affidavit_types = []
        if args.command == 'all':
            affidavit_types = ['master', 'custody', 'housing', 'jtc', '1983']
        else:
            if args.master:
                affidavit_types.append('master')
            if args.custody:
                affidavit_types.append('custody')
            if args.housing:
                affidavit_types.append('housing')
            if args.jtc:
                affidavit_types.append('jtc')
            if args.civil_rights:
                affidavit_types.append('1983')
            if args.emergency:
                affidavit_types.append('emergency')
        
        for aff_type in affidavit_types:
            print(f"\n[*] Generating {aff_type} affidavit...")
            affidavit_text = writer.generate_affidavit(aff_type, args.case if hasattr(args, 'case') else None)
            
            # Determine output path
            if aff_type == 'custody':
                output_path = base_output / "lane_A_custody" / "affidavits" / "affidavit_custody.txt"
            elif aff_type == 'housing':
                output_path = base_output / "lane_B_housing" / "affidavits" / "affidavit_housing.txt"
            elif aff_type in ['jtc', '1983']:
                output_path = base_output / "lane_C_convergence" / "affidavits" / f"affidavit_{aff_type}.txt"
            else:
                output_path = base_output / "narratives" / f"affidavit_{aff_type}.txt"
            
            output_path.write_text(affidavit_text, encoding='utf-8')
            print(f"[+] Affidavit saved: {output_path}")
    
    if args.command == 'claims' or args.command == 'all':
        print("\n[*] Analyzing claims...")
        analyzer = ClaimAnalyzer(reader.events, reader.evidence)
        claims = analyzer.analyze_all_claims()
        
        # Filter if requested
        if hasattr(args, 'against') and args.against != 'all':
            if args.against == 'watson':
                claims = [c for c in claims if 'watson' in c.defendant.lower()]
            elif args.against == 'judge':
                claims = [c for c in claims if 'judge' in c.defendant.lower()]
            elif args.against == 'foc':
                claims = [c for c in claims if 'foc' in c.defendant.lower() or 'friend' in c.defendant.lower()]
            elif args.against == 'housing':
                claims = [c for c in claims if 'shady' in c.defendant.lower() or 'landlord' in c.defendant.lower()]
        
        report = analyzer.generate_claims_report()
        output_path = base_output / "analysis" / "claims_report.txt"
        output_path.write_text(report, encoding='utf-8')
        print(f"[+] Claims report saved: {output_path}")
    
    if args.command == 'report' or args.command == 'all':
        print("\n[*] Generating full report...")
        
        report_lines = []
        report_lines.append("=" * 80)
        report_lines.append("AFFIDAVIT AGENT STATUS REPORT")
        report_lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append("=" * 80)
        report_lines.append("")
        
        report_lines.append("DATA SOURCES:")
        for db_name, db_path in reader.databases.items():
            exists = "[+]" if db_path.exists() else "[X]"
            report_lines.append(f"  {exists} {db_name}: {db_path}")
        
        report_lines.append(f"\nEVENTS EXTRACTED: {len(reader.events)}")
        report_lines.append(f"EVIDENCE ITEMS: {len(reader.evidence)}")
        report_lines.append(f"ENTITIES TRACKED: {len(reader.entities)}")
        
        report_lines.append(f"\nCHAPTERS BUILT: {len(chapters)}")
        for chapter_num in sorted(chapters.keys()):
            event_count = len(chapters[chapter_num])
            report_lines.append(f"  Chapter {chapter_num}: {event_count} events")
        
        report_lines.append("\nOUTPUT FILES:")
        for output_dir in [base_output / "narratives", 
                          base_output / "lane_A_custody" / "affidavits",
                          base_output / "lane_B_housing" / "affidavits",
                          base_output / "lane_C_convergence" / "affidavits",
                          base_output / "analysis"]:
            if output_dir.exists():
                files = list(output_dir.glob("*.*"))
                report_lines.append(f"  {output_dir}: {len(files)} files")
        
        report_text = "\n".join(report_lines)
        output_path = base_output / "analysis" / "agent_report.txt"
        output_path.write_text(report_text, encoding='utf-8')
        print(f"[+] Report saved: {output_path}")
    
    print("\n" + "=" * 80)
    print("[+] Affidavit Agent Complete")
    print("=" * 80)


if __name__ == "__main__":
    main()
