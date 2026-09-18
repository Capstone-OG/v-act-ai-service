"""
Utility script to view documents and vectors stored in pgvector.
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
# Convert to standard libpq connection string
CONN_STR = DB_URL.replace("postgresql+psycopg://", "postgresql://")


def main():
    print("=" * 70)
    print("  📊 PGVECTOR DATA VIEWER")
    print("=" * 70)

    try:
        with psycopg.connect(CONN_STR, row_factory=dict_row) as conn:
            with conn.cursor() as cur:
                # Count total
                cur.execute("SELECT count(*) as total FROM rag_documents;")
                total = cur.fetchone()["total"]
                print(f"📌 Total documents in 'rag_documents': {total}\n")

                if total == 0:
                    print("⚠️  No documents found in database.")
                    return

                # Fetch records
                cur.execute("""
                    SELECT 
                        langchain_id,
                        content,
                        langchain_metadata,
                        vector_dims(embedding) as dim
                    FROM rag_documents
                    ORDER BY langchain_id
                    LIMIT 20;
                """)
                rows = cur.fetchall()

                for idx, row in enumerate(rows, 1):
                    content = row["content"].strip().replace("\n", " ")
                    if len(content) > 100:
                        content = content[:97] + "..."
                    
                    print(f"[{idx}] ID: {row['langchain_id']}")
                    print(f"    Dimensions: {row['dim']} | Metadata: {row['langchain_metadata']}")
                    print(f"    Content   : {content}")
                    print("-" * 70)

                if total > 20:
                    print(f"... and {total - 20} more records.")

    except Exception as e:
        print(f"❌ Error connecting to database: {e}")


if __name__ == "__main__":
    main()
