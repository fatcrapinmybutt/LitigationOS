
import os
import shutil
import json

# Load the folder structure
with open('fred_prime_structure.json', 'r') as f:
    category_map = json.load(f)

# Set base directory (change to your actual base path)
base_path = "F:/FRED-PRIME"
log_file_path = os.path.join(base_path, "master_log.txt")

# Ensure base path exists
os.makedirs(base_path, exist_ok=True)

# Initialize log
with open(log_file_path, 'w') as log:
    log.write("FRED-PRIME File Classification Log\n")
    log.write("="*60 + "\n\n")

# Function to classify a file
def classify_file(file_path):
    filename = os.path.basename(file_path).lower()
    try:
        with open(file_path, 'r', errors='ignore') as f:
            content = f.read().lower()
    except:
        content = ""

    matched_categories = set()
    for category, keywords in category_map.items():
        for keyword in keywords:
            if keyword.lower() in filename or keyword.lower() in content:
                matched_categories.add(category)
                break  # avoid duplicate categories for same keyword

    if not matched_categories:
        matched_categories.add("Misc")

    return matched_categories

# Walk through the drive
for root, dirs, files in os.walk("F:/", topdown=True):
    for name in files:
        try:
            full_path = os.path.join(root, name)
            categories = classify_file(full_path)

            for cat in categories:
                target_dir = os.path.join(base_path, cat)
                os.makedirs(target_dir, exist_ok=True)
                shutil.copy2(full_path, target_dir)

                with open(log_file_path, 'a') as log:
                    log.write(f"FILE: {full_path}\n -> CATEGORY: {cat}\n")

        except Exception as e:
            with open(log_file_path, 'a') as log:
                log.write(f"ERROR: {name} -> {str(e)}\n")

print("FRED-PRIME classification completed. Log saved to:", log_file_path)
