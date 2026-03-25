import os
import sys



from langchain_community.document_loaders import TextLoader
from langchain_community.vectorstores import FAISS
from models.embeddings import embedding

documents = []

docs_path = "docs"

for file in os.listdir(docs_path):

    path = os.path.join(docs_path, file)

    loader = TextLoader(path, encoding="utf-8")

    documents.extend(loader.load())

vectorstore = FAISS.from_documents(documents, embedding)

vectorstore.save_local("vectorstore")

print("Vector DB created")