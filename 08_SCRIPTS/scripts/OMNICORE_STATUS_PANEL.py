import tkinter as tk
from pathlib import Path
import datetime

STATUS_DIR = "F:/SYSTEM/FLAGS"

def get_status():
    modules = [
        "auto_ingest",
        "motion_generator",
        "affidavit_generator",
        "exhibit_embedder",
        "binder_compiler",
        "zip_validator",
        "scao_overlay_autofill",
        "strikeback_chain"
    ]
    status = {}
    for mod in modules:
        p = Path(f"{STATUS_DIR}/{mod}.done")
        status[mod] = p.exists()
    return status

def build_panel():
    root = tk.Tk()
    root.title("OMNICORE MODULE STATUS")
    root.geometry("400x350")

    tk.Label(root, text="SYSTEM STATUS", font=("Arial", 14)).pack(pady=10)

    status = get_status()
    for mod, flag in status.items():
        color = "green" if flag else "red"
        label = f"{mod.replace('_', ' ').upper()} : {'OK' if flag else 'MISSING'}"
        tk.Label(root, text=label, fg=color, font=("Arial", 11)).pack()

    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    tk.Label(root, text=f"Checked: {now}", font=("Arial", 9)).pack(pady=10)

    root.mainloop()

if __name__ == "__main__":
    build_panel()
