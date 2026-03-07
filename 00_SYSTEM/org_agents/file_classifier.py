"""
ORG-classifier: FileClassifier Agent
Pulls unclassified files from INDEX.db and assigns lane, doc_type, parties, tags
using MANBEARPIG (local TF-IDF + Naive Bayes + MEEK signals). Batch: 100 files/cycle.
Flags low-confidence items (< 0.6) for human review.
"""
import sys
import re
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))
from __init__ import (
    content_preview, detect_lane, detect_doc_type,
    index_db, state_db, log_audit, LITIGOS_ROOT,
)

BATCH_SIZE = 100


class FileClassifier:
    """AI-classify indexed files that haven't been classified yet."""

    def __init__(self, batch_size=BATCH_SIZE):
        self.batch_size = batch_size
        self.stats = {"classified": 0, "low_confidence": 0, "errors": 0, "skipped": 0}
        self._manbearpig = None

    @property
    def manbearpig(self):
        """Lazy-load MANBEARPIG inference engine."""
        if self._manbearpig is None:
            try:
                sys.path.insert(0, str(LITIGOS_ROOT / "00_SYSTEM" / "local_model"))
                from inference_engine import MichiganLegalModel
                self._manbearpig = MichiganLegalModel()
                print("  ✅ MANBEARPIG loaded for classification")
            except Exception as e:
                print(f"  ⚠️ MANBEARPIG unavailable, using regex fallback: {e}")
        return self._manbearpig

    def _classify_with_manbearpig(self, text, filename):
        """Classify using MANBEARPIG if available, fall back to regex."""
        result = {
            "lane": None, "doc_type": "unknown", "confidence": 0.0,
            "parties": [], "tags": [], "case_number": None,
        }

        if self.manbearpig and text:
            try:
                intent, conf = self.manbearpig.classify_intent(text[:2000])
                result["doc_type"] = intent if conf > 0.3 else detect_doc_type(text, filename)
                result["confidence"] = conf

                entities = self.manbearpig.extract_entities(text[:2000])
                result["parties"] = entities.get("persons", [])[:10]
                result["case_number"] = entities.get("case_numbers", [None])[0] if entities.get("case_numbers") else None
                result["tags"] = entities.get("statutes", [])[:10]
            except Exception:
                pass

        # MEEK lane detection always runs (more reliable for lanes)
        result["lane"] = detect_lane(text) if text else None

        # Regex fallback for doc_type if MANBEARPIG didn't classify
        if result["doc_type"] == "unknown" and text:
            result["doc_type"] = detect_doc_type(text, filename)
            result["confidence"] = max(result["confidence"], 0.5)

        # Extract case numbers from text via regex
        if not result["case_number"] and text:
            case_match = re.search(r"(\d{4}-\d{5,6}-[A-Z]{2})", text)
            if case_match:
                result["case_number"] = case_match.group(1)

        return result

    def classify_batch(self):
        """Pull and classify a batch of unclassified files."""
        sys.stdout = open(sys.stdout.fileno(), mode="w", encoding="utf-8", errors="replace")
        print(f"\n{'='*60}")
        print(f"  FILE CLASSIFIER — Batch Size: {self.batch_size}")
        print(f"{'='*60}\n")

        with index_db() as conn:
            # Get unclassified files
            rows = conn.execute(
                """SELECT id, path, filename, extension, content_preview 
                   FROM files WHERE status = 'indexed' 
                   ORDER BY size_bytes DESC LIMIT ?""",
                (self.batch_size,),
            ).fetchall()

            if not rows:
                print("  No unclassified files found.")
                return self.stats

            print(f"  Processing {len(rows)} unclassified files...\n")

            for i, row in enumerate(rows):
                try:
                    file_id = row["id"]
                    filepath = row["path"]
                    filename = row["filename"]
                    preview = row["content_preview"] or ""

                    # Get more content if preview is empty/short
                    if len(preview) < 100 and Path(filepath).exists():
                        preview = content_preview(filepath, 1000) or preview

                    classification = self._classify_with_manbearpig(preview, filename)

                    conn.execute(
                        """UPDATE files SET 
                           case_lane = ?, case_number = ?, doc_type = ?,
                           parties = ?, tags = ?, classifier_confidence = ?,
                           status = ?, classified_at = ?
                           WHERE id = ?""",
                        (
                            classification["lane"],
                            classification["case_number"],
                            classification["doc_type"],
                            str(classification["parties"]) if classification["parties"] else None,
                            str(classification["tags"]) if classification["tags"] else None,
                            classification["confidence"],
                            "classified" if classification["confidence"] >= 0.6 else "review",
                            datetime.now().isoformat(),
                            file_id,
                        ),
                    )

                    # Multi-lane assignment
                    if classification["lane"]:
                        conn.execute(
                            "INSERT OR REPLACE INTO file_lanes (file_id, case_lane, case_number, relevance_score) VALUES (?, ?, ?, ?)",
                            (file_id, classification["lane"], classification["case_number"], classification["confidence"]),
                        )

                    status = "✅" if classification["confidence"] >= 0.6 else "⚠️"
                    if classification["confidence"] < 0.6:
                        self.stats["low_confidence"] += 1

                    print(f"  [{i+1}/{len(rows)}] {status} {filename[:40]:40s} → lane={classification['lane']} type={classification['doc_type']} conf={classification['confidence']:.2f}")
                    self.stats["classified"] += 1

                except Exception as e:
                    print(f"  [{i+1}/{len(rows)}] ❌ {filename[:40]}: {e}")
                    self.stats["errors"] += 1

                if (i + 1) % 50 == 0:
                    conn.commit()

            conn.commit()

        print(f"\n{'='*60}")
        print(f"  CLASSIFICATION COMPLETE")
        for k, v in self.stats.items():
            print(f"    {k:20s} = {v}")
        print(f"{'='*60}")
        return self.stats


def main():
    import argparse
    parser = argparse.ArgumentParser(description="FileClassifier: AI-classify indexed files")
    parser.add_argument("--batch-size", type=int, default=BATCH_SIZE, help="Files per batch")
    args = parser.parse_args()

    classifier = FileClassifier(batch_size=args.batch_size)
    stats = classifier.classify_batch()

    with state_db() as conn:
        log_audit(conn, "classify_run", "INDEX.db",
                  f"classified={stats['classified']}, low_conf={stats['low_confidence']}, errors={stats['errors']}",
                  "ORG-classifier", "omega-v5.0")


if __name__ == "__main__":
    main()
