import tkinter as tk
from tkinter import messagebox
import os

def start_system():
    # Placeholder — hook into your litigation OS logic
    messagebox.showinfo("FRED System", "Litigation Control Panel Engaged.")

app = tk.Tk()
app.title("FRED Master GUI")
app.geometry("400x200")
app.iconbitmap("FRED_Master_GUI.ico")

label = tk.Label(app, text="FRED Litigation System Launcher", font=("Arial", 14))
label.pack(pady=20)

start_button = tk.Button(app, text="Launch System", command=start_system)
start_button.pack(pady=10)

app.mainloop()
