"""
Utility script to view Document Catalog and Vector Chunks in PostgreSQL + pgvector.
Run: .venv\\Scripts\\python view_db.py
"""
import asyncio
import os
import sys
from dotenv import load_dotenv

# Fix Windows event loop and encoding if on Windows
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import psycopg
from psycopg.rows import dict_row

load_dotenv()

DB_URL = os.getenv("DATABASE_URL", "postgresql+psycopg://rag_user:rag_password@localhost:5433/rag_db")
CONN_STR = DB_URL.replace("postgresql+psycopg://", "postgresql://")


def main():
    print("=" * 80)
    print("  📚 PGVECTOR DOCUMENT CATALOG & VECTOR CHUNKS VIEWER")
    print("=" * 80)

    try:
        with psycopg.connect(CONN_STR, row_factory=dict_row) as conn:
            with conn.cursor() as cur:
                # -------------------------------------------------------------
                # 1. Document Catalog
                # -------------------------------------------------------------
                print("\n📂 [1] DOCUMENTS CATALOG (Table: 'documents')")
                print("-" * 80)
                cur.execute("""
                    SELECT 
                        id,
                        document_group_id,
                        file_name,
                        version,
                        substring(file_hash from 1 for 12) as short_hash,
                        status,
                        is_current,
                        total_chunks,
                        to_char(created_at, 'YYYY-MM-DD HH24:MI:SS') as created
                    FROM documents
                    ORDER BY document_group_id, version ASC;
                """)
                docs = cur.fetchall()

                if not docs:
                    print("⚠️  No documents found in 'documents' table.")
                else:
                    for d in docs:
                        current_tag = "🟢 ACTIVE (CURRENT)" if d["is_current"] else "⚪ INACTIVE"
                        print(f"• File: {d['file_name']} (v{d['version']}) [{current_tag}]")
                        print(f"  ID: {d['id']} | Group: {d['document_group_id']}")
                        print(f"  Status: {d['status']} | Chunks: {d['total_chunks']} | Hash: {d['short_hash']}... | Created: {d['created']}")
                        print()

                # -------------------------------------------------------------
                # 2. Vector Chunks
                # -------------------------------------------------------------
                print("\n🧩 [2] VECTOR CHUNKS (Table: 'document_chunks')")
                print("-" * 80)
                cur.execute("""
                    SELECT 
                        langchain_id,
                        content,
                        langchain_metadata->>'file_name' as file_name,
                        langchain_metadata->>'version' as version,
                        langchain_metadata->>'is_current' as is_current,
                        langchain_metadata->>'chunk_index' as chunk_index,
                        vector_dims(embedding) as dim
                    FROM document_chunks
                    ORDER BY langchain_metadata->>'file_name', (langchain_metadata->>'version')::int, (langchain_metadata->>'chunk_index')::int
                    LIMIT 20;
                """)
                chunks = cur.fetchall()

                cur.execute("SELECT count(*) as total FROM document_chunks;")
                total_chunks = cur.fetchone()["total"]
                print(f"📌 Total chunks in database: {total_chunks}\n")

                if not chunks:
                    print("⚠️  No vector chunks found in 'document_chunks' table.")
                else:
                    for idx, c in enumerate(chunks, 1):
                        is_curr = c["is_current"]
                        tag = "🟢 CURRENT" if str(is_curr).lower() == "true" else "⚪ INACTIVE"
                        content = c["content"].strip().replace("\n", " ")
                        if len(content) > 90:
                            content = content[:87] + "..."
                        
                        print(f"[{idx}] {c['file_name']} (v{c['version']}) [Chunk #{c['chunk_index']}] [{tag}]")
                        print(f"    ID: {c['langchain_id']} | Dims: {c['dim']}")
                        print(f"    Content: {content}")
                        print("-" * 80)

                    if total_chunks > 20:
                        print(f"... and {total_chunks - 20} more chunks.")

    except Exception as e:
        print(f"❌ Error connecting to database: {e}")


if __name__ == "__main__":
    main()
