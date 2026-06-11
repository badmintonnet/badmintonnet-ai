import os

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

try:
    from langchain_core.rate_limiters import InMemoryRateLimiter
except Exception:  # pragma: no cover - keeps older LangChain installs usable.
    InMemoryRateLimiter = None

load_dotenv()

OPENAI_MODEL = os.getenv("OPENAI_MODEL_FAST") or os.getenv("OPENAI_MODEL", "gpt-5.4-mini")
OPENAI_RECOVERY_MODEL = os.getenv("OPENAI_MODEL_RECOVERY") or os.getenv("OPENAI_MODEL_STRONG") or OPENAI_MODEL
OPENAI_TITLE_MODEL = os.getenv("OPENAI_MODEL_TITLE", OPENAI_MODEL)
OPENAI_TIMEOUT_SECONDS = float(os.getenv("OPENAI_TIMEOUT_SECONDS", "60"))
OPENAI_MAX_RETRIES = int(os.getenv("OPENAI_MAX_RETRIES", "2"))
OPENAI_TEMPERATURE = float(os.getenv("OPENAI_TEMPERATURE", "0.2"))
OPENAI_MAX_TOKENS = os.getenv("OPENAI_MAX_TOKENS")
OPENAI_RECOVERY_MAX_TOKENS = os.getenv("OPENAI_RECOVERY_MAX_TOKENS") or OPENAI_MAX_TOKENS
OPENAI_TITLE_MAX_TOKENS = os.getenv("OPENAI_TITLE_MAX_TOKENS", "120")
OPENAI_REQUESTS_PER_SECOND = float(os.getenv("OPENAI_REQUESTS_PER_SECOND", "0.2"))
OPENAI_RATE_CHECK_SECONDS = float(os.getenv("OPENAI_RATE_CHECK_SECONDS", "0.25"))
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL")


def create_llm(model: str, max_tokens: str | None = OPENAI_MAX_TOKENS) -> ChatOpenAI:
    llm_kwargs = {
        "model": model,
        "temperature": OPENAI_TEMPERATURE,
        "timeout": OPENAI_TIMEOUT_SECONDS,
        "max_retries": OPENAI_MAX_RETRIES,
    }

    if max_tokens:
        llm_kwargs["max_tokens"] = int(max_tokens)

    if InMemoryRateLimiter is not None and OPENAI_REQUESTS_PER_SECOND > 0:
        llm_kwargs["rate_limiter"] = InMemoryRateLimiter(
            requests_per_second=OPENAI_REQUESTS_PER_SECOND,
            check_every_n_seconds=OPENAI_RATE_CHECK_SECONDS,
            max_bucket_size=1,
        )

    openai_api_key = os.getenv("OPENAI_API_KEY")
    if openai_api_key:
        llm_kwargs["api_key"] = openai_api_key

    if OPENAI_BASE_URL:
        llm_kwargs["base_url"] = OPENAI_BASE_URL

    return ChatOpenAI(**llm_kwargs)


llm = create_llm(OPENAI_MODEL)
recovery_llm = create_llm(OPENAI_RECOVERY_MODEL, OPENAI_RECOVERY_MAX_TOKENS)
title_llm = create_llm(OPENAI_TITLE_MODEL, OPENAI_TITLE_MAX_TOKENS)
