# Hugging Face Components to Graft (Repo IDs)

## Retrieval Core
- Embeddings: `BAAI/bge-m3`
- Reranker: `BAAI/bge-reranker-v2-m3`

## DocAI / OCR Rails
- Layout understanding: `microsoft/layoutlmv3-base`
- OCR printed: `microsoft/trocr-base-printed`
- OCR handwriting: `microsoft/trocr-base-handwritten`
- OCR-free parsing: `naver-clova-ix/donut-base`
- Lightweight doc-image parsing: `docling-project/SmolDocling-256M-preview`
- PDF/image-to-text: `facebook/nougat-base`

## LitigationOS graft points
1) Scan-aware intake -> choose TEXT vs OCR vs OCR-free.
2) Retrieval -> embed (recall) + rerank (precision).
3) Quote-Lock promotion -> build candidate queue for pinpointing + exhibits.
