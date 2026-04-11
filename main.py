import asyncio
from contextlib import asynccontextmanager
import logging
import os
import time

from fastapi import FastAPI, Header
from langchain_core.callbacks.base import BaseCallbackHandler
from langchain_core.messages import HumanMessage
from pydantic import BaseModel

from agent.graph import cleanup_graph, get_graph, get_mcp_tool_names
from agent.request_context import request_access_token_scope
from memory.store import get_session_memory_context, save_session_turn
from models.llm import llm
from prompts.system_prompt import SYSTEM_PROMPT
from rag.retriever import retriever

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger("badmintonnet.agent")
AGENT_TIMEOUT_SECONDS = float(os.getenv("AGENT_TIMEOUT_SECONDS", "45"))
AGENT_RECURSION_LIMIT = int(os.getenv("AGENT_RECURSION_LIMIT", "6"))
LLM_MAX_CONCURRENCY = int(os.getenv("LLM_MAX_CONCURRENCY", "1"))
RATE_LIMIT_COOLDOWN_SECONDS = float(os.getenv("RATE_LIMIT_COOLDOWN_SECONDS", "8"))
_llm_semaphore = asyncio.Semaphore(max(1, LLM_MAX_CONCURRENCY))
_rate_limited_until = 0.0


def _shorten(value: object, limit: int = 300) -> str:
    text = str(value).replace("\n", " ")
    return text if len(text) <= limit else f"{text[:limit]}..."


class ToolLogHandler(BaseCallbackHandler):
    def __init__(self, mcp_tool_names: set[str]):
        self.mcp_tool_names = mcp_tool_names

    def on_tool_start(self, serialized, input_str, **kwargs):
        tool_name = serialized.get("name", "unknown") if isinstance(serialized, dict) else "unknown"
        tool_kind = "MCP" if tool_name in self.mcp_tool_names else "LOCAL"
        logger.info(
            "[TOOL_START][%s] name=%s input=%s",
            tool_kind,
            tool_name,
            _shorten(input_str),
        )

    def on_tool_end(self, output, **kwargs):
        logger.info("[TOOL_END] output=%s", _shorten(output))

    def on_tool_error(self, error, **kwargs):
        logger.error("[TOOL_ERROR] %s", error)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Warm up graph on startup so first request is faster.
    await get_graph()
    yield
    await cleanup_graph()


app = FastAPI(lifespan=lifespan)


class ChatRequest(BaseModel):
    sessionId: str
    question: str
    access_token: str | None = None


def _is_rate_limit_error(exc: Exception) -> bool:
    text = str(exc).lower()
    return (
        "429" in text
        or "too many requests" in text
        or "rate limit" in text
    )


def _mark_rate_limited_now() -> None:
    global _rate_limited_until
    _rate_limited_until = time.monotonic() + RATE_LIMIT_COOLDOWN_SECONDS


def _is_in_rate_limit_cooldown() -> bool:
    return time.monotonic() < _rate_limited_until


def _extract_access_token(
    explicit_access_token: str | None,
    authorization_header: str | None,
) -> str | None:
    if explicit_access_token:
        token = explicit_access_token.strip()
        if not token:
            return None
        if token.lower().startswith("bearer "):
            return token[7:].strip() or None
        return token

    if not authorization_header:
        return None

    header_value = authorization_header.strip()
    if not header_value:
        return None
    if header_value.lower().startswith("bearer "):
        return header_value[7:].strip() or None
    return header_value


def _build_chat_input(
    question: str,
    memory_context: str,
    rag_context: str,
) -> str:
    parts = [f"Cau hoi hien tai:\n{question.strip()}"]

    if memory_context.strip():
        parts.insert(0, f"Context phien chat truoc do:\n{memory_context.strip()}")

    if rag_context.strip():
        insert_at = 1 if memory_context.strip() else 0
        parts.insert(insert_at, f"Knowledge base lien quan:\n{rag_context.strip()}")

    return "\n\n".join(parts)


def _safe_get_session_memory_context(session_id: str, question: str) -> str:
    try:
        return get_session_memory_context(session_id, question)
    except Exception:
        logger.exception("[CHAT] Failed to load session memory for session_id=%s", session_id)
        return ""


def _safe_get_rag_context(question: str) -> str:
    try:
        docs = retriever.invoke(question)
    except Exception:
        logger.exception("[CHAT] Failed to retrieve RAG context")
        return ""

    return "\n".join(doc.page_content for doc in docs)


def _safe_save_session_turn(session_id: str, question: str, answer: str) -> None:
    try:
        save_session_turn(session_id, question, answer)
    except Exception:
        logger.exception("[CHAT] Failed to persist session memory for session_id=%s", session_id)


@app.post("/chat")
async def chat(
    payload: ChatRequest,
    authorization: str | None = Header(default=None, alias="Authorization"),
):
    if _is_in_rate_limit_cooldown():
        return {
            "answer": "AI dang qua tai. Vui long thu lai sau vai giay.",
            "source": "rate-limit-cooldown",
        }

    graph = await get_graph()
    mcp_tool_names = get_mcp_tool_names()
    access_token = _extract_access_token(payload.access_token, authorization)
    memory_context = _safe_get_session_memory_context(payload.sessionId, payload.question)
    rag_context = _safe_get_rag_context(payload.question)
    chat_input = _build_chat_input(payload.question, memory_context, rag_context)
    logger.info("[CHAT] access_token_present=%s", bool(access_token))
    logger.info("[CHAT] session_id=%s", payload.sessionId)
    logger.info("[CHAT] question=%s", _shorten(payload.question, 200))
    logger.info(
        "[CHAT] mcp_tools=%s",
        ", ".join(sorted(mcp_tool_names)) if mcp_tool_names else "none",
    )

    try:
        with request_access_token_scope(access_token):
            async with _llm_semaphore:
                result = await asyncio.wait_for(
                    graph.ainvoke(
                        {"messages": [HumanMessage(content=chat_input)]},
                        config={
                            "callbacks": [ToolLogHandler(mcp_tool_names)],
                            "recursion_limit": AGENT_RECURSION_LIMIT,
                        },
                    ),
                    timeout=AGENT_TIMEOUT_SECONDS,
                )
        answer = result["messages"][-1].content
        _safe_save_session_turn(payload.sessionId, payload.question, answer)
        return {"answer": answer, "source": "agent"}
    except Exception as exc:
        logger.exception("[CHAT] Agent failed, fallback to RAG: %s", exc)

        # Avoid triggering another immediate LLM call when already rate-limited.
        if _is_rate_limit_error(exc):
            _mark_rate_limited_now()
            return {
                "answer": "AI đang quá tải. Bạn chờ 10-20 giây để thử lại nhé.",
                "source": "rate-limit",
                "error": str(exc),
            }

        # Fallback to direct RAG answer if tool-calling fails.
        prompt = f"""
        {SYSTEM_PROMPT}

        Session memory:
        {memory_context}

        Context:
        {rag_context}

        Question:
        {payload.question}
        """

        try:
            async with _llm_semaphore:
                llm_result = await asyncio.to_thread(llm.invoke, prompt)
            answer = llm_result.content
        except Exception as fallback_exc:
            if _is_rate_limit_error(fallback_exc):
                _mark_rate_limited_now()
                return {
                    "answer": "AI đang quá tải. Bạn chờ 10-20 giây để thử lại nhé.",
                    "source": "rate-limit",
                    "error": str(fallback_exc),
                }
            raise

        _safe_save_session_turn(payload.sessionId, payload.question, answer)

        return {
            "answer": answer,
            "source": "fallback-rag",
            "error": str(exc),
        }
