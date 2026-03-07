"""
ORG-relationships: RelationshipLinker Agent
Links evidence→filings, orders→hearings, detects supersession chains (v1→v2→v3).
Uses case_number + date proximity + keyword matching. Cross-references across lanes.
"""
import sys
import re
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))
from __init__ import (
    content_preview, index_db, state_db, log_audit, LITIGOS_ROOT,
)

BATCH_SIZE = 200

# Relationship detection patterns
SUPERSESSION_PATTERN = re.compile(
    r"(?i)(amended|revised|updated|v\d|version\s*\d|_v\d|corrected|final|draft)"
)
RESPONSE_PATTERN = re.compile(
    r"(?i)(response|reply|opposition|answer|rebuttal|objection)\s+(to|regarding)"
)
EXHIBIT_PATTERN = re.compile(
    r"(?i)(exhibit\s+[a-z0-9]+|attached\s+(hereto|herewith)|see\s+attached)"
)
CITATION_PATTERN = re.compile(
    r"(?i)(MCL\s+\d+\.\d+|MCR\s+\d+\.\d+|USC\s+§\s*\d+|\d+\s+Mich\s+\d+|\d+\s+NW2d\s+\d+)"
)


class RelationshipLinker:
    """Build relationship graph between indexed files."""

    def __init__(self, batch_size=BATCH_SIZE):
        self.batch_size = batch_size
        self.stats = {
            "links_created": 0, "supersession_chains": 0,
            "cross_lane_links": 0, "errors": 0,
        }

    def run(self):
        """Run all relationship detection passes."""
        sys.stdout = open(sys.stdout.fileno(), mode="w", encoding="utf-8", errors="replace")
        print(f"\n{'='*60}")
        print(f"  RELATIONSHIP LINKER — Building File Graph")
        print(f"{'='*60}\n")

        self._detect_supersession()
        self._detect_case_links()
        self._detect_response_chains()
        self._detect_exhibit_links()

        print(f"\n{'='*60}")
        print(f"  RELATIONSHIP LINKING COMPLETE")
        for k, v in self.stats.items():
            print(f"    {k:20s} = {v}")
        print(f"{'='*60}")
        return self.stats

    def _detect_supersession(self):
        """Find v1→v2→v3 chains of the same document."""
        print("  ── Supersession Detection ──\n")

        with index_db() as conn:
            # Group files by base name (strip version suffixes)
            files = conn.execute(
                """SELECT id, path, filename, extension, doc_type, case_lane, case_number 
                   FROM files WHERE status IN ('classified', 'indexed') 
                   ORDER BY filename""",
            ).fetchall()

            # Build groups by normalized name
            groups = {}
            for f in files:
                fname = dict(f)
                base = self._normalize_name(fname["filename"])
                key = (base, fname["extension"], fname.get("case_lane"))
                if key not in groups:
                    groups[key] = []
                groups[key].append(fname)

            chains_found = 0
            for key, group in groups.items():
                if len(group) < 2:
                    continue

                # Sort by version indicator or filename
                group.sort(key=lambda x: self._version_sort_key(x["filename"]))

                # Create supersession chain
                for i in range(len(group) - 1):
                    older = group[i]
                    newer = group[i + 1]
                    conn.execute(
                        "INSERT OR REPLACE INTO file_links (source_id, target_id, link_type, confidence) VALUES (?, ?, ?, ?)",
                        (newer["id"], older["id"], "supersedes", 0.8),
                    )
                    self.stats["links_created"] += 1

                chains_found += 1
                if chains_found <= 20:
                    names = " → ".join(g["filename"][:30] for g in group)
                    print(f"  📝 Chain: {names}")

            self.stats["supersession_chains"] = chains_found
            conn.commit()
            print(f"\n  Found {chains_found} supersession chains\n")

    def _detect_case_links(self):
        """Link files that share case numbers."""
        print("  ── Case Number Links ──\n")

        with index_db() as conn:
            case_files = conn.execute(
                """SELECT id, filename, case_number, doc_type, case_lane 
                   FROM files WHERE case_number IS NOT NULL 
                   ORDER BY case_number, doc_type""",
            ).fetchall()

            case_groups = {}
            for f in case_files:
                fd = dict(f)
                cn = fd["case_number"]
                if cn not in case_groups:
                    case_groups[cn] = []
                case_groups[cn].append(fd)

            links = 0
            for case_num, group in case_groups.items():
                if len(group) < 2:
                    continue

                # Link filings to evidence within same case
                filings = [f for f in group if f["doc_type"] in ("motion", "brief", "complaint", "affidavit")]
                evidence = [f for f in group if f["doc_type"] in ("exhibit", "photo", "financial", "correspondence", "transcript")]

                for filing in filings:
                    for ev in evidence:
                        conn.execute(
                            "INSERT OR REPLACE INTO file_links (source_id, target_id, link_type, confidence) VALUES (?, ?, ?, ?)",
                            (filing["id"], ev["id"], "supports", 0.7),
                        )
                        links += 1

                # Cross-lane detection
                lanes = set(f["case_lane"] for f in group if f["case_lane"])
                if len(lanes) > 1:
                    self.stats["cross_lane_links"] += 1

            self.stats["links_created"] += links
            conn.commit()
            print(f"  Created {links} case-based links across {len(case_groups)} cases\n")

    def _detect_response_chains(self):
        """Detect motion→response→reply chains."""
        print("  ── Response Chain Detection ──\n")

        with index_db() as conn:
            motions = conn.execute(
                "SELECT id, filename, case_number FROM files WHERE doc_type = 'motion' AND case_number IS NOT NULL",
            ).fetchall()
            responses = conn.execute(
                "SELECT id, filename, case_number, content_preview FROM files WHERE doc_type IN ('brief', 'unknown') AND content_preview IS NOT NULL",
            ).fetchall()

            links = 0
            for motion in motions:
                md = dict(motion)
                for resp in responses:
                    rd = dict(resp)
                    if md["case_number"] != rd.get("case_number"):
                        continue
                    if RESPONSE_PATTERN.search(rd.get("content_preview", "") or ""):
                        conn.execute(
                            "INSERT OR REPLACE INTO file_links (source_id, target_id, link_type, confidence) VALUES (?, ?, ?, ?)",
                            (rd["id"], md["id"], "responds_to", 0.6),
                        )
                        links += 1

            self.stats["links_created"] += links
            conn.commit()
            print(f"  Found {links} response chain links\n")

    def _detect_exhibit_links(self):
        """Link exhibit cover pages to their attachments."""
        print("  ── Exhibit Link Detection ──\n")

        with index_db() as conn:
            exhibits = conn.execute(
                """SELECT id, filename, case_lane FROM files 
                   WHERE filename LIKE '%Exhibit%' OR filename LIKE '%exhibit%'
                   ORDER BY filename""",
            ).fetchall()

            links = 0
            exhibit_list = [dict(e) for e in exhibits]
            for i, ex in enumerate(exhibit_list):
                # Link sequential exhibits (Exhibit_A → Exhibit_B etc.)
                for j in range(i + 1, min(i + 5, len(exhibit_list))):
                    if exhibit_list[j]["case_lane"] == ex["case_lane"]:
                        conn.execute(
                            "INSERT OR REPLACE INTO file_links (source_id, target_id, link_type, confidence) VALUES (?, ?, ?, ?)",
                            (ex["id"], exhibit_list[j]["id"], "exhibits", 0.5),
                        )
                        links += 1

            self.stats["links_created"] += links
            conn.commit()
            print(f"  Found {links} exhibit links\n")

    @staticmethod
    def _normalize_name(filename):
        """Strip version indicators and suffixes to get base document name."""
        name = Path(filename).stem
        name = re.sub(r"[\s_]*(v\d+|_\d+|draft|final|revised|amended|corrected|\(\d+\)|copy)", "", name, flags=re.IGNORECASE)
        name = re.sub(r"_+", "_", name).strip("_").lower()
        return name

    @staticmethod
    def _version_sort_key(filename):
        """Extract a sortable version key from filename."""
        match = re.search(r"v(\d+)", filename, re.IGNORECASE)
        if match:
            return int(match.group(1))
        match = re.search(r"\((\d+)\)", filename)
        if match:
            return int(match.group(1))
        if re.search(r"(?i)final", filename):
            return 999
        if re.search(r"(?i)draft", filename):
            return 0
        return 1


def main():
    import argparse
    parser = argparse.ArgumentParser(description="RelationshipLinker: Build file relationship graph")
    parser.add_argument("--batch-size", type=int, default=BATCH_SIZE)
    args = parser.parse_args()

    linker = RelationshipLinker(batch_size=args.batch_size)
    stats = linker.run()

    with state_db() as conn:
        log_audit(conn, "relationship_run", "INDEX.db",
                  f"links={stats['links_created']}, chains={stats['supersession_chains']}, cross_lane={stats['cross_lane_links']}",
                  "ORG-relationships", "omega-v5.0")


if __name__ == "__main__":
    main()
