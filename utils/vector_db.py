# vector_db.py
from langchain_community.vectorstores import FAISS
from langchain_core.embeddings import Embeddings
import os
from dotenv import load_dotenv
from utils.embeddings import get_embeddings

load_dotenv()

class GoogleEmbeddings(Embeddings):
    def embed_documents(self, texts):
        return get_embeddings(texts)
    
    def embed_query(self, text):
        return get_embeddings([text])[0]

embeddings = GoogleEmbeddings()

# Initialize vector_db as None, will be created on first use
vector_db = None

def add_texts(texts, metadatas=None):
    global vector_db
    if metadatas is not None and not isinstance(metadatas, list):
        # Convert single metadata dict to list of dicts
        metadatas = [metadatas] * len(texts)
    elif metadatas is None:
        metadatas = [{}] * len(texts)
    
    if vector_db is None:
        # Create vector_db with the first batch of texts
        vector_db = FAISS.from_texts(texts, embedding=embeddings, metadatas=metadatas)
    else:
        vector_db.add_texts(texts, metadatas=metadatas)

def similarity_search(query, k=5):
    if vector_db is None:
        return []
    return [doc.page_content for doc in vector_db.similarity_search(query, k=k)]
