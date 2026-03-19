from __future__ import annotations
import argparse, json, re, hashlib
from datetime import datetime
from pathlib import Path
from io_extractors import iter_line_records

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
IMPORTS = ROOT / "imports"

STOP = {
    "the","and","for","with","from","that","this","into","your","have","will","then","only","they","their",
    "order","hearing","transcript","target","quote","lock","page","line","exact","extract","promotion","pending"
}

def load_json(path: Path, default):
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))

def save_json(path: Path, payload):
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

def tokenize(s: str) -> list[str]:
    return [t for t in re.findall(r"[A-Za-z0-9]{3,}", (s or "").lower()) if t not in STOP]

def date_tokens(*vals):
    out = []
    pats = [
        (r"(20\d{2})[-_/](\d{2})[-_/](\d{2})", lambda m: f"{m.group(1)}-{m.group(2)}-{m.group(3)}"),
        (r"(?<!\d)(\d{1,2})/(\d{1,2})/(20\d{2})(?!\d)", lambda m: f"{int(m.group(3)):04d}-{int(m.group(1)):02d}-{int(m.group(2)):02d}")
    ]
    for v in vals:
        txt = str(v or "")
        for pat, fn in pats:
            for m in re.finditer(pat, txt):
                out.append(fn(m))
    return list(dict.fromkeys(out))

def target_seed_tokens(q: dict) -> list[str]:
    toks = []
    toks += tokenize(q.get("label",""))
    toks += tokenize(q.get("pinpoint",""))
    toks += tokenize(q.get("source_ref",""))
    toks += [t for dt in date_tokens(q.get("hearing_or_order_date"), q.get("label"), q.get("source_ref")) for t in dt.split("-")]
    # Favor judicial terms if lane/source suggests it
    if "MEEK3" == q.get("lane"):
        toks += ["ppo","contempt","show","cause"]
    if "MEEK2" == q.get("lane"):
        toks += ["parenting","time","custody","order"]
    # Dedup preserve order
    out=[]
    for t in toks:
        if t not in out:
            out.append(t)
    return out[:24]

def collect_corpus():
    folders = [IMPORTS / "transcripts", IMPORTS / "orders_text"]
    files = []
    for folder in folders:
        if not folder.exists():
            continue
        for p in folder.rglob("*"):
            if p.is_file() and p.suffix.lower() in {".txt",".md",".pdf",".docx",".json",".csv",".tsv"}:
                files.append(p)
    corpus = []
    for fp in sorted(files):
        recs = iter_line_records(fp)
        for r in recs:
            txt = r["text"]
            corpus.append({
                "file_path": str(fp.relative_to(ROOT)).replace("\\","/"),
                "page": r["page"],
                "line": r["line"],
                "text": txt,
                "text_lower": txt.lower(),
                "tokens": set(tokenize(txt)),
                "is_seed": fp.name.startswith("_seed_")
            })
    return corpus

def score_candidate(q: dict, row: dict) -> tuple[float, list[str]]:
    reasons = []
    qtokens = target_seed_tokens(q)
    if not qtokens:
        return 0.0, reasons
    rowtoks = row["tokens"]
    overlap = [t for t in qtokens if t in rowtoks]
    score = 0.0
    if overlap:
        score += min(0.75, 0.08 * len(overlap))
        reasons.append("token_overlap:" + ",".join(overlap[:8]))
    # Date signal
    for dt in date_tokens(q.get("hearing_or_order_date"), q.get("label"), q.get("source_ref")):
        if dt in row["text"] or dt.replace("-","/") in row["text"]:
            score += 0.25; reasons.append("date_match:"+dt)
    # Page/line explicit marker signal (transcript style)
    if re.search(r"\b(p\.?\s*\d+|page\s+\d+)\b", row["text_lower"]):
        score += 0.12; reasons.append("page_marker")
    if re.search(r"\b(l\.?\s*\d+|line\s+\d+)\b", row["text_lower"]):
        score += 0.12; reasons.append("line_marker")
    # Prefer non-seed artifacts for exact promotion
    if not row.get("is_seed"):
        score += 0.05
    # If quote_text_exact exists, exact substring match is a real promotion
    exact = (q.get("quote_text_exact") or "").strip()
    if exact and exact.lower() in row["text_lower"]:
        score = max(score, 0.98)
        reasons.append("exact_substring_match")
    return min(score, 1.0), reasons

def build_preview(q: dict, row: dict, score: float, reasons: list[str]) -> dict:
    quote_id = q.get("quote_id")
    hint = f"{row['file_path']}::p{row['page']}l{row['line']}"
    return {
        "preview_id": "QPV-" + hashlib.md5(f"{quote_id}|{hint}".encode()).hexdigest()[:10],
        "quote_id": quote_id,
        "lane": q.get("lane"),
        "file_path": row["file_path"],
        "page": row["page"],
        "line": row["line"],
        "pinpoint": f"p.{row['page']} l.{row['line']}",
        "score": round(score, 3),
        "candidate_text": row["text"][:500],
        "reasons": reasons,
        "provenance_jump_hints": [quote_id, hint, q.get("provenance_jump_hint")],
        "truth_tag": q.get("truth_tag", "UNVERIFIED"),
        "promotion_stage": "EXACT_READY" if "exact_substring_match" in reasons else "PREVIEW_READY",
        "resolution_target": "Review preview and promote exact quote into transcript_quotes.json once verified against transcript/order source."
    }

def maybe_promote_exact(q: dict, previews: list[dict]) -> dict | None:
    exact_ready = [p for p in previews if p.get("promotion_stage") == "EXACT_READY"]
    if not exact_ready:
        return None
    best = max(exact_ready, key=lambda p: p["score"])
    return {
        "quote_id": q.get("quote_id"),
        "promotion_type": "EXACT_QUOTE_PROMOTION",
        "file_path": best["file_path"],
        "pinpoint": best["pinpoint"],
        "quote_text_exact": best["candidate_text"],
        "score": best["score"],
        "provenance_jump_hints": best["provenance_jump_hints"],
        "truth_tag": "RECORD_RECITED" if q.get("truth_tag") in ("RECORD_RECITED","PROVEN") else q.get("truth_tag","UNVERIFIED"),
    }

def main() -> int:
    parser = argparse.ArgumentParser(description="Transcript exact-quote preview extractor with Quote-Lock promotion candidates")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    qpayload = load_json(DATA / "transcript_quotes.json", {"quotes": []})
    quotes = qpayload.get("quotes", [])
    corpus = collect_corpus()

    all_previews = []
    promotions = []
    by_quote = {}
    for q in quotes:
        # Only target transcript/order anchors without exact quote
        if q.get("quote_text_exact"):
            continue
        # Build top candidate previews
        previews = []
        for row in corpus:
            score, reasons = score_candidate(q, row)
            if score < 0.28:
                continue
            previews.append(build_preview(q, row, score, reasons))
        previews.sort(key=lambda p: (-p["score"], p["file_path"], p["page"], p["line"]))
        top = previews[:5]
        all_previews.extend(top)
        by_quote[q.get("quote_id")] = top
        promo = maybe_promote_exact(q, top)
        if promo:
            promotions.append(promo)

    # Apply exact promotions into transcript_quotes.json (append-only fields)
    promo_map = {p["quote_id"]: p for p in promotions}
    promoted_count = 0
    for q in quotes:
        p = promo_map.get(q.get("quote_id"))
        if not p:
            continue
        q["quote_text_exact"] = p["quote_text_exact"]
        q["pinpoint"] = p["pinpoint"]
        q["quote_lock_band"] = "EXACT_OR_NEAR_EXACT"
        q["truth_tag"] = p["truth_tag"]
        q["quote_preview"] = p["quote_text_exact"][:180]
        q["resolution_target"] = "Exact quote promoted from transcript/order corpus; verify and pin to filing packet."
        promoted_count += 1

    previews_payload = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "summary": {
            "corpus_line_count": len(corpus),
            "quote_targets_scanned": len(quotes),
            "preview_count": len(all_previews),
            "quotes_with_previews": len({p['quote_id'] for p in all_previews}),
            "promotion_candidates_count": sum(1 for p in all_previews if p.get("promotion_stage") == "PREVIEW_READY"),
            "exact_promoted_count": promoted_count,
        },
        "filters": {
            "lanes": sorted({p.get("lane") for p in all_previews if p.get("lane")}),
            "files": sorted({p.get("file_path") for p in all_previews}),
            "stages": ["PREVIEW_READY","EXACT_READY"],
        },
        "previews": all_previews,
    }
    promotions_payload = {
        "generated_at": previews_payload["generated_at"],
        "summary": {
            "exact_promotions": len(promotions),
            "quotes_total": len(quotes),
            "quotes_now_exact_or_near": sum(1 for q in quotes if q.get("quote_lock_band") == "EXACT_OR_NEAR_EXACT"),
        },
        "promotions": promotions,
        "resolution_targets": [
            "Drop transcript PDFs/TXT into imports/transcripts to unlock non-seed page-line previews and exact quote promotions.",
            "Use quote preview provenance jump hints to bind transcript lines into Quote-Lock and filing packets."
        ],
    }
    if not args.dry_run:
        save_json(DATA / "transcript_quotes.json", qpayload)
        save_json(DATA / "transcript_quote_previews.json", previews_payload)
        save_json(DATA / "transcript_quote_promotions.json", promotions_payload)
    print(json.dumps({"status":"ok","preview_count":len(all_previews),"exact_promotions":len(promotions)}, indent=2))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
