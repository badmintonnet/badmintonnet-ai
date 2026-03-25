import httpx
import logging
from collections.abc import Awaitable, Callable
from typing import Any

from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_mcp_adapters.interceptors import MCPToolCallRequest
from langgraph.prebuilt import ToolNode, create_react_agent

from agent.request_context import get_request_access_token
from agent.tools import rag_search
from models.llm import llm
from prompts.system_prompt import SYSTEM_PROMPT

MCP_CONFIG = {
	"badmintonnet": {
		"url": "http://127.0.0.1:3001/sse",
		"transport": "sse",
	}
}

_mcp_client: MultiServerMCPClient | None = None
_graph = None
_mcp_tool_names: set[str] = set()
BACKEND_BASE_URL = "http://127.0.0.1:8080"
logger = logging.getLogger("badmintonnet.agent")


async def _inject_access_token_header(
    request: MCPToolCallRequest,
    handler: Callable[[MCPToolCallRequest], Awaitable[Any]],
) -> Any:
    """Forward request-scoped bearer token to MCP over HTTP headers."""
    access_token = get_request_access_token()
    if access_token:
        headers: dict[str, Any] = dict(request.headers or {})
        headers["Authorization"] = f"Bearer {access_token}"
        request = request.override(headers=headers)

    return await handler(request)


async def _is_backend_up() -> bool:
	"""Fast health check for MCP downstream backend."""
	try:
		async with httpx.AsyncClient(timeout=1.5) as client:
			resp = await client.get(BACKEND_BASE_URL)
			return resp.status_code < 500
	except Exception:
		return False


async def build_graph():
    """Build ReAct graph with local RAG tool and remote MCP tools."""
    global _mcp_client, _mcp_tool_names

    # LUÔN load MCP tools (không check backend nữa)
    try:
        _mcp_client = MultiServerMCPClient(
            MCP_CONFIG,
            tool_interceptors=[_inject_access_token_header],
        )
        mcp_tools = await _mcp_client.get_tools()
        _mcp_tool_names = {tool.name for tool in mcp_tools}

        logger.info(
            "MCP tools loaded: %s",
            ", ".join(sorted(_mcp_tool_names)) if _mcp_tool_names else "none",
        )

    except Exception as e:
        logger.exception("Failed to load MCP tools: %s", e)
        _mcp_client = None
        _mcp_tool_names = set()
        mcp_tools = []

    all_tools = [rag_search, *mcp_tools]

    def _handle_tool_error(e: Exception) -> str:
        logger.exception("Tool execution failed: %s", e)
        return f"Tool call failed: {e}"

    tool_node = ToolNode(
        all_tools,
        handle_tool_errors=_handle_tool_error,
    )

    return create_react_agent(
        model=llm,
        tools=tool_node,
        prompt=SYSTEM_PROMPT,
    )


async def get_graph():
	global _graph

	if _graph is None:
		_graph = await build_graph()
	return _graph


async def cleanup_graph():
	global _mcp_client, _graph, _mcp_tool_names

	if _mcp_client is not None and hasattr(_mcp_client, "aclose"):
		await _mcp_client.aclose()

	_mcp_client = None
	_graph = None
	_mcp_tool_names = set()


def get_mcp_tool_names() -> set[str]:
	"""Return MCP tool names currently loaded in memory."""
	return set(_mcp_tool_names)

