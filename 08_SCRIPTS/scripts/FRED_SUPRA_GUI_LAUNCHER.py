
import tkinter as tk
from tkinter import messagebox
import subprocess
import os

# Define scripts for each function
scripts = {
    "Run Full Pipeline": "super_pipeline_v2.py",
    "Convert to DOCX": "ConvertToDocx.py",
    "Generate Complaint": "AutoComplaintGenerator.py",
    "Generate Proposed Order": "AutoProposedOrderGenerator.py",
    "Generate Show Cause Motion": "AutoShowCauseMotionGenerator.py"
}

def run_script(script_name):
    script = scripts.get(script_name)
    if script and os.path.exists(script):
        try:
            subprocess.run(["python", script], check=True)
            messagebox.showinfo("Success", f"{script_name} completed successfully.")
        except subprocess.CalledProcessError:
            messagebox.showerror("Error", f"Failed to run {script}.")
    else:
        messagebox.showerror("Error", f"{script} not found.")

# GUI setup
root = tk.Tk()
root.title("FRED_SUPRA_GUI_LAUNCHER")
root.geometry("400x300")

title = tk.Label(root, text="FRED SUPRA LITIGATION OS", font=("Helvetica", 14, "bold"))
title.pack(pady=20)

for name in scripts.keys():
    btn = tk.Button(root, text=name, command=lambda n=name: run_script(n), width=30, height=2)
    btn.pack(pady=5)

exit_btn = tk.Button(root, text="Exit", command=root.quit, width=30, height=2, bg="red", fg="white")
exit_btn.pack(pady=10)

root.mainloop()
