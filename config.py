"""
config.py — Configuration & Model Initialization
==================================================
Central configuration module for the Conversational RAG system.

Responsibilities:
- Load environment variables (.env) for API keys and DB connection.
- Initialize Google Gemini LLM and Embedding models.
- Provide a PGEngine and PGVectorStore factory for pgvector access.
"""

from __future__ import annotations

import asyncio
import os
import sys
import logging
from functools import lru_cache

# Fix for Windows: psycopg async requires WindowsSelectorEventLoopPolicy
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_postgres import PGEngine, PGVectorStore

# ---------------------------------------------------------------------------
# Environment
# ---------------------------------------------------------------------------
load_dotenv()  # reads .env in project root

logger = logging.getLogger(__name__)

# Required env vars
GOOGLE_API_KEY: str = os.environ.get("GOOGLE_API_KEY", "")
DATABASE_URL: str = os.environ.get("DATABASE_URL", "")

if not GOOGLE_API_KEY:
    raise EnvironmentError(
        "GOOGLE_API_KEY is not set. "
        "Copy .env.example → .env and fill in your Google API key."
    )
if not DATABASE_URL:
    raise EnvironmentError(
        "DATABASE_URL is not set. "
        "Copy .env.example → .env and provide a PostgreSQL+psycopg connection string."
    )

# Server settings
API_HOST: str = os.environ.get("API_HOST", "0.0.0.0")
API_PORT: int = int(os.environ.get("API_PORT", "8000"))

# ---------------------------------------------------------------------------
# Model Constants
# ---------------------------------------------------------------------------
LLM_MODEL: str = "gemini-3.5-flash"
EMBEDDING_MODEL: str = "models/gemini-embedding-001"
EMBEDDING_DIMENSIONS: int = 3072  # gemini-embedding-001 default output size

# ---------------------------------------------------------------------------
# Chunking Constants
# ---------------------------------------------------------------------------
CHUNK_SIZE: int = 1000
CHUNK_OVERLAP: int = 200

# ---------------------------------------------------------------------------
# Vector Store Constants
# ---------------------------------------------------------------------------
COLLECTION_NAME: str = "rag_documents"

# ---------------------------------------------------------------------------
# Model Factories (cached singletons)
# ---------------------------------------------------------------------------


@lru_cache(maxsize=1)
def get_llm() -> ChatGoogleGenerativeAI:
    """Return a cached ChatGoogleGenerativeAI instance.

    Uses ``gemini-3.5-flash`` with temperature=0 for deterministic,
    context-grounded answers.
    """
    logger.info("Initializing LLM: %s", LLM_MODEL)
    return ChatGoogleGenerativeAI(
        model=LLM_MODEL,
        api_key=GOOGLE_API_KEY,
        temperature=0,
    )


@lru_cache(maxsize=1)
def get_embeddings() -> GoogleGenerativeAIEmbeddings:
    """Return a cached GoogleGenerativeAIEmbeddings instance.

    Uses ``models/gemini-embedding-001`` which outputs 3072-dim vectors.
    """
    logger.info("Initializing Embeddings: %s", EMBEDDING_MODEL)
    return GoogleGenerativeAIEmbeddings(
        model=EMBEDDING_MODEL,
        api_key=GOOGLE_API_KEY,
    )


# ---------------------------------------------------------------------------
# Database / Vector Store Factories
# ---------------------------------------------------------------------------


@lru_cache(maxsize=1)
def get_pg_engine() -> PGEngine:
    """Create and cache a PGEngine connection pool from DATABASE_URL.

    Raises
    ------
    ConnectionError
        If the database is unreachable.
    """
    logger.info("Creating PGEngine from DATABASE_URL")
    try:
        engine = PGEngine.from_connection_string(url=DATABASE_URL)
        return engine
    except Exception as exc:
        raise ConnectionError(
            f"Failed to connect to PostgreSQL: {exc}"
        ) from exc


def init_vector_store_table() -> None:
    """Ensure the pgvector table exists.

    This is **not** idempotent — calling it when the table already exists
    will raise a ``ProgrammingError``.  The function catches that and
    logs a debug message so it is safe to call on every startup.
    """
    engine = get_pg_engine()
    try:
        engine.init_vectorstore_table(
            table_name=COLLECTION_NAME,
            vector_size=EMBEDDING_DIMENSIONS,
        )
        logger.info("Created vector store table '%s'", COLLECTION_NAME)
    except Exception as exc:
        # Table already exists — that's fine.
        if "42P07" in str(exc) or "already exists" in str(exc).lower():
            logger.debug("Vector store table '%s' already exists.", COLLECTION_NAME)
        else:
            raise


def get_vector_store() -> PGVectorStore:
    """Return a ready-to-use PGVectorStore instance.

    Ensures the underlying table exists before returning.
    """
    init_vector_store_table()
    engine = get_pg_engine()
    return PGVectorStore.create_sync(
        engine=engine,
        table_name=COLLECTION_NAME,
        embedding_service=get_embeddings(),
    )
