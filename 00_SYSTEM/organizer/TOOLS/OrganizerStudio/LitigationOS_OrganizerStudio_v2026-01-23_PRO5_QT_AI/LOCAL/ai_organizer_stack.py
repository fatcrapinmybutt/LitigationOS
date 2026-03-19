#!/usr/bin/env python
from __future__ import annotations

import os, csv, json, re, shutil, argparse, math, fnmatch
from datetime import datetime
from pathlib import Path
from typing import List, Tuple, Dict, Optional, Iterable, Set

import yaml
try:
    from tqdm import tqdm  # type: ignore
except Exception:
    tqdm = None  # type: ignore


try:
    import magic  # python-magic-bin on Windows
except Exception:
    magic = None

import mimetypes

PLAN_COLUMNS = [
    "action","src","dst","bucket","reason","confidence",
    "size_bytes","mtime_iso","cluster_id","proposed_name",
    "root_tag","flags"
]

DEFAULT_EXCLUDE_NAMES = {
    "BUCKETS", ".git", ".svn", ".hg", "node_modules", "__pycache__",
    "$RECYCLE.BIN", "System Volume Information"
}
# -----------------------------
# Progress signaling (GUI mode)
# -----------------------------
# When ORGANIZERSTUDIO_PROGRESS=1 is set, the engine emits machine-readable progress
# lines to stdout for the Qt launcher to parse and render as a progress bar.
#
# Format (one line):
#   @@PROGRESS@@ {"phase":"APPLY","current":12,"total":250,"item":"F:/LitigationOS/path/file.pdf","detail":"MOVE"}
#
PROGRESS_PREFIX = "@@PROGRESS@@ "

def _progress_on() -> bool:
    return os.environ.get("ORGANIZERSTUDIO_PROGRESS", "").strip() == "1"

def _emit_progress(phase: str, current: int, total: int, item: str = "", detail: str = "") -> None:
    if not _progress_on():
        return
    try:
        payload = {
            "phase": str(phase),
            "current": int(current),
            "total": int(total),
            "item": str(item or ""),
            "detail": str(detail or ""),
        }
        print(PROGRESS_PREFIX + json.dumps(payload, ensure_ascii=False), flush=True)
    except Exception:
        # Never break the organizer for progress reporting
        return

def now_stamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")

def iso_now() -> str:
    return datetime.now().isoformat(timespec="seconds")

def safe_mkdir(p: Path) -> None:
    p.mkdir(parents=True, exist_ok=True)

def load_cfg(path: Path) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}

def write_jsonl(path: Path, obj: dict) -> None:
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(obj, ensure_ascii=False) + "\n")

def norm_path(p: Path) -> str:
    # normalized for Windows-ish globs
    return str(p).replace("/", "\\").rstrip("\\")

def ext_lower(name: str) -> str:
    return (Path(name).suffix or "").lower()

def cfg_set(cfg: dict, key: str, default):
    v = cfg.get(key, None)
    return default if v is None else v

def is_excluded_dirname(name: str, cfg: dict) -> bool:
    names = set([str(x) for x in (cfg.get("exclude_dir_names") or [])])
    names |= DEFAULT_EXCLUDE_NAMES
    return name in names or name.upper() in names

def matches_any_glob(path_norm: str, globs: List[str]) -> bool:
    for g in globs:
        if fnmatch.fnmatch(path_norm.lower(), str(g).lower()):
            return True
    return False

def should_include(path_norm: str, include_globs: List[str]) -> bool:
    if not include_globs:
        return True
    return matches_any_glob(path_norm, include_globs)

def classify_bucket(cfg: dict, file_path: Path) -> str:
    buckets = cfg.get("buckets", {})
    ext = ext_lower(file_path.name)
    for b, exts in buckets.items():
        if ext in [e.lower() for e in exts]:
            return b

    # Optional MIME inference
    if magic is not None:
        try:
            mime = magic.from_file(str(file_path), mime=True) or ""
            if mime.startswith("image/"):
                return "IMAGES"
            if mime.startswith("audio/"):
                return "AUDIO"
            if mime.startswith("video/"):
                return "VIDEO"
            if mime == "application/pdf":
                return "PDFS"
        except Exception:
            pass

    try:
        mime2, _ = mimetypes.guess_type(str(file_path))
        if mime2:
            if mime2.startswith("image/"):
                return "IMAGES"
            if mime2.startswith("audio/"):
                return "AUDIO"
            if mime2.startswith("video/"):
                return "VIDEO"
            if mime2 == "application/pdf":
                return "PDFS"
    except Exception:
        pass

    return "OTHER"

def resolve_collision(dest: Path) -> Path:
    if not dest.exists():
        return dest
    stem, suf = dest.stem, dest.suffix
    for i in range(1, 10000):
        cand = dest.parent / f"{stem} ({i}){suf}"
        if not cand.exists():
            return cand
    return dest.parent / f"{stem}__COLLISION__{now_stamp()}{suf}"

def sanitize_basename(name: str, max_len: int) -> str:
    name = re.sub(r"\s+", " ", name).strip()
    name = name.rstrip(" .")
    name = re.sub(r'[<>:"/\\|?*\x00-\x1F]', "_", name)
    if len(name) > max_len:
        name = name[:max_len].rstrip(" .")
    return name if name else "untitled"

def rule_based_rename_suggestion(fp: Path, max_len: int) -> str:
    stem = fp.stem
    suf = fp.suffix
    s = stem
    s = re.sub(r"\s*\(\d+\)$", "", s)
    s = re.sub(r"\s*-\s*Copy$", "", s, flags=re.IGNORECASE)
    s = re.sub(r"\s*copy\s*\d*$", "", s, flags=re.IGNORECASE)
    s = sanitize_basename(s, max_len=max_len)
    return f"{s}{suf}"

def read_sample_text(fp: Path, max_bytes: int) -> str:
    try:
        with open(fp, "rb") as f:
            data = f.read(max_bytes)
        return data.decode("utf-8", errors="ignore")
    except Exception:
        return ""

def cosine(a, b) -> float:
    dot = 0.0
    na = 0.0
    nb = 0.0
    for x, y in zip(a, b):
        dot += x * y
        na += x * x
        nb += y * y
    if na <= 0 or nb <= 0:
        return 0.0
    return dot / (math.sqrt(na) * math.sqrt(nb))

def scan_files(roots: List[Path], cfg: dict, run_root: Path, follow_symlinks: bool) -> List[Path]:
    """
    Fast-ish iterative scan. Excludes run_root and configured excluded folders and globs.
    """
    exclude_globs = [norm_path(Path(x)) for x in (cfg.get("exclude_globs") or [])]
    include_globs = [norm_path(Path(x)) for x in (cfg.get("include_globs") or [])]

    limits = cfg.get("limits") or {}
    max_files = int(limits.get("max_files", 0) or 0)
    max_size_mb = float(limits.get("max_file_size_mb", 0) or 0)
    max_size_bytes = int(max_size_mb * 1024 * 1024) if max_size_mb > 0 else 0

    out: List[Path] = []
    run_root_n = norm_path(run_root)

    for root in roots:
        if not root.exists():
            continue

        stack = [root]
        while stack:
            d = stack.pop()
            try:
                d_n = norm_path(d)
                if d_n.lower().startswith(run_root_n.lower()):
                    continue
                if not should_include(d_n, include_globs):
                    continue
                if matches_any_glob(d_n, exclude_globs):
                    continue
                if is_excluded_dirname(d.name, cfg):
                    continue

                with os.scandir(d) as it:
                    for entry in it:
                        try:
                            p = Path(entry.path)
                            if entry.is_dir(follow_symlinks=follow_symlinks):
                                if is_excluded_dirname(p.name, cfg):
                                    continue
                                p_n = norm_path(p)
                                if p_n.lower().startswith(run_root_n.lower()):
                                    continue
                                if matches_any_glob(p_n, exclude_globs):
                                    continue
                                if not should_include(p_n, include_globs):
                                    continue
                                stack.append(p)
                            elif entry.is_file(follow_symlinks=follow_symlinks):
                                p_n = norm_path(p)
                                if matches_any_glob(p_n, exclude_globs):
                                    continue
                                if not should_include(p_n, include_globs):
                                    continue
                                if max_size_bytes > 0:
                                    try:
                                        if entry.stat().st_size > max_size_bytes:
                                            continue
                                    except Exception:
                                        pass
                                out.append(p)
                                # Progress: emit periodic scan updates for GUI
                                if _progress_on() and (len(out) == 1 or (len(out) % 25) == 0):
                                    _emit_progress('SCAN', len(out), 0, str(p), 'FOUND')
                                if max_files > 0 and len(out) >= max_files:
                                    return out
                        except Exception:
                            continue
            except Exception:
                continue

    return out

def find_denest_actions(root: Path, max_chain: int, cfg: dict) -> List[Tuple[Path, Path, str, List[Path]]]:
    """
    Detect a chain of single-child folders ending in files. Propose moving leaf files to chain head.
    Returns: (file, proposed_dst_placeholder, reason, chain_dirs)
    """
    actions: List[Tuple[Path, Path, str, List[Path]]] = []
    for dirpath, dirnames, filenames in os.walk(root):
        p = Path(dirpath)
        if is_excluded_dirname(p.name, cfg):
            dirnames[:] = []
            continue
        if filenames:
            continue
        if len(dirnames) == 1:
            chain = [p]
            cur = p
            depth = 0
            while depth < max_chain:
                try:
                    kids = [d for d in cur.iterdir() if d.is_dir() and not is_excluded_dirname(d.name, cfg)]
                    files = [f for f in cur.iterdir() if f.is_file()]
                except Exception:
                    break
                if files or len(kids) != 1:
                    break
                cur = kids[0]
                chain.append(cur)
                depth += 1

            leaf = chain[-1]
            try:
                leaf_files = [f for f in leaf.iterdir() if f.is_file()]
            except Exception:
                leaf_files = []

            if leaf_files and len(chain) >= 3:
                head = chain[0]
                for f in leaf_files:
                    actions.append((f, head / f.name, f"denest_chain_len={len(chain)}", chain))
    return actions

def nlp_cluster_files(cfg: dict, files: List[Path], run_dir: Path, ledger: Path) -> Dict[str, int]:
    nlp_cfg = (cfg.get("nlp") or {}).get("embeddings") or {}
    if not nlp_cfg.get("enabled", False):
        return {}

    try:
        from sentence_transformers import SentenceTransformer
    except Exception as e:
        write_jsonl(ledger, {"ts": iso_now(), "event": "nlp_disabled_missing_dep", "error": str(e)})
        return {}

    model_id = nlp_cfg.get("model_id", "sentence-transformers/all-MiniLM-L6-v2")
    only_exts = set([e.lower() for e in (nlp_cfg.get("only_extensions") or [])])
    sample_bytes = int(nlp_cfg.get("sample_text_bytes", 4096))
    thr = float(nlp_cfg.get("cluster_cosine_threshold", 0.86))

    model = SentenceTransformer(model_id)

    reps: List[str] = []
    eligible: List[Path] = []
    for fp in files:
        if only_exts and ext_lower(fp.name) not in only_exts:
            continue
        txt = read_sample_text(fp, sample_bytes)
        reps.append(f"{fp.name}\n{txt[:800]}")
        eligible.append(fp)

    if not eligible:
        return {}

    embs = model.encode(reps, normalize_embeddings=True, show_progress_bar=False)
    centers: List[List[float]] = []
    out: Dict[str, int] = {}

    for i, fp in enumerate(eligible):
        v = embs[i].tolist()
        assigned = None
        best = -1.0
        for ci, c in enumerate(centers):
            s = cosine(v, c)
            if s > best:
                best = s
                assigned = ci
        if assigned is None or best < thr:
            centers.append(v)
            assigned = len(centers) - 1
        out[str(fp)] = int(assigned)

    out_json = run_dir / "nlp_clusters.json"
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2)
    write_jsonl(ledger, {"ts": iso_now(), "event": "nlp_clusters_written", "path": str(out_json), "clusters": len(centers)})
    return out

def root_tag_for_path(fp: Path, roots: List[Path]) -> str:
    fp_n = norm_path(fp).lower()
    best = ""
    best_len = -1
    for r in roots:
        r_n = norm_path(r).lower()
        if fp_n.startswith(r_n) and len(r_n) > best_len:
            best = norm_path(r)
            best_len = len(r_n)
    return best

def target_base_for_file(cfg: dict, run_dir: Path, fp: Path, roots: List[Path]) -> Path:
    mode = (cfg.get("target_mode") or "stage").lower()
    if mode == "stage":
        return run_dir / "_TARGET"
    # in_place
    rtag = root_tag_for_path(fp, roots)
    if rtag:
        return Path(rtag) / "BUCKETS"
    # fallback to stage if we can't resolve
    return run_dir / "_TARGET"

def plan_actions(cfg: dict, run_dir: Path, roots: List[Path]) -> None:
    plan_path = run_dir / "plan.csv"
    ledger = run_dir / "run_ledger.jsonl"
    safe_mkdir(run_dir)

    run_root = Path(cfg.get("run_root") or r"F:\LitigationOS\_OrganizeAI")
    safe_mkdir(run_root)

    follow_symlinks = bool(cfg.get("follow_symlinks", False))

    # Denest actions per root
    denest_cfg = cfg.get("denest") or {}
    denest_enabled = bool(denest_cfg.get("enabled", True))
    denest_max = int(denest_cfg.get("max_chain", 8))
    denest_actions: List[Tuple[Path, Path, str, List[Path]]] = []
    if denest_enabled:
        for r in roots:
            denest_actions.extend(find_denest_actions(r, denest_max, cfg))

    files = scan_files(roots, cfg, run_root=run_root, follow_symlinks=follow_symlinks)

    # Optional NLP clusters
    cluster_map = nlp_cluster_files(cfg, files, run_dir, ledger)

    rename_cfg = cfg.get("rename") or {}
    rename_enabled = bool(rename_cfg.get("enabled", False))
    rename_max_len = int(rename_cfg.get("max_len", 120))

    # Plan writing
    with open(plan_path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(PLAN_COLUMNS)

        # De-nest proposals
        for src, _, reason, chain in denest_actions:
            tbase = target_base_for_file(cfg, run_dir, src, roots)
            # Stage denested into a dedicated folder under target base
            dest = resolve_collision(tbase / "DENESTED" / src.name)
            st = None
            try:
                st = src.stat()
                sizeb = st.st_size
                mtime = datetime.fromtimestamp(st.st_mtime).isoformat(timespec="seconds")
            except Exception:
                sizeb = ""
                mtime = ""
            w.writerow([
                "MOVE", str(src), str(dest), "", reason, "0.80",
                sizeb, mtime, "", "",
                root_tag_for_path(src, roots), "DENEST"
            ])
            write_jsonl(ledger, {"ts": iso_now(), "event":"plan_denest", "src":str(src), "dst":str(dest), "reason":reason, "chain":[str(x) for x in chain]})

        # Bucketization proposals
        n_files = len(files)
        if _progress_on():
            iter_files = enumerate(files, start=1)
        else:
            iter_files = tqdm(files, desc="Planning bucketization") if tqdm else files

        for item in iter_files:
            if _progress_on():
                i, fp = item
                _emit_progress("PLAN", i, n_files, str(fp), "BUCKETIZE")
            else:
                fp = item
            bucket = classify_bucket(cfg, fp)
            tbase = target_base_for_file(cfg, run_dir, fp, roots)
            dest_dir = (tbase / bucket) if (tbase.name == "BUCKETS") else (tbase / "BUCKETS" / bucket)
            dest = resolve_collision(dest_dir / fp.name)

            proposed = ""
            if rename_enabled:
                proposed = rule_based_rename_suggestion(fp, max_len=rename_max_len)

            try:
                st = fp.stat()
                sizeb = st.st_size
                mtime = datetime.fromtimestamp(st.st_mtime).isoformat(timespec="seconds")
            except Exception:
                sizeb = ""
                mtime = ""

            cid = cluster_map.get(str(fp), "")
            w.writerow([
                "MOVE", str(fp), str(dest), bucket, f"bucket={bucket}", "0.95",
                sizeb, mtime, cid, proposed,
                root_tag_for_path(fp, roots), ""
            ])
            write_jsonl(ledger, {"ts": iso_now(), "event":"plan_bucket", "src":str(fp), "dst":str(dest), "bucket":bucket})

    # LAST_RUN pointer
    last_run = run_root / "LAST_RUN.txt"
    last_run.write_text(str(run_dir), encoding="utf-8")

    # Summary
    summary = summarize_plan(plan_path)
    (run_dir / "run_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    (run_dir / "run_summary.md").write_text(render_summary_md(summary), encoding="utf-8")

    print(f"PLAN COMPLETE: {plan_path}")
    print(f"LAST_RUN: {last_run}")

def summarize_plan(plan_path: Path) -> dict:
    import collections
    counts = collections.Counter()
    buckets = collections.Counter()
    rows = 0
    bytes_total = 0
    try:
        with open(plan_path, "r", encoding="utf-8") as f:
            rdr = csv.DictReader(f)
            for r in rdr:
                rows += 1
                counts[r.get("action","")] += 1
                b = r.get("bucket","")
                if b:
                    buckets[b] += 1
                try:
                    bytes_total += int(r.get("size_bytes") or 0)
                except Exception:
                    pass
    except Exception:
        pass
    return {
        "plan": str(plan_path),
        "rows": rows,
        "actions": dict(counts),
        "buckets": dict(buckets),
        "bytes_total": bytes_total,
    }

def render_summary_md(summary: dict) -> str:
    lines = []
    lines.append(f"# Run Summary")
    lines.append("")
    lines.append(f"- Plan: `{summary.get('plan','')}`")
    lines.append(f"- Rows: {summary.get('rows',0)}")
    lines.append(f"- Total bytes: {summary.get('bytes_total',0)}")
    lines.append("")
    lines.append("## Actions")
    for k,v in (summary.get("actions") or {}).items():
        lines.append(f"- {k}: {v}")
    lines.append("")
    lines.append("## Buckets")
    for k,v in sorted((summary.get("buckets") or {}).items()):
        lines.append(f"- {k}: {v}")
    lines.append("")
    return "\n".join(lines)

def apply_plan(cfg: dict, run_dir: Path) -> None:
    plan_path = run_dir / "plan.csv"
    ledger = run_dir / "run_ledger.jsonl"
    if not plan_path.exists():
        raise FileNotFoundError(plan_path)

    move_mode = (cfg.get("move_mode") or "move").lower()
    assert move_mode in ("move","copy")

    denest_cfg = cfg.get("denest") or {}
    cleanup_empty = bool(denest_cfg.get("cleanup_empty_dirs", False))

    undo_path = run_dir / "undo.csv"
    with open(plan_path, "r", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    with open(undo_path, "w", newline="", encoding="utf-8") as uf:
        uw = csv.writer(uf)
        uw.writerow(["undo_action","src","dst","note"])

        n_total = len(rows)
        if _progress_on():
            iter_rows = enumerate(rows, start=1)
        else:
            iter_rows = tqdm(rows, desc="Applying plan") if tqdm else rows

        for item in iter_rows:
            if _progress_on():
                i, row = item
            else:
                i, row = 0, item

            action = row.get("action","MOVE").upper()
            src = Path(row.get("src",""))
            dst = Path(row.get("dst",""))

            if _progress_on():
                _emit_progress("APPLY", i, n_total, str(src), action)

            if not src.exists():
                write_jsonl(ledger, {"ts": iso_now(), "event":"skip_missing_src", "src":str(src), "dst":str(dst)})
                continue

            safe_mkdir(dst.parent)
            final_dst = resolve_collision(dst)

            try:
                if move_mode == "copy":
                    shutil.copy2(src, final_dst)
                    write_jsonl(ledger, {"ts": iso_now(), "event":"copied", "src":str(src), "dst":str(final_dst)})
                    uw.writerow(["DELETE", str(final_dst), "", "undo copy by deleting dst"])
                else:
                    # move
                    shutil.move(str(src), str(final_dst))
                    write_jsonl(ledger, {"ts": iso_now(), "event":"moved", "src":str(src), "dst":str(final_dst)})
                    uw.writerow(["MOVE_BACK", str(final_dst), str(src), "undo move by moving dst back to src"])
            except Exception as e:
                write_jsonl(ledger, {"ts": iso_now(), "event":"error", "src":str(src), "dst":str(final_dst), "error":str(e)})
                uw.writerow(["NONE", str(src), str(final_dst), f"error={e}"])

    # Optional cleanup: remove empty dirs for denest chains (best-effort)
    if cleanup_empty:
        try:
            cleanup_empty_directories(run_dir, ledger)
        except Exception as e:
            write_jsonl(ledger, {"ts": iso_now(), "event":"cleanup_error", "error": str(e)})

    print(f"APPLY COMPLETE: {run_dir}")
    print(f"UNDO FILE: {undo_path}")

def cleanup_empty_directories(run_dir: Path, ledger: Path) -> None:
    # Best-effort: remove empty directories under roots that were denest sources
    plan_path = run_dir / "plan.csv"
    if not plan_path.exists():
        return
    dirs: Set[Path] = set()
    with open(plan_path, "r", encoding="utf-8") as f:
        rdr = csv.DictReader(f)
        for r in rdr:
            if (r.get("flags") or "").upper() == "DENEST":
                src = Path(r.get("src",""))
                # include parent chain candidates
                p = src.parent
                for _ in range(10):
                    dirs.add(p)
                    if p.parent == p:
                        break
                    p = p.parent
    # remove in deepest-first order
    for d in sorted(dirs, key=lambda x: len(norm_path(x)), reverse=True):
        try:
            if d.exists() and d.is_dir():
                if not any(d.iterdir()):
                    d.rmdir()
                    write_jsonl(ledger, {"ts": iso_now(), "event":"rmdir_empty", "dir": str(d)})
        except Exception:
            pass

def main():
    ap = argparse.ArgumentParser(description="OrganizerStack ULT3 (PLAN/VALIDATE/APPLY/UNDO).")
    ap.add_argument("--config", default="config.yaml")
    ap.add_argument("--mode", choices=["plan","apply"], default=None)
    ap.add_argument("--root", action="append", default=[], help="Override roots from config (can repeat).")
    ap.add_argument("--run_dir", default="", help="Existing run folder for apply; if empty, uses LAST_RUN or creates new.")
    args = ap.parse_args()

    cfg = load_cfg(Path(args.config))
    mode = args.mode or (cfg.get("mode") or "plan")

    roots = [Path(p) for p in (args.root if args.root else (cfg.get("roots") or []))]
    run_root = Path(cfg.get("run_root") or r"F:\LitigationOS\_OrganizeAI")
    safe_mkdir(run_root)

    # determine run_dir
    run_dir = None
    if args.run_dir:
        run_dir = Path(args.run_dir)
    elif mode == "apply":
        last_run = run_root / "LAST_RUN.txt"
        if last_run.exists():
            try:
                run_dir = Path(last_run.read_text(encoding="utf-8").strip())
            except Exception:
                run_dir = None

    if run_dir is None:
        run_dir = run_root / f"RUN_{now_stamp()}"
    safe_mkdir(run_dir)

    ledger = run_dir / "run_ledger.jsonl"
    write_jsonl(ledger, {"ts": iso_now(), "event":"run_start", "mode":mode, "roots":[str(r) for r in roots]})

    if mode == "plan":
        plan_actions(cfg, run_dir, roots)
    else:
        apply_plan(cfg, run_dir)

    write_jsonl(ledger, {"ts": iso_now(), "event":"run_end", "mode":mode})


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
