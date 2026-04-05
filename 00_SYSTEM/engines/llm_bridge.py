#!/usr/bin/env python3
"""
llm_bridge.py - Universal Ollama LLM interface for all LitigationOS engines.

Provides a single entry point for all LLM operations: ask, embed, classify,
summarize, extract legal entities, and batch processing.

Usage:
    from llm_bridge import llm_ask, llm_embed, llm_classify, llm_summarize
    from llm_bridge import llm_extract_legal_entities, llm_analyze_legal, llm_batch

CLI:
    python llm_bridge.py --test
    python llm_bridge.py --ask "What is MCR 7.212?"
    python llm_bridge.py --extract "MCR 2.003 requires disqualification..."
"""

import os
import sys
import json
import time
import logging
import argparse
import traceback

logger = logging.getLogger(__name__)

# ── Config ───────────────────────────────────────────────────────────────────
OLLAMA_URL      = os.environ.get("OLLAMA_URL", "http://localhost:11434")
LLM_MODEL       = os.environ.get("LLM_MODEL", "qwen2.5:7b")
EMBED_MODEL     = os.environ.get("LLM_EMBED_MODEL", "nomic-embed-text")
RATE_LIMIT_SEC  = float(os.environ.get("LLM_RATE_LIMIT", "1.0"))
TIMEOUT_SEC     = int(os.environ.get("LLM_TIMEOUT", "600"))
MAX_RETRIES     = int(os.environ.get("LLM_RETRIES", "3"))

_last_request_ts = 0.0

# ── Transport layer ──────────────────────────────────────────────────────────
_USE_OLLAMA_PKG = False
_ollama_client = None
try:
    import ollama as _ollama_pkg
    from httpx import Timeout as _HttpxTimeout
    _ollama_client = _ollama_pkg.Client(
        host=OLLAMA_URL,
        timeout=_HttpxTimeout(TIMEOUT_SEC, connect=30.0),
    )
    _USE_OLLAMA_PKG = True
except (ImportError, Exception):
    _ollama_pkg = None

try:
    import requests as _requests
except ImportError:
    _requests = None


def _rate_limit():
    """Enforce minimum delay between requests."""
    global _last_request_ts
    elapsed = time.time() - _last_request_ts
    if elapsed < RATE_LIMIT_SEC:
        time.sleep(RATE_LIMIT_SEC - elapsed)
    _last_request_ts = time.time()


def _call_generate(prompt: str, system_prompt: str = None,
                   temperature: float = 0.3, max_tokens: int = 4096) -> str:
    """Low-level generate call with retry + exponential backoff."""
    for attempt in range(1, MAX_RETRIES + 1):
        _rate_limit()
        try:
            if _USE_OLLAMA_PKG:
                opts = {"temperature": temperature, "num_predict": max_tokens}
                kwargs = dict(model=LLM_MODEL, prompt=prompt, options=opts, stream=False)
                if system_prompt:
                    kwargs["system"] = system_prompt
                resp = _ollama_client.generate(**kwargs)
                text = resp.get("response", "").strip()
                if not text and resp.get("error"):
                    raise RuntimeError(f"Ollama error: {resp['error']}")
                return text
            else:
                payload = {
                    "model": LLM_MODEL,
                    "prompt": prompt,
                    "stream": False,
                    "options": {"temperature": temperature, "num_predict": max_tokens},
                }
                if system_prompt:
                    payload["system"] = system_prompt
                r = _requests.post(f"{OLLAMA_URL}/api/generate", json=payload,
                                   timeout=TIMEOUT_SEC)
                r.raise_for_status()
                data = r.json()
                if "error" in data:
                    raise RuntimeError(f"Ollama error: {data['error']}")
                return data.get("response", "").strip()
        except Exception as exc:
            if attempt == MAX_RETRIES:
                raise RuntimeError(
                    f"LLM generate failed after {MAX_RETRIES} attempts: {exc}"
                ) from exc
            wait = 2 ** attempt
            print(f"  ⚠ Attempt {attempt}/{MAX_RETRIES} failed ({exc}), retrying in {wait}s …")
            time.sleep(wait)
    return ""


def _call_embed(text: str) -> list:
    """Low-level embedding call with retry."""
    for attempt in range(1, MAX_RETRIES + 1):
        _rate_limit()
        try:
            if _USE_OLLAMA_PKG:
                resp = _ollama_client.embeddings(model=EMBED_MODEL, prompt=text)
                return resp.get("embedding", [])
            else:
                payload = {"model": EMBED_MODEL, "prompt": text}
                r = _requests.post(f"{OLLAMA_URL}/api/embeddings", json=payload,
                                   timeout=TIMEOUT_SEC)
                r.raise_for_status()
                data = r.json()
                if "error" in data:
                    raise RuntimeError(f"Ollama error: {data['error']}")
                return data.get("embedding", [])
        except Exception as exc:
            if attempt == MAX_RETRIES:
                raise RuntimeError(
                    f"Embedding failed after {MAX_RETRIES} attempts: {exc}"
                ) from exc
            wait = 2 ** attempt
            time.sleep(wait)
    return []


# ── Public API ───────────────────────────────────────────────────────────────

def llm_ask(prompt: str, system_prompt: str = None,
            temperature: float = 0.3, max_tokens: int = 4096) -> str:
    """Send a prompt to the LLM and return the response text."""
    return _call_generate(prompt, system_prompt=system_prompt,
                          temperature=temperature, max_tokens=max_tokens)


def llm_embed(text: str) -> list:
    """Return an embedding vector for *text* using nomic-embed-text."""
    return _call_embed(text)


def llm_classify(text: str, categories: list) -> str:
    """Classify *text* into one of the given *categories*."""
    cats = ", ".join(categories)
    prompt = (
        f"Classify the following text into exactly one of these categories: {cats}\n\n"
        f"Text: {text}\n\n"
        f"Respond with ONLY the category name, nothing else."
    )
    system = (
        "You are a precise text classifier for litigation documents. "
        "Respond with ONLY the category name — no explanation, no punctuation. "
        "If the text does not clearly fit any category, pick the closest match."
    )
    result = _call_generate(prompt, system_prompt=system, temperature=0.1)
    # Normalise: pick closest match if LLM added extra words
    result_lower = result.lower().strip().rstrip(".")
    for cat in categories:
        if cat.lower() in result_lower:
            return cat
    return result.strip()


def llm_summarize(text: str, max_words: int = 200) -> str:
    """Summarize *text* in at most *max_words* words."""
    prompt = (
        f"Summarize the following text in no more than {max_words} words. "
        f"Be concise and capture the key points.\n\n{text}"
    )
    system = (
        "You are a legal document summarizer. Rules:\n"
        "1. Preserve party names, dates, case numbers, and legal citations exactly\n"
        "2. Lead with the most legally significant finding\n"
        "3. Never add information not present in the source text"
    )
    return _call_generate(prompt, system_prompt=system, temperature=0.2)


def llm_extract_legal_entities(text: str) -> dict:
    """Extract legal entities from *text*.

    Returns dict with keys: statutes, cases, rules, parties, dates, courts.
    Each value is a list of strings.
    """
    prompt = (
        "Extract all legal entities from the following text.\n"
        "Return a JSON object with these exact keys (each a list of strings):\n"
        '  "statutes" — MCL sections (e.g., "MCL 722.23")\n'
        '  "cases" — case names (e.g., "Vodvarka v Grasmeyer")\n'
        '  "rules" — court rules (e.g., "MCR 2.003(D)")\n'
        '  "parties" — person/entity names mentioned\n'
        '  "dates" — dates in any format found\n'
        '  "courts" — court names mentioned\n'
        "If a category has no matches, use an empty list.\n"
        "Extract ONLY entities explicitly stated in the text — never infer or fabricate.\n\n"
        f"Text: {text}\n\n"
        "Respond with ONLY the JSON object, no markdown fences or extra text."
    )
    system = (
        "You are a legal entity extraction engine. "
        "Return only valid JSON. Extract only what is explicitly present in the text."
    )
    raw = _call_generate(prompt, system_prompt=system, temperature=0.1)
    # Strip markdown fences if present
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        lines = cleaned.split("\n")
        lines = [l for l in lines if not l.strip().startswith("```")]
        cleaned = "\n".join(lines)
    try:
        parsed = json.loads(cleaned)
    except json.JSONDecodeError:
        parsed = {
            "statutes": [], "cases": [], "rules": [],
            "parties": [], "dates": [], "courts": [],
            "_raw": raw,
        }
    # Ensure all expected keys exist
    for key in ("statutes", "cases", "rules", "parties", "dates", "courts"):
        if key not in parsed:
            parsed[key] = []
    return parsed


def llm_analyze_legal(text: str, analysis_type: str) -> str:
    """Perform a legal analysis of *text*.

    analysis_type: one of "violation", "defense", "damages", "procedural".
    """
    type_prompts = {
        "violation": (
            "Analyze the following text for legal violations. Step by step:\n"
            "1. Identify the specific statute, rule, or standard potentially violated\n"
            "2. Quote or paraphrase the relevant requirement\n"
            "3. Explain how the conduct described violates that requirement\n"
            "4. Assess severity: CLEAR VIOLATION / PROBABLE / POSSIBLE\n"
            "Only cite authorities present in the text. Mark others as UNVERIFIED."
        ),
        "defense": (
            "Analyze the following text and identify potential legal defenses. Step by step:\n"
            "1. Identify each available defense\n"
            "2. Cite the relevant MCR, MCL, or case law authority\n"
            "3. Explain how the facts support or undermine each defense\n"
            "4. Rank defenses by strength: STRONG / MODERATE / WEAK\n"
            "Only cite authorities present in the text. Mark others as UNVERIFIED."
        ),
        "damages": (
            "Analyze the following text for potential damages claims. Step by step:\n"
            "1. Identify each category of damages (compensatory, punitive, statutory)\n"
            "2. Connect each category to specific evidence in the text\n"
            "3. Note any quantifiable amounts mentioned\n"
            "4. Identify gaps where additional evidence is needed\n"
            "Do not fabricate dollar amounts — only report figures stated in the text."
        ),
        "procedural": (
            "Analyze the following text for procedural issues. Step by step:\n"
            "1. Identify applicable deadlines and filing requirements under MCR\n"
            "2. Flag any jurisdictional or venue issues\n"
            "3. Note service of process requirements\n"
            "4. Identify potential procedural defenses\n"
            "Only cite MCR sections present in the text. Mark others as UNVERIFIED."
        ),
    }
    instruction = type_prompts.get(
        analysis_type,
        f"Perform a '{analysis_type}' legal analysis of the following text."
    )
    prompt = f"{instruction}\n\nText: {text}"
    system = (
        "You are an expert Michigan litigation analyst. "
        "Cite specific MCRs, Michigan statutes, and case law where applicable. "
        "Only cite authorities present in the provided text — if not present, write UNVERIFIED. "
        "Never fabricate case names or statute numbers."
    )
    return _call_generate(prompt, system_prompt=system, temperature=0.3)


def llm_batch(prompts: list, system_prompt: str = None) -> list:
    """Process a list of prompts sequentially, printing progress."""
    results = []
    total = len(prompts)
    for i, p in enumerate(prompts, 1):
        print(f"  → Batch {i}/{total} …", end="\r")
        results.append(llm_ask(p, system_prompt=system_prompt))
    print(f"  ✓ Batch complete: {total} prompts processed")
    return results


# ── Self-test ────────────────────────────────────────────────────────────────

def _self_test():
    """Run a quick self-test of all llm_bridge functions."""
    print("=" * 60)
    print("  LLM Bridge Self-Test")
    print(f"  Model       : {LLM_MODEL}")
    print(f"  Embed model : {EMBED_MODEL}")
    print(f"  Endpoint    : {OLLAMA_URL}")
    print(f"  Transport   : {'ollama pkg' if _USE_OLLAMA_PKG else 'requests'}")
    print("=" * 60)

    passed = 0
    failed = 0

    # 1. Connectivity check
    print("\n[1/7] Ollama connectivity …")
    try:
        r = _requests.get(f"{OLLAMA_URL}/api/tags", timeout=10)
        r.raise_for_status()
        models = [m["name"] for m in r.json().get("models", [])]
        print(f"  ✓ Connected – {len(models)} model(s) available")
        for m in models:
            tag = "◆" if LLM_MODEL in m or EMBED_MODEL in m else " "
            print(f"    {tag} {m}")
        passed += 1
    except Exception as exc:
        print(f"  ✗ Cannot reach Ollama: {exc}")
        failed += 1
        print(f"\nResult: {passed} passed, {failed} failed (Ollama offline)")
        return failed == 0

    # 2. llm_ask
    print("\n[2/7] llm_ask …")
    try:
        ans = llm_ask("Respond with only the word 'OK'.", temperature=0.0)
        ok = len(ans) > 0
        print(f"  {'✓' if ok else '✗'} Response ({len(ans)} chars): {ans[:80]}")
        passed += 1 if ok else 0
        failed += 0 if ok else 1
    except Exception as exc:
        print(f"  ✗ {exc}")
        failed += 1

    # 3. llm_embed
    print("\n[3/7] llm_embed …")
    try:
        vec = llm_embed("test embedding")
        ok = isinstance(vec, list) and len(vec) > 0
        print(f"  {'✓' if ok else '✗'} Embedding dim = {len(vec)}")
        passed += 1 if ok else 0
        failed += 0 if ok else 1
    except Exception as exc:
        print(f"  ✗ {exc}")
        failed += 1

    # 4. llm_classify
    print("\n[4/7] llm_classify …")
    try:
        cat = llm_classify("The judge was biased against the defendant",
                           ["procedural", "substantive", "ethical"])
        ok = len(cat) > 0
        print(f"  {'✓' if ok else '✗'} Classification: {cat}")
        passed += 1 if ok else 0
        failed += 0 if ok else 1
    except Exception as exc:
        print(f"  ✗ {exc}")
        failed += 1

    # 5. llm_summarize
    print("\n[5/7] llm_summarize …")
    try:
        summary = llm_summarize("Michigan Court Rule 7.212 governs the form and "
                                "content of briefs filed in the Michigan Court of "
                                "Appeals. It specifies requirements for cover pages, "
                                "tables of contents, statement of facts, and argument "
                                "sections.", max_words=30)
        ok = len(summary) > 0
        print(f"  {'✓' if ok else '✗'} Summary: {summary[:100]}")
        passed += 1 if ok else 0
        failed += 0 if ok else 1
    except Exception as exc:
        print(f"  ✗ {exc}")
        failed += 1

    # 6. llm_extract_legal_entities
    print("\n[6/7] llm_extract_legal_entities …")
    try:
        ents = llm_extract_legal_entities(
            "MCR 2.003 requires disqualification when bias is shown "
            "per Cain v Dept of Corrections, 451 Mich 470 (1996)"
        )
        ok = isinstance(ents, dict) and any(
            len(ents.get(k, [])) > 0 for k in ("rules", "cases", "statutes")
        )
        print(f"  {'✓' if ok else '✗'} Entities: {json.dumps(ents, indent=2)[:200]}")
        passed += 1 if ok else 0
        failed += 0 if ok else 1
    except Exception as exc:
        print(f"  ✗ {exc}")
        failed += 1

    # 7. llm_analyze_legal
    print("\n[7/7] llm_analyze_legal …")
    try:
        analysis = llm_analyze_legal(
            "The trial court denied the motion to disqualify without holding a hearing.",
            "procedural"
        )
        ok = len(analysis) > 20
        print(f"  {'✓' if ok else '✗'} Analysis ({len(analysis)} chars): {analysis[:120]}…")
        passed += 1 if ok else 0
        failed += 0 if ok else 1
    except Exception as exc:
        print(f"  ✗ {exc}")
        failed += 1

    print("\n" + "=" * 60)
    print(f"  Result: {passed} passed, {failed} failed")
    print("=" * 60)
    return failed == 0


# ── CLI ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="LitigationOS LLM Bridge")
    parser.add_argument("--test", action="store_true", help="Run self-test")
    parser.add_argument("--ask", type=str, help="Ask a question")
    parser.add_argument("--extract", type=str, help="Extract legal entities from text")
    args = parser.parse_args()

    if args.test:
        ok = _self_test()
        sys.exit(0 if ok else 1)
    elif args.ask:
        print(llm_ask(args.ask))
    elif args.extract:
        ents = llm_extract_legal_entities(args.extract)
        print(json.dumps(ents, indent=2))
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
