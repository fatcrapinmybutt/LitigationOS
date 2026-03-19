# Begin injection of final V3 modules (AI Semantic Tagger, Form Matcher, etc.)

final_modules = """
# === AI SEMANTIC TAGGER ===
def semantic_tag(text):
    tags = []
    categories = {
        "[CUSTODY]": ["parenting time", "custody", "visitation"],
        "[SUPPORT]": ["child support", "arrears", "obligation"],
        "[PPO]": ["personal protection", "PPO", "show cause"],
        "[DUE PROCESS]": ["notice", "hearing", "right to be heard"],
        "[CONTEMPT]": ["contempt", "violation", "sanction"],
        "[FINANCIAL]": ["ledger", "rent", "payment", "utilities"],
    }
    for tag, keywords in categories.items():
        if any(word in text.lower() for word in keywords):
            tags.append(tag)
    return tags

# === FORM MATCH ENGINE ===
def form_match(text):
    if "support" in text.lower():
        return "FOC10, FOC50"
    elif "custody" in text.lower() or "parenting time" in text.lower():
        return "FOC87, FOC89"
    elif "protection" in text.lower() or "PPO" in text.lower():
        return "CC 375, CC 382"
    else:
        return "N/A"

# === MOTION SHELL GENERATOR ===
def motion_suggestion(text):
    if "denied" in text.lower() and "custody" in text.lower():
        return "Motion for Reconsideration of Custody (MCR 2.119(F))"
    elif "PPO" in text and "violation" in text:
        return "Motion to Terminate PPO or Show Cause Defense"
    return "No suggestion"

# === CHAIN OF CUSTODY METADATA ===
def embed_metadata(file_path, sha256):
    meta_path = os.path.join(file_path + ".meta.txt")
    with open(meta_path, "w", encoding="utf-8") as f:
        f.write(f"SHA-256: {sha256}\\n")
        f.write(f"Scanned: {datetime.now().isoformat()}\\n")
        f.write(f"Original Path: {file_path}\\n")

# === RED FLAG EXTRACTOR ===
def extract_red_flags(text):
    flags = []
    triggers = ["supervised", "denied", "no contact", "harassment", "abuse", "emergency"]
    for word in triggers:
        if word in text.lower():
            flags.append(word)
    return flags

# === AUDIO + IMAGE EXTRACTOR ===
def scan_for_audio_image(file_path):
    ext = file_path.lower().split(".")[-1]
    if ext in ["mp3", "wav", "m4a"]:
        dest = os.path.join(AUDIO_DIR, os.path.basename(file_path))
        os.rename(file_path, dest)
        log(f"Audio extracted: {file_path}")
    elif ext in ["jpg", "jpeg", "png", "tiff", "bmp"]:
        dest = os.path.join(IMAGE_DIR, os.path.basename(file_path))
        os.rename(file_path, dest)
        log(f"Image extracted: {file_path}")

# === TIMELINE VISUALIZER (HTML) ===
def generate_timeline_html():
    html_path = os.path.join(LOCAL_FRED, "timeline_visual.html")
    try:
        with open(TIMELINE_FILE, "r", encoding="utf-8") as csvfile, open(html_path, "w", encoding="utf-8") as html:
            reader = csv.reader(csvfile)
            next(reader)
            html.write("<html><head><title>Legal Timeline</title></head><body><h1>Legal Timeline</h1><ul>")
            for row in reader:
                html.write(f"<li><b>{row[1]}</b>: {row[2]} from <i>{row[0]}</i></li>")
            html.write("</ul></body></html>")
        log("Timeline HTML generated.")
    except Exception as e:
        log(f"Timeline HTML generation failed: {e}")
"""

# Append final modules
with open(v3_path, "a", encoding="utf-8") as f:
    f.write("\n\n# === FINAL SYSTEM MODULES ===\n" + final_modules.strip())

v3_path
