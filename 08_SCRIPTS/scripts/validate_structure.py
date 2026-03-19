import os

base_path = "F:/FRED-PRIME"

required_folders = [
    "EvidenceMatrix",
    "ExhibitSets",
    "OCR_Input",
    "MotionTemplates",
    "ProposedOrders",
    "CertificatesOfService",
    "CaseFiles",
    "PPO_Defense",
    "Custody_Modifications",
    "Support_Calculations",
    "Benchbook_References",
    "AppClose_Logs",
    "Alienation_Tracker",
    "JudicialPatternLogs",
    "Sanctions_Motions",
    "Federal_Escalation",
    "Compiled_Motions",
    "PDF_Output",
    "UserInterface",
    "Logs",
    "Triggers"
]

missing = []

print(f"🔍 Validating FRED-PRIME structure at {base_path}...")

for folder in required_folders:
    path = os.path.join(base_path, folder)
    if not os.path.exists(path):
        missing.append(folder)

if missing:
    print("❌ Missing folders:")
    for folder in missing:
        print(f"- {folder}")
else:
    print("✅ All required folders are present.")

# Optionally write to log
log_path = os.path.join(base_path, "Logs", "structure_audit_log.txt")
os.makedirs(os.path.dirname(log_path), exist_ok=True)
with open(log_path, "w") as f:
    if missing:
        f.write("MISSING DIRECTORIES:\n")
        f.write("\n".join(missing))
    else:
        f.write("All required folders exist. Structure validated successfully.")
