# PDF Knowledge Base — 8 Tools

## litigation_scan_drives
Scan local drives for PDF files.
- `drives` (list[str], optional): Drive letters. Default: ["C", "D", "H"]
- `max_results` (int, optional): Max files. Default: 100
- Returns: PDF file paths with sizes

## litigation_ingest_pdf
Extract text from a single PDF and store in knowledge base.
- `file_path` (str, required): Absolute path to PDF
- `tags` (str, optional): Comma-separated tags
- Returns: Document ID, page count, extraction stats

## litigation_bulk_ingest
Batch ingest all PDFs from a directory.
- `directory` (str, required): Directory path
- `recursive` (bool, optional): Scan subdirs. Default: true
- `max_files` (int, optional): Max to process. Default: 50
- Returns: Ingestion summary, failures, total pages

## litigation_search
FTS5 full-text search across all ingested PDF text.
- `query` (str, required): FTS5 query (AND/OR/NOT, "phrases", prefix*)
- `limit` (int, optional): Max results. Default: 20
- Returns: Page excerpts with doc name, page number, relevance

**Examples:**
```
litigation_search(query="ex parte AND custody", limit=10)
litigation_search(query='"parenting time" OR "visitation"')
litigation_search(query="MCR 3.206*")
```

## litigation_list_documents
List all indexed documents.
- `limit` (int, optional): Max results. Default: 50
- `offset` (int, optional): Pagination. Default: 0
- Returns: Document ID, filename, path, pages, date, tags

## litigation_get_document
Get full text content by document ID.
- `document_id` (int, required): Document ID
- Returns: Full text, metadata, page-by-page breakdown

## litigation_delete_document
Remove a document from the index.
- `document_id` (int, required): Document ID
- Returns: Confirmation

## litigation_get_stats
Knowledge base statistics.
- Returns: Documents, pages, graph nodes, rules, risk events, FTS size, DB size
