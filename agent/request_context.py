from contextlib import contextmanager
from contextvars import ContextVar, Token
from typing import Iterator

_request_access_token: ContextVar[str | None] = ContextVar(
    "request_access_token",
    default=None,
)


@contextmanager
def request_access_token_scope(access_token: str | None) -> Iterator[None]:
    """Attach access token to current async request context."""
    ctx_token: Token[str | None] = _request_access_token.set(access_token)
    try:
        yield
    finally:
        _request_access_token.reset(ctx_token)


def get_request_access_token() -> str | None:
    """Return request-scoped access token used for MCP forwarding."""
    token = _request_access_token.get()
    if token is None:
        return None

    normalized = token.strip()
    return normalized or None
