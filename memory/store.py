from __future__ import annotations

from datetime import datetime, timezone
import logging
import os
from threading import Lock
from uuid import uuid4

import faiss
from langchain_community.docstore.in_memory import InMemoryDocstore
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document

from models.embeddings import embedding

logger = logging.getLogger("badmintonnet.memory")
MEMORY_STORE_PATH = os.getenv("SESSION_MEMORY_STORE_PATH", "session_memory_store")
MEMORY_RETRIEVE_K = int(os.getenv("SESSION_MEMORY_RETRIEVE_K", "4"))
_store_lock = Lock()


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _build_empty_vectorstore() -> FAISS:
    dimension = len(embedding.embed_query("session-memory-probe"))
    index = faiss.IndexFlatL2(dimension)
    return FAISS(
        embedding_function=embedding,
        index=index,
        docstore=InMemoryDocstore({}),
        index_to_docstore_id={},
    )


def _load_vectorstore() -> FAISS:
    if os.path.isdir(MEMORY_STORE_PATH):
        return FAISS.load_local(
            MEMORY_STORE_PATH,
            embedding,
            allow_dangerous_deserialization=True,
        )
    return _build_empty_vectorstore()


def get_session_memory_context(
    session_id: str,
    query: str,
    k: int = MEMORY_RETRIEVE_K,
) -> str:
    """Return relevant memory snippets for one chat session."""
    if not session_id.strip():
        logger.info("[MEMORY][SKIP_RETRIEVE] empty session_id")
        return ""

    with _store_lock:
        vectorstore = _load_vectorstore()
        docs = vectorstore.similarity_search(
            query,
            k=max(1, k),
            filter={"session_id": session_id},
        )

    logger.info(
        "[MEMORY][RETRIEVE] session_id=%s query=%s hits=%s",
        session_id,
        query[:120].replace("\n", " "),
        len(docs),
    )

    if not docs:
        return ""

    snippets: list[str] = []
    seen_contents: set[str] = set()
    for doc in docs:
        content = doc.page_content.strip()
        if not content or content in seen_contents:
            continue
        seen_contents.add(content)
        snippets.append(content)

    return "\n\n---\n\n".join(snippets)


def save_session_turn(session_id: str, question: str, answer: str) -> None:
    """Persist one user/assistant exchange as semantic memory."""
    if not session_id.strip():
        logger.info("[MEMORY][SKIP_SAVE] empty session_id")
        return

    content = (
        f"User: {question.strip()}\n"
        f"Assistant: {answer.strip()}"
    ).strip()
    if not content:
        return

    document = Document(
        page_content=content,
        metadata={
            "session_id": session_id,
            "type": "chat_turn",
            "created_at": _utc_now_iso(),
        },
    )

    with _store_lock:
        vectorstore = _load_vectorstore()
        doc_id = str(uuid4())
        vectorstore.add_documents([document], ids=[doc_id])
        vectorstore.save_local(MEMORY_STORE_PATH)
        total_docs = len(vectorstore.index_to_docstore_id)

    logger.info(
        "[MEMORY][SAVE] session_id=%s doc_id=%s store_path=%s total_docs=%s question=%s answer=%s",
        session_id,
        doc_id,
        MEMORY_STORE_PATH,
        total_docs,
        question[:120].replace("\n", " "),
        answer[:120].replace("\n", " "),
    )
