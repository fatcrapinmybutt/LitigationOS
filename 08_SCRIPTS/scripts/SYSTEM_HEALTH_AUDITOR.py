import logging
from pathlib import Path

def audit_modules():
    logging.basicConfig(filename="F:/LITIGATION_DRIVE/LEGAL_RESULTS/log_system_auditor.txt", level=logging.INFO)
    required_flags = [
        "auto_ingest", "motion_generator", "affidavit_generator",
        "exhibit_embedder", "binder_compiler", "zip_validator",
        "scao_overlay_autofill", "strikeback_chain", "mifile_packager"
    ]

    missing = []
    for mod in required_flags:
        f = Path(f"F:/SYSTEM/FLAGS/{mod}.done")
        if not f.exists():
            missing.append(mod)

    if missing:
        logging.warning(f"[!] Missing flags: {', '.join(missing)}")
    else:
        logging.info("[✓] All modules accounted for.")

    Path("F:/SYSTEM/FLAGS/system_health_auditor.done").touch()

if __name__ == "__main__":
    audit_modules()
