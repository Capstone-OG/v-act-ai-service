"""
ingestion.py — Document Ingestion Pipeline
============================================
Handles loading, chunking, and storing documents into the pgvector database.

Supported document types:
- PDF  (via ``PyPDFLoader``)
- DOCX (via ``Docx2txtLoader``)
- Text (plain string input)
"""

from __future__ import annotations

import logging
import os
from typing import Literal

from langchain_community.document_loaders import Docx2txtLoader, PyPDFLoader
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from config import CHUNK_OVERLAP, CHUNK_SIZE, get_vector_store

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Text Splitter (module-level, reusable)
# ---------------------------------------------------------------------------
_text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=CHUNK_SIZE,
    chunk_overlap=CHUNK_OVERLAP,
    length_function=len,
    is_separator_regex=False,
)


# ---------------------------------------------------------------------------
# Document Loaders
# ---------------------------------------------------------------------------


def _load_pdf(file_path: str) -> list[Document]:
    """Load pages from a PDF file.

    Parameters
    ----------
    file_path : str
        Absolute or relative path to a ``.pdf`` file.

    Returns
    -------
    list[Document]
        One ``Document`` per page with ``page_content`` and ``metadata``.

    Raises
    ------
    FileNotFoundError
        If *file_path* does not exist.
    ValueError
        If the file cannot be parsed as PDF.
    """
    if not os.path.isfile(file_path):
        raise FileNotFoundError(f"PDF file not found: {file_path}")
    try:
        loader = PyPDFLoader(file_path)
        documents = loader.load()
        logger.info("Loaded %d page(s) from PDF: %s", len(documents), file_path)
        return documents
    except Exception as exc:
        raise ValueError(f"Failed to parse PDF '{file_path}': {exc}") from exc


def _load_docx(file_path: str) -> list[Document]:
    """Load content from a DOCX file.

    Parameters
    ----------
    file_path : str
        Absolute or relative path to a ``.docx`` file.

    Returns
    -------
    list[Document]
        A list containing one ``Document`` with the full text content.

    Raises
    ------
    FileNotFoundError
        If *file_path* does not exist.
    ValueError
        If the file cannot be parsed as DOCX.
    """
    if not os.path.isfile(file_path):
        raise FileNotFoundError(f"DOCX file not found: {file_path}")
    try:
        loader = Docx2txtLoader(file_path)
        documents = loader.load()
        logger.info("Loaded DOCX document: %s", file_path)
        return documents
    except Exception as exc:
        raise ValueError(f"Failed to parse DOCX '{file_path}': {exc}") from exc


def _load_text(content: str) -> list[Document]:
    """Wrap a plain-text string into a LangChain Document.

    Parameters
    ----------
    content : str
        Raw text content to ingest.

    Returns
    -------
    list[Document]
        A single-element list containing the text as a ``Document``.

    Raises
    ------
    ValueError
        If *content* is empty or whitespace-only.
    """
    if not content or not content.strip():
        raise ValueError("Text content is empty.")
    doc = Document(
        page_content=content.strip(),
        metadata={"source": "user_input", "type": "text"},
    )
    logger.info("Created Document from text input (%d chars)", len(doc.page_content))
    return [doc]


# ---------------------------------------------------------------------------
# Loader Dispatch
# ---------------------------------------------------------------------------
_LOADERS = {
    "pdf": _load_pdf,
    "docx": _load_docx,
    "text": _load_text,
}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def ingest_document(
    source: str,
    doc_type: Literal["pdf", "docx", "text"],
) -> int:
    """Ingest a document into the pgvector database.

    End-to-end pipeline: **load → chunk → embed → store**.

    Parameters
    ----------
    source : str
        - For ``pdf`` / ``docx``: path to the file on disk.
        - For ``text``: the raw text content itself.
    doc_type : {"pdf", "docx", "text"}
        The type of document being ingested.

    Returns
    -------
    int
        Number of chunks successfully stored in the vector database.

    Raises
    ------
    ValueError
        If *doc_type* is not one of the supported types, or if the
        document cannot be parsed.
    FileNotFoundError
        If a file path is given but the file does not exist.
    ConnectionError
        If the database is unreachable.

    Examples
    --------
    >>> ingest_document("report.pdf", "pdf")
    42
    >>> ingest_document("Hello, this is a test.", "text")
    1
    """
    # 1. Validate doc_type
    doc_type_lower = doc_type.lower().strip()
    if doc_type_lower not in _LOADERS:
        raise ValueError(
            f"Unsupported document type: '{doc_type}'. "
            f"Must be one of: {list(_LOADERS.keys())}"
        )

    # 2. Load raw documents
    logger.info("Loading document (type=%s) ...", doc_type_lower)
    loader_fn = _LOADERS[doc_type_lower]
    raw_documents = loader_fn(source)

    if not raw_documents:
        logger.warning("No content extracted from source.")
        return 0

    # 3. Split into chunks
    logger.info("Splitting into chunks (size=%d, overlap=%d) ...", CHUNK_SIZE, CHUNK_OVERLAP)
    chunks = _text_splitter.split_documents(raw_documents)
    logger.info("Produced %d chunk(s)", len(chunks))

    if not chunks:
        logger.warning("Text splitter produced 0 chunks — nothing to store.")
        return 0

    # 4. Store in pgvector
    logger.info("Storing %d chunk(s) in pgvector ...", len(chunks))
    try:
        vector_store = get_vector_store()
        vector_store.add_documents(chunks)
        logger.info("Successfully stored %d chunk(s).", len(chunks))
    except Exception as exc:
        raise ConnectionError(
            f"Failed to store documents in pgvector: {exc}"
        ) from exc

    return len(chunks)

