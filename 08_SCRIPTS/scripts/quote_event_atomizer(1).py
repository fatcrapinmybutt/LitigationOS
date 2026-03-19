\
from __future__ import annotations
import re
from typing import List, Dict, Tuple

DATE_RE = re.compile(r"\b(20\d{2}[-/]\d{1,2}[-/]\d{1,2}|\d{1,2}[-/]\d{1,2}[-/](20\d{2}|\d{2}))\b")
SPLIT_RE = re.compile(r"(?:\n\s*\n+|(?<=[\.\?!])\s{2,})")

def quoteize_text(text: str, max_len: int = 1200) -> List[Tuple[int,int,str]]:
    chunks: List[Tuple[int,int,str]] = []
    pos = 0
    for part in SPLIT_RE.split(text):
        if not part:
            continue
        start = text.find(part, pos)
        if start < 0:
            start = pos
        end = start + len(part)
        pos = end
        part = part.strip()
        if not part:
            continue
        if len(part) <= max_len:
            chunks.append((start, end, part))
        else:
            i = 0
            while i < len(part):
                sub = part[i:i+max_len]
                chunks.append((start+i, start+i+len(sub), sub))
                i += max_len
    return chunks

def eventize_quotes(quotes: List[Dict]) -> List[Dict]:
    events: List[Dict] = []
    for q in quotes:
        txt = q.get("text","")
        dates = DATE_RE.findall(txt)
        low = txt.lower()
        action = "mentioned_event"
        if "order" in low:
            action = "order_reference"
        elif "hearing" in low:
            action = "hearing_reference"
        elif "ppo" in low:
            action = "ppo_reference"
        elif "custody" in low or "parenting time" in low:
            action = "custody_parenting_reference"
        events.append({
            "action": action,
            "when_event_raw": dates[0][0] if dates else None,
            "support_quote_text": txt[:240]
        })
    return events
