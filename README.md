# Legal RAG Agent

A small legal retrieval-augmented generation prototype for answering questions over a legal PDF with citation-backed evidence. The current indexed document is an ICC Arbitration Rules PDF, stored locally as `data/legal.pdf`.

The project demonstrates the core shape of a legal AI system: ingest a source document, preserve citation metadata, retrieve relevant excerpts, generate grounded answers, and refuse when the indexed evidence is not strong enough.

## What It Does

- Parses a legal PDF page by page.
- Splits extracted text into overlapping chunks.
- Preserves source, page, and chunk metadata for citations.
- Embeds chunks with OpenAI embeddings.
- Stores and queries vectors in ChromaDB.
- Uses a LangGraph agent loop to retrieve, grade evidence, optionally rewrite weak queries, generate answers, or refuse unsupported questions.
- Exposes a FastAPI `/query` endpoint that returns an answer and citations.
- Includes a lightweight FastAPI-served frontend for demoing queries, citations, the indexed PDF, and the agent flow.

## Architecture

```text
PDF
 ↓
PDF parser
 ↓
Chunker + metadata
 ↓
OpenAI embeddings
 ↓
ChromaDB
 ↓
LangGraph agent
   ├─ retrieve
   ├─ grade evidence
   ├─ rewrite query if weak
   ├─ generate answer
   └─ refuse if unsupported
 ↓
FastAPI response with citations
```

## Tech Stack

- Python 3.13
- FastAPI
- LangGraph
- OpenAI API
- ChromaDB
- pypdf
- Pydantic / pydantic-settings
- uv

## Project Structure

```text
app/
  agent.py       LangGraph retrieve-grade-rewrite-generate/refuse loop
  config.py      Environment-based settings
  generation.py  Direct grounded answer generation helper
  indexing.py    ChromaDB collection setup and PDF indexing
  ingestion.py   PDF parsing and chunking
  main.py        FastAPI app
  retrieval.py   Semantic search over ChromaDB
  schemas.py     Pydantic request, response, and chunk models
data/
  legal.pdf      Source legal document
frontend/
  app/           Next.js RAG workbench UI
storage/chroma/  Local persistent vector database
```

## How To Run

Install dependencies:

```bash
uv sync
```

Create a `.env` file:

```bash
OPENAI_API_KEY=your_openai_api_key
```

Index the PDF:

```bash
uv run python -m app.indexing
```

Start the API:

```bash
uv run uvicorn app.main:app --reload
```

Run the Next.js frontend:

```bash
cd frontend
npm install
npm run dev
```

Open the Next.js frontend:

```text
http://127.0.0.1:3000
```

Health check:

```bash
curl http://127.0.0.1:8000/health
```

Ask a question:

```bash
curl -X POST http://127.0.0.1:8000/query \
  -H "Content-Type: application/json" \
  -d '{"question":"Can someone get urgent protection before the tribunal exists?"}'
```

Unsupported questions should refuse instead of hallucinating:

```bash
curl -X POST http://127.0.0.1:8000/query \
  -H "Content-Type: application/json" \
  -d '{"question":"What does this document say about Indian tax law?"}'
```

Expected answer:

```text
The indexed document does not contain sufficiently relevant information to answer this question with reliable citations.
```

Expected citations:

```json
[]
```

## Known Limitations

- The system indexes one local PDF, not a full legal corpus.
- Chunking is word-count based and does not yet understand legal section boundaries.
- Evidence grading uses a compact LLM judgment rather than a formal legal entailment model.
- There is no authentication, rate limiting, or production deployment hardening.
- ChromaDB uses local persistent storage in this prototype.
- Citations point to page-level metadata, not exact paragraph or clause spans.

## Next Improvements

- Add multi-document ingestion with corpus-level filtering.
- Improve chunking around legal headings, articles, and numbered clauses.
- Add automated tests for retrieval, refusal behavior, and API responses.
- Add reranking before answer generation.
- Return richer citation spans with exact quoted evidence.
- Add evaluation questions for supported, partially supported, and unsupported prompts.
- Add authentication and deployment configuration for a hosted demo.

