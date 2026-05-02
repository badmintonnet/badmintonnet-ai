import os

from dotenv import load_dotenv
from langchain_groq import ChatGroq

try:
    from langchain_core.rate_limiters import InMemoryRateLimiter
except Exception:  # pragma: no cover - keeps older LangChain installs usable.
    InMemoryRateLimiter = None

load_dotenv()

GROQ_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")
GROQ_TIMEOUT_SECONDS = float(os.getenv("GROQ_TIMEOUT_SECONDS", "60"))
GROQ_MAX_RETRIES = int(os.getenv("GROQ_MAX_RETRIES", "1"))
GROQ_TEMPERATURE = float(os.getenv("GROQ_TEMPERATURE", "0.2"))
GROQ_MAX_TOKENS = os.getenv("GROQ_MAX_TOKENS")
GROQ_REQUESTS_PER_SECOND = float(os.getenv("GROQ_REQUESTS_PER_SECOND", "0.2"))
GROQ_RATE_CHECK_SECONDS = float(os.getenv("GROQ_RATE_CHECK_SECONDS", "0.25"))

_llm_kwargs = {
    "model": GROQ_MODEL,
    "temperature": GROQ_TEMPERATURE,
    "timeout": GROQ_TIMEOUT_SECONDS,
    "max_retries": GROQ_MAX_RETRIES,
}

if GROQ_MAX_TOKENS:
    _llm_kwargs["max_tokens"] = int(GROQ_MAX_TOKENS)

if InMemoryRateLimiter is not None and GROQ_REQUESTS_PER_SECOND > 0:
    _llm_kwargs["rate_limiter"] = InMemoryRateLimiter(
        requests_per_second=GROQ_REQUESTS_PER_SECOND,
        check_every_n_seconds=GROQ_RATE_CHECK_SECONDS,
        max_bucket_size=1,
    )

# If API key is not provided here, ChatGroq will read GROQ_API_KEY from env.
groq_api_key = os.getenv("GROQ_API_KEY")
if groq_api_key:
    _llm_kwargs["api_key"] = groq_api_key

llm = ChatGroq(**_llm_kwargs)
