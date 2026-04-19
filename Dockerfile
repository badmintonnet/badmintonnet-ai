FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PORT=8000 \
    EMBEDDING_MODEL_NAME=BAAI/bge-small-en-v1.5 \
    HF_HOME=/app/.cache/huggingface \
    SENTENCE_TRANSFORMERS_HOME=/app/.cache/huggingface

WORKDIR /app

ARG HF_TOKEN=

RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --upgrade pip \
    && pip install -r requirements.txt

RUN HF_TOKEN="${HF_TOKEN}" python -c "from sentence_transformers import SentenceTransformer; import os; SentenceTransformer(os.environ['EMBEDDING_MODEL_NAME'], cache_folder=os.environ['SENTENCE_TRANSFORMERS_HOME'])"

COPY . .

RUN mkdir -p /app/session_memory_store \
    && useradd --create-home --shell /bin/bash appuser \
    && chown -R appuser:appuser /app

USER appuser

EXPOSE 8000

CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT}"]
