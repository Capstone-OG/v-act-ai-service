"""
main.py — Interactive CLI for Conversational RAG
==================================================
Provides a terminal-based interface to:

- Ingest documents (PDF, DOCX, plain text) into pgvector.
- Chat with the AI using multi-turn conversation memory.
- Switch between sessions and manage history.

Commands
--------
/ingest <type> <source>   — Ingest a document (type: pdf | docx | text).
/session <id>             — Switch to a different session.
/sessions                 — List all active sessions.
/clear                    — Clear current session history.
/help                     — Show available commands.
/quit                     — Exit the program.
"""

from __future__ import annotations

import logging

from ingestion import ingest_document
from rag_engine import ask, clear_session, get_session_ids

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
BANNER = r"""
╔══════════════════════════════════════════════════╗
║       🤖  Conversational RAG System  🤖         ║
║  Powered by Gemini + LangChain + PgVector       ║
╚══════════════════════════════════════════════════╝
"""

HELP_TEXT = """
Available commands:
  /ingest <type> <source>  — Ingest a document into the knowledge base.
                             type: pdf | docx | text
                             source: file path (pdf/docx) or quoted text.
  /session <id>            — Switch to a named session.
  /sessions                — List active sessions.
  /clear                   — Clear current session's chat history.
  /help                    — Show this help message.
  /quit                    — Exit the program.

Anything else is treated as a question to the AI.
"""


# ---------------------------------------------------------------------------
# CLI Handlers
# ---------------------------------------------------------------------------


def _handle_ingest(args: str) -> None:
    """Parse and execute an /ingest command.

    Expected format: ``/ingest <type> <source>``
    """
    parts = args.strip().split(maxsplit=1)
    if len(parts) < 2:
        print("⚠️  Usage: /ingest <pdf|docx|text> <file_path_or_text>")
        return

    doc_type, source = parts[0], parts[1]

    if doc_type not in ("pdf", "docx", "text"):
        print(f"⚠️  Unknown type '{doc_type}'. Use: pdf, docx, or text.")
        return

    print(f"📥 Ingesting ({doc_type}): {source[:80]}{'...' if len(source) > 80 else ''}")
    try:
        count = ingest_document(source, doc_type)  # type: ignore[arg-type]
        print(f"✅ Successfully ingested {count} chunk(s) into the knowledge base.")
    except FileNotFoundError as exc:
        print(f"❌ File not found: {exc}")
    except ValueError as exc:
        print(f"❌ Invalid input: {exc}")
    except ConnectionError as exc:
        print(f"❌ Database error: {exc}")


def _handle_ask(question: str, session_id: str) -> None:
    """Send a question to the RAG chain and display the answer."""
    try:
        result = ask(question, session_id=session_id)
        answer = result.get("answer", "No answer generated.")
        context_docs = result.get("context", [])

        print(f"\n🤖 AI: {answer}")

        if context_docs:
            print(f"\n📚 Sources ({len(context_docs)} document(s) retrieved):")
            for i, doc in enumerate(context_docs, 1):
                source = doc.metadata.get("source", "unknown")
                page = doc.metadata.get("page", "")
                page_info = f" (page {page})" if page != "" else ""
                snippet = doc.page_content[:120].replace("\n", " ")
                print(f"   [{i}] {source}{page_info}: {snippet}...")
    except RuntimeError as exc:
        print(f"❌ Error: {exc}")


# ---------------------------------------------------------------------------
# Main Loop
# ---------------------------------------------------------------------------


def main() -> None:
    """Run the interactive CLI loop."""
    logging.basicConfig(
        level=logging.WARNING,
        format="%(levelname)s | %(name)s | %(message)s",
    )

    print(BANNER)
    print("Type /help for available commands, or just ask a question.\n")

    current_session = "default"
    print(f"📌 Current session: {current_session}\n")

    while True:
        try:
            user_input = input(f"[{current_session}] You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n👋 Goodbye!")
            break

        if not user_input:
            continue

        # --- Command dispatch ---
        if user_input.lower() in ("/quit", "/exit", "/q"):
            print("👋 Goodbye!")
            break

        elif user_input.lower() == "/help":
            print(HELP_TEXT)

        elif user_input.lower().startswith("/ingest"):
            _handle_ingest(user_input[len("/ingest"):])

        elif user_input.lower().startswith("/session"):
            new_id = user_input[len("/session"):].strip()
            if new_id:
                current_session = new_id
                print(f"📌 Switched to session: {current_session}")
            else:
                print(f"📌 Current session: {current_session}")

        elif user_input.lower() == "/sessions":
            sessions = get_session_ids()
            if sessions:
                print("📋 Active sessions: " + ", ".join(sessions))
            else:
                print("📋 No active sessions yet.")

        elif user_input.lower() == "/clear":
            clear_session(current_session)
            print(f"🗑️  Cleared history for session '{current_session}'.")

        elif user_input.startswith("/"):
            print(f"⚠️  Unknown command: {user_input.split()[0]}. Type /help.")

        else:
            # Regular question → send to RAG
            _handle_ask(user_input, current_session)

        print()  # blank line between turns


if __name__ == "__main__":
    main()
