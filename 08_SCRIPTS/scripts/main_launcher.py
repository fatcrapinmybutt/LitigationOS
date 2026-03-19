
import json
import os
import subprocess
import tkinter as tk
from tkinter import messagebox

# Load registry
try:
    with open("THE_PROGRAM_REGISTRY.json", "r") as f:
        registry = json.load(f)
except FileNotFoundError:
    registry = {"components": []}

class TheProgramGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("THE PROGRAM – Launcher Core")
        self.geometry("700x600")
        self.configure(bg="#1e1e1e")
        self.create_widgets()

    def create_widgets(self):
        tk.Label(self, text="THE PROGRAM MODULE MENU", font=("Arial", 18, "bold"), fg="#00ffcc", bg="#1e1e1e").pack(pady=10)

        self.listbox = tk.Listbox(self, width=80, height=25, selectmode=tk.MULTIPLE, bg="#121212", fg="#ffffff", font=("Courier", 10))
        self.listbox.pack(pady=10)

        for component in registry.get("components", []):
            self.listbox.insert(tk.END, component)

        button_frame = tk.Frame(self, bg="#1e1e1e")
        button_frame.pack(pady=20)

        activate_btn = tk.Button(button_frame, text="Activate Selected", command=self.activate_selected, bg="#00ffcc", fg="black")
        deactivate_btn = tk.Button(button_frame, text="Deactivate Selected", command=self.deactivate_selected, bg="#ff6666", fg="white")

        activate_btn.grid(row=0, column=0, padx=10)
        deactivate_btn.grid(row=0, column=1, padx=10)

    def activate_selected(self):
        selected = [self.listbox.get(i) for i in self.listbox.curselection()]
        results = []
        for item in selected:
            result = self.run_module(item)
            results.append(f"{item}: {result}")
        messagebox.showinfo("Activation", "\n".join(results))

    def deactivate_selected(self):
        selected = [self.listbox.get(i) for i in self.listbox.curselection()]
        for item in selected:
            print(f"[DEACTIVATE] {item}")
        messagebox.showinfo("Deactivation", f"Deactivated: {', '.join(selected)}")

    def run_module(self, module_name):
        name = module_name.lower().replace(' ', '_')
        candidates = [f"{name}.py", f"{name}.exe", f"{name}.json"]
        for fname in candidates:
            if os.path.exists(fname):
                try:
                    if fname.endswith(".py"):
                        subprocess.Popen(["python", fname])
                    elif fname.endswith(".exe"):
                        subprocess.Popen([fname])
                    elif fname.endswith(".json"):
                        os.startfile(fname)
                    return f"✓ Launched {fname}"
                except Exception as e:
                    return f"✗ Failed to launch {fname} ({str(e)})"
        return "✗ No executable or script found."

if __name__ == "__main__":
    app = TheProgramGUI()
    app.mainloop()
