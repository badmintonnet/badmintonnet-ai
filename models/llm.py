import os

from dotenv import load_dotenv
from langchain_groq import ChatGroq

load_dotenv()

GROQ_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")
GROQ_TIMEOUT_SECONDS = float(os.getenv("GROQ_TIMEOUT_SECONDS", "60"))
GROQ_MAX_RETRIES = int(os.getenv("GROQ_MAX_RETRIES", "1"))
GROQ_TEMPERATURE = float(os.getenv("GROQ_TEMPERATURE", "0.2"))
GROQ_MAX_TOKENS = os.getenv("GROQ_MAX_TOKENS")

_llm_kwargs = {
    "model": GROQ_MODEL,
    "temperature": GROQ_TEMPERATURE,
    "timeout": GROQ_TIMEOUT_SECONDS,
    "max_retries": GROQ_MAX_RETRIES,
}

if GROQ_MAX_TOKENS:
    _llm_kwargs["max_tokens"] = int(GROQ_MAX_TOKENS)

# If API key is not provided here, ChatGroq will read GROQ_API_KEY from env.
groq_api_key = os.getenv("GROQ_API_KEY")
if groq_api_key:
    _llm_kwargs["api_key"] = groq_api_key

llm = ChatGroq(**_llm_kwargs)