#!/usr/bin/env python3
from __future__ import annotations

import os
import sys
import json
import threading
from dataclasses import dataclass
from pathlib import Path
from datetime import datetime

# Ensure bundled lanes are importable
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE / "LOCAL"))
sys.path.insert(0, str(HERE / "GDRIVE"))

import ai_organizer_stack as local_lane
import gdrive_scoped_organizer as gdrive_lane

APP_NAME = "OrganizerStudio"
APP_VERSION = "2026-01-23-PRO3"

RUNROOT_LOCAL_DEFAULT = "F:/LitigationOS/_OrganizeAI/LOCAL"
RUNROOT_GDRIVE_DEFAULT = "F:/LitigationOS/_OrganizeAI/GDRIVE"
STATE_ROOT_DEFAULT = "F:/LitigationOS/_OrganizeAI/STUDIO"

def _ts() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def _ensure_dir(p: Path) -> None:
    p.mkdir(parents=True, exist_ok=True)

@dataclass
class PlanRow:
    op: str
    src: str
    dst: str
    extra: str

def load_plan_rows(plan_path: Path) -> list[PlanRow]:
    rows: list[PlanRow] = []
    if plan_path.suffix.lower() == ".json":
        obj = json.loads(plan_path.read_text(encoding="utf-8"))
        for it in obj.get("ops", []):
            rows.append(PlanRow(
                op=str(it.get("op","")),
                src=str(it.get("id","")) + " | " + str(it.get("from_parent","")),
                dst=str(it.get("to_parent","")),
                extra=str(it.get("name",""))
            ))
        return rows

    # CSV plan: first line header
    import csv
    with plan_path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for r in reader:
            rows.append(PlanRow(
                op=str(r.get("op","")),
                src=str(r.get("src","")),
                dst=str(r.get("dst","")),
                extra=str(r.get("reason",""))
            ))
    return rows

def open_path(p: str) -> None:
    path = Path(p)
    if not path.exists():
        return
    if os.name == "nt":
        os.startfile(str(path))
    else:
        print(str(path))

def try_import_ai() -> tuple[bool, str]:
    try:
        import sentence_transformers  # noqa
        return True, "sentence-transformers available"
    except Exception:
        return False, "AI embeddings not installed (optional)"

def main() -> int:
    try:
        from PySide6 import QtCore, QtGui, QtWidgets
    except Exception as e:
        print("ERROR: PySide6 not installed. Run LAUNCH_STUDIO_QT.cmd to install dependencies.")
        print(str(e))
        return 1

    import io, sys, traceback
    PROGRESS_PREFIX = "@@PROGRESS@@ "

    class Worker(QtCore.QObject):
        log = QtCore.Signal(str)
        progress = QtCore.Signal(int, int, str, str)  # current, total, phase, item
        done = QtCore.Signal(int)

        def __init__(self, fn):
            super().__init__()
            self._fn = fn
            self._buf = ""

        def _handle_line(self, line: str) -> None:
            # Progress markers emitted by the engine:
            #   @@PROGRESS@@ {"phase":"APPLY","current":1,"total":10,"item":"F:/LitigationOS/path/file.pdf","detail":"MOVE"}
            if line.startswith(PROGRESS_PREFIX):
                try:
                    payload = json.loads(line[len(PROGRESS_PREFIX):].strip())
                    phase = str(payload.get("phase", "")).strip()
                    detail = str(payload.get("detail", "")).strip()
                    if detail:
                        phase = f"{phase} · {detail}"
                    cur = int(payload.get("current", 0) or 0)
                    tot = int(payload.get("total", 0) or 0)
                    item = str(payload.get("item", "") or "")
                    self.progress.emit(cur, tot, phase, item)
                except Exception:
                    self.log.emit(line + "\n")
                return

            self.log.emit(line + "\n")

        def _write(self, s: str) -> None:
            self._buf += s
            while "\n" in self._buf:
                line, self._buf = self._buf.split("\n", 1)
                if line is not None:
                    self._handle_line(line)

        @QtCore.Slot()
        def run(self):
            # Capture stdout/stderr so the GUI can display real-time progress/logs.
            old_out, old_err = sys.stdout, sys.stderr

            class _Sink(io.TextIOBase):
                def __init__(self, outer):
                    super().__init__()
                    self.outer = outer
                def write(self, s):
                    if not s:
                        return 0
                    self.outer._write(str(s))
                    return len(s)
                def flush(self):
                    return None

            sys.stdout = _Sink(self)
            sys.stderr = _Sink(self)

            try:
                rc = self._fn()
                try:
                    code = int(rc) if rc is not None else 0
                except Exception:
                    code = 0
                if self._buf.strip():
                    self._handle_line(self._buf.rstrip("\n"))
                    self._buf = ""
                self.done.emit(code)
            except Exception as e:
                tb = traceback.format_exc()
                self.log.emit(f"[{_ts()}] ERROR: {e}\n{tb}\n")
                self.done.emit(1)
            finally:
                sys.stdout, sys.stderr = old_out, old_err

    class Studio(QtWidgets.QMainWindow):
        def __init__(self):
            super().__init__()
            self.setWindowTitle(f"{APP_NAME} {APP_VERSION}")
            self.resize(1220, 780)

            self.state_path = Path(STATE_ROOT_DEFAULT) / "state.json"
            _ensure_dir(self.state_path.parent)
            self.state = self._load_state()

            self._validated_ok = False
            self._active_jobs = []
            self._build_ui()
            self._sync_state_to_ui()
            self._append_log(f"[{_ts()}] Ready\n")

        def _load_state(self) -> dict:
            try:
                if self.state_path.exists():
                    return json.loads(self.state_path.read_text(encoding="utf-8"))
            except Exception:
                pass
            return {
                "local_roots": ["F:/"],
                "local_config": "LOCAL/config.yaml",
                "gdrive_root_id": "",
                "gdrive_config": "GDRIVE/config.yaml",
                "last_plan": "",
                "last_undo": "",
            }

        def _save_state(self) -> None:
            try:
                self.state_path.write_text(json.dumps(self.state, indent=2), encoding="utf-8")
            except Exception:
                pass

        def _build_ui(self):
            cw = QtWidgets.QWidget()
            self.setCentralWidget(cw)

            layout = QtWidgets.QVBoxLayout(cw)

            self._build_menus()

            header = QtWidgets.QHBoxLayout()
            layout.addLayout(header)

            self.lbl_ai = QtWidgets.QLabel()
            ok, msg = try_import_ai()
            self.lbl_ai.setText(f"AI: {'ON' if ok else 'OFF'} — {msg}")
            header.addWidget(self.lbl_ai)

            header.addStretch(1)

            self.btn_open_local_runs = QtWidgets.QPushButton("Open LOCAL runs")
            self.btn_open_local_runs.clicked.connect(lambda: open_path(RUNROOT_LOCAL_DEFAULT))
            header.addWidget(self.btn_open_local_runs)

            self.btn_open_gdrive_runs = QtWidgets.QPushButton("Open GDRIVE runs")
            self.btn_open_gdrive_runs.clicked.connect(lambda: open_path(RUNROOT_GDRIVE_DEFAULT))
            header.addWidget(self.btn_open_gdrive_runs)

            self.tabs = QtWidgets.QTabWidget()
            self.tabs.setDocumentMode(True)
            layout.addWidget(self.tabs, 1)

            # Footer: progress + current item
            footer = QtWidgets.QHBoxLayout()
            layout.addLayout(footer)

            self.progress = QtWidgets.QProgressBar()
            self.progress.setMinimum(0)
            self.progress.setMaximum(1)
            self.progress.setValue(0)
            self.progress.setTextVisible(True)
            self.progress.setFormat("Idle")
            footer.addWidget(self.progress, 2)

            self.lbl_phase2 = QtWidgets.QLabel("")
            self.lbl_phase2.setMinimumWidth(140)
            footer.addWidget(self.lbl_phase2, 0)

            self.lbl_item2 = QtWidgets.QLabel("")
            self.lbl_item2.setTextInteractionFlags(QtCore.Qt.TextSelectableByMouse)
            self.lbl_item2.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Preferred)
            footer.addWidget(self.lbl_item2, 3)

            self.btn_clear_progress = QtWidgets.QPushButton("Clear")
            self.btn_clear_progress.clicked.connect(self._reset_progress)
            footer.addWidget(self.btn_clear_progress, 0)

            self.tab_local = QtWidgets.QWidget()
            self.tab_gdrive = QtWidgets.QWidget()
            self.tab_plan = QtWidgets.QWidget()
            self.tab_ai = QtWidgets.QWidget()
            self.tab_log = QtWidgets.QWidget()

            self.tabs.addTab(self.tab_local, "LOCAL")
            self.tabs.addTab(self.tab_gdrive, "GDRIVE")
            self.tabs.addTab(self.tab_plan, "PLAN PREVIEW")
            self.tabs.addTab(self.tab_ai, "AI MODELS")
            self.tabs.addTab(self.tab_log, "LOG")

            self._build_local_tab()
            self._build_gdrive_tab()
            self._build_plan_tab()
            self._build_ai_tab()
            self._build_log_tab()

        def _build_local_tab(self):
            from PySide6 import QtWidgets
            lay = QtWidgets.QVBoxLayout(self.tab_local)

            form = QtWidgets.QFormLayout()
            lay.addLayout(form)

            self.local_roots = QtWidgets.QLineEdit()
            form.addRow("Roots (semicolon separated)", self.local_roots)

            row_cfg = QtWidgets.QHBoxLayout()
            self.local_cfg = QtWidgets.QLineEdit()
            self.btn_open_local_cfg = QtWidgets.QPushButton("Open")
            self.btn_open_local_cfg.clicked.connect(lambda: open_path(self.local_cfg.text().strip()))
            row_cfg.addWidget(self.local_cfg, 1)
            row_cfg.addWidget(self.btn_open_local_cfg)
            form.addRow("LOCAL config.yaml", row_cfg)

            btns = QtWidgets.QHBoxLayout()
            lay.addLayout(btns)

            self.btn_local_plan = QtWidgets.QPushButton("PLAN")
            self.btn_local_plan.clicked.connect(self._local_plan)
            btns.addWidget(self.btn_local_plan)

            self.btn_validate = QtWidgets.QPushButton("VALIDATE")
            self.btn_validate.clicked.connect(self._validate)
            btns.addWidget(self.btn_validate)

            self.btn_apply = QtWidgets.QPushButton("APPLY")
            self.btn_apply.setEnabled(False)
            self.btn_apply.clicked.connect(self._apply)
            btns.addWidget(self.btn_apply)

            self.btn_local_undo_last = QtWidgets.QPushButton("UNDO LAST")
            self.btn_local_undo_last.clicked.connect(self._local_undo_last)
            btns.addWidget(self.btn_local_undo_last)

            btns.addStretch(1)

            note = QtWidgets.QLabel("Tip: PLAN produces a plan.csv in the most recent run folder. Use PLAN PREVIEW to inspect it.")
            note.setWordWrap(True)
            lay.addWidget(note)

        def _build_gdrive_tab(self):
            from PySide6 import QtWidgets
            lay = QtWidgets.QVBoxLayout(self.tab_gdrive)

            form = QtWidgets.QFormLayout()
            lay.addLayout(form)

            self.gdrive_root_id = QtWidgets.QLineEdit()
            form.addRow("Scoped Drive folder ID (not root)", self.gdrive_root_id)

            row_cfg = QtWidgets.QHBoxLayout()
            self.gdrive_cfg = QtWidgets.QLineEdit()
            self.btn_open_gdrive_cfg = QtWidgets.QPushButton("Open")
            self.btn_open_gdrive_cfg.clicked.connect(lambda: open_path(self.gdrive_cfg.text().strip()))
            row_cfg.addWidget(self.gdrive_cfg, 1)
            row_cfg.addWidget(self.btn_open_gdrive_cfg)
            form.addRow("GDRIVE config.yaml", row_cfg)

            btns = QtWidgets.QHBoxLayout()
            lay.addLayout(btns)

            self.btn_gdrive_plan = QtWidgets.QPushButton("PLAN")
            self.btn_gdrive_plan.clicked.connect(self._gdrive_plan)
            btns.addWidget(self.btn_gdrive_plan)

            self.btn_validate2 = QtWidgets.QPushButton("VALIDATE")
            self.btn_validate2.clicked.connect(self._validate)
            btns.addWidget(self.btn_validate2)

            self.btn_apply2 = QtWidgets.QPushButton("APPLY")
            self.btn_apply2.setEnabled(False)
            self.btn_apply2.clicked.connect(self._apply)
            btns.addWidget(self.btn_apply2)

            self.btn_gdrive_undo = QtWidgets.QPushButton("UNDO")
            self.btn_gdrive_undo.clicked.connect(self._undo)
            btns.addWidget(self.btn_gdrive_undo)

            btns.addStretch(1)

            note = QtWidgets.QLabel("Safety: root ID is refused. Always scope to a folder subtree you can afford to reorganize.")
            note.setWordWrap(True)
            lay.addWidget(note)

        def _build_plan_tab(self):
            from PySide6 import QtWidgets
            lay = QtWidgets.QVBoxLayout(self.tab_plan)

            top = QtWidgets.QHBoxLayout()
            lay.addLayout(top)

            self.plan_path = QtWidgets.QLineEdit()
            top.addWidget(self.plan_path, 1)

            self.btn_browse_plan = QtWidgets.QPushButton("Browse")
            self.btn_browse_plan.clicked.connect(self._browse_plan)
            top.addWidget(self.btn_browse_plan)

            self.btn_load_plan = QtWidgets.QPushButton("Load")
            self.btn_load_plan.clicked.connect(self._load_plan)
            top.addWidget(self.btn_load_plan)

            self.tbl = QtWidgets.QTableWidget(0, 4)
            self.tbl.setHorizontalHeaderLabels(["op", "src", "dst", "extra"])
            self.tbl.horizontalHeader().setStretchLastSection(True)
            self.tbl.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
            lay.addWidget(self.tbl, 1)


        def _build_ai_tab(self):
            from PySide6 import QtWidgets
            lay = QtWidgets.QVBoxLayout(self.tab_ai)

            info = QtWidgets.QLabel("AI is optional. Install AI deps, download an embeddings model, then run a smoke test.")
            info.setWordWrap(True)
            lay.addWidget(info)

            form = QtWidgets.QFormLayout()
            lay.addLayout(form)

            self.ai_cache_dir = QtWidgets.QLineEdit(self.state.get("hf_cache_dir","F:/LitigationOS/_HF_CACHE"))
            form.addRow("HF cache dir", self.ai_cache_dir)

            self.ai_model = QtWidgets.QComboBox()
            self.ai_model.addItems([
                "nomic-ai/nomic-embed-text-v1.5",
                "BAAI/bge-small-en-v1.5",
            ])
            self.ai_model.setCurrentText(self.state.get("ai_model_id","nomic-ai/nomic-embed-text-v1.5"))
            form.addRow("Embedding model", self.ai_model)

            btns = QtWidgets.QHBoxLayout()
            lay.addLayout(btns)

            self.btn_ai_install = QtWidgets.QPushButton("Install AI deps")
            self.btn_ai_install.clicked.connect(self._ai_install_deps)
            btns.addWidget(self.btn_ai_install)

            self.btn_ai_download = QtWidgets.QPushButton("Download model")
            self.btn_ai_download.clicked.connect(self._ai_download_model)
            btns.addWidget(self.btn_ai_download)

            self.btn_ai_smoke = QtWidgets.QPushButton("Smoke test embeddings")
            self.btn_ai_smoke.clicked.connect(self._ai_smoke_test)
            btns.addWidget(self.btn_ai_smoke)

            btns.addStretch(1)

            note = QtWidgets.QLabel("AI never applies changes directly. It only produces suggestions after you review a plan.")
            note.setWordWrap(True)
            lay.addWidget(note)

        def _ai_install_deps(self):
            def fn():
                import subprocess, sys
                req = Path(__file__).resolve().parent / "requirements_ai.txt"
                for attempt in [1, 2]:
                    p = subprocess.run([sys.executable, "-m", "pip", "install", "-r", str(req)], text=True, capture_output=True)
                    self._append_log(p.stdout[-2000:])
                    self._append_log(p.stderr[-2000:])
                    if p.returncode == 0:
                        return 0
                return 1
            self._run_async("AI INSTALL", fn)

        def _ai_download_model(self):
            def fn():
                from AI import model_manager
                model_id = self.ai_model.currentText().strip()
                cache_dir = self.ai_cache_dir.text().strip()
                self.state["ai_model_id"] = model_id
                self.state["hf_cache_dir"] = cache_dir
                self._save_state()
                path = model_manager.download_model(model_id, cache_dir=cache_dir)
                self._append_log(f"[{_ts()}] model_path={path}\n")
                return 0
            self._run_async("AI DOWNLOAD", fn)

        def _ai_smoke_test(self):
            def fn():
                from AI.embedding_engine import EmbedConfig, embed_texts
                model_id = self.ai_model.currentText().strip()
                cache_dir = self.ai_cache_dir.text().strip()
                cfg = EmbedConfig(model_id=model_id, cache_dir=cache_dir)
                v = embed_texts(["test document", "another document"], cfg)
                self._append_log(f"[{_ts()}] embeddings_ok dims={len(v[0])}\n")
                return 0
            self._run_async("AI SMOKE", fn)


        def _build_log_tab(self):
            from PySide6 import QtWidgets
            lay = QtWidgets.QVBoxLayout(self.tab_log)

            self.log = QtWidgets.QPlainTextEdit()
            self.log.setReadOnly(True)
            lay.addWidget(self.log, 1)

        def _append_log(self, s: str) -> None:
            self.log.appendPlainText(s.rstrip("\n"))

        def _sync_state_to_ui(self):
            self.local_roots.setText(";".join(self.state.get("local_roots", ["F:/"])))
            self.local_cfg.setText(self.state.get("local_config","LOCAL/config.yaml"))
            self.gdrive_root_id.setText(self.state.get("gdrive_root_id",""))
            self.gdrive_cfg.setText(self.state.get("gdrive_config","GDRIVE/config.yaml"))
            self.plan_path.setText(self.state.get("last_plan",""))

        def _sync_ui_to_state(self):
            self.state["local_roots"] = [x.strip() for x in self.local_roots.text().split(";") if x.strip()]
            self.state["local_config"] = self.local_cfg.text().strip() or "LOCAL/config.yaml"
            self.state["gdrive_root_id"] = self.gdrive_root_id.text().strip()
            self.state["gdrive_config"] = self.gdrive_cfg.text().strip() or "GDRIVE/config.yaml"
            self.state["last_plan"] = self.plan_path.text().strip()

        def _run_async(self, label: str, fn):
            from PySide6 import QtCore, QtWidgets
            self._sync_ui_to_state()
            self._save_state()

            self._append_log(f"[{_ts()}] {label}\n")
            self.statusBar().showMessage(label)

            # Enable structured progress markers for the engine
            os.environ["ORGANIZERSTUDIO_PROGRESS"] = "1"

            # Prep progress UI (indeterminate until we get totals)
            if hasattr(self, "progress"):
                self.progress.setMaximum(0)
                self.progress.setValue(0)
                self.progress.setFormat(label)

            thread = QtCore.QThread(self)
            worker = Worker(fn)
            worker.moveToThread(thread)

            # Keep references so worker/thread are not GC'd mid-run
            self._active_jobs.append((label, thread, worker))

            worker.log.connect(lambda x: self._append_log(x))
            worker.progress.connect(self._on_progress)
            worker.done.connect(lambda code: self._done(label, code, thread))
            thread.started.connect(worker.run)
            thread.start()

        def _done(self, label: str, code: int, thread):
            self._append_log(f"[{_ts()}] {label} DONE code={code}\n")
            self._reset_progress()
            try:
                self._active_jobs = [t for t in self._active_jobs if t[1] is not thread]
            except Exception:
                pass
            self.statusBar().showMessage("Ready")
            thread.quit()
            thread.wait()
            if label.startswith("VALIDATE"):
                self._validated_ok = (code == 0)
                self.btn_apply.setEnabled(self._validated_ok)
                self.btn_apply2.setEnabled(self._validated_ok)

        def _reset_progress(self) -> None:
            from PySide6 import QtCore, QtWidgets
            if hasattr(self, "progress"):
                self.progress.setMaximum(1)
                self.progress.setValue(0)
                self.progress.setFormat("Idle")
            if hasattr(self, "lbl_phase2"):
                self.lbl_phase2.setText("")
            if hasattr(self, "lbl_item2"):
                self.lbl_item2.setText("")
            self.statusBar().showMessage("Ready")

        def _on_progress(self, current: int, total: int, phase: str, item: str) -> None:
            from PySide6 import QtWidgets
            # total==0 means indeterminate in our protocol
            if not hasattr(self, "progress"):
                return
            if total <= 0:
                self.progress.setMaximum(0)  # busy
                self.progress.setValue(0)
                self.progress.setFormat(phase if phase else "Working")
            else:
                self.progress.setMaximum(max(1, int(total)))
                self.progress.setValue(max(0, min(int(current), int(total))))
                self.progress.setFormat(f"{phase}  %v/%m" if phase else "%v/%m")
            if hasattr(self, "lbl_phase2"):
                self.lbl_phase2.setText(phase or "")
            if hasattr(self, "lbl_item2"):
                self.lbl_item2.setText(item or "")

        def _build_menus(self) -> None:
            from PySide6 import QtGui
            from pathlib import Path

            mb = self.menuBar()

            m_file = mb.addMenu("File")
            a_state = QtGui.QAction("Open State Folder", self)
            a_state.triggered.connect(lambda: open_path(str(self.state_root)))
            m_file.addAction(a_state)

            a_local = QtGui.QAction("Open LOCAL runs", self)
            a_local.triggered.connect(lambda: open_path(RUNROOT_LOCAL_DEFAULT))
            m_file.addAction(a_local)

            a_gdrive = QtGui.QAction("Open GDRIVE runs", self)
            a_gdrive.triggered.connect(lambda: open_path(RUNROOT_GDRIVE_DEFAULT))
            m_file.addAction(a_gdrive)

            m_file.addSeparator()
            a_exit = QtGui.QAction("Exit", self)
            a_exit.triggered.connect(self.close)
            m_file.addAction(a_exit)

            m_actions = mb.addMenu("Actions")
            a_plan_local = QtGui.QAction("LOCAL: Build plan", self)
            a_plan_local.triggered.connect(self._local_plan)
            m_actions.addAction(a_plan_local)

            a_apply_local = QtGui.QAction("LOCAL: Apply plan", self)
            a_apply_local.triggered.connect(self._local_apply)
            m_actions.addAction(a_apply_local)

            a_undo_local = QtGui.QAction("LOCAL: Undo last", self)
            a_undo_local.triggered.connect(self._local_undo)
            m_actions.addAction(a_undo_local)

            m_actions.addSeparator()

            a_plan_gd = QtGui.QAction("GDRIVE: Build plan", self)
            a_plan_gd.triggered.connect(self._gdrive_plan)
            m_actions.addAction(a_plan_gd)

            a_apply_gd = QtGui.QAction("GDRIVE: Apply plan", self)
            a_apply_gd.triggered.connect(self._gdrive_apply)
            m_actions.addAction(a_apply_gd)

            a_undo_gd = QtGui.QAction("GDRIVE: Undo last", self)
            a_undo_gd.triggered.connect(self._gdrive_undo)
            m_actions.addAction(a_undo_gd)

            m_tools = mb.addMenu("Tools")
            a_val = QtGui.QAction("Validate selected plan", self)
            a_val.triggered.connect(self._validate)
            m_tools.addAction(a_val)

            a_ai = QtGui.QAction("AI: Smoke test", self)
            a_ai.triggered.connect(self._ai_smoke)
            m_tools.addAction(a_ai)

            m_view = mb.addMenu("View")
            a_tab_local = QtGui.QAction("Go to LOCAL tab", self)
            a_tab_local.triggered.connect(lambda: self.tabs.setCurrentWidget(self.tab_local))
            m_view.addAction(a_tab_local)

            a_tab_gd = QtGui.QAction("Go to GDRIVE tab", self)
            a_tab_gd.triggered.connect(lambda: self.tabs.setCurrentWidget(self.tab_gdrive))
            m_view.addAction(a_tab_gd)

            a_tab_plan = QtGui.QAction("Go to PLAN PREVIEW tab", self)
            a_tab_plan.triggered.connect(lambda: self.tabs.setCurrentWidget(self.tab_plan))
            m_view.addAction(a_tab_plan)

            m_help = mb.addMenu("Help")
            a_readme = QtGui.QAction("Open README", self)
            a_readme.triggered.connect(lambda: open_path(str((Path(__file__).resolve().parent / "README.md"))))
            m_help.addAction(a_readme)

            a_about = QtGui.QAction("About", self)
            def _about():
                from PySide6 import QtWidgets
                QtWidgets.QMessageBox.information(self, "OrganizerStudio", "OrganizerStudio QT\nProgress + improved menus\n")
            a_about.triggered.connect(_about)
            m_help.addAction(a_about)


        def _browse_plan(self):
            from PySide6 import QtWidgets
            p, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Select plan", str(Path.home()), "Plan (*.json *.csv)")
            if p:
                self.plan_path.setText(p)
                self.state["last_plan"] = p
                self._save_state()

        def _load_plan(self):
            from PySide6 import QtWidgets
            p = Path(self.plan_path.text().strip())
            if not p.exists():
                QtWidgets.QMessageBox.warning(self, "Missing", f"Plan not found:\n{p}")
                return
            rows = load_plan_rows(p)
            self.tbl.setRowCount(0)
            for r in rows[:25000]:
                i = self.tbl.rowCount()
                self.tbl.insertRow(i)
                self.tbl.setItem(i, 0, QtWidgets.QTableWidgetItem(r.op))
                self.tbl.setItem(i, 1, QtWidgets.QTableWidgetItem(r.src))
                self.tbl.setItem(i, 2, QtWidgets.QTableWidgetItem(r.dst))
                self.tbl.setItem(i, 3, QtWidgets.QTableWidgetItem(r.extra))
            self._append_log(f"[{_ts()}] Loaded plan rows={len(rows)}\n")

        def _local_plan(self):
            def fn():
                roots = self.state.get("local_roots", [])
                if not roots:
                    return 1
                argv = ["--config", self.state.get("local_config","LOCAL/config.yaml"), "--mode", "plan"]
                for r in roots:
                    argv += ["--root", r]
                return local_lane.run(argv)
            self._run_async("LOCAL PLAN", fn)

        def _gdrive_plan(self):
            def fn():
                rid = self.state.get("gdrive_root_id","").strip()
                if not rid or rid.lower() == "root":
                    return 1
                argv = ["--config", self.state.get("gdrive_config","GDRIVE/config.yaml"), "--mode", "plan", "--root-id", rid]
                return gdrive_lane.run(argv)
            self._run_async("GDRIVE PLAN", fn)

        def _validate(self):
            from PySide6 import QtWidgets
            plan = self.state.get("last_plan","").strip()
            if not plan:
                QtWidgets.QMessageBox.warning(self, "Missing", "Select a plan in PLAN PREVIEW.")
                return
            p = Path(plan)
            def fn():
                if p.suffix.lower() == ".json":
                    return gdrive_lane.run(["--validate", str(p)])
                # local: validate uses module
                import plan_validator as pv
                return pv.run(["--plan", str(p)])
            self._run_async("VALIDATE", fn)

        def _apply(self):
            from PySide6 import QtWidgets
            if not self._validated_ok:
                QtWidgets.QMessageBox.warning(self, "Blocked", "VALIDATE must succeed before APPLY.")
                return
            plan = self.state.get("last_plan","").strip()
            if not plan:
                return
            p = Path(plan)
            def fn():
                if p.suffix.lower() == ".json":
                    return gdrive_lane.run(["--mode", "apply", "--plan", str(p)])
                run_dir = str(p.parent)
                return local_lane.run(["--config", self.state.get("local_config","LOCAL/config.yaml"), "--mode", "apply", "--run_dir", run_dir])
            self._run_async("APPLY", fn)

        def _undo(self):
            from PySide6 import QtWidgets
            undo = self.state.get("last_undo","").strip()
            if not undo:
                QtWidgets.QMessageBox.information(self, "Pick undo", "Select an undo.json in a run folder.")
                return
            p = Path(undo)
            def fn():
                if p.suffix.lower() == ".json":
                    return gdrive_lane.run(["--mode", "undo", "--undo", str(p)])
                import undo_last as ul
                return ul.run(["--undo", str(p)])
            self._run_async("UNDO", fn)

        def _local_undo_last(self):
            def fn():
                import undo_last as ul
                return ul.run([])
            self._run_async("LOCAL UNDO LAST", fn)

    app = QtWidgets.QApplication(sys.argv)
    try:
        app.setStyle("Fusion")
    except Exception:
        pass
    win = Studio()
    win.show()
    return app.exec()

if __name__ == "__main__":
    raise SystemExit(main())
