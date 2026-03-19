import os
import shutil
import zipfile
from pathlib import Path

# ========== CONFIG ==========
TARGET_DRIVE = "F:\\"
BASE_FOLDER = os.path.join(TARGET_DRIVE, "FRED-PRIME")
EMPTY_ARCHIVE = os.path.join(BASE_FOLDER, "Z_EMPTY_ARCHIVE")
MAX_FOLDERS = 100
MIN_FOLDERS = 40
SUBFOLDERS_PER_MAIN = 5
MAX_DEPTH = 3
# ============================

# Rule-based keyword mappings for categories
CATEGORY_KEYWORDS = {
    "Medical": ["vaccination", "pediatrics", "dentist", "medical"],
    "Police": ["police", "report", "sheriff", "incident"],
    "Custody": ["custody", "visitation", "parenting_time"],
    "PPO": ["ppo", "protection", "restraining"],
    "Financial": ["paystub", "insurance", "support", "bank", "income"],
    "Contempt": ["violation", "compliance", "contempt"],
    "LT": ["rent", "landlord", "eviction", "shady", "hoa"],
    "Witness": ["statement", "affidavit", "recommendation", "letter"],
    "AppClose": ["appclose", "communication", "co-parenting"],
    "Timeline": ["log", "timeline", "date"],
    "Photos": [".jpg", ".jpeg", ".png"],
    "Video": [".mp4", ".mov", ".avi"],
    "LegalDocs": [".pdf", ".docx", ".txt"],
    "FalseAllegations": ["false", "accusation", "perjury"],
    "JudicialBias": ["judge", "bias", "disqualify", "muted"],
    "Discovery": ["discovery", "subpoena", "interrogatories"],
    "Surveillance": ["camera", "footage", "surveil"],
    "Emails": ["email", "gmail", "outlook"],"Medical": ["vaccination", "pediatrics", "dentist", "medical", "clinic", "doctor", "immunization", "records", "checkup", "billing"],
"Police": ["police", "report", "sheriff", "incident", "dispatch", "officer", "investigation", "welfare_check", "complaint"],
"Custody": ["custody", "visitation", "parenting_time", "ece", "parental_rights", "722.27", "parenting_plan", "modification"],
"PPO": ["ppo", "protection", "restraining", "order", "harassment", "violation", "nocontact", "mcra", "motion_to_terminate"],
"Financial": ["paystub", "insurance", "support", "bank", "income", "tax", "irs", "employment", "benefits", "ledger", "childsupport", "reimbursement"],
"Contempt": ["violation", "compliance", "contempt", "enforcement", "mcl_552.644", "mcr_3.606", "sanctions"],
"LT": ["rent", "landlord", "eviction", "shady", "hoa", "lease", "meter", "sewer", "utilities", "homes_of_america", "code_violation", "constructive_eviction", "alden"],
"Witness": ["statement", "affidavit", "recommendation", "letter", "support_letter", "character_reference", "declaration"],
"AppClose": ["appclose", "communication", "co-parenting", "messaging", "log", "alienation", "scheduling", "exchange"],
"Timeline": ["log", "timeline", "date", "event", "incident", "calendar", "record", "milestone", "master_doc"],
"Photos": [".jpg", ".jpeg", ".png", "photo", "image", "snapshot"],
"Video": [".mp4", ".mov", ".avi", "video", "footage", "clip", "recording", "exchange_video"],
"LegalDocs": [".pdf", ".docx", ".txt", "motion", "order", "affidavit", "filing", "judgment", "pleading", "brief", "petition"],
"FalseAllegations": ["false", "accusation", "perjury", "fabricated", "lies", "misrepresentation", "malicious", "defamatory"],
"JudicialBias": ["judge", "bias", "disqualify", "muted", "irregularity", "misconduct", "prejudice", "favoritism", "exhibit_u"],
"Discovery": ["discovery", "subpoena", "interrogatories", "requests", "foia", "production", "evidence_request", "response"],
"Surveillance": ["camera", "footage", "surveil", "watch", "observe", "stalking", "monitor", "security"],
"Emails": ["email", "gmail", "outlook", "inbox", "sent", "thread", "header", "correspondence", "reply", "forward"],
"EvidenceMatrix": ["matrix", "index", "evidence_list", "scoring", "exhibit_index"],
"Exhibits": ["exhibit", "label", "attachment", "supporting_doc", "proof", "reference"],
"JudicialConduct": ["judicial", "conduct", "misconduct", "log", "irregularity", "mute", "zoom"],
"ChildNeglect": ["neglect", "medical_neglect", "dental_neglect", "school_absence", "failure_to_provide"],
"Sanctions": ["sanction", "rule11", "costs", "mcr_1.109", "frivolous"],
"Appeals": ["appeal", "reconsideration", "de_novo", "rehearing", "review", "coa", "supreme"],
"Insurance": ["medicaid", "bcbs", "claims", "health_insurance", "premium", "coverage", "employer_benefits"],
"HousingDisputes": ["meter", "sewer", "rent", "lot", "shady_oaks", "hoa", "lease_issues", "water", "maintenance"],
"Property": ["title", "ownership", "home", "dwelling", "mobile_home", "property_rights"],
"ChildSupport": ["support", "modification", "arrears", "insurance", "income", "deviation", "worksheet"],
"Procedural": ["mcl", "mcr", "statute", "case_law", "law", "benchbook", "court_rule", "form"],
"Scripts": ["script", ".py", ".ps1", ".bat", "automation", "ai", "scan", "compliance"],
"Audio": [".mp3", ".wav", ".ogg", "recording", "voicemail", "calllog"],
"Declarations": ["declaration", "verified", "statement", "support", "motion_support"],
"FOIA": ["foia", "freedom_of_information", "record_request", "data_request"],
"Misc": ["misc", "unsorted", "uncategorized", "to_sort", "unknown"],
"AlienationMatrix": ["alienation", "estrangement", "withholding", "hostile", "exchange", "emily_watson_behavior"],
"CentralDashboard": ["dashboard", "master_log", "control", "overview", "map"],
"GodModComplex": ["tactical", "supremacy", "god_mode", "ultimate", "unified", "fusion"],
"CrystalCores": ["crystal", "core", "crystal1", "crystal7", "protocol"],
"ExecuteSupremacy": ["supremacy", "dominate", "absolute", "protocol", "execution"],
"ComplianceAudit": ["audit", "review", "compliance", "checklist", "rule_validation"],
"CaseNumbers": ["20235907pp", "20241507dc", "25186592gc", "lt24-", "case_index"],
"FalseClaims": ["mental_health", "drug_use", "abuse", "erratic", "poisoning", "arsenic"],
"ParentingExchange": ["exchange", "handoff", "denial", "supervision", "emergency", "holiday"],
"Emergency": ["emergency", "welfare", "911", "urgent", "crisis", "call"],
"MasterDocs": ["master", "document", "bundle", "filing_packet", "master_narrative"],
}

def get_category(filename):
    name = filename.lower()
    for category, keywords in CATEGORY_KEYWORDS.items():
        if any(kw in name for kw in keywords):
            return category
    return "Uncategorized"

def unpack_zips(folder):
    for root, _, files in os.walk(folder):
        for file in files:
            if file.lower().endswith(".zip"):
                zip_path = os.path.join(root, file)
                extract_to = os.path.join(root, Path(file).stem)
                try:
                    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                        zip_ref.extractall(extract_to)
                    os.remove(zip_path)
                except Exception as e:
                    print(f"❌ Failed to extract {zip_path}: {e}")

def create_directory_tree():
    categories = list(CATEGORY_KEYWORDS.keys()) + ["Uncategorized"]
    folders_needed = max(MIN_FOLDERS, min(len(categories) * SUBFOLDERS_PER_MAIN, MAX_FOLDERS))

    created_paths = []
    for cat in categories:
        cat_folder = os.path.join(BASE_FOLDER, f"FRED-MODULE_{cat}")
        os.makedirs(cat_folder, exist_ok=True)
        created_paths.append(cat_folder)
        for i in range(1, SUBFOLDERS_PER_MAIN + 1):
            sub = os.path.join(cat_folder, f"Section-{i}")
            os.makedirs(sub, exist_ok=True)
            created_paths.append(sub)
    return created_paths

def organize_files():
    for root, _, files in os.walk(TARGET_DRIVE):
        if BASE_FOLDER.lower() in root.lower():
            continue
        for file in files:
            file_path = os.path.join(root, file)
            cat = get_category(file)
            dest_dir = os.path.join(BASE_FOLDER, f"FRED-MODULE_{cat}", "Section-1")
            os.makedirs(dest_dir, exist_ok=True)
            try:
                shutil.move(file_path, os.path.join(dest_dir, file))
            except Exception as e:
                print(f"❌ Couldn't move {file_path}: {e}")

def archive_empty_dirs():
    os.makedirs(EMPTY_ARCHIVE, exist_ok=True)
    for root, dirs, _ in os.walk(BASE_FOLDER, topdown=False):
        for d in dirs:
            dir_path = os.path.join(root, d)
            if not os.listdir(dir_path):
                try:
                    dest = os.path.join(EMPTY_ARCHIVE, os.path.basename(dir_path))
                    shutil.move(dir_path, dest)
                except Exception as e:
                    print(f"❌ Couldn't move empty folder {dir_path}: {e}")

# ========== MAIN EXECUTION ==========
print("🧠 Unpacking ZIPs...")
unpack_zips(TARGET_DRIVE)

print("🧱 Building folder structure...")
create_directory_tree()

print("📂 Organizing files...")
organize_files()

print("🧹 Archiving empty folders...")
archive_empty_dirs()

print("✅ COMPLETED: All files organized. Empty folders moved to Z_EMPTY_ARCHIVE.")
