
import re
from pathlib import Path

# === SMART CLASSIFIER ===

CATEGORY_KEYWORDS = {
    "Leases_Contracts": [r"lease", r"rental", r"agreement", r"terms", r"occupancy"],
    "Utility_Ledgers": [r"utility", r"bill", r"zego", r"invoice", r"statement"],
    "CourtOrders_Judgments": [r"order", r"judgment", r"disposition", r"motion_granted", r"show_cause"],
    "Photos_MetadataAnchored": [r".*\.(jpg|jpeg|png|bmp|heic)$"],
    "Communications_Text_Email_AppClose": [r"text", r"email", r"appclose", r"sms", r"messenger"],
    "Affidavits_SwornStatements": [r"affidavit", r"sworn", r"notary", r"statement", r"verified"],
    "EntityFraud_CorporateDocs": [r"llc", r"lara", r"registered", r"entity", r"assignment", r"transfer"],
    "FOC_ChildSupport_Documents": [r"friend_of_court", r"foc", r"support", r"child", r"arrears"],
    "PPO_Contempt_CourtFilings": [r"ppo", r"contempt", r"violation", r"hearing", r"respondent"],
    "EvidenceUnclassified_AuditQueue": []
}

def classify_file(filename: str) -> str:
    name = filename.lower()
    for category, patterns in CATEGORY_KEYWORDS.items():
        for pat in patterns:
            if re.search(pat, name):
                return category
    return "EvidenceUnclassified_AuditQueue"

def classify_path(filepath: Path) -> str:
    return classify_file(filepath.name)

# === EXAMPLE USAGE ===
if __name__ == "__main__":
    test_files = [
        "2025_05_15_rent_ledger_zego.pdf",
        "order_show_cause_contempt_hearing.pdf",
        "Lease_Agreement_Signed_2024.pdf",
        "sworn_affidavit_may2025.docx",
        "photo_evidence_ppo.jpg",
        "text_thread_export_appclose.txt",
        "lara_entity_report_homesofamerica.pdf"
    ]
    for test in test_files:
        result = classify_file(test)
        print(f"{test} → {result}")
