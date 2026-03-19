#!/usr/bin/env python3
from __future__ import annotations

import os
import sys
import json
import threading
import queue
from pathlib import Path
from dataclasses import dataclass
from datetime import datetime

import tkinter as tk
from tkinter import ttk, filedialog, messagebox

# Import the two lanes as modules
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

# Local lane module
sys.path.insert(0, str(HERE / "LOCAL"))
# GDrive lane module
sys.path.insert(0, str(HERE / "GDRIVE"))

import ai_organizer_stack as local_lane
import gdrive_scoped_organizer as gdrive_lane

APP_NAME = "OrganizerStudio"
APP_VERSION = "2026-01-23-PRO1"

def now_stamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")

def default_f_root() -> Path:
    return Path("F:/LitigationOS/_OrganizeAI/STUDIO")

@dataclass
class RunResult:
    ok: bool
    code: int
    stdout: str

class LogSink:
    def __init__(self, text_widget: tk.Text):
        self.text = text_widget
        self.q: "queue.Queue[str]" = queue.Queue()

    def write(self, s: str) -> None:
        self.q.put(s)

    def flush(self) -> None:
        pass

    def pump(self) -> None:
        try:
            while True:
                s = self.q.get_nowait()
                self.text.insert("end", s)
                self.text.see("end")
        except queue.Empty:
            return

class OrganizerStudio(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title(f"{APP_NAME} {APP_VERSION}")
        self.geometry("1100x720")
        self.minsize(1000, 650)

        self.state_path = default_f_root() / "state.json"
        self.state: dict = self._load_state()

        self._build_ui()

        self.after(120, self._tick)

    def _load_state(self) -> dict:
        try:
            if self.state_path.exists():
                return json.loads(self.state_path.read_text(encoding="utf-8"))
        except Exception:
            pass
        return {
            "last_local_roots": ["F:/"],
            "last_gdrive_root_id": "",
            "last_plan_path": "",
            "last_undo_path": "",
        }

    def _save_state(self) -> None:
        try:
            self.state_path.parent.mkdir(parents=True, exist_ok=True)
            self.state_path.write_text(json.dumps(self.state, indent=2), encoding="utf-8")
        except Exception:
            return

    def _build_ui(self) -> None:
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True)

        self.tab_local = ttk.Frame(self.notebook)
        self.tab_gdrive = ttk.Frame(self.notebook)
        self.tab_runs = ttk.Frame(self.notebook)

        self.notebook.add(self.tab_local, text="LOCAL")
        self.notebook.add(self.tab_gdrive, text="GDRIVE")
        self.notebook.add(self.tab_runs, text="RUNS AND LOGS")

        self._build_local_tab()
        self._build_gdrive_tab()
        self._build_runs_tab()

    def _build_local_tab(self) -> None:
        f = self.tab_local

        top = ttk.Frame(f)
        top.pack(fill="x", padx=12, pady=10)

        ttk.Label(top, text="Roots to organize (semicolon separated)").grid(row=0, column=0, sticky="w")
        self.local_roots_var = tk.StringVar(value=";".join(self.state.get("last_local_roots", ["F:/"])))
        self.local_roots_entry = ttk.Entry(top, textvariable=self.local_roots_var, width=90)
        self.local_roots_entry.grid(row=1, column=0, sticky="we", padx=(0, 8))

        ttk.Button(top, text="Add Folder", command=self._local_add_folder).grid(row=1, column=1, sticky="e")
        top.columnconfigure(0, weight=1)

        cfg_box = ttk.LabelFrame(f, text="LOCAL config")
        cfg_box.pack(fill="x", padx=12, pady=(0, 10))

        self.local_cfg_path = Path("LOCAL/config.yaml")
        ttk.Label(cfg_box, text="config.yaml path").grid(row=0, column=0, sticky="w", padx=8, pady=6)
        self.local_cfg_entry = ttk.Entry(cfg_box, width=90)
        self.local_cfg_entry.insert(0, str(self.local_cfg_path))
        self.local_cfg_entry.grid(row=0, column=1, sticky="we", padx=8, pady=6)
        ttk.Button(cfg_box, text="Open", command=lambda: self._open_path(self.local_cfg_entry.get())).grid(row=0, column=2, padx=8, pady=6)

        btns = ttk.Frame(f)
        btns.pack(fill="x", padx=12, pady=8)

        ttk.Button(btns, text="PLAN", command=self._local_plan).pack(side="left", padx=6)
        ttk.Button(btns, text="VALIDATE", command=self._validate_any).pack(side="left", padx=6)
        ttk.Button(btns, text="APPLY", command=self._apply_any).pack(side="left", padx=6)
        ttk.Button(btns, text="UNDO LAST", command=self._local_undo_last).pack(side="left", padx=6)

        self._build_log_area(f)

    def _build_gdrive_tab(self) -> None:
        f = self.tab_gdrive

        top = ttk.Frame(f)
        top.pack(fill="x", padx=12, pady=10)

        ttk.Label(top, text="Scoped Drive folder ID (must not be root)").grid(row=0, column=0, sticky="w")
        self.gdrive_root_var = tk.StringVar(value=self.state.get("last_gdrive_root_id", ""))
        self.gdrive_root_entry = ttk.Entry(top, textvariable=self.gdrive_root_var, width=60)
        self.gdrive_root_entry.grid(row=1, column=0, sticky="w", padx=(0, 8))

        ttk.Label(top, text="config.yaml").grid(row=0, column=1, sticky="w")
        self.gdrive_cfg_entry = ttk.Entry(top, width=50)
        self.gdrive_cfg_entry.insert(0, "GDRIVE/config.yaml")
        self.gdrive_cfg_entry.grid(row=1, column=1, sticky="we", padx=(0, 8))
        ttk.Button(top, text="Open", command=lambda: self._open_path(self.gdrive_cfg_entry.get())).grid(row=1, column=2, sticky="e")

        top.columnconfigure(1, weight=1)

        btns = ttk.Frame(f)
        btns.pack(fill="x", padx=12, pady=8)
        ttk.Button(btns, text="PLAN", command=self._gdrive_plan).pack(side="left", padx=6)
        ttk.Button(btns, text="VALIDATE", command=self._validate_any).pack(side="left", padx=6)
        ttk.Button(btns, text="APPLY", command=self._apply_any).pack(side="left", padx=6)
        ttk.Button(btns, text="UNDO", command=self._gdrive_undo).pack(side="left", padx=6)

        self._build_log_area(f)

    def _build_runs_tab(self) -> None:
        f = self.tab_runs
        box = ttk.Frame(f)
        box.pack(fill="both", expand=True, padx=12, pady=10)

        ttk.Label(box, text="Open the run roots on disk").pack(anchor="w")

        rows = ttk.Frame(box)
        rows.pack(fill="x", pady=8)

        ttk.Button(rows, text="Open LOCAL runs", command=lambda: self._open_path("F:/LitigationOS/_OrganizeAI/LOCAL")).pack(side="left", padx=6)
        ttk.Button(rows, text="Open GDRIVE runs", command=lambda: self._open_path("F:/LitigationOS/_OrganizeAI/GDRIVE")).pack(side="left", padx=6)
        ttk.Button(rows, text="Open STUDIO state", command=lambda: self._open_path(str(default_f_root()))).pack(side="left", padx=6)

        info = ttk.LabelFrame(box, text="Last paths")
        info.pack(fill="x", pady=10)

        self.last_plan_var = tk.StringVar(value=self.state.get("last_plan_path",""))
        self.last_undo_var = tk.StringVar(value=self.state.get("last_undo_path",""))

        ttk.Label(info, text="Last plan path").grid(row=0, column=0, sticky="w", padx=8, pady=6)
        ttk.Entry(info, textvariable=self.last_plan_var, width=110).grid(row=0, column=1, sticky="we", padx=8, pady=6)

        ttk.Label(info, text="Last undo path").grid(row=1, column=0, sticky="w", padx=8, pady=6)
        ttk.Entry(info, textvariable=self.last_undo_var, width=110).grid(row=1, column=1, sticky="we", padx=8, pady=6)

        info.columnconfigure(1, weight=1)

        ttk.Button(box, text="Validate last plan", command=self._validate_any).pack(anchor="w", padx=4)
        ttk.Button(box, text="Apply last plan", command=self._apply_any).pack(anchor="w", padx=4)
        ttk.Button(box, text="Undo last undo", command=self._undo_last_any).pack(anchor="w", padx=4)

    def _build_log_area(self, parent: ttk.Frame) -> None:
        pane = ttk.PanedWindow(parent, orient="vertical")
        pane.pack(fill="both", expand=True, padx=12, pady=(6, 10))

        frame = ttk.Frame(pane)
        pane.add(frame, weight=3)

        self.log_text = tk.Text(frame, height=20, wrap="word")
        self.log_text.pack(side="left", fill="both", expand=True)
        sb = ttk.Scrollbar(frame, command=self.log_text.yview)
        sb.pack(side="right", fill="y")
        self.log_text.configure(yscrollcommand=sb.set)

        self.log_sink = LogSink(self.log_text)

        status = ttk.Frame(pane)
        pane.add(status, weight=1)

        self.status_var = tk.StringVar(value="Ready")
        ttk.Label(status, textvariable=self.status_var).pack(anchor="w", padx=6, pady=6)

        self.progress = ttk.Progressbar(status, mode="indeterminate")
        self.progress.pack(fill="x", padx=6, pady=6)

    def _tick(self) -> None:
        if hasattr(self, "log_sink"):
            self.log_sink.pump()
        self.after(120, self._tick)

    def _open_path(self, p: str) -> None:
        try:
            path = Path(p)
            if not path.exists():
                messagebox.showwarning("Missing", f"Path not found:\n{p}")
                return
            if os.name == "nt":
                os.startfile(str(path))
            else:
                messagebox.showinfo("Open", str(path))
        except Exception as e:
            messagebox.showerror("Open error", str(e))

    def _local_add_folder(self) -> None:
        d = filedialog.askdirectory()
        if not d:
            return
        roots = [x for x in self.local_roots_var.get().split(";") if x.strip()]
        roots.append(d)
        self.local_roots_var.set(";".join(roots))

    def _run_in_thread(self, label: str, fn) -> None:
        self.status_var.set(label)
        self.progress.start(10)
        self.log_sink.write(f"\n[{label}] {datetime.now().isoformat()}\n")

        def target():
            try:
                fn()
                self.log_sink.write(f"[{label}] DONE\n")
            except Exception as e:
                self.log_sink.write(f"[{label}] ERROR: {e}\n")
            finally:
                self.progress.stop()
                self.status_var.set("Ready")
                self._save_state()

        t = threading.Thread(target=target, daemon=True)
        t.start()


    def _local_plan(self) -> None:
        def run():
            roots = [x.strip() for x in self.local_roots_var.get().split(";") if x.strip()]
            if not roots:
                raise ValueError("No roots provided")
            self.state["last_local_roots"] = roots
            argv = ["--config", str(self.local_cfg_entry.get()), "--mode", "plan"]
            for r in roots:
                argv += ["--root", r]
            code = local_lane.run(argv)
            self.log_sink.write(f"LOCAL plan exit code: {code}\n")
            try:
                import yaml
                cfgp = Path(self.local_cfg_entry.get())
                cfg = yaml.safe_load(cfgp.read_text(encoding="utf-8")) or {}
                run_root = Path(str(cfg.get("run_root","F:/LitigationOS/_OrganizeAI")))
                last_run = run_root / "LAST_RUN.txt"
                if last_run.exists():
                    rd = last_run.read_text(encoding="utf-8").strip()
                    if rd:
                        self.state["last_local_run_dir"] = rd
                        self.log_sink.write(f"LOCAL last run dir: {rd}\n")
            except Exception:
                return
        self._run_in_thread("LOCAL PLAN", run)

    def _gdrive_plan(self) -> None:
        def run():
            rid = self.gdrive_root_var.get().strip()
            if not rid:
                raise ValueError("Missing folder ID")
            if rid.lower() == "root":
                raise ValueError("Refusing root")
            self.state["last_gdrive_root_id"] = rid
            argv = ["--mode", "plan", "--root-id", rid]
            code = gdrive_lane.run(argv)
            self.log_sink.write(f"GDRIVE plan exit code: {code}\n")
        self._run_in_thread("GDRIVE PLAN", run)

    def _validate_any(self) -> None:
        plan = self.last_plan_var.get().strip() or self.state.get("last_plan_path","")
        if not plan:
            plan = filedialog.askopenfilename(title="Select plan.json or plan.csv")
        if not plan:
            return
        self.last_plan_var.set(plan)
        self.state["last_plan_path"] = plan

        def run():
            p = Path(plan)
            if p.suffix.lower() == ".json":
                code = gdrive_lane.run(["--validate", str(p)])
            else:
                # LOCAL validate uses plan_validator.py via module call
                sys.path.insert(0, str(HERE / "LOCAL"))
                import plan_validator as pv
                code = pv.run(["--plan", str(p)])
            self.log_sink.write(f"VALIDATE exit code: {code}\n")

        self._run_in_thread("VALIDATE", run)


    def _apply_any(self) -> None:
        plan = self.last_plan_var.get().strip() or self.state.get("last_plan_path","")
        if not plan:
            plan = filedialog.askopenfilename(title="Select plan.json or plan.csv")
        if not plan:
            return

        if not messagebox.askyesno("Apply", "Apply the selected plan. You can undo after apply. Continue"):
            return

        self.last_plan_var.set(plan)
        self.state["last_plan_path"] = plan

        def run():
            p = Path(plan)
            if p.suffix.lower() == ".json":
                code = gdrive_lane.run(["--mode", "apply", "--plan", str(p)])
                self.log_sink.write(f"APPLY exit code: {code}\n")
                return

            run_dir = str(p.parent)
            code = local_lane.run(["--config", str(self.local_cfg_entry.get()), "--mode", "apply", "--run_dir", run_dir])
            self.log_sink.write(f"APPLY exit code: {code}\n")
            self.state["last_local_run_dir"] = run_dir

        self._run_in_thread("APPLY", run)

    def _undo_last_any(self) -> None:
        undo = self.last_undo_var.get().strip() or self.state.get("last_undo_path","")
        if not undo:
            undo = filedialog.askopenfilename(title="Select undo.json or undo.csv")
        if not undo:
            return

        self.last_undo_var.set(undo)
        self.state["last_undo_path"] = undo

        def run():
            p = Path(undo)
            if p.suffix.lower() == ".json":
                code = gdrive_lane.run(["--mode", "undo", "--undo", str(p)])
            else:
                sys.path.insert(0, str(HERE / "LOCAL"))
                import undo_last as ul
                code = ul.run(["--undo", str(p)])
            self.log_sink.write(f"UNDO exit code: {code}\n")
        self._run_in_thread("UNDO", run)

    def _local_undo_last(self) -> None:
        # LOCAL: undo_last.py has a run wrapper in this package
        def run():
            sys.path.insert(0, str(HERE / "LOCAL"))
            import undo_last as ul
            code = ul.run([])
            self.log_sink.write(f"LOCAL undo last exit code: {code}\n")
        self._run_in_thread("LOCAL UNDO LAST", run)

    def _gdrive_undo(self) -> None:
        self._undo_last_any()

def main() -> None:
    app = OrganizerStudio()
    app.mainloop()

if __name__ == "__main__":
    main()
