from langchain_core.tools import tool

from rag.retriever import retriever


@tool
def rag_search(query: str) -> str:
    """Search badminton platform knowledge base for relevant context."""
    docs = retriever.invoke(query)
    if not docs:
        return "Khong tim thay thong tin lien quan trong kho tri thuc."
    return "\n\n---\n\n".join(doc.page_content for doc in docs)
