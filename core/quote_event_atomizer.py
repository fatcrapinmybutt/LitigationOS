from __future__ import annotations
import re
from typing import List, Dict, Tuple, Optional

DATE_RE = re.compile(r"\b(20\d{2}[-/]\d{1,2}[-/]\d{1,2}|\d{1,2}[-/]\d{1,2}[-/](20\d{2}|\d{2}))\b")
NEGATIVE_RE = re.compile(r"\b(liar|crazy|threat|violent|unstable|danger|contempt|violation|harass)\b", re.I)
PAGE_TAG_RE = re.compile(r"^\[PAGE\s+(\d+)\]\s*$", re.I)
PARA_TAG_RE = re.compile(r"^\[PARA\s+(\d+)\]\s+", re.I)

def quoteize_text(text: str, max_len: int = 1200) -> List[Tuple[int, int, str, Optional[int]]]:
    # Page-aware splitter: preserve [PAGE n] tags as hints.
    chunks: List[Tuple[int, int, str, Optional[int]]] = []
    current_page: Optional[int] = None
    pos = 0
    for block in re.split(r"\n\s*\n+", text):
        raw = block.strip()
        if not raw:
            continue
        m = PAGE_TAG_RE.match(raw)
        if m:
            current_page = int(m.group(1))
            continue
        start = text.find(block, pos)
        if start < 0:
            start = pos
        end = start + len(block)
        pos = end

        # Split long blocks on sentence-ish boundaries.
        parts = re.split(r"(?<=[\.\?!])\s{1,}", raw)
        buf = ""
        part_start = start
        cursor = start
        for part in parts:
            if not part:
                continue
            if len(buf) + len(part) + 1 <= max_len:
                if not buf:
                    part_start = cursor
                buf = (buf + " " + part).strip()
            else:
                if buf:
                    chunks.append((part_start, part_start + len(buf), buf, current_page))
                # hard split if one sentence still too long
                if len(part) <= max_len:
                    buf = part.strip()
                    part_start = cursor
                else:
                    i = 0
                    p = part.strip()
                    while i < len(p):
                        sub = p[i:i+max_len]
                        chunks.append((cursor + i, cursor + i + len(sub), sub, current_page))
                        i += max_len
                    buf = ""
            cursor += len(part) + 1
        if buf:
            chunks.append((part_start, part_start + len(buf), buf, current_page))
    return chunks

def eventize_quotes(quotes: List[Dict]) -> List[Dict]:
    events: List[Dict] = []
    for q in quotes:
        txt = q.get("text", "")
        low = txt.lower()
        dates = [m[0] if isinstance(m, tuple) else m for m in DATE_RE.findall(txt)]
        action = "mentioned_event"
        if "order" in low:
            action = "order_reference"
        elif "hearing" in low:
            action = "hearing_reference"
        elif "show cause" in low or "contempt" in low:
            action = "contempt_reference"
        elif "ppo" in low:
            action = "ppo_reference"
        elif "custody" in low or "parenting time" in low:
            action = "custody_parenting_reference"
        elif "rent" in low or "lease" in low or "sewage" in low or "utility" in low:
            action = "housing_reference"
        events.append({
            "action": action,
            "when_event_raw": dates[0] if dates else None,
            "negative_flag": bool(NEGATIVE_RE.search(txt)),
        })
    return events

def contradiction_pairs(quotes: List[Dict], limit: int = 40) -> List[Dict]:
    # Lightweight contradiction heuristic; not truth adjudication.
    pairs: List[Dict] = []
    positives = []
    negatives = []
    for q in quotes:
        t = q.get("text", "")
        low = t.lower()
        if any(k in low for k in ["did not", "never", "no ", "not "]):
            negatives.append(q)
        if any(k in low for k in ["did ", "was ", "were ", "has ", "have "]):
            positives.append(q)
    for a in negatives[:limit]:
        for b in positives[:limit]:
            if a.get("atom_id") == b.get("atom_id"):
                continue
            # weak overlap by keywords
            wa = set(re.findall(r"[a-z]{4,}", a.get("text","").lower()))
            wb = set(re.findall(r"[a-z]{4,}", b.get("text","").lower()))
            overlap = sorted(list(wa & wb))
            if len(overlap) >= 3:
                pairs.append({
                    "quote_a": a.get("quote_id"),
                    "quote_b": b.get("quote_id"),
                    "shared_terms": overlap[:10],
                    "confidence": "LOW_HEURISTIC"
                })
            if len(pairs) >= limit:
                return pairs
    return pairs
