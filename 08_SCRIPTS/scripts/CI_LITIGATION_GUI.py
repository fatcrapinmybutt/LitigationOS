
import tkinter as tk
from tkinter import messagebox
import os
from CI_AUTOMATION_LAYER import trigger_pipeline, fetch_ci_metrics

# --- GUI Functions ---
def trigger_ci():
    try:
        trigger_pipeline("2025-002760-CZ", "MiFile")
        messagebox.showinfo("Success", "CI Pipeline Triggered!")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to trigger pipeline: {e}")

def show_metrics():
    try:
        metrics = fetch_ci_metrics()
        metrics_str = "\n".join([f"{k}: {v}" for k, v in metrics.get('org_data', {}).get('metrics', {}).items()])
        messagebox.showinfo("CI Metrics", metrics_str or "No metrics available.")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to fetch metrics: {e}")

# --- GUI Setup ---
root = tk.Tk()
root.title("LITIGATION OS: CI Control Panel")
root.geometry("400x300")
root.configure(bg="#1e1e1e")

tk.Label(root, text="⚖️ Litigation CI Control Panel", fg="#ffffff", bg="#1e1e1e", font=("Arial", 14)).pack(pady=10)

tk.Button(root, text="🚀 Trigger CircleCI Build", font=("Arial", 12), width=30, command=trigger_ci).pack(pady=10)
tk.Button(root, text="📊 View CircleCI Metrics", font=("Arial", 12), width=30, command=show_metrics).pack(pady=10)

tk.Label(root, text="Case: 2025-002760-CZ", fg="#aaaaaa", bg="#1e1e1e", font=("Arial", 10)).pack(side="bottom", pady=10)
root.mainloop()
