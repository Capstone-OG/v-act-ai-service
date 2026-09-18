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

### 4. Run

```bash
python main.py
```

## CLI Commands

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

Any other input is treated as a question to the AI.

## Project Structure

```
├── .env.example       # Environment template
├── requirements.txt   # Python dependencies
├── config.py          # Configuration & model initialization
├── ingestion.py       # Document loading, chunking, vector storage
├── rag_engine.py      # Conversational RAG chain (LCEL)
├── main.py            # Interactive CLI
├── view_db.py         # Utility to inspect pgvector stored data
└── run.bat            # One-click launcher for Windows
```

## Standalone Ingestion

```bash
python ingestion.py pdf "path/to/document.pdf"
python ingestion.py text "Your raw text content here"
```
