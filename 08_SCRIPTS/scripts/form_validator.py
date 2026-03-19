import json
import os

MCR_FORMS_MAP = {
    "motion for custody": {"mcr": "2.119", "form": "FOC 87"},
    "ex parte motion": {"mcr": "3.207(B)", "form": "MC 231"},
    "motion to modify support": {"mcr": "3.207(C)", "form": "FOC 115"},
    "motion to dismiss": {"mcr": "2.504", "form": "MC 09"},
    "motion for contempt": {"mcr": "3.606(A)", "form": "FOC 22"}
}

def validate_forms(input_dir, output_path):
    violations = []
    for file in os.listdir(input_dir):
        fname = file.lower()
        for keyword, refs in MCR_FORMS_MAP.items():
            if keyword in fname:
                if refs["form"].lower() not in fname:
                    violations.append({
                        "file": file,
                        "issue": "Missing correct form",
                        "expected_form": refs["form"],
                        "required_mcr": refs["mcr"]
                    })
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(violations, f, indent=2)

if __name__ == "__main__":
    validate_forms("F:/Filings", "./output/form_validation_log.json")