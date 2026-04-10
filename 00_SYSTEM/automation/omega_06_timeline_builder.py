#!/usr/bin/env python3
"""
Ω6: TIMELINE BUILDER — OMEGA-ELITE-MASTER
Right-click any folder → auto-generate chronological timeline from all documents.
Extracts dates + surrounding context, sorts chronologically, outputs timeline.
"""
import sys, os, re, json
from pathlib import Path
from datetime import datetime
from collections import defaultdict

MONTHS = {
    'january': '01', 'february': '02', 'march': '03', 'april': '04',
    'may': '05', 'june': '06', 'july': '07', 'august': '08',
    'september': '09', 'october': '10', 'november': '11', 'december': '12',
}

def parse_date(text):
    """Try to parse various date formats to ISO."""
    # Month DD, YYYY
    m = re.match(r'(\w+)\s+(\d{1,2}),?\s+(\d{4})', text)
    if m:
        month = MONTHS.get(m.group(1).lower())
        if month:
            return f"{m.group(3)}-{month}-{int(m.group(2)):02d}"
    # MM/DD/YYYY
    m = re.match(r'(\d{1,2})/(\d{1,2})/(\d{2,4})', text)
    if m:
        yr = m.group(3)
        if len(yr) == 2:
            yr = f"20{yr}" if int(yr) < 50 else f"19{yr}"
        return f"{yr}-{int(m.group(1)):02d}-{int(m.group(2)):02d}"
    # YYYY-MM-DD
    m = re.match(r'(\d{4})-(\d{2})-(\d{2})', text)
    if m:
        return text[:10]
    return None

DATE_PATTERNS = [
    r'((?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4})',
    r'(\d{1,2}/\d{1,2}/\d{2,4})',
    r'(\d{4}-\d{2}-\d{2})',
]

def extract_timeline(fp, target):
    try:
        text = fp.read_text(encoding='utf-8', errors='replace')
    except Exception:
        return []

    events = []
    lines = text.split('\n')
    
    for i, line in enumerate(lines):
        for pattern in DATE_PATTERNS:
            for match in re.finditer(pattern, line):
                raw = match.group(1)
                iso = parse_date(raw)
                if iso:
                    ctx_start = max(0, i - 1)
                    ctx_end = min(len(lines), i + 3)
                    context = ' '.join(lines[ctx_start:ctx_end]).strip()[:300]
                    context = re.sub(r'\s+', ' ', context)
                    events.append({
                        "date": iso, "raw_date": raw,
                        "context": context,
                        "source": str(fp.relative_to(target)),
                        "line": i + 1
                    })
    return events

def build_timeline(target):
    target = Path(target).resolve()
    print(f"{'='*60}")
    print(f"  Ω6: TIMELINE BUILDER")
    print(f"  Target: {target}")
    print(f"{'='*60}\n")

    all_events = []
    files = 0
    for fp in sorted(target.rglob("*")):
        if fp.suffix.lower() in ('.md', '.txt', '.docx', '.csv') and fp.is_file():
            events = extract_timeline(fp, target)
            all_events.extend(events)
            files += 1

    all_events.sort(key=lambda e: e["date"])
    
    # Deduplicate nearby events
    seen = set()
    unique_events = []
    for ev in all_events:
        key = (ev["date"], ev["context"][:80])
        if key not in seen:
            seen.add(key)
            unique_events.append(ev)

    print(f"📊 TIMELINE RESULTS")
    print(f"  Files scanned:   {files:,}")
    print(f"  Events found:    {len(all_events):,}")
    print(f"  Unique events:   {len(unique_events):,}")

    if unique_events:
        date_range = f"{unique_events[0]['date']} → {unique_events[-1]['date']}"
        print(f"  Date range:      {date_range}")

    print(f"\n{'─'*60}")
    print(f"  CHRONOLOGICAL TIMELINE")
    print(f"{'─'*60}")
    
    current_month = ""
    for ev in unique_events[:100]:
        month = ev["date"][:7]
        if month != current_month:
            current_month = month
            print(f"\n  ═══ {current_month} ═══")
        ctx = ev["context"][:120]
        print(f"  {ev['date']}  {ctx}")
        print(f"             ⤷ {ev['source']}:{ev['line']}")

    if len(unique_events) > 100:
        print(f"\n  ... and {len(unique_events)-100} more events (see full report)")

    # Save reports
    timeline_path = target / f"_timeline_{datetime.now():%Y%m%d_%H%M%S}.json"
    with open(timeline_path, "w") as f:
        json.dump({"build_time": datetime.now().isoformat(), "files": files,
                    "total_events": len(all_events), "unique_events": len(unique_events),
                    "timeline": unique_events}, f, indent=2)

    md_path = target / f"_TIMELINE_{datetime.now():%Y%m%d}.md"
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(f"# Timeline — Built {datetime.now():%Y-%m-%d %H:%M}\n\n")
        current_month = ""
        for ev in unique_events:
            month = ev["date"][:7]
            if month != current_month:
                current_month = month
                f.write(f"\n## {current_month}\n\n")
            f.write(f"- **{ev['date']}**: {ev['context'][:200]}\n")
            f.write(f"  - Source: `{ev['source']}` line {ev['line']}\n\n")

    print(f"\n📄 JSON: {timeline_path}")
    print(f"📄 Markdown: {md_path}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python omega_06_timeline_builder.py <folder_path>")
        sys.exit(1)
    build_timeline(sys.argv[1])
    input("\nPress Enter to close...")
