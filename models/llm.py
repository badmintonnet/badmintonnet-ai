import os

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

try:
    from langchain_core.rate_limiters import InMemoryRateLimiter
except Exception:  # pragma: no cover - keeps older LangChain installs usable.
    InMemoryRateLimiter = None

load_dotenv()

OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-5.5")
OPENAI_TIMEOUT_SECONDS = float(os.getenv("OPENAI_TIMEOUT_SECONDS", "60"))
OPENAI_MAX_RETRIES = int(os.getenv("OPENAI_MAX_RETRIES", "2"))
OPENAI_TEMPERATURE = float(os.getenv("OPENAI_TEMPERATURE", "0.2"))
OPENAI_MAX_TOKENS = os.getenv("OPENAI_MAX_TOKENS")
OPENAI_REQUESTS_PER_SECOND = float(os.getenv("OPENAI_REQUESTS_PER_SECOND", "0.2"))
OPENAI_RATE_CHECK_SECONDS = float(os.getenv("OPENAI_RATE_CHECK_SECONDS", "0.25"))
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL")

_llm_kwargs = {
    "model": OPENAI_MODEL,
    "temperature": OPENAI_TEMPERATURE,
    "timeout": OPENAI_TIMEOUT_SECONDS,
    "max_retries": OPENAI_MAX_RETRIES,
}

if OPENAI_MAX_TOKENS:
    _llm_kwargs["max_tokens"] = int(OPENAI_MAX_TOKENS)

if InMemoryRateLimiter is not None and OPENAI_REQUESTS_PER_SECOND > 0:
    _llm_kwargs["rate_limiter"] = InMemoryRateLimiter(
        requests_per_second=OPENAI_REQUESTS_PER_SECOND,
        check_every_n_seconds=OPENAI_RATE_CHECK_SECONDS,
        max_bucket_size=1,
    )

openai_api_key = os.getenv("OPENAI_API_KEY")
if openai_api_key:
    _llm_kwargs["api_key"] = openai_api_key

if OPENAI_BASE_URL:
    _llm_kwargs["base_url"] = OPENAI_BASE_URL

llm = ChatOpenAI(**_llm_kwargs)
