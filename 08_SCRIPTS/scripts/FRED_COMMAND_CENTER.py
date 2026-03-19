
import tkinter as tk
from tkinter import ttk

class FREDCommandCenter(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("FRED COMMAND CENTER")
        self.geometry("1000x700")
        self.configure(bg="#1a1a1a")
        self.create_tabs()

    def create_tabs(self):
        style = ttk.Style()
        style.theme_use("default")
        style.configure("TNotebook", background="#1a1a1a", foreground="white", borderwidth=0)
        style.configure("TNotebook.Tab", background="#333", foreground="white", padding=10)
        style.map("TNotebook.Tab", background=[("selected", "#00ccff")])

        tab_control = ttk.Notebook(self)

        self.tab1 = ttk.Frame(tab_control)
        self.tab2 = ttk.Frame(tab_control)
        self.tab3 = ttk.Frame(tab_control)
        self.tab4 = ttk.Frame(tab_control)
        self.tab5 = ttk.Frame(tab_control)

        tab_control.add(self.tab1, text="📁 Case File Scanner")
        tab_control.add(self.tab2, text="📑 Decision Tree Output")
        tab_control.add(self.tab3, text="🧠 Motion Generator")
        tab_control.add(self.tab4, text="📊 Matrix & Evidence Viewer")
        tab_control.add(self.tab5, text="⚙️ Settings & Sync Tools")

        tab_control.pack(expand=1, fill="both")

        self.setup_tab1()
        self.setup_tab2()
        self.setup_tab3()
        self.setup_tab4()
        self.setup_tab5()

    def setup_tab1(self):
        tk.Label(self.tab1, text="Case File Scanner", font=("Arial", 16), bg="#1a1a1a", fg="#00ffcc").pack(pady=20)

    def setup_tab2(self):
        tk.Label(self.tab2, text="Decision Tree Output", font=("Arial", 16), bg="#1a1a1a", fg="#00ffcc").pack(pady=20)

    def setup_tab3(self):
        tk.Label(self.tab3, text="Motion Generator", font=("Arial", 16), bg="#1a1a1a", fg="#00ffcc").pack(pady=20)

    def setup_tab4(self):
        tk.Label(self.tab4, text="Matrix & Evidence Viewer", font=("Arial", 16), bg="#1a1a1a", fg="#00ffcc").pack(pady=20)

    def setup_tab5(self):
        tk.Label(self.tab5, text="Settings & Sync Tools", font=("Arial", 16), bg="#1a1a1a", fg="#00ffcc").pack(pady=20)

if __name__ == "__main__":
    app = FREDCommandCenter()
    app.mainloop()
