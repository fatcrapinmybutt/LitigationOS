# High-signal Hugging Face tooling map (from in-chat tool search)

## Document intelligence / PDF→MD (Docling family)

- `docling-project/docling-models` (downloads: 670.0K) — https://hf.co/docling-project/docling-models
- `docling-project/docling-layout-heron` (downloads: 572.9K) — https://hf.co/docling-project/docling-layout-heron
- `ibm-granite/granite-docling-258M` (downloads: 195.6K) — https://hf.co/ibm-granite/granite-docling-258M
- `docling-project/SmolDocling-256M-preview` (downloads: 45.0K) — https://hf.co/docling-project/SmolDocling-256M-preview
- `docling-project/DocumentFigureClassifier` (downloads: 38.8K) — https://hf.co/docling-project/DocumentFigureClassifier

## Spaces worth stealing ideas from (PDF→MD / OCR demos)

- `opendatalab/MinerU` (likes: 541) — https://hf.co/spaces/opendatalab/MinerU
- `docling-project/SmolDocling-256M-Demo` (likes: 258) — https://hf.co/spaces/docling-project/SmolDocling-256M-Demo
- `PaddlePaddle/PaddleOCR-VL_Online_Demo` (likes: 232) — https://hf.co/spaces/PaddlePaddle/PaddleOCR-VL_Online_Demo
- `merterbak/DeepSeek-OCR-Demo` (likes: 412) — https://hf.co/spaces/merterbak/DeepSeek-OCR-Demo

## Datasets (legal NLP / retrieval / eval)

- `pile-of-law/pile-of-law` (downloads: 2.6K; license: cc-by-nc-sa-4.0) — https://hf.co/datasets/pile-of-law/pile-of-law
- `coastalcph/lex_glue` (downloads: 7.3K; license: cc-by-4.0) — https://hf.co/datasets/coastalcph/lex_glue
- `hoorangyee/pile-of-law-chunked` (downloads: 40; license: mit) — https://hf.co/datasets/hoorangyee/pile-of-law-chunked

## How these plug into LitigationOS

- Docling is a strong **layout-first** PDF→structured-text layer feeding your Markdown shard store.
- MinerU is a useful reference design for PDF→Markdown+JSON conversion; replicate locally with open-source components.
- LexGLUE is a legal NLU benchmark; useful for scoring issue/topic routing offline.
- Pile-of-Law is broad US legal language; MI-specific authority ingestion remains mandatory for filing-grade work.