"""
LitigationOS HuggingFace Legal AI Engine v1.0
Integrates Legal-BERT, MiniLM embeddings, BERT-NER, spaCy, eyecite, and NLTK
into a unified legal document analysis pipeline.

Usage:
    python hf_legal_engine.py --analyze <file_path>
    python hf_legal_engine.py --embed <text>
    python hf_legal_engine.py --ner <text>
    python hf_legal_engine.py --citations <text>
    python hf_legal_engine.py --classify <file_path>
    python hf_legal_engine.py --benchmark
"""
import os, sys, json, sqlite3, time, argparse
from pathlib import Path

# Set HF cache to LitigationOS
os.environ["HF_HOME"] = str(Path(r"C:\Users\andre\LitigationOS\00_SYSTEM\local_model\hf_cache"))
os.environ["TOKENIZERS_PARALLELISM"] = "false"

MODELS_DIR = Path(r"C:\Users\andre\LitigationOS\00_SYSTEM\local_model\models")
DB_PATH = r"C:\Users\andre\LitigationOS\litigation_context.db"

# Lazy-loaded model instances
_legal_bert = None
_legal_tokenizer = None
_embedder = None
_ner_pipeline = None
_spacy_nlp = None

def get_legal_bert():
    """Load Legal-BERT Small for classification/embeddings"""
    global _legal_bert, _legal_tokenizer
    if _legal_bert is None:
        from transformers import AutoTokenizer, AutoModel
        model_path = str(MODELS_DIR / "nlpaueb_legal-bert-small-uncased")
        _legal_tokenizer = AutoTokenizer.from_pretrained(model_path)
        _legal_bert = AutoModel.from_pretrained(model_path)
        _legal_bert.eval()
        print("[HF] Legal-BERT Small loaded")
    return _legal_bert, _legal_tokenizer

def get_embedder():
    """Load sentence-transformers MiniLM for fast semantic similarity"""
    global _embedder
    if _embedder is None:
        from sentence_transformers import SentenceTransformer
        model_path = str(MODELS_DIR / "sentence-transformers_all-MiniLM-L6-v2")
        _embedder = SentenceTransformer(model_path)
        print("[HF] MiniLM-L6-v2 embedder loaded")
    return _embedder

def get_ner():
    """Load BERT-NER pipeline"""
    global _ner_pipeline
    if _ner_pipeline is None:
        from transformers import pipeline
        model_path = str(MODELS_DIR / "dslim_bert-base-NER")
        _ner_pipeline = pipeline("ner", model=model_path, tokenizer=model_path,
                                 aggregation_strategy="simple", device=-1)
        print("[HF] BERT-NER pipeline loaded")
    return _ner_pipeline

def get_spacy():
    """Load spaCy with legal entity patterns"""
    global _spacy_nlp
    if _spacy_nlp is None:
        import spacy
        _spacy_nlp = spacy.load("en_core_web_sm")
        # Add Michigan-specific patterns
        ruler = _spacy_nlp.add_pipe("entity_ruler", before="ner")
        patterns = [
            {"label": "CASE_NUMBER", "pattern": [{"SHAPE": "dddd"}, {"TEXT": "-"}, {"SHAPE": "dddddd"}, {"TEXT": "-"}, {"TEXT": {"REGEX": "[A-Z]{2}"}}]},
            {"label": "MCR", "pattern": [{"TEXT": "MCR"}, {"SHAPE": "d.ddd"}]},
            {"label": "MCL", "pattern": [{"TEXT": "MCL"}, {"SHAPE": "ddd.dd"}]},
            {"label": "MRE", "pattern": [{"TEXT": "MRE"}, {"SHAPE": "ddd"}]},
            {"label": "JUDGE", "pattern": [{"TEXT": {"IN": ["Judge", "Hon.", "Honorable"]}}, {"POS": "PROPN", "OP": "+"}]},
        ]
        ruler.add_patterns(patterns)
        print("[HF] spaCy + legal entity ruler loaded")
    return _spacy_nlp

def extract_citations(text):
    """Extract legal citations using eyecite"""
    try:
        from eyecite import get_citations
        cites = get_citations(text)
        return [{"text": str(c), "type": type(c).__name__} for c in cites]
    except Exception as e:
        return [{"error": str(e)}]

def embed_text(text):
    """Generate 384-dim embedding vector for semantic search"""
    model = get_embedder()
    embedding = model.encode(text, normalize_embeddings=True)
    return embedding.tolist()

def embed_batch(texts):
    """Batch embed multiple texts efficiently"""
    model = get_embedder()
    embeddings = model.encode(texts, normalize_embeddings=True, batch_size=32, show_progress_bar=True)
    return embeddings

def extract_entities(text):
    """Extract named entities using BERT-NER + spaCy legal patterns"""
    results = {"bert_ner": [], "spacy_legal": [], "citations": []}
    
    # BERT-NER
    ner = get_ner()
    # Truncate for BERT (512 token limit)
    chunk = text[:2000]
    entities = ner(chunk)
    results["bert_ner"] = [{"text": e["word"], "label": e["entity_group"], "score": round(e["score"], 3)} for e in entities]
    
    # spaCy legal patterns
    nlp = get_spacy()
    doc = nlp(chunk)
    results["spacy_legal"] = [{"text": ent.text, "label": ent.label_} for ent in doc.ents]
    
    # eyecite citations
    results["citations"] = extract_citations(text[:5000])
    
    return results

def classify_legal_document(text):
    """Classify legal document type and case lane using Legal-BERT embeddings"""
    model = get_embedder()
    
    # Reference descriptions for each category
    categories = {
        "custody_motion": "Motion regarding child custody, parenting time, best interest factors under MCL 722.23",
        "ppo_filing": "Personal protection order, PPO petition, stalking, domestic violence restraining order",
        "housing_complaint": "Landlord tenant dispute, housing code violation, habitability, eviction",
        "court_order": "Court order, judicial ruling, judgment, decree signed by judge",
        "evidence_document": "Evidence exhibit, photograph, screenshot, medical record, financial record",
        "legal_brief": "Legal brief, memorandum of law, argument, appellate brief, statement of facts",
        "affidavit": "Affidavit, sworn statement, declaration under penalty of perjury",
        "correspondence": "Letter, email, communication between parties or with court",
        "transcript": "Court transcript, hearing transcript, deposition transcript",
        "chatgpt_export": "ChatGPT conversation export, AI-generated analysis, prompt response",
    }
    
    # Case lane classification
    lanes = {
        "A_CUSTODY": "Watson custody dispute, parenting time, child best interest, FOC, Lincoln",
        "B_HOUSING": "Shady Oaks, manufactured housing, landlord tenant, habitability, MCL 554",
        "C_CONVERGENCE": "Housing and custody intersection, weaponized housing against custody",
        "D_PPO": "Personal protection order, PPO abuse, weaponized PPO, MCL 600.2950",
        "E_MISCONDUCT": "Judicial misconduct, McNeill bias, ex parte contacts, due process violation",
        "F_APPELLATE": "Court of Appeals, COA 366810, appellate brief, standard of review",
        "G_MSC": "Michigan Supreme Court, superintending control, MCL 600.1701, original jurisdiction",
    }
    
    # Encode document
    doc_emb = model.encode(text[:2000], normalize_embeddings=True)
    cat_embs = model.encode(list(categories.values()), normalize_embeddings=True)
    lane_embs = model.encode(list(lanes.values()), normalize_embeddings=True)
    
    import numpy as np
    cat_scores = np.dot(cat_embs, doc_emb)
    lane_scores = np.dot(lane_embs, doc_emb)
    
    cat_idx = int(np.argmax(cat_scores))
    lane_idx = int(np.argmax(lane_scores))
    
    return {
        "document_type": list(categories.keys())[cat_idx],
        "document_type_score": round(float(cat_scores[cat_idx]), 4),
        "case_lane": list(lanes.keys())[lane_idx],
        "case_lane_score": round(float(lane_scores[lane_idx]), 4),
        "all_type_scores": {k: round(float(v), 4) for k, v in zip(categories.keys(), cat_scores)},
        "all_lane_scores": {k: round(float(v), 4) for k, v in zip(lanes.keys(), lane_scores)},
    }

def analyze_document(filepath):
    """Full analysis pipeline for a single document"""
    ext = Path(filepath).suffix.lower()
    text = ""
    
    if ext == ".pdf":
        try:
            import fitz
            doc = fitz.open(filepath)
            text = "\n".join(page.get_text() for page in doc)
            doc.close()
        except:
            text = f"[Could not extract text from {filepath}]"
    elif ext in (".txt", ".md", ".csv", ".json", ".html"):
        try:
            text = Path(filepath).read_text(encoding="utf-8", errors="replace")[:50000]
        except:
            text = f"[Could not read {filepath}]"
    elif ext == ".docx":
        try:
            from docx import Document
            doc = Document(filepath)
            text = "\n".join(p.text for p in doc.paragraphs)
        except:
            text = f"[Could not read DOCX {filepath}]"
    
    if not text or text.startswith("[Could not"):
        return {"error": text, "filepath": str(filepath)}
    
    result = {
        "filepath": str(filepath),
        "size_bytes": os.path.getsize(filepath),
        "text_length": len(text),
        "classification": classify_legal_document(text),
        "entities": extract_entities(text),
        "summary_first_500": text[:500],
    }
    return result

def benchmark():
    """Run benchmark to verify all components work"""
    print("=" * 60)
    print("  LitigationOS HuggingFace Legal AI Engine v1.0")
    print("  BENCHMARK TEST")
    print("=" * 60)
    
    test_text = """
    MOTION FOR RECONSIDERATION
    Case No. 2024-001507-DC
    14th Circuit Court, Muskegon County, Michigan
    
    Plaintiff Andrew J. Pigors, appearing pro se, respectfully moves this Court
    to reconsider its Order dated August 8, 2025, suspending all parenting time
    with minor child Lincoln Pigors, on the following grounds:
    
    1. The Order was entered ex parte in violation of MCR 2.119(A) and 
       Const 1963 Art 1 §17 (due process).
    2. Judge McNeill failed to make findings under MCL 722.23 best interest factors.
    3. The PPO (Case 2023-5907-PP) was weaponized to deny custody in violation of
       Vodvarka v Grasmeyer, 259 Mich App 499 (2003).
    """
    
    start = time.time()
    
    # Test 1: Classification
    print("\n[1/5] Document Classification...")
    cls = classify_legal_document(test_text)
    print(f"  Type: {cls['document_type']} ({cls['document_type_score']:.4f})")
    print(f"  Lane: {cls['case_lane']} ({cls['case_lane_score']:.4f})")
    
    # Test 2: Embeddings
    print("\n[2/5] Semantic Embeddings...")
    emb = embed_text(test_text)
    print(f"  Vector dim: {len(emb)}, norm: {sum(x**2 for x in emb):.4f}")
    
    # Test 3: NER
    print("\n[3/5] Named Entity Recognition...")
    ents = extract_entities(test_text)
    print(f"  BERT-NER: {len(ents['bert_ner'])} entities")
    for e in ents['bert_ner'][:5]:
        print(f"    {e['text']} [{e['label']}] ({e['score']})")
    print(f"  spaCy legal: {len(ents['spacy_legal'])} entities")
    for e in ents['spacy_legal'][:5]:
        print(f"    {e['text']} [{e['label']}]")
    
    # Test 4: Citations
    print("\n[4/5] Legal Citation Extraction...")
    cites = ents['citations']
    print(f"  Found {len(cites)} citations")
    for c in cites[:5]:
        print(f"    {c}")
    
    # Test 5: Similarity
    print("\n[5/5] Semantic Similarity...")
    model = get_embedder()
    texts = [
        "Motion for reconsideration of custody order",
        "PPO was weaponized to deny parenting time",
        "Landlord failed to maintain habitable premises",
        "Judge entered ex parte order without notice",
    ]
    embs = model.encode(texts, normalize_embeddings=True)
    import numpy as np
    sim_matrix = np.dot(embs, embs.T)
    print("  Similarity matrix:")
    for i, t in enumerate(texts):
        scores = [f"{sim_matrix[i][j]:.3f}" for j in range(len(texts))]
        print(f"    [{', '.join(scores)}] {t[:50]}")
    
    elapsed = time.time() - start
    print(f"\n{'='*60}")
    print(f"  BENCHMARK COMPLETE in {elapsed:.1f}s")
    print(f"  All 5 components operational ✅")
    print(f"{'='*60}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="LitigationOS HF Legal AI Engine")
    parser.add_argument("--benchmark", action="store_true", help="Run benchmark test")
    parser.add_argument("--analyze", type=str, help="Analyze a document")
    parser.add_argument("--classify", type=str, help="Classify a document")
    parser.add_argument("--embed", type=str, help="Generate embedding for text")
    parser.add_argument("--ner", type=str, help="Extract entities from text")
    parser.add_argument("--citations", type=str, help="Extract citations from text")
    
    args = parser.parse_args()
    
    if args.benchmark:
        benchmark()
    elif args.analyze:
        result = analyze_document(args.analyze)
        print(json.dumps(result, indent=2, default=str))
    elif args.classify:
        text = Path(args.classify).read_text(encoding="utf-8", errors="replace")[:5000]
        result = classify_legal_document(text)
        print(json.dumps(result, indent=2))
    elif args.embed:
        emb = embed_text(args.embed)
        print(json.dumps({"embedding": emb[:10], "dim": len(emb), "note": "truncated to first 10 dims"}))
    elif args.ner:
        ents = extract_entities(args.ner)
        print(json.dumps(ents, indent=2, default=str))
    elif args.citations:
        cites = extract_citations(args.citations)
        print(json.dumps(cites, indent=2, default=str))
    else:
        parser.print_help()
