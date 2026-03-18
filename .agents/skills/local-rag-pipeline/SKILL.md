---
name: local-rag-pipeline
description: "Local RAG pipeline using MANBEARPIG + FTS5. Multi-source retrieval, fact-checking, research reports. Zero network. Replaces Tavily+OpenRouter. Triggers: rag, retrieval, research, fact check, grounded, search and answer, knowledge retrieval, citation, pipeline"
---

# Local RAG Pipeline

Build RAG pipelines entirely locally. No Tavily. No Exa. No OpenRouter.

## Patterns

### Pattern 1: Simple Search + Answer
```python
from sdk.rag_pipeline import RAGPipeline
rag = RAGPipeline()
result = rag.search("MCR 2.003 disqualification")
```

### Pattern 2: Multi-Source Research
```python
result = rag.research("judicial misconduct patterns")
# Sources: FTS5 + TF-IDF + authority + concepts + MCR DB
```

### Pattern 3: Document Analysis
```python
result = rag.analyze(open("motion.md").read())
```

### Pattern 4: Fact-Checking
```python
result = rag.fact_check("Judge McNeill held 47 ex parte hearings")
print(result.patterns)  # ['SUPPORTED — strong evidence found']
```

### Pattern 5: Research Report
```python
result = rag.research_report("parental alienation in Michigan")
```

## Architecture

```
Query → [FTS5 Search] ──┐
      → [TF-IDF]        ──┤→ Dedup → Rank → Synthesize
      → [Authority]      ──┤
      → [Concepts]       ──┤
      → [MCR DB]         ──┘
```
