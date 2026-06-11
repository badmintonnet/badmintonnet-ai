import asyncio
from collections.abc import Awaitable, Callable
from contextlib import asynccontextmanager
import logging
import os
import re
import time
from typing import TypeVar
import warnings

from langchain_core._api.deprecation import LangChainPendingDeprecationWarning

warnings.filterwarnings(
    "ignore",
    message=r"The default value of `allowed_objects` will change in a future version\..*",
    category=LangChainPendingDeprecationWarning,
)

from fastapi import FastAPI, Header
from langchain_core.callbacks.base import BaseCallbackHandler
from langchain_core.messages import AIMessage, HumanMessage
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
LLM_MIN_INTERVAL_SECONDS = float(os.getenv("LLM_MIN_INTERVAL_SECONDS", "3"))
RATE_LIMIT_COOLDOWN_SECONDS = float(os.getenv("RATE_LIMIT_COOLDOWN_SECONDS", "35"))
MEMORY_CONTEXT_CHAR_LIMIT = 1500
RAG_CONTEXT_CHAR_LIMIT = 2500
CHAT_INPUT_CHAR_LIMIT = 5000
FALLBACK_RAG_PROMPT = """
Ban la tro ly BadmintonNet.
Chi tra loi bang tieng Viet.
Chi dung Session memory va Context duoc cung cap trong prompt nay.
Khong goi tool, khong tao tool call, khong tra ve JSON tool call.
Neu Context khong co du lieu can thiet, hay noi ro chua co thong tin.
"""
_llm_semaphore = asyncio.Semaphore(max(1, LLM_MAX_CONCURRENCY))
_llm_schedule_lock = asyncio.Lock()
_next_llm_request_at = 0.0
_rate_limited_until = 0.0
T = TypeVar("T")


def _shorten(value: object, limit: int = 300) -> str:
    text = str(value).replace("\n", " ")
    text = re.sub(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+", "<email>", text)
    text = re.sub(r"(?<!\d)(0\d{8,10})(?!\d)", "<phone>", text)
    return text if len(text) <= limit else f"{text[:limit]}..."


def _truncate_context(value: object, limit: int) -> str:
    text = str(value or "").strip()
    if len(text) <= limit:
        return text
    return f"{text[:limit].rstrip()}\n...[context truncated]"


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


class ConversationTitleRequest(BaseModel):
    message: str


def _is_payload_too_large_error(exc: Exception) -> bool:
    text = str(exc).lower()
    return (
        "413" in text
        or "payload too large" in text
        or "request too large" in text
    )


def _is_rate_limit_error(exc: Exception) -> bool:
    if _is_payload_too_large_error(exc):
        return False

    text = str(exc).lower()
    return (
        "429" in text
        or "too many requests" in text
        or "rate limit" in text
    )


def _extract_retry_after_seconds(exc: Exception) -> float | None:
    response = getattr(exc, "response", None)
    headers = getattr(response, "headers", None)
    retry_after = None
    if headers:
        retry_after = headers.get("retry-after") or headers.get("Retry-After")

    if retry_after:
        try:
            return max(0.0, float(retry_after))
        except ValueError:
            pass

    text = str(exc)
    patterns = (
        r"try again in\s+([0-9]+(?:\.[0-9]+)?)\s*(ms|milliseconds|s|sec|seconds|m|minutes)?",
        r"retry(?:-after| after)?[:=\s]+([0-9]+(?:\.[0-9]+)?)\s*(ms|milliseconds|s|sec|seconds|m|minutes)?",
    )
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if not match:
            continue

        value = float(match.group(1))
        unit = (match.group(2) or "seconds").lower()
        if unit in {"ms", "milliseconds"}:
            return max(0.0, value / 1000)
        if unit in {"m", "minutes"}:
            return max(0.0, value * 60)
        return max(0.0, value)

    return None


def _mark_rate_limited_now(exc: Exception | None = None) -> None:
    global _rate_limited_until
    retry_after_seconds = _extract_retry_after_seconds(exc) if exc else None
    cooldown_seconds = max(RATE_LIMIT_COOLDOWN_SECONDS, retry_after_seconds or 0.0)
    _rate_limited_until = time.monotonic() + cooldown_seconds
    logger.warning("[RATE_LIMIT] Cooling down LLM calls for %.1fs", cooldown_seconds)


def _is_in_rate_limit_cooldown() -> bool:
    return time.monotonic() < _rate_limited_until


async def _wait_for_llm_slot() -> None:
    global _next_llm_request_at

    async with _llm_schedule_lock:
        now = time.monotonic()
        wait_seconds = max(
            0.0,
            _rate_limited_until - now,
            _next_llm_request_at - now,
        )

        if wait_seconds:
            logger.info("[LLM_GATE] Waiting %.1fs before next LLM call", wait_seconds)
            await asyncio.sleep(wait_seconds)
            now = time.monotonic()

        _next_llm_request_at = now + max(0.0, LLM_MIN_INTERVAL_SECONDS)


async def _run_llm_call(call: Callable[[], Awaitable[T]]) -> T:
    async with _llm_semaphore:
        await _wait_for_llm_slot()
        try:
            return await call()
        except Exception as exc:
            if _is_rate_limit_error(exc):
                _mark_rate_limited_now(exc)
            raise


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


def _normalize_generated_title(raw_title: str) -> str:
    title = raw_title.strip().strip("\"'`")
    title = " ".join(title.split())
    return title[:120].rstrip(" .,;:-")


def _build_title_fallback(message: str) -> str:
    cleaned = " ".join(message.strip().split())
    if not cleaned:
        return "Cuộc trò chuyện mới"

    words = cleaned.split()
    fallback = " ".join(words[:8])
    if len(words) > 8:
        fallback = f"{fallback}..."
    return fallback[:120]


def _message_content_to_text(content: object) -> str:
    if isinstance(content, str):
        return content.strip()

    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, dict):
                text = item.get("text") or item.get("content")
                if text:
                    parts.append(str(text))
            elif item:
                parts.append(str(item))
        return "\n".join(parts).strip()

    return str(content or "").strip()


def _extract_agent_answer(result: object) -> str:
    messages = result.get("messages", []) if isinstance(result, dict) else []
    for message in reversed(messages):
        if not isinstance(message, AIMessage):
            continue
        content = _message_content_to_text(message.content)
        if content:
            return content
    return ""


def _format_agent_messages_for_final_answer(result: object, limit: int = 6000) -> str:
    messages = result.get("messages", []) if isinstance(result, dict) else []
    lines = []
    for message in messages[-12:]:
        role = getattr(message, "type", message.__class__.__name__)
        content = _message_content_to_text(getattr(message, "content", ""))
        if not content:
            continue
        lines.append(f"{role}:\n{content}")

    text = "\n\n".join(lines)
    return _truncate_context(text, limit)


async def _recover_empty_agent_answer(result: object, question: str) -> str:
    transcript = _format_agent_messages_for_final_answer(result)
    if not transcript:
        return ""

    prompt = f"""
    Bạn là trợ lý BadmintonNet. Hãy viết câu trả lời cuối cùng bằng tiếng Việt
    dựa trên kết quả tool và ngữ cảnh bên dưới.

    Yêu cầu:
    - Không trả rỗng.
    - Không bịa dữ liệu ngoài tool/ngữ cảnh.
    - Trả lời trực tiếp câu hỏi của người dùng.
    - Nếu câu hỏi là gợi ý tập luyện, hãy dựa vào trình độ/rating hiện có để đưa kế hoạch cụ thể.

    Câu hỏi:
    {question}

    Ngữ cảnh và kết quả tool:
    {transcript}
    """
    llm_result = await _run_llm_call(lambda: asyncio.to_thread(llm.invoke, prompt))
    return _message_content_to_text(llm_result.content)


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
    memory_context = _truncate_context(
        _safe_get_session_memory_context(payload.sessionId, payload.question),
        MEMORY_CONTEXT_CHAR_LIMIT,
    )
    rag_context = _truncate_context(
        _safe_get_rag_context(payload.question),
        RAG_CONTEXT_CHAR_LIMIT,
    )
    chat_input = _truncate_context(
        _build_chat_input(payload.question, memory_context, rag_context),
        CHAT_INPUT_CHAR_LIMIT,
    )
    logger.info("[CHAT] access_token_present=%s", bool(access_token))
    logger.info("[CHAT] session_id=%s", payload.sessionId)
    logger.info("[CHAT] question=%s", _shorten(payload.question, 200))
    logger.info(
        "[CHAT] mcp_tools=%s",
        ", ".join(sorted(mcp_tool_names)) if mcp_tool_names else "none",
    )

    try:
        with request_access_token_scope(access_token):
            async def _invoke_agent():
                return await asyncio.wait_for(
                    graph.ainvoke(
                        {"messages": [HumanMessage(content=chat_input)]},
                        config={
                            "callbacks": [ToolLogHandler(mcp_tool_names)],
                            "recursion_limit": AGENT_RECURSION_LIMIT,
                        },
                    ),
                    timeout=AGENT_TIMEOUT_SECONDS,
                )

            result = await _run_llm_call(_invoke_agent)
        answer = _extract_agent_answer(result)
        if not answer:
            logger.warning("[CHAT] Agent returned empty answer; recovering from tool outputs")
            answer = await _recover_empty_agent_answer(result, payload.question)

        if not answer:
            answer = "Mình chưa tạo được câu trả lời từ dữ liệu hiện có. Bạn thử hỏi lại ngắn hơn hoặc cung cấp thêm mục tiêu tập luyện cụ thể nhé."

        _safe_save_session_turn(payload.sessionId, payload.question, answer)
        return {"answer": answer, "source": "agent"}
    except Exception as exc:
        if _is_payload_too_large_error(exc):
            logger.warning("[CHAT] Agent request too large: %s", exc)
            return {
                "answer": "AI đang nhận quá nhiều ngữ cảnh nên chưa thể trả lời. Bạn thử hỏi ngắn hơn hoặc giảm bớt dữ liệu liên quan rồi thử lại nhé.",
                "source": "payload-too-large",
                "error": str(exc),
            }

        # Avoid triggering another immediate LLM call when already rate-limited.
        if _is_rate_limit_error(exc):
            _mark_rate_limited_now(exc)
            logger.warning("[CHAT] Agent rate-limited: %s", exc)
            return {
                "answer": "AI đang quá tải. Bạn chờ 10-20 giây để thử lại nhé.",
                "source": "rate-limit",
                "error": str(exc),
            }

        logger.exception("[CHAT] Agent failed, fallback to RAG: %s", exc)

        # Fallback to direct RAG answer if tool-calling fails.
        prompt = f"""
        {FALLBACK_RAG_PROMPT}

        Session memory:
        {memory_context}

        Context:
        {rag_context}

        Question:
        {payload.question}
        """

        try:
            llm_result = await _run_llm_call(lambda: asyncio.to_thread(llm.invoke, prompt))
            answer = llm_result.content
        except Exception as fallback_exc:
            if _is_payload_too_large_error(fallback_exc):
                return {
                    "answer": "AI đang nhận quá nhiều ngữ cảnh nên chưa thể trả lời. Bạn thử hỏi ngắn hơn hoặc giảm bớt dữ liệu liên quan rồi thử lại nhé.",
                    "source": "payload-too-large",
                    "error": str(fallback_exc),
                }
            if _is_rate_limit_error(fallback_exc):
                _mark_rate_limited_now(fallback_exc)
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


@app.post("/conversation-title")
async def generate_conversation_title(payload: ConversationTitleRequest):
    message = payload.message.strip()
    if not message:
        return {"title": "Cuộc trò chuyện mới", "source": "fallback"}
    if _is_in_rate_limit_cooldown():
        return {"title": _build_title_fallback(message), "source": "rate-limit-cooldown"}

    prompt = f"""
    Bạn là trợ lý đặt tiêu đề cho cuộc hội thoại.
    Hãy tạo đúng 1 tiêu đề ngắn gọn, rõ nghĩa cho cuộc trò chuyện dựa trên tin nhắn đầu tiên.
    Yêu cầu:
    - Chỉ trả về duy nhất tiêu đề, không giải thích.
    - Tối đa 12 từ.
    - Bắt buộc dùng tiếng Việt có dấu tự nhiên, rõ ràng.

    Tin nhắn đầu tiên:
    {message}
    """

    try:
        llm_result = await _run_llm_call(lambda: asyncio.to_thread(llm.invoke, prompt))
        title = _normalize_generated_title(llm_result.content)
        if not title:
            raise ValueError("Empty title returned from LLM")
        return {"title": title, "source": "llm"}
    except Exception as exc:
        logger.exception("[TITLE] Failed to generate conversation title: %s", exc)
        return {
            "title": _build_title_fallback(message),
            "source": "fallback",
            "error": str(exc),
        }
