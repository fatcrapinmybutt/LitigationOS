#!/usr/bin/env python3
"""
LEXOS BIBLE — brain_builder.py
Extracts high-signal knowledge from agent journals and compresses into 50 brain nuclei.
Run: python D:\\TEMP\\lexos_bible\\brain_builder.py
"""
import os, sys, re, json, hashlib, math, time, glob as globmod
from collections import Counter, defaultdict
from datetime import datetime, timezone

sys.path.insert(0, "D:/TEMP")
sys.path.insert(0, "D:/TEMP/pylibs")

BASE_DIR = "D:/TEMP/lexos_bible"
BRAINS_DIR = os.path.join(BASE_DIR, "brains")
CONFIG_PATH = os.path.join(BASE_DIR, "lexos_config.json")
INDEX_PATH = os.path.join(BASE_DIR, "lexos_index.json")

# ── Regex patterns for high-signal extraction ──────────────────────────
RE_MCL = re.compile(r"MCL\s+\d[\d.]*", re.IGNORECASE)
RE_MCR = re.compile(r"MCR\s+\d[\d.]*", re.IGNORECASE)
RE_USC = re.compile(r"\d+\s+U\.?S\.?C\.?\s+(?:§\s*)?\d+", re.IGNORECASE)
RE_CFR = re.compile(r"\d+\s+C\.?F\.?R\.?\s+(?:§\s*)?\d+", re.IGNORECASE)
RE_CASE_CITE = re.compile(r"\d+\s+(?:Mich(?:\s+App)?|NW2d|NW\.2d|F\.\d[a-z]*|S\.?Ct\.?)\s+\d+", re.IGNORECASE)
RE_CONST = re.compile(r"(?:Const\s+\d+|Art(?:icle)?\s+[IVXLCDM\d]+|Amend(?:ment)?\s+[IVXLCDM\d]+)", re.IGNORECASE)
RE_DATE = re.compile(r"\b(?:\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{4}-\d{2}-\d{2}|(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\w*\s+\d{1,2},?\s+\d{4})\b", re.IGNORECASE)
RE_DOLLAR = re.compile(r"\$\s*[\d,]+(?:\.\d{2})?")
RE_VIOLATION = re.compile(
    r"\b(?:violat|misconduct|fraud|perjur|contempt|obstruct|coerci|alienat|"
    r"abuse|neglect|denial|deprivat|suppress|falsif|tamper|retaliat|intimidat|"
    r"conspir|collud|ex\s*parte|bias|prejudic|error|irregulari)\w*\b",
    re.IGNORECASE,
)
RE_LEGAL = re.compile(
    r"\b(?:plaintiff|defendant|respondent|petitioner|appellant|appellee|"
    r"custody|parenting\s*time|best\s*interest|guardian|conservator|"
    r"hearing|motion|order|judgment|opinion|ruling|decree|stipulat|"
    r"jurisdiction|venue|standing|statute|burden|standard\s*of\s*review|"
    r"de\s*novo|abuse\s*of\s*discretion|due\s*process|equal\s*protect|"
    r"PPO|FOC|CPS|DHHS|injunction|stay|remand|reversal)\b",
    re.IGNORECASE,
)

PERSON_NAMES = {
    "andrew": "andrew_pigors", "pigors": "andrew_pigors",
    "emily": "emily_watson", "albert": "albert_watson",
    "lori": "lori_watson", "cody": "cody_watson",
    "mcneill": "judge_mcneill", "rusco": "rusco",
    "l.d.w": "child_ldw", "ldw": "child_ldw",
}
RE_PERSONS = re.compile(
    r"\b(?:" + "|".join(re.escape(k) for k in PERSON_NAMES) + r")\b",
    re.IGNORECASE,
)

# ── Brain-to-keyword mapping (which signals route to which brain) ──────
BRAIN_KEYWORDS = {
    "01_mcl":        [RE_MCL],
    "02_mcr":        [RE_MCR],
    "03_caselaw":    [RE_CASE_CITE],
    "04_usc":        [RE_USC],
    "05_cfr":        [RE_CFR],
    "06_constitution":[RE_CONST],
    "07_benchbook":  [re.compile(r"\b(?:benchbook|MJI|jury\s*instruction|standard\s*instruction)\b", re.I)],
    "08_authority":  [re.compile(r"\b(?:MRPC|canon|ethic|professional\s*conduct|disciplin)\w*\b", re.I)],
    "09_andrew":     [re.compile(r"\b(?:andrew|pigors)\b", re.I)],
    "10_emily":      [re.compile(r"\bemily\b", re.I)],
    "11_albert":     [re.compile(r"\balbert\b", re.I)],
    "12_lori":       [re.compile(r"\blori\b", re.I)],
    "13_cody":       [re.compile(r"\bcody\b", re.I)],
    "14_mcneill":    [re.compile(r"\bmcneill\b", re.I)],
    "15_rusco":      [re.compile(r"\brusco\b", re.I)],
    "16_child":      [re.compile(r"\b(?:l\.?d\.?w\.?|child|minor)\b", re.I)],
    "17_persons":    [RE_PERSONS],
    "18_alienation": [re.compile(r"\b(?:alienat|interfere|undermin|gatekeep|estrange)\w*\b", re.I)],
    "19_custody":    [re.compile(r"\b(?:custody|parenting\s*time|placement|best\s*interest|BIF)\w*\b", re.I)],
    "20_ppo":        [re.compile(r"\b(?:PPO|personal\s*protection|restraining|stalking)\b", re.I)],
    "21_due_process":[re.compile(r"\b(?:due\s*process|procedural\s*due|substantive\s*due|notice|opportunit)\w*\b", re.I)],
    "22_misconduct": [re.compile(r"\b(?:misconduct|judicial\s*error|canon|recusal|disqualif)\w*\b", re.I)],
    "23_fraud":      [re.compile(r"\b(?:fraud|perjur|false\s*statement|misrepresent|fabricat)\w*\b", re.I)],
    "24_contempt":   [re.compile(r"\b(?:contempt|enforce|compli|sanction|violat.*order)\w*\b", re.I)],
    "25_violations": [RE_VIOLATION],
    "26_hearings":   [re.compile(r"\b(?:hearing|proceeding|oral\s*argument|evidentiary|status\s*conference)\b", re.I)],
    "27_orders":     [re.compile(r"\b(?:order|judgment|decree|condition|injunction|directive)\b", re.I)],
    "28_motions":    [re.compile(r"\b(?:motion|brief|petition|request|filing|response|reply)\b", re.I)],
    "29_discovery":  [re.compile(r"\b(?:discovery|subpoena|interrogator|deposition|request.*production|FOIA)\w*\b", re.I)],
    "30_evidence":   [re.compile(r"\b(?:evidence|exhibit|document|record|testimony|affidavit|declaration)\b", re.I)],
    "31_best_int":   [re.compile(r"\b(?:best\s*interest|factor\s*[a-n]|MCL\s*722\.23|BIF)\b", re.I)],
    "32_financial":  [RE_DOLLAR, re.compile(r"\b(?:financ|damage|cost|fee|income|asset|debt|support)\w*\b", re.I)],
    "33_timeline":   [RE_DATE, re.compile(r"\b(?:timeline|chronolog|sequence|date)\b", re.I)],
    "34_narrative":  [re.compile(r"\b(?:narrative|theme|story|pattern|overview|summary)\b", re.I)],
    "35_welfare":    [re.compile(r"\b(?:welfare|safety|protect|CPS|DHHS|neglect|abuse|harm.*child)\w*\b", re.I)],
    "36_bond":       [re.compile(r"\b(?:bond|bail|access.*justice|indigent|financial\s*barrier)\w*\b", re.I)],
    "37_comms":      [re.compile(r"\b(?:communicat|text|email|message|letter|phone|voicemail)\w*\b", re.I)],
    "38_credibility":[re.compile(r"\b(?:credib|reliab|inconsisten|contradict|impeach|demeanor)\w*\b", re.I)],
    "39_patterns":   [re.compile(r"\b(?:pattern|recurring|systematic|repeated|habitual|history\s*of)\w*\b", re.I)],
    "40_impact":     [re.compile(r"\b(?:impact|harm|damage|trauma|consequence|effect|suffer)\w*\b", re.I)],
    "41_appellate":  [re.compile(r"\b(?:appell|appeal|COA|court\s*of\s*appeals|remand|reversal)\w*\b", re.I)],
    "42_emergency":  [re.compile(r"\b(?:emergency|emergent|ex\s*parte|immediate|irreparable|TRO)\w*\b", re.I)],
    "43_remedies":   [re.compile(r"\b(?:remed|relief|restitut|compensat|injunctive|declaratory)\w*\b", re.I)],
    "44_review":     [re.compile(r"\b(?:standard.*review|de\s*novo|abuse.*discretion|clearly\s*erroneous|plain\s*error)\b", re.I)],
    "45_procedural": [re.compile(r"\b(?:procedural|compliance|timel|deadline|filing\s*require|jurisdict)\w*\b", re.I)],
    "46_foc":        [re.compile(r"\b(?:FOC|friend.*court|referee|recommendation|investigat)\w*\b", re.I)],
    "47_police":     [re.compile(r"\b(?:police|officer|arrest|report|incident|dispatch|law\s*enforcement)\w*\b", re.I)],
    "48_medical":    [re.compile(r"\b(?:medic|health|diagnos|therap|treatment|prescription|mental\s*health)\w*\b", re.I)],
    "49_meek":       [re.compile(r"\b(?:pro\s*se|self.*represent|meek|unrepresent|access.*court)\w*\b", re.I)],
    "50_case_no":    [re.compile(r"\b(?:case\s*(?:no|number|#)|docket|file\s*(?:no|number)|\d{2,4}-\d{4,})\w*\b", re.I)],
}

BRAIN_META = {
    "01_mcl":        ("Michigan Compiled Laws",       "statutes"),
    "02_mcr":        ("Michigan Court Rules",          "court_rules"),
    "03_caselaw":    ("Case Citations",                "caselaw"),
    "04_usc":        ("Federal Statutes",              "federal_statutes"),
    "05_cfr":        ("Federal Regulations",           "federal_regs"),
    "06_constitution":("Constitutional Provisions",    "constitution"),
    "07_benchbook":  ("MJI Benchbook",                 "benchbook"),
    "08_authority":  ("Ethics & Professional Conduct", "ethics"),
    "09_andrew":     ("Andrew Pigors",                 "person"),
    "10_emily":      ("Emily Watson",                  "person"),
    "11_albert":     ("Albert Watson",                 "person"),
    "12_lori":       ("Lori Watson",                   "person"),
    "13_cody":       ("Cody Watson",                   "person"),
    "14_mcneill":    ("Judge McNeill",                 "person"),
    "15_rusco":      ("Opposing Counsel",              "person"),
    "16_child":      ("L.D.W.",                        "person"),
    "17_persons":    ("All Persons Combined",          "persons_combined"),
    "18_alienation": ("Parental Alienation",           "alienation"),
    "19_custody":    ("Custody Proceedings",            "custody"),
    "20_ppo":        ("PPO Evidence & Defenses",       "ppo"),
    "21_due_process":("Due Process Violations",        "due_process"),
    "22_misconduct": ("Judicial Misconduct",           "misconduct"),
    "23_fraud":      ("Fraud & Perjury",               "fraud"),
    "24_contempt":   ("Contempt & Enforcement",        "contempt"),
    "25_violations": ("Violations Catalog",            "violations"),
    "26_hearings":   ("Hearing Records",               "hearings"),
    "27_orders":     ("Court Orders",                  "orders"),
    "28_motions":    ("Motion Practice",               "motions"),
    "29_discovery":  ("Discovery Records",             "discovery"),
    "30_evidence":   ("Evidence Inventory",            "evidence"),
    "31_best_int":   ("Best Interest Factors",         "best_interest"),
    "32_financial":  ("Financial Damages",             "financial"),
    "33_timeline":   ("Chronological Events",          "timeline"),
    "34_narrative":  ("Case Narratives",               "narrative"),
    "35_welfare":    ("Child Welfare",                 "welfare"),
    "36_bond":       ("Bond & Access to Justice",      "bond"),
    "37_comms":      ("Communications Analysis",       "communications"),
    "38_credibility":("Credibility Assessments",       "credibility"),
    "39_patterns":   ("Behavioral Patterns",           "patterns"),
    "40_impact":     ("Impact & Harm Quantification",  "impact"),
    "41_appellate":  ("Appellate Issues",              "appellate"),
    "42_emergency":  ("Emergency Relief",              "emergency"),
    "43_remedies":   ("Available Remedies",            "remedies"),
    "44_review":     ("Standards of Review",           "review_standards"),
    "45_procedural": ("Procedural Compliance",         "procedural_compliance"),
    "46_foc":        ("Friend of Court",               "foc"),
    "47_police":     ("Police Reports",                "police"),
    "48_medical":    ("Medical/Health Records",        "medical"),
    "49_meek":       ("Meek/Pro Se Considerations",    "pro_se"),
    "50_case_no":    ("Case Number Tracking",          "case_numbers"),
}

MAX_BRAIN_KB = 500


def load_config():
    if os.path.isfile(CONFIG_PATH):
        with open(CONFIG_PATH, "r", encoding="utf-8", errors="replace") as f:
            return json.load(f)
    return {"journals_dir": "C:/Users/andre/Desktop/AGENT_JOURNALS", "max_brain_size_kb": 500}


def _stable_id(text):
    return hashlib.sha1(text.encode("utf-8", errors="replace")).hexdigest()[:12]


def _tokenize(text):
    return re.findall(r"[a-z0-9]+(?:\.[a-z0-9]+)*", text.lower())


def _score_line(line):
    """Score a line by citation density * keyword density."""
    cit = len(RE_MCL.findall(line)) + len(RE_MCR.findall(line)) + len(RE_CASE_CITE.findall(line))
    cit += len(RE_USC.findall(line)) + len(RE_CONST.findall(line))
    kw = len(RE_LEGAL.findall(line)) + len(RE_VIOLATION.findall(line))
    dollar = len(RE_DOLLAR.findall(line))
    date = len(RE_DATE.findall(line))
    length_factor = min(len(line) / 200.0, 1.0)
    return (cit * 3.0 + kw * 1.5 + dollar * 1.0 + date * 0.5) * max(length_factor, 0.1)


def _extract_citations(line):
    cites = []
    cites.extend(RE_MCL.findall(line))
    cites.extend(RE_MCR.findall(line))
    cites.extend(RE_CASE_CITE.findall(line))
    cites.extend(RE_USC.findall(line))
    cites.extend(RE_CFR.findall(line))
    cites.extend(RE_CONST.findall(line))
    return cites


def _extract_tags(line):
    tags = set()
    if RE_MCL.search(line):       tags.add("mcl")
    if RE_MCR.search(line):       tags.add("mcr")
    if RE_CASE_CITE.search(line): tags.add("caselaw")
    if RE_VIOLATION.search(line): tags.add("violation")
    if RE_DOLLAR.search(line):    tags.add("financial")
    if RE_DATE.search(line):      tags.add("dated")
    if RE_PERSONS.search(line):   tags.add("person")
    if RE_LEGAL.search(line):     tags.add("legal")
    return sorted(tags)


def _build_tfidf_index(entries):
    """Build an inverted index mapping tokens -> list of entry indices."""
    index = defaultdict(list)
    for i, entry in enumerate(entries):
        tokens = set(_tokenize(entry.get("text", "")))
        for tok in tokens:
            index[tok].append(i)
    return {k: v for k, v in index.items()}


def gather_journal_files(journals_dir):
    """Recursively gather all readable text files from journal directories."""
    all_files = []
    if not os.path.isdir(journals_dir):
        print(f"  [WARN] Journals directory not found: {journals_dir}")
        return all_files
    for root, _dirs, files in os.walk(journals_dir):
        for fn in files:
            ext = os.path.splitext(fn)[1].lower()
            if ext in (".md", ".txt", ".json", ".jsonl", ".csv", ".log", ".yml", ".yaml"):
                all_files.append(os.path.join(root, fn).replace("\\", "/"))
    return all_files


def read_file_lines(fpath):
    """Read a file and return non-empty lines."""
    try:
        with open(fpath, "r", encoding="utf-8", errors="replace") as f:
            text = f.read()
        lines = []
        for raw in text.split("\n"):
            line = raw.strip()
            if len(line) >= 20:
                lines.append(line)
        return lines, fpath
    except Exception as e:
        print(f"  [WARN] Cannot read {fpath}: {e}")
        return [], fpath


def match_line_to_brains(line, brain_id):
    """Check if a line matches the keyword patterns for a given brain."""
    patterns = BRAIN_KEYWORDS.get(brain_id, [])
    for pat in patterns:
        if pat.search(line):
            return True
    return False


def build_brain(brain_id, all_lines_with_source, config):
    """Build a single brain nucleus from matched lines."""
    max_kb = config.get("max_brain_size_kb", MAX_BRAIN_KB)
    name, domain = BRAIN_META.get(brain_id, (brain_id, "unknown"))

    matched = []
    seen_hashes = set()
    for line, source in all_lines_with_source:
        if not match_line_to_brains(line, brain_id):
            continue
        h = _stable_id(line)
        if h in seen_hashes:
            continue
        seen_hashes.add(h)
        score = _score_line(line)
        citations = _extract_citations(line)
        tags = _extract_tags(line)
        matched.append({
            "id": h,
            "text": line,
            "score": round(score, 4),
            "source": source,
            "citations": citations,
            "tags": tags,
        })

    matched.sort(key=lambda e: e["score"], reverse=True)

    # Trim to fit within max_kb
    entries = []
    total_chars = 0
    max_chars = max_kb * 1024
    for entry in matched:
        entry_size = len(entry["text"]) + 200  # overhead estimate
        if total_chars + entry_size > max_chars:
            break
        entries.append(entry)
        total_chars += entry_size

    # Renumber IDs sequentially
    for i, entry in enumerate(entries):
        entry["id"] = f"e{i+1:04d}"

    index = _build_tfidf_index(entries)

    unique_cites = set()
    unique_persons = set()
    for e in entries:
        unique_cites.update(e.get("citations", []))
        for m in RE_PERSONS.finditer(e.get("text", "")):
            unique_persons.add(m.group(0).lower())

    nucleus = {
        "brain_id": brain_id,
        "name": name,
        "domain": domain,
        "created": datetime.now(timezone.utc).isoformat(),
        "entry_count": len(entries),
        "nucleus_size_kb": round(total_chars / 1024, 1),
        "entries": entries,
        "index": index,
        "stats": {
            "total_chars": total_chars,
            "unique_citations": len(unique_cites),
            "unique_persons": len(unique_persons),
            "top_score": entries[0]["score"] if entries else 0,
            "source_files_matched": len(set(e["source"] for e in entries)),
        },
    }
    return nucleus


def save_brain(nucleus, brains_dir):
    num = nucleus["brain_id"].split("_")[0]
    rest = "_".join(nucleus["brain_id"].split("_")[1:])
    fname = f"brain_{num}_{rest}.json"
    fpath = os.path.join(brains_dir, fname).replace("\\", "/")
    with open(fpath, "w", encoding="utf-8") as f:
        json.dump(nucleus, f, indent=2, ensure_ascii=False)
    return fpath


def main():
    print("=" * 70)
    print("  LEXOS BIBLE — Brain Builder v1.0")
    print("=" * 70)
    t0 = time.time()

    config = load_config()
    journals_dir = config.get("journals_dir", "C:/Users/andre/Desktop/AGENT_JOURNALS")
    os.makedirs(BRAINS_DIR, exist_ok=True)

    # Phase 1: Gather all journal files
    print(f"\n[Phase 1] Scanning journals: {journals_dir}")
    files = gather_journal_files(journals_dir)
    print(f"  Found {len(files)} files")

    # Phase 2: Read all lines
    print("[Phase 2] Reading files...")
    all_lines = []
    for fpath in files:
        lines, src = read_file_lines(fpath)
        for line in lines:
            all_lines.append((line, src))
    print(f"  Loaded {len(all_lines)} lines from {len(files)} files")

    # Phase 3: Build each brain
    print(f"[Phase 3] Building {len(BRAIN_META)} brain nuclei...")
    results = []
    for brain_id in sorted(BRAIN_META.keys()):
        nucleus = build_brain(brain_id, all_lines, config)
        fpath = save_brain(nucleus, BRAINS_DIR)
        results.append((brain_id, nucleus["entry_count"], nucleus["nucleus_size_kb"]))
        status = "OK" if nucleus["entry_count"] > 0 else "EMPTY"
        print(f"  [{status}] {brain_id:20s} -> {nucleus['entry_count']:5d} entries, {nucleus['nucleus_size_kb']:6.1f} KB")

    # Phase 4: Summary
    total_entries = sum(r[1] for r in results)
    total_kb = sum(r[2] for r in results)
    populated = sum(1 for r in results if r[1] > 0)
    elapsed = time.time() - t0

    print(f"\n{'=' * 70}")
    print(f"  BUILD COMPLETE in {elapsed:.1f}s")
    print(f"  Brains: {len(results)} total, {populated} populated, {len(results)-populated} empty")
    print(f"  Entries: {total_entries} total")
    print(f"  Size: {total_kb:.1f} KB total ({total_kb/1024:.2f} MB)")
    print(f"  Output: {BRAINS_DIR}")
    print(f"{'=' * 70}")

    # If no journals found, seed empty brains so server can still start
    if total_entries == 0:
        print("\n  [INFO] No journal data found. Empty brain nuclei created as placeholders.")
        print("  [INFO] Run brain_builder.py again after placing journals in:")
        print(f"         {journals_dir}")


if __name__ == "__main__":
    main()
