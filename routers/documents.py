"""
routers/documents.py — Document Ingestion & Management Endpoints
==================================================================
Provides endpoints to upload files (PDF, DOCX) and ingest plain text
into the pgvector database.
"""

from __future__ import annotations

import logging
import os
import shutil
import tempfile
from pathlib import Path

import psycopg
from fastapi import APIRouter, File, HTTPException, UploadFile, status

from config import COLLECTION_NAME, DATABASE_URL, EMBEDDING_DIMENSIONS
from ingestion import ingest_document
from schemas import DocStatsResponse, IngestResponse, TextIngestRequest

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/documents", tags=["Document Management"])

# Allowed upload file extensions
ALLOWED_EXTENSIONS = {
    ".pdf": "pdf",
    ".docx": "docx",
}


@router.post(
    "/upload",
    response_model=IngestResponse,
    summary="Upload and ingest a document file (PDF or DOCX)",
    description=(
        "Upload a PDF or DOCX file to be parsed, chunked, and embedded into the "
        "pgvector database. The file is temporarily processed and removed immediately after."
    ),
)
async def upload_document_endpoint(
    file: UploadFile = File(..., description="PDF or DOCX file to upload")
) -> IngestResponse:
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file must have a filename.",
        )

    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        allowed = ", ".join(ALLOWED_EXTENSIONS.keys())
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file format '{file_ext}'. Allowed formats: {allowed}",
        )

    doc_type = ALLOWED_EXTENSIONS[file_ext]

    # Save to a temporary file
    temp_dir = tempfile.mkdtemp(prefix="rag_upload_")
    temp_file_path = os.path.join(temp_dir, file.filename)

    try:
        with open(temp_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        chunks_count = ingest_document(source=temp_file_path, doc_type=doc_type)  # type: ignore[arg-type]

        return IngestResponse(
            message=f"Successfully ingested file '{file.filename}'.",
            doc_type=doc_type,
            source=file.filename,
            chunks_ingested=chunks_count,
        )
    except Exception as exc:
        logger.error("Failed to ingest uploaded file '%s': %s", file.filename, exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process file: {exc}",
        ) from exc
    finally:
        # Clean up temporary directory and file
        shutil.rmtree(temp_dir, ignore_errors=True)


@router.post(
    "/text",
    response_model=IngestResponse,
    summary="Ingest raw text content",
    description="Ingest a plain-text snippet directly into the pgvector database.",
)
def ingest_text_endpoint(payload: TextIngestRequest) -> IngestResponse:
    try:
        chunks_count = ingest_document(source=payload.content, doc_type="text")
        return IngestResponse(
            message="Successfully ingested text content.",
            doc_type="text",
            source="user_text",
            chunks_ingested=chunks_count,
        )
    except Exception as exc:
        logger.error("Failed to ingest text: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to ingest text: {exc}",
        ) from exc


@router.get(
    "/stats",
    response_model=DocStatsResponse,
    summary="Get document and vector store statistics",
)
def get_document_stats_endpoint() -> DocStatsResponse:
    conn_str = DATABASE_URL.replace("postgresql+psycopg://", "postgresql://")
    try:
        with psycopg.connect(conn_str) as conn:
            with conn.cursor() as cur:
                cur.execute(f"SELECT count(*) FROM {COLLECTION_NAME};")
                count = cur.fetchone()[0]
                return DocStatsResponse(
                    total_documents=count,
                    table_name=COLLECTION_NAME,
                    embedding_dimensions=EMBEDDING_DIMENSIONS,
                )
    except Exception as exc:
        logger.error("Failed to query stats: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch database statistics: {exc}",
        ) from exc
