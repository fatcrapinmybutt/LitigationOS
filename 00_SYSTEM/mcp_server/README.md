# Litigation Context MCP Server

A local MCP server that permanently stores and indexes litigation context extracted from PDF files on your local drives.

## Features
- Scans local drives for PDF files
- Extracts text page-by-page using PyMuPDF
- Stores in persistent SQLite database with FTS5 full-text search
- Provides search, retrieval, and management tools via MCP protocol

## Installation

```bash
cd litigation_context_mcp
pip install -e .
```

## Usage

### stdio (Claude Desktop / VS Code / Gemini CLI)
```bash
python -m litigation_context_mcp.server
```

### Claude Desktop config (`claude_desktop_config.json`)
```json
{
  "mcpServers": {
    "litigation_context": {
      "command": "python",
      "args": ["-m", "litigation_context_mcp.server"],
      "cwd": "C:\\Users\\andre\\litigation_context_mcp"
    }
  }
}
```

## Tools
| Tool | Description |
|------|-------------|
| `litigation_scan_drives` | Scan drives/folders for PDF files |
| `litigation_ingest_pdf` | Extract + store text from one PDF |
| `litigation_bulk_ingest` | Ingest all unprocessed PDFs from a path |
| `litigation_search` | Full-text search across all ingested content |
| `litigation_list_documents` | List indexed documents with pagination |
| `litigation_get_document` | Retrieve full text of a specific document |
| `litigation_get_stats` | Knowledge base statistics |
| `litigation_delete_document` | Remove a document from the index |
