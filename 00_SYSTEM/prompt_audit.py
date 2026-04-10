"""Comprehensive prompt surface area audit for LitigationOS."""
import os
from pathlib import Path
from collections import defaultdict

ROOT = Path(r"C:\Users\andre\LitigationOS")

def count_lines_chars(path):
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
        return len(text.splitlines()), len(text), len(text.split())
    except:
        return 0, 0, 0

# === 1. copilot-instructions.md ===
ci = ROOT / ".github" / "copilot-instructions.md"
ci_lines, ci_chars, ci_words = count_lines_chars(ci)
ci_tokens_est = ci_words * 1.3  # rough token estimate

# === 2. Instruction files ===
inst_dir = ROOT / ".github" / "instructions"
inst_files = sorted(inst_dir.glob("*.md")) if inst_dir.exists() else []
inst_total_lines = 0
inst_total_chars = 0
inst_total_words = 0
inst_details = []
for f in inst_files:
    l, c, w = count_lines_chars(f)
    inst_total_lines += l
    inst_total_chars += c
    inst_total_words += w
    inst_details.append((f.name, l, c, w))

# === 3. Agent definitions (.github/agents/) ===
agents_dir = ROOT / ".github" / "agents"
agent_files = sorted(agents_dir.glob("*.md")) if agents_dir.exists() else []
agent_total_lines = 0
agent_total_chars = 0
agent_total_words = 0
agent_details = []
for f in agent_files:
    l, c, w = count_lines_chars(f)
    agent_total_lines += l
    agent_total_chars += c
    agent_total_words += w
    agent_details.append((f.name, l, c, w))

# === 4. Skills runtime (.github/skills_runtime/) ===
skills_rt_dir = ROOT / ".github" / "skills_runtime"
skills_rt_files = sorted(skills_rt_dir.glob("*.md")) if skills_rt_dir.exists() else []
srt_total_lines = 0
srt_total_chars = 0
srt_total_words = 0
for f in skills_rt_files:
    l, c, w = count_lines_chars(f)
    srt_total_lines += l
    srt_total_chars += c
    srt_total_words += w

# === 5. SINGULARITY skills (.agents/skills/SINGULARITY-*/) ===
sing_dir = ROOT / ".agents" / "skills"
sing_skills = []
sing_total_lines = 0
sing_total_chars = 0
sing_total_words = 0
if sing_dir.exists():
    for d in sorted(sing_dir.iterdir()):
        if d.is_dir() and d.name.startswith("SINGULARITY-"):
            skill_md = d / "SKILL.md"
            if skill_md.exists():
                l, c, w = count_lines_chars(skill_md)
                sing_total_lines += l
                sing_total_chars += c
                sing_total_words += w
                sing_skills.append((d.name, l, c, w))

# === 6. Non-SINGULARITY skills (.agents/skills/ other) ===
other_skills = []
other_total_lines = 0
other_total_chars = 0
if sing_dir.exists():
    for d in sorted(sing_dir.iterdir()):
        if d.is_dir() and not d.name.startswith("SINGULARITY-"):
            skill_md = d / "SKILL.md"
            if skill_md.exists():
                l, c, w = count_lines_chars(skill_md)
                other_total_lines += l
                other_total_chars += c
                other_skills.append((d.name, l, c))

# === 7. .claude skills ===
claude_dir = ROOT / ".claude" / "skills"
claude_skills = []
claude_total_lines = 0
claude_total_chars = 0
if claude_dir.exists():
    for d in sorted(claude_dir.iterdir()):
        if d.is_dir():
            skill_md = d / "SKILL.md"
            if skill_md.exists():
                l, c, w = count_lines_chars(skill_md)
                claude_total_lines += l
                claude_total_chars += c
                claude_skills.append((d.name, l, c))

# === GRAND TOTALS ===
grand_chars = ci_chars + inst_total_chars + agent_total_chars + srt_total_chars + sing_total_chars + other_total_chars + claude_total_chars
grand_lines = ci_lines + inst_total_lines + agent_total_lines + srt_total_lines + sing_total_lines + other_total_lines + claude_total_lines
grand_words = ci_words + inst_total_words + agent_total_words + srt_total_words + sing_total_words
grand_tokens_est = grand_words * 1.3

print("=" * 70)
print("LITIGATIONOS PROMPT SURFACE AREA AUDIT")
print("=" * 70)

print(f"\n{'LAYER':<40} {'FILES':>6} {'LINES':>8} {'CHARS':>10} {'~TOKENS':>10}")
print("-" * 70)
print(f"{'copilot-instructions.md':<40} {'1':>6} {ci_lines:>8,} {ci_chars:>10,} {int(ci_tokens_est):>10,}")
print(f"{'Instruction files (.github/inst/)':<40} {len(inst_files):>6} {inst_total_lines:>8,} {inst_total_chars:>10,} {int(inst_total_words*1.3):>10,}")
print(f"{'Agent definitions (.github/agents/)':<40} {len(agent_files):>6} {agent_total_lines:>8,} {agent_total_chars:>10,} {int(agent_total_words*1.3):>10,}")
print(f"{'Skills runtime (.github/skills_rt/)':<40} {len(skills_rt_files):>6} {srt_total_lines:>8,} {srt_total_chars:>10,} {int(srt_total_words*1.3):>10,}")
print(f"{'SINGULARITY skills (.agents/skills/)':<40} {len(sing_skills):>6} {sing_total_lines:>8,} {sing_total_chars:>10,} {int(sing_total_words*1.3):>10,}")
print(f"{'Other .agents skills':<40} {len(other_skills):>6} {other_total_lines:>8,} {other_total_chars:>10,} {'—':>10}")
print(f"{'.claude skills':<40} {len(claude_skills):>6} {claude_total_lines:>8,} {claude_total_chars:>10,} {'—':>10}")
print("-" * 70)
total_files = 1 + len(inst_files) + len(agent_files) + len(skills_rt_files) + len(sing_skills) + len(other_skills) + len(claude_skills)
print(f"{'GRAND TOTAL':<40} {total_files:>6} {grand_lines:>8,} {grand_chars:>10,} {int(grand_tokens_est):>10,}")

print(f"\n{'='*70}")
print("INSTRUCTION FILES BREAKDOWN")
print(f"{'='*70}")
for name, l, c, w in sorted(inst_details, key=lambda x: -x[2]):
    print(f"  {name:<50} {l:>6} lines  {c:>8,} chars  ~{int(w*1.3):>6,} tok")

print(f"\n{'='*70}")
print(f"TOP 15 LARGEST SINGULARITY SKILLS")
print(f"{'='*70}")
for name, l, c, w in sorted(sing_skills, key=lambda x: -x[2])[:15]:
    print(f"  {name:<50} {l:>6} lines  {c:>8,} chars")

print(f"\n{'='*70}")
print(f"TOP 10 LARGEST AGENT DEFINITIONS")
print(f"{'='*70}")
for name, l, c, w in sorted(agent_details, key=lambda x: -x[2])[:10]:
    print(f"  {name:<50} {l:>6} lines  {c:>8,} chars")

print(f"\n{'='*70}")
print(f"SMALLEST AGENT DEFINITIONS (potential stubs)")
print(f"{'='*70}")
for name, l, c, w in sorted(agent_details, key=lambda x: x[2])[:10]:
    print(f"  {name:<50} {l:>6} lines  {c:>8,} chars")

# === ANTI-PATTERN DETECTION ===
print(f"\n{'='*70}")
print("PROMPT ENGINEERING ANTI-PATTERN DETECTION")
print(f"{'='*70}")

# Check for duplicate content across instruction files
# Load all instruction file content for overlap detection
inst_contents = {}
for f in inst_files:
    try:
        inst_contents[f.name] = f.read_text(encoding="utf-8", errors="replace")
    except:
        pass

# Check copilot-instructions for key rule duplication
ci_text = ci.read_text(encoding="utf-8", errors="replace") if ci.exists() else ""

# Key rules that might be duplicated
duplicate_indicators = [
    ("FTS5 safety", "sanitize.*fts5|FTS5.*safety|MATCH.*try.*except"),
    ("child name", "L\\.D\\.W\\.|MCR 8\\.119"),
    ("no AI refs", "LitigationOS.*court|AI.*filing|database.*court"),
    ("pro se", "pro se|undersigned counsel"),
    ("schema verify", "PRAGMA table_info"),
    ("busy_timeout", "busy_timeout"),
    ("no delete", "NO DELET|never delet|append.only"),
]

import re
print("\nRule duplication across instruction layers:")
for rule_name, pattern in duplicate_indicators:
    count_ci = len(re.findall(pattern, ci_text, re.IGNORECASE))
    count_inst = sum(len(re.findall(pattern, txt, re.IGNORECASE)) for txt in inst_contents.values())
    total = count_ci + count_inst
    if total > 2:
        print(f"  ⚠️  '{rule_name}' appears {total}× ({count_ci} in copilot-inst, {count_inst} in instruction files)")
    else:
        print(f"  ✅ '{rule_name}' — {total} occurrences (OK)")

# Check for conflicting instructions
print("\nPotential instruction conflicts:")
# Check if "be concise" and "be comprehensive" coexist
concise_count = len(re.findall(r"concis|brief|short|minimal", ci_text, re.IGNORECASE))
verbose_count = len(re.findall(r"comprehensiv|thorough|complete|exhaustive|every.*detail", ci_text, re.IGNORECASE))
if concise_count > 0 and verbose_count > 0:
    print(f"  ⚠️  Concise signals ({concise_count}) vs Comprehensive signals ({verbose_count}) — potential conflict")

# Context window budget analysis
print(f"\n{'='*70}")
print("CONTEXT WINDOW BUDGET ANALYSIS")
print(f"{'='*70}")
print(f"  Model context: ~200K tokens (Claude Opus/Sonnet)")
print(f"  Recommended system prompt budget: <10K tokens (5%)")
print(f"  copilot-instructions.md alone: ~{int(ci_tokens_est):,} tokens")
print(f"  + instruction files auto-loaded: ~{int(inst_total_words*1.3):,} tokens")
print(f"  = TOTAL ALWAYS-ON PROMPT: ~{int((ci_words + inst_total_words)*1.3):,} tokens")
pct = (ci_words + inst_total_words) * 1.3 / 200000 * 100
print(f"  = {pct:.1f}% of context window (target: <5%)")
if pct > 10:
    print(f"  🔴 CRITICAL: System prompt exceeds 10% of context — severe attention dilution")
elif pct > 5:
    print(f"  🟡 WARNING: System prompt exceeds 5% — moderate attention dilution")
else:
    print(f"  🟢 OK: Within budget")

# Skills loaded on-demand (not always-on)
print(f"\n  On-demand skills (loaded per invocation):")
print(f"    SINGULARITY skills: {len(sing_skills)} files, ~{int(sing_total_words*1.3):,} tokens total")
print(f"    Skills runtime: {len(skills_rt_files)} files, ~{int(srt_total_words*1.3):,} tokens total")
print(f"    If ALL skills loaded simultaneously: ~{int((sing_total_words + srt_total_words)*1.3):,} tokens")

print(f"\n{'='*70}")
print("PRE vs POST SINGULARITY SKILL DUPLICATION")
print(f"{'='*70}")

# Check for pre-SINGULARITY skills that should have been absorbed
pre_sing = [s for s in sing_skills if not s[0].startswith("SINGULARITY-MBP")]
absorbed_map = {
    "adversary-warfare": "litigation-warfare",
    "case-operations": "litigation-warfare",
    "custody-strategy": "litigation-warfare",
    "evidence-intelligence": "litigation-warfare",
    "court-filing": "court-arsenal",
    "legal-authority": "court-arsenal",
    "appellate-federal": "court-arsenal",
    "data-engineering": "data-dominion",
    "database-mastery": "data-dominion",
    "agent-architect": "agent-nexus",
    "agent-evaluation": "agent-nexus",
    "mcp-tools": "agent-nexus",
    "ai-engineering": "ai-core",
    "debugging-mastery": "debug-ops",
    "testing-quality": "code-mastery",
    "clean-code": "system-forge",
    "performance-optimization": "system-forge",
    "system-design": "system-forge",
    "devops-cloud": "system-forge",
    "file-format-mastery": "document-forge",
    "technical-writing": "document-forge",
    "automation-scraping": "automation-engine",
    "git-workflow": "automation-engine",
    "typescript-python": "code-mastery",
    "fullstack-web": "ui-engineering",
    "design-ux": "ui-engineering",
    "offensive-security": "security-fortress",
    "appsec": "security-fortress",
    "crypto-infra": "security-fortress",
    "mobile-cross-platform": "creative-engine",
    "messaging-integration": "creative-engine",
    "ai-media-creation": "creative-engine",
    "project-management": "product-architecture",
    "backend-api": "product-architecture",
}

pre_sing_names = set()
post_sing_names = set()
for name, _, _, _ in pre_sing:
    short = name.replace("SINGULARITY-", "")
    if short in absorbed_map:
        pre_sing_names.add(short)
    post = absorbed_map.get(short)
    if post:
        # Check if the forged superskill also exists
        forged_name = f"SINGULARITY-{post}"
        if any(s[0] == forged_name for s in sing_skills):
            post_sing_names.add(post)

both_exist = []
for old_name, new_name in absorbed_map.items():
    old_full = f"SINGULARITY-{old_name}"
    new_full = f"SINGULARITY-{new_name}"
    old_exists = any(s[0] == old_full for s in sing_skills)
    new_exists = any(s[0] == new_full for s in sing_skills)
    if old_exists and new_exists:
        old_size = next((s[2] for s in sing_skills if s[0] == old_full), 0)
        new_size = next((s[2] for s in sing_skills if s[0] == new_full), 0)
        both_exist.append((old_full, new_full, old_size, new_size))

if both_exist:
    print(f"  🔴 {len(both_exist)} PRE-SINGULARITY skills still exist alongside their FORGED superskill:")
    for old, new, old_sz, new_sz in sorted(both_exist, key=lambda x: -x[2])[:15]:
        print(f"     {old} ({old_sz:,} chars) → ABSORBED INTO → {new} ({new_sz:,} chars)")
    waste = sum(x[2] for x in both_exist)
    print(f"  Total wasted chars in obsolete skills: {waste:,}")
else:
    print("  ✅ No pre/post duplication detected")

print(f"\n{'='*70}")
print("RECOMMENDATIONS")
print(f"{'='*70}")

recommendations = []
if pct > 5:
    recommendations.append("1. CRITICAL: Reduce always-on prompt budget from {:.1f}% to <5% of context window".format(pct))
if both_exist:
    recommendations.append(f"2. HIGH: Delete {len(both_exist)} obsolete pre-SINGULARITY skills (replaced by forged superskills)")
if any(l < 10 for _, l, _, _ in agent_details):
    stub_count = sum(1 for _, l, _, _ in agent_details if l < 10)
    recommendations.append(f"3. MEDIUM: {stub_count} agent definitions are stubs (<10 lines) — flesh out or remove")
recommendations.append("4. MEDIUM: Deduplicate rules that appear in BOTH copilot-instructions.md AND instruction files")
recommendations.append("5. LOW: Consider a prompt registry (version-controlled, A/B testable) for agent definitions")

for r in recommendations:
    print(f"  {r}")

print(f"\nAudit complete.")
