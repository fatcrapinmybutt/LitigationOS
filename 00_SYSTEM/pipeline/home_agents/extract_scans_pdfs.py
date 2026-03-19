import os, sys, csv, json, re, time, hashlib
import warnings
warnings.filterwarnings("ignore")

SCANS = r"C:\Users\andre\Scans"
OUT = r"D:\LITIGATIONOS_DATA"
PROGRESS = r"D:\TEMP\pdf_progress.json"
BATCH_SIZE = 50

# Regex patterns (inline for speed)
MCR_PAT = re.compile(r'MCR\s*\d+\.\d+', re.IGNORECASE)
MCL_PAT = re.compile(r'MCL\s*\d+[\.\d]*', re.IGNORECASE)
CASE_PAT = re.compile(r'\d+\s+(?:Mich(?:\s*App)?|NW2d|NW\.?\s*2d)\s+\d+', re.IGNORECASE)
FED_PAT = re.compile(r'(?:42\s*U\.?S\.?C\.?\s*(?:§\s*)?\d+|28\s*U\.?S\.?C\.?\s*(?:§\s*)?\d+)', re.IGNORECASE)
USC_PAT = re.compile(r'\d+\s*U\.?S\.?C\.?\s*(?:§\s*)?\d+', re.IGNORECASE)
DATE_PAT = re.compile(r'\b(?:\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\w*\s+\d{1,2},?\s+\d{4})\b', re.IGNORECASE)

VIOL_PATS = {
    'contempt': re.compile(r'\bcontempt\b', re.I),
    'ex_parte': re.compile(r'\bex\s*parte\b', re.I),
    'due_process': re.compile(r'\bdue\s*process\b', re.I),
    'bias': re.compile(r'\b(?:bias|prejudic)', re.I),
    'fraud': re.compile(r'\bfraud', re.I),
    'misconduct': re.compile(r'\bmisconduct\b', re.I),
    'alienation': re.compile(r'\b(?:parental\s*alienat|alienat)', re.I),
    'perjury': re.compile(r'\bperjur', re.I),
    'coercion': re.compile(r'\bcoerci', re.I),
    'retaliation': re.compile(r'\bretali', re.I),
    'obstruction': re.compile(r'\bobstruct', re.I),
    'abuse_of_discretion': re.compile(r'\babuse\s*of\s*discretion\b', re.I),
    'denial_of_rights': re.compile(r'\bden(?:y|ied|ial)\s+(?:of\s+)?(?:right|access|parent)', re.I),
}

PERSON_PATS = {
    'Watson': re.compile(r'\bWatson\b'),
    'Pigors': re.compile(r'\bPigors\b'),
    'McNeill': re.compile(r'\bMcNeill\b', re.I),
    'Rusco': re.compile(r'\bRusco\b', re.I),
    'Martini': re.compile(r'\bMartini\b', re.I),
    'HealthWest': re.compile(r'\bHealthWest\b', re.I),
    'Bone': re.compile(r'\bDr\.?\s*Bone\b|\bRichard\s*Bone\b', re.I),
    'Randall': re.compile(r'\bRandall\b', re.I),
    'Lori Watson': re.compile(r'\bLori\b', re.I),
    'Albert Watson': re.compile(r'\bAlbert\b', re.I),
}

# Try multiple PDF libraries
pdf_lib = None
try:
    import pdfplumber
    pdf_lib = "pdfplumber"
except:
    pass
if not pdf_lib:
    try:
        from pdfminer.high_level import extract_text as pdfminer_extract
        pdf_lib = "pdfminer"
    except:
        pass
if not pdf_lib:
    try:
        import PyPDF2
        pdf_lib = "pypdf2"
    except:
        pass

print(f"PDF library: {pdf_lib}", flush=True)
if not pdf_lib:
    print("ERROR: No PDF library available", flush=True)
    sys.exit(1)

def extract_pdf_text(path, max_pages=200):
    try:
        if pdf_lib == "pdfplumber":
            text = []
            with pdfplumber.open(path) as pdf:
                for i, page in enumerate(pdf.pages[:max_pages]):
                    try:
                        t = page.extract_text()
                        if t:
                            text.append(t)
                    except:
                        pass
            return "\n".join(text)
        elif pdf_lib == "pdfminer":
            return pdfminer_extract(path, maxpages=max_pages)
        elif pdf_lib == "pypdf2":
            text = []
            with open(path, "rb") as f:
                reader = PyPDF2.PdfReader(f)
                for i, page in enumerate(reader.pages[:max_pages]):
                    try:
                        t = page.extract_text()
                        if t:
                            text.append(t)
                    except:
                        pass
            return "\n".join(text)
    except Exception as e:
        return ""

def get_context(lines, idx, width=1):
    start = max(0, idx - width)
    end = min(len(lines), idx + width + 1)
    return " ".join(lines[start:end]).strip()[:300]

# Load progress
done_files = set()
if os.path.exists(PROGRESS):
    with open(PROGRESS, "r") as f:
        done_files = set(json.load(f).get("done", []))
    print(f"Resuming: {len(done_files)} files already done", flush=True)

# Collect all PDFs
all_pdfs = []
for root, dirs, files in os.walk(SCANS):
    for fn in files:
        if fn.lower().endswith(".pdf"):
            all_pdfs.append(os.path.join(root, fn))

all_pdfs.sort()
remaining = [p for p in all_pdfs if p not in done_files]
print(f"Total PDFs: {len(all_pdfs)}, Already done: {len(done_files)}, Remaining: {len(remaining)}", flush=True)

# Open CSV files in append mode
cite_f = open(os.path.join(OUT, "MASTER_CITATIONS.csv"), "a", encoding="utf-8", newline="", errors="replace")
cite_w = csv.writer(cite_f)

viol_f = open(os.path.join(OUT, "MASTER_VIOLATIONS.csv"), "a", encoding="utf-8", newline="", errors="replace")
viol_w = csv.writer(viol_f)

time_f = open(os.path.join(OUT, "MASTER_TIMELINE.csv"), "a", encoding="utf-8", newline="", errors="replace")
time_w = csv.writer(time_f)

pers_f = open(os.path.join(OUT, "MASTER_PERSONS.csv"), "a", encoding="utf-8", newline="", errors="replace")
pers_w = csv.writer(pers_f)

evid_f = open(os.path.join(OUT, "MASTER_EVIDENCE_INDEX.csv"), "a", encoding="utf-8", newline="", errors="replace")
evid_w = csv.writer(evid_f)

total_chars = 0
total_cites = 0
total_viols = 0
total_dates = 0
total_persons = 0
files_done = 0
start_time = time.time()

for i, pdf_path in enumerate(remaining):
    rel = os.path.relpath(pdf_path, SCANS)
    dirname = os.path.dirname(rel)
    
    # Skip files > 50MB
    try:
        sz = os.path.getsize(pdf_path)
        if sz > 50_000_000:
            done_files.add(pdf_path)
            continue
    except:
        continue
    
    # Extract text with timeout guard
    try:
        text = extract_pdf_text(pdf_path)
    except:
        text = ""
    
    if not text:
        done_files.add(pdf_path)
        if (i+1) % 100 == 0:
            print(f"  [{i+1}/{len(remaining)}] (empty) {rel[:60]}", flush=True)
        continue
    
    total_chars += len(text)
    lines = text.split("\n")
    
    cite_count = 0
    viol_count = 0
    date_count = 0
    pers_count = 0
    
    for ln_num, line in enumerate(lines, 1):
        # Citations
        for m in MCR_PAT.finditer(line):
            cite_w.writerow([rel, dirname, "MCR", m.group(), ln_num, get_context(lines, ln_num-1)])
            cite_count += 1
        for m in MCL_PAT.finditer(line):
            cite_w.writerow([rel, dirname, "MCL", m.group(), ln_num, get_context(lines, ln_num-1)])
            cite_count += 1
        for m in CASE_PAT.finditer(line):
            cite_w.writerow([rel, dirname, "caselaw", m.group(), ln_num, get_context(lines, ln_num-1)])
            cite_count += 1
        for m in FED_PAT.finditer(line):
            cite_w.writerow([rel, dirname, "federal", m.group(), ln_num, get_context(lines, ln_num-1)])
            cite_count += 1
        for m in USC_PAT.finditer(line):
            if not FED_PAT.search(m.group()):
                cite_w.writerow([rel, dirname, "USC", m.group(), ln_num, get_context(lines, ln_num-1)])
                cite_count += 1
        
        # Violations
        for vtype, vpat in VIOL_PATS.items():
            if vpat.search(line):
                viol_w.writerow([rel, dirname, vtype, ln_num, get_context(lines, ln_num-1)])
                viol_count += 1
        
        # Dates
        for m in DATE_PAT.finditer(line):
            time_w.writerow([rel, dirname, m.group(), ln_num, get_context(lines, ln_num-1)])
            date_count += 1
        
        # Persons
        for pname, ppat in PERSON_PATS.items():
            if ppat.search(line):
                pers_w.writerow([rel, dirname, pname, ln_num, get_context(lines, ln_num-1)])
                pers_count += 1
    
    # Evidence index
    score = cite_count * 3 + viol_count * 5 + date_count + pers_count * 2
    evid_w.writerow([rel, dirname, cite_count, viol_count, date_count, pers_count, score])
    
    total_cites += cite_count
    total_viols += viol_count
    total_dates += date_count
    total_persons += pers_count
    files_done += 1
    done_files.add(pdf_path)
    
    if (i+1) % 50 == 0:
        # Flush CSVs
        cite_f.flush()
        viol_f.flush()
        time_f.flush()
        pers_f.flush()
        evid_f.flush()
        elapsed = time.time() - start_time
        rate = files_done / elapsed if elapsed > 0 else 0
        eta_min = (len(remaining) - i - 1) / rate / 60 if rate > 0 else 0
        print(f"  [{i+1}/{len(remaining)}] {files_done} extracted | {total_chars:,} chars | {total_cites} cites | {total_viols} viols | {rate:.1f} f/s | ETA {eta_min:.0f}m", flush=True)
        
        # Save progress
        with open(PROGRESS, "w") as pf:
            json.dump({"done": list(done_files), "stats": {
                "files_done": files_done, "total_chars": total_chars,
                "cites": total_cites, "viols": total_viols,
                "dates": total_dates, "persons": total_persons
            }}, pf)

# Close
for f in [cite_f, viol_f, time_f, pers_f, evid_f]:
    f.flush()
    f.close()

# Final save
with open(PROGRESS, "w") as pf:
    json.dump({"done": list(done_files), "stats": {
        "files_done": files_done, "total_chars": total_chars,
        "cites": total_cites, "viols": total_viols,
        "dates": total_dates, "persons": total_persons
    }}, pf)

elapsed = time.time() - start_time
print(f"\n=== SCANS PDF EXTRACTION COMPLETE ===", flush=True)
print(f"Files processed: {files_done}/{len(remaining)}", flush=True)
print(f"Total chars extracted: {total_chars:,}", flush=True)
print(f"Citations found: {total_cites:,}", flush=True)
print(f"Violations found: {total_viols:,}", flush=True)
print(f"Dates found: {total_dates:,}", flush=True)
print(f"Persons found: {total_persons:,}", flush=True)
print(f"Time: {elapsed:.0f}s ({elapsed/60:.1f}m)", flush=True)
print("DONE", flush=True)