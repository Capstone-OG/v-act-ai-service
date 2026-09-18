# Conversational RAG System

A production-ready Conversational Retrieval-Augmented Generation system powered by **Google Gemini**, **LangChain (LCEL)**, and **PostgreSQL + pgvector**.

## Architecture

```
User Question + Chat History
        │
        ▼
┌───────────────────────────┐
│  History-Aware Retriever  │  → reformulates question → vector search
└─────────────┬─────────────┘
              │  retrieved docs
              ▼
┌───────────────────────────┐
│  Stuff Documents QA Chain │  → context + history → Gemini LLM
└─────────────┬─────────────┘
              │
              ▼
┌───────────────────────────┐
│ RunnableWithMessageHistory│  → auto-saves turns per session_id
└───────────────────────────┘
```

## Quick Start

### 1. Start PostgreSQL + pgvector (Docker)

```bash
docker run -d \
  --name pgvector-rag \
  -e POSTGRES_USER=rag_user \
  -e POSTGRES_PASSWORD=rag_password \
  -e POSTGRES_DB=rag_db \
  -p 5433:5432 \
  pgvector/pgvector:pg16

# Wait a few seconds, then enable the extension:
docker exec -it pgvector-rag psql -U rag_user -d rag_db -c "CREATE EXTENSION IF NOT EXISTS vector;"
```

### 2. Install Dependencies

```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate

pip install -r requirements.txt
```

### 3. Configure Environment

```bash
cp .env.example .env
# Edit .env with your actual GOOGLE_API_KEY
```

### 4. Run Server

```bash
# Run FastAPI server (default: port 8000)
python main.py
# Or on Windows:
run.bat
```

- **Swagger UI Interactive Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc Docs**: [http://localhost:8000/redoc](http://localhost:8000/redoc)

---

## REST API Endpoints

### 1. Conversational Chat
- **`POST /api/v1/chat`**: Ask a question with conversational memory.
  ```json
  {
    "question": "V-Act cung cấp dịch vụ gì?",
    "session_id": "user-123"
  }
  ```
- **`POST /api/v1/chat/stream`**: Stream answer token-by-token using Server-Sent Events (SSE).
- **`GET /api/v1/chat/sessions`**: List all active session IDs.
- **`DELETE /api/v1/chat/sessions/{session_id}`**: Clear history for a session.

### 2. Document Ingestion & Versioning Management
- **`POST /api/v1/documents/upload`**: Upload PDF or DOCX file with SHA-256 duplicate checking & background Graceful Swap.
- **`POST /api/v1/documents/text`**: Ingest plain text content with `title` grouping and SHA-256 hash comparison.
- **`GET /api/v1/documents`**: List all logical documents with their currently active version and total version count.
- **`GET /api/v1/documents/{document_group_id}/versions`**: View full version history for a logical document.
- **`POST /api/v1/documents/{document_group_id}/rollback`**: Rollback to an earlier version without recalculating embeddings:
  ```json
  { "version": 1 }
  ```
- **`DELETE /api/v1/documents/{document_group_id}`**: Soft delete (de-activate all versions from RAG while preserving history).
- **`DELETE /api/v1/documents/{document_group_id}/purge`**: Permanently hard-delete a document and all its vector chunks.
- **`GET /api/v1/documents/stats`**: Get detailed statistics of catalog records and active vector chunks.

### 3. System Health
- **`GET /health`**: Health check, database connection status, and active models.

---

## Project Structure

```
├── .env.example       # Environment variables template
├── requirements.txt   # Dependencies (FastAPI, LangChain, pgvector, etc.)
├── config.py          # Configuration & model factories (Gemini, PGEngine)
├── schemas.py         # Pydantic models for request & response
├── routers/           # FastAPI router modules
│   ├── chat.py        # Conversational Q&A & streaming endpoints
│   └── documents.py   # PDF/DOCX file upload & text ingestion
├── ingestion.py       # Document loading, chunking, and pgvector storage
├── rag_engine.py      # Conversational RAG chain (LCEL) & streaming
├── main.py            # FastAPI application entrypoint & Swagger setup
└── run.bat            # Windows 1-click launcher for FastAPI server
```

