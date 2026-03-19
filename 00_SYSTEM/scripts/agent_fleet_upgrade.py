"""
Agent Fleet Upgrade Script — LitigationOS
Audits, reports, enhances, and registers all 64 Copilot agent .md files.
"""
import sys, os, glob, re, statistics
from datetime import datetime

sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')

# ── Configuration ──────────────────────────────────────────────────────────────
AGENTS_DIR = r"C:\Users\andre\.copilot\agents"
REPORT_PATH = r"C:\Users\andre\LitigationOS\05_ANALYSIS\AGENT_FLEET_REPORT.md"
REGISTRY_PATH = r"C:\Users\andre\LitigationOS\00_SYSTEM\AGENT_REGISTRY.md"
ENHANCEMENT_THRESHOLD = 500  # bytes — enhance files under this size
MAX_ENHANCE = 10

# ── Key patterns to detect ─────────────────────────────────────────────────────
PATTERNS = {
    "EAGAIN Prevention": [
        r"eagain",
        r"max\s*3\s*concurrent",
        r"background\s*agents?\s*limit",
        r"SQLITE_BUSY",
        r"database\s*is\s*locked",
    ],
    "Lane Awareness": [
        r"lane\s*[A-F]",
        r"cross[- ]contaminat",
        r"2024-001507",
        r"2025-002760",
        r"custody|housing|convergence|ppo|misconduct|appellate",
    ],
    "DB Access Patterns": [
        r"PRAGMA\s*busy_timeout",
        r"PRAGMA\s*journal_mode",
        r"PRAGMA\s*table_info",
        r"litigation_context\.db",
        r"WAL",
    ],
    "Error Protocol": [
        r"7[- ]layer",
        r"error\s*protocol",
        r"deadman\s*switch",
        r"exponential\s*backoff",
        r"retry.*3",
        r"tier\s*fallback",
    ],
    "Checkpoint/Recovery": [
        r"checkpoint",
        r"crash[- ]resum",
        r"save\s*progress",
        r"recovery",
        r"GOAWAY",
    ],
    "Tool Definitions": [
        r"```(tool|json|yaml)",
        r"tool[_\s]?defin",
        r"function[_\s]?call",
        r"mcp.*tool",
        r"litigation_\w+",
    ],
}

# ── Standard footer for small agents ───────────────────────────────────────────
SOP_FOOTER = """

## Standard Operating Procedures

### Database Access
- Always use: PRAGMA busy_timeout=60000; PRAGMA journal_mode=WAL;
- Verify schema before querying: PRAGMA table_info(table_name)
- Central DB: C:\\Users\\andre\\LitigationOS\\litigation_context.db

### Error Protocol  
1. Try operation → 2. Specific catch → 3. Broad catch + skip → 4. Checkpoint → 5. Deadman switch (120s) → 6. Retry (3x backoff) → 7. Tier fallback

### EAGAIN Prevention
- Max 3 concurrent background agents
- Count running agents before spawning new ones
- If SQLITE_BUSY or database is locked → STOP spawning, wait for current agents

### Lane Awareness
Evidence must stay in its assigned lane (A-F). Never cross-contaminate:
- Lane A: Watson custody (2024-001507-DC)
- Lane B: Shady Oaks housing (2025-002760-CZ)
- Lane C: Convergence (cross-lane)
- Lane D: PPO / Protection Orders
- Lane E: Judicial Misconduct / JTC
- Lane F: Appellate (COA/MSC)

### Checkpoint/Recovery
- Save progress constantly — GOAWAY 503 errors kill agents after 27-40 min
- Checkpoint to SQL todos + filesystem every 10 minutes
- On crash: resume from last checkpoint, never restart from zero

### User Rules
- NO hard deletions — move to I:\\ or Recycle Bin
- Content-based dedup (peek at documents, don't just hash)
- Save progress constantly
"""

SOP_MARKER = "## Standard Operating Procedures"


def read_agent(filepath):
    """Read an agent file and extract metadata."""
    try:
        with open(filepath, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
    except Exception as e:
        return None, str(e)

    size = os.path.getsize(filepath)
    name = os.path.basename(filepath)
    lines = content.strip().split("\n")
    first_line = lines[0].strip() if lines else "(empty)"

    # Detect patterns
    detected = {}
    for pattern_name, regexes in PATTERNS.items():
        found = False
        for rgx in regexes:
            if re.search(rgx, content, re.IGNORECASE):
                found = True
                break
        detected[pattern_name] = found

    coverage_score = sum(1 for v in detected.values() if v)

    return {
        "name": name,
        "path": filepath,
        "first_line": first_line,
        "size": size,
        "content": content,
        "patterns": detected,
        "coverage_score": coverage_score,
        "has_sop": SOP_MARKER in content,
    }, None


def main():
    print("=" * 70)
    print("  AGENT FLEET UPGRADE — LitigationOS")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)

    # ── Step 1: Audit ──────────────────────────────────────────────────────
    print("\n[STEP 1] Auditing agents...")
    md_files = sorted(glob.glob(os.path.join(AGENTS_DIR, "*.md")))
    print(f"  Found {len(md_files)} .md files")

    agents = []
    errors = []
    for fp in md_files:
        info, err = read_agent(fp)
        if err:
            errors.append((os.path.basename(fp), err))
        else:
            agents.append(info)

    if errors:
        print(f"  Errors reading {len(errors)} files:")
        for name, err in errors:
            print(f"    - {name}: {err}")

    sizes = [a["size"] for a in agents]
    print(f"  Successfully read: {len(agents)} agents")
    print(f"  Size range: {min(sizes)}-{max(sizes)} bytes")
    print(f"  Average: {statistics.mean(sizes):.0f} bytes")

    # Pattern coverage summary
    print("\n  Pattern coverage (pre-enhancement):")
    pattern_counts_before = {}
    for pname in PATTERNS:
        count = sum(1 for a in agents if a["patterns"][pname])
        pattern_counts_before[pname] = count
        pct = count / len(agents) * 100
        print(f"    {pname:25s}: {count:3d}/{len(agents)} ({pct:.0f}%)")

    avg_coverage_before = statistics.mean([a["coverage_score"] for a in agents])
    print(f"\n  Average coverage score (before): {avg_coverage_before:.2f}/6")

    # ── Step 2: Fleet Report ───────────────────────────────────────────────
    print("\n[STEP 2] Generating AGENT_FLEET_REPORT.md...")

    sorted_by_size_desc = sorted(agents, key=lambda a: a["size"], reverse=True)
    sorted_by_size_asc = sorted(agents, key=lambda a: a["size"])
    top10_largest = sorted_by_size_desc[:10]
    top10_smallest = sorted_by_size_asc[:10]

    os.makedirs(os.path.dirname(REPORT_PATH), exist_ok=True)

    report_lines = []
    report_lines.append(f"# Agent Fleet Report — LitigationOS")
    report_lines.append(f"")
    report_lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report_lines.append(f"Source: `{AGENTS_DIR}`")
    report_lines.append(f"")
    report_lines.append(f"## Summary")
    report_lines.append(f"")
    report_lines.append(f"| Metric | Value |")
    report_lines.append(f"|--------|-------|")
    report_lines.append(f"| Total agents | {len(agents)} |")
    report_lines.append(f"| Min size | {min(sizes):,} bytes |")
    report_lines.append(f"| Max size | {max(sizes):,} bytes |")
    report_lines.append(f"| Average size | {statistics.mean(sizes):,.0f} bytes |")
    report_lines.append(f"| Median size | {statistics.median(sizes):,.0f} bytes |")
    report_lines.append(f"| Std deviation | {statistics.stdev(sizes):,.0f} bytes |")
    report_lines.append(f"| Agents < 500 bytes | {sum(1 for s in sizes if s < 500)} |")
    report_lines.append(f"| Agents < 1KB | {sum(1 for s in sizes if s < 1024)} |")
    report_lines.append(f"| Agents > 10KB | {sum(1 for s in sizes if s > 10240)} |")
    report_lines.append(f"")
    report_lines.append(f"## Pattern Coverage Analysis (Pre-Enhancement)")
    report_lines.append(f"")
    report_lines.append(f"| Pattern | Count | Percentage |")
    report_lines.append(f"|---------|-------|------------|")
    for pname in PATTERNS:
        c = pattern_counts_before[pname]
        pct = c / len(agents) * 100
        bar = "█" * int(pct / 5) + "░" * (20 - int(pct / 5))
        report_lines.append(f"| {pname} | {c}/{len(agents)} | {pct:.0f}% {bar} |")
    report_lines.append(f"")
    report_lines.append(f"Average coverage score: **{avg_coverage_before:.2f}/6**")
    report_lines.append(f"")
    report_lines.append(f"## Top 10 Largest Agents (Most Complete)")
    report_lines.append(f"")
    report_lines.append(f"| # | Agent File | Size | Coverage | Patterns Present |")
    report_lines.append(f"|---|-----------|------|----------|------------------|")
    for i, a in enumerate(top10_largest, 1):
        present = [k for k, v in a["patterns"].items() if v]
        present_str = ", ".join(present) if present else "None"
        report_lines.append(f"| {i} | {a['name']} | {a['size']:,} B | {a['coverage_score']}/6 | {present_str} |")
    report_lines.append(f"")
    report_lines.append(f"## Top 10 Smallest Agents (Need Enhancement)")
    report_lines.append(f"")
    report_lines.append(f"| # | Agent File | Size | Coverage | First Line |")
    report_lines.append(f"|---|-----------|------|----------|------------|")
    for i, a in enumerate(top10_smallest, 1):
        fl = a["first_line"][:60] + ("..." if len(a["first_line"]) > 60 else "")
        report_lines.append(f"| {i} | {a['name']} | {a['size']:,} B | {a['coverage_score']}/6 | {fl} |")
    report_lines.append(f"")

    # Size distribution buckets
    buckets = [
        ("< 500 B", 0, 500),
        ("500 B - 1 KB", 500, 1024),
        ("1 KB - 2 KB", 1024, 2048),
        ("2 KB - 5 KB", 2048, 5120),
        ("5 KB - 10 KB", 5120, 10240),
        ("10 KB - 15 KB", 10240, 15360),
        ("15 KB+", 15360, 999999),
    ]
    report_lines.append(f"## Size Distribution")
    report_lines.append(f"")
    report_lines.append(f"| Bucket | Count | Agents |")
    report_lines.append(f"|--------|-------|--------|")
    for label, lo, hi in buckets:
        bucket_agents = [a["name"].replace(".agent.md", "") for a in agents if lo <= a["size"] < hi]
        report_lines.append(f"| {label} | {len(bucket_agents)} | {', '.join(bucket_agents[:8])}{'...' if len(bucket_agents) > 8 else ''} |")
    report_lines.append(f"")

    # Full agent table
    report_lines.append(f"## Full Agent Inventory")
    report_lines.append(f"")
    report_lines.append(f"| Agent | Size | Score | EAGAIN | Lanes | DB | Errors | Ckpt | Tools |")
    report_lines.append(f"|-------|------|-------|--------|-------|----|--------|------|-------|")
    for a in sorted(agents, key=lambda x: x["name"]):
        p = a["patterns"]
        report_lines.append(
            f"| {a['name'].replace('.agent.md', '')} | {a['size']:,} | {a['coverage_score']}/6 "
            f"| {'✅' if p['EAGAIN Prevention'] else '❌'} "
            f"| {'✅' if p['Lane Awareness'] else '❌'} "
            f"| {'✅' if p['DB Access Patterns'] else '❌'} "
            f"| {'✅' if p['Error Protocol'] else '❌'} "
            f"| {'✅' if p['Checkpoint/Recovery'] else '❌'} "
            f"| {'✅' if p['Tool Definitions'] else '❌'} |"
        )

    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(report_lines))
    print(f"  Saved to: {REPORT_PATH}")

    # ── Step 3: Enhance smallest agents ────────────────────────────────────
    print("\n[STEP 3] Enhancing smallest agents...")

    # Find candidates: under threshold AND don't already have SOP
    candidates = [
        a for a in sorted_by_size_asc
        if a["size"] < ENHANCEMENT_THRESHOLD and not a["has_sop"]
    ]
    # If fewer than MAX_ENHANCE under threshold, expand to smallest without SOPs
    if len(candidates) < MAX_ENHANCE:
        all_without_sop = [a for a in sorted_by_size_asc if not a["has_sop"]]
        candidates = all_without_sop[:MAX_ENHANCE]

    enhanced_count = 0
    enhanced_names = []
    for a in candidates[:MAX_ENHANCE]:
        filepath = a["path"]
        # Double-check: don't append if already has SOP marker
        try:
            with open(filepath, "r", encoding="utf-8", errors="replace") as f:
                current = f.read()
        except Exception as e:
            print(f"  SKIP {a['name']}: read error: {e}")
            continue

        if SOP_MARKER in current:
            print(f"  SKIP {a['name']}: already has SOPs")
            continue

        with open(filepath, "a", encoding="utf-8") as f:
            f.write(SOP_FOOTER)

        new_size = os.path.getsize(filepath)
        enhanced_count += 1
        enhanced_names.append(a["name"])
        print(f"  ✅ Enhanced: {a['name']} ({a['size']} → {new_size} bytes)")

    print(f"\n  Enhanced {enhanced_count} agents")

    # ── Re-audit after enhancement ─────────────────────────────────────────
    print("\n[POST-ENHANCEMENT] Re-auditing...")
    agents_after = []
    for fp in md_files:
        info, _ = read_agent(fp)
        if info:
            agents_after.append(info)

    pattern_counts_after = {}
    for pname in PATTERNS:
        count = sum(1 for a in agents_after if a["patterns"][pname])
        pattern_counts_after[pname] = count

    avg_coverage_after = statistics.mean([a["coverage_score"] for a in agents_after])
    print(f"  Average coverage score (after): {avg_coverage_after:.2f}/6")
    print(f"\n  Pattern coverage changes:")
    for pname in PATTERNS:
        before = pattern_counts_before[pname]
        after = pattern_counts_after[pname]
        delta = after - before
        print(f"    {pname:25s}: {before} → {after} ({'+' if delta > 0 else ''}{delta})")

    # ── Step 4: Master Agent Registry ──────────────────────────────────────
    print("\n[STEP 4] Creating AGENT_REGISTRY.md...")

    os.makedirs(os.path.dirname(REGISTRY_PATH), exist_ok=True)

    reg = []
    reg.append(f"# LitigationOS — Master Agent Registry")
    reg.append(f"")
    reg.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    reg.append(f"Total agents: {len(agents_after)}")
    reg.append(f"Average coverage: {avg_coverage_after:.2f}/6")
    reg.append(f"Enhanced this run: {enhanced_count}")
    reg.append(f"")
    reg.append(f"## Registry")
    reg.append(f"")
    reg.append(f"| Agent File | Purpose | Size | Has SOPs | Has Tools | Coverage Score |")
    reg.append(f"|-----------|---------|------|----------|-----------|----------------|")

    for a in sorted(agents_after, key=lambda x: x["name"]):
        # Extract purpose from first line (strip markdown heading chars)
        purpose = a["first_line"].lstrip("#").strip()
        if len(purpose) > 60:
            purpose = purpose[:57] + "..."
        has_sops = "✅" if a["has_sop"] else "❌"
        has_tools = "✅" if a["patterns"]["Tool Definitions"] else "❌"
        reg.append(
            f"| {a['name']} | {purpose} | {a['size']:,} B | {has_sops} | {has_tools} | {a['coverage_score']}/6 |"
        )

    reg.append(f"")
    reg.append(f"## Coverage Legend")
    reg.append(f"")
    reg.append(f"Score is 0-6 based on presence of:")
    reg.append(f"1. EAGAIN Prevention (concurrent agent limits)")
    reg.append(f"2. Lane Awareness (case lane A-F routing)")
    reg.append(f"3. DB Access Patterns (PRAGMA statements)")
    reg.append(f"4. Error Protocol (7-layer error handling)")
    reg.append(f"5. Checkpoint/Recovery (crash resilience)")
    reg.append(f"6. Tool Definitions (MCP/function tools)")
    reg.append(f"")
    reg.append(f"## Enhancement Log")
    reg.append(f"")
    reg.append(f"Agents enhanced with Standard Operating Procedures footer:")
    reg.append(f"")
    for name in enhanced_names:
        reg.append(f"- {name}")
    if not enhanced_names:
        reg.append(f"- (none — all agents already had SOPs or were above threshold)")

    with open(REGISTRY_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(reg))
    print(f"  Saved to: {REGISTRY_PATH}")

    # ── Final Summary ──────────────────────────────────────────────────────
    print("\n" + "=" * 70)
    print("  FINAL SUMMARY")
    print("=" * 70)
    print(f"  Total agents:           {len(agents_after)}")
    print(f"  Enhanced this run:      {enhanced_count}")
    print(f"  Avg coverage BEFORE:    {avg_coverage_before:.2f}/6")
    print(f"  Avg coverage AFTER:     {avg_coverage_after:.2f}/6")
    print(f"  Coverage improvement:   +{avg_coverage_after - avg_coverage_before:.2f}")
    print(f"")
    print(f"  Reports generated:")
    print(f"    {REPORT_PATH}")
    print(f"    {REGISTRY_PATH}")
    print("=" * 70)


if __name__ == "__main__":
    main()
