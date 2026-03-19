
import tkinter as tk
from tkinter import messagebox
import subprocess
import os

# Central registry of modules/systems/cores
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

# GUI Window
root = tk.Tk()
root.title("FRED-PRIME ULTRA TOGGLE BOARD")
root.geometry("600x600")

tk.Label(root, text="Toggle Tools to Combine", font=("Helvetica", 14)).pack(pady=10)

frame = tk.Frame(root)
frame.pack(pady=10)

for name in MODULES:
    var = tk.BooleanVar()
    chk = tk.Checkbutton(frame, text=name, variable=var, font=("Helvetica", 10), anchor="w", width=50)
    chk.pack(anchor="w")
    module_vars[name] = var

tk.Button(root, text="🧠 Run Selected Modules", font=("Helvetica", 12), command=run_selected).pack(pady=20)
tk.Button(root, text="Exit", font=("Helvetica", 10), command=root.destroy).pack(pady=5)

root.mainloop()
