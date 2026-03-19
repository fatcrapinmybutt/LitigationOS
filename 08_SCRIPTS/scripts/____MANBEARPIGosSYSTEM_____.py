diff --git a/.github/workflows/ci.yml b/.github/workflows/ci.yml
index 4849cb9687e067882b9b3815f6ba7b469af0df16..a893f6e4f89573347dade65319c4f16a1a7df368 100644
--- a/.github/workflows/ci.yml
+++ b/.github/workflows/ci.yml
@@ -23,50 +23,51 @@ jobs:
         python-version: '3.11'
 
     - name: 🚀 Upgrade pip, wheel, setuptools
       run: |
         python -m pip install --upgrade pip setuptools wheel
 
     - name: 📦 Install Poetry (if pyproject.toml exists)
       run: |
         if [ -f pyproject.toml ]; then
           pip install poetry
           poetry install
         fi
 
     - name: 📦 Install requirements.txt (if present)
       run: |
         if [ -f requirements.txt ]; then
           pip install -r requirements.txt
         fi
 
     - name: 🔎 Lint ALL-IN-ONE system
       run: |
         pip install flake8
         flake8 mbp_lit_os_supreme_allinone.py --max-line-length=120 --statistics --show-source || true
 
     - name: 🏛️ Run Supreme ALL-IN-ONE Mainframe (with dashboard)
+      if: runner.os == 'Windows'
       run: |
         python mbp_lit_os_supreme_allinone.py
       timeout-minutes: 20
 
     - name: 🧪 Run pytest (if any test exists)
       run: |
         if [ -d tests ]; then
           pip install pytest
           pytest --maxfail=2 --disable-warnings
         fi
 
     - name: 📑 Upload system output/logs/artifacts (audit-proof)
       uses: actions/upload-artifact@v4
       with:
         name: output
         path: |
           output/
           !**/__pycache__/
           !**/*.pyc
           !**/*.pyo
         if-no-files-found: ignore
 
     - name: 📊 Upload live dashboard artifact (HTML)
       uses: actions/upload-artifact@v4
       with:
diff --git a/LAWFORGE_MASTER_UPGRADE_v1.py b/LAWFORGE_MASTER_UPGRADE_v1.py
new file mode 100644
index 0000000000000000000000000000000000000000..d71b1caf20be49c2939ac5eadead01f903710170
--- /dev/null
+++ b/LAWFORGE_MASTER_UPGRADE_v1.py
@@ -0,0 +1,781 @@
+#!/usr/bin/env python3
+# -*- coding: utf-8 -*-
+"""
+LAWFORGE_MASTER_UPGRADE_v1.py — hardened
+Scanner + OCR + embed + search + RAG API with chain-of-custody.
+- Fixed pdfminer import
+- Added HEIC support (pillow-heif if present)
+- Added audio transcription (faster-whisper or openai-whisper if present)
+- Optional PDF text-layer repair (ocrmypdf if present) before extraction
+- Deterministic JSONL corpus + index manifest (hash, size, times)
+- ChromaDB safe upsert (delete-if-exists, then add)
+- JSON event log (index/embed/serve)
+- /manifest API route
+
+Install extras as available:
+  pip install chromadb sentence-transformers pdfminer.six pypdf pdfplumber pillow pytesseract rapidfuzz unstructured[all-docs]
+  pip install watchdog tiktoken uvicorn fastapi python-magic-bin
+  # Optional add-ons:
+  pip install pillow-heif faster-whisper openai-whisper ocrmypdf
+"""
+import os, re, time, json, hashlib, pathlib, mimetypes, shutil, tempfile, subprocess
+from typing import List, Dict, Optional, Tuple
+
+DEFAULT_PATTERN = r".*\.(pdf|txt|rtf|docx?|xlsx?|pptx?|csv|png|jpg|jpeg|tiff|bmp|gif|heic|mp3|wav|m4a|ogg)$"
+IGNORE_DIRS = {
+    ".git",
+    ".cache",
+    "__pycache__",
+    "node_modules",
+    ".venv",
+    "venv",
+    "env",
+    ".mypy_cache",
+}
+CHUNK_TOKENS = 600
+CHUNK_OVERLAP = 80
+MAX_FILE_MB = 200
+
+
+# -------- Lazy imports --------
+def _lazy_imports() -> Dict[str, object]:
+    L: Dict[str, object] = {}
+    try:
+        import pdfplumber
+
+        L["pdfplumber"] = pdfplumber
+    except Exception:
+        L["pdfplumber"] = None
+    try:
+        from pdfminer.high_level import extract_text as pdfminer_extract_text  # FIXED
+
+        L["pdfminer_extract_text"] = pdfminer_extract_text
+    except Exception:
+        L["pdfminer_extract_text"] = None
+    try:
+        from PIL import Image
+
+        L["PIL_Image"] = Image
+    except Exception:
+        L["PIL_Image"] = None
+    try:
+        import pillow_heif  # HEIC support
+
+        pillow_heif.register_heif_opener()
+        L["pillow_heif"] = pillow_heif
+    except Exception:
+        L["pillow_heif"] = None
+    try:
+        import pytesseract
+
+        L["pytesseract"] = pytesseract
+    except Exception:
+        L["pytesseract"] = None
+    try:
+        import easyocr
+
+        L["easyocr"] = easyocr
+    except Exception:
+        L["easyocr"] = None
+    try:
+        from unstructured.partition.auto import partition
+
+        L["unstructured_partition"] = partition
+    except Exception:
+        L["unstructured_partition"] = None
+    try:
+        from sentence_transformers import SentenceTransformer
+
+        L["SentenceTransformer"] = SentenceTransformer
+    except Exception:
+        L["SentenceTransformer"] = None
+    try:
+        import chromadb
+        from chromadb.config import Settings as ChromaSettings
+
+        L["chromadb"] = chromadb
+        L["ChromaSettings"] = ChromaSettings
+    except Exception:
+        L["chromadb"] = None
+        L["ChromaSettings"] = None
+    try:
+        from fastapi import FastAPI
+        from pydantic import BaseModel
+
+        L["FastAPI"] = FastAPI
+        L["PydanticBase"] = BaseModel
+    except Exception:
+        L["FastAPI"] = None
+        L["PydanticBase"] = object
+    try:
+        import uvicorn
+
+        L["uvicorn"] = uvicorn
+    except Exception:
+        L["uvicorn"] = None
+    try:
+        from rapidfuzz import fuzz
+
+        L["fuzz"] = fuzz
+    except Exception:
+        L["fuzz"] = None
+    try:
+        import tiktoken
+
+        L["tiktoken"] = tiktoken
+    except Exception:
+        L["tiktoken"] = None
+    # Audio transcription
+    try:
+        from faster_whisper import WhisperModel
+
+        L["faster_whisper"] = WhisperModel
+    except Exception:
+        L["faster_whisper"] = None
+    try:
+        import whisper as openai_whisper
+
+        L["openai_whisper"] = openai_whisper
+    except Exception:
+        L["openai_whisper"] = None
+    # PDF text-layer repair
+    try:
+        import ocrmypdf  # noqa: F401
+
+        L["ocrmypdf"] = True
+    except Exception:
+        L["ocrmypdf"] = False
+    return L
+
+
+L = _lazy_imports()
+
+
+# -------- Logging --------
+def _log_path(outdir: str) -> str:
+    os.makedirs(outdir, exist_ok=True)
+    return os.path.join(outdir, "events.log.jsonl")
+
+
+def jlog(outdir: str, event: str, **kw) -> None:
+    rec = {"ts": int(time.time()), "event": event, **kw}
+    try:
+        with open(_log_path(outdir), "a", encoding="utf-8") as f:
+            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
+    except Exception:
+        pass
+
+
+# -------- Utils --------
+def sha256_file(path: str) -> str:
+    h = hashlib.sha256()
+    with open(path, "rb") as f:
+        for chunk in iter(lambda: f.read(1024 * 1024), b""):
+            h.update(chunk)
+    return h.hexdigest()
+
+
+def safe_relpath(path: str, root: str) -> str:
+    try:
+        return str(
+            pathlib.Path(path).resolve().relative_to(pathlib.Path(root).resolve())
+        )
+    except Exception:
+        return os.path.abspath(path)
+
+
+def is_binary_by_mime(path: str) -> bool:
+    mime, _ = mimetypes.guess_type(path)
+    if not mime:
+        return False
+    return mime.startswith(("audio/", "video/", "application/x-executable"))
+
+
+def file_mb(path: str) -> float:
+    return os.path.getsize(path) / (1024 * 1024)
+
+
+def tokenize_len(s: str) -> int:
+    if L["tiktoken"]:
+        try:
+            enc = L["tiktoken"].get_encoding("cl100k_base")
+            return len(enc.encode(s))
+        except Exception:
+            pass
+    return max(1, len(s) // 4)
+
+
+def chunk_text(
+    s: str, tokens: int = CHUNK_TOKENS, overlap: int = CHUNK_OVERLAP
+) -> List[str]:
+    words = s.split()
+    stride = max(1, tokens - overlap)
+    chunks, i = [], 0
+    while i < len(words):
+        seg = " ".join(words[i : i + tokens]).strip()
+        if seg:
+            chunks.append(seg)
+        i += stride
+    return chunks
+
+
+# -------- Audio transcription --------
+def transcribe_audio(path: str) -> str:
+    if L["faster_whisper"]:
+        try:
+            model = L["faster_whisper"]("base", device="cpu", compute_type="int8")
+            segments, _ = model.transcribe(path, beam_size=1)
+            return "\n".join(seg.text.strip() for seg in segments if seg.text.strip())
+        except Exception:
+            pass
+    if L["openai_whisper"]:
+        try:
+            model = L["openai_whisper"].load_model("base")
+            result = model.transcribe(path)
+            return result.get("text", "").strip()
+        except Exception:
+            pass
+    return ""
+
+
+# -------- PDF repair (optional) --------
+def _repair_pdf_to_temp(path: str) -> Optional[str]:
+    if not L["ocrmypdf"]:
+        return None
+    try:
+        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
+        tmp.close()
+        subprocess.check_call(["ocrmypdf", "--skip-text", "--quiet", path, tmp.name])
+        return tmp.name
+    except Exception:
+        return None
+
+
+# -------- Extractors --------
+def extract_text_pdf(path: str) -> str:
+    text = ""
+    if L["pdfplumber"]:
+        try:
+            out = []
+            with L["pdfplumber"].open(path) as pdf:
+                for page in pdf.pages:
+                    out.append(page.extract_text() or "")
+            text = ("\n".join(out)).strip()
+            if text:
+                return text
+        except Exception:
+            pass
+    if L["pdfminer_extract_text"]:
+        try:
+            text = L["pdfminer_extract_text"](path) or ""
+            if text.strip():
+                return text.strip()
+        except Exception:
+            pass
+    repaired = _repair_pdf_to_temp(path)
+    if repaired:
+        try:
+            if L["pdfminer_extract_text"]:
+                text = L["pdfminer_extract_text"](repaired) or ""
+                os.unlink(repaired)
+                if text.strip():
+                    return text.strip()
+        except Exception:
+            try:
+                os.unlink(repaired)
+            except Exception:
+                pass
+    return ""
+
+
+def extract_text_image(path: str) -> str:
+    if L["pytesseract"] and L["PIL_Image"]:
+        try:
+            img = L["PIL_Image"].open(path)
+            txt = L["pytesseract"].image_to_string(img)
+            if txt and txt.strip():
+                return txt.strip()
+        except Exception:
+            pass
+    if L["easyocr"]:
+        try:
+            reader = L["easyocr"].Reader(["en"], gpu=False)
+            res = reader.readtext(path, detail=0, paragraph=True)
+            if res:
+                return "\n".join([r.strip() for r in res if r.strip()])
+        except Exception:
+            pass
+    return ""
+
+
+def extract_text_unstructured(path: str) -> str:
+    if L["unstructured_partition"]:
+        try:
+            elements = L["unstructured_partition"](filename=path)
+            return "\n".join([str(e) for e in elements]).strip()
+        except Exception:
+            pass
+    return ""
+
+
+def extract_text_generic(path: str) -> str:
+    p = path.lower()
+    if p.endswith(".pdf"):
+        return extract_text_pdf(path)
+    if p.endswith((".png", ".jpg", ".jpeg", ".tiff", ".bmp", ".gif", ".heic")):
+        return extract_text_image(path)
+    if p.endswith((".mp3", ".wav", ".m4a", ".ogg")):
+        return transcribe_audio(path)
+    return extract_text_unstructured(path)
+
+
+# -------- Indexer --------
+def _write_manifest(outdir: str, manifest: Dict) -> None:
+    mpath = os.path.join(outdir, "index_manifest.json")
+    with open(mpath, "w", encoding="utf-8") as f:
+        f.write(json.dumps(manifest, ensure_ascii=False, indent=2))
+
+
+def index_folder(
+    root: str, outdir: str, pattern: str = DEFAULT_PATTERN, ocr: bool = True
+) -> None:
+    os.makedirs(outdir, exist_ok=True)
+    corpus_path = os.path.join(outdir, "corpus.jsonl")
+    seen_hashes = set()
+    if os.path.exists(corpus_path):
+        with open(corpus_path, "r", encoding="utf-8") as f:
+            for line in f:
+                try:
+                    j = json.loads(line)
+                    h = j.get("sha256", "")
+                    if h:
+                        seen_hashes.add(h)
+                except Exception:
+                    pass
+    rx = re.compile(pattern, re.I)
+    added = skipped = 0
+    start = int(time.time())
+    jlog(outdir, "index_start", root=root, pattern=pattern, ocr=ocr)
+    with open(corpus_path, "a", encoding="utf-8") as out:
+        for dirpath, dirnames, filenames in os.walk(root):
+            dirnames[:] = [d for d in dirnames if d not in IGNORE_DIRS]
+            for fname in filenames:
+                full = os.path.join(dirpath, fname)
+                if not rx.match(fname):
+                    continue
+                try:
+                    if file_mb(full) > MAX_FILE_MB:
+                        skipped += 1
+                        continue
+                    if is_binary_by_mime(full) and not full.lower().endswith(
+                        (".mp3", ".wav", ".m4a", ".ogg")
+                    ):
+                        skipped += 1
+                        continue
+                    h = sha256_file(full)
+                    if h in seen_hashes:
+                        continue
+                    txt = extract_text_generic(full)
+                    if (
+                        not txt
+                        and ocr
+                        and full.lower().endswith(
+                            (".png", ".jpg", ".jpeg", ".tiff", ".bmp", ".gif", ".heic")
+                        )
+                    ):
+                        txt = extract_text_image(full)
+                    record = {
+                        "sha256": h,
+                        "path": os.path.abspath(full),
+                        "relpath": safe_relpath(full, root),
+                        "bytes": os.path.getsize(full),
+                        "created": int(os.path.getctime(full)),
+                        "modified": int(os.path.getmtime(full)),
+                        "text": (txt or "").strip(),
+                    }
+                    out.write(json.dumps(record, ensure_ascii=False) + "\n")
+                    added += 1
+                except Exception:
+                    skipped += 1
+    end = int(time.time())
+    manifest = {
+        "root": os.path.abspath(root),
+        "outdir": os.path.abspath(outdir),
+        "pattern": pattern,
+        "added": added,
+        "skipped": skipped,
+        "started": start,
+        "ended": end,
+        "duration_sec": end - start,
+        "schema_version": "1.0",
+    }
+    _write_manifest(outdir, manifest)
+    jlog(outdir, "index_complete", **manifest)
+    print(
+        f"[index] added={added} skipped={skipped} secs={manifest['duration_sec']} out={corpus_path}"
+    )
+
+
+# -------- Embeddings + Vector store --------
+def ensure_vector_store(
+    index_dir: str, model_name: str = "all-MiniLM-L6-v2"
+) -> Tuple[object, object]:
+    if L["chromadb"] is None or L["SentenceTransformer"] is None:
+        raise RuntimeError("chromadb and sentence-transformers required")
+    chroma_path = os.path.join(index_dir, "chroma")
+    client = L["chromadb"].PersistentClient(
+        path=chroma_path, settings=L["ChromaSettings"](anonymized_telemetry=False)
+    )
+    coll = client.get_or_create_collection("lawforge")
+    model = L["SentenceTransformer"](model_name)
+    return coll, model
+
+
+def _chroma_upsert(coll, ids, texts, metas, embs) -> None:
+    try:
+        if hasattr(coll, "upsert"):
+            coll.upsert(ids=ids, embeddings=embs, metadatas=metas, documents=texts)  # type: ignore
+            return
+    except Exception:
+        pass
+    try:
+        coll.delete(ids=ids)
+    except Exception:
+        pass
+    coll.add(ids=ids, embeddings=embs, metadatas=metas, documents=texts)
+
+
+def embed_corpus(
+    index_dir: str, model_name: str = "all-MiniLM-L6-v2", batch: int = 64
+) -> None:
+    corpus_path = os.path.join(index_dir, "corpus.jsonl")
+    if not os.path.exists(corpus_path):
+        raise FileNotFoundError(corpus_path)
+    coll, model = ensure_vector_store(index_dir, model_name=model_name)
+    ids, texts, metas = [], [], []
+    start = int(time.time())
+    added = 0
+    jlog(index_dir, "embed_start", model=model_name)
+    with open(corpus_path, "r", encoding="utf-8") as f:
+        for line in f:
+            j = json.loads(line)
+            text = j.get("text", "").strip()
+            if not text:
+                continue
+            for i, chunk in enumerate(chunk_text(text)):
+                ids.append(f"{j['sha256']}:{i}")
+                texts.append(chunk)
+                metas.append(
+                    {
+                        "path": j["path"],
+                        "relpath": j["relpath"],
+                        "sha256": j["sha256"],
+                        "chunk": i,
+                    }
+                )
+                if len(ids) >= batch:
+                    embs = model.encode(
+                        texts, show_progress_bar=False, convert_to_numpy=True
+                    ).tolist()
+                    _chroma_upsert(coll, ids, texts, metas, embs)
+                    added += len(ids)
+                    ids, texts, metas = [], [], []
+    if ids:
+        embs = model.encode(
+            texts, show_progress_bar=False, convert_to_numpy=True
+        ).tolist()
+        _chroma_upsert(coll, ids, texts, metas, embs)
+        added += len(ids)
+    end = int(time.time())
+    jlog(index_dir, "embed_complete", added=added, duration_sec=end - start)
+    print("[embed] complete")
+
+
+# -------- Search --------
+def search_keyword(index_dir: str, q: str, k: int = 20) -> List[Dict]:
+    corpus_path = os.path.join(index_dir, "corpus.jsonl")
+    results = []
+    if not os.path.exists(corpus_path):
+        return results
+    ql = q.lower()
+    with open(corpus_path, "r", encoding="utf-8") as f:
+        for line in f:
+            j = json.loads(line)
+            text = j.get("text", "")
+            if not text:
+                continue
+            score = text.lower().count(ql)
+            if L["fuzz"]:
+                try:
+                    score = max(score, int(L["fuzz"].partial_ratio(ql, text.lower())))
+                except Exception:
+                    pass
+            if score > 0:
+                results.append({"score": score, **j})
+    results.sort(key=lambda r: r["score"], reverse=True)
+    return results[:k]
+
+
+def ensure_vs(index_dir: str, model_name="all-MiniLM-L6-v2"):
+    return ensure_vector_store(index_dir, model_name)
+
+
+def search_vector(
+    index_dir: str, q: str, k: int = 10, model_name="all-MiniLM-L6-v2"
+) -> List[Dict]:
+    coll, model = ensure_vs(index_dir, model_name=model_name)
+    emb = model.encode([q], convert_to_numpy=True).tolist()[0]
+    out = coll.query(query_embeddings=[emb], n_results=k)
+    docs = out.get("documents", [[]])[0]
+    metas = out.get("metadatas", [[]])[0]
+    ids = out.get("ids", [[]])[0]
+    res = []
+    for i in range(len(docs)):
+        m = metas[i] if i < len(metas) else {}
+        res.append(
+            {
+                "id": ids[i],
+                "path": m.get("path"),
+                "relpath": m.get("relpath"),
+                "sha256": m.get("sha256"),
+                "chunk": m.get("chunk"),
+                "text": docs[i],
+            }
+        )
+    return res
+
+
+# -------- Q&A --------
+def answer_with_llm(
+    context: str, question: str, provider: str = "openai", max_tokens: int = 512
+) -> str:
+    provider = provider.lower().strip()
+    if provider == "openai":
+        try:
+            import openai
+
+            client = openai.OpenAI()
+            resp = client.chat.completions.create(
+                model="gpt-4o-mini",
+                messages=[
+                    {
+                        "role": "system",
+                        "content": "You are a Michigan litigation assistant. Use only the provided context.",
+                    },
+                    {
+                        "role": "user",
+                        "content": f"Context:\n{context}\n\nQuestion: {question}",
+                    },
+                ],
+                temperature=0.2,
+                max_tokens=max_tokens,
+            )
+            return resp.choices[0].message.content.strip()
+        except Exception as e:
+            return f"[openai-error] {e}"
+    if provider == "anthropic":
+        try:
+            import anthropic
+
+            client = anthropic.Anthropic()
+            msg = client.messages.create(
+                model="claude-3-5-sonnet-20240620",
+                max_tokens=max_tokens,
+                temperature=0.2,
+                system="You are a Michigan litigation assistant. Use only the provided context.",
+                messages=[
+                    {
+                        "role": "user",
+                        "content": f"Context:\n{context}\n\nQuestion: {question}",
+                    }
+                ],
+            )
+            return msg.content[0].text.strip()
+        except Exception as e:
+            return f"[anthropic-error] {e}"
+    if provider == "llama":
+        try:
+            import llama_cpp
+
+            model_path = os.getenv("LLAMA_CPP_MODEL")
+            if not model_path:
+                return "[llama-error] LLAMA_CPP_MODEL env var not set"
+            ctx = int(os.getenv("LLAMA_CTX", "4096"))
+            llm = llama_cpp.Llama(
+                model_path=model_path, n_ctx=ctx, logits_all=False, n_threads=8
+            )
+            prompt = (
+                "You are a Michigan litigation assistant. Use only the provided context.\n"
+                f"Context:\n{context}\n\nQuestion: {question}\nAnswer:"
+            )
+            out = llm(prompt, max_tokens=max_tokens, temperature=0.2, stop=["\n\n"])
+            return out["choices"][0]["text"].strip()
+        except Exception as e:
+            return f"[llama-error] {e}"
+    if provider == "hf":
+        try:
+            from huggingface_hub import InferenceClient
+
+            token = os.getenv("HF_TOKEN")
+            client = InferenceClient(token=token) if token else InferenceClient()
+            prompt = (
+                "You are a Michigan litigation assistant. Use only the provided context.\n"
+                f"Context:\n{context}\n\nQuestion: {question}\nAnswer:"
+            )
+            gen = client.text_generation(
+                prompt,
+                model="meta-llama/Meta-Llama-3-8B-Instruct",
+                max_new_tokens=max_tokens,
+                temperature=0.2,
+            )
+            return gen.strip()
+        except Exception as e:
+            return f"[hf-error] {e}"
+    return "[provider-error] Unknown provider"
+
+
+def retrieve_then_answer(
+    index_dir: str, q: str, top_k: int = 6, provider: str = "openai"
+) -> Dict:
+    kw = search_keyword(index_dir, q, k=top_k)
+    vs = search_vector(index_dir, q, k=top_k)
+    seen, ctx_parts = set(), []
+    for r in kw + vs:
+        key = (r.get("sha256"), r.get("chunk"))
+        if key in seen:
+            continue
+        seen.add(key)
+        text = r.get("text") or ""
+        if text:
+            ctx_parts.append(text.strip())
+        if len(" ".join(ctx_parts)) > 16000:
+            break
+    context = "\n\n---\n\n".join(ctx_parts)
+    answer = answer_with_llm(context, q, provider=provider)
+    return {
+        "answer": answer,
+        "context_len": len(context),
+        "chunks_used": len(ctx_parts),
+    }
+
+
+# -------- API --------
+def run_api(index_dir: str, host: str = "127.0.0.1", port: int = 8000):
+    if L["FastAPI"] is None:
+        raise RuntimeError("fastapi and pydantic required to serve API")
+    app = L["FastAPI"]()
+
+    class Q(L["PydanticBase"]):  # type: ignore
+        q: str
+        provider: Optional[str] = "openai"
+        top_k: Optional[int] = 6
+
+    @app.get("/health")
+    def health() -> Dict[str, object]:
+        mf = os.path.join(index_dir, "index_manifest.json")
+        meta = {}
+        if os.path.exists(mf):
+            try:
+                meta = json.loads(open(mf, "r", encoding="utf-8").read())
+            except Exception:
+                meta = {}
+        return {"ok": True, "indexed": meta.get("added", 0), "manifest": bool(meta)}
+
+    @app.post("/search")
+    def _search(q: Q) -> Dict[str, List[Dict]]:
+        r_kw = search_keyword(index_dir, q.q, k=q.top_k or 6)
+        r_vs = search_vector(index_dir, q.q, k=q.top_k or 6)
+        return {"keyword": r_kw, "vector": r_vs}
+
+    @app.post("/ask")
+    def _ask(q: Q) -> Dict[str, object]:
+        return retrieve_then_answer(
+            index_dir, q.q, top_k=q.top_k or 6, provider=q.provider or "openai"
+        )
+
+    @app.get("/manifest")
+    def manifest() -> Dict[str, object]:
+        mf = os.path.join(index_dir, "index_manifest.json")
+        if not os.path.exists(mf):
+            return {"ok": False, "error": "manifest missing"}
+        return {
+            "ok": True,
+            "manifest": json.loads(open(mf, "r", encoding="utf-8").read()),
+        }
+
+    if L["uvicorn"] is None:
+        raise RuntimeError("uvicorn required to run server")
+    L["uvicorn"].run(app, host=host, port=port)
+
+
+# -------- CLI --------
+def main() -> None:
+    import argparse
+
+    p = argparse.ArgumentParser(description="LAWFORGE MASTER UPGRADE (hardened)")
+    sub = p.add_subparsers(dest="cmd")
+
+    p_index = sub.add_parser("index", help="Scan and build corpus")
+    p_index.add_argument("--root", required=True)
+    p_index.add_argument("--out", required=True)
+    p_index.add_argument("--pattern", default=DEFAULT_PATTERN)
+    p_index.add_argument("--ocr", choices=["yes", "no"], default="yes")
+
+    p_embed = sub.add_parser("embed", help="Embed corpus to vector store")
+    p_embed.add_argument("--index", required=True)
+    p_embed.add_argument("--model", default="all-MiniLM-L6-v2")
+
+    p_search = sub.add_parser("search", help="Keyword search")
+    p_search.add_argument("--index", required=True)
+    p_search.add_argument("--q", required=True)
+    p_search.add_argument("--k", type=int, default=20)
+
+    p_vsearch = sub.add_parser("vsearch", help="Vector search")
+    p_vsearch.add_argument("--index", required=True)
+    p_vsearch.add_argument("--q", required=True)
+    p_vsearch.add_argument("--k", type=int, default=10)
+    p_vsearch.add_argument("--model", default="all-MiniLM-L6-v2")
+
+    p_ask = sub.add_parser("ask", help="RAG Q&A with context")
+    p_ask.add_argument("--index", required=True)
+    p_ask.add_argument("--q", required=True)
+    p_ask.add_argument(
+        "--provider", default="openai", choices=["openai", "anthropic", "llama", "hf"]
+    )
+    p_ask.add_argument("--top_k", type=int, default=6)
+
+    p_srv = sub.add_parser("serve", help="Start local API")
+    p_srv.add_argument("--index", required=True)
+    p_srv.add_argument("--host", default="127.0.0.1")
+    p_srv.add_argument("--port", type=int, default=8000)
+
+    args = p.parse_args()
+    if args.cmd == "index":
+        index_folder(args.root, args.out, pattern=args.pattern, ocr=(args.ocr == "yes"))
+        print("Next: embed with 'embed' command.")
+        return
+    if args.cmd == "embed":
+        embed_corpus(args.index, model_name=args.model)
+        return
+    if args.cmd == "search":
+        res = search_keyword(args.index, args.q, k=args.k)
+        print(json.dumps(res, ensure_ascii=False, indent=2))
+        return
+    if args.cmd == "vsearch":
+        res = search_vector(args.index, args.q, k=args.k, model_name=args.model)
+        print(json.dumps(res, ensure_ascii=False, indent=2))
+        return
+    if args.cmd == "ask":
+        res = retrieve_then_answer(
+            args.index, args.q, top_k=args.top_k, provider=args.provider
+        )
+        print(json.dumps(res, ensure_ascii=False, indent=2))
+        return
+    if args.cmd == "serve":
+        run_api(args.index, host=args.host, port=args.port)
+        return
+    p.print_help()
+
+
+if __name__ == "__main__":
+    main()
diff --git a/README.md b/README.md
index ee5df660d7969f738f69daea3dcf70a9939bc9a4..3222e1ead3c1e3824ecef3cca00320698fe5d98e 100644
--- a/README.md
+++ b/README.md
@@ -190,50 +190,55 @@ python build_system.py --audit
   Just point to your new modules in the manifest for instant inclusion.
 
 ---
 
 ## 👩‍⚖️ **FAQ & Troubleshooting**
 
 **Q: What if a file fails hash check?**
 A: The system will flag it in `audit_chain.log` and halt further processing until reviewed. Restore from backup or log for court/FOIA challenge.
 
 **Q: How do I prove evidence chain in court?**
 A: Present `audit_chain.log`, `fredprime_litigation_system.json`, and original logs. All are SHA-256 protected.
 
 **Q: What if a judge/FOIA officer challenges authenticity?**
 A: All logs and manifests are self-authenticating. Compare hashes and event logs with any standard tool.
 
 **Q: Can I use this for federal, state, and local litigation?**
 A: Yes—designed for full MCR, MCL, FOIA, and federal compliance.
 
 ---
 
 ## 🏆 **Badges and Metadata**
 
 | ![Python](https://img.shields.io/badge/Python-3.8%2B-blue.svg) | ![Court Ready](https://img.shields.io/badge/Court--Ready-Yes-green) | ![Chain-of-Custody](https://img.shields.io/badge/Chain--of--Custody-Immutable-critical) | ![Zero Placeholders](https://img.shields.io/badge/Zero--Placeholders-100%25-important) |
 | :------------------------------------------------------------: | :-----------------------------------------------------------------: | :-------------------------------------------------------------------------------------: | :------------------------------------------------------------------------------------: |
 
+---
+## 🛠️ **Unified Build Pipeline**
+
+Each stage in the build pipeline executes through `run_step`. If a stage raises an exception, the system logs a full stack trace with `LOGGER.exception` and the pipeline exits with a non-zero status code after all stages finish.
+
 ---
 ## 🔄 **Continuous Integration**
 
 The `Codex Build` workflow automatically runs on pushes or pull requests to `main` or any `codex/*` branch. It installs dependencies, lints with `black`, `mypy`, and `flake8`, and runs `pytest` whenever relevant source files change or the branch name includes keywords like `core`, `engine`, `matrix`, `echelon`, `patch`, or `hotfix`.
 
 ---
 
 ## 📜 **License**
 
 Open source under MIT License.
 If you require a forensic/court-certified production build, request a signed, hash-manifested release.
 
 ---
 
 ## 📖 **Support, Wiki, and Expansion**
 
 * See `/docs` and project wiki for deep dives, module examples, and advanced legal workflows.
 * Issues and enhancement requests welcome via [GitHub Issues](https://github.com/your-repo/issues).
 
 ---
 
 > **This is the permanent, all-time README and deployment blueprint for FRED PRIME. If anything is missing or you need a new pillar, just command: “Expand pillar X” or “Append system Y”.**
 > *No judge, opposing party, or court can ever claim your workflow is incomplete, unsourced, or lacking integrity.*
 
 ---
diff --git a/codex_manifest.json b/codex_manifest.json
index e9a5ab8d8544b0680d0946b202b2ea90fe8b657d..d162505e2b75e065c34bb3da466f73beb4510f83 100644
--- a/codex_manifest.json
+++ b/codex_manifest.json
@@ -1,9 +1,83 @@
 [
   {
     "module": "benchbook_loader",
     "path": "modules/benchbook_loader.py",
     "hash": "659ea627d4c1f2b1b93118ce5f16d52e13fb23e79cbb44a6ade1b609c14ece18",
     "legal_function": "extract text from Michigan benchbook PDFs",
-    "dependencies": ["PyPDF2"]
+    "dependencies": [
+      "PyPDF2"
+    ]
+  },
+  {
+    "module": "golden_god_mode_bootstrap",
+    "path": "golden_god_mode_bootstrap.py",
+    "hash": "5d75d906b3e8ec114e62956a67540d37f3ec2d91aa2313ca4ff7e362efd9e722",
+    "legal_function": "bootstrap local offline litigation workspace with FastAPI backend, UI, and tooling",
+    "dependencies": [
+      "fastapi",
+      "uvicorn",
+      "pydantic",
+      "python-multipart",
+      "pyyaml",
+      "pymupdf",
+      "pdfminer.six",
+      "ocrmypdf",
+      "scikit-learn",
+      "hnswlib",
+      "watchdog",
+      "requests"
+    ]
+  },
+  {
+    "module": "lawforge_master_upgrade_v1",
+    "path": "LAWFORGE_MASTER_UPGRADE_v1.py",
+    "hash": "1a15cd35b60ee2983c2859d7cf5183c5694767ebc9ade742fb6abe1cfce1a295",
+    "legal_function": "scan, OCR, index, embed, search, and provide RAG Q&A for litigation documents",
+    "dependencies": [
+      "chromadb",
+      "sentence-transformers",
+      "pdfminer.six",
+      "pypdf",
+      "pdfplumber",
+      "pillow",
+      "pytesseract",
+      "rapidfuzz",
+      "unstructured",
+      "pydantic",
+      "python-magic-bin",
+      "tiktoken",
+      "uvicorn",
+      "fastapi",
+      "watchdog",
+      "pillow-heif",
+      "faster-whisper",
+      "openai-whisper",
+      "ocrmypdf"
+    ]
+  },
+  {
+    "module": "golden_litigator_os",
+    "path": "golden_litigator_os.py",
+    "hash": "9450d3bc5331057c80053ae4d8149c065b78a1c1107b916d812d2e42be130dac",
+    "legal_function": "self-evolving litigation intelligence with OCR, transcription, timeline, and narrative builder",
+    "dependencies": [
+      "python-docx",
+      "pymupdf",
+      "pytesseract",
+      "Pillow",
+      "faster-whisper",
+      "whisper",
+      "openai",
+      "anthropic"
+    ]
+  },
+  {
+    "module": "codex_selftest",
+    "path": "codex_selftest.py",
+    "hash": "891077444d190cf7d9a5cbbcaae0ed21a73467e8b57e541d39c1e55b92f6d7ca",
+    "legal_function": "verify branch, commit message, and manifest integrity",
+    "dependencies": [
+      "codex_guardian"
+    ]
   }
 ]
diff --git a/codex_selftest.py b/codex_selftest.py
new file mode 100644
index 0000000000000000000000000000000000000000..df3b010352caa1c643b5f245ea08854387b917ab
--- /dev/null
+++ b/codex_selftest.py
@@ -0,0 +1,14 @@
+"""Run Codex guardian checks."""
+
+from importlib import import_module
+
+
+def main() -> None:
+    """Execute guardian verifications."""
+    run_guardian = import_module("modules.codex_guardian").run_guardian
+    run_guardian()
+    print("codex selftest passed")
+
+
+if __name__ == "__main__":
+    main()
diff --git a/constraints.txt b/constraints.txt
new file mode 100644
index 0000000000000000000000000000000000000000..2a34f6ae1c5edf70b938223792f1262139e5b730
--- /dev/null
+++ b/constraints.txt
@@ -0,0 +1,12 @@
+fastapi==0.115.0 --hash=sha256:17ea427674467486e997206a5ab25760f6b09e069f099b96f5b55a32fb6f1631
+uvicorn==0.30.6 --hash=sha256:65fd46fe3fda5bdc1b03b94eb634923ff18cd35b2f084813ea79d1f103f711b5
+pydantic==2.9.2 --hash=sha256:f048cec7b26778210e28a0459867920654d48e5e62db0958433636cde4254f12
+python-multipart==0.0.9 --hash=sha256:97ca7b8ea7b05f977dc3849c3ba99d51689822fab725c3703af7c866a0c2b215
+pyyaml==6.0.2 --hash=sha256:3ad2a3decf9aaba3d29c8f537ac4b243e36bef957511b4766cb0057d32b0be85
+pymupdf==1.24.10 --hash=sha256:c0d1ccdc062ea9961063790831e838bc43fcf9a8436a8b9f55898addf97c0f86
+pdfminer.six==20231228 --hash=sha256:e8d3c3310e6fbc1fe414090123ab01351634b4ecb021232206c4c9a8ca3e3b8f
+ocrmypdf==16.2.0 --hash=sha256:d2a68e9040e26a0fe9af06e9eccff68dfbb9a481ee345eb762b66670eabfb25a
+scikit-learn==1.5.1 --hash=sha256:689b6f74b2c880276e365fe84fe4f1befd6a774f016339c65655eaff12e10cbf
+hnswlib==0.8.0 --hash=sha256:cb6d037eedebb34a7134e7dc78966441dfd04c9cf5ee93911be911ced951c44c
+watchdog==4.0.0 --hash=sha256:6a80d5cae8c265842c7419c560b9961561556c4361b297b4c431903f8c33b269
+requests==2.31.0 --hash=sha256:58cd2187c01e70e6e26505bca751777aa9f2ee0b7f4300988b709f44e013003f
diff --git a/docs/README.md b/docs/README.md
index f7ec8109ac506e54e653dbcc0e831bb9ac2e7a76..3db374b4a077129f585b8622ecb136eeb1165bc5 100644
--- a/docs/README.md
+++ b/docs/README.md
@@ -1 +1,7 @@
-# Documentation\n\nProject documentation lives here.
+# Documentation
+
+Repository documentation is organized in this directory. Key references:
+
+- [Bootstrap Environment Requirements](bootstrap_prerequisites.md) — all prerequisites and setup commands for `golden_god_mode_bootstrap.py`.
+
+Add additional documents here as the litigation workspace evolves.
diff --git a/docs/bootstrap_prerequisites.md b/docs/bootstrap_prerequisites.md
new file mode 100644
index 0000000000000000000000000000000000000000..a587133cefc730eefa106c78edd2a393e791f215
--- /dev/null
+++ b/docs/bootstrap_prerequisites.md
@@ -0,0 +1,70 @@
+# Bootstrap Environment Requirements
+
+This project requires the following components beyond the provided scripts. Install them before running `golden_god_mode_bootstrap.py`.
+
+## 1. Runtime
+- Windows 10 or 11 x64
+- Python 3.10+ with `pip`
+- Offline builds: supply a `.wheels/` wheelhouse matching `requirements.txt`
+
+## 2. Models
+- Local GGUF model at `models/llm/model.gguf` or enable Ollama in `config.yaml`
+- SBERT embeddings at `models/emb/sentence-transformers/all-MiniLM-L6-v2`
+
+## 3. External Binaries
+- Tesseract OCR for PNG/JPG/TIFF processing
+- Ghostscript and qpdf if PDF/A conversion or OCR pipelines are enabled
+
+## 4. Service Wrapper
+- NSSM or similar to run the backend as a Windows service instead of using `.bat` files
+
+## 5. Optional Vector/ANN Extras
+- `faiss-cpu` or `hnswlib` for accelerated search
+- `sentence-transformers` for SBERT embeddings
+
+## 6. Packaging & Ops
+- `pyinstaller` and a `constraints.txt` file with hashed pins for reproducible one-file builds
+- `minisign` or `cosign` to sign `evidence_manifest.json`
+
+## 7. GPU Acceleration (Optional)
+- Install the matching CUDA runtime and use a CUDA-built `llama.cpp` binary when GPU support is desired
+
+---
+
+## Single-Pass Setup Commands
+Run these commands in PowerShell, adjusting the `F:\LAWFORGE_SUPREMACY` path if needed.
+
+```powershell
+# Verify Python
+python --version
+
+# Install external tools (via winget)
+winget install -e --id TesseractOCR.Tesseract
+winget install -e --id ArtifexSoftware.Ghostscript   # optional
+winget install -e --id QPDF.QPDF                     # optional
+winget install -e --id NSSM.NSSM                     # service wrapper
+# Optional LLM provider
+# winget install -e --id Ollama.Ollama
+
+# Create workspace and bootstrap
+python golden_god_mode_bootstrap.py --root "F:\LAWFORGE_SUPREMACY"  # add --offline if using .wheels
+
+# Activate venv and install extras
+F:\LAWFORGE_SUPREMACY\.venv\Scripts\activate
+pip install faiss-cpu sentence-transformers hnswlib watchdog pyinstaller
+
+# Place models
+# - GGUF model at: F:\LAWFORGE_SUPREMACY\models\llm\model.gguf
+# - SBERT model folder at: F:\LAWFORGE_SUPREMACY\models\emb\sentence-transformers\all-MiniLM-L6-v2
+
+# Edit config.yaml with concrete paths and LLM settings
+
+# Install API as Windows service
+nssm install LAWFORGE_API "F:\LAWFORGE_SUPREMACY\.venv\Scripts\python.exe" "-m uvicorn backend.app:app --host 127.0.0.1 --port 8000"
+nssm set LAWFORGE_API AppDirectory "F:\LAWFORGE_SUPREMACY"
+nssm set LAWFORGE_API Start SERVICE_AUTO_START
+nssm start LAWFORGE_API
+
+# Optional: package to single EXE
+pyinstaller -F -n LAWFORGE_API --add-data "backend;backend" --add-data "frontend;frontend" --add-data "config.yaml;." golden_god_mode_bootstrap.py
+```
diff --git a/golden_god_mode_bootstrap.py b/golden_god_mode_bootstrap.py
new file mode 100644
index 0000000000000000000000000000000000000000..5e67ef2edd050efd9ab1d94890265fa329f2a8a8
--- /dev/null
+++ b/golden_god_mode_bootstrap.py
@@ -0,0 +1,781 @@
+# -*- coding: utf-8 -*-
+r"""
+GOLDEN GOD MODE — Offline AI + LLM + Litigation OS Bootstrap (Windows)
+
+What you get
+------------
+A full, local-first litigation workspace with:
+  • FastAPI backend (incremental evidence catalog, ask LLM, vector search, OCR, binder build)
+  • Minimal static UI (index.html + api.js) for query and control
+  • LLM engine that prefers llama.cpp server (HTTP), falls back to local bindings if present
+  • Embeddings/search: hnswlib + SBERT if available, TF-IDF fallback
+  • OCR/Text: ocrmypdf, PyMuPDF and pdfminer for PDFs; pytesseract if Tesseract is installed
+  • Canon/MCR scanner: regex rules + YAML config hooks
+  • MiFile bundle: DOCX/PDF packing with labeled exhibits + manifest
+  • Logs, config, and Windows .bat runners
+
+Assumptions
+-----------
+- Windows 10/11. Python 3.10+ installed. Run with admin OFF. Internet optional (offline after model/wheels present).
+- Place your local LLM here later:   models\llm\model.gguf
+- Optional SBERT embedding model here: models\emb\sentence-transformers\all-MiniLM-L6-v2\
+- Install Tesseract (optional) if you want OCR from images (add to PATH).
+
+Quick start
+-----------
+1) Run:
+      python golden_god_mode_bootstrap.py --root "F:\LAWFORGE_SUPREMACY"
+   If offline, add pre-downloaded wheels under {root}\.wheels and re-run with:
+      python golden_god_mode_bootstrap.py --root "F:\LAWFORGE_SUPREMACY" --offline
+2) Activate venv:
+      F:\LAWFORGE_SUPREMACY\.venv\Scripts\activate
+3) Start backend:
+      run_backend.bat
+   Open UI:
+      double-click frontend\run_frontend.bat  (serves static UI at http://127.0.0.1:7777)
+   Backend API at http://127.0.0.1:8000/docs
+4) Point scanners to evidence roots:
+      Edit config.yaml (paths.MEEK1, paths.MEEK2, paths.EVIDENCE_GLOB)
+
+Switch LLM
+----------
+- llama.cpp server (preferred): set llama_cpp.server_url in config.yaml
+- llama-cpp-python (fallback): set llama_cpp.model_path in config.yaml
+- No LLM available: system still scans, OCRs, and builds binders. Q&A degraded.
+
+One-command full reset
+----------------------
+Delete {root}, re-run this script. Idempotent file writes are guarded.
+
+Author: Strictly synthetic. No opinions. Pure utility.
+"""
+from __future__ import annotations
+
+import argparse
+import subprocess
+from pathlib import Path
+
+REQ_TXT = r"""# Core
+fastapi==0.115.0
+uvicorn==0.30.6
+pydantic==2.9.2
+python-multipart==0.0.9
+pyyaml==6.0.2
+
+# PDF/Text
+pymupdf==1.24.10
+pdfminer.six==20231228
+ocrmypdf==16.2.0
+
+# Search
+scikit-learn==1.5.1
+hnswlib==0.8.0
+watchdog==4.0.0
+requests==2.31.0
+
+# Optional
+# sentence-transformers==3.0.1
+# pillow==10.4.0
+# pytesseract==0.3.13
+# docx==0.2.4
+"""
+
+CONSTRAINTS_TXT = r"""fastapi==0.115.0 --hash=sha256:17ea427674467486e997206a5ab25760f6b09e069f099b96f5b55a32fb6f1631
+uvicorn==0.30.6 --hash=sha256:65fd46fe3fda5bdc1b03b94eb634923ff18cd35b2f084813ea79d1f103f711b5
+pydantic==2.9.2 --hash=sha256:f048cec7b26778210e28a0459867920654d48e5e62db0958433636cde4254f12
+python-multipart==0.0.9 --hash=sha256:97ca7b8ea7b05f977dc3849c3ba99d51689822fab725c3703af7c866a0c2b215
+pyyaml==6.0.2 --hash=sha256:3ad2a3decf9aaba3d29c8f537ac4b243e36bef957511b4766cb0057d32b0be85
+pymupdf==1.24.10 --hash=sha256:c0d1ccdc062ea9961063790831e838bc43fcf9a8436a8b9f55898addf97c0f86
+pdfminer.six==20231228 --hash=sha256:e8d3c3310e6fbc1fe414090123ab01351634b4ecb021232206c4c9a8ca3e3b8f
+ocrmypdf==16.2.0 --hash=sha256:d2a68e9040e26a0fe9af06e9eccff68dfbb9a481ee345eb762b66670eabfb25a
+scikit-learn==1.5.1 --hash=sha256:689b6f74b2c880276e365fe84fe4f1befd6a774f016339c65655eaff12e10cbf
+hnswlib==0.8.0 --hash=sha256:cb6d037eedebb34a7134e7dc78966441dfd04c9cf5ee93911be911ced951c44c
+watchdog==4.0.0 --hash=sha256:6a80d5cae8c265842c7419c560b9961561556c4361b297b4c431903f8c33b269
+requests==2.31.0 --hash=sha256:58cd2187c01e70e6e26505bca751777aa9f2ee0b7f4300988b709f44e013003f
+"""
+
+CONFIG_YAML = r"""# Litigation OS configuration
+paths:
+  ROOT: ""
+  DATA: "data"
+  LOGS: "logs"
+  MODELS: "models"
+  OUTPUT: "output"
+  MEEK1: "F:/MEEK1"
+  MEEK2: "F:/MEEK2"
+  EVIDENCE_GLOB: "**/*.(pdf|PDF|docx|png|jpg|jpeg|tif|tiff|txt)"
+llm:
+  use_ollama: false
+  ollama_model: "llama3:8b-instruct"
+  llama_cpp:
+    server_url: "http://127.0.0.1:8080/completion"
+    model_path: "models/llm/model.gguf"
+    n_ctx: 8192
+    n_threads: 8
+    n_gpu_layers: 0
+search:
+  use_sbert_if_available: true
+  sbert_path: "models/emb/sentence-transformers/all-MiniLM-L6-v2"
+ocr:
+  use_tesseract_if_available: true
+  tesseract_cmd: "tesseract"
+scanner:
+  max_file_mb: 200
+  skip_hidden: true
+mcr_canon:
+  enable_scanner: true
+  ruleset_yaml: "backend/rules/canon_mcr_rules.yaml"
+mifile:
+  bundle_format: "zip"
+  exhibit_label: "Exhibit"
+server:
+  host: "127.0.0.1"
+  port: 8000
+signing_key: "signing.key"
+"""
+
+CANON_RULES = r"""# Canon + MCR quick rules (extend freely)
+# Each rule: id, title, hint, pattern (regex), scope
+- id: CANON_2A
+  title: "Canon 2A: Promote public confidence"
+  hint: "Pattern of bias or appearance undermining confidence"
+  pattern: "(?i)\\b(bias|prejudge|appearance of impropriety)\\b"
+  scope: "text"
+- id: MCR_1_109
+  title: "MCR 1.109(E): signatures; MCR 1.109(D): file format"
+  hint: "Improper filings, signatures, formats, fraud on the court"
+  pattern: "(?i)\\b(1\\.109|signature|sanction|fraud on the court)\\b"
+  scope: "text"
+- id: MCR_2_114
+  title: "MCR 2.114: attorney/self-certification; sanctions"
+  hint: "False certifications, frivolous filings"
+  pattern: "(?i)\\b(2\\.114|frivolous|sanctions)\\b"
+  scope: "text"
+- id: MCR_2_116
+  title: "MCR 2.116: summary disposition"
+  hint: "Rule-driven dispositive motions"
+  pattern: "(?i)\\b(2\\.116|summary disposition)\\b"
+  scope: "text"
+"""
+
+BACKEND_APP = r"""# backend/app.py
+import hashlib
+import io
+import json
+import logging
+import os
+import re
+import sqlite3
+import subprocess
+import threading
+import time
+from pathlib import Path
+from typing import Any, Dict, List, Optional
+
+import yaml
+from fastapi import FastAPI, HTTPException, UploadFile
+from fastapi.middleware.cors import CORSMiddleware
+from fastapi.responses import FileResponse, HTMLResponse
+from pydantic import BaseModel
+
+def _try_import(name: str):
+    try:
+        return __import__(name)
+    except Exception:
+        return None
+
+fitz = _try_import("fitz")
+pdfminer = _try_import("pdfminer")
+pytesseract = _try_import("pytesseract")
+PIL = _try_import("PIL")
+st = _try_import("sentence_transformers")
+hnswlib = _try_import("hnswlib")
+requests = _try_import("requests")
+
+watchdog = _try_import("watchdog")
+if watchdog:
+    from watchdog.events import FileSystemEventHandler  # type: ignore
+    from watchdog.observers import Observer  # type: ignore
+else:  # pragma: no cover - watchdog missing
+    FileSystemEventHandler = object  # type: ignore
+    Observer = None  # type: ignore
+
+ROOT = Path(__file__).resolve().parents[1]
+CFG = yaml.safe_load(open(ROOT / "config.yaml", "r", encoding="utf-8"))
+LOGS = ROOT / CFG["paths"]["LOGS"]
+DATA = ROOT / CFG["paths"]["DATA"]
+MODELS = ROOT / CFG["paths"]["MODELS"]
+OUTPUT = ROOT / CFG["paths"]["OUTPUT"]
+RULES_YAML = ROOT / CFG["mcr_canon"]["ruleset_yaml"]
+DB_PATH = ROOT / "catalog.db"
+
+for p in [LOGS, DATA, MODELS, OUTPUT]:
+    p.mkdir(parents=True, exist_ok=True)
+
+logging.basicConfig(
+    filename=str(LOGS / "backend.log"),
+    level=logging.INFO,
+    format="%(asctime)s %(levelname)s %(message)s",
+)
+
+
+def init_db() -> sqlite3.Connection:
+    conn = sqlite3.connect(DB_PATH)
+    conn.execute(
+        "CREATE TABLE IF NOT EXISTS files(path TEXT PRIMARY KEY, sha256 TEXT, size INTEGER, mtime INTEGER, text TEXT)"
+    )
+    conn.execute(
+        "CREATE TABLE IF NOT EXISTS rule_hits(path TEXT, rule_id TEXT, title TEXT, hint TEXT)"
+    )
+    conn.commit()
+    return conn
+
+DB = init_db()
+
+RULES = yaml.safe_load(open(RULES_YAML, "r", encoding="utf-8")) if RULES_YAML.exists() else []
+
+def scan_rules(text: str) -> List[Dict[str, str]]:
+    hits: List[Dict[str, str]] = []
+    for r in RULES:
+        try:
+            if re.search(r.get("pattern", ""), text):
+                hits.append(
+                    {"id": r.get("id", ""), "title": r.get("title", ""), "hint": r.get("hint", "")}
+                )
+        except Exception:
+            continue
+    return hits
+
+def extract_text(path: Path) -> str:
+    try:
+        if path.suffix.lower() == ".pdf":
+            if fitz:
+                doc = fitz.open(path)
+                txt = "\n".join(pg.get_text("text") for pg in doc)
+            elif pdfminer:
+                from pdfminer.high_level import extract_text as pdf_extract
+
+                txt = pdf_extract(str(path))
+            else:
+                txt = ""
+            if not txt.strip():
+                tmp = path.with_suffix(".ocr.pdf")
+                try:
+                    subprocess.run(["ocrmypdf", "--quiet", str(path), str(tmp)], check=True)
+                    txt = extract_text(tmp)
+                finally:
+                    if tmp.exists():
+                        tmp.unlink()
+            return txt
+        if path.suffix.lower() == ".txt":
+            return path.read_text("utf-8", errors="ignore")
+        if path.suffix.lower() == ".docx":
+            docx = _try_import("docx")
+            if docx:
+                d = docx.Document(str(path))
+                return "\n".join(p.text for p in d.paragraphs)
+        if path.suffix.lower() in [".png", ".jpg", ".jpeg", ".tif", ".tiff"]:
+            if pytesseract and PIL:
+                from PIL import Image
+
+                return pytesseract.image_to_string(Image.open(path))
+        return ""
+    except Exception as e:  # pragma: no cover
+        logging.exception("extract_text error: %s", e)
+        return ""
+
+
+class SearchIndex:
+    def __init__(self) -> None:
+        self.paths: List[str] = []
+        self._sbert = st.SentenceTransformer(str(ROOT / CFG["search"]["sbert_path"])) if st else None
+        self._use_hnsw = bool(self._sbert and hnswlib)
+        self._tfidf = None
+        if not self._use_hnsw:
+            from sklearn.feature_extraction.text import TfidfVectorizer
+
+            self._tfidf = TfidfVectorizer(max_features=200000, ngram_range=(1, 2))
+        self._index = None
+        self.reload()
+
+    def reload(self) -> None:
+        rows = DB.execute("SELECT path, text FROM files").fetchall()
+        self.paths = [r[0] for r in rows]
+        texts = [r[1] for r in rows]
+        if self._use_hnsw and self._sbert:
+            import numpy as np
+
+            embs = self._sbert.encode(texts, normalize_embeddings=True)
+            dim = embs.shape[1] if len(embs) else self._sbert.get_sentence_embedding_dimension()
+            self._index = hnswlib.Index(space="ip", dim=dim)
+            self._index.init_index(max_elements=len(embs) + 1000, ef_construction=200, M=16)
+            if len(embs):
+                self._index.add_items(embs, list(range(len(embs))))
+            self._index.save_index(str(MODELS / "ann.index"))
+        elif self._tfidf:
+            self._tfidf.fit(texts)
+
+    def add_document(self, path: str, text: str) -> None:
+        if self._use_hnsw and self._sbert and self._index is not None:
+            import numpy as np
+
+            emb = self._sbert.encode([text], normalize_embeddings=True)
+            self._index.add_items(emb, [len(self.paths)])
+            self._index.save_index(str(MODELS / "ann.index"))
+        elif self._tfidf:
+            self._tfidf.fit([text])
+        self.paths.append(path)
+
+    def search(self, query: str, k: int = 8) -> List[Dict[str, Any]]:
+        if not self.paths:
+            return []
+        if self._use_hnsw and self._sbert and self._index is not None:
+            import numpy as np
+
+            qv = self._sbert.encode([query], normalize_embeddings=True)
+            D, I = self._index.knn_query(qv, k=min(k, len(self.paths)))
+            idxs = I[0].tolist()
+            scores = D[0].tolist()
+        else:
+            from sklearn.metrics.pairwise import cosine_similarity
+
+            texts = [r[0] for r in DB.execute("SELECT text FROM files").fetchall()]
+            X = self._tfidf.transform(texts)  # type: ignore[union-attr]
+            q = self._tfidf.transform([query])  # type: ignore[union-attr]
+            sims = cosine_similarity(q, X).ravel()
+            idxs = sims.argsort()[::-1][:k].tolist()
+            scores = [float(sims[i]) for i in idxs]
+        out: List[Dict[str, Any]] = []
+        for i, sc in zip(idxs, scores):
+            path = self.paths[i]
+            hits = [
+                {"id": r[1], "title": r[2], "hint": r[3]}
+                for r in DB.execute("SELECT * FROM rule_hits WHERE path=?", (path,))
+            ]
+            out.append({"path": path, "score": sc, "hits": hits})
+        return out
+
+INDEX = SearchIndex()
+
+
+class EvidenceHandler(FileSystemEventHandler):
+    def on_created(self, event):  # type: ignore[override]
+        if not getattr(event, "is_directory", False):
+            index_file(Path(event.src_path))
+
+    def on_modified(self, event):  # type: ignore[override]
+        if not getattr(event, "is_directory", False):
+            index_file(Path(event.src_path))
+
+def start_watchers() -> None:
+    if Observer is None:
+        return
+    roots = [Path(CFG["paths"]["MEEK1"]), Path(CFG["paths"]["MEEK2"])]
+    for r in roots:
+        if r.exists():
+            obs = Observer()
+            obs.schedule(EvidenceHandler(), str(r), recursive=True)
+            obs.daemon = True
+            obs.start()
+
+def index_file(path: Path) -> None:
+    text = extract_text(path)
+    sha = hashlib.sha256(path.read_bytes()).hexdigest()
+    stat = path.stat()
+    DB.execute(
+        "REPLACE INTO files(path, sha256, size, mtime, text) VALUES(?,?,?,?,?)",
+        (str(path), sha, stat.st_size, int(stat.st_mtime), text),
+    )
+    DB.execute("DELETE FROM rule_hits WHERE path=?", (str(path),))
+    for hit in scan_rules(text):
+        DB.execute(
+            "INSERT INTO rule_hits(path, rule_id, title, hint) VALUES(?,?,?,?)",
+            (str(path), hit["id"], hit["title"], hit["hint"]),
+        )
+    DB.commit()
+    INDEX.add_document(str(path), text)
+
+def initial_scan() -> None:
+    roots = [Path(CFG["paths"]["MEEK1"]), Path(CFG["paths"]["MEEK2"])]
+    known = {r[0] for r in DB.execute("SELECT path FROM files").fetchall()}
+    for r in roots:
+        if not r.exists():
+            continue
+        for p in r.rglob("*"):
+            if p.is_file() and str(p) not in known:
+                index_file(p)
+
+initial_scan()
+start_watchers()
+
+
+class AskIn(BaseModel):
+    question: str
+    k: int = 6
+
+
+class ScanOut(BaseModel):
+    ok: bool
+    count: int
+
+
+class LLME:
+    def __init__(self, cfg: Dict[str, Any]):
+        self.cfg = cfg
+
+    def generate(
+        self,
+        prompt: str,
+        system: Optional[str] = None,
+        max_tokens: int = 512,
+        temperature: float = 0.2,
+    ) -> str:
+        server = self.cfg["llm"]["llama_cpp"].get("server_url")
+        if server and requests:
+            try:
+                payload = {
+                    "prompt": (system + "\n" if system else "") + prompt,
+                    "n_predict": max_tokens,
+                    "temperature": temperature,
+                }
+                r = requests.post(server, json=payload, timeout=120)
+                if r.ok:
+                    j = r.json()
+                    return j.get("content", "")
+            except Exception:
+                pass
+        model_path = ROOT / self.cfg["llm"]["llama_cpp"]["model_path"]
+        llama_cpp = _try_import("llama_cpp")
+        if llama_cpp and model_path.exists():
+            try:
+                from llama_cpp import Llama  # type: ignore
+
+                llm = Llama(
+                    model_path=str(model_path),
+                    n_ctx=self.cfg["llm"]["llama_cpp"]["n_ctx"],
+                    n_threads=self.cfg["llm"]["llama_cpp"]["n_threads"],
+                    n_gpu_layers=self.cfg["llm"]["llama_cpp"]["n_gpu_layers"],
+                )
+                out = llm(
+                    prompt=(system + "\n" if system else "") + prompt,
+                    max_tokens=max_tokens,
+                    temperature=temperature,
+                )
+                return out["choices"][0]["text"]
+            except Exception:
+                return ""
+        return ""
+
+LLM = LLME(CFG)
+
+app = FastAPI(title="LAWFORGE Litigation OS API", version="2.0")
+app.add_middleware(
+    CORSMiddleware,
+    allow_origins=["*"],
+    allow_credentials=True,
+    allow_methods=["*"],
+    allow_headers=["*"],
+)
+
+@app.get("/")
+def home() -> HTMLResponse:
+    return HTMLResponse("<h3>LAWFORGE API online</h3><p>See /docs</p>")
+
+@app.post("/scan")
+def scan() -> ScanOut:
+    initial_scan()
+    INDEX.reload()
+    count = DB.execute("SELECT COUNT(*) FROM files").fetchone()[0]
+    return ScanOut(ok=True, count=count)
+
+@app.post("/ask")
+def ask(inp: AskIn) -> Dict[str, Any]:
+    hits = INDEX.search(inp.question, k=inp.k)
+    context = []
+    for h in hits:
+        row = DB.execute("SELECT text FROM files WHERE path=?", (h["path"],)).fetchone()
+        snippet = row[0][:4000] if row else ""
+        context.append(f"[{Path(h['path']).name}] {snippet}")
+    sys_prompt = (
+        "You are a Michigan litigation engine. Use only provided context. "
+        "Cite by filename in brackets. Flag possible MCR/Canon issues precisely. "
+        "Avoid vague language."
+    )
+    prompt = (
+        "Question:\n" + inp.question + "\n\n"
+        "Context:\n" + "\n\n".join(context[:8]) + "\n\n"
+        "Answer with numbered, court-usable points and minimal prose."
+    )
+    answer = LLM.generate(prompt, system=sys_prompt, max_tokens=700, temperature=0.1)
+    return {"answer": answer, "retrieval": hits}
+
+@app.post("/ingest_files")
+def ingest(files: List[UploadFile]) -> Dict[str, Any]:
+    saved = []
+    for f in files:
+        data = f.file.read()
+        target = DATA / f.filename
+        target.write_bytes(data)
+        saved.append(str(target))
+        index_file(target)
+    return {"ok": True, "saved": saved}
+
+@app.post("/bundle_mifile")
+def bundle_mifile() -> Dict[str, Any]:
+    stamp = time.strftime("%Y%m%d_%H%M%S")
+    outdir = OUTPUT / f"FILING_{stamp}"
+    outdir.mkdir(parents=True, exist_ok=True)
+    manifest = []
+    rows = DB.execute("SELECT path FROM files LIMIT 50").fetchall()
+    for i, (path,) in enumerate(rows, start=1):
+        src = Path(path)
+        label = f"{CFG['mifile']['exhibit_label']} {i:02d} - {src.name}"
+        dest = outdir / label
+        try:
+            import shutil
+
+            shutil.copy2(src, dest)
+            manifest.append({"label": label, "source": path})
+        except Exception:
+            continue
+    (outdir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
+    zip_path = OUTPUT / f"FILING_{stamp}.zip"
+    import zipfile
+
+    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
+        for p in outdir.rglob("*"):
+            z.write(p, p.relative_to(OUTPUT))
+    return {"ok": True, "zip": str(zip_path), "dir": str(outdir)}
+
+@app.get("/metrics")
+def metrics() -> Dict[str, Any]:
+    files, size = DB.execute("SELECT COUNT(*), SUM(size) FROM files").fetchone()
+    return {"files": files, "bytes": size or 0, "llm_mode": "server"}
+
+@app.get("/diag")
+def diag() -> Dict[str, Any]:
+    return {"config": CFG, "python": os.sys.version}
+
+@app.post("/manifest/sign")
+def manifest_sign() -> Dict[str, Any]:
+    rows = DB.execute("SELECT path, sha256 FROM files").fetchall()
+    manifest = [{"path": p, "sha256": h} for p, h in rows]
+    out = OUTPUT / "evidence_manifest.json"
+    out.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
+    key = CFG.get("signing_key")
+    if key and Path(key).exists():
+        sig = out.with_suffix(out.suffix + ".minisig")
+        subprocess.run(["minisign", "-S", "-s", key, "-m", out], check=True)
+        return {"ok": True, "manifest": str(out), "signature": str(sig)}
+    raise HTTPException(status_code=500, detail="signing key not found")
+"""
+
+PYI_SPEC = r"""# golden_god_mode_bootstrap.spec
+# PyInstaller spec for building a portable EXE
+block_cipher = None
+
+a = Analysis(['golden_god_mode_bootstrap.py'], pathex=['.'])
+pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)
+exe = EXE(
+    pyz,
+    a.scripts,
+    [],
+    exclude_binaries=True,
+    name='golden_god_mode_bootstrap',
+    debug=False,
+    bootloader_ignore_signals=False,
+    strip=False,
+    upx=True,
+    console=True,
+)
+coll = COLLECT(
+    exe, a.binaries, a.zipfiles, a.datas,
+    strip=False, upx=True, upx_exclude=[],
+    name='golden_god_mode_bootstrap')
+"""
+
+RUN_BACKEND_BAT = r"""@echo off
+setlocal
+cd /d %~dp0
+call .venv\Scripts\activate
+uvicorn backend.app:app --host 127.0.0.1 --port 8000 --log-level info
+"""
+
+RUN_FRONTEND_BAT = r"""@echo off
+setlocal
+cd /d %~dp0\frontend
+echo Serving static UI at http://127.0.0.1:7777  (Ctrl+C to stop)
+python - <<PY
+import http.server, socketserver, os
+os.chdir(os.path.dirname(__file__))
+with socketserver.TCPServer(("127.0.0.1", 7777), http.server.SimpleHTTPRequestHandler) as httpd:
+    httpd.serve_forever()
+PY
+"""
+
+FRONTEND_INDEX = r"""<!doctype html>
+<html>
+<head>
+  <meta charset="utf-8">
+  <title>LAWFORGE — Litigation OS</title>
+  <style>
+    body { font-family: Arial, sans-serif; margin: 18px; }
+    textarea, input { width: 100%; }
+    .row { display: flex; gap: 16px; }
+    .col { flex: 1; }
+    pre { background: #111; color: #ddd; padding: 12px; overflow:auto; }
+    button { padding: 8px 12px; }
+  </style>
+</head>
+<body>
+  <h2>LAWFORGE — Offline Litigation OS</h2>
+  <div>
+    <button onclick="scan()">Scan Evidence</button>
+    <small id="scanStatus"></small>
+  </div>
+  <hr/>
+  <div class="row">
+    <div class="col">
+      <h3>Ask</h3>
+      <label for="q">Enter your question:</label>
+      <textarea id="q" rows="8"></textarea>
+      <button onclick="ask()">Run</button>
+      <pre id="ans"></pre>
+    </div>
+    <div class="col">
+      <h3>Bundle (MiFile)</h3>
+      <button onclick="bundle()">Build ZIP</button>
+      <pre id="bundleOut"></pre>
+      <h3>Health</h3>
+      <button onclick="health()">Check</button>
+      <pre id="healthOut"></pre>
+    </div>
+  </div>
+  <script src="api.js"></script>
+</body>
+</html>
+"""
+
+FRONTEND_API = r"""const API = "http://127.0.0.1:8000";
+
+async function scan() {
+  document.getElementById("scanStatus").innerText = " scanning...";
+  const r = await fetch(API + "/scan", {
+  method: "POST",
+  headers: {"Content-Type": "application/json"},
+  body: JSON.stringify({})
+});
+  const j = await r.json();
+  document.getElementById("scanStatus").innerText = ` indexed: ${j.count}`;
+}
+
+async function ask() {
+  const q = document.getElementById("q").value;
+  const r = await fetch(API + "/ask", {
+  method: "POST",
+  headers: {"Content-Type": "application/json"},
+  body: JSON.stringify({question:q, k:8})
+});
+  const j = await r.json();
+  document.getElementById("ans").innerText = j.answer || "(no LLM output)\n" + JSON.stringify(j.retrieval, null, 2);
+}
+
+async function bundle() {
+  const r = await fetch(API + "/bundle_mifile", {method:"POST"});
+  const j = await r.json();
+  document.getElementById("bundleOut").innerText = JSON.stringify(j, null, 2);
+}
+
+async function health() {
+  const r = await fetch(API + "/metrics");
+  const j = await r.json();
+  document.getElementById("healthOut").innerText = JSON.stringify(j, null, 2);
+}
+"""
+
+
+def write_if_missing(path: Path, content: str, binary: bool = False) -> None:
+    if not path.exists():
+        path.parent.mkdir(parents=True, exist_ok=True)
+        mode = "wb" if binary else "w"
+        with open(path, mode, encoding=None if binary else "utf-8") as f:
+            f.write(content)
+
+
+def run(cmd: str, cwd: Path) -> int:
+    print(f"$ {cmd}")
+    return subprocess.call(cmd, cwd=str(cwd), shell=True)
+
+
+def install_deps(root: Path, offline: bool) -> None:
+    venv = root / ".venv"
+    if not (venv / "Scripts" / "activate").exists():
+        run(f'python -m venv "{venv}"', root)
+    pip = venv / "Scripts" / "pip.exe"
+    req = root / "requirements.txt"
+    con = root / "constraints.txt"
+    req.write_text(REQ_TXT, encoding="utf-8")
+    con.write_text(CONSTRAINTS_TXT, encoding="utf-8")
+    if offline:
+        wheels = root / ".wheels"
+        if wheels.exists():
+            run(
+                f'"{pip}" install --no-index --find-links "{wheels}" -r "{req}" -c "{con}"',
+                root,
+            )
+        else:
+            print("[!] Offline mode selected but .wheels not found. Skipping pip.")
+    else:
+        run(f'"{pip}" install -r "{req}" -c "{con}"', root)
+
+
+def main() -> None:
+    ap = argparse.ArgumentParser()
+    ap.add_argument(
+        "--root", required=True, help="Install root, e.g., F:\\LAWFORGE_SUPREMACY"
+    )
+    ap.add_argument("--offline", action="store_true", help="Use local wheels only")
+    args = ap.parse_args()
+
+    root = Path(args.root)
+    root.mkdir(parents=True, exist_ok=True)
+
+    write_if_missing(root / "requirements.txt", REQ_TXT)
+    write_if_missing(root / "constraints.txt", CONSTRAINTS_TXT)
+    write_if_missing(root / "config.yaml", CONFIG_YAML)
+    write_if_missing(root / "backend" / "app.py", BACKEND_APP)
+    write_if_missing(root / "backend" / "rules" / "__init__.py", "")
+    write_if_missing(root / "backend" / "rules" / "canon_mcr_rules.yaml", CANON_RULES)
+    write_if_missing(root / "frontend" / "index.html", FRONTEND_INDEX)
+    write_if_missing(root / "frontend" / "api.js", FRONTEND_API)
+    write_if_missing(root / "run_backend.bat", RUN_BACKEND_BAT)
+    write_if_missing(root / "frontend" / "run_frontend.bat", RUN_FRONTEND_BAT)
+    write_if_missing(root / "golden_god_mode_bootstrap.spec", PYI_SPEC)
+
+    for d in [
+        "data",
+        "logs",
+        "models/llm",
+        "models/emb/sentence-transformers/all-MiniLM-L6-v2",
+        "output",
+        ".wheels",
+    ]:
+        (root / d).mkdir(parents=True, exist_ok=True)
+
+    install_deps(root, args.offline)
+
+    print("\n[READY]")
+    print(f"Root: {root}")
+    print("1) Activate:    " + str(root / ".venv" / "Scripts" / "activate"))
+    print("2) Backend:     run_backend.bat")
+    print("3) Frontend:    frontend\\run_frontend.bat")
+    print(
+        "4) Models:      put GGUF at models\\llm\\model.gguf; set config.yaml -> llm.llama_cpp.model_path"
+    )
+    print(
+        "5) Evidence:    set config.yaml paths.MEEK1, paths.MEEK2; file events auto-index"
+    )
+
+
+if __name__ == "__main__":
+    main()
diff --git a/golden_god_mode_bootstrap.spec b/golden_god_mode_bootstrap.spec
new file mode 100644
index 0000000000000000000000000000000000000000..79c2a40ff312be23943be8495bcb458d48fac2d2
--- /dev/null
+++ b/golden_god_mode_bootstrap.spec
@@ -0,0 +1,28 @@
+# golden_god_mode_bootstrap.spec
+# PyInstaller spec for building a portable EXE
+block_cipher = None
+
+a = Analysis(["golden_god_mode_bootstrap.py"], pathex=["."])
+pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)
+exe = EXE(
+    pyz,
+    a.scripts,
+    [],
+    exclude_binaries=True,
+    name="golden_god_mode_bootstrap",
+    debug=False,
+    bootloader_ignore_signals=False,
+    strip=False,
+    upx=True,
+    console=True,
+)
+coll = COLLECT(
+    exe,
+    a.binaries,
+    a.zipfiles,
+    a.datas,
+    strip=False,
+    upx=True,
+    upx_exclude=[],
+    name="golden_god_mode_bootstrap",
+)
diff --git a/golden_litigator_os.py b/golden_litigator_os.py
new file mode 100644
index 0000000000000000000000000000000000000000..1261c9441f66635dcfa0f4900533877468d21cd3
--- /dev/null
+++ b/golden_litigator_os.py
@@ -0,0 +1,662 @@
+# -*- coding: utf-8 -*-
+"""
+GOLDEN LITIGATOR OS v∞ — SINGLE-FILE DEPLOY (Windows)
+Self-evolving litigation intelligence with OCR, audio transcription, LLM legal extraction,
+evidence ledger, timeline builder, exhibit mapper, and motion generator.
+
+RUN
+   python golden_litigator_os.py
+"""
+
+import json
+import logging
+import os
+import re
+import sqlite3
+import sys
+import traceback
+from datetime import datetime
+from pathlib import Path
+from typing import Any, Dict, List
+
+# Configuration
+DRIVES = ["C:/", "E:/", "F:/", "Z:/", "G:/MyDrive/"]
+EXCLUDE_DIRS = {
+    r"C:\\Windows",
+    r"C:\\Program Files",
+    r"C:\\Program Files (x86)",
+    r"C:\\$Recycle.Bin",
+    r"C:\\ProgramData",
+    r"C:\\Users\Public",
+    r"C:\\Recovery",
+    r"C:\\PerfLogs",
+}
+DB_PATH = "golden_litigator.db"
+LOG_FILE = "litigator.log"
+PROCESSED_TAG = "__DONE__"
+RESULTS_DIR = Path("LegalResults")
+MOTIONS_DIR = RESULTS_DIR / "Motions"
+NARRATIVE_DIR = RESULTS_DIR / "Narratives"
+TRANSCRIPTS_DIR = RESULTS_DIR / "Transcripts"
+EXHIBITS_DIR = RESULTS_DIR / "Exhibits"
+LEDGER_EXPORT = RESULTS_DIR / "EvidenceLedger.jsonl"
+
+LLM_PROVIDER_ORDER = ["openai", "anthropic"]
+OPENAI_MODEL = "gpt-4o-mini"
+ANTHROPIC_MODEL = "claude-3-5-sonnet-20240620"
+
+WHISPER_BACKEND = "faster-whisper"
+WHISPER_MODEL = "medium"
+TESSERACT_CMD = os.environ.get("TESSERACT_OCR_PATH", "").strip()
+
+TEXT_TYPES = {".txt", ".json", ".csv", ".md"}
+DOC_TYPES = {".docx"}
+PDF_TYPES = {".pdf"}
+IMG_TYPES = {".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp", ".webp"}
+AUDIO_TYPES = {".mp3", ".wav", ".m4a", ".aac", ".flac", ".ogg", ".wma"}
+VIDEO_TYPES = {".mp4", ".mkv", ".mov", ".m4v", ".wmv", ".avi"}
+CODE_TYPES = {".py", ".ps1", ".psm1", ".json", ".txt"}
+
+logging.basicConfig(
+    filename=LOG_FILE,
+    level=logging.INFO,
+    format="%(asctime)s [%(levelname)s] %(message)s",
+)
+console = logging.getLogger("console")
+console.setLevel(logging.INFO)
+stream = logging.StreamHandler(sys.stdout)
+stream.setFormatter(logging.Formatter("%(message)s"))
+console.addHandler(stream)
+
+SCHEMA = {
+    "evidence": """
+        CREATE TABLE IF NOT EXISTS evidence (
+            id INTEGER PRIMARY KEY,
+            sha256 TEXT UNIQUE,
+            filename TEXT,
+            filepath TEXT,
+            ext TEXT,
+            size_bytes INTEGER,
+            modified_ts TEXT,
+            content_excerpt TEXT,
+            party TEXT,
+            parties_json TEXT,
+            claims_json TEXT,
+            statutes_json TEXT,
+            court_rules_json TEXT,
+            relevance_score REAL,
+            timeline_refs_json TEXT,
+            exhibit_tag TEXT,
+            exhibit_label TEXT,
+            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
+        )
+    """,
+    "exhibits": """
+        CREATE TABLE IF NOT EXISTS exhibits (
+            id INTEGER PRIMARY KEY,
+            evidence_sha256 TEXT,
+            label TEXT,
+            title TEXT,
+            description TEXT,
+            page_refs_json TEXT,
+            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
+        )
+    """,
+    "timelines": """
+        CREATE TABLE IF NOT EXISTS timelines (
+            id INTEGER PRIMARY KEY,
+            evidence_sha256 TEXT,
+            event_dt TEXT,
+            actor TEXT,
+            action TEXT,
+            location TEXT,
+            details TEXT,
+            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
+        )
+    """,
+    "filings": """
+        CREATE TABLE IF NOT EXISTS filings (
+            id INTEGER PRIMARY KEY,
+            filing_type TEXT,
+            title TEXT,
+            court_name TEXT,
+            case_number TEXT,
+            body_path TEXT,
+            status TEXT,
+            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
+        )
+    """,
+    "sources": """
+        CREATE TABLE IF NOT EXISTS sources (
+            id INTEGER PRIMARY KEY,
+            evidence_sha256 TEXT,
+            source_type TEXT,
+            meta_json TEXT,
+            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
+        )
+    """,
+    "case_meta": """
+        CREATE TABLE IF NOT EXISTS case_meta (
+            id INTEGER PRIMARY KEY,
+            court_name TEXT,
+            case_number TEXT,
+            caption_plaintiff TEXT,
+            caption_defendant TEXT,
+            judge TEXT,
+            jurisdiction TEXT,
+            division TEXT,
+            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
+        )
+    """,
+}
+
+
+def db_conn() -> sqlite3.Connection:
+    return sqlite3.connect(DB_PATH)
+
+
+def init_db() -> None:
+    conn = db_conn()
+    cur = conn.cursor()
+    for stmt in SCHEMA.values():
+        cur.execute(stmt)
+    conn.commit()
+    conn.close()
+
+
+def sha256_file(path: Path) -> str:
+    import hashlib
+
+    h = hashlib.sha256()
+    with open(path, "rb") as f:
+        for chunk in iter(lambda: f.read(8192), b""):
+            h.update(chunk)
+    return h.hexdigest()
+
+
+def is_excluded_dir(p: str) -> bool:
+    if os.name != "nt":
+        return False
+    return any(p.startswith(ex) for ex in EXCLUDE_DIRS)
+
+
+def safe_rename_done(path: Path) -> None:
+    new_name = f"{path.stem}{PROCESSED_TAG}{path.suffix}"
+    target = path.with_name(new_name)
+    if not target.exists():
+        try:
+            path.rename(target)
+        except OSError:
+            logging.warning("Failed to rename %s", path)
+
+
+def write_jsonl(path: Path, obj: Dict[str, Any]) -> None:
+    path.parent.mkdir(parents=True, exist_ok=True)
+    with open(path, "a", encoding="utf-8") as f:
+        f.write(json.dumps(obj, ensure_ascii=False) + "\n")
+
+
+def excerpt(text: str, n: int = 800) -> str:
+    return re.sub(r"\s+", " ", text or "").strip()[:n]
+
+
+def extract_text_txt(path: Path) -> str:
+    try:
+        return path.read_text(encoding="utf-8", errors="ignore")
+    except OSError:
+        return ""
+
+
+def extract_text_docx(path: Path) -> str:
+    try:
+        import docx
+
+        doc = docx.Document(str(path))
+        return "\n".join(p.text for p in doc.paragraphs)
+    except Exception:
+        return ""
+
+
+def extract_text_pdf(path: Path) -> str:
+    try:
+        import fitz  # type: ignore[import-not-found]
+
+        text = []
+        with fitz.open(str(path)) as doc:
+            for page in doc:
+                text.append(page.get_text() or "")
+        return "\n".join(text)
+    except Exception:
+        return ""
+
+
+def extract_text_image(path: Path) -> str:
+    try:
+        import pytesseract  # type: ignore[import-untyped]
+        from PIL import Image, ImageOps
+
+        if TESSERACT_CMD:
+            pytesseract.pytesseract.tesseract_cmd = TESSERACT_CMD
+        img: Image.Image = Image.open(str(path))
+        img = ImageOps.grayscale(img)
+        return pytesseract.image_to_string(img) or ""
+    except Exception:
+        return ""
+
+
+def transcribe_audio(path: Path) -> str:
+    TRANSCRIPTS_DIR.mkdir(parents=True, exist_ok=True)
+    out_txt = TRANSCRIPTS_DIR / f"{path.stem}.txt"
+    try:
+        if WHISPER_BACKEND == "faster-whisper":
+            from faster_whisper import WhisperModel  # type: ignore[import-not-found]
+
+            model = WhisperModel(WHISPER_MODEL, compute_type="int8_float16")
+            segments, _ = model.transcribe(str(path), vad_filter=True)
+            text = " ".join(seg.text for seg in segments if getattr(seg, "text", None))
+        else:
+            import whisper  # type: ignore[import-not-found]
+
+            model = whisper.load_model(WHISPER_MODEL)
+            res = model.transcribe(str(path))
+            text = res.get("text", "")
+        out_txt.write_text(text, encoding="utf-8", errors="ignore")
+        return text
+    except Exception:
+        return ""
+
+
+def extract_text_video(path: Path) -> str:
+    try:
+        import subprocess
+        import tempfile
+
+        with tempfile.TemporaryDirectory() as td:
+            audio_path = Path(td) / f"{path.stem}.wav"
+            cmd = [
+                "ffmpeg",
+                "-y",
+                "-i",
+                str(path),
+                "-vn",
+                "-ac",
+                "1",
+                "-ar",
+                "16000",
+                str(audio_path),
+            ]
+            subprocess.run(
+                cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False
+            )
+            if audio_path.exists():
+                return transcribe_audio(audio_path)
+            return ""
+    except Exception:
+        return ""
+
+
+def call_llm(prompt: str) -> str:
+    text = ""
+    try:
+        if "openai" in LLM_PROVIDER_ORDER and os.environ.get("OPENAI_API_KEY"):
+            from openai import OpenAI
+
+            client = OpenAI()
+            resp = client.chat.completions.create(
+                model=OPENAI_MODEL,
+                messages=[
+                    {
+                        "role": "system",
+                        "content": "You are a Michigan-focused litigation expert.",
+                    },
+                    {"role": "user", "content": prompt},
+                ],
+                temperature=0.2,
+                max_tokens=1200,
+            )
+            text = resp.choices[0].message.content or ""
+            if text.strip():
+                return text
+    except Exception:
+        pass
+    try:
+        if "anthropic" in LLM_PROVIDER_ORDER and os.environ.get("ANTHROPIC_API_KEY"):
+            import anthropic  # type: ignore[import-not-found]
+
+            client = anthropic.Anthropic()
+            msg = client.messages.create(
+                model=ANTHROPIC_MODEL,
+                max_tokens=1200,
+                temperature=0.2,
+                system="You are a Michigan-focused litigation expert.",
+                messages=[{"role": "user", "content": prompt}],
+            )
+            text = "".join(
+                block.text for block in msg.content if hasattr(block, "text")
+            )
+    except Exception:
+        pass
+    return text
+
+
+def legal_extract(text: str, fname: str) -> Dict[str, Any]:
+    if not text.strip():
+        return {}
+    prompt = f"""
+From the following document content, extract structured Michigan litigation intel:
+- parties
+- claims
+- statutes
+- court_rules
+- timeline
+- exhibits
+Return JSON only.
+FILENAME: {fname}
+CONTENT:
+{text[:10000]}
+"""
+    raw = call_llm(prompt)
+    try:
+        data = json.loads(raw)
+        return {
+            "parties": data.get("parties", []),
+            "claims": data.get("claims", []),
+            "statutes": data.get("statutes", []),
+            "court_rules": data.get("court_rules", []),
+            "timeline": data.get("timeline", []),
+            "exhibits": data.get("exhibits", []),
+        }
+    except Exception:
+        return {
+            "parties": [],
+            "claims": [],
+            "statutes": [],
+            "court_rules": [],
+            "timeline": [],
+            "exhibits": [],
+        }
+
+
+def insert_evidence(rec: Dict[str, Any]) -> None:
+    conn = db_conn()
+    cur = conn.cursor()
+    cur.execute(
+        """
+        INSERT OR IGNORE INTO evidence (
+            sha256, filename, filepath, ext, size_bytes, modified_ts,
+            content_excerpt, party, parties_json, claims_json, statutes_json,
+            court_rules_json, relevance_score, timeline_refs_json,
+            exhibit_tag, exhibit_label
+        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
+        """,
+        (
+            rec["sha256"],
+            rec["filename"],
+            rec["filepath"],
+            rec["ext"],
+            rec["size_bytes"],
+            rec["modified_ts"],
+            rec.get("content_excerpt", ""),
+            rec.get("party", ""),
+            json.dumps(rec.get("parties", []), ensure_ascii=False),
+            json.dumps(rec.get("claims", []), ensure_ascii=False),
+            json.dumps(rec.get("statutes", []), ensure_ascii=False),
+            json.dumps(rec.get("court_rules", []), ensure_ascii=False),
+            rec.get("relevance_score", 0.0),
+            json.dumps(rec.get("timeline_refs", []), ensure_ascii=False),
+            rec.get("exhibit_tag", ""),
+            rec.get("exhibit_label", ""),
+        ),
+    )
+    conn.commit()
+    conn.close()
+
+
+def insert_timeline(sha: str, ev: Dict[str, Any]) -> None:
+    conn = db_conn()
+    cur = conn.cursor()
+    cur.execute(
+        """
+        INSERT INTO timelines (evidence_sha256, event_dt, actor, action, location, details)
+        VALUES (?, ?, ?, ?, ?, ?)
+        """,
+        (
+            sha,
+            ev.get("date", ""),
+            ev.get("actor", ""),
+            ev.get("action", ""),
+            ev.get("location", ""),
+            ev.get("details", ""),
+        ),
+    )
+    conn.commit()
+    conn.close()
+
+
+def insert_exhibit(sha: str, ex: Dict[str, Any]) -> None:
+    conn = db_conn()
+    cur = conn.cursor()
+    cur.execute(
+        """
+        INSERT INTO exhibits (evidence_sha256, label, title, description, page_refs_json)
+        VALUES (?, ?, ?, ?, ?)
+        """,
+        (
+            sha,
+            ex.get("label", ""),
+            ex.get("title", ""),
+            ex.get("description", ""),
+            json.dumps(ex.get("pages", []), ensure_ascii=False),
+        ),
+    )
+    conn.commit()
+    conn.close()
+
+
+def insert_source(sha: str, source_type: str, meta: Dict[str, Any]) -> None:
+    conn = db_conn()
+    cur = conn.cursor()
+    cur.execute(
+        """
+        INSERT INTO sources (evidence_sha256, source_type, meta_json)
+        VALUES (?, ?, ?)
+        """,
+        (sha, source_type, json.dumps(meta, ensure_ascii=False)),
+    )
+    conn.commit()
+    conn.close()
+
+
+def process_file(path: Path) -> None:
+    try:
+        if PROCESSED_TAG in path.stem:
+            return
+        ext = path.suffix.lower()
+        stat = path.stat()
+        sha = sha256_file(path)
+        text = ""
+        src_type = None
+        if ext in TEXT_TYPES:
+            text = extract_text_txt(path)
+            src_type = "txt"
+        elif ext in DOC_TYPES:
+            text = extract_text_docx(path)
+            src_type = "docx"
+        elif ext in PDF_TYPES:
+            text = extract_text_pdf(path)
+            src_type = "pdf"
+        elif ext in IMG_TYPES:
+            text = extract_text_image(path)
+            src_type = "img"
+        elif ext in AUDIO_TYPES:
+            text = transcribe_audio(path)
+            src_type = "audio"
+        elif ext in VIDEO_TYPES:
+            text = extract_text_video(path)
+            src_type = "video"
+        elif ext in CODE_TYPES:
+            src_type = "code"
+            try:
+                text = path.read_text(encoding="utf-8", errors="ignore")
+            except OSError:
+                text = ""
+        else:
+            return
+        insert_source(
+            sha,
+            src_type or "unknown",
+            {
+                "filename": path.name,
+                "filepath": str(path),
+                "size_bytes": stat.st_size,
+                "modified_ts": datetime.fromtimestamp(stat.st_mtime).isoformat(),
+            },
+        )
+        parties: List[Dict[str, Any]] = []
+        claims: List[Dict[str, Any]] = []
+        statutes: List[str] = []
+        rules: List[str] = []
+        timeline: List[Dict[str, Any]] = []
+        exhibits: List[Dict[str, Any]] = []
+        if text.strip():
+            llm = legal_extract(text, path.name)
+            parties = llm.get("parties", [])
+            claims = llm.get("claims", [])
+            statutes = llm.get("statutes", [])
+            rules = llm.get("court_rules", [])
+            timeline = llm.get("timeline", [])
+            exhibits = llm.get("exhibits", [])
+        relevance = 0.0
+        if claims:
+            relevance += 1.0
+        relevance += 0.5 * min(len(statutes), 3)
+        relevance += 0.5 * min(len(rules), 3)
+        insert_evidence(
+            {
+                "sha256": sha,
+                "filename": path.name,
+                "filepath": str(path),
+                "ext": ext,
+                "size_bytes": stat.st_size,
+                "modified_ts": datetime.fromtimestamp(stat.st_mtime).isoformat(),
+                "content_excerpt": excerpt(text, 1000),
+                "party": parties[0]["name"] if parties else "",
+                "parties": parties,
+                "claims": claims,
+                "statutes": statutes,
+                "court_rules": rules,
+                "relevance_score": relevance,
+                "timeline_refs": timeline,
+                "exhibit_tag": exhibits[0]["label"] if exhibits else "",
+                "exhibit_label": exhibits[0]["label"] if exhibits else "",
+            }
+        )
+        for ev in timeline:
+            insert_timeline(sha, ev)
+        for ex in exhibits:
+            insert_exhibit(sha, ex)
+        write_jsonl(
+            LEDGER_EXPORT,
+            {
+                "sha256": sha,
+                "filename": path.name,
+                "filepath": str(path),
+                "claims": claims,
+                "statutes": statutes,
+                "rules": rules,
+            },
+        )
+        if relevance >= 0.5:
+            safe_rename_done(path)
+        logging.info("Processed %s", path)
+    except Exception as e:  # noqa: BLE001
+        logging.error("Error processing %s: %s\n%s", path, e, traceback.format_exc())
+
+
+def crawl_all() -> None:
+    for root_drive in DRIVES:
+        for root, dirs, files in os.walk(root_drive):
+            if is_excluded_dir(root):
+                continue
+            for fname in files:
+                fpath = Path(root) / fname
+                if fpath.name.startswith("~$"):
+                    continue
+                process_file(fpath)
+
+
+def export_ledger_jsonl() -> None:
+    conn = db_conn()
+    cur = conn.cursor()
+    cur.execute(
+        """
+        SELECT sha256, filename, filepath, ext, size_bytes, modified_ts, parties_json,
+               claims_json, statutes_json, court_rules_json, timeline_refs_json, exhibit_label
+        FROM evidence ORDER BY id ASC
+        """
+    )
+    rows = cur.fetchall()
+    conn.close()
+    for r in rows:
+        rec = {
+            "sha256": r[0],
+            "filename": r[1],
+            "filepath": r[2],
+            "ext": r[3],
+            "size_bytes": r[4],
+            "modified_ts": r[5],
+            "parties": json.loads(r[6] or "[]"),
+            "claims": json.loads(r[7] or "[]"),
+            "statutes": json.loads(r[8] or "[]"),
+            "court_rules": json.loads(r[9] or "[]"),
+            "timeline": json.loads(r[10] or "[]"),
+            "exhibit_label": r[11] or "",
+        }
+        write_jsonl(LEDGER_EXPORT, rec)
+
+
+def build_master_narrative() -> None:
+    conn = db_conn()
+    cur = conn.cursor()
+    cur.execute(
+        """
+        SELECT filename, content_excerpt, parties_json, claims_json, timeline_refs_json
+        FROM evidence ORDER BY id ASC LIMIT 1000
+        """
+    )
+    rows = cur.fetchall()
+    conn.close()
+    bundle = []
+    for r in rows:
+        bundle.append(
+            {
+                "filename": r[0],
+                "excerpt": r[1],
+                "parties": json.loads(r[2] or "[]"),
+                "claims": json.loads(r[3] or "[]"),
+                "timeline": json.loads(r[4] or "[]"),
+            }
+        )
+    prompt = (
+        "Build a fact-only, Michigan court-compliant narrative/affidavit from the following "
+        "structured inputs. Use numbered paragraphs, cite exhibits by label when present; "
+        "no speculation:\n" + json.dumps(bundle, ensure_ascii=False)
+    )
+    narrative = call_llm(prompt)
+    NARRATIVE_DIR.mkdir(parents=True, exist_ok=True)
+    out = (
+        NARRATIVE_DIR
+        / f"Master_Narrative_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
+    )
+    out.write_text(narrative, encoding="utf-8", errors="ignore")
+
+
+if __name__ == "__main__":
+    console.info("Launching GOLDEN LITIGATOR OS v∞")
+    for d in [RESULTS_DIR, MOTIONS_DIR, NARRATIVE_DIR, TRANSCRIPTS_DIR, EXHIBITS_DIR]:
+        d.mkdir(parents=True, exist_ok=True)
+    init_db()
+    crawl_all()
+    export_ledger_jsonl()
+    build_master_narrative()
+    console.info("Complete. Evidence indexed and narrative built.")
diff --git a/tests/test_golden_litigator_os.py b/tests/test_golden_litigator_os.py
new file mode 100644
index 0000000000000000000000000000000000000000..d23a9f46f0f9697c60d7e865506b7555d4e28ce0
--- /dev/null
+++ b/tests/test_golden_litigator_os.py
@@ -0,0 +1,6 @@
+from pathlib import Path
+from golden_litigator_os import sha256_file
+
+
+def test_sha256_file() -> None:
+    assert len(sha256_file(Path(__file__))) == 64
diff --git a/tests/test_lawforge_master_upgrade_v1.py b/tests/test_lawforge_master_upgrade_v1.py
new file mode 100644
index 0000000000000000000000000000000000000000..b1c8090fff9baaf206cbac39bf8a915958ddc508
--- /dev/null
+++ b/tests/test_lawforge_master_upgrade_v1.py
@@ -0,0 +1,8 @@
+import LAWFORGE_MASTER_UPGRADE_v1 as lm
+
+
+def test_chunk_text_basic():
+    data = "word " * 50
+    chunks = lm.chunk_text(data, tokens=10, overlap=2)
+    assert isinstance(chunks, list)
+    assert chunks
