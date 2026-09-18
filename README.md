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

### 2. Document Ingestion
- **`POST /api/v1/documents/upload`**: Upload a PDF or DOCX file (`multipart/form-data`).
- **`POST /api/v1/documents/text`**: Ingest plain text content directly:
  ```json
  {
    "content": "Nội dung tài liệu cần đưa vào hệ thống..."
  }
  ```
- **`GET /api/v1/documents/stats`**: Get document count in pgvector.

### 3. System Health
- **`GET /health`**: Health check, database connection status, and active models.

---

## Interactive CLI (Optional)

If you prefer testing directly in the terminal:
```bash
python cli.py
```

| Command | Description |
|---------|-------------|
| `/ingest pdf <path>` | Ingest a PDF file |
| `/ingest docx <path>` | Ingest a DOCX file |
| `/ingest text <content>` | Ingest plain text |
| `/session <id>` | Switch conversation session |
| `/sessions` | List active sessions |
| `/clear` | Clear current session history |
| `/help` | Show help |
| `/quit` | Exit |

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
├── cli.py             # Optional interactive terminal chat
├── view_db.py         # CLI utility to inspect pgvector stored data
└── run.bat            # Windows 1-click launcher for FastAPI server
```
