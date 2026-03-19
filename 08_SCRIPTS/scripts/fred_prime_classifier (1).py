
import os
import shutil
import json

# Load the folder structure
structure_file = "fred_prime_structure.json"
if not os.path.exists(structure_file):
    print(f"Structure file {structure_file} not found.")
    exit(1)

with open(structure_file, 'r') as f:
    category_map = json.load(f)

# Set base directory for sorted output
base_path = "F:/FRED-PRIME"
log_file_path = os.path.join(base_path, "master_log.txt")

# Ensure base path exists
os.makedirs(base_path, exist_ok=True)

# Initialize log file
with open(log_file_path, 'w', encoding='utf-8') as log:
    log.write("FRED-PRIME File Classification Log\n")
    log.write("="*60 + "\n\n")

# Function to classify a file by name or content
def classify_file(file_path):
    filename = os.path.basename(file_path).lower()
    matched_categories = set()
    
    # Try reading content (if text)
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read().lower()
    except:
        content = ""

    # Match by keywords
    for category, keywords in category_map.items():
        for keyword in keywords:
            if keyword in filename or keyword in content:
                matched_categories.add(category)
                break

    if not matched_categories:
        matched_categories.add("Misc")

    return matched_categories

# Walk through the drive and classify files
for root, dirs, files in os.walk("F:/", topdown=True):
    for name in files:
        try:
            full_path = os.path.join(root, name)
            categories = classify_file(full_path)

            for cat in categories:
                target_dir = os.path.join(base_path, cat)
                os.makedirs(target_dir, exist_ok=True)
                shutil.copy2(full_path, target_dir)

                with open(log_file_path, 'a', encoding='utf-8') as log:
                    log.write(f"FILE: {full_path}\n -> CATEGORY: {cat}\n")

        except Exception as e:
            with open(log_file_path, 'a', encoding='utf-8') as log:
                log.write(f"ERROR: {name} -> {str(e)}\n")

print("FRED-PRIME classification complete. Log saved to:", log_file_path)
