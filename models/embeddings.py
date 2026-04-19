import os

from langchain_huggingface import HuggingFaceEmbeddings

embedding = HuggingFaceEmbeddings(
    model_name=os.getenv("EMBEDDING_MODEL_NAME", "BAAI/bge-small-en-v1.5"),
    cache_folder=os.getenv("SENTENCE_TRANSFORMERS_HOME")
    or os.getenv("HF_HOME"),
    model_kwargs={
        "local_files_only": os.getenv(
            "EMBEDDING_LOCAL_FILES_ONLY", ""
        ).lower()
        in {"1", "true", "yes"},
    },
)
