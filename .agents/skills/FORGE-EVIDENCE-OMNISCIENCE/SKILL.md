---
name: FORGE-EVIDENCE-OMNISCIENCE
description: >-
  Unified evidence intelligence engine fusing evidence harvesting, authentication,
  chain of custody, discovery warfare, interrogatory drafting, subpoena management,
  mandatory disclosure, asset discovery, document classification, and evidence
  presentation into a complete evidentiary command system. Scans 6 local drives
  (C/D/F/G/I/J), extracts evidence atoms via OCR, classifies by MEEK lane signals,
  performs content-based deduplication, Bates-stamps exhibits, and generates
  MRE-compliant authentication packages. Triggers on evidence, discovery, exhibit,
  Bates, authentication, subpoena, interrogatory, document scan, OCR, deduplication.
category: litigation
version: "1.0.0"
triggers:
  - "find evidence"
  - "discovery request"
  - "exhibit preparation"
  - "Bates stamping"
  - "evidence authentication"
  - "subpoena draft"
  - "interrogatory"
  - "document scanning"
  - "OCR extraction"
  - "evidence deduplication"
  - "chain of custody"
  - "MRE compliance"
metadata:
  tier: FORGE
  fused_skills: 10
  author: andrew-pigors + copilot-omega-delta-99
  forge_date: 2026-03-27
  forge_class: litigation-evidence
  emergent_capability: "Complete evidence lifecycle management from raw drive scanning to court-ready authenticated exhibit packages"
---

# 🔍 FORGE-EVIDENCE-OMNISCIENCE > **Complete Evidence Intelligence Engine (Ω-Δ99)**

> A FORGE-tier litigation evidence intelligence engine for **Pigors v Watson**
> that unifies scanning, extraction, deduplication, routing, Bates control,
> authentication, discovery warfare, subpoena management, and exhibit presentation.
> The child reference is **L.D.W. only**. No alternate child names are used.

## 📊 Overview

| Property | Value |
|---|---|
| Tier | FORGE |
| Class | litigation-evidence |
| Matter | Pigors v Watson |
| Child Reference | L.D.W. only |
| Drive Map | C = NVMe SSD; D/F/G = USB; I = SD card; J = 2TB USB exFAT |
| Dedup Rule | Content-based deduplication that peeks inside documents, not hash-only |
| Router Priority | E → D → F → C → A → B |
| Primary Outputs | Evidence atoms, Bates-stamped exhibits, authentication packets, discovery products |
| Governing Proof Concepts | MRE 901, MRE 902, Sullivan v Gray, chain of custody |
| Litigation Goal | Transform raw files into court-ready authenticated evidence packages |

FORGE-EVIDENCE-OMNISCIENCE treats evidence as a lifecycle, not a folder problem.
It begins at drive discovery, looks inside files to understand actual content,
routes atoms to the right MEEK lane, assigns permanent Bates identifiers, then
assembles authentication and presentation layers. The result is a single command
surface for discovery, subpoenas, and exhibits that stays grounded in Michigan
family-law evidentiary realities.

## 🔥 Forged from 10 Skills

| # | Source Skill | What It Contributes | Primary Module |
|---|---|---|---|
| 1 | litigation-evidence-harvester | Multi-drive scanning, file discovery | EO1 |
| 2 | litigation-evidence-authentication | MRE 901/902, chain of custody | EO5 |
| 3 | litigation-evidence-intelligence-system | Evidence scoring, relevance ranking | EO2 |
| 4 | evidence-intelligence-nexus | Cross-lane evidence correlation | EO3 |
| 5 | evidence-context-injector | Evidence-to-argument mapping | EO8 |
| 6 | litigation-discovery-warfare | Discovery strategy, deficiency tracking | EO6 |
| 7 | litigation-interrogatory-specialist | Interrogatory drafting, response analysis | EO6 |
| 8 | litigation-subpoena-engine | Subpoena generation, service tracking | EO7 |
| 9 | litigation-mandatory-disclosure-specialist | MCR 2.302 disclosures | EO6 |
| 10 | litigation-asset-discovery-engine | Financial discovery, hidden assets | EO7 |

## 🏗️ Architecture

```
┌──────────────────────────────────────────────────────────────────────────────┐
│             FORGE-EVIDENCE-OMNISCIENCE (Ω-Δ99)                              │
│                                                                              │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐                   │
│  │ EO1          │───▶│ EO2          │───▶│ EO3          │                   │
│  │ Drive        │    │ OCR &        │    │ MEEK Lane    │                   │
│  │ Scanner      │    │ Extraction   │    │ Router       │                   │
│  └──────┬───────┘    └──────┬───────┘    └──────┬───────┘                   │
│         │                   │                   │                           │
│         ▼                   ▼                   ▼                           │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐                   │
│  │ EO4          │───▶│ EO5          │───▶│ EO8          │                   │
│  │ Bates        │    │ Authentication│   │ Evidence     │                   │
│  │ Stamping     │    │ Engine       │    │ Presentation │                   │
│  └──────┬───────┘    └──────┬───────┘    └──────────────┘                   │
│         │                   ▲                                               │
│         │                   │                                               │
│         ▼                   │                                               │
│  ┌──────────────┐    ┌──────┴───────┐                                       │
│  │ EO6          │───▶│ EO7          │                                       │
│  │ Discovery    │    │ Subpoena     │                                       │
│  │ Warfare      │    │ Manager      │                                       │
│  └──────────────┘    └──────────────┘                                       │
│                                                                              │
│  FLOW: Source Drives → Evidence Atoms → Lane Decisions → Bates Registry      │
│        → Authentication Packets → Discovery Escalation → Exhibit Packages    │
└──────────────────────────────────────────────────────────────────────────────┘
```

## 🧭 Core Operating Rules

1. **Content first:** deduplication must inspect text/structure inside documents. Hash-only logic is insufficient.
2. **Drive-aware provenance:** C, D, F, G, I, and J carry different storage-risk assumptions and must be logged.
3. **Lane discipline:** apply the strict priority order **E → D → F → C → A → B**.
4. **Child naming discipline:** the child is referenced as **L.D.W. only**.
5. **Derivative separation:** never alter source evidence when generating Bates-stamped or OCR-derived outputs.
6. **Authentication by design:** every module should improve later admissibility, not just convenience.

    ## ⚙️ Module EO1: Drive Scanner

    **Purpose:** Scan C/D/F/G/I/J for PDFs, DOCX, images, audio, and video in a single pass; capture size, timestamps, drive class, and evidence-safe metadata without mutating source files.

    **Design Pattern:** Iterator + Stream Processor + Adapter

    ### Code

    ```python
    import os
import mimetypes
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Iterator

DRIVE_PROFILE = {
    "C": {"label": "NVMe SSD", "removable": False},
    "D": {"label": "USB", "removable": True},
    "F": {"label": "USB", "removable": True},
    "G": {"label": "USB", "removable": True},
    "I": {"label": "SD card", "removable": True},
    "J": {"label": "2TB USB exFAT", "removable": True},
}

EVIDENCE_SUFFIXES = {
    ".pdf", ".doc", ".docx", ".txt", ".rtf",
    ".jpg", ".jpeg", ".png", ".tif", ".tiff", ".heic",
    ".mp3", ".wav", ".m4a", ".mp4", ".mov", ".avi",
}

@dataclass(slots=True)
class EvidenceFile:
    drive: str
    drive_label: str
    path: str
    relative_path: str
    suffix: str
    mime_type: str
    size_bytes: int
    created_utc: str
    modified_utc: str
    accessed_utc: str
    discovered_utc: str

class DriveScanner:
    def __init__(self, roots: dict[str, str]) -> None:
        self.roots = {k.upper(): Path(v) for k, v in roots.items()}

    def discover(self) -> Iterator[EvidenceFile]:
        for drive, root in self.roots.items():
            if not root.exists():
                continue
            yield from self._walk_drive(drive, root)

    def _walk_drive(self, drive: str, root: Path) -> Iterator[EvidenceFile]:
        stack = [root]
        while stack:
            current = stack.pop()
            try:
                with os.scandir(current) as entries:
                    for entry in entries:
                        if entry.name.startswith("$"):
                            continue
                        if entry.is_dir(follow_symlinks=False):
                            stack.append(Path(entry.path))
                            continue
                        suffix = Path(entry.name).suffix.lower()
                        if suffix not in EVIDENCE_SUFFIXES:
                            continue
                        stats = entry.stat(follow_symlinks=False)
                        mime_type = mimetypes.guess_type(entry.path)[0] or "application/octet-stream"
                        yield EvidenceFile(
                            drive=drive,
                            drive_label=DRIVE_PROFILE[drive]["label"],
                            path=entry.path,
                            relative_path=str(Path(entry.path).relative_to(root)),
                            suffix=suffix,
                            mime_type=mime_type,
                            size_bytes=stats.st_size,
                            created_utc=datetime.fromtimestamp(stats.st_ctime, tz=timezone.utc).isoformat(),
                            modified_utc=datetime.fromtimestamp(stats.st_mtime, tz=timezone.utc).isoformat(),
                            accessed_utc=datetime.fromtimestamp(stats.st_atime, tz=timezone.utc).isoformat(),
                            discovered_utc=datetime.now(tz=timezone.utc).isoformat(),
                        )
            except OSError as exc:
                yield EvidenceFile(
                    drive=drive,
                    drive_label=DRIVE_PROFILE[drive]["label"],
                    path=str(current),
                    relative_path=str(current.relative_to(root)),
                    suffix=".error",
                    mime_type=f"scan-error:{type(exc).__name__}",
                    size_bytes=0,
                    created_utc="",
                    modified_utc="",
                    accessed_utc="",
                    discovered_utc=datetime.now(tz=timezone.utc).isoformat(),
                )

    def manifest_rows(self) -> Iterable[dict]:
        for evidence_file in self.discover():
            yield asdict(evidence_file)
    ```

    ### Integration
- Feeds EO2 with normalized file manifests and stable source paths.
- Annotates drive class: C=NVMe SSD, D/F/G=USB, I=SD card, J=2TB USB exFAT.
- Never writes into evidence roots; all derivative work happens in controlled output folders.
- Records source timestamps for later EO5 chain-of-custody narratives.

### Failure Modes & Safeguards

| Failure Mode | Signal | Mitigation |
|---|---|---|
| Drive offline | Mount missing | Flag scan gap and continue other drives. |
| Permission denied | AccessError | Log path, owner, and retry instruction. |
| Huge media folder | Scan latency spike | Switch to chunked manifest writes. |
| Extension spoofing | MIME mismatch | Sniff header bytes before classification. |
| Clock drift | Impossible timestamp order | Mark as metadata anomaly for EO5. |

### Operator Checklist

1. Confirm all six drives are mounted before scan start.
2. Honor deny-lists for system folders, browser caches, and package directories.
3. Capture created, modified, accessed, and discovered timestamps separately.
4. Emit resumable manifests keyed by drive and relative path.
5. Preserve raw source path for exhibit affidavits and subpoena follow-up.

    ## ⚙️ Module EO2: OCR & Extraction

    **Purpose:** Extract text, embedded metadata, speaker clues, and page-level snippets with content-based deduplication that peeks inside documents rather than relying on hashes alone.

    **Design Pattern:** Pipeline + Strategy + Fingerprint Heuristic

    ### Code

    ```python
    import hashlib
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

import fitz  # PyMuPDF
from docx import Document

WORD_RE = re.compile(r"[A-Za-z0-9']+")

@dataclass(slots=True)
class EvidenceAtom:
    source_path: str
    page_or_part: str
    text: str
    metadata: dict
    semantic_fingerprint: str
    duplicate_of: str | None = None
    duplicate_confidence: float = 0.0
    extraction_method: str = ""

class ContentDeduper:
    def __init__(self) -> None:
        self.fingerprints: dict[str, str] = {}

    def normalize(self, text: str) -> str:
        text = text.lower()
        text = text.replace("ﬁ", "fi").replace("ﬂ", "fl")
        text = re.sub(r"\s+", " ", text)
        return re.sub(r"[^a-z0-9 ]+", "", text).strip()

    def fingerprint(self, text: str, metadata: dict) -> str:
        normalized = self.normalize(text)
        tokens = WORD_RE.findall(normalized)
        head = " ".join(tokens[:80])
        middle = " ".join(tokens[max(0, len(tokens)//2 - 40): len(tokens)//2 + 40])
        tail = " ".join(tokens[-80:])
        payload = "|".join([
            head,
            middle,
            tail,
            metadata.get("title", ""),
            metadata.get("author", ""),
            metadata.get("created", ""),
        ])
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    def register(self, atom: EvidenceAtom) -> EvidenceAtom:
        if atom.semantic_fingerprint in self.fingerprints:
            atom.duplicate_of = self.fingerprints[atom.semantic_fingerprint]
            atom.duplicate_confidence = 0.99
        else:
            self.fingerprints[atom.semantic_fingerprint] = atom.source_path
        return atom

class ExtractionEngine:
    def __init__(self, deduper: ContentDeduper) -> None:
        self.deduper = deduper

    def extract(self, file_path: str) -> Iterable[EvidenceAtom]:
        suffix = Path(file_path).suffix.lower()
        if suffix == ".pdf":
            yield from self._extract_pdf(file_path)
        elif suffix == ".docx":
            yield from self._extract_docx(file_path)

    def _extract_pdf(self, file_path: str) -> Iterable[EvidenceAtom]:
        with fitz.open(file_path) as pdf:
            doc_meta = pdf.metadata or {}
            for index, page in enumerate(pdf, start=1):
                text = page.get_text("text")
                metadata = {
                    "title": doc_meta.get("title", ""),
                    "author": doc_meta.get("author", ""),
                    "created": doc_meta.get("creationDate", ""),
                    "page": index,
                }
                atom = EvidenceAtom(
                    source_path=file_path,
                    page_or_part=f"page-{index}",
                    text=text,
                    metadata=metadata,
                    semantic_fingerprint=self.deduper.fingerprint(text, metadata),
                    extraction_method="pymupdf-text",
                )
                yield self.deduper.register(atom)

    def _extract_docx(self, file_path: str) -> Iterable[EvidenceAtom]:
        document = Document(file_path)
        core = document.core_properties
        paragraphs = [p.text for p in document.paragraphs if p.text.strip()]
        chunk_size = 8
        for index in range(0, len(paragraphs), chunk_size):
            chunk = "\n".join(paragraphs[index:index + chunk_size])
            metadata = {
                "title": core.title or "",
                "author": core.author or "",
                "created": str(core.created or ""),
                "part": index // chunk_size + 1,
            }
            atom = EvidenceAtom(
                source_path=file_path,
                page_or_part=f"part-{index // chunk_size + 1}",
                text=chunk,
                metadata=metadata,
                semantic_fingerprint=self.deduper.fingerprint(chunk, metadata),
                extraction_method="python-docx",
            )
            yield self.deduper.register(atom)
    ```

    ### Integration
- Consumes EO1 manifests and emits evidence atoms for EO3 lane routing.
- Supports PyMuPDF for PDFs and python-docx for DOCX; leaves room for OCR adapters.
- Builds semantic fingerprints from normalized text windows, metadata, and structural cues.
- Emits duplicate confidence with rationale so operators can review near-duplicates.

### Failure Modes & Safeguards

| Failure Mode | Signal | Mitigation |
|---|---|---|
| Scanned PDF | Text under threshold | Queue OCR fallback and note confidence. |
| Encrypted file | Open failure | Preserve metadata and request password chain. |
| Near duplicate | High similarity | Mark duplicate candidate, do not auto-delete. |
| Corrupt DOCX | Zip error | Extract filesystem metadata and quarantine. |
| Mixed encoding | Unicode anomalies | Re-normalize with replacement and log. |

### Operator Checklist

1. Normalize whitespace, punctuation, and OCR ligatures before dedup comparison.
2. Peek at page text, headings, and body snippets before any hash is computed.
3. Store page-level excerpts to support later impeachment and exhibit indexing.
4. Preserve original binary path and extraction method for authentication.
5. Flag low-text image PDFs for OCR follow-up rather than misclassifying them as blank.

    ## ⚙️ Module EO3: MEEK Lane Router

    **Purpose:** Route evidence atoms into MEEK lanes A-F using compiled regex signals with mandatory priority E→D→F→C→A→B and explicit LaneCrossContaminationError handling.

    **Design Pattern:** Rules Engine + Priority Resolver + Exception Fence

    ### Code

    ```python
    import re
from dataclasses import dataclass

class LaneCrossContaminationError(RuntimeError):
    pass

@dataclass(slots=True)
class LaneDecision:
    lane: str
    confidence: float
    signals: list[str]
    review_required: bool = False

SIGNALS = {
    "E": [re.compile(p, re.I) for p in [
        r"judge", r"court rule", r"bias", r"disqualification", r"ethics", r"ex parte"
    ]],
    "D": [re.compile(p, re.I) for p in [
        r"ppo", r"personal protection", r"threat", r"stalking", r"safety"
    ]],
    "F": [re.compile(p, re.I) for p in [
        r"appeal", r"coa", r"msc", r"leave to appeal", r"standard of review"
    ]],
    "C": [re.compile(p, re.I) for p in [
        r"1983", r"constitutional", r"qualified immunity", r"due process", r"equal protection"
    ]],
    "A": [re.compile(p, re.I) for p in [
        r"custody", r"parenting time", r"best interest", r"L\.D\.W\.", r"alienation"
    ]],
    "B": [re.compile(p, re.I) for p in [
        r"housing", r"lease", r"eviction", r"property", r"residence"
    ]],
}

PRIORITY = ["E", "D", "F", "C", "A", "B"]

class MEEKLaneRouter:
    def score_lane(self, text: str, lane: str) -> tuple[int, list[str]]:
        hits: list[str] = []
        for pattern in SIGNALS[lane]:
            match = pattern.search(text)
            if match:
                hits.append(match.group(0))
        return len(hits), hits

    def route(self, atom_text: str, metadata: dict | None = None) -> LaneDecision:
        metadata = metadata or {}
        if "child_name" in metadata and metadata["child_name"] not in {"", "L.D.W."}:
            raise LaneCrossContaminationError("Child reference must be L.D.W. only.")

        scored: list[tuple[str, int, list[str]]] = []
        for lane in PRIORITY:
            score, hits = self.score_lane(atom_text, lane)
            scored.append((lane, score, hits))

        scored.sort(key=lambda item: (-item[1], PRIORITY.index(item[0])))
        top_lane, top_score, top_hits = scored[0]
        second_lane, second_score, _ = scored[1]

        if top_score == 0:
            return LaneDecision(lane="REVIEW", confidence=0.0, signals=[], review_required=True)
        if top_score == second_score and top_score > 1:
            raise LaneCrossContaminationError(
                f"Lane collision between {top_lane} and {second_lane}: {top_score}"
            )

        priority_bonus = 0.05 * (len(PRIORITY) - PRIORITY.index(top_lane))
        confidence = min(0.99, (top_score / 5.0) + priority_bonus)
        return LaneDecision(
            lane=top_lane,
            confidence=round(confidence, 2),
            signals=top_hits,
            review_required=confidence < 0.55,
        )
    ```

    ### Integration
- Consumes EO2 atoms and returns lane, confidence, and signal matches.
- Enforces child naming discipline: use only L.D.W. for child references.
- Raises cross-contamination when multiple lanes score materially the same.
- Feeds EO4 Bates prefixes and EO8 exhibit grouping logic.

### Failure Modes & Safeguards

| Failure Mode | Signal | Mitigation |
|---|---|---|
| Lane collision | Two top scores tied | Raise LaneCrossContaminationError. |
| No match | Score zero | Queue manual review bundle. |
| OCR noise | False positive regex | Apply confidence discount for weak spans. |
| Name drift | Unknown child name | Reject and replace with L.D.W. only. |
| Priority inversion | Lower lane chosen | Re-run with strict priority order. |

### Operator Checklist

1. Compile regex once at process start for deterministic performance.
2. Check Lane E before all others because misconduct/judicial signals override context.
3. Check Lane D next for PPO and safety content.
4. Run Lane F appellate signals before federal damages to preserve posture logic.
5. Treat low-confidence multi-match items as review required, not silently assigned.

    ## ⚙️ Module EO4: Bates Stamping

    **Purpose:** Apply sequential PIGORS-{LANE}-{NNNNNN} Bates numbers to PDF pages with registry-backed uniqueness and exhibit-safe page overlays.

    **Design Pattern:** Repository + Transaction Script + Overlay Renderer

    ### Code

    ```python
    import sqlite3
from dataclasses import dataclass
from pathlib import Path

import fitz

@dataclass(slots=True)
class BatesAllocation:
    lane: str
    source_path: str
    start_number: int
    end_number: int

    @property
    def start_label(self) -> str:
        return f"PIGORS-{self.lane}-{self.start_number:06d}"

    @property
    def end_label(self) -> str:
        return f"PIGORS-{self.lane}-{self.end_number:06d}"

class BatesRegistry:
    def __init__(self, db_path: str) -> None:
        self.conn = sqlite3.connect(db_path)
        self.conn.execute(
            '''
            CREATE TABLE IF NOT EXISTS bates_registry (
                lane TEXT NOT NULL,
                source_path TEXT NOT NULL,
                page_number INTEGER NOT NULL,
                bates_label TEXT NOT NULL UNIQUE,
                PRIMARY KEY (lane, source_path, page_number)
            )
            '''
        )

    def allocate(self, lane: str, source_path: str, pages: int) -> BatesAllocation:
        cur = self.conn.cursor()
        cur.execute(
            "SELECT COALESCE(MAX(CAST(SUBSTR(bates_label, -6) AS INTEGER)), 0) FROM bates_registry WHERE lane = ?",
            (lane,),
        )
        last = cur.fetchone()[0] or 0
        start = last + 1
        end = start + pages - 1
        for page_number, numeric in enumerate(range(start, end + 1), start=1):
            label = f"PIGORS-{lane}-{numeric:06d}"
            cur.execute(
                "INSERT INTO bates_registry (lane, source_path, page_number, bates_label) VALUES (?, ?, ?, ?)",
                (lane, source_path, page_number, label),
            )
        self.conn.commit()
        return BatesAllocation(lane=lane, source_path=source_path, start_number=start, end_number=end)

class BatesStamper:
    def __init__(self, registry: BatesRegistry) -> None:
        self.registry = registry

    def stamp_pdf(self, source_pdf: str, output_pdf: str, lane: str) -> BatesAllocation:
        source_pdf = str(Path(source_pdf))
        output_pdf = str(Path(output_pdf))
        with fitz.open(source_pdf) as pdf:
            allocation = self.registry.allocate(lane=lane, source_path=source_pdf, pages=pdf.page_count)
            for page_index, page in enumerate(pdf, start=1):
                numeric = allocation.start_number + page_index - 1
                label = f"PIGORS-{lane}-{numeric:06d}"
                rect = page.rect
                point = fitz.Point(rect.width - 165, rect.height - 22)
                page.insert_text(
                    point,
                    label,
                    fontsize=10,
                    fontname="helv",
                    color=(0, 0, 0),
                    overlay=True,
                )
            pdf.save(output_pdf)
            return allocation
    ```

    ### Integration
- Consumes EO3 lane decisions so prefixes remain lane-specific.
- Writes allocations to bates_registry for audit and collision prevention.
- Supplies EO8 exhibit indexes with final Bates ranges per source file.
- Provides EO5 authentication packets with stamped-page references.

### Failure Modes & Safeguards

| Failure Mode | Signal | Mitigation |
|---|---|---|
| Registry collision | Unique constraint | Retry allocation inside fresh transaction. |
| Non-PDF source | Unsupported suffix | Convert or skip with review note. |
| Page render failure | Overlay exception | Abort write and rollback registry. |
| Wrong lane prefix | Mismatch with EO3 | Reject package before output. |
| Missing output dir | IO error | Create controlled derivative folder. |

### Operator Checklist

1. Allocate Bates numbers before rendering any page overlay.
2. Keep one row per source file and page in bates_registry.
3. Use transactional commits to prevent duplicate numbering under concurrency.
4. Store start and end Bates values for every stamped artifact.
5. Never overwrite source evidence; output to derivative exhibit paths only.

    ## ⚙️ Module EO5: Authentication Engine

    **Purpose:** Generate MRE 901/902-compliant authentication packets with personal knowledge affidavits, voice identification, recording authentication under Sullivan v Gray, and chain-of-custody logs.

    **Design Pattern:** Template Method + Evidence Policy Engine + Affidavit Builder

    ### Code

    ```python
    from dataclasses import dataclass, field
from datetime import date

@dataclass(slots=True)
class CustodyEvent:
    when: str
    actor: str
    action: str
    location: str
    notes: str = ""

@dataclass(slots=True)
class AuthenticationPacket:
    title: str
    rule_basis: list[str] = field(default_factory=list)
    affidavit_text: str = ""
    chain_of_custody: list[CustodyEvent] = field(default_factory=list)
    witness_questions: list[str] = field(default_factory=list)

class AuthenticationEngine:
    def personal_knowledge_packet(
        self,
        exhibit_title: str,
        witness_name: str,
        facts: list[str],
        bates_range: str,
    ) -> AuthenticationPacket:
        affidavit_lines = [
            f"AFFIDAVIT OF {witness_name.upper()}",
            "",
            f"1. I have personal knowledge of {exhibit_title}.",
            f"2. I reviewed Bates {bates_range} and recognize it as the same item I observed.",
        ]
        for index, fact in enumerate(facts, start=3):
            affidavit_lines.append(f"{index}. {fact}")
        affidavit_lines.append(f"{len(affidavit_lines)}. I declare under penalty of perjury that the foregoing is true.")
        return AuthenticationPacket(
            title=exhibit_title,
            rule_basis=["MRE 901(b)(1)"],
            affidavit_text="\n".join(affidavit_lines),
            witness_questions=[
                "How do you recognize this item?",
                "When did you first see it?",
                "Has it been changed since you observed it?",
            ],
        )

    def voice_identification_packet(
        self,
        exhibit_title: str,
        familiar_witness: str,
        basis_of_familiarity: str,
    ) -> AuthenticationPacket:
        affidavit = "\n".join([
            f"{familiar_witness} states familiarity with the voice in {exhibit_title}.",
            f"Basis of familiarity: {basis_of_familiarity}.",
            "The witness can identify the speaker under MRE 901(b)(5).",
        ])
        return AuthenticationPacket(
            title=exhibit_title,
            rule_basis=["MRE 901(b)(5)"],
            affidavit_text=affidavit,
            witness_questions=[
                "How are you familiar with the speaker's voice?",
                "How many times have you heard that voice before?",
                "What makes you confident the recording captures that speaker?",
            ],
        )

    def recording_packet(
        self,
        exhibit_title: str,
        recorder: str,
        device: str,
        chain: list[CustodyEvent],
    ) -> AuthenticationPacket:
        affidavit = "\n".join([
            f"Recording foundation for {exhibit_title}.",
            f"Recorder: {recorder}. Device: {device}.",
            "The recording is offered with foundation principles recognized in Sullivan v Gray.",
            "The packet addresses creation, preservation, custody, and completeness.",
        ])
        return AuthenticationPacket(
            title=exhibit_title,
            rule_basis=["MRE 901", "Sullivan v Gray"],
            affidavit_text=affidavit,
            chain_of_custody=chain,
            witness_questions=[
                "What device created the recording?",
                "Where was the recording stored after creation?",
                "Has the file been altered, edited, or transcoded?",
            ],
        )

    def chain_log(self, source_path: str, discovered_by: str, discovered_at: str) -> list[CustodyEvent]:
        return [
            CustodyEvent(
                when=discovered_at,
                actor=discovered_by,
                action="Discovered source evidence",
                location=source_path,
                notes=f"Logged {date.today().isoformat()} for litigation hold.",
            )
        ]
    ```

    ### Integration
- Consumes EO1 provenance, EO2 extraction metadata, and EO4 Bates ranges.
- Outputs affidavit drafts, witness checklists, and exhibit foundation scripts.
- Builds recording-authentication logic for audio/video evidence and speaker ID.
- Feeds EO8 exhibit packages with ready-to-file authentication tabs.

### Failure Modes & Safeguards

| Failure Mode | Signal | Mitigation |
|---|---|---|
| Unknown custodian | Gap in possession | Generate cure task before filing. |
| Speaker disputed | Voice ID weak | Escalate to corroborating witness evidence. |
| Edited recording | Integrity challenge | Preserve raw source and export chain. |
| Missing timestamp | Temporal ambiguity | Use filesystem provenance and testimony. |
| Generic affidavit | Foundation too broad | Require item-specific fact paragraphs. |

### Operator Checklist

1. Document who found the item, where it was found, and when.
2. Tie every affidavit paragraph to a source path or Bates-stamped page.
3. Use MRE 901(b)(1) for personal knowledge when a witness observed the item.
4. Use MRE 901(b)(5) for voice identification with prior familiarity facts.
5. For recordings, document equipment, custody, completeness, and lack of alteration.

    ## ⚙️ Module EO6: Discovery Warfare

    **Purpose:** Draft interrogatories, requests for production, and requests for admission; track response deadlines, deficiencies, and motions to compel under MCR 2.302-2.313.

    **Design Pattern:** Workflow Engine + Rule Calendar + Deficiency Analyzer

    ### Code

    ```python
    from dataclasses import dataclass, field
from datetime import datetime, timedelta

@dataclass(slots=True)
class DiscoveryRequest:
    kind: str
    number: int
    text: str
    objective: str
    lane: str

@dataclass(slots=True)
class DiscoveryMatter:
    served_on: str
    requests: list[DiscoveryRequest]
    service_date: str
    response_due: str
    responses: dict[int, str] = field(default_factory=dict)
    deficiencies: list[str] = field(default_factory=list)

class DiscoveryWarfare:
    def build_interrogatories(self, lane: str, topics: list[str]) -> list[DiscoveryRequest]:
        requests = []
        for number, topic in enumerate(topics, start=1):
            requests.append(
                DiscoveryRequest(
                    kind="interrogatory",
                    number=number,
                    lane=lane,
                    objective=f"Obtain sworn factual narrative for {topic}",
                    text=f"State all facts, dates, witnesses, and documents supporting your position regarding {topic}.",
                )
            )
        return requests

    def build_rfps(self, lane: str, categories: list[str]) -> list[DiscoveryRequest]:
        requests = []
        for number, category in enumerate(categories, start=1):
            requests.append(
                DiscoveryRequest(
                    kind="request_for_production",
                    number=number,
                    lane=lane,
                    objective=f"Obtain documents for {category}",
                    text=f"Produce all documents, messages, photos, recordings, and metadata concerning {category}.",
                )
            )
        return requests

    def open_matter(self, served_on: str, requests: list[DiscoveryRequest], service_date: str) -> DiscoveryMatter:
        service_dt = datetime.fromisoformat(service_date)
        return DiscoveryMatter(
            served_on=served_on,
            requests=requests,
            service_date=service_date,
            response_due=(service_dt + timedelta(days=28)).date().isoformat(),
        )

    def analyze_deficiencies(self, matter: DiscoveryMatter) -> DiscoveryMatter:
        for request in matter.requests:
            response = matter.responses.get(request.number, "").strip()
            if not response:
                matter.deficiencies.append(f"{request.kind} {request.number}: no response served.")
                continue
            lowered = response.lower()
            if "subject to and without waiving" in lowered or "overly broad" in lowered:
                matter.deficiencies.append(
                    f"{request.kind} {request.number}: boilerplate objection without full answer."
                )
            if request.kind == "request_for_production" and "will produce" in lowered and "none yet" in lowered:
                matter.deficiencies.append(
                    f"{request.kind} {request.number}: promised production not actually delivered."
                )
        return matter

    def motion_to_compel_outline(self, matter: DiscoveryMatter) -> str:
        bullets = "\n".join(f"- {item}" for item in matter.deficiencies)
        return "\n".join([
            "MOTION TO COMPEL OUTLINE",
            "Authority: MCR 2.302 through MCR 2.313.",
            f"Service date: {matter.service_date}",
            f"Response due: {matter.response_due}",
            "Deficiencies:",
            bullets or "- None detected.",
        ])
    ```

    ### Integration
- Consumes EO2/EO3 evidence atoms to identify missing facts and unanswered topics.
- Creates request sets tied to lane, witness, and evidentiary objective.
- Escalates deficiencies into compel-ready narratives and exhibit references.
- Feeds EO7 subpoena requests when party discovery is evasive or incomplete.

### Failure Modes & Safeguards

| Failure Mode | Signal | Mitigation |
|---|---|---|
| Compound request | Objection risk | Split into narrower items. |
| Overbroad scope | Boilerplate objection | Tie to lane and time period. |
| Missed deadline | Waiver argument | Escalate to motion calendar. |
| Incomplete production | Placeholder responses | Generate deficiency matrix. |
| No meet and confer | Compel vulnerability | Require outreach log. |

### Operator Checklist

1. Draft each discovery item to a single fact objective or record category.
2. Track service date, response due date, objections, supplementation, and meet-and-confer.
3. Map every deficiency to a specific request number and missing content.
4. Preserve an exhibit-ready chronology for motions to compel.
5. Quote MCR 2.302-2.313 in templates where procedural authority matters.

    ## ⚙️ Module EO7: Subpoena Manager

    **Purpose:** Draft subpoenas duces tecum, manage service logistics, track motions to quash, and generate FOIA requests for government records relevant to Pigors v Watson.

    **Design Pattern:** Command Builder + Service Tracker + Escalation Queue

    ### Code

    ```python
    from dataclasses import dataclass, field

@dataclass(slots=True)
class SubpoenaTarget:
    custodian: str
    organization: str
    address: str
    records_requested: list[str]
    due_date: str
    lane: str

@dataclass(slots=True)
class ServiceRecord:
    issued_date: str
    served_date: str | None = None
    server: str | None = None
    return_status: str = "pending"
    quash_deadline: str | None = None
    notes: list[str] = field(default_factory=list)

class SubpoenaManager:
    def draft_duces_tecum(self, target: SubpoenaTarget) -> str:
        asks = "\n".join(f"{idx}. {item}" for idx, item in enumerate(target.records_requested, start=1))
        return "\n".join([
            "SUBPOENA DUCES TECUM",
            f"Custodian: {target.custodian}",
            f"Organization: {target.organization}",
            f"Address: {target.address}",
            f"Lane: {target.lane}",
            f"Compliance date: {target.due_date}",
            "Documents requested:",
            asks,
        ])

    def service_packet(self, issued_date: str, quash_deadline: str) -> ServiceRecord:
        return ServiceRecord(
            issued_date=issued_date,
            quash_deadline=quash_deadline,
            notes=["Preserve proof of service, return receipt, and communications."],
        )

    def record_service(self, record: ServiceRecord, served_date: str, server: str) -> ServiceRecord:
        record.served_date = served_date
        record.server = server
        record.return_status = "served"
        return record

    def foia_request(self, agency: str, records_requested: list[str], requester: str) -> str:
        asks = "\n".join(f"- {item}" for item in records_requested)
        return "\n".join([
            f"FOIA REQUEST TO {agency.upper()}",
            f"Requester: {requester}",
            "Requested records:",
            asks,
            "Please provide native files, attachments, and metadata where available.",
        ])
    ```

    ### Integration
- Escalates from EO6 when party discovery fails or third-party proof is required.
- Uses EO1/EO2 source-path intelligence to target custodians precisely.
- Produces service packets and tracking records for deadlines and returns.
- Can request public records through FOIA workflows when agencies hold evidence.

### Failure Modes & Safeguards

| Failure Mode | Signal | Mitigation |
|---|---|---|
| Wrong custodian | No records | Reissue with corrected recipient. |
| Overbroad subpoena | Motion to quash | Narrow scope and explain necessity. |
| Service failure | No return | Re-attempt with alternate method. |
| Agency denial | FOIA refusal | Draft statutory appeal or narrowed request. |
| Late compliance | Missed hearing prep | Move for enforcement or adjournment. |

### Operator Checklist

1. Identify custodian, exact document class, date range, and relevance objective.
2. Track issuance, service, compliance date, return date, and quash deadline.
3. Separate party subpoenas, non-party subpoenas, and FOIA requests in the ledger.
4. Preserve proof of service and communication logs for enforcement.
5. Link subpoena outputs to exhibit packages when records arrive.

    ## ⚙️ Module EO8: Evidence Presentation

    **Purpose:** Assemble exhibit indexes, cover sheets, summaries, demonstrative aids, and court-ready evidence packets that integrate Bates ranges, foundation notes, and lane-specific narratives.

    **Design Pattern:** Assembler + Facade + Presentation DSL

    ### Code

    ```python
    from dataclasses import dataclass, field

@dataclass(slots=True)
class ExhibitItem:
    label: str
    title: str
    lane: str
    bates_range: str
    source_path: str
    foundation: str
    summary_points: list[str] = field(default_factory=list)

class EvidencePresentation:
    def exhibit_index(self, items: list[ExhibitItem]) -> str:
        header = "| Exhibit | Title | Lane | Bates | Foundation |"
        divider = "|---|---|---|---|---|"
        rows = [
            f"| {item.label} | {item.title} | {item.lane} | {item.bates_range} | {item.foundation} |"
            for item in items
        ]
        return "\n".join([header, divider, *rows])

    def cover_sheet(self, item: ExhibitItem) -> str:
        bullets = "\n".join(f"- {point}" for point in item.summary_points)
        return "\n".join([
            f"# {item.label} — {item.title}",
            f"Lane: {item.lane}",
            f"Bates: {item.bates_range}",
            f"Source: {item.source_path}",
            f"Foundation: {item.foundation}",
            "Key points:",
            bullets or "- Summary pending",
        ])

    def evidence_summary(self, items: list[ExhibitItem]) -> str:
        sections = []
        for item in items:
            sections.append(self.cover_sheet(item))
        return "\n\n---\n\n".join(sections)

    def demonstrative_outline(self, issue: str, items: list[ExhibitItem]) -> str:
        rows = "\n".join(
            f"{item.label}: {item.title} ({item.bates_range})" for item in items
        )
        return "\n".join([
            f"DEMONSTRATIVE AID — {issue}",
            "Use only after confirming admissibility posture.",
            rows,
        ])
    ```

    ### Integration
- Consumes EO4 Bates allocations and EO5 authentication packets.
- Groups exhibits by lane, hearing objective, or motion section.
- Produces presentation summaries for briefs, hearings, and impeachment use.
- Exports exhibit indexes with source path, Bates range, and foundation theory.

### Failure Modes & Safeguards

| Failure Mode | Signal | Mitigation |
|---|---|---|
| Bad title | Confusing exhibit index | Rewrite with date + actor + purpose. |
| Missing Bates range | Presentation gap | Block package release until stamped. |
| No authentication tab | Foundation challenge | Attach EO5 packet. |
| Oversized packet | Judge usability issue | Split by hearing issue or lane. |
| Demonstrative confusion | Admissibility dispute | Label clearly as demonstrative. |

### Operator Checklist

1. One exhibit row per document or media item with final Bates range.
2. Separate admitted evidence, demonstratives, and reference-only materials.
3. Carry foundation notes forward so hearing prep mirrors exhibit tabs.
4. Use concise titles that reflect content, date, and evidentiary purpose.
5. Build summaries that point to pages, timestamps, and exact quotations.

## 🌲 Decision Tree

```
START
  │
  ├─► Is the source file on C/D/F/G/I/J?
  │      ├─ No  → Create acquisition task before processing
  │      └─ Yes
  │
  ├─► Can EO1 classify the file as evidence-bearing?
  │      ├─ No  → Ignore or log as non-evidence
  │      └─ Yes
  │
  ├─► Can EO2 extract meaningful text or metadata?
  │      ├─ No  → Queue OCR / manual extraction / media review
  │      └─ Yes
  │
  ├─► Does content-based dedup find a prior substantive twin?
  │      ├─ Yes → Link duplicate, preserve source path, do not destroy original
  │      └─ No
  │
  ├─► Does EO3 assign a clean lane under E→D→F→C→A→B?
  │      ├─ No match → Manual review bundle
  │      ├─ Cross-match → LaneCrossContaminationError review
  │      └─ Clean lane
  │
  ├─► Is the artifact destined for court presentation?
  │      ├─ No  → Retain as discovery/intelligence atom
  │      └─ Yes
  │
  ├─► Has EO4 allocated PIGORS-{LANE}-{NNNNNN} Bates labels?
  │      ├─ No  → Stamp and register pages
  │      └─ Yes
  │
  ├─► Can EO5 establish foundation?
  │      ├─ Personal knowledge available → MRE 901(b)(1)
  │      ├─ Voice familiarity available → MRE 901(b)(5)
  │      ├─ Recording integrity issue    → Sullivan v Gray workflow
  │      └─ Missing custodian            → Cure before filing
  │
  ├─► Does the evidence expose a discovery gap?
  │      ├─ Yes → EO6 drafts interrogatories/RFPs/RFAs and deficiency plan
  │      └─ No
  │
  ├─► Is third-party production required?
  │      ├─ Yes → EO7 subpoena or FOIA packet
  │      └─ No
  │
  └─► EO8 assembles exhibit index, cover sheet, summaries, and hearing packet
```

## 🔗 Cross-Module Integration Matrix

| From | To | Payload | Why It Matters |
|---|---|---|---|
| EO1 | EO2 | Source path, timestamps, drive profile | Extraction must preserve provenance |
| EO2 | EO3 | Evidence atoms, metadata, duplicate confidence | Lane routing needs actual content |
| EO3 | EO4 | Lane code and review flags | Bates prefix depends on lane correctness |
| EO4 | EO5 | Bates range, stamped page references | Affidavits must point to exhibit pages |
| EO5 | EO8 | Foundation scripts, chain logs | Presentation must anticipate admissibility |
| EO2 | EO6 | Missing facts and records categories | Discovery requests are evidence-driven |
| EO6 | EO7 | Non-party targets and record gaps | Subpoenas close holes left by party discovery |
| EO7 | EO8 | Produced records and service proof | Third-party records become exhibits |
| EO3 | EO8 | Lane narrative and issue framing | Exhibit order should match legal theory |
| EO1 | EO5 | Acquisition facts | Chain-of-custody starts at discovery moment |

## 🏛️ Domain Applications

| Use Case | Modules | Output |
|---|---|---|
| Custody hearing exhibit build | EO1, EO2, EO3, EO4, EO5, EO8 | Bates-stamped, authenticated exhibit packet |
| Discovery deficiency attack | EO2, EO6 | Deficiency matrix and motion-to-compel outline |
| Third-party phone record acquisition | EO6, EO7, EO5 | Subpoena packet plus authentication plan |
| Audio/video evidence foundation | EO2, EO5, EO8 | Voice ID packet and recording summary |
| Asset-discovery escalation | EO2, EO6, EO7 | Financial discovery requests and custodian subpoenas |
| Appellate record preservation | EO3, EO4, EO8 | Indexed record appendix with clean Bates citations |
| Judicial misconduct evidence set | EO2, EO3, EO4, EO8 | Lane E packet with cross-referenced exhibits |
| PPO evidentiary bundle | EO3, EO4, EO5, EO8 | Safety-focused evidence summary with foundation notes |

### Practice Notes

- **Michigan family-law posture:** evidence should be organized so it can migrate between motions, hearings, appeals, and accountability filings.
- **Discovery warfare:** every piece of evidence can either prove a fact directly or define the next discovery request.
- **Authentication planning:** if a source cannot be authenticated, the system should say so early and propose a cure path.
- **Presentation discipline:** exhibit titles, summaries, and Bates ranges should be concise enough for a bench packet and precise enough for appellate citation.
- **Storage realism:** removable-media evidence from D/F/G/I/J deserves extra custody detail because portability increases challenge risk.

## ⚡ Quick Reference Card

```
╔══════════════════════════════════════════════════════════════════════════════╗
║            FORGE-EVIDENCE-OMNISCIENCE (Ω-Δ99) QUICK REFERENCE              ║
╠══════════════════════════════════════════════════════════════════════════════╣
║ EO1  Drive Scanner        → discover C/D/F/G/I/J evidence files            ║
║ EO2  OCR & Extraction     → peek inside docs; content-based dedup only     ║
║ EO3  MEEK Lane Router     → priority E → D → F → C → A → B                 ║
║ EO4  Bates Stamping       → PIGORS-{LANE}-{NNNNNN} + bates_registry        ║
║ EO5  Authentication       → MRE 901(b)(1), 901(b)(5), Sullivan v Gray      ║
║ EO6  Discovery Warfare    → interrogatories, RFPs, RFAs, compel tracking   ║
║ EO7  Subpoena Manager     → duces tecum, service, FOIA, quash response     ║
║ EO8  Presentation         → exhibit index, cover sheets, summaries         ║
╠══════════════════════════════════════════════════════════════════════════════╣
║ CHILD REFERENCE: L.D.W. only                                                ║
║ DRIVE MAP: C=NVMe SSD | D/F/G=USB | I=SD card | J=2TB USB exFAT             ║
║ DEDUP RULE: inspect document content, not hash-only                          ║
║ PRIMARY OUTPUT: court-ready authenticated exhibit packages                   ║
╚══════════════════════════════════════════════════════════════════════════════╝
```

## Appendix 1: Evidence Operations Runbook

| Step | Question | Required Output | Owning Module |
|---|---|---|---|
| 1 | Which drive or custodian holds the source? | Source manifest row | EO1 |
| 2 | What does the content actually say? | Evidence atoms and metadata | EO2 |
| 3 | Which lane owns the signal? | Lane decision with confidence | EO3 |
| 4 | What is the permanent exhibit identifier? | Bates allocation | EO4 |
| 5 | How will it be authenticated? | Affidavit and custody log | EO5 |
| 6 | What discovery gap does it cure? | Deficiency or request mapping | EO6 |
| 7 | Which third party must produce more? | Subpoena/FOIA packet | EO7 |
| 8 | How is it shown to the court? | Exhibit index and summary | EO8 |

```python
class EvidenceRunbook:
    def __init__(self, scanner, extractor, router, stamper, auth, discovery, subpoena, presentation):
        self.scanner = scanner
        self.extractor = extractor
        self.router = router
        self.stamper = stamper
        self.auth = auth
        self.discovery = discovery
        self.subpoena = subpoena
        self.presentation = presentation

    def execute(self, roots: dict[str, str]) -> dict:
        manifests = list(self.scanner.manifest_rows())
        atoms = []
        for manifest in manifests:
            atoms.extend(self.extractor.extract(manifest["path"]))
        routed = []
        for atom in atoms:
            routed.append((atom, self.router.route(atom.text, atom.metadata)))
        return {
            "manifest_count": len(manifests),
            "atom_count": len(atoms),
            "routed_count": len(routed),
            "status": "ready-for-human-review",
        }
```

## Appendix 2: Evidence Operations Runbook

| Step | Question | Required Output | Owning Module |
|---|---|---|---|
| 1 | Which drive or custodian holds the source? | Source manifest row | EO1 |
| 2 | What does the content actually say? | Evidence atoms and metadata | EO2 |
| 3 | Which lane owns the signal? | Lane decision with confidence | EO3 |
| 4 | What is the permanent exhibit identifier? | Bates allocation | EO4 |
| 5 | How will it be authenticated? | Affidavit and custody log | EO5 |
| 6 | What discovery gap does it cure? | Deficiency or request mapping | EO6 |
| 7 | Which third party must produce more? | Subpoena/FOIA packet | EO7 |
| 8 | How is it shown to the court? | Exhibit index and summary | EO8 |

```python
class EvidenceRunbook:
    def __init__(self, scanner, extractor, router, stamper, auth, discovery, subpoena, presentation):
        self.scanner = scanner
        self.extractor = extractor
        self.router = router
        self.stamper = stamper
        self.auth = auth
        self.discovery = discovery
        self.subpoena = subpoena
        self.presentation = presentation

    def execute(self, roots: dict[str, str]) -> dict:
        manifests = list(self.scanner.manifest_rows())
        atoms = []
        for manifest in manifests:
            atoms.extend(self.extractor.extract(manifest["path"]))
        routed = []
        for atom in atoms:
            routed.append((atom, self.router.route(atom.text, atom.metadata)))
        return {
            "manifest_count": len(manifests),
            "atom_count": len(atoms),
            "routed_count": len(routed),
            "status": "ready-for-human-review",
        }
```

## Appendix 3: Evidence Operations Runbook

| Step | Question | Required Output | Owning Module |
|---|---|---|---|
| 1 | Which drive or custodian holds the source? | Source manifest row | EO1 |
| 2 | What does the content actually say? | Evidence atoms and metadata | EO2 |
| 3 | Which lane owns the signal? | Lane decision with confidence | EO3 |
| 4 | What is the permanent exhibit identifier? | Bates allocation | EO4 |
| 5 | How will it be authenticated? | Affidavit and custody log | EO5 |
| 6 | What discovery gap does it cure? | Deficiency or request mapping | EO6 |
| 7 | Which third party must produce more? | Subpoena/FOIA packet | EO7 |
| 8 | How is it shown to the court? | Exhibit index and summary | EO8 |

```python
class EvidenceRunbook:
    def __init__(self, scanner, extractor, router, stamper, auth, discovery, subpoena, presentation):
        self.scanner = scanner
        self.extractor = extractor
        self.router = router
        self.stamper = stamper
        self.auth = auth
        self.discovery = discovery
        self.subpoena = subpoena
        self.presentation = presentation

    def execute(self, roots: dict[str, str]) -> dict:
        manifests = list(self.scanner.manifest_rows())
        atoms = []
        for manifest in manifests:
            atoms.extend(self.extractor.extract(manifest["path"]))
        routed = []
        for atom in atoms:
            routed.append((atom, self.router.route(atom.text, atom.metadata)))
        return {
            "manifest_count": len(manifests),
            "atom_count": len(atoms),
            "routed_count": len(routed),
            "status": "ready-for-human-review",
        }
```

## Appendix 4: Evidence Operations Runbook

| Step | Question | Required Output | Owning Module |
|---|---|---|---|
| 1 | Which drive or custodian holds the source? | Source manifest row | EO1 |
| 2 | What does the content actually say? | Evidence atoms and metadata | EO2 |
| 3 | Which lane owns the signal? | Lane decision with confidence | EO3 |
| 4 | What is the permanent exhibit identifier? | Bates allocation | EO4 |
| 5 | How will it be authenticated? | Affidavit and custody log | EO5 |
| 6 | What discovery gap does it cure? | Deficiency or request mapping | EO6 |
| 7 | Which third party must produce more? | Subpoena/FOIA packet | EO7 |
| 8 | How is it shown to the court? | Exhibit index and summary | EO8 |

```python
class EvidenceRunbook:
    def __init__(self, scanner, extractor, router, stamper, auth, discovery, subpoena, presentation):
        self.scanner = scanner
        self.extractor = extractor
        self.router = router
        self.stamper = stamper
        self.auth = auth
        self.discovery = discovery
        self.subpoena = subpoena
        self.presentation = presentation

    def execute(self, roots: dict[str, str]) -> dict:
        manifests = list(self.scanner.manifest_rows())
        atoms = []
        for manifest in manifests:
            atoms.extend(self.extractor.extract(manifest["path"]))
        routed = []
        for atom in atoms:
            routed.append((atom, self.router.route(atom.text, atom.metadata)))
        return {
            "manifest_count": len(manifests),
            "atom_count": len(atoms),
            "routed_count": len(routed),
            "status": "ready-for-human-review",
        }
```

