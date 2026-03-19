"""
AUTONOMOS Validation Script — Run to verify all modules load correctly.
Usage: cd C:\\Users\\andre\\LitigationOS\\00_SYSTEM\\autonomos && python _validate.py
"""
import sys
import os
from pathlib import Path

# Ensure correct paths
root = Path(__file__).parent
for sub in ["shared", "sentinel", "inquisitor", str(root)]:
    p = str(root / sub) if sub != str(root) else sub
    if p not in sys.path:
        sys.path.insert(0, p)

print("=" * 60)
print("AUTONOMOS v1.0.0 — Validation")
print("=" * 60)

errors = []
modules = [
    ("autonomos_config", "Shared Config"),
    ("provenance", "Provenance Tracker"),
    ("event_bridge", "Event Bridge"),
    ("sentinel_monitor", "SENTINEL Monitor"),
    ("sentinel_classifier", "SENTINEL Classifier"),
    ("sentinel_mover", "SENTINEL Mover"),
    ("sentinel", "SENTINEL Orchestrator"),
    ("inquisitor", "INQUISITOR Analyzer"),
    ("publisher", "INQUISITOR Publisher"),
]

for mod_name, label in modules:
    try:
        __import__(mod_name)
        print(f"  ✓ {label:<25} ({mod_name})")
    except Exception as e:
        errors.append((label, str(e)))
        print(f"  ✗ {label:<25} FAILED: {e}")

print()

# Check watchdog
try:
    import watchdog
    print(f"  ✓ watchdog library        v{watchdog.version.VERSION_STRING}")
except ImportError:
    errors.append(("watchdog", "Not installed. Run: pip install watchdog"))
    print("  ✗ watchdog library        MISSING — run: pip install watchdog")

# Check PyMuPDF
try:
    import fitz
    print(f"  ✓ PyMuPDF (fitz)          v{fitz.version[0]}")
except ImportError:
    print("  ○ PyMuPDF (fitz)          Optional — PDF extraction limited without it")

# Check python-docx
try:
    import docx
    print(f"  ✓ python-docx             installed")
except ImportError:
    print("  ○ python-docx             Optional — DOCX extraction limited without it")

print()

# Quick functional test
try:
    from sentinel_classifier import classify_file
    # Classify a known file
    test_file = root.parent / "pipeline" / "config.py"
    if test_file.exists():
        result = classify_file(str(test_file))
        print(f"  ✓ Classification test:    {result.category} / {result.doc_type}")
    else:
        print("  ○ Classification test:    config.py not found (skipped)")
except Exception as e:
    errors.append(("Classification test", str(e)))
    print(f"  ✗ Classification test:    FAILED: {e}")

try:
    from event_bridge import EventBridge
    bridge = EventBridge()
    eid = bridge.publish("TEST", {"message": "validation"})
    events = bridge.consume(["TEST"])
    if events:
        bridge.ack(events[0].event_id)
        print(f"  ✓ Event bridge test:      publish→consume→ack OK")
    bridge.close()
except Exception as e:
    errors.append(("Event bridge test", str(e)))
    print(f"  ✗ Event bridge test:      FAILED: {e}")

try:
    from provenance import ProvenanceTracker
    tracker = ProvenanceTracker()
    stats = tracker.stats()
    print(f"  ✓ Provenance test:        {stats['total']} records in DB")
    tracker.close()
except Exception as e:
    errors.append(("Provenance test", str(e)))
    print(f"  ✗ Provenance test:        FAILED: {e}")

print()
print("=" * 60)
if errors:
    print(f"RESULT: {len(errors)} error(s) — fix before starting")
    for label, err in errors:
        print(f"  → {label}: {err}")
else:
    print("RESULT: ALL CHECKS PASSED ✓")
    print()
    print("Quick start:")
    print("  python autonomos.py health      # Health check")
    print("  python autonomos.py classify <f> # Classify a file")
    print("  python autonomos.py start        # Start full daemon")
print("=" * 60)
