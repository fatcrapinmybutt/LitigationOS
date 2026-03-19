#!/usr/bin/env python3
from __future__ import annotations

"""
Scoped Google Drive Organizer (safe-by-default)

Key properties:
- Refuses to operate on the My Drive root folder ("root")
- Operates only within one explicit folder subtree (root_id)
- Produces a plan artifact (JSON) before applying any changes
- Apply creates an undo artifact (JSON) suitable for best-effort rollback
- Optional rename suggestions are deterministic and threshold-gated by config

Drive API notes:
- Renaming is achieved by updating the File metadata field "name" via files.update
- Moving files across folders is achieved by files.update with addParents and removeParents
"""

import argparse
import json
import os
import pathlib
import re
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

import yaml

MIME_FOLDER = "application/vnd.google-apps.folder"

def iso_now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

# -----------------------------
# Progress signaling (GUI mode)
# -----------------------------
PROGRESS_PREFIX = "@@PROGRESS@@ "

def _progress_on() -> bool:
    return os.environ.get("ORGANIZERSTUDIO_PROGRESS", "").strip() == "1"

def _emit_progress(phase: str, current: int, total: int, item: str = "", detail: str = "") -> None:
    if not _progress_on():
        return
    try:
        payload = {"phase": str(phase), "current": int(current), "total": int(total), "item": str(item or ""), "detail": str(detail or "")}
        print(PROGRESS_PREFIX + json.dumps(payload, ensure_ascii=False), flush=True)
    except Exception:
        return

def log_jsonl(path: pathlib.Path, obj: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(obj, ensure_ascii=False) + "\n")

def read_json(path: pathlib.Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))

def write_json(path: pathlib.Path, obj: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

def safe_conf_get(cfg: Dict[str, Any], path: str, default: Any) -> Any:
    cur: Any = cfg
    for part in path.split("."):
        if not isinstance(cur, dict) or part not in cur:
            return default
        cur = cur[part]
    return cur

def sanitize_name(name: str, *, max_len: int = 180, normalize_ws: bool = True, windows_safe: bool = True) -> str:
    """
    Conservative filename sanitizer suitable for Drive and Windows mirroring.
    Drive allows more characters than Windows; this normalizes to a safe subset.
    """
    s = name
    s = s.replace("\x00", "")
    s = s.replace("/", " ")
    if normalize_ws:
        s = re.sub(r"\s+", " ", s).strip()
    if windows_safe:
        s = re.sub(r'[<>:"\\|?*]+', "_", s)
        s = s.rstrip(" .")
    if not s:
        s = "untitled"
    if len(s) > max_len:
        base, ext = os.path.splitext(s)
        keep = max_len - len(ext)
        if keep < 1:
            s = s[:max_len]
        else:
            s = base[:keep] + ext
    return s

def unique_name(desired: str, existing: set[str], max_len: int) -> str:
    if desired not in existing:
        existing.add(desired)
        return desired
    base, ext = os.path.splitext(desired)
    n = 2
    while True:
        suffix = f" ({n})"
        cand = base + suffix + ext
        if len(cand) > max_len:
            over = len(cand) - max_len
            shrink_base = base[:-over] if over < len(base) else base[:1]
            cand = shrink_base + suffix + ext
        if cand not in existing:
            existing.add(cand)
            return cand
        n += 1

@dataclass
class Op:
    op: str
    file_id: str = ""
    src_name: str = ""
    src_parent: str = ""
    dest_parent: str = ""
    dest_name: str = ""
    note: str = ""

class DriveClient:
    def get(self, file_id: str) -> Dict[str, Any]:
        raise NotImplementedError

    def list_children(self, folder_id: str) -> List[Dict[str, Any]]:
        raise NotImplementedError

    def ensure_folder(self, parent_id: str, name: str) -> str:
        raise NotImplementedError

    def update_file(self, file_id: str, *, add_parent: Optional[str], remove_parents: List[str], new_name: Optional[str]) -> Dict[str, Any]:
        raise NotImplementedError

    def find_subtree_files(self, root_id: str) -> List[Dict[str, Any]]:
        raise NotImplementedError

    def find_subtree_folders(self, root_id: str) -> List[Dict[str, Any]]:
        raise NotImplementedError

class MockDrive(DriveClient):
    def __init__(self) -> None:
        self.nodes: Dict[str, Dict[str, Any]] = {}
        self._id = 1

    def _new_id(self) -> str:
        self._id += 1
        return str(self._id)

    def add_folder(self, name: str, parent: Optional[str]) -> str:
        fid = self._new_id()
        self.nodes[fid] = {"id": fid, "name": name, "mimeType": MIME_FOLDER, "parents": [parent] if parent else []}
        return fid

    def add_file(self, name: str, parent: str, mime: str) -> str:
        fid = self._new_id()
        self.nodes[fid] = {"id": fid, "name": name, "mimeType": mime, "parents": [parent]}
        return fid

    def get(self, file_id: str) -> Dict[str, Any]:
        return dict(self.nodes[file_id])

    def list_children(self, folder_id: str) -> List[Dict[str, Any]]:
        out = []
        for n in self.nodes.values():
            ps = n.get("parents") or []
            if ps and ps[0] == folder_id:
                out.append(dict(n))
        return out

    def ensure_folder(self, parent_id: str, name: str) -> str:
        for ch in self.list_children(parent_id):
            if ch.get("mimeType") == MIME_FOLDER and ch.get("name") == name:
                return ch["id"]
        return self.add_folder(name, parent_id)

    def update_file(self, file_id: str, *, add_parent: Optional[str], remove_parents: List[str], new_name: Optional[str]) -> Dict[str, Any]:
        n = self.nodes[file_id]
        if new_name is not None and new_name != "":
            n["name"] = new_name
        if add_parent:
            n["parents"] = [add_parent]
        return dict(n)

    def _walk(self, root_id: str) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        folders: List[Dict[str, Any]] = []
        files: List[Dict[str, Any]] = []
        stack = [root_id]
        seen = set()
        while stack:
            cur = stack.pop()
            if cur in seen:
                continue
            seen.add(cur)
            meta = self.get(cur)
            if meta.get("mimeType") == MIME_FOLDER:
                folders.append(meta)
                for ch in self.list_children(cur):
                    if ch.get("mimeType") == MIME_FOLDER:
                        stack.append(ch["id"])
                    else:
                        files.append(ch)
        return folders, files

    def find_subtree_files(self, root_id: str) -> List[Dict[str, Any]]:
        return self._walk(root_id)[1]

    def find_subtree_folders(self, root_id: str) -> List[Dict[str, Any]]:
        return self._walk(root_id)[0]

class RealDrive(DriveClient):
    def __init__(self, service) -> None:
        self.service = service

    def get(self, file_id: str) -> Dict[str, Any]:
        return self.service.files().get(
            fileId=file_id,
            fields="id,name,mimeType,parents",
            supportsAllDrives=True,
        ).execute()

    def list_children(self, folder_id: str) -> List[Dict[str, Any]]:
        q = f"'{folder_id}' in parents and trashed=false"
        out: List[Dict[str, Any]] = []
        page_token = None
        while True:
            res = self.service.files().list(
                q=q,
                fields="nextPageToken, files(id,name,mimeType,parents)",
                pageToken=page_token,
                pageSize=1000,
                supportsAllDrives=True,
                includeItemsFromAllDrives=True,
            ).execute()
            out.extend(res.get("files", []))
            page_token = res.get("nextPageToken")
            if not page_token:
                break
        return out

    def ensure_folder(self, parent_id: str, name: str) -> str:
        for ch in self.list_children(parent_id):
            if ch.get("mimeType") == MIME_FOLDER and ch.get("name") == name:
                return ch["id"]
        body = {"name": name, "mimeType": MIME_FOLDER, "parents": [parent_id]}
        created = self.service.files().create(body=body, fields="id", supportsAllDrives=True).execute()
        return created["id"]

    def update_file(self, file_id: str, *, add_parent: Optional[str], remove_parents: List[str], new_name: Optional[str]) -> Dict[str, Any]:
        body: Dict[str, Any] = {}
        if new_name is not None:
            body["name"] = new_name
        kwargs: Dict[str, Any] = {
            "fileId": file_id,
            "supportsAllDrives": True,
            "fields": "id,name,mimeType,parents",
        }
        if body:
            kwargs["body"] = body
        if add_parent:
            kwargs["addParents"] = add_parent
        if remove_parents:
            kwargs["removeParents"] = ",".join([p for p in remove_parents if p])
        return self.service.files().update(**kwargs).execute()

    def find_subtree_folders(self, root_id: str) -> List[Dict[str, Any]]:
        out: List[Dict[str, Any]] = []
        stack = [root_id]
        seen = set()
        while stack:
            cur = stack.pop(0)
            if cur in seen:
                continue
            seen.add(cur)
            meta = self.get(cur)
            if meta.get("mimeType") != MIME_FOLDER:
                continue
            out.append(meta)
            for ch in self.list_children(cur):
                if ch.get("mimeType") == MIME_FOLDER:
                    stack.append(ch["id"])
        return out

    def find_subtree_files(self, root_id: str) -> List[Dict[str, Any]]:
        folders = self.find_subtree_folders(root_id)
        files: List[Dict[str, Any]] = []
        for fol in folders:
            for ch in self.list_children(fol["id"]):
                if ch.get("mimeType") != MIME_FOLDER:
                    files.append(ch)
        return files

def load_config(path: pathlib.Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}

def load_buckets(path: pathlib.Path) -> Dict[str, List[str]]:
    if not path.exists():
        return {"OTHER": []}
    d = json.loads(path.read_text(encoding="utf-8"))
    out: Dict[str, List[str]] = {}
    for k, v in d.items():
        out[str(k)] = [str(x).lower() for x in (v or [])]
    if "OTHER" not in out:
        out["OTHER"] = []
    return out

def pick_bucket(name: str, buckets: Dict[str, List[str]]) -> str:
    ext = os.path.splitext(name)[1].lower()
    for bucket, exts in buckets.items():
        if bucket == "OTHER":
            continue
        if ext and ext in exts:
            return bucket
    return "OTHER"

def in_subtree(drive: DriveClient, root_id: str, file_meta: Dict[str, Any], folder_set: set[str]) -> bool:
    parents = file_meta.get("parents") or []
    if not parents:
        return False
    cur = parents[0]
    seen = set()
    while cur and cur not in seen:
        seen.add(cur)
        if cur == root_id:
            return True
        if cur not in folder_set:
            return False
        meta = drive.get(cur)
        ps = meta.get("parents") or []
        cur = ps[0] if ps else ""
    return False

def build_plan(drive: DriveClient, root_id: str, buckets: Dict[str, List[str]], cfg: Dict[str, Any], ledger: pathlib.Path) -> Dict[str, Any]:
    rename_enabled = bool(safe_conf_get(cfg, "rename.enabled", False))
    rename_max_len = int(safe_conf_get(cfg, "rename.max_len", 180))
    normalize_ws = bool(safe_conf_get(cfg, "rename.normalize_whitespace", True))
    windows_safe = bool(safe_conf_get(cfg, "rename.windows_safe", True))

    log_jsonl(ledger, {"ts": iso_now(), "event": "plan_start", "root_id": root_id, "rename_enabled": rename_enabled})

    folder_metas = drive.find_subtree_folders(root_id)
    folder_ids = set([f["id"] for f in folder_metas])

    files = drive.find_subtree_files(root_id)

    ensure_ops: List[Op] = []
    for bucket in buckets.keys():
        if bucket:
            ensure_ops.append(Op(op="ensure_folder", dest_parent=root_id, dest_name=bucket, note="bucket folder"))

    move_ops: List[Op] = []
    n_files = len(files)
    for i, fm in enumerate(files, start=1):
        if _progress_on():
            _emit_progress("GDRIVE_PLAN", i, n_files, fm.get("name","") or fm.get("id",""), "SCAN")
        if fm.get("mimeType") == MIME_FOLDER:
            continue
        if not in_subtree(drive, root_id, fm, folder_ids):
            continue
        fid = fm["id"]
        src_name = fm.get("name", "")
        src_parent = (fm.get("parents") or [""])[0]

        bucket = pick_bucket(src_name, buckets)
        dest_parent = f"bucket::{bucket}"

        dest_name = src_name
        if rename_enabled:
            dest_name = sanitize_name(src_name, max_len=rename_max_len, normalize_ws=normalize_ws, windows_safe=windows_safe)

        move_ops.append(Op(op="move_rename", file_id=fid, src_name=src_name, src_parent=src_parent, dest_parent=dest_parent, dest_name=dest_name, note=bucket))

    plan = {
        "meta": {
            "ts": iso_now(),
            "root_id": root_id,
            "rename_enabled": rename_enabled,
            "rename_max_len": rename_max_len,
        },
        "ops": [o.__dict__ for o in (ensure_ops + move_ops)],
    }
    return plan

def validate_plan_dict(plan: Dict[str, Any]) -> Dict[str, Any]:
    ops = plan.get("ops") or []
    ok = True
    errors: List[str] = []
    if not isinstance(ops, list) or not ops:
        ok = False
        errors.append("plan has no ops")
    for i, op in enumerate(ops):
        if not isinstance(op, dict):
            ok = False
            errors.append(f"op {i} not a dict")
            continue
        if op.get("op") not in ("ensure_folder", "move_rename"):
            ok = False
            errors.append(f"op {i} invalid op {op.get('op')}")
        if op.get("op") == "move_rename":
            for k in ("file_id", "src_parent", "dest_parent", "dest_name", "src_name"):
                if not op.get(k):
                    ok = False
                    errors.append(f"op {i} missing {k}")
    seen = set()
    for i, op in enumerate(ops):
        if op.get("op") != "move_rename":
            continue
        key = (op.get("dest_parent"), op.get("dest_name"))
        if key in seen:
            ok = False
            errors.append(f"collision duplicate dest {key}")
        seen.add(key)
    return {"ok": ok, "errors": errors, "ops": len(ops)}

def apply_plan(drive: DriveClient, plan: Dict[str, Any], ledger: pathlib.Path) -> pathlib.Path:
    ops = plan.get("ops") or []
    meta = plan.get("meta") or {}
    root_id = meta.get("root_id") or ""
    if not root_id:
        raise SystemExit("ERROR: plan missing root_id")

    bucket_folder_ids: Dict[str, str] = {}
    n_ops = len(ops)
    for i, op in enumerate(ops, start=1):
        if _progress_on():
            item = op.get("src_name") or op.get("dest_name") or op.get("file_id") or ""
            _emit_progress("GDRIVE_APPLY", i, n_ops, str(item), op.get("op",""))
        if op.get("op") == "ensure_folder":
            name = op.get("dest_name")
            if not name:
                continue
            fid = drive.ensure_folder(root_id, name)
            bucket_folder_ids[name] = fid
            log_jsonl(ledger, {"ts": iso_now(), "op": "ensure_folder", "name": name, "id": fid})

    existing_by_parent: Dict[str, set[str]] = {}
    for bucket_name, folder_id in bucket_folder_ids.items():
        names = set([ch.get("name", "") for ch in drive.list_children(folder_id)])
        existing_by_parent[folder_id] = names

    undo_rows: List[Dict[str, Any]] = []

    for op in ops:
        if op.get("op") != "move_rename":
            continue
        fid = op["file_id"]
        dest_parent_tag = op["dest_parent"]
        dest_name_desired = op["dest_name"]

        if not dest_parent_tag.startswith("bucket::"):
            raise SystemExit("ERROR: dest_parent must be bucket tag")
        bucket_name = dest_parent_tag.split("bucket::", 1)[1]
        dest_parent = bucket_folder_ids.get(bucket_name)
        if not dest_parent:
            raise SystemExit(f"ERROR: missing bucket folder id for {bucket_name}")

        max_len = int(meta.get("rename_max_len") or 180)
        existing = existing_by_parent.setdefault(dest_parent, set())
        dest_name = unique_name(dest_name_desired, existing, max_len)

        before = drive.get(fid)
        old_name = before.get("name", "")
        old_parents = before.get("parents") or []
        old_parent = old_parents[0] if old_parents else ""

        want_move = (old_parent != dest_parent and dest_parent != "")
        want_rename = (old_name != dest_name and dest_name != "")

        if not want_move and not want_rename:
            log_jsonl(ledger, {"ts": iso_now(), "op": "skip_noop", "file_id": fid})
            continue

        updated = drive.update_file(
            fid,
            add_parent=dest_parent if want_move else None,
            remove_parents=[old_parent] if want_move and old_parent else [],
            new_name=dest_name if want_rename else None,
        )

        undo_rows.append({
            "op": "move_rename_back",
            "file_id": fid,
            "old_parent": old_parent,
            "old_name": old_name,
            "new_parent": dest_parent,
            "new_name": updated.get("name", dest_name),
        })

        log_jsonl(ledger, {
            "ts": iso_now(),
            "op": "move_rename",
            "file_id": fid,
            "from_parent": old_parent,
            "to_parent": dest_parent,
            "from_name": old_name,
            "to_name": updated.get("name", dest_name),
        })

    undo_path = ledger.parent / "undo.json"
    write_json(undo_path, {"meta": {"ts": iso_now(), "root_id": root_id}, "undo": undo_rows})
    return undo_path

def undo_plan(drive: DriveClient, undo_path: pathlib.Path, ledger: pathlib.Path) -> None:
    data = read_json(undo_path)
    rows = data.get("undo") or []
    for r in reversed(rows):
        if r.get("op") != "move_rename_back":
            continue
        fid = r["file_id"]
        old_parent = r.get("old_parent", "")
        old_name = r.get("old_name", "")
        new_parent = r.get("new_parent", "")
        before = drive.get(fid)
        cur_parent = (before.get("parents") or [""])[0]
        cur_name = before.get("name", "")
        want_move = (old_parent and cur_parent != old_parent)
        want_rename = (old_name and cur_name != old_name)
        drive.update_file(
            fid,
            add_parent=old_parent if want_move else None,
            remove_parents=[new_parent] if want_move and new_parent else [],
            new_name=old_name if want_rename else None,
        )
        log_jsonl(ledger, {"ts": iso_now(), "op": "undo_move_rename", "file_id": fid, "to_parent": old_parent, "to_name": old_name})

def run_self_test_mock() -> bool:
    d = MockDrive()
    root = d.add_folder("TEST_ROOT", parent=None)
    a = d.add_folder("A", parent=root)
    b = d.add_folder("B", parent=a)

    f1 = d.add_file("Report  2026  .pdf", parent=b, mime="application/pdf")
    d.add_file("notes.txt", parent=a, mime="text/plain")

    tmp = pathlib.Path(".") / "_MOCK_RUN"
    if tmp.exists():
        for p in tmp.rglob("*"):
            if p.is_file():
                p.unlink()
        for p in sorted([x for x in tmp.rglob("*") if x.is_dir()], reverse=True):
            if p != tmp:
                p.rmdir()
    tmp.mkdir(exist_ok=True)
    ledger = tmp / "ledger.jsonl"

    cfg = {"rename": {"enabled": True, "max_len": 120, "normalize_whitespace": True, "windows_safe": True}}
    buckets = {"PDFS": [".pdf"], "DOCS": [".txt"], "OTHER": []}

    plan = build_plan(d, root, buckets, cfg, ledger)
    v = validate_plan_dict(plan)
    if not v.get("ok"):
        raise AssertionError("validate_plan failed")

    move_ops = [o for o in plan["ops"] if o.get("op") == "move_rename"]
    if len(move_ops) < 2:
        raise AssertionError("expected move_rename ops")

    if not any(o["src_name"] != o["dest_name"] for o in move_ops):
        raise AssertionError("expected at least one rename in plan")

    undo_path = apply_plan(d, plan, ledger)

    pdfs = d.ensure_folder(root, "PDFS")
    meta_f1 = d.get(f1)
    if meta_f1["parents"][0] != pdfs:
        raise AssertionError("f1 not moved to PDFS")
    if meta_f1["name"] == "Report  2026  .pdf":
        raise AssertionError("f1 not renamed")

    undo_plan(d, undo_path, ledger)
    meta_f1b = d.get(f1)
    if meta_f1b["parents"][0] != b:
        raise AssertionError("f1 parent not restored")
    if meta_f1b["name"] != "Report  2026  .pdf":
        raise AssertionError("f1 name not restored")

    return True

def build_drive_client(cfg: Dict[str, Any], args: argparse.Namespace) -> DriveClient:
    if args.mock:
        return MockDrive()

    from google.oauth2 import service_account
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request
    import googleapiclient.discovery

    scopes = safe_conf_get(cfg, "auth.scopes", ["https://www.googleapis.com/auth/drive"])
    sa_path = args.service_account or safe_conf_get(cfg, "auth.service_account_json", "")
    cred_path = args.credentials or safe_conf_get(cfg, "auth.credentials_json", "credentials.json")
    token_path = args.token or safe_conf_get(cfg, "auth.token_json", "token.json")

    creds = None
    if sa_path:
        creds = service_account.Credentials.from_service_account_file(sa_path, scopes=scopes)
    else:
        import pickle
        if os.path.exists(token_path):
            with open(token_path, "rb") as f:
                creds = pickle.load(f)
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(cred_path, scopes)
                creds = flow.run_local_server(port=0)
            with open(token_path, "wb") as f:
                pickle.dump(creds, f)

    service = googleapiclient.discovery.build("drive", "v3", credentials=creds, cache_discovery=False)
    return RealDrive(service)

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="config.yaml")
    ap.add_argument("--root-id", default="")
    ap.add_argument("--mode", choices=["plan", "apply", "undo"], default="")
    ap.add_argument("--plan", default="", help="Plan JSON path for apply")
    ap.add_argument("--undo", default="", help="Undo JSON path for undo")
    ap.add_argument("--buckets", default="buckets.json")
    ap.add_argument("--validate", default="", help="Validate a plan JSON path and exit")
    ap.add_argument("--service-account", default="", help="Service account JSON path")
    ap.add_argument("--credentials", default="credentials.json")
    ap.add_argument("--token", default="token.json")
    ap.add_argument("--mock", action="store_true", help="Use mock drive client (no Google libs)")
    ap.add_argument("--self-test", action="store_true", help="Run mock self-test and exit")
    args = ap.parse_args()

    if args.self_test:
        ok = run_self_test_mock()
        if ok:
            print("SELF_TEST_OK")
            raise SystemExit(0)
        raise SystemExit(1)

    cfg = load_config(pathlib.Path(args.config))
    root_id = args.root_id or safe_conf_get(cfg, "drive.root_id", "")
    if not root_id:
        raise SystemExit("ERROR: missing root id. Use --root-id")
    if root_id.strip().lower() == "root":
        raise SystemExit("ERROR: refusing to operate on My Drive root. Provide a scoped folder id.")

    run_root = pathlib.Path(safe_conf_get(cfg, "runs_root", str(pathlib.Path("..") / ".." / "_OrganizeAI" / "GDRIVE")))
    run_root.mkdir(parents=True, exist_ok=True)
    run_dir = run_root / f"RUN_{time.strftime('%Y%m%d_%H%M%S')}"
    run_dir.mkdir(parents=True, exist_ok=True)
    ledger = run_dir / "ledger.jsonl"

    log_jsonl(ledger, {"ts": iso_now(), "event": "run_start", "root_id": root_id})
    drive = build_drive_client(cfg, args)

    if args.validate:
        plan_path = pathlib.Path(args.validate)
        v = validate_plan_dict(read_json(plan_path))
        write_json(run_dir / "validate.json", v)
        print(json.dumps(v, indent=2))
        raise SystemExit(0 if v.get("ok") else 2)

    buckets = load_buckets(pathlib.Path(args.buckets))
    mode = args.mode or "plan"

    if mode == "plan":
        plan = build_plan(drive, root_id, buckets, cfg, ledger)
        plan_path = run_dir / "plan.json"
        write_json(plan_path, plan)
        v = validate_plan_dict(plan)
        write_json(run_dir / "validate.json", v)
        print(f"PLAN_PATH={plan_path}")
        print(f"VALIDATE_OK={v.get('ok')}")
    elif mode == "apply":
        if not args.plan:
            raise SystemExit("ERROR: apply requires --plan PATH")
        plan_path = pathlib.Path(args.plan)
        plan = read_json(plan_path)
        v = validate_plan_dict(plan)
        if not v.get("ok"):
            raise SystemExit("ERROR: plan validation failed")
        undo_path = apply_plan(drive, plan, ledger)
        print(f"UNDO_PATH={undo_path}")
        print("APPLY_DONE")
    else:
        if not args.undo:
            raise SystemExit("ERROR: undo requires --undo PATH")
        undo_path = pathlib.Path(args.undo)
        undo_plan(drive, undo_path, ledger)
        print("UNDO_DONE")

    log_jsonl(ledger, {"ts": iso_now(), "event": "run_end"})


def run(argv: list[str]) -> int:
    """Programmatic entrypoint for GUI and tests."""
    import sys as _sys
    old = _sys.argv
    _sys.argv = [old[0]] + list(argv)
    try:
        main()
        return 0
    except SystemExit as e:
        try:
            return int(e.code or 0)
        except Exception:
            return 1
    finally:
        _sys.argv = old


if __name__ == "__main__":
    main()
