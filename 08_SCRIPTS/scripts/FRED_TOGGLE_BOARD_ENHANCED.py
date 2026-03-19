
import tkinter as tk
from tkinter import messagebox, filedialog
import subprocess
import os
import json
import random

# Full registry of modules
MODULES = {
    "Motion Packet Generator": "./_ENGINES/Motion_Packet_Generator_Engine/module_task.py",
    "Violation Response Engine": "./_ENGINES/Violation_Response_Engine/module_task.py",
    "Evidence Weighing Core": "./_CORES/Evidence_Weighing_Core/module_task.py",
    "Contempt Trigger Workflow": "./_WORKFLOWS/Contempt_Trigger_Workflow/module_task.py",
    "AppClose Analyzer Plugin": "./_PLUGINS/AppClose_Analyzer_Plugin/module_task.py",
    "Trigger Heatmap Dashboard": "./_DASHBOARDS/Trigger_Heatmap_Dashboard/module_task.py",
    "Statute Breach Pipeline": "./_PIPELINES/Statute_Breach_Pipeline/module_task.py",
    "Case Masterlist Core": "./_MASTERLISTS/Case_Masterlist/module_task.py",
    "Test Simulation System": "./_SYSTEMS/Test_Simulation_System/module_task.py",
    "Automation Trigger Daemon": "./_SYSTEMS/Automation_Trigger_Daemon/module_task.py",
    "Master Loader": "./FRED_CASE_MASTER_LOADER.py",
    "Evidence Report Generator": "./Generate_Evidence_Report.py",
    "Plugin Signature Validator": "./_PLUGINS/Plugin_Signature_Validator.py"
}

module_vars = {}

def run_selected():
    selected = [name for name, var in module_vars.items() if var.get()]
    if not selected:
        messagebox.showwarning("Warning", "No modules selected.")
        return

    results = []
    for name in selected:
        try:
            subprocess.run(["python", MODULES[name]], check=True)
            results.append(f"✓ {name}")
        except Exception as e:
            results.append(f"⚠ {name} failed")

    messagebox.showinfo("Execution Results", "\n".join(results))

def save_preset():
    selected = [name for name, var in module_vars.items() if var.get()]
    if not selected:
        messagebox.showwarning("Warning", "No modules selected.")
        return
    preset_path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON Files", "*.json")])
    if preset_path:
        with open(preset_path, 'w') as f:
            json.dump(selected, f)
        messagebox.showinfo("Preset Saved", f"Preset saved to {preset_path}")

def load_preset():
    preset_path = filedialog.askopenfilename(filetypes=[("JSON Files", "*.json")])
    if preset_path:
        with open(preset_path, 'r') as f:
            selected = json.load(f)
        for name, var in module_vars.items():
            var.set(name in selected)
        messagebox.showinfo("Preset Loaded", f"Preset loaded from {preset_path}")

def randomize_selection():
    for name, var in module_vars.items():
        var.set(random.choice([True, False]))

def smart_combo(case_type):
    smart_map = {
        "ppo": ["Violation Response Engine", "Evidence Weighing Core", "Trigger Heatmap Dashboard"],
        "custody": ["Contempt Trigger Workflow", "AppClose Analyzer Plugin", "Case Masterlist Core"],
        "support": ["Motion Packet Generator", "Evidence Report Generator"],
        "default": ["Master Loader", "Automation Trigger Daemon"]
    }
    combo = smart_map.get(case_type.lower(), smart_map["default"])
    for name, var in module_vars.items():
        var.set(name in combo)

# GUI Setup
root = tk.Tk()
root.title("FRED-PRIME ULTRA TOGGLE BOARD – ENHANCED")
root.geometry("700x700")

tk.Label(root, text="Toggle Tools to Combine", font=("Helvetica", 14)).pack(pady=10)
frame = tk.Frame(root)
frame.pack(pady=10)

for name in MODULES:
    var = tk.BooleanVar()
    chk = tk.Checkbutton(frame, text=name, variable=var, font=("Helvetica", 10), anchor="w", width=60)
    chk.pack(anchor="w")
    module_vars[name] = var

# Button Controls
tk.Button(root, text="🧠 Run Selected Modules", font=("Helvetica", 12), command=run_selected).pack(pady=10)
tk.Button(root, text="💾 Save Preset", command=save_preset).pack()
tk.Button(root, text="📂 Load Preset", command=load_preset).pack()
tk.Button(root, text="🔀 Randomize Selection", command=randomize_selection).pack()
tk.Button(root, text="🧬 Smart Combo: PPO", command=lambda: smart_combo("ppo")).pack()
tk.Button(root, text="🧬 Smart Combo: Custody", command=lambda: smart_combo("custody")).pack()
tk.Button(root, text="🧬 Smart Combo: Support", command=lambda: smart_combo("support")).pack()
tk.Button(root, text="Exit", font=("Helvetica", 10), command=root.destroy).pack(pady=10)

root.mainloop()
